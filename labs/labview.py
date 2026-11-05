"""Camera and live-view helpers for the Myduino labs.

open_camera()  opens the camera you chose with   lab start <name> camera <number>
live()         live picture inside a notebook, with Stop and Save buttons
sudo_login()   asks for your password once, so "sudo" works in notebook cells
build_lock()   one TensorRT build at a time on the Jetson (the 8 GB memory fits one)
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
    """The camera of this student: a /dev/videoN path from lab start, or 0 when nothing was chosen."""
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
                         "and check the camera number with:  lab cameras")
    return cap


# ---------------------------------------------------------------- sudo in notebooks
def sudo_login():
    """Ask for your password once (it is not shown and not saved in the notebook).

    After this, a cell such as   !sudo apt update   works: a notebook has no terminal where sudo could ask.
    The password lives only in this notebook's kernel. Restarting the kernel forgets it.
    """
    folder = tempfile.mkdtemp(prefix="labsudo_")
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


# ---------------------------------------------------------------- one build at a time
class build_lock:
    """with build_lock():  ...   Building a TensorRT engine uses most of the memory, so students take turns."""
    path = os.path.expanduser("~/.lab_build.lock")

    def __enter__(self):
        shown = False
        while True:
            try:
                os.mkdir(self.path)
                break
            except FileExistsError:
                try:
                    owner = open(os.path.join(self.path, "owner")).read().split()
                    pid = int(owner[-1])
                    os.kill(pid, 0)                       # still alive?
                except (OSError, ValueError, IndexError):
                    shutil.rmtree(self.path, ignore_errors=True)   # left behind by a closed session
                    continue
                if not shown:
                    print(f"{owner[0]} is building an engine now. Only one build at a time fits in the 8 GB memory, "
                          "so you wait here.", flush=True)
                    shown = True
                time.sleep(10)
        with open(os.path.join(self.path, "owner"), "w") as f:
            f.write(f"{os.path.basename(os.environ.get('LAB_HOME', 'student'))} {os.getpid()}\n")
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.path, ignore_errors=True)


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
                ok, buf = cv2.imencode(".jpg", shown, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    self._img.value = buf.tobytes()
        except Exception as error:           # show the problem in the notebook, not only in a hidden thread
            self._status.value = f"Stopped by an error: {error}"
        finally:
            cap.release()
            if not self._status.value.startswith("Stopped by"):
                self._status.value = "Stopped. The camera is free."
            if LiveView._active is self:
                LiveView._active = None


def live(process, controls=None, **options):
    """Start a live view in the notebook and return it (call .stop() or press the Stop button)."""
    return LiveView(process, controls, **options).start()
