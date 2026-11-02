"""Camera and live-view helpers for the Myduino labs.

open_camera()  opens the camera you chose with   lab start <name> camera <number>
Viewer         live picture for programs you run in the terminal:
               a window on the Jetson screen, or a page in your laptop browser when you work over SSH
live()         live picture inside a notebook, with Stop and Save buttons
"""
import atexit
import os
import select
import socket
import sys
import threading
import time
from urllib.parse import unquote

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


def _my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))     # sends nothing, only finds the address of this Jetson
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


# ---------------------------------------------------------------- terminal programs
_PAGE = """<!doctype html><meta charset="utf-8"><title>Myduino live view</title>
<style>body{font-family:sans-serif;background:#111;color:#eee;margin:16px}img{max-width:100%;margin:8px 0;display:block}</style>
<h3>Myduino live view</h3><p>Press the keys of the program in your SSH terminal (q = quit).</p><div id="v"></div>
<script>
const seen = new Set();
async function refresh(){
  const names = await (await fetch('/names')).json();
  for (const n of names){ if(!seen.has(n)){ seen.add(n);
    const i = document.createElement('img'); i.src = '/s/' + encodeURIComponent(n); i.alt = n;
    document.getElementById('v').appendChild(i);} }
}
refresh(); setInterval(refresh, 2000);
</script>"""


class Viewer:
    """show() and key() work like cv2.imshow and cv2.waitKey.

    On the Jetson screen it opens a window. Over SSH it serves the picture to a browser
    and reads the keys from your terminal. Force one with the variable LAB_VIEW=window or stream.
    """

    def __init__(self):
        mode = os.environ.get("LAB_VIEW", "")
        if mode not in ("window", "stream"):
            local = os.environ.get("DISPLAY") and not os.environ.get("SSH_CONNECTION")
            mode = "window" if local else "stream"
        self.mode = mode
        self._frames = {}
        self._cond = threading.Condition()
        self._closed = False
        self._server = None
        self._term = None
        if mode == "stream":
            self._start_server()
            self._raw_keys()
        atexit.register(self.close)

    # -- stream mode
    def _start_server(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import json
        viewer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path == "/names":
                    body = json.dumps(sorted(viewer._frames)).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif self.path.startswith("/s/"):
                    self._stream(unquote(self.path[3:]))
                else:
                    body = _PAGE.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

            def _stream(self, name):
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                last = None
                try:
                    while not viewer._closed:
                        with viewer._cond:
                            viewer._cond.wait(timeout=1)
                            jpg = viewer._frames.get(name)
                        if jpg is None or jpg is last:
                            continue
                        last = jpg
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(jpg))
                        self.wfile.write(jpg)
                        self.wfile.write(b"\r\n")
                except OSError:
                    pass

        import socketserver

        class Server(ThreadingHTTPServer):
            daemon_threads = True

            def server_bind(self):
                # HTTPServer looks up the full host name here, which can take seconds without a DNS server
                socketserver.TCPServer.server_bind(self)
                self.server_name, self.server_port = "jetson", self.server_address[1]

        port = int(os.environ.get("LAB_STREAM_PORT") or 8800)
        while True:
            try:
                self._server = Server(("0.0.0.0", port), Handler)
                break
            except OSError:
                port += 1
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        print(f"Live view: open  http://{_my_ip()}:{port}/  in the browser of your laptop.", flush=True)
        print("Press the keys of the program here in this terminal.", flush=True)

    def _raw_keys(self):
        if not sys.stdin.isatty():
            return
        import termios
        import tty
        fd = sys.stdin.fileno()
        self._term = (fd, termios.tcgetattr(fd))
        tty.setcbreak(fd)           # keys arrive at once; Ctrl + C still works

    # -- the same two calls as OpenCV
    def show(self, name, img):
        if self.mode == "window":
            cv2.imshow(name, img)
            return
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            with self._cond:
                self._frames[name] = buf.tobytes()
                self._cond.notify_all()

    def key(self):
        """The code of the key that was pressed, or 255 when there is none (like cv2.waitKey(1) & 0xFF)."""
        if self.mode == "window":
            return cv2.waitKey(1) & 0xFF
        if self._term is not None and select.select([sys.stdin], [], [], 0)[0]:
            data = os.read(sys.stdin.fileno(), 1)
            if data:
                return data[0]
        return 255

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self._term is not None:
            import termios
            termios.tcsetattr(self._term[0], termios.TCSADRAIN, self._term[1])
            self._term = None
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self.mode == "window":
            cv2.destroyAllWindows()
        with self._cond:
            self._cond.notify_all()


# ---------------------------------------------------------------- notebooks
class LiveView:
    """Live video inside a notebook.

    process(frame, state) gets each camera picture and returns the picture to show.
    state holds the values of your controls and "fps". controls is a dict:
        {"Mode": ["normal", "gray"]}          a drop-down list
        {"Confidence": (0.05, 0.95, 0.05, 0.4)}   a slider: (min, max, step, start)
    """
    _active = None

    def __init__(self, process, controls=None, width=640, size=(640, 480), mjpg=True):
        self.process = process
        self.controls = controls or {}
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
