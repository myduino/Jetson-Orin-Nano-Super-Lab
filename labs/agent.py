"""The Jetson agent of the Myduino lab. It runs on every Jetson as a service (setup-lab.sh installs it).

Every few seconds it tells the teacher server which Jetson this is, its IP address and its cameras, and asks which
students should work here. For each student it makes the folder ~/myduino-jetson-lab/<class>/<student> and starts
that student's JupyterLab on the port and with the PIN the teacher page shows, with the chosen camera. When the
teacher takes a student away, the agent stops that JupyterLab. Only the Python standard library is used.

    python3 labs/agent.py            (the service does this)
"""
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       # the course folder
HOME = os.path.expanduser("~")
CONFIG = os.path.join(HOME, ".lab_agent.json")
ROOT = os.path.join(HOME, "myduino-jetson-lab")
VENV = os.path.join(HOME, "venvs", "jetson")
SYSFS = os.environ.get("LAB_SYSFS", "/sys/class/video4linux")
DEV = os.environ.get("LAB_DEV", "/dev")
NAME = re.compile(r"^[a-z0-9_]{1,20}$")
EVERY = 5                                                               # seconds between two reports

running = {}          # key -> {"proc", "port", "pin", "camera", "started"}
deleted = []          # keys of folders deleted since the last report


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


def jupyter_path():
    return os.path.join(VENV, "bin", "jupyter")


# ---------------------------------------------------------------- a student's folder and JupyterLab
def prepare(home):
    for n in range(10):
        os.makedirs(os.path.join(home, f"lab{n}"), exist_ok=True)
    for d in ("models", ".jupyter", ".ipython", ".config"):
        os.makedirs(os.path.join(home, d), exist_ok=True)
    shutil.copyfile(os.path.join(HERE, "labs", "start_here.ipynb"), os.path.join(home, "Start_Here.ipynb"))
    labs = os.path.join(HERE, "labs")
    for folder in sorted(os.listdir(labs)):
        m = re.match(r"lab(\d)_", folder)
        if not m or not os.path.isdir(os.path.join(labs, folder)):
            continue
        for f in os.listdir(os.path.join(labs, folder)):
            if f.endswith(".ipynb"):
                dest = os.path.join(home, f"lab{m.group(1)}", f)
                if not os.path.exists(dest):                               # never overwrite a student's copy
                    shutil.copyfile(os.path.join(labs, folder, f), dest)


def student_env(home, cls, camera_device):
    env = dict(os.environ)
    env.update(
        VIRTUAL_ENV=VENV, PATH=os.path.join(VENV, "bin") + os.pathsep + env.get("PATH", ""),
        LAB_HOME=home, LAB_CLASS=cls, HISTFILE=os.path.join(home, ".bash_history"),
        JUPYTER_CONFIG_DIR=os.path.join(home, ".jupyter", "config"), JUPYTER_DATA_DIR=os.path.join(home, ".jupyter", "data"),
        JUPYTER_RUNTIME_DIR=os.path.join(home, ".jupyter", "runtime"), JUPYTERLAB_SETTINGS_DIR=os.path.join(home, ".jupyter", "settings"),
        JUPYTERLAB_WORKSPACES_DIR=os.path.join(home, ".jupyter", "workspaces"), IPYTHONDIR=os.path.join(home, ".ipython"),
        YOLO_CONFIG_DIR=os.path.join(home, ".config", "Ultralytics"), MPLCONFIGDIR=os.path.join(home, ".config", "matplotlib"),
    )
    env.pop("PYTHONHOME", None)
    if camera_device:
        env["LAB_CAMERA"] = camera_device
    else:
        env.pop("LAB_CAMERA", None)
    for key in ("JUPYTER_CONFIG_DIR", "JUPYTER_DATA_DIR", "JUPYTER_RUNTIME_DIR", "JUPYTERLAB_SETTINGS_DIR", "JUPYTERLAB_WORKSPACES_DIR", "YOLO_CONFIG_DIR", "MPLCONFIGDIR"):
        os.makedirs(env[key], exist_ok=True)
    return env


