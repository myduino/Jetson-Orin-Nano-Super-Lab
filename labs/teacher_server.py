"""The teacher server of the Myduino lab. It runs on the teacher's PC (Windows, Mac or Linux), not on a Jetson.

    python labs/teacher_server.py          (setup-teacher.ps1 does this for you)

The page shows every Jetson that reports in, the classes and their students. The teacher puts each
student on a Jetson and a camera. The Jetson agent (labs/agent.py) asks this server what to run and starts
the student's JupyterLab on the port shown here. The student opens  http://<Jetson IP>:<port>  and types the PIN.
Only the Python standard library is used.
"""
import getpass
import hashlib
import hmac
import json
import os
import re
import secrets
import socket
import socketserver
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8800
FIRST_PORT = 8881                       # student JupyterLab ports on a Jetson start here
DATA = os.path.join(os.path.expanduser("~"), "myduino-teacher")
STATE = os.path.join(DATA, "state.json")
NAME = re.compile(r"^[a-z0-9_]{1,20}$")
ONLINE = 20                             # seconds without news before a Jetson counts as offline

lock = threading.RLock()
sessions = set()                        # browsers that typed the password
db = {"password": "", "key": "", "classes": {}, "pending_delete": []}
jetsons = {}                            # id -> what the agent last reported (not saved)


# ---------------------------------------------------------------- saved state
def load():
    os.makedirs(DATA, exist_ok=True)
    try:
        db.update(json.load(open(STATE)))
    except (OSError, ValueError):
        pass


def save():
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(db, f, indent=1)
    os.replace(tmp, STATE)


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()


def set_password():
    while True:
        a = getpass.getpass("Choose a teacher password: ")
        if len(a) < 4:
            print("Use at least 4 characters.")
            continue
        if a != getpass.getpass("Type it again: "):
            print("They are not the same.")
            continue
        salt = secrets.token_bytes(16)
        db["password"] = salt.hex() + " " + _hash(a, salt)
        save()
        return


def check_password(password):
    try:
        salt_hex, digest = db["password"].split()
    except ValueError:
        return False
    return hmac.compare_digest(_hash(password, bytes.fromhex(salt_hex)), digest)


def my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def clean(text):
    return re.sub(r"[^a-z0-9_]", "_", str(text).lower()).strip("_")[:20]


# ---------------------------------------------------------------- the rules
def online(j):
    return time.time() - j.get("seen", 0) < ONLINE


def free_port(jetson, student):
    """The port of this student on this Jetson: the same as last time when it is still free."""
    taken = {s["port"] for c in db["classes"].values() for s in c["students"].values() if s.get("jetson") == jetson and s is not student}
    old = student.get("ports", {}).get(jetson)
    if old and old not in taken:
        return old
    port = FIRST_PORT
    while port in taken:
        port += 1
    return port


def assign(cls, name, jetson, camera):
    s = db["classes"][cls]["students"][name]
    if not jetson:
        s["jetson"], s["camera"] = "", None
        return "Saved."
    if jetson not in jetsons:
        return "That Jetson has not reported in."
    if camera in ("", None):
        camera = None
    else:
        camera = int(camera)
        for c2, cl in db["classes"].items():
            for n2, o in cl["students"].items():
                if o is not s and o.get("jetson") == jetson and o.get("camera") == camera:
                    return f"Camera {camera} of {jetson} is used by {c2}/{n2}."
    s["jetson"], s["camera"] = jetson, camera
    s["port"] = free_port(jetson, s)
    s.setdefault("ports", {})[jetson] = s["port"]
    if jetson not in s.setdefault("homes", []):
        s["homes"].append(jetson)
    return "Saved."


def new_student(cls, name):
    return {"pin": f"{secrets.randbelow(1_000_000):06d}", "jetson": "", "camera": None, "port": 0, "ports": {}, "homes": []}


