"""Camera and live-view helpers for the Myduino labs.

open_camera()  opens the camera your teacher chose for you on the teacher page
live()         live picture inside a notebook, with Stop and Save buttons
sudo_login()   asks for your password once, so "sudo" works in notebook cells
build_lock()   one TensorRT build at a time on the Jetson (the 8 GB memory fits one)
setup_begin()  one student at a time runs the Lab 0 install (setup_end() lets the next one in)
"""
import getpass
import os
import shutil
import stat
import subprocess
import tempfile
import threading
import time

import cv2


# ---------------------------------------------------------------- camera
def camera_source():
    """The camera of this student: a /dev/videoN path chosen on the teacher page, or 0 when nothing was chosen."""
    choice = os.environ.get("LAB_CAMERA", "")
    if not choice:
        return 0
    return int(choice) if choice.isdigit() else choice


def open_camera(size=(640, 480), mjpg=True):
    """Open the camera. size=None keeps the default size of the camera."""
    cap = cv2.VideoCapture(camera_source(), cv2.CAP_V4L2)
    if mjpg:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    if size:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
    if not cap.isOpened():
        raise SystemExit("Cannot open the camera. Check the USB cable, close other programs that use it, "
                         "and ask your teacher to check your camera on the teacher page")
    return cap


# ---------------------------------------------------------------- sudo in notebooks
def sudo_login():
    """Ask for your password once (it is not shown and not saved in the notebook).

    After this, a cell such as   !sudo apt update   works: a notebook has no terminal where sudo could ask.
    The password lives only in this notebook's kernel. Restarting the kernel forgets it.
    """
    folder = tempfile.mkdtemp(prefix="labsudo_")
    import atexit
    atexit.register(shutil.rmtree, folder, True)        # the helper folder goes away with the kernel
    os.chmod(folder, stat.S_IRWXU)
    ask = os.path.join(folder, "askpass")
    shim = os.path.join(folder, "sudo")
    with open(ask, "w") as f:
        f.write('#!/bin/sh\nprintf "%s\\n" "$LAB_SUDO_PW"\n')
    with open(shim, "w") as f:
        f.write('#!/bin/sh\nexec /usr/bin/sudo -A "$@"\n')
    os.chmod(ask, stat.S_IRWXU)
    os.chmod(shim, stat.S_IRWXU)
    os.environ["LAB_SUDO_PW"] = getpass.getpass("Password of the Jetson: ")
    os.environ["SUDO_ASKPASS"] = ask
    os.environ["PATH"] = folder + os.pathsep + os.environ["PATH"]
    ok = subprocess.run(["sudo", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if ok:
        print("sudo is ready.")
    else:
        os.environ.pop("LAB_SUDO_PW", None)
        print("That password was not accepted. Run this cell again.")


# ---------------------------------------------------------------- taking turns
def _lock_path(name):
    """Locks shared by all the students of this Jetson live in the lab folder (a student's ~ is their own folder)."""
    root = os.environ.get("LAB_ROOT") or os.path.join(os.path.expanduser("~"), "myduino-jetson-lab")
    folder = os.path.join(root, ".locks")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, name)


class _Lock:
    """A lock shared by all students of this Jetson. A folder is the lock; its owner file says who has it."""
    path = ""
    waiting = ""

    def _pid(self):
        return os.getpid()

    def __enter__(self):
        me = f"{os.path.basename(os.environ.get('LAB_HOME', 'student'))} {self._pid()}"
        shown = False
        while True:
            try:
                os.mkdir(self.path)
                break
            except FileExistsError:
                try:
                    owner = open(os.path.join(self.path, "owner")).read().split()
                    if " ".join(owner) == me:
                        return self                           # this student already holds it
                    os.kill(int(owner[-1]), 0)                # still alive?
                except (OSError, ValueError, IndexError):
                    shutil.rmtree(self.path, ignore_errors=True)   # left behind by a closed session
                    continue
                if not shown:
                    print(f"{owner[0]} is {self.waiting} now. {self.reason} so you wait here.", flush=True)
                    shown = True
                time.sleep(10)
        with open(os.path.join(self.path, "owner"), "w") as f:
            f.write(me + "\n")
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.path, ignore_errors=True)


class build_lock(_Lock):
    """with build_lock():  ...   Building a TensorRT engine uses most of the memory, so students take turns."""
    path = property(lambda self: _lock_path("build.lock"))
    waiting = "building an engine"
    reason = "Only one build at a time fits in the 8 GB memory,"


_setup = None


def setup_begin():
    """Lab 0, Part 0: one student at a time installs the system programs (two apt installs would block each other)."""
    global _setup

    class setup_lock(_Lock):
        path = property(lambda self: _lock_path("setup.lock"))
        waiting = "installing the course packages"
        reason = "Two installs at the same time would break each other,"

        def _pid(self):
            return os.getppid()          # the JupyterLab server, so a kernel restart keeps the lock

    _setup = setup_lock().__enter__()
    return True


def setup_end():
    """Let the next student install. Works after a kernel restart too: it looks at the lock file, not at memory."""
    global _setup
    lock = _lock_path("setup.lock")
    me = f"{os.path.basename(os.environ.get('LAB_HOME', 'student'))} {os.getppid()}"
    try:
        if open(os.path.join(lock, "owner")).read().split() == me.split():
            shutil.rmtree(lock, ignore_errors=True)
    except OSError:
        pass
    _setup = None
    print("Setup lock released.")


