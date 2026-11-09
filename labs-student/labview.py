"""Camera and live-view helpers for the Myduino labs.

open_camera()  opens the camera your teacher chose for you on the teacher page
mqtt()         connects this notebook to the MQTT broker of your own (ESP32 boards and phone apps use it too)
live()         live picture inside a notebook, with Stop and Save buttons
sudo_login()   asks for your password once, so "sudo" works in notebook cells
record()       record sound from the microphone (webcam or USB); play() plays it; MicStream() listens all the time
llm_start(), llm_chat()  start and ask the language model that runs on this Jetson (llama.cpp); llm_link(), llm_stop()
Esp32()        the Jetson side of the link to the ESP32 board; VirtualEsp32() is a pretend board; esp32_files() writes the board program
build_lock()   one TensorRT build at a time on the Jetson (the 8 GB memory fits one)
train_lock()   one model training at a time (shares the lock of build_lock)
setup_begin()  one student at a time runs the Lab 0 install (setup_end() lets the next one in)
"""
import getpass
import os
import re
import shutil
import stat
import sys
import subprocess
import tempfile
import threading
import time

import cv2


# ---------------------------------------------------------------- MQTT (ESP32 boards, phone apps)
def mqtt_info():
    """Your own MQTT broker on this Jetson. Give host, port, user and password to the ESP32 and to a phone app (IoT MQTT Panel).
    The broker is yours alone, like your JupyterLab: use any topic names, for example "gate" or "temperature"."""
    env = os.environ
    return {"host": env.get("LAB_MQTT_HOST", ""), "port": int(env.get("LAB_MQTT_PORT", "0") or 0), "user": env.get("LAB_MQTT_USER", ""),
            "password": env.get("LAB_MQTT_PASS", "")}


_mqtt_count = [0]


def mqtt(on_message=None, subscribe=()):
    """Connect this notebook to your MQTT broker and return the client.
    on_message(topic, text) is called for every message on the topics in subscribe (for example ["temperature"], or "#" for all)."""
    try:
        import paho.mqtt.client as paho
    except ImportError:
        subprocess.run(["pip", "install", "-q", "paho-mqtt"], check=True)
        import paho.mqtt.client as paho
    info = mqtt_info()
    if not info["port"]:
        raise SystemExit("No MQTT broker. Ask your teacher to start the lab, then restart this notebook's kernel.")
    _mqtt_count[0] += 1
    name = f"{info['user']}-nb-{os.getpid()}-{_mqtt_count[0]}"          # every client needs its own name
    try:
        client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=name)
    except AttributeError:                                    # an older paho-mqtt
        client = paho.Client(client_id=name)
    client.username_pw_set(info["user"], info["password"])
    if on_message:
        client.on_message = lambda c, u, m: on_message(m.topic, m.payload.decode(errors="replace"))
    client.connect("127.0.0.1", info["port"], keepalive=30)          # the broker runs on this Jetson
    for topic in ([subscribe] if isinstance(subscribe, str) else subscribe):
        client.subscribe(topic)
    client.loop_start()
    return client


# ---------------------------------------------------------------- the ESP32-S3 board (IoT) and the Jetson (AI)
def esp32_files(wifi_name="", wifi_password="", folder="esp32"):
    """Copy the program of the ESP32 board (main.py and config.py) into your folder.
    The MQTT lines of config.py are filled with the details of YOUR broker. Upload the files to the board with Thonny."""
    import re
    source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esp32")
    os.makedirs(folder, exist_ok=True)
    info = mqtt_info()
    for name in ("main.py", "config.py"):
        text = open(os.path.join(source, name)).read()
        if name == "config.py":
            for key, value in (("MQTT_HOST", f'"{info["host"]}"'), ("MQTT_PORT", str(info["port"])), ("MQTT_USER", f'"{info["user"]}"'),
                               ("MQTT_PASSWORD", f'"{info["password"]}"'), ("WIFI_SSID", f'"{wifi_name}"' if wifi_name else None),
                               ("WIFI_PASSWORD", f'"{wifi_password}"' if wifi_password else None)):
                if value:
                    text = re.sub(rf"^{key} = .*?(\s+#.*)?$", lambda m, k=key, v=value: f"{k} = {v}" + (m.group(1) or ""), text, flags=re.M)
        with open(os.path.join(folder, name), "w") as f:
            f.write(text)
        print("Wrote", os.path.join(folder, name))


class Esp32:
    """The Jetson side of the link to the ESP32 board. The Jetson does the AI, the board does the IoT.
    send("led", "on") sends a command. online() tells if the board is alive. sensors, telemetry, events and latencies hold what came back.
    A heartbeat goes to the board every 5 seconds: if it stops, the board switches the alert off (fail-safe)."""

    def __init__(self):
        self.status = "unknown"
        self.telemetry, self.sensors, self.events, self.latencies = {}, {}, [], []
        self.last_heard = 0.0
        self._sent = {}
        self._stop = threading.Event()
        self.client = mqtt(self._on_message, subscribe=["esp/#"])
        threading.Thread(target=self._heartbeat, daemon=True).start()

    def _on_message(self, topic, text):
        now = time.time()
        if topic == "esp/status":
            self.status = text                              # may be a retained message from an old session
        elif topic == "esp/telemetry":
            self.last_heard = now
            try:
                import json
                self.telemetry = json.loads(text)
            except ValueError:
                pass
        elif topic.startswith("esp/sensor/"):
            self.last_heard = now
            try:
                self.sensors[topic.split("/")[-1]] = (float(text), now)
            except ValueError:
                self.sensors[topic.split("/")[-1]] = (text, now)
        elif topic == "esp/ack":
            self.last_heard = now
            sent = self._sent.pop(text, None)
            if sent:
                self.latencies.append(now - sent)
        elif topic == "esp/event":
            self.events.append((now, text))

    def _heartbeat(self):
        while not self._stop.wait(5.0):
            self.client.publish("jetson/hb", "1")

    def send(self, name, value):
        """Send a command to the board, for example send("led", "on"), send("servo", 90), send("buzzer", 500), send("alert", "on")."""
        self._sent[f"{name}={value}"] = time.time()
        self.client.publish(f"esp/cmd/{name}", str(value))

    def online(self, within=15.0):
        """True when the board says online and was heard in the last `within` seconds."""
        return self.status == "online" and time.time() - self.last_heard < within

    def close(self):
        self._stop.set()
        self.client.loop_stop()
        self.client.disconnect()


