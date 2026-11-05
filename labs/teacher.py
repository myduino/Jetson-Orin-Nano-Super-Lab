"""The teacher page of the Myduino lab:   lab teacher

Shows the classes, the students of each class, the port of each student's JupyterLab, who is working now
and which camera they use. The teacher can make a class and stop a session whose connection was lost.
Deleting a class or a student stays on the command line (lab clean), where it asks you to type the name.
"""
import getpass
import hashlib
import hmac
import json
import os
import re
import secrets
import socketserver
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8800
HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, "myduino-jetson-lab")
SHARE = os.path.join(HOME, ".lab_share")
LOCKS = os.path.join(HOME, ".lab_cameras")
PASSFILE = os.path.join(HOME, ".lab_teacher")
SYSFS = os.environ.get("LAB_SYSFS", "/sys/class/video4linux")
DEV = os.environ.get("LAB_DEV", "/dev")
NAME = re.compile(r"^[a-z0-9_]{1,20}$")

sessions = set()          # logged-in browsers (a random cookie each)
_cache = {}               # folder -> (time, size, last used), because walking a folder takes a moment


# ---------------------------------------------------------------- password
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
        with open(PASSFILE, "w") as f:
            f.write(salt.hex() + " " + _hash(a, salt) + "\n")
        os.chmod(PASSFILE, 0o600)
        return


def check_password(password):
    try:
        salt_hex, digest = open(PASSFILE).read().split()
    except (OSError, ValueError):
        return False
    return hmac.compare_digest(_hash(password, bytes.fromhex(salt_hex)), digest)


# ---------------------------------------------------------------- what is on the Jetson
def alive(pid):
    try:
        pid = int(pid)
        if pid <= 0:
            return False
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def read(path):
    try:
        return open(path).read().strip()
    except OSError:
        return ""


def folder_info(path):
    now = time.time()
    hit = _cache.get(path)
    if hit and now - hit[0] < 20:
        return hit[1], hit[2]
    size, newest = 0, 0.0
    for folder, _, files in os.walk(path):
        for name in files:
            try:
                st = os.lstat(os.path.join(folder, name))
            except OSError:
                continue
            size += st.st_size
            newest = max(newest, st.st_mtime)
    _cache[path] = (now, size, newest)
    return size, newest


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def cameras():
    found = []
    try:
        names = sorted((d for d in os.listdir(SYSFS) if d.startswith("video")), key=lambda d: int(d[5:]))
    except OSError:
        names = []
    for d in names:
        if read(os.path.join(SYSFS, d, "index")) != "0":
            continue
        found.append({"number": len(found), "device": os.path.join(DEV, d), "name": read(os.path.join(SYSFS, d, "name")) or "?"})
    return found


def camera_users():
    users = {}
    try:
        files = os.listdir(LOCKS)
    except OSError:
        return users
    for n in files:
        parts = read(os.path.join(LOCKS, n)).split()
        if len(parts) == 2 and alive(parts[1]):
            users[parts[0]] = n          # key -> camera number
    return users


def state(ip):
    cams = camera_users()
    classes = []
    try:
        class_names = sorted(d for d in os.listdir(ROOT) if not d.startswith("_") and os.path.isdir(os.path.join(ROOT, d)))
    except OSError:
        class_names = []
    for c in class_names:
        students = []
        try:
            names = sorted(d for d in os.listdir(os.path.join(ROOT, c)) if os.path.isdir(os.path.join(ROOT, c, d)))
        except OSError:
            names = []
        for s in names:
            key = f"{c}__{s}"
            path = os.path.join(ROOT, c, s)
            size, newest = folder_info(path)
            working = alive(read(os.path.join(SHARE, key + ".pid")))
            port = read(os.path.join(path, ".port"))
            link = ""
            if working:
                link = f"http://{ip}:{read(os.path.join(SHARE, key + '.port'))}/?token={read(os.path.join(SHARE, key + '.token'))}"
            students.append({"name": s, "port": port, "size": human(size), "working": working, "camera": cams.get(key, ""),
                             "last": time.strftime("%Y-%m-%d %H:%M", time.localtime(newest)) if newest else "-", "link": link})
        classes.append({"name": c, "students": students})
    owner_of = {number: key.replace("__", "/") for key, number in cams.items()}
    found = [dict(c, user=owner_of.get(str(c["number"]), "")) for c in cameras()]
    return {"ip": ip, "host": os.uname().nodename, "classes": classes, "cameras": found}


