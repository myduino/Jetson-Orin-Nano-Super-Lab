"""The Jetson agent of the Myduino lab. It runs on every Jetson as a service (labs-setup.sh installs it).

Every few seconds it tells the teacher server which Jetson this is, its IP address and its cameras, and asks which
students should work here. For each student it makes the folder ~/myduino-jetson-lab/<class>/<student> and starts
that student's JupyterLab on the port and with the PIN the teacher page shows, with the chosen camera. When the
teacher takes a student away, the agent stops that JupyterLab. Each student has their own Python environment in
their folder (.venv), made by the agent the first time. Only the Python standard library is used.

    python3 labs-student/agent.py            (the service does this)
"""
import base64
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       # the course folder
HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, "myduino-jetson-lab")                          # everything of the lab: ROOT/<class>/<student>, ROOT/.agent.json
CONFIG = os.environ.get("LAB_AGENT_CONFIG", os.path.join(ROOT, ".agent.json"))
SYSFS = os.environ.get("LAB_SYSFS", "/sys/class/video4linux")
DEV = os.environ.get("LAB_DEV", "/dev")
MAX_LABS = 45                                                                     # lab0 ... lab44 folders in each student's folder
NAME = re.compile(r"^[a-z0-9_]{1,20}$")
GRACE = 15 * 60                                                         # seconds without the teacher before every student session is closed
EVERY = 5                                                               # seconds between two reports

running = {}          # key -> {"proc", "port", "pin", "camera", "started"}
preparing = {}        # key -> time when the student's Python environment is being made
failed = {}           # key -> (time, message) of the last failed attempt to make it
deleted = []          # keys of folders deleted since the last report
renamed = []          # "old>new" of class folders renamed since the last report
rename_failed = {}    # "old>new" -> message, shown to the teacher until it works


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- the Jetson
def read(path):
    try:
        return open(path).read().strip()
    except OSError:
        return ""


def cameras():
    """USB cameras in order: the capture node of each camera (sysfs index 0), numbered 0, 1, 2."""
    found = []
    try:
        names = sorted((d for d in os.listdir(SYSFS) if d.startswith("video")), key=lambda d: int(d[5:]))
    except OSError:
        return found
    for d in names:
        if read(os.path.join(SYSFS, d, "index")) == "0":
            found.append({"number": len(found), "device": os.path.join(DEV, d), "name": read(os.path.join(SYSFS, d, "name")) or "?"})
    return found


def my_ip(teacher_host):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((teacher_host, 9))                     # sends nothing: finds the address that reaches the teacher PC
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def venv_of(home):
    return os.path.join(home, ".venv")


def venv_ready(home):
    return os.path.exists(os.path.join(venv_of(home), ".ready"))