class VirtualEsp32:
    """A pretend ESP32 board that runs in Python. It follows the same rules and topics as esp32/main.py, so you can build and test
    your AIoT program before the real board is on your table. Later, switch it off (stop()) and switch the real board on: nothing else changes."""

    def __init__(self):
        import random
        self._random = random
        self.led, self.alert, self.servo, self.buzzer_until = "off", False, 90, 0.0
        self.hb = time.time()
        self.light = 2000.0
        self.temp = 30.0
        self._offsets = {}                  # kind -> (amount, until): a made-up disturbance, see disturb()
        self.log = []
        self._stop = threading.Event()
        self.client = mqtt(self._on_message, subscribe=["esp/cmd/#", "jetson/hb"])
        self.client.publish("esp/status", "online", retain=True)
        self.started = time.time()
        threading.Thread(target=self._run, daemon=True).start()

    def _say(self, topic, text, retain=False):
        self.client.publish(topic, str(text), retain=retain)

    def _note(self, text):
        self.log.append((time.time(), text))

    def _on_message(self, topic, text):
        name = topic.split("/")[-1]
        if topic.startswith("esp/cmd/"):
            try:
                if name == "led":
                    self.led = text
                elif name == "buzzer":
                    self.buzzer_until = time.time() + int(text) / 1000
                elif name == "servo":
                    self.servo = max(0, min(180, int(text)))
                elif name == "alert":
                    self.alert = text == "on"
                    self.hb = time.time()
                else:
                    return
            except ValueError:
                self._say("esp/event", f"bad value for {name}: {text}")
                return
            self._note(f"{name} = {text}")
            self._say("esp/ack", f"{name}={text}")
        elif topic == "jetson/hb":
            self.hb = time.time()

    def _run(self):
        last_sensor = last_telemetry = 0.0
        while not self._stop.wait(0.1):
            now = time.time()
            if self.alert and now - self.hb > 15:
                self.alert = False
                self._note("fail-safe: no heartbeat, alert off")
                self._say("esp/event", "failsafe: no heartbeat from the Jetson, alert off")
            if now - last_sensor > 2:
                last_sensor = now
                self.light = min(4095, max(0, self.light + self._random.uniform(-60, 60)))
                self.temp = min(45, max(25, self.temp + self._random.uniform(-0.3, 0.3)))
                self._say("esp/sensor/light", int(self.light + self._offset("light", now)))
                self._say("esp/sensor/temp", round(self.temp + self._offset("temp", now), 1))
            if now - last_telemetry > 5:
                last_telemetry = now
                import json
                self._say("esp/telemetry", json.dumps({"uptime_s": int(now - self.started), "rssi": -55, "led": self.led,
                                                       "alert": self.alert, "servo": self.servo}))

    def _offset(self, kind, now):
        amount, until = self._offsets.get(kind, (0.0, 0.0))
        return amount if now < until else 0.0

    def disturb(self, kind="light", amount=1500.0, seconds=6.0):
        """Make a made-up disturbance in a sensor (kind "light" or "temp") for some seconds, to test an alarm. Example: board.disturb("temp", 12, 8)."""
        self._offsets[kind] = (amount, time.time() + seconds)

    def describe(self):
        """What the board does now, as text."""
        beeping = time.time() < self.buzzer_until or self.alert
        return f"LED {'BLINK FAST' if self.alert else self.led.upper()} | buzzer {'ON' if beeping else 'off'} | servo {self.servo} degrees | alert {'ON' if self.alert else 'off'}"

    def stop(self):
        self._stop.set()
        self._say("esp/status", "offline", retain=True)
        time.sleep(0.2)
        self.client.loop_stop()
        self.client.disconnect()


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


# ---------------------------------------------------------------- sound (microphone and speaker)
def _device_file(kind):
    return os.path.join(os.environ.get("LAB_HOME") or os.path.expanduser("~"), "." + kind)