def my_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def lab(*args):
    r = subprocess.run(["bash", os.path.join(HERE, "lab.sh"), *args], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return (r.stdout + r.stderr).strip()


# ---------------------------------------------------------------- the page
PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Myduino teacher</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#f4f5f7;color:#1c2330}
header{background:#14213d;color:#fff;padding:14px 20px;display:flex;gap:16px;align-items:baseline;flex-wrap:wrap}
header h1{font-size:18px;margin:0} header span{opacity:.8;font-size:13px}
main{padding:16px 20px;max-width:1100px;margin:auto}
section{background:#fff;border-radius:10px;padding:14px 16px;margin:0 0 16px;box-shadow:0 1px 3px #0002}
h2{font-size:16px;margin:0 0 10px} table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #e6e8ee} th{font-size:12px;color:#5b6477;text-transform:uppercase}
.wrap{overflow-x:auto}
.on{color:#0a7a3b;font-weight:600} .off{color:#8a91a1}
button{font:inherit;padding:5px 10px;border-radius:6px;border:1px solid #b9c0cf;background:#fff;cursor:pointer}
button.go{background:#14213d;color:#fff;border-color:#14213d}
input{font:inherit;padding:6px 8px;border:1px solid #b9c0cf;border-radius:6px}
a{color:#1d4ed8} .note{color:#5b6477;font-size:13px}
#login{max-width:340px;margin:80px auto}
</style></head><body>
<div id="login" hidden><section><h2>Teacher password</h2>
<form onsubmit="login(event)"><input id="pw" type="password" autofocus> <button class="go">Open</button></form>
<p id="loginmsg" class="note"></p></section></div>
<div id="app" hidden>
<header><h1>Myduino Jetson Lab: teacher</h1><span id="where"></span><span id="when"></span></header>
<main>
<section><h2>Cameras</h2><div class="wrap"><table id="cams"></table></div></section>
<section><h2>Make a class</h2>
<form onsubmit="addClass(event)"><input id="cname" placeholder="class name, for example a" size="22"> <button class="go">Add class</button></form>
<p class="note">Students start with: <code>lab start &lt;name&gt; class &lt;class&gt; camera &lt;N&gt;</code>. Delete a class or a student with <code>lab clean</code> in the terminal.</p></section>
<div id="classes"></div>
</main></div>
<script>
const $ = id => document.getElementById(id);
function el(tag, props, ...kids){ const e = document.createElement(tag); Object.assign(e, props||{}); kids.forEach(k => e.append(k)); return e; }
async function api(path, body){
  const r = await fetch(path, body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {});
  if (r.status === 401){ show(false); throw new Error('login'); }
  return r.json();
}
function show(ok){ $('app').hidden = !ok; $('login').hidden = ok; }
async function login(e){ e.preventDefault();
  const r = await fetch('/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({password:$('pw').value})});
  if (r.ok){ show(true); refresh(); } else { $('loginmsg').textContent = 'Wrong password.'; } }
async function addClass(e){ e.preventDefault(); const r = await api('/api/class', {name:$('cname').value});
  alert(r.message); $('cname').value=''; refresh(); }
async function stop(c, s){ if (!confirm('Stop the JupyterLab of ' + c + '/' + s + ' and free the camera?')) return;
  const r = await api('/api/stop', {class:c, student:s}); alert(r.message); refresh(); }
function row(cells){ const tr = el('tr'); cells.forEach(c => tr.append(el('td', {}, c))); return tr; }
function head(cols){ const tr = el('tr'); cols.forEach(c => tr.append(el('th', {textContent:c}))); return el('thead', {}, tr); }
function render(s){
  $('where').textContent = s.host + '  (' + s.ip + ')'; $('when').textContent = new Date().toLocaleTimeString();
  const cams = $('cams'); cams.replaceChildren(head(['Camera','Device','Name','Used by']));
  if (!s.cameras.length) cams.append(row(['No USB camera found','','','']));
  s.cameras.forEach(c => cams.append(row([String(c.number), c.device, c.name, c.user || 'free'])));
  const box = $('classes'); box.replaceChildren();
  if (!s.classes.length) box.append(el('section', {}, el('p', {className:'note', textContent:'No class yet. Make one above.'})));
  s.classes.forEach(c => {
    const t = el('table'); t.append(head(['Student','Port','State','Camera','Folder','Last used','JupyterLab','']));
    c.students.forEach(st => {
      const state = el('span', {className: st.working ? 'on' : 'off', textContent: st.working ? 'working' : 'offline'});
      const link = st.link ? el('a', {href:st.link, target:'_blank', textContent:'open'}) : '';
      const btn = st.working ? el('button', {textContent:'Stop', onclick:() => stop(c.name, st.name)}) : '';
      t.append(row([st.name, st.port || '-', state, st.camera === '' ? '-' : st.camera, st.size, st.last, link, btn]));
    });
    if (!c.students.length) t.append(row(['No student yet','','','','','','','']));
    const online = c.students.filter(x => x.working).length;
    box.append(el('section', {}, el('h2', {textContent:'Class ' + c.name + '  (' + c.students.length + ' students, ' + online + ' working)'}), el('div', {className:'wrap'}, t)));
  });
}
async function refresh(){ try { render(await api('/api/state')); } catch(e){} }
(async () => { const r = await fetch('/api/state'); if (r.ok){ show(true); render(await r.json()); } else show(false); setInterval(() => { if (!$('app').hidden) refresh(); }, 3000); })();
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
            return self._send(200, json.dumps(state(self.server.ip)))
        if self.path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        self._send(404, '{"error":"not found"}')

    def do_POST(self):
        body = self._json()
        if self.path == "/login":
            if check_password(str(body.get("password", ""))):
                token = secrets.token_urlsafe(24)
                sessions.add(token)
                return self._send(200, '{"ok":true}', headers=[("Set-Cookie", f"lab_teacher={token}; HttpOnly; SameSite=Strict; Path=/")])
            time.sleep(1)
            return self._send(403, '{"ok":false}')
        if not self._authed():
            return self._send(401, '{"error":"login"}')
        if self.path == "/api/class":
            name = re.sub(r"[^a-z0-9_]", "_", str(body.get("name", "")).lower()).strip("_")[:20]
            if not NAME.match(name):
                return self._send(200, json.dumps({"message": "Use letters or numbers for the class name."}))
            return self._send(200, json.dumps({"message": lab("class", "add", name)}))
        if self.path == "/api/stop":
            c, s = str(body.get("class", "")), str(body.get("student", ""))
            if not (NAME.match(c) and NAME.match(s)):
                return self._send(200, json.dumps({"message": "Wrong class or student name."}))
            return self._send(200, json.dumps({"message": lab("stop", c, s)}))
        self._send(404, '{"error":"not found"}')


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)          # no slow host name lookup
        self.server_name, self.server_port = "jetson", self.server_address[1]


def main():
    os.makedirs(ROOT, exist_ok=True)
    if not os.path.exists(PASSFILE):
        if not sys.stdin.isatty():
            sys.exit("Run  lab teacher  in a terminal once, to choose the teacher password.")
        set_password()
    elif "--password" in sys.argv:
        set_password()
    server = Server(("0.0.0.0", PORT), Handler)
    server.ip = my_ip()
    print(f"Teacher page:  http://{server.ip}:{PORT}/   (also http://{os.uname().nodename}:{PORT}/)")
    print("Open it in the browser of your laptop and type the teacher password. Press Ctrl + C here to stop it.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