# ---------------------------------------------------------------- notebooks
class LiveView:
    """Live video inside a notebook.

    process(frame, state) gets each camera picture and returns the picture to show.
    state holds the values of your controls and "fps". controls is a dict:
        {"Mode": ["normal", "gray"]}          a drop-down list
        {"Confidence": (0.05, 0.95, 0.05, 0.4)}   a slider: (min, max, step, start)
    actions is a dict of extra buttons: {"Start": function}. The function gets state when the button is pressed.
    """
    _active = None

    def __init__(self, process, controls=None, width=640, size=(640, 480), mjpg=True, actions=None):
        self.process = process
        self.controls = controls or {}
        self.actions = actions or {}
        self.width = width
        self.size = size
        self.mjpg = mjpg
        self.state = {"fps": 0.0}
        self._stop = threading.Event()
        self._thread = None
        self._last = None
        self._saved = 0
        self._shared = 0

    def start(self):
        import ipywidgets as widgets
        from IPython.display import display
        if LiveView._active is not None:
            LiveView._active.stop()          # running this cell again: let go of the camera first
        LiveView._active = self
        self._img = widgets.Image(format="jpeg", width=self.width)
        self._status = widgets.Label(value="Starting the camera...")
        stop = widgets.Button(description="Stop", button_style="danger")
        save = widgets.Button(description="Save picture")
        stop.on_click(lambda _: self.stop())
        save.on_click(lambda _: self._save())
        boxes = [stop, save]
        for label, func in self.actions.items():
            b = widgets.Button(description=label, button_style="success")
            b.on_click(lambda _, f=func: f(self.state))
            boxes.append(b)
        for name, spec in self.controls.items():
            self.state[name] = spec[0] if isinstance(spec, list) else spec[3]
            if isinstance(spec, list):
                w = widgets.Dropdown(options=spec, value=spec[0], description=name)
            else:
                w = widgets.FloatSlider(min=spec[0], max=spec[1], step=spec[2], value=spec[3], description=name,
                                        continuous_update=False)
            w.observe(lambda change, key=name: self.state.__setitem__(key, change["new"]), names="value")
            boxes.append(w)
        display(widgets.VBox([widgets.HBox(boxes), self._status, self._img]))
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=3)

    def _save(self):
        if self._last is None:
            return
        self._saved += 1
        name = f"saved_{self._saved}.jpg"
        cv2.imwrite(name, self._last)
        self._status.value = f"Saved {name}"

    def _share(self, picture):
        """Keep a small picture of the live view for the teacher page (the agent sends it; it is deleted when the camera stops)."""
        home = os.environ.get("LAB_HOME")
        if not home or time.time() - self._shared < 1.5:
            return
        self._shared = time.time()
        try:
            h, w = picture.shape[:2]
            ok, buf = cv2.imencode(".jpg", cv2.resize(picture, (320, max(1, int(h * 320 / w)))), [cv2.IMWRITE_JPEG_QUALITY, 60])
            if ok:
                path = os.path.join(home, ".tmp", "live.jpg")
                with open(path + ".part", "wb") as f:
                    f.write(buf.tobytes())
                os.replace(path + ".part", path)
        except Exception:
            pass                                   # the teacher picture is optional: never disturb the student's live view

    def _run(self):
        try:
            cap = open_camera(self.size, self.mjpg)
        except SystemExit as error:
            self._status.value = str(error)
            return
        self._status.value = "Live. Press Stop when you are done."
        last = time.perf_counter()
        try:
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    self._status.value = "No frame from the camera."
                    break
                shown = self.process(frame, self.state)
                now = time.perf_counter()
                self.state["fps"] = 0.9 * self.state["fps"] + 0.1 * (1.0 / max(now - last, 1e-6))
                last = now
                self._last = shown
                self._share(shown)
                ok, buf = cv2.imencode(".jpg", shown, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    self._img.value = buf.tobytes()
        except Exception as error:           # show the problem in the notebook, not only in a hidden thread
            self._status.value = f"Stopped by an error: {error}"
        finally:
            cap.release()
            try:
                os.remove(os.path.join(os.environ.get("LAB_HOME", ""), ".tmp", "live.jpg"))
            except OSError:
                pass
            if not self._status.value.startswith("Stopped by"):
                self._status.value = "Stopped. The camera is free."
            if LiveView._active is self:
                LiveView._active = None


def live(process, controls=None, **options):
    """Start a live view in the notebook and return it (call .stop() or press the Stop button)."""
    return LiveView(process, controls, **options).start()


def reset(number):
    """Put a fresh copy of the notebook of lab <number> in your folder. Your old copy is kept next to it as .old."""
    import glob
    home = os.environ.get("LAB_HOME") or os.getcwd()
    found = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"lab{number}_*", f"lab{number}_*.ipynb"))
    if not found:
        print(f"There is no lab {number}.")
        return
    dest = os.path.join(home, f"lab{number}", os.path.basename(found[0]))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        os.replace(dest, dest + ".old")
        print("Your old copy was kept as", dest + ".old")
    shutil.copyfile(found[0], dest)
    print("Fresh notebook:", dest)


def cuda_libs():
    """Make PyTorch find the NVIDIA libraries that Lab 0 installs into your own environment.
    A kernel that was already running before Step 8 cannot see a folder that did not exist when it started,
    so the library is loaded here by its full path. Safe to run many times."""
    import ctypes
    import glob
    import sysconfig
    site = sysconfig.get_paths()["purelib"]
    for path in glob.glob(os.path.join(site, "nvidia", "cu12", "lib", "libcudss.so.0")):
        try:
            ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
        except OSError:
            pass


cuda_libs()              # also when a notebook starts with import labview
