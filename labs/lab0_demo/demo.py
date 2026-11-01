import os
import time

import cv2
import torch
from ultralytics import YOLO

# ---------------- Settings ----------------
MODEL = "yolo26n_fp16.engine"   # fast model. Falls back to yolo26n.pt
CHALLENGE_SECONDS = 60          # length of the game
CONFIDENCE = 0.40               # how sure the model must be (+ and - change it)
SCALE = 1.5                     # make the window bigger
# ------------------------------------------

device = 0 if torch.cuda.is_available() else "cpu"
if not os.path.exists(MODEL):
    print(f"{MODEL} not found, using yolo26n.pt (slower)")
    MODEL = "yolo26n.pt"
model = YOLO(MODEL, task="detect")


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
                    ("SPACE = start the 60 second challenge", green),
                    (f"+ / - = change the confidence ({conf:.2f})", white),
                    ("Q = quit", white)], 10, 10, 520)
    elif game.state == "playing":
        panel(img, [("MYDUINO AI VISION DEMO", yellow),
                    (f"Time left: {game.time_left(now):4.0f} s", white),
                    (f"Kinds found: {len(game.found)}", green),
                    (f"Confidence: {conf:.2f}  (+ / -)", white)], 10, 10, 380)
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
        lines += [("R = try again   Q = quit", yellow)]
        panel(img, lines, 10, 10, min(w - 20, 620))
    cv2.putText(img, f"{fps:.0f} FPS", (w - 110, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)


def main():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        raise SystemExit("Cannot open the camera. Check the USB cable.")

    game = Game(CHALLENGE_SECONDS)
    conf = CONFIDENCE
    fps, last = 0.0, time.perf_counter()
    print("SPACE = start, R = restart, + / - = confidence, Q = quit")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No frame from the camera.")
            break

        shown, names = see(frame, conf)
        now = time.perf_counter()
        game.update(names, now)
        fps = 0.9 * fps + 0.1 * (1.0 / (now - last))
        last = now

        shown = cv2.resize(shown, None, fx=SCALE, fy=SCALE)
        draw(shown, game, fps, now, conf)
        cv2.imshow("Myduino AI Vision Demo", shown)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key in (ord("+"), ord("=")):
            conf = min(0.95, conf + 0.05)
        if key in (ord("-"), ord("_")):
            conf = max(0.05, conf - 0.05)
        if key == ord(" ") and game.state == "ready":
            game.start(now)
        if key == ord("r"):
            game.start(now)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