def start(cls, student, port, pin, camera):
    home = os.path.join(ROOT, cls, student)
    prepare(home)
    device = next((c["device"] for c in cameras() if c["number"] == camera), "") if camera is not None else ""
    log("start", f"{cls}/{student}", "port", port, "camera", camera if camera is not None else "-")
    out = open(os.path.join(home, ".jupyter", "server.log"), "ab")
    proc = subprocess.Popen(
        [jupyter_path(), "lab", "--no-browser", "--ip=0.0.0.0", f"--port={port}", "--ServerApp.port_retries=0",
         f"--ServerApp.token={pin}", "--ServerApp.allow_remote_access=True", "Start_Here.ipynb"],
        cwd=home, env=student_env(home, cls, device), stdout=out, stderr=out, start_new_session=True)
    running[f"{cls}__{student}"] = {"proc": proc, "port": port, "pin": pin, "camera": camera, "started": time.time()}


def stop(key):
    r = running.pop(key, None)
    if not r:
        return
    log("stop", key.replace("__", "/"))
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
    target = os.path.realpath(os.path.join(ROOT, cls, student))
    if os.path.dirname(os.path.dirname(target)) == os.path.realpath(ROOT) and os.path.isdir(target):
        shutil.rmtree(target, ignore_errors=True)
        log("deleted", f"{cls}/{student}")
    deleted.append(key)


def reconcile(plan):
    wanted = {}
    for p in plan:
        if NAME.match(str(p.get("class", ""))) and NAME.match(str(p.get("student", ""))):
            wanted[f"{p['class']}__{p['student']}"] = p
    for key in list(running):
        r = running[key]
        w = wanted.get(key)
        if w is None or r["proc"].poll() is not None or (r["port"], r["pin"], r["camera"]) != (w["port"], str(w["pin"]), w.get("camera")):
            gone = w is not None and r["proc"].poll() is not None
            stop(key)
            if gone and time.time() - r["started"] < 15:
                wanted[key]["_wait"] = True                                  # it stops at once: do not restart in a loop
    for key, w in wanted.items():
        if key not in running and not w.get("_wait"):
            try:
                start(w["class"], w["student"], int(w["port"]), str(w["pin"]), w.get("camera"))
            except OSError as error:
                log("cannot start", key, error)


# ---------------------------------------------------------------- talking to the teacher server
def hello(cfg):
    host, _, _ = cfg["teacher"].partition(":")
    body = {
        "id": cfg.get("id") or re.sub(r"[^a-z0-9_]", "_", socket.gethostname().lower()), "ip": my_ip(host), "cameras": cameras(),
        "running": [{"key": k, "port": r["port"], "alive": r["proc"].poll() is None} for k, r in running.items()],
        "deleted": list(deleted), "ready": os.path.exists(jupyter_path()),
        "note": "" if os.path.exists(jupyter_path()) else "JupyterLab is missing. Run setup-lab.sh again.",
    }
    req = urllib.request.Request(f"http://{cfg['teacher']}/agent/hello", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "X-Key": cfg["key"]})
    with urllib.request.urlopen(req, timeout=6) as r:
        answer = json.load(r)
    del deleted[:]
    return answer


def main():
    try:
        cfg = json.load(open(CONFIG))
    except (OSError, ValueError):
        sys.exit(f"No settings in {CONFIG}. Run setup-lab.sh <teacher address> <class key>.")
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    log("agent started; teacher", cfg["teacher"])
    shown = ""
    try:
        while True:
            try:
                answer = hello(cfg)
                for d in answer.get("delete", []):
                    delete_folder(str(d.get("class", "")), str(d.get("student", "")))
                reconcile(answer.get("plan", []))
                shown = ""
            except (urllib.error.URLError, OSError, ValueError) as error:
                if str(error) != shown:                                      # say it once, not every 5 seconds
                    log("cannot reach the teacher server:", error)
                    shown = str(error)
            time.sleep(EVERY)
    finally:
        for key in list(running):
            stop(key)


if __name__ == "__main__":
    main()