def _usb_cards(tool):
    """The sound cards that are not the built-in NVIDIA ones (arecord -l or aplay -l): a list of (name, "plughw:card,device")."""
    try:
        out = subprocess.run([tool, "-l"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    cards = []
    for line in out.splitlines():
        m = re.match(r"card (\d+): .*?\[(.*?)\], device (\d+):", line)
        if m and "NVIDIA" not in m.group(2) and "Tegra" not in m.group(2):
            cards.append((m.group(2), f"plughw:{m.group(1)},{m.group(3)}"))
    return cards


def _hdmi_ports():
    """The HDMI sound outputs of the Jetson: a list of ("plughw:0,3", monitor_present)."""
    try:
        out = subprocess.run(["aplay", "-l"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    ports = []
    for line in out.splitlines():
        m = re.match(r"card (\d+): .*HDMI.*?device (\d+): HDMI", line) or re.match(r"card (\d+): [^,]*HDA[^,]*, device (\d+): HDMI", line)
        if m:
            card, dev = m.group(1), m.group(2)
            present = False
            try:                                 # a monitor on the port shows in the ELD files of the sound card
                for name in os.listdir(f"/proc/asound/card{card}"):
                    if name.startswith("eld#") and "monitor_present\t\t1" in open(f"/proc/asound/card{card}/{name}").read():
                        present = True
            except OSError:
                pass
            ports.append((f"plughw:{card},{dev}", present))
    return ports


def _device_get(kind):
    """The device chosen with mic_set / speaker_set. If none was chosen: the first USB card, else "default".
    (The "default" of the Jetson is a built-in chip with nothing plugged in, so it would record silence.)"""
    try:
        chosen = open(_device_file(kind)).read().strip()
    except OSError:
        chosen = ""
    if chosen:
        return chosen
    cards = _usb_cards("arecord" if kind == "mic" else "aplay")
    if cards:
        return cards[0][1]
    if kind == "speaker":                       # the speakers of a monitor on HDMI: the port that has a monitor, else the first port
        ports = _hdmi_ports()
        if ports:
            return sorted(ports, key=lambda p: not p[1])[0][0]
    return "default"


def qr_picture(text, size=6):
    """A QR code picture (grey, 0 = black, 255 = white, with a white border) for this text.
    Uses OpenCV when it can make QR codes (OpenCV 4.5.4 on JetPack 6 cannot), otherwise the `qrcode` package."""
    import numpy as np
    if hasattr(cv2, "QRCodeEncoder"):
        code = cv2.QRCodeEncoder.create().encode(text)
    else:
        try:
            import qrcode
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "qrcode"], check=True)
            import qrcode
        maker = qrcode.QRCode(border=0, box_size=1)
        maker.add_data(text)
        maker.make(fit=True)
        code = np.where(np.array(maker.get_matrix(), dtype=bool), 0, 255).astype("uint8")
        code = cv2.copyMakeBorder(code, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=255)   # the quiet zone
    code = cv2.resize(code, None, fx=size, fy=size, interpolation=cv2.INTER_NEAREST)
    return cv2.copyMakeBorder(code, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)


def read_qr(frame):
    """All QR codes in a picture: a list of (text, corners), corners being 4 (x, y) points.
    Uses pyzbar (it always decodes); the OpenCV detector of JetPack 6 can find a code but cannot read it."""
    import numpy as np
    try:
        from pyzbar import pyzbar
    except Exception:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyzbar"], check=False)    # needs libzbar0 (setup installs it)
        try:
            from pyzbar import pyzbar
        except Exception:
            pyzbar = None
    if pyzbar is not None:
        grey = frame if frame.ndim == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return [(d.data.decode("utf-8", "replace"), np.array([[p.x, p.y] for p in d.polygon], dtype=int))
                for d in pyzbar.decode(grey) if d.type == "QRCODE" and len(d.polygon) == 4]
    found, texts, corners, _ = cv2.QRCodeDetector().detectAndDecodeMulti(frame)
    return list(zip(texts, corners.astype(int))) if found else []


def mic_get():
    """The microphone chosen with mic_set(), or "default"."""
    return _device_get("mic")


def mic_set(device):
    """Choose the microphone for all labs, for example mic_set("plughw:2,0"). Find the name with audio_devices()."""
    with open(_device_file("mic"), "w") as f:
        f.write(device)
    print("Microphone set to", device)


def speaker_get():
    return _device_get("speaker")


def speaker_set(device):
    """Choose the speaker (a name of aplay -l, for example "plughw:1,0")."""
    with open(_device_file("speaker"), "w") as f:
        f.write(device)
    print("Speaker set to", device)


def audio_devices():
    """Print the USB microphones and speakers of this Jetson, and the ones the labs use now.
    'card 2, device 0' is written plughw:2,0. Choose another with mic_set(...) or speaker_set(...)."""
    for title, tool, kind in (("Microphones", "arecord", "mic"), ("Speakers", "aplay", "speaker")):
        print(f"--- {title} ---")
        try:
            cards = _usb_cards(tool)
        except Exception:
            cards = []
        if not cards and not (kind == "speaker" and _hdmi_ports()):
            print("no USB device found (the built-in chips of the Jetson have nothing plugged in)")
        for name, dev in cards:
            print(f"  {dev}   {name}")
        if kind == "speaker":
            for dev, present in _hdmi_ports():
                print(f"  {dev}   HDMI (monitor speakers)" + ("   <- a monitor is connected" if present else ""))
        print("  used by the labs now:", _device_get(kind))


def record(seconds=3, rate=16000, mic=None):
    """Record from the microphone and return the sound as a numpy array of numbers between -1 and 1 (mono)."""
    import numpy as np
    mic = mic or mic_get()
    cmd = ["arecord", "-q", "-D", mic, "-f", "S16_LE", "-r", str(rate), "-c", "1", "-t", "raw", "-d", str(max(1, int(seconds + 0.999))), "-"]
    try:
        out = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        raise SystemExit("arecord is not installed. Run: sudo apt install alsa-utils")
    if out.returncode != 0:
        raise SystemExit("Cannot record: " + out.stderr.decode(errors="replace").strip() +
                         "\nCheck the name of the microphone with labview.audio_devices() and set it with labview.mic_set(...)")
    data = np.frombuffer(out.stdout, dtype=np.int16).astype(np.float32) / 32768
    return data[:int(seconds * rate)]


class MicStream:
    """Listen all the time in a background thread. latest(seconds) gives the newest sound. Call stop() when you are done."""

    def __init__(self, rate=16000, mic=None, keep=6.0):
        import numpy as np
        self.rate = rate
        self._np = np
        self._buf = np.zeros(int(keep * rate), np.float32)
        self._lock = threading.Lock()
        self._proc = subprocess.Popen(["arecord", "-q", "-D", mic or mic_get(), "-f", "S16_LE", "-r", str(rate), "-c", "1", "-t", "raw", "-"],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        np = self._np
        chunk = int(self.rate * 0.05) * 2                       # 50 ms of 16-bit sound
        while self._proc.poll() is None:
            raw = self._proc.stdout.read(chunk)
            if not raw:
                break
            data = np.frombuffer(raw[:len(raw) // 2 * 2], dtype=np.int16).astype(np.float32) / 32768
            with self._lock:
                self._buf = np.concatenate([self._buf[len(data):], data])

    def latest(self, seconds=1.0):
        with self._lock:
            return self._buf[-int(seconds * self.rate):].copy()

    def alive(self):
        return self._proc.poll() is None

    def error(self):
        """The message of arecord when it stopped (a wrong microphone name, or another program uses it)."""
        try:
            return self._proc.stderr.read().decode(errors="replace").strip() if self._proc.poll() is not None else ""
        except Exception:
            return ""

    def stop(self):
        if self._proc.poll() is None:
            self._proc.terminate()


def save_wav(data, path="sound.wav", rate=16000):
    """Write a numpy sound (-1 to 1) as a WAV file."""
    import wave
    import numpy as np
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(data, -1, 1) * 32767).astype(np.int16).tobytes())
    return path


def load_wav(path):
    """Read a mono 16-bit WAV file. Returns (numpy sound between -1 and 1, sample rate)."""
    import wave
    import numpy as np
    with wave.open(path, "rb") as w:
        rate, channels = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return (data.reshape(-1, channels).mean(axis=1) if channels > 1 else data), rate


def play(sound, rate=16000, browser=True, speaker=True):
    """Play a sound (numpy array or the path of a WAV file).
    browser=True: a player appears under the cell and plays on your laptop. speaker=True: plays on the speaker of the Jetson."""
    path = sound if isinstance(sound, str) else save_wav(sound, os.path.join(tempfile.gettempdir(), f"labplay_{os.getpid()}.wav"), rate)
    if browser:
        from IPython.display import Audio, display
        display(Audio(filename=path) if isinstance(sound, str) else Audio(sound, rate=rate))
    if speaker:
        dev = speaker_get()
        try:
            subprocess.run(["aplay", "-q"] + ([] if dev == "default" else ["-D", dev]) + [path], capture_output=True, timeout=120)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass


# ---------------------------------------------------------------- language models (llama.cpp runs on this Jetson)
LLM_URL = os.environ.get("LLM_URL", "http://127.0.0.1:8080")
LLM_PORT = 8080
# In a student notebook HOME is the student's own folder, but llama.cpp and the model files belong to the whole Jetson: they are in the
# home of the Jetson user, which is the folder above LAB_ROOT.
JETSON_HOME = os.path.dirname(os.environ["LAB_ROOT"]) if os.environ.get("LAB_ROOT") else os.path.expanduser("~")
LLM_DIR = os.path.join(JETSON_HOME, "models")
LLM_SERVER = os.path.join(JETSON_HOME, "llama.cpp", "build", "bin", "llama-server")
LLM_LOG = os.path.join(JETSON_HOME, "llama-server.log")
# The models of the labs (Q4_K_M = 4 bit). Each has its main file and its "eyes" file (the mmproj) for pictures.
# "hf" is the web address of the files, "eyes" the name of the eyes file there, "eyes_here" its name on this Jetson.
LLM_MODELS = {
    "gemma4-e2b": {"hf": "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/", "file": "gemma-4-E2B-it-Q4_K_M.gguf",
                   "vision_model": "lfm3-vl-2b",                 # its own eyes work, but one picture takes about 20 s here: pictures go to LFM3-VL
                   # Gemma 4 has a very large table of word numbers: it stays in the normal memory (the CPU part), the rest runs on the GPU.
                   # Small batches and an 8 bit cache keep the GPU memory below the limit of this board.
                   "args": ["-ngl", "99", "-ot", r"per_layer_token_embd\.weight=CPU", "-c", "4096", "-b", "256", "-ub", "128",
                            "-ctk", "q8_0", "-ctv", "q8_0", "-fa", "on", "--jinja"],
                   "extra": ["--reasoning", "off"],
                   "note": "the default for text: Google Gemma 4 E2B, clean answers in English and Malay, about 25 tokens per second, about 5 GB of memory in use"},
    "lfm3-1.7b": {"hf": "https://huggingface.co/LiquidAI/LFM3-1.7B-GGUF/resolve/main/", "file": "LFM3-1.7B-Q4_K_M.gguf",
                  "vision_model": "lfm3-vl-2b",                  # no eyes of its own: llm_start(vision=True) switches to this one
                  "extra": ["--reasoning", "off"],              # LFM3 thinks first by default, and the short answers stay empty
                  "note": "Liquid AI LFM3 (text), about 27 tokens per second, about 3 GB of memory in use; weaker at strict answer formats"},
    "lfm3-vl-2b": {"hf": "https://huggingface.co/LiquidAI/LFM3-VL-2B-GGUF/resolve/main/", "file": "LFM3-VL-2B-Q4_K_M.gguf",
                   "eyes": "mmproj-LFM3-VL-2B-Q8_0.gguf", "eyes_here": "LFM3-VL-2B-mmproj-Q8_0.gguf", "extra": ["--reasoning", "off"],
                   "note": "the default for pictures: Liquid AI LFM3 vision-language, about 30 tokens per second, about 3.5 GB in use with the eyes"},
    "qwen3.5-2b": {"hf": "https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/", "file": "Qwen3.5-2B-Q4_K_M.gguf",
                   "eyes": "mmproj-F16.gguf", "eyes_here": "Qwen3.5-2B-mmproj-F16.gguf",
                   "note": "fast (about 33 tokens per second), about 3.5 GB of memory in use (4.2 GB with the eyes)"},
    "lfm2.5-vl-1.6b": {"hf": "https://huggingface.co/LiquidAI/LFM2.5-VL-1.6B-GGUF/resolve/main/", "file": "LFM2.5-VL-1.6B-Q4_K_M.gguf",
                       "eyes": "mmproj-LFM2.5-VL-1.6b-Q8_0.gguf", "eyes_here": "LFM2.5-VL-1.6B-mmproj-Q8_0.gguf",
                       "note": "the smallest and fastest (about 59 tokens per second), about 2.4 GB in use (2.7 GB with the eyes), simpler answers"},
}
LLM_DEFAULT = "gemma4-e2b"
LLM_USE = os.path.join(LLM_DIR, ".llm_use")           # who asked the server last, and when (shared by the students of this Jetson)
LLM_BUSY_SECONDS = 120                                 # a switch is refused while somebody else used the server in this time


def _who():
    """The name of the student of this notebook (from the folder: .../dka_4/<student>/labNN)."""
    parts = os.getcwd().split(os.sep)
    return parts[parts.index("dka_4") + 1] if "dka_4" in parts and parts.index("dka_4") + 1 < len(parts) else getpass.getuser()


def _used_by_others():
    """(name, seconds ago) of another student who used the server lately, else None."""
    import json
    try:
        with open(LLM_USE) as f:
            info = json.load(f)
        ago = time.time() - info["time"]
        if info["who"] != _who() and ago < LLM_BUSY_SECONDS:
            return info["who"], ago
    except (OSError, ValueError, KeyError):
        pass
    return None


def _llm(path, body=None, timeout=600):
    """Send one request to llama-server on this Jetson. Returns the open answer."""
    import json
    import urllib.error
    import urllib.request
    request = urllib.request.Request(LLM_URL + path, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.URLError as error:
        raise SystemExit(f"Cannot reach the language model at {LLM_URL} ({error.reason}). "
                         "Is the server started? One student of this Jetson runs llm_start() (Part A of the lab).")


def llm_ready():
    """True when the language model server is running and the model is loaded."""
    import urllib.request
    try:
        with urllib.request.urlopen(LLM_URL + "/health", timeout=3) as answer:
            return answer.status == 200
    except Exception:
        return False


def llm_link():
    """The address of the chat page. Open it in the browser of any laptop in the same network."""
    import socket
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        ip = probe.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        probe.close()
    return f"http://{ip}:{LLM_PORT}"


def llm_models():
    """Print the models that you can choose, and which one runs now (with or without the eyes)."""
    now = llm_current()
    for name, info in LLM_MODELS.items():
        print(f"{'>' if name == now else ' '} {name:<16} {info['note']}")
    if now is None:
        print("The server runs: (not started)")
    else:
        print(f"The server runs: {now}, {'WITH the eyes (pictures)' if llm_vision() else 'text only'}")


def _props():
    import json
    import urllib.request
    try:
        with urllib.request.urlopen(LLM_URL + "/props", timeout=5) as answer:
            return json.load(answer)
    except Exception:
        return {}


def llm_current():
    """The name of the model that the server runs now (None when the server is not running)."""
    if not llm_ready():
        return None
    path = _props().get("model_path", "")
    for name, info in LLM_MODELS.items():
        if os.path.basename(path) == info["file"]:
            return name
    return "(unknown)"


def llm_vision():
    """True when the server runs with the eyes (it accepts pictures), False when it is text only, None when it is not running."""
    if not llm_ready():
        return None
    return bool(_props().get("modalities", {}).get("vision"))


def _drop_cache(path):
    """Tell Linux that a big model file need not stay in the file cache. On this board the cache and the GPU share the memory, and a model
    that was just copied or downloaded can leave too little for the GPU (the server then stops with 'cudaMalloc failed: out of memory')."""
    try:
        fd = os.open(path, os.O_RDONLY)
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        finally:
            os.close(fd)
    except OSError:
        pass


def llm_download(model=LLM_DEFAULT, vision=False, show=print):
    """Download the files of a model (only one student per Jetson needs to; a file that is already here is skipped).
    The eyes file is downloaded only with vision=True."""
    info = LLM_MODELS[model]
    os.makedirs(LLM_DIR, exist_ok=True)
    files = [(info["file"], info["file"])] + ([(info["eyes_here"], info["eyes"])] if vision else [])
    for name, remote in files:
        path = os.path.join(LLM_DIR, name)
        if os.path.exists(path) and not os.path.exists(path + ".part"):
            show(f"{name}: already here")
            _drop_cache(path)
            continue
        show(f"{name}: downloading (a few minutes)...")
        command = ["curl", "-fL", "-C", "-", "-o", path + ".part", "-s", info["hf"] + remote]
        if subprocess.run(command).returncode != 0:
            raise SystemExit(f"Download of {name} failed. Check the network and run this cell again (it continues where it stopped).")
        os.replace(path + ".part", path)
        _drop_cache(path)
        show(f"{name}: done")


def llm_start(model=None, vision=None, wait=90, force=False):
    """Start the language model server (only ONE student per Jetson runs this; the others use the same server).
    llm_start() starts the default model as TEXT ONLY, or keeps what runs.
    llm_start(vision=True) loads a model WITH the eyes (pictures): the vision twin of the text model. llm_start("qwen3.5-2b") switches the model.
    A change RESTARTS the server for all students of this Jetson (about 30 seconds), so tell your team first.
    It is refused while a team mate used the server in the last 2 minutes (force=True changes it anyway).
    Only one model fits in the memory at a time. Then it prints the link of the chat page."""
    if model is not None and model not in LLM_MODELS:
        raise SystemExit(f"Unknown model {model!r}. Choose one of: {', '.join(LLM_MODELS)}")
    if alm_ready():                                                          # the audio server and a text model do not fit together
        print("Stopping the audio server of Lab 22 first ...")
        llm_stop()
    now, eyes = llm_current(), llm_vision()
    if now is not None and model in (None, now) and vision in (None, eyes):
        print(f"The server is already running ({now}, {'with the eyes' if eyes else 'text only'}). Chat page:", llm_link())
        return
    if model is None:
        model = LLM_DEFAULT if now is None else now
    if vision is None:
        vision = bool(eyes)
    if vision and "eyes" not in LLM_MODELS[model]:                         # a text-only model: use its vision twin
        twin = LLM_MODELS[model].get("vision_model")
        if twin is None:
            raise SystemExit(f"{model} has no eyes. Choose a model with eyes: " + ", ".join(m for m, i in LLM_MODELS.items() if "eyes" in i))
        model = twin
    if now is not None:
        other = _used_by_others()
        if other and not force:
            raise SystemExit(f"{other[0]} used the model {other[1]:.0f} s ago. Changing it restarts it for everybody. "
                             f"Ask {other[0]} to finish first, or add force=True.")
        print(f"Restarting the server as {model} ({'with the eyes' if vision else 'text only'}): everybody on this Jetson waits about 30 s ...")
        llm_stop()
    info = LLM_MODELS[model]
    if not os.path.exists(LLM_SERVER):
        raise SystemExit("llama-server is not built on this Jetson (ask the teacher to run labs-setup.sh).")
    llm_download(model, vision)
    flags = info.get("args") or ["-ngl", "99", "-c", "4096", "-fa", "on", "-lm", "none", "--jinja"]   # -lm none: load into the GPU memory directly (the default can run out of memory here)
    command = [LLM_SERVER, "-m", os.path.join(LLM_DIR, info["file"])] + flags + ["--host", "0.0.0.0", "--port", str(LLM_PORT)] + info.get("extra", [])
    if vision:
        command += ["--mmproj", os.path.join(LLM_DIR, info["eyes_here"])]
    log = open(LLM_LOG, "w")
    subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)   # keeps running after the notebook
    started = time.time()
    while time.time() - started < wait:
        if llm_ready():
            print(f"{model} ({'with the eyes' if vision else 'text only'}) ready after {time.time() - started:.0f} s. "
                  f"Chat page: {llm_link()}  (give this link to your team)")
            return
        time.sleep(2)
    raise SystemExit("The server did not start in time. Look at the end of " + LLM_LOG + " (!tail -20 ~/llama-server.log)")


def llm_stop():
    """Stop the language model server (frees 2 to 4 GB of memory). Waits until it has really stopped.
    The small embedding server stops too; embed() starts it again when needed."""
    subprocess.run(["pkill", "-x", "llama-server"])
    for _ in range(30):
        if not llm_ready() and subprocess.run(["pgrep", "-x", "llama-server"], capture_output=True).returncode != 0:
            return
        time.sleep(1)


# ---------------------------------------------------------------- text embeddings (a second, small llama.cpp server)
EMB_URL = "http://127.0.0.1:8082"
EMB_PORT = 8082
EMB_HF = "https://huggingface.co/ggml-org/embeddinggemma-2-GGUF/resolve/main/"
EMB_FILE = "embeddinggemma-2-Q8_0.gguf"                      # EmbeddingGemma 2 (Google), 4 bit would be 176 MB, this one 310 MB
EMB_QUERY = "task: search result | query: "                  # the model wants a short label before a question ...
EMB_DOCUMENT = "title: none | text: "                        # ... and another before a note; without them the search is worse
EMB_LOG = os.path.join(JETSON_HOME, "embedding-server.log")


def emb_ready():
    """True when the embedding server answers."""
    import urllib.request
    try:
        with urllib.request.urlopen(EMB_URL + "/health", timeout=2) as answer:
            return answer.status == 200
    except Exception:
        return False


def emb_start(wait=90):
    """Start the embedding server (EmbeddingGemma 2, about 0.25 GB of memory). It is shared by all students of the Jetson.
    embed() starts it by itself when it is not running, so you rarely need to call this."""
    if emb_ready():
        return
    os.makedirs(LLM_DIR, exist_ok=True)
    path = os.path.join(LLM_DIR, EMB_FILE)
    if not os.path.exists(path) or os.path.exists(path + ".part"):
        print(f"{EMB_FILE}: downloading (about 310 MB, a few minutes, only the first time)...")
        if subprocess.run(["curl", "-fL", "-C", "-", "-o", path + ".part", "-s", EMB_HF + EMB_FILE]).returncode != 0:
            raise SystemExit(f"Download of {EMB_FILE} failed. Check the network and run this cell again (it continues where it stopped).")
        os.replace(path + ".part", path)
    if not os.path.exists(LLM_SERVER):
        raise SystemExit("llama-server is not built on this Jetson (ask the teacher to run labs-setup.sh).")
    command = [LLM_SERVER, "-m", path, "--embeddings", "-ngl", "99", "-c", "2048", "-lm", "none", "--host", "127.0.0.1", "--port", str(EMB_PORT)]
    subprocess.Popen(command, stdout=open(EMB_LOG, "w"), stderr=subprocess.STDOUT, start_new_session=True)
    started = time.time()
    while time.time() - started < wait:
        if emb_ready():
            print(f"Embedding server ready after {time.time() - started:.0f} s.")
            return
        time.sleep(1)
    raise SystemExit("The embedding server did not start in time. Look at the end of " + EMB_LOG + " (!tail -20 ~/embedding-server.log)")


def embed(texts, kind="document"):
    """Turn texts into vectors of 768 numbers (each of length 1). kind="document" for notes, kind="query" for a question.
    Returns a numpy array with one row for each text. Starts the embedding server if it is not running."""
    import json
    import urllib.request
    import numpy as np
    if not emb_ready():
        emb_start()
    prefix = EMB_QUERY if kind == "query" else EMB_DOCUMENT
    body = json.dumps({"input": [prefix + t for t in texts]}).encode()
    request = urllib.request.Request(EMB_URL + "/v1/embeddings", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as answer:
        vectors = np.array([d["embedding"] for d in json.load(answer)["data"]], dtype=float)
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


# ---------------------------------------------------------------- audio language model (LFM3-Audio on llama.cpp: speech in, speech out)
ALM_URL = "http://127.0.0.1:8083"
ALM_PORT = 8083
ALM_MODELS = {                                                # the model file (language model) and the ears-and-voice file (mmproj) of each
    "lfm3-audio-2b": {"hf": "https://huggingface.co/LiquidAI/LFM3-Audio-2B-GGUF/resolve/main/", "file": "LFM3-Audio-2B-Q4_K_M.gguf",
                      "ears": "mmproj-LFM3-Audio-2B-Q8_0.gguf", "ctx": "1024", "note": "speech in, speech out (Lab 22), about 1.5 GB",
                      "voice": [["-ngl", "99", "-c", "512", "-b", "64", "-ub", "32", "-ctk", "q8_0", "-ctv", "q8_0", "-fa", "on"],
                                ["-ngl", "0", "-c", "512", "-b", "64", "-ub", "32", "--no-mmproj-offload"], "CPU"]},
    "lfm3-omni-2b": {"hf": "https://huggingface.co/LiquidAI/LFM3-Omni-2B-GGUF/resolve/main/", "file": "LFM3-Omni-2B-Q4_K_M.gguf",
                     "ears": "mmproj-LFM3-Omni-2B-Q8_0.gguf", "ctx": "3072", "note": "text, pictures and speech in one model (Lab 23), about 2 GB",
                     "voice": [["-ngl", "0", "-c", "512", "-b", "64", "-ub", "32", "--no-mmproj-offload"], "CPU"]},      # next to the Omni server the GPU memory is tight: the voice uses the GPU only a little, or not at all
}
ALM_DEFAULT = "lfm3-audio-2b"
ALM_TTS = os.path.join(JETSON_HOME, "llama.cpp", "build", "bin", "llama-tts")
ALM_LOG = os.path.join(JETSON_HOME, "audio-server.log")


def alm_ready():
    """True when the audio language model server answers."""
    import urllib.request
    try:
        with urllib.request.urlopen(ALM_URL + "/health", timeout=2) as answer:
            return answer.status == 200
    except Exception:
        return False


def alm_current():
    """The name of the audio model that the audio server runs now (None when it is not running)."""
    import json
    import urllib.request
    if not alm_ready():
        return None
    try:
        with urllib.request.urlopen(ALM_URL + "/props", timeout=5) as answer:
            path = os.path.basename(json.load(answer).get("model_path", ""))
    except Exception:
        return "(unknown)"
    return next((name for name, info in ALM_MODELS.items() if info["file"] == path), "(unknown)")


def alm_start(model=None, wait=120):
    """Start the audio language model server. alm_start() starts LFM3-Audio (Lab 22), alm_start("lfm3-omni-2b") starts LFM3-Omni (Lab 23).
    Only one student per Jetson does this. The text model of Lab 20 must be stopped first (labview.llm_stop()): they do not fit together."""
    model = model or ALM_DEFAULT
    if model not in ALM_MODELS:
        raise SystemExit(f"Unknown model {model!r}. Choose one of: {', '.join(ALM_MODELS)}")
    now = alm_current()
    if now == model:
        print(f"The audio server is already running ({model}).")
        return
    if llm_ready() and now is None:
        raise SystemExit("The text model is running and the memory is not enough for both. Tell your team, then run  labview.llm_stop()  "
                         "and start this cell again. Afterwards labview.llm_start() brings the text model back.")
    if now is not None:
        print(f"Restarting the audio server as {model} ...")
        llm_stop()
    info = ALM_MODELS[model]
    os.makedirs(LLM_DIR, exist_ok=True)
    for name in (info["file"], info["ears"]):
        path = os.path.join(LLM_DIR, name)
        if os.path.exists(path) and not os.path.exists(path + ".part"):
            _drop_cache(path)
            continue
        print(f"{name}: downloading (a few minutes, only the first time)...")
        if subprocess.run(["curl", "-fL", "-C", "-", "-o", path + ".part", "-s", info["hf"] + name]).returncode != 0:
            raise SystemExit(f"Download of {name} failed. Check the network and run this cell again (it continues where it stopped).")
        os.replace(path + ".part", path)
        _drop_cache(path)
    command = [LLM_SERVER, "-m", os.path.join(LLM_DIR, info["file"]), "--mmproj", os.path.join(LLM_DIR, info["ears"]), "-ngl", "99", "-c", info["ctx"],
               "-b", "256", "-ub", "128", "-ctk", "q8_0", "-ctv", "q8_0", "-fa", "on", "--jinja", "--reasoning", "off", "--host", "127.0.0.1", "--port", str(ALM_PORT)]
    # a short context and small batches keep the GPU memory low, so that llama-tts (speech out) can run next to this server
    subprocess.Popen(command, stdout=open(ALM_LOG, "w"), stderr=subprocess.STDOUT, start_new_session=True)
    started = time.time()
    while time.time() - started < wait:
        if alm_ready():
            print(f"Audio server ({model}) ready after {time.time() - started:.0f} s.")
            return
        time.sleep(2)
    raise SystemExit("The audio server did not start in time. Look at the end of " + ALM_LOG + " (!tail -20 ~/audio-server.log)")


def alm_stop():
    """Stop the audio language model server (frees about 1.4 GB). The text model server, if it runs, is stopped too."""
    llm_stop()


def alm_listen(sound, system="Perform ASR.", question=None, max_tokens=150, image=None):
    """Give a sound to the audio model. sound is a numpy array (as labview.record returns) or the path of a WAV file.
    With the system prompt "Perform ASR." the answer is what was said. With another system prompt (and question=None) the model
    answers the spoken question. image (optional): a JPEG picture as bytes (only the Omni model sees it). Returns a dict: text, seconds (time it took), audio_seconds, rtf (seconds / audio_seconds)."""
    import base64
    import json
    import tempfile
    import urllib.request
    path = sound
    if not isinstance(sound, str):
        path = tempfile.mktemp(suffix=".wav", dir=os.environ.get("TMPDIR"))
        save_wav(sound, path)
    wav = open(path, "rb").read()
    if not isinstance(sound, str):
        os.remove(path)
    parts = [{"type": "input_audio", "input_audio": {"data": base64.b64encode(wav).decode(), "format": "wav"}}]
    if image:                                                   # the picture goes AFTER the sound: the other way round the answer stops early
        parts = parts + [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(image).decode()}}]
    if question:
        parts = [{"type": "text", "text": question}] + parts
    body = {"messages": [{"role": "system", "content": system}, {"role": "user", "content": parts}], "temperature": 0, "max_tokens": max_tokens}
    started = time.time()
    request = urllib.request.Request(ALM_URL + "/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as answer:
            text = json.load(answer)["choices"][0]["message"]["content"].strip()
    except OSError as problem:
        raise SystemExit(f"Cannot reach the audio server at {ALM_URL} ({problem}). Run  labview.alm_start()  (one student per Jetson).")
    took = time.time() - started
    seconds = (len(wav) - 44) / 2 / 16000
    return {"text": text, "seconds": took, "audio_seconds": seconds, "rtf": took / max(seconds, 0.01)}


def alm_ask(text, system="Answer in one short sentence.", max_tokens=150):
    """Give the audio model a TEXT question (no sound). Returns a dict: text, seconds."""
    import json
    import urllib.request
    body = {"messages": [{"role": "system", "content": system}, {"role": "user", "content": text}], "temperature": 0, "max_tokens": max_tokens}
    started = time.time()
    request = urllib.request.Request(ALM_URL + "/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as answer:
            reply = json.load(answer)["choices"][0]["message"]["content"].strip()
    except OSError as problem:
        raise SystemExit(f"Cannot reach the audio server at {ALM_URL} ({problem}). Run  labview.alm_start()  (one student per Jetson).")
    return {"text": reply, "seconds": time.time() - started}


def alm_speak(text, path="speech.wav", voice="female", lang="en"):
    """Turn text into speech with the voice of the audio model and save it as a WAV file (24 000 Hz). voice: "female" or "male".
    lang: a language code such as en, fr, es, de, ja. Returns the seconds it took (it loads the model each time, so it is slow)."""
    if not os.path.exists(ALM_TTS):
        raise SystemExit("llama-tts is not built on this Jetson (ask the teacher to run labs-setup.sh).")
    info = ALM_MODELS[alm_current() if alm_current() in ALM_MODELS else ALM_DEFAULT]
    base = [ALM_TTS, "-m", os.path.join(LLM_DIR, info["file"]), "-mm", os.path.join(LLM_DIR, info["ears"])]
    tail = ["-p", text, "--tts-voice", voice, "--tts-lang", lang, "-o", path]
    # The GPU memory is tight when the audio server runs too: the voice tries the settings of the model one after the other.
    settings = info["voice"]
    started = time.time()
    result = None
    for options in settings:
        if os.path.exists(path):
            os.remove(path)                                    # an old file must not look like a success
        env = dict(os.environ)
        if options == "CPU":                                   # the last resort: hide the GPU, so the voice uses only the CPU
            options = settings[-2]
            env["CUDA_VISIBLE_DEVICES"] = ""
        result = subprocess.run(base + options + tail, capture_output=True, text=True, env=env)
        if result.returncode == 0 and os.path.exists(path):
            break
    else:
        raise SystemExit("llama-tts failed. If it says out of memory, close other notebooks and try again. " + (result.stderr or result.stdout)[-300:])
    return time.time() - started


def llm_chat(messages, images=None, options=None, on_token=None):
    """Ask the language model. messages is a list like [{"role": "user", "content": "Hello"}].
    images (optional): a list of JPEG pictures as bytes, for the last message. on_token(text) is called for every piece of the answer.
    Returns a dict: text, first_token_s (time to the first word), tokens, tokens_per_s, total_s."""
    import base64
    import json
    messages = [dict(m) for m in messages]
    if images:
        if not llm_vision():
            raise SystemExit("The server runs text only, so it cannot see pictures. One student runs  labview.llm_start(vision=True)  "
                             "(it restarts the server for the team, about 30 seconds).")
        parts = [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(i).decode()}}
                 for i in images]
        messages[-1]["content"] = parts + [{"type": "text", "text": messages[-1]["content"]}]
    options = dict(options or {})
    if "num_predict" in options:                       # the name that some other programs use
        options["max_tokens"] = options.pop("num_predict")
    body = {"messages": messages, "stream": True, "temperature": 0.7, "max_tokens": 400,
            "chat_template_kwargs": {"enable_thinking": False}, **options}
    started = time.time()
    first, text, timings = None, "", {}
    try:
        with open(LLM_USE, "w") as f:
            json.dump({"who": _who(), "time": started}, f)
    except OSError:
        pass
    with _llm("/v1/chat/completions", body) as answer:
        for line in answer:
            line = line.decode().strip()
            if not line.startswith("data:") or line.endswith("[DONE]"):
                continue
            info = json.loads(line[5:])
            if info.get("error"):
                raise SystemExit("The model says: " + str(info["error"]))
            choice = (info.get("choices") or [{}])[0]
            piece = (choice.get("delta") or {}).get("content") or ""
            if piece:
                if first is None:
                    first = time.time() - started
                text += piece
                if on_token:
                    on_token(piece)
            if info.get("timings"):
                timings = info["timings"]
    return {"text": text.strip(), "first_token_s": first or 0.0, "tokens": timings.get("predicted_n", 0),
            "tokens_per_s": timings.get("predicted_per_second", 0.0), "total_s": time.time() - started}


def llm_message(messages, tools=None, options=None):
    """Ask the language model for ONE complete answer (not streamed). Use it for tool calling.
    messages: the conversation. tools (optional): a list of tool descriptions. A tool call comes back in message["tool_calls"].
    Returns a dict: message (the answer, with "content" and maybe "tool_calls"), finish ("stop" or "tool_calls"), total_s."""
    import json
    options = dict(options or {})
    body = {"messages": [dict(m) for m in messages], "stream": False, "temperature": 0.0, "max_tokens": 400,
            "chat_template_kwargs": {"enable_thinking": False}, **options}
    if tools:
        body["tools"] = tools
    started = time.time()
    try:
        with open(LLM_USE, "w") as f:
            json.dump({"who": _who(), "time": started}, f)
    except OSError:
        pass
    with _llm("/v1/chat/completions", body) as answer:
        info = json.loads(answer.read())
    if info.get("error"):
        raise SystemExit("The model says: " + str(info["error"]))
    choice = info["choices"][0]
    return {"message": choice["message"], "finish": choice.get("finish_reason"), "total_s": time.time() - started}


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


class train_lock(build_lock):
    """with train_lock():  ...   Training a model uses most of the memory, too. It takes turns with the engine builds (same lock)."""
    waiting = "training a model"
    reason = "Training uses most of the 8 GB memory,"


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
            if w > 800:                                # the camera's own size (640 wide) is kept; only bigger pictures are made smaller
                picture = cv2.resize(picture, (800, max(1, int(h * 800 / w))))
            ok, buf = cv2.imencode(".jpg", picture, [cv2.IMWRITE_JPEG_QUALITY, 88])
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