def view(ip):
    classes = []
    for cn in sorted(db["classes"]):
        rows = []
        for sn in sorted(db["classes"][cn]["students"]):
            s = db["classes"][cn]["students"][sn]
            j = jetsons.get(s.get("jetson", ""), {})
            key = f"{cn}__{sn}"
            running = key in {r["key"] for r in j.get("running", [])}
            preparing = key in j.get("preparing", [])
            rows.append({"name": sn, "jetson": s.get("jetson", ""), "camera": s.get("camera"), "pin": s["pin"], "port": s.get("port") or "",
                         "address": f"{j['ip']}:{s['port']}" if s.get("jetson") and j.get("ip") else "", "state": ("running" if running else ("preparing" if preparing else ("starting" if s.get("jetson") and online(j) else ("offline" if s.get("jetson") else "")))),
                         "homes": s.get("homes", [])})
        classes.append({"name": cn, "students": rows})
    out = []
    for jid in sorted(jetsons):
        j = jetsons[jid]
        users = {}
        for cn, cl in db["classes"].items():
            for sn, s in cl["students"].items():
                if s.get("jetson") == jid and s.get("camera") is not None:
                    users[s["camera"]] = f"{cn}/{sn}"
        out.append({"id": jid, "ip": j.get("ip", ""), "online": online(j), "ago": int(time.time() - j.get("seen", 0)),
                    "ready": j.get("ready", True), "note": j.get("note", ""),
                    "cameras": [dict(c, user=users.get(c["number"], "")) for c in j.get("cameras", [])],
                    "students": sum(1 for cl in db["classes"].values() for s in cl["students"].values() if s.get("jetson") == jid)})
    return {"ip": ip, "port": PORT, "key": db["key"], "host": socket.gethostname(), "classes": classes, "jetsons": out,
            "pending": len(db["pending_delete"])}


def agent_hello(body):
    jid = clean(body.get("id", ""))
    if not jid:
        return {"error": "no id"}
    j = jetsons.setdefault(jid, {})
    j.update(ip=str(body.get("ip", "")), seen=time.time(), cameras=body.get("cameras", [])[:6], running=body.get("running", [])[:40],
             ready=bool(body.get("ready", True)), note=str(body.get("note", ""))[:200], preparing=body.get("preparing", [])[:40])
    for gone in body.get("deleted", []):                                   # the agent deleted these folders
        db["pending_delete"] = [d for d in db["pending_delete"] if not (d["jetson"] == jid and f"{d['class']}__{d['student']}" == gone)]
    save_soon()
    plan = []
    for cn, cl in db["classes"].items():
        for sn, s in cl["students"].items():
            if s.get("jetson") == jid:
                plan.append({"class": cn, "student": sn, "port": s["port"], "pin": s["pin"], "camera": s.get("camera")})
    return {"plan": plan, "delete": [d for d in db["pending_delete"] if d["jetson"] == jid]}


_dirty = False


def save_soon():
    global _dirty
    _dirty = True


def saver():
    global _dirty
    while True:
        time.sleep(3)
        with lock:
            if _dirty:
                _dirty = False
                save()