def make_venv(key, home):
    """Make the student's own Python environment (about 2 to 3 minutes). Runs in a thread, so other students are not held up."""
    venv = venv_of(home)
    os.makedirs(os.path.join(home, ".jupyter"), exist_ok=True)
    with open(os.path.join(home, ".jupyter", "prepare.log"), "ab") as out:
        env = student_env(home, os.path.basename(os.path.dirname(home)), "")     # pip and python write only inside the folder

        def run(*cmd):
            subprocess.run(cmd, stdout=out, stderr=subprocess.STDOUT, check=True, env=env, cwd=home)
        try:
            log("making the Python environment of", key.replace("__", "/"))
            shutil.rmtree(venv, ignore_errors=True)
            run("/usr/bin/python3", "-m", "venv", "--system-site-packages", venv)
            run(os.path.join(venv, "bin", "pip"), "install", "--upgrade", "pip")
            run(os.path.join(venv, "bin", "pip"), "install", "numpy<2", "jupyterlab", "ipywidgets", "openpyxl", "paho-mqtt")
            site = subprocess.run([os.path.join(venv, "bin", "python"), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
                                  capture_output=True, text=True, check=True, env=env).stdout.strip()
            # OpenCV on the Jetson makes NumPy print a harmless warning: hide only that one message.
            with open(os.path.join(site, "myduino_quiet.pth"), "w") as f:
                f.write('import warnings; warnings.filterwarnings("ignore", message="The value of the smallest subnormal")\n')
            with open(os.path.join(site, "myduino_labs.pth"), "w") as f:       # the notebooks import labview
                f.write(os.path.join(HERE, "labs-student") + "\n")
            open(os.path.join(venv, ".ready"), "w").close()
            failed.pop(key, None)
            log("Python environment ready:", key.replace("__", "/"))
        except (subprocess.CalledProcessError, OSError) as error:
            shutil.rmtree(venv, ignore_errors=True)
            failed[key] = (time.time(), f"Could not make the Python environment ({error}). See .jupyter/prepare.log in the student folder.")
            log("failed:", key, error)
        finally:
            preparing.pop(key, None)


# ---------------------------------------------------------------- a student's folder and JupyterLab
def prepare(home):
    for n in range(MAX_LABS):
        os.makedirs(os.path.join(home, f"lab{n}"), exist_ok=True)
    for d in ("models", ".jupyter", ".ipython", ".config", ".tmp"):
        os.makedirs(os.path.join(home, d), exist_ok=True)
    # JupyterLab saves the open notebook every 20 seconds, so the teacher's Progress tab is never far behind (the default is 2 minutes).
    dm = os.path.join(home, ".jupyter", "settings", "@jupyterlab", "docmanager-extension")
    os.makedirs(dm, exist_ok=True)
    if not os.path.exists(os.path.join(dm, "plugin.jupyterlab-settings")):          # a setting the student made is kept
        with open(os.path.join(dm, "plugin.jupyterlab-settings"), "w") as f:
            json.dump({"autosaveInterval": 20}, f)
    # The student's own bash: the Terminal tab of their JupyterLab starts in their folder, with their environment on.
    rc = os.path.join(home, ".bashrc")
    if "# myduino-lab" not in read(rc):
        with open(rc, "a") as f:
            f.write('# myduino-lab\n[ -f "$HOME/.venv/bin/activate" ] && source "$HOME/.venv/bin/activate"\n'
                    'cd "$HOME" 2>/dev/null\n')
    if "alias lab=" in read(rc):                                   # the old lab command is gone
        with open(rc, "w") as f:
            f.write("".join(l for l in read(rc).splitlines(True) if not l.startswith("alias lab=")))
    with open(os.path.join(home, ".bash_profile"), "w") as f:
        f.write('[ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"\n')
    for pth in glob.glob(os.path.join(home, ".venv", "lib", "python*", "site-packages", "myduino_labs.pth")):   # keep the path right if the course folder moves
        with open(pth, "w") as f:
            f.write(os.path.join(HERE, "labs-student") + "\n")
    shutil.copyfile(os.path.join(HERE, "labs-student", "start_here.ipynb"), os.path.join(home, "Start_Here.ipynb"))
    sync_notebooks(home)


def file_hash(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def sync_notebooks(home):
    """Gives the student the notebooks of the course. A new lab is copied. A notebook the student never changed is replaced by the newer
    version of the course. A notebook the student changed is kept as it is, and the newer version is added next to it as "<name> (new).ipynb"."""
    labs = os.path.join(HERE, "labs-student")
    book = os.path.join(home, ".delivered.json")                   # what the student was given: file -> {"sent": hash of that version, "new": hash of the newer version put next to it}
    try:
        given = json.load(open(book))
    except (OSError, ValueError):
        given = {}
    for folder in sorted(os.listdir(labs)):
        m = re.match(r"lab(\d{1,2})_", folder)
        if not m or not os.path.isdir(os.path.join(labs, folder)):
            continue
        for f in os.listdir(os.path.join(labs, folder)):
            if not f.endswith(".ipynb"):
                continue
            src, dest = os.path.join(labs, folder, f), os.path.join(home, f"lab{m.group(1)}", f)
            rel = f"lab{m.group(1)}/{f}"
            new, rec = file_hash(src), given.get(rel, {})
            if not os.path.exists(dest):
                shutil.copyfile(src, dest)
                given[rel] = {"sent": new}
            elif file_hash(dest) == new:
                given[rel] = {"sent": new}                          # the student has the current version
            elif rec.get("sent") and file_hash(dest) == rec["sent"]:
                shutil.copyfile(src, dest)                          # never changed by the student: the newer version replaces it
                given[rel] = {"sent": new}
            elif rec.get("new") != new:
                shutil.copyfile(src, dest[:-6] + " (new).ipynb")    # changed by the student: their work stays, the newer version comes next to it
                given[rel] = {**rec, "new": new}
    tmp = book + ".tmp"
    with open(tmp, "w") as f:
        json.dump(given, f)
    os.replace(tmp, book)

def student_env(home, cls, camera_device, pin=None, mqtt_port=None, lab=None):
    env = dict(os.environ)
    venv = venv_of(home)
    env.update(
        # HOME is the student folder, so everything the programs write (settings, caches, history, temporary files)
        # lands in the student's own folder and nothing is left anywhere else on the Jetson.
        LD_LIBRARY_PATH=os.path.join(venv, "lib", "python3.10", "site-packages", "nvidia", "cu12", "lib") + os.pathsep + env.get("LD_LIBRARY_PATH", ""),
        HOME=home, TMPDIR=os.path.join(home, ".tmp"), PIP_CACHE_DIR=os.path.join(ROOT, ".cache", "pip"), LAB_ROOT=ROOT,
        VIRTUAL_ENV=venv, PATH=os.path.join(venv, "bin") + os.pathsep + env.get("PATH", ""),
        LAB_HOME=home, LAB_CLASS=cls, HISTFILE=os.path.join(home, ".bash_history"),
        JUPYTER_CONFIG_DIR=os.path.join(home, ".jupyter", "config"), JUPYTER_DATA_DIR=os.path.join(home, ".jupyter", "data"),
        JUPYTER_RUNTIME_DIR=os.path.join(home, ".jupyter", "runtime"), JUPYTERLAB_SETTINGS_DIR=os.path.join(home, ".jupyter", "settings"),
        JUPYTERLAB_WORKSPACES_DIR=os.path.join(home, ".jupyter", "workspaces"), IPYTHONDIR=os.path.join(home, ".ipython"),
        YOLO_CONFIG_DIR=os.path.join(home, ".config", "Ultralytics"), MPLCONFIGDIR=os.path.join(home, ".config", "matplotlib"),
    )
    env.pop("PYTHONHOME", None)
    if lab is not None:                                    # each lab keeps its own JupyterLab layout (the open tabs of the lab before do not come back)
        env["JUPYTERLAB_WORKSPACES_DIR"] = os.path.join(home, ".jupyter", "workspaces", f"lab{lab}")
        os.makedirs(env["JUPYTERLAB_WORKSPACES_DIR"], exist_ok=True)
    if pin is not None and mqtt_port:                      # the student's own MQTT broker (see the MQTT section)
        env.update(LAB_MQTT_HOST=MQTT_HOST[0], LAB_MQTT_PORT=str(mqtt_port), LAB_MQTT_USER=os.path.basename(home), LAB_MQTT_PASS=str(pin))
    if camera_device:
        env["LAB_CAMERA"] = camera_device
    else:
        env.pop("LAB_CAMERA", None)
    for key in ("PIP_CACHE_DIR", "TMPDIR", "JUPYTER_CONFIG_DIR", "JUPYTER_DATA_DIR", "JUPYTER_RUNTIME_DIR", "JUPYTERLAB_SETTINGS_DIR", "JUPYTERLAB_WORKSPACES_DIR", "YOLO_CONFIG_DIR", "MPLCONFIGDIR"):
        os.makedirs(env[key], exist_ok=True)
    return env


def start(cls, student, port, pin, camera, mqtt_port=None, lab=None):
    home = os.path.join(ROOT, cls, student)
    prepare(home)
    mqtt_port = mqtt_port or int(port) - 7000
    device = next((c["device"] for c in cameras() if c["number"] == camera), "") if camera is not None else ""
    # The teacher started one lab: JupyterLab shows only that lab's folder and opens its notebook. Without a lab it shows the whole folder (old way).
    root, first = home, "Start_Here.ipynb"
    if lab is not None and os.path.isdir(os.path.join(home, f"lab{lab}")):
        root = os.path.join(home, f"lab{lab}")
        books = sorted(f for f in os.listdir(root) if f.endswith(".ipynb"))
        first = books[0] if books else ""
    log("start", f"{cls}/{student}", "port", port, "lab", lab if lab is not None else "-", "camera", camera if camera is not None else "-")
    out = open(os.path.join(home, ".jupyter", "server.log"), "ab")
    proc = subprocess.Popen(
        [os.path.join(venv_of(home), "bin", "jupyter"), "lab", "--no-browser", "--ip=0.0.0.0", f"--port={port}", "--ServerApp.port_retries=0",
         f"--ServerApp.token={pin}", "--ServerApp.allow_remote_access=True", f"--ServerApp.root_dir={root}"] + ([first] if first else []),
        cwd=root, env=student_env(home, cls, device, pin, mqtt_port, lab), stdout=out, stderr=out, start_new_session=True)
    running[f"{cls}__{student}"] = {"proc": proc, "port": port, "pin": pin, "camera": camera, "lab": lab, "started": time.time(),
                                    "mqtt": mqtt_start(home, student, pin, mqtt_port), "mqtt_port": mqtt_port}


def stop(key):
    r = running.pop(key, None)
    if not r:
        return
    log("stop", key.replace("__", "/"))
    mqtt_stop(r.get("mqtt"))
    try:
        os.killpg(r["proc"].pid, signal.SIGTERM)
        r["proc"].wait(timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        try:
            os.killpg(r["proc"].pid, signal.SIGKILL)
        except OSError:
            pass


def delete_folder(cls, student):
    if not (NAME.match(cls) and NAME.match(student)):
        return
    key = f"{cls}__{student}"
    stop(key)
    failed.pop(key, None)
    target = os.path.realpath(os.path.join(ROOT, cls, student))
    if os.path.dirname(os.path.dirname(target)) == os.path.realpath(ROOT) and os.path.isdir(target):
        shutil.rmtree(target, ignore_errors=True)
        log("deleted", f"{cls}/{student}")
        try:
            os.rmdir(os.path.join(ROOT, cls))                       # the class folder goes too, once the last student is gone
        except OSError:
            pass
    deleted.append(key)


def rename_class(old, new):
    """The teacher renamed a class: move the class folder, then fix the paths inside the students' Python environments."""
    if not (NAME.match(old) and NAME.match(new)) or old == new:
        return
    tag = f"{old}>{new}"
    src, dst = os.path.join(ROOT, old), os.path.join(ROOT, new)
    for key in [k for k in running if k.startswith(old + "__")]:
        stop(key)
    try:
        if os.path.isdir(src):
            if os.path.isdir(dst):
                os.rmdir(dst)                                      # an empty folder of an old class of that name is fine; a full one raises
            os.rename(src, dst)
            for student in os.listdir(dst):
                fix_paths(os.path.join(dst, student), os.path.join(src, student), os.path.join(dst, student))
            log("renamed class", old, "to", new)
        rename_failed.pop(tag, None)
        renamed.append(tag)
    except OSError as error:
        if rename_failed.get(tag) != str(error):
            log("cannot rename class", old, "to", new, ":", error)
        rename_failed[tag] = str(error)


def fix_paths(home, old_home, new_home):
    """A Python environment has its own folder path inside its scripts. After a move, write the new path."""
    venv = os.path.join(home, ".venv")
    if not os.path.isdir(venv):
        return
    old_b, new_b = old_home.encode(), new_home.encode()
    for folder, _, files in os.walk(os.path.join(venv, "bin")):
        for name in files:
            path = os.path.join(folder, name)
            try:
                if os.path.islink(path) or os.path.getsize(path) > 2_000_000:
                    continue
                with open(path, "rb") as f:
                    data = f.read()
                if old_b in data and b"\0" not in data[:512]:       # a script, not a program
                    with open(path, "wb") as f:
                        f.write(data.replace(old_b, new_b))
            except OSError:
                pass
    cfg = os.path.join(venv, "pyvenv.cfg")
    try:
        text = open(cfg).read()
        if old_home in text:
            open(cfg, "w").write(text.replace(old_home, new_home))
    except OSError:
        pass


def reconcile(plan):
    wanted = {}
    for p in plan:
        if NAME.match(str(p.get("class", ""))) and NAME.match(str(p.get("student", ""))):
            wanted[f"{p['class']}__{p['student']}"] = p
    for key in list(running):
        r = running[key]
        w = wanted.get(key)
        if w is None or r["proc"].poll() is not None or (r["port"], r["pin"], r["camera"], r.get("lab")) != (w["port"], str(w["pin"]), w.get("camera"), w.get("lab")):
            gone = w is not None and r["proc"].poll() is not None
            stop(key)
            if gone and time.time() - r["started"] < 15:
                wanted[key]["_wait"] = True                                  # it stops at once: do not restart in a loop
    for key, r in running.items():                                           # a broker that stopped by itself starts again
        if r.get("mqtt") is not None and r["mqtt"].poll() is not None:
            home = os.path.join(ROOT, *key.split("__", 1))
            r["mqtt"] = mqtt_start(home, key.split("__", 1)[1], r["pin"], r["mqtt_port"])
    for key, w in wanted.items():
        home = os.path.join(ROOT, w["class"], w["student"])
        if key not in running and not venv_ready(home):            # the student's own Python environment first
            if key not in preparing and time.time() - failed.get(key, (0, ""))[0] > 60:
                preparing[key] = time.time()
                threading.Thread(target=make_venv, args=(key, home), daemon=True).start()
            continue
        if key not in running and not w.get("_wait"):
            try:
                start(w["class"], w["student"], int(w["port"]), str(w["pin"]), w.get("camera"), w.get("mqtt_port"), w.get("lab"))
            except OSError as error:
                log("cannot start", key, error)


# ---------------------------------------------------------------- MQTT broker of each student (ESP32 boards, phone apps)
MQTT_HOST = [""]                  # the address of this Jetson as the teacher sees it (set by hello)


def mqtt_ready():
    return bool(shutil.which("mosquitto") and shutil.which("mosquitto_passwd"))


def mqtt_start(home, user, pin, port):
    """The student's own MQTT broker, on its own port like their JupyterLab: user = the student's name, password = the PIN.
    It is a program of the agent (no sudo needed) and stops with the student's lab."""
    if not mqtt_ready():
        return None
    folder = os.path.join(home, ".mqtt")
    os.makedirs(folder, exist_ok=True)
    passwd, conf = os.path.join(folder, "passwd"), os.path.join(folder, "mosquitto.conf")
    try:
        subprocess.run(["mosquitto_passwd", "-c", "-b", passwd, user, str(pin)], check=True, capture_output=True)
        with open(conf, "w") as f:
            f.write(f"listener {port} 0.0.0.0\nallow_anonymous false\npassword_file {passwd}\npersistence false\n")
        for f in (passwd, conf):
            os.chmod(f, 0o600)
        return subprocess.Popen(["mosquitto", "-c", conf], stdout=open(os.path.join(folder, "mosquitto.log"), "ab"), stderr=subprocess.STDOUT,
                                start_new_session=True)
    except (subprocess.CalledProcessError, OSError) as error:
        log("cannot start the MQTT broker of", user, error)
        return None


def mqtt_stop(proc):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


# ---------------------------------------------------------------- progress: read from the students' saved notebooks
progress_at, progress_last = 0, {}
progress_cache = {}     # notebook path -> (mtime, done, total, errors)


def notebook_progress(path):
    try:
        mtime = os.path.getmtime(path)
        hit = progress_cache.get(path)
        if hit and hit[0] == mtime:
            return hit
        done = total = errors = 0
        for c in json.load(open(path)).get("cells", []):
            if c.get("cell_type") != "code" or not "".join(c.get("source", [])).strip():
                continue
            total += 1
            if c.get("execution_count") is not None:
                done += 1
            if any(o.get("output_type") == "error" for o in c.get("outputs", [])):
                errors += 1
        progress_cache[path] = hit = (mtime, done, total, errors)
        return hit
    except (OSError, ValueError):
        return None


live_sent = {}        # key -> modified time of the last live picture sent


def live_report():
    """Small pictures of the students' running camera views (labview writes .tmp/live.jpg about every 1.5 seconds)."""
    out = {}
    for key in list(running)[:8]:
        cls, _, stu = key.partition("__")
        path = os.path.join(ROOT, cls, stu, ".tmp", "live.jpg")
        try:
            mtime = os.stat(path).st_mtime
            if time.time() - mtime > 8:
                live_sent.pop(key, None)
                continue
            if live_sent.get(key) == mtime:
                out[key] = ""                                  # same picture as before: the teacher keeps the one it has
                continue
            with open(path, "rb") as f:
                data = f.read()
            if len(data) < 250000:
                out[key] = base64.b64encode(data).decode()
                live_sent[key] = mtime
        except OSError:
            live_sent.pop(key, None)
    return out


def progress_report():
    out = {}
    try:
        classes = [c for c in os.listdir(ROOT) if NAME.match(c) and os.path.isdir(os.path.join(ROOT, c))]
    except OSError:
        return out
    for cls in classes:
        for stu in os.listdir(os.path.join(ROOT, cls)):
            home = os.path.join(ROOT, cls, stu)
            if not NAME.match(stu) or not os.path.isdir(home):
                continue
            labs, last = {}, 0
            for n in range(MAX_LABS):
                for f in glob.glob(os.path.join(home, f"lab{n}", "*.ipynb")):
                    p = notebook_progress(f)
                    if p and p[2]:
                        labs[str(n)] = [p[1], p[2], p[3]]
                        if p[1]:
                            last = max(last, p[0])
            out[f"{cls}__{stu}"] = {"labs": labs, "idle": int(time.time() - last) if last else None}
    return out


# ---------------------------------------------------------------- talking to the teacher server
def course_version():
    """The commit of the course folder on this Jetson (the teacher compares it with the newest one on GitHub)."""
    try:
        head = read(os.path.join(HERE, ".git", "HEAD")).strip()
        if head.startswith("ref:"):
            head = read(os.path.join(HERE, ".git", head[4:].strip())).strip()
        return head[:40]
    except Exception:
        return ""


def hello(cfg):
    global progress_at, progress_last
    host, _, _ = cfg["teacher"].partition(":")
    MQTT_HOST[0] = my_ip(host)
    if time.time() - progress_at > 9:                                # notebooks are read every 10 seconds, not every 5
        progress_at, progress_last = time.time(), progress_report()
    body = {
        "id": cfg.get("id") or re.sub(r"[^a-z0-9_]", "_", socket.gethostname().lower()), "ip": MQTT_HOST[0], "cameras": cameras(),
        "running": [{"key": k, "port": r["port"], "alive": r["proc"].poll() is None} for k, r in running.items()],
        "progress": progress_last, "live": live_report(), "deleted": list(deleted), "renamed": list(renamed), "preparing": list(preparing), "ready": True, "course": course_version(),
        "note": next(iter(m for _, m in failed.values()), "") or ("MQTT is not installed on this Jetson. Click Update on the Jetsons page." if running and not mqtt_ready() else "") or next(iter(f"Could not rename a class folder: {m}" for m in rename_failed.values()), ""),
    }
    req = urllib.request.Request(f"http://{cfg['teacher']}/agent/hello", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "X-Key": cfg["key"]})
    with urllib.request.urlopen(req, timeout=6) as r:
        answer = json.load(r)
    del deleted[:]
    del renamed[:]
    return answer


def main():
    try:
        cfg = json.load(open(CONFIG))
    except (OSError, ValueError):
        sys.exit(f"No settings in {CONFIG}. Run labs-setup.sh <teacher address> <class key>.")
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    log("agent started; teacher", cfg["teacher"])
    shown = ""
    last_ok = time.time()
    try:
        while True:
            try:
                answer = hello(cfg)
                last_ok = time.time()
                for r in answer.get("rename", []):
                    rename_class(str(r.get("from", "")), str(r.get("to", "")))
                for d in answer.get("delete", []):
                    delete_folder(str(d.get("class", "")), str(d.get("student", "")))
                reconcile(answer.get("plan", []))
                shown = ""
            except (urllib.error.URLError, OSError, ValueError) as error:
                if str(error) != shown:                                      # say it once, not every 5 seconds
                    log("cannot reach the teacher server:", error)
                    shown = str(error)
                if running and time.time() - last_ok > GRACE:                # the teacher PC is gone: close the lab
                    log("no news from the teacher for", GRACE // 60, "minutes: stopping all student sessions")
                    for key in list(running):
                        stop(key)
            time.sleep(EVERY)
    finally:
        for key in list(running):
            stop(key)


if __name__ == "__main__":
    main()
