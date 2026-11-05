import os
import time

import cv2

# ---------------- Settings ----------------
MODEL = "yolo26n_fp16.engine"   # fast model (made in Lab 8). Falls back to yolo26n.pt
CHALLENGE_SECONDS = 60          # length of the game
CONFIDENCE = 0.40               # how sure the model must be (the slider changes it)
# ------------------------------------------

model = None
device = "cpu"


def find_model():
    """Your own engine from Lab 8 if you have one, else the plain model from your models folder."""
    home = os.environ.get("LAB_HOME", "")
    for path in (MODEL, os.path.join(home, "lab8", MODEL), os.path.join(home, "models", "yolo26n.pt"), "yolo26n.pt"):
        if os.path.exists(path):
            return path
    return "yolo26n.pt"


def load_model():
    """Load the model once (the first call takes about 20 seconds)."""
    global model, device
    if model is None:
        import labview
        labview.cuda_libs()               # PyTorch needs a library that Lab 0 Step 8 installed
        import torch
        from ultralytics import YOLO
        device = 0 if torch.cuda.is_available() else "cpu"
        path = find_model()
        print(f"Using model: {path}")
        model = YOLO(path, task="detect")
    return model


class Game:
    """Keeps the state of the challenge: ready, playing or done."""

    def __init__(self, seconds):
        self.seconds = seconds
        self.reset()

    def reset(self):
        self.state = "ready"
        self.found = []          # kinds of objects found, in the order found
        self.start_time = 0.0

    def start(self, now):
        self.reset()
        self.state = "playing"
        self.start_time = now

    def time_left(self, now):
        return max(0.0, self.seconds - (now - self.start_time))

    def update(self, names, now):
        """Call once for every frame with the names seen in that frame."""
        if self.state != "playing":
            return
        for name in names:
            if name not in self.found:
                self.found.append(name)
        if self.time_left(now) <= 0:
            self.state = "done"


def see(frame, conf):
    """Run the model. Return the picture with boxes and the set of names."""
    load_model()
    result = model(frame, conf=conf, device=device, verbose=False)[0]
    names = {result.names[int(c)] for c in result.boxes.cls}
    return result.plot(), names


def panel(img, lines, x, y, width):
    """Draw a dark box with lines of text."""
    height = 12 + 28 * len(lines)
    shade = img.copy()
    cv2.rectangle(shade, (x, y), (x + width, y + height), (30, 30, 30), -1)
    cv2.addWeighted(shade, 0.65, img, 0.35, 0, img)
    for i, (text, colour) in enumerate(lines):
        cv2.putText(img, text, (x + 10, y + 26 + 28 * i),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, colour, 2)


def draw(img, game, fps, now, conf):
    """Add the game text on top of the picture."""
    white, green, yellow = (255, 255, 255), (0, 255, 0), (0, 255, 255)
    h, w = img.shape[:2]
    if game.state == "ready":
        panel(img, [("MYDUINO AI VISION DEMO", yellow),
                    ("Show objects to the camera", white),
                    ("Press Start to begin the 60 second challenge", green),
                    (f"Confidence: {conf:.2f}  (slider)", white),
                    ("Stop button = quit", white)], 10, 10, 520)
    elif game.state == "playing":
        panel(img, [("MYDUINO AI VISION DEMO", yellow),
                    (f"Time left: {game.time_left(now):4.0f} s", white),
                    (f"Kinds found: {len(game.found)}", green),
                    (f"Confidence: {conf:.2f}", white)], 10, 10, 380)
        shown = game.found[-10:]
        lines = [(name, white) for name in shown]
        if lines:
            panel(img, lines, w - 250, 10, 240)
    else:
        lines = [("MYDUINO AI VISION DEMO", yellow),
                 ("TIME IS UP!", white),
                 (f"You found {len(game.found)} kinds:", green)]
        lines += [(", ".join(game.found[i:i + 3]), white)
                  for i in range(0, min(len(game.found), 12), 3)]
        lines += [("Press Start to try again", yellow)]
        panel(img, lines, 10, 10, min(w - 20, 620))
    cv2.putText(img, f"{fps:.0f} FPS", (w - 110, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)


def notebook():
    """The same game inside a notebook: Start and Restart buttons, a Confidence slider."""
    from labview import live
    load_model()
    game = Game(CHALLENGE_SECONDS)

    def process(frame, state):
        shown, names = see(frame, state["Confidence"])
        now = time.perf_counter()
        if state.pop("go", False):
            game.start(now)
        game.update(names, now)
        draw(shown, game, state["fps"], now, state["Confidence"])
        return shown

    def start(state):
        state["go"] = True

    return live(process, {"Confidence": (0.05, 0.95, 0.05, CONFIDENCE)}, actions={"Start / Restart": start}, width=800)