# ---------------------------------------------------------------- the page
PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Myduino teacher</title>
<style>
body{font-family:system-ui,Segoe UI,sans-serif;margin:0;background:#f4f5f7;color:#1c2330}
header{background:#14213d;color:#fff;padding:14px 20px;display:flex;gap:16px;align-items:baseline;flex-wrap:wrap}
header h1{font-size:18px;margin:0} header span{opacity:.8;font-size:13px}
main{padding:16px 20px;max-width:1150px;margin:auto}
section{background:#fff;border-radius:10px;padding:14px 16px;margin:0 0 16px;box-shadow:0 1px 3px #0002}
h2{font-size:16px;margin:0 0 10px} table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #e6e8ee;vertical-align:middle} th{font-size:12px;color:#5b6477;text-transform:uppercase}
.wrap{overflow-x:auto}
.on{color:#0a7a3b;font-weight:600} .off{color:#8a91a1} .warn{color:#b45309}
button{font:inherit;padding:5px 10px;border-radius:6px;border:1px solid #b9c0cf;background:#fff;cursor:pointer}
button.go{background:#14213d;color:#fff;border-color:#14213d}
input,select,textarea{font:inherit;padding:5px 7px;border:1px solid #b9c0cf;border-radius:6px}
a{color:#1d4ed8} .note{color:#5b6477;font-size:13px} code{background:#eef0f4;padding:1px 5px;border-radius:4px}
.addr{font-family:Consolas,monospace;font-weight:600}
#login{max-width:340px;margin:80px auto}
</style></head><body>
<div id="login" hidden><section><h2>Teacher password</h2>
<form onsubmit="login(event)"><input id="pw" type="password" autofocus> <button class="go">Open</button></form>
<p id="loginmsg" class="note"></p></section></div>
<div id="app" hidden>
<header><h1>Myduino Jetson Lab: teacher</h1><span id="where"></span><span id="when"></span></header>
<main>
<section><h2>Jetsons</h2><div class="wrap"><table id="jets"></table></div>
<p class="note" id="addjet"></p></section>
<section><h2>Make a class</h2>
<form onsubmit="addClass(event)"><input id="cname" placeholder="class name, for example a" size="22"> <button class="go">Add class</button></form></section>
<div id="classes"></div>
<p class="note" id="pending"></p>
</main></div>
<script>
const $ = id => document.getElementById(id);
function el(tag, props, ...kids){ const e = document.createElement(tag); Object.assign(e, props||{}); kids.forEach(k => e.append(k)); return e; }
let busy = false, last = null;
async function api(path, body){
  const r = await fetch(path, body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {});
  if (r.status === 401){ show(false); throw new Error('login'); }
  return r.json();
}
function show(ok){ $('app').hidden = !ok; $('login').hidden = ok; }
async function login(e){ e.preventDefault();
  const r = await fetch('/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({password:$('pw').value})});
  if (r.ok){ show(true); refresh(); } else { $('loginmsg').textContent = 'Wrong password.'; } }
async function act(path, body){ busy = true; try { const r = await api(path, body); if (r.message && r.message !== 'Saved.') alert(r.message); } finally { busy = false; } refresh(); }
function addClass(e){ e.preventDefault(); act('/api/class', {name:$('cname').value}); $('cname').value=''; }
function addStudents(c, box){ act('/api/students', {class:c, names:box.value}); box.value=''; }
function remove(c, s){ const t = prompt('This removes ' + c + '/' + s + ' and deletes their folder on the Jetson. Type the name to confirm:'); if (t === s) act('/api/remove', {class:c, student:s}); }
function removeClass(c){ const t = prompt('This removes the whole class ' + c + ' and deletes all the student folders. Type the class name to confirm:'); if (t === c) act('/api/remove_class', {class:c}); }
function copy(text){ navigator.clipboard && navigator.clipboard.writeText(text); }
function row(cells){ const tr = el('tr'); cells.forEach(c => tr.append(el('td', {}, c))); return tr; }
function head(cols){ const tr = el('tr'); cols.forEach(c => tr.append(el('th', {textContent:c}))); return el('thead', {}, tr); }
function render(s){
  $('where').textContent = s.host + '  (' + s.ip + ':' + s.port + ')'; $('when').textContent = new Date().toLocaleTimeString();
  const jets = $('jets'); jets.replaceChildren(head(['Jetson','IP address','State','Cameras','Students']));
  if (!s.jetsons.length) jets.append(row(['No Jetson yet','','','','']));
  s.jetsons.forEach(j => {
    const cams = j.cameras.length ? j.cameras.map(c => c.number + ': ' + c.name + (c.user ? ' (' + c.user + ')' : ' (free)')).join('  |  ') : 'no camera';
    const st = el('span', {className: j.online ? 'on' : 'off', textContent: j.online ? 'online' : 'offline (' + j.ago + ' s)'});
    jets.append(row([j.id, j.ip, el('span', {}, st, j.note ? el('span', {className:'warn', textContent:'  ' + j.note}) : ''), cams, String(j.students)]));
  });
  $('addjet').innerHTML = 'To add a Jetson, run this on it: <code>cd ~/Jetson-Orin-Nano-Super-Lab && bash setup-lab.sh ' + s.ip + ':' + s.port + ' ' + s.key + ' jetson-01</code> (use a different name for each Jetson)';
  const box = $('classes'); box.replaceChildren();
  if (!s.classes.length) box.append(el('section', {}, el('p', {className:'note', textContent:'No class yet. Make one above.'})));
  s.classes.forEach(c => {
    const t = el('table'); t.append(head(['Student','Jetson','Camera','Address for the student','PIN','State','']));
    c.students.forEach(st => {
      const jsel = el('select', {onchange: () => act('/api/assign', {class:c.name, student:st.name, jetson:jsel.value, camera:''})});
      jsel.append(el('option', {value:'', textContent:'(none)'}));
      s.jetsons.forEach(j => jsel.append(el('option', {value:j.id, textContent:j.id + (j.online ? '' : ' (offline)'), selected: j.id === st.jetson})));
      const jet = s.jetsons.find(j => j.id === st.jetson);
      const csel = el('select', {onchange: () => act('/api/assign', {class:c.name, student:st.name, jetson:st.jetson, camera:csel.value})});
      csel.append(el('option', {value:'', textContent:'(none)'}));
      if (jet) jet.cameras.forEach(k => { if (!k.user || k.user === c.name + '/' + st.name) csel.append(el('option', {value:String(k.number), textContent:k.number + ': ' + k.name, selected: k.number === st.camera})); });
      csel.disabled = !st.jetson;
      const addr = st.address ? el('span', {}, el('span', {className:'addr', textContent:st.address}), ' ', el('button', {textContent:'Copy', onclick:() => copy(st.address)})) : '';
      const state = el('span', {className: st.state === 'running' ? 'on' : (st.state === 'preparing' ? 'warn' : 'off'), textContent: st.state || '-'});
      const acts = el('span', {}, el('button', {textContent:'New PIN', onclick:() => act('/api/pin', {class:c.name, student:st.name})}), ' ', el('button', {textContent:'Remove', onclick:() => remove(c.name, st.name)}));
      t.append(row([st.name, jsel, csel, addr, el('span', {className:'addr', textContent:st.pin}), state, acts]));
    });
    if (!c.students.length) t.append(row(['No student yet','','','','','','']));
    const ta = el('textarea', {rows:1, cols:30, placeholder:'names, separated by commas'});
    const add = el('div', {}, ta, ' ', el('button', {className:'go', textContent:'Add students', onclick:() => addStudents(c.name, ta)}), ' ', el('button', {textContent:'Remove class', onclick:() => removeClass(c.name)}));
    box.append(el('section', {}, el('h2', {textContent:'Class ' + c.name + '  (' + c.students.length + ' students)'}), el('div', {className:'wrap'}, t), el('p', {}, add)));
  });
  $('pending').textContent = s.pending ? s.pending + ' folder(s) waiting to be deleted on a Jetson (the Jetson must be online).' : '';
}
async function refresh(){ if (busy) return; try { render(await api('/api/state')); } catch(e){} }
(async () => { const r = await fetch('/api/state'); if (r.ok){ show(true); render(await r.json()); } else show(false); setInterval(() => { if (!$('app').hidden && !document.activeElement.matches('textarea,input')) refresh(); }, 3000); })();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, kind="application/json", headers=()):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _authed(self):
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "lab_teacher" and v in sessions:
                return True
        return False

    def _json(self):
        try:
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        if self.path == "/api/state":
            if not self._authed():
                return self._send(401, '{"error":"login"}')
            with lock:
                return self._send(200, json.dumps(view(self.server.ip)))
        if self.path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        self._send(404, '{"error":"not found"}')

    def do_POST(self):
        body = self._json()
        if self.path == "/agent/hello":                       # a Jetson reports in and asks what to run
            if not hmac.compare_digest(self.headers.get("X-Key", ""), db["key"]):
                return self._send(403, '{"error":"wrong class key"}')
            with lock:
                return self._send(200, json.dumps(agent_hello(body)))
        if self.path == "/login":
            if check_password(str(body.get("password", ""))):
                token = secrets.token_urlsafe(24)
                sessions.add(token)
                return self._send(200, '{"ok":true}', headers=[("Set-Cookie", f"lab_teacher={token}; HttpOnly; SameSite=Strict; Path=/")])
            time.sleep(1)
            return self._send(403, '{"ok":false}')
        if not self._authed():
            return self._send(401, '{"error":"login"}')
        with lock:
            msg = self.api(body)
            save()
        self._send(200, json.dumps({"message": msg}))

    def api(self, b):
        cls, stu = clean(b.get("class", "")), clean(b.get("student", ""))
        if self.path == "/api/class":
            name = clean(b.get("name", ""))
            if not NAME.match(name):
                return "Use letters or numbers for the class name."
            db["classes"].setdefault(name, {"students": {}})
            return "Saved."
        if cls not in db["classes"]:
            return "There is no such class."
        students = db["classes"][cls]["students"]
        if self.path == "/api/students":
            added = 0
            for raw in re.split(r"[,\n;]", str(b.get("names", ""))):
                n = clean(raw)
                if NAME.match(n) and not n.isdigit() and n not in students:
                    students[n] = new_student(cls, n)
                    added += 1
            return "Saved." if added else "No new valid names (use letters or numbers)."
        if self.path == "/api/remove_class":
            for n in list(students):
                self.remove(cls, n)
            del db["classes"][cls]
            return "Saved."
        if stu not in students:
            return "There is no such student."
        if self.path == "/api/assign":
            return assign(cls, stu, str(b.get("jetson", "")), b.get("camera"))
        if self.path == "/api/pin":
            students[stu]["pin"] = f"{secrets.randbelow(1_000_000):06d}"
            return "Saved."
        if self.path == "/api/remove":
            self.remove(cls, stu)
            return "Saved."
        return "Unknown action."

    @staticmethod
    def remove(cls, stu):
        s = db["classes"][cls]["students"].pop(stu)
        for home in s.get("homes", []):                                  # the folder must be deleted on each Jetson it was made on
            db["pending_delete"].append({"jetson": home, "class": cls, "student": stu})


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)          # no slow host name lookup
        self.server_name, self.server_port = "teacher", self.server_address[1]


def demo():
    """A preview with made-up Jetsons and students, so you can see the page. Password: demo. Nothing is saved."""
    global DATA, STATE
    import tempfile
    DATA = tempfile.mkdtemp(prefix="myduino_demo_")
    STATE = os.path.join(DATA, "state.json")
    salt = secrets.token_bytes(16)
    db.update(password=salt.hex() + " " + _hash("demo", salt), key="demo1234")
    now = time.time()
    cams = lambda n: [{"number": i, "device": f"/dev/video{2 * i}", "name": "USB 2.0 Camera"} for i in range(n)]
    jetsons["jetson-01"] = dict(ip="192.168.0.234", seen=now, cameras=cams(3), running=[{"key": "a__amira"}, {"key": "a__ali"}], ready=True, note="")
    jetsons["jetson-02"] = dict(ip="192.168.0.235", seen=now, cameras=cams(2), running=[{"key": "a__budi"}], ready=True, note="")
    jetsons["jetson-03"] = dict(ip="192.168.0.236", seen=now - 300, cameras=cams(1), running=[], ready=True, note="")
    students = {}
    for name, jet, cam, port in (("amira", "jetson-01", 0, 8881), ("ali", "jetson-01", 1, 8882), ("budi", "jetson-02", 0, 8881),
                                 ("siti", "jetson-03", 0, 8881), ("hafiz", "", None, 0), ("dina", "", None, 0)):
        st = new_student("a", name)
        st.update(jetson=jet, camera=cam, port=port, ports={jet: port} if jet else {}, homes=[jet] if jet else [])
        students[name] = st
    db["classes"] = {"a": {"students": students}, "b": {"students": {"farid": new_student("b", "farid")}}}


def main():
    if "--demo" in sys.argv:
        demo()
    else:
        load()
    if not db["key"]:
        db["key"] = secrets.token_hex(4)
        save()
    if "--demo" in sys.argv:
        print("PREVIEW with made-up data. The password is: demo")
    elif not db["password"]:
        if not sys.stdin.isatty():
            sys.exit("Run this in a terminal once, to choose the teacher password.")
        set_password()
    elif "--password" in sys.argv:
        set_password()
    server = Server(("0.0.0.0", PORT), Handler)
    server.ip = my_ip()
    if "--demo" not in sys.argv:
        threading.Thread(target=saver, daemon=True).start()
    print(f"\nTeacher page:   http://{server.ip}:{PORT}/    (on this PC also http://localhost:{PORT}/)")
    print(f"Class key:      {db['key']}")
    print(f"On each Jetson: bash setup-lab.sh {server.ip}:{PORT} {db['key']} <name, for example jetson-01>")
    print("Open the teacher page in the browser and type the password. Close this window or press Ctrl + C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    if "--demo" not in sys.argv:
        with lock:
            save()


if __name__ == "__main__":
    main()
