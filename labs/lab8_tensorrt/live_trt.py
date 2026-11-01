import sys
import time
import cv2
import torch
from ultralytics import YOLO

device = 0 if torch.cuda.is_available() else "cpu"
name = sys.argv[1] if len(sys.argv) > 1 else "yolo26n_fp16.engine"
model = YOLO(name, task="detect")
print("Using model:", name)

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not cap.isOpened():
    raise SystemExit("Cannot open the camera.")

conf = 0.40
fps = 0.0
last = time.perf_counter()
print("Keys: + / - = change confidence limit, s = save picture, q = quit")

while True:
    ok, frame = cap.read()
    if not ok:
        print("No frame from the camera.")
        break

    result = model(frame, conf=conf, device=device, verbose=False)[0]
    shown = result.plot()

    counts = {}
    for c in result.boxes.cls:
        name = result.names[int(c)]
        counts[name] = counts.get(name, 0) + 1
    summary = ", ".join(f"{n}: {k}" for n, k in counts.items()) or "nothing found"

    now = time.perf_counter()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - last))
    last = now
    cv2.putText(shown, f"{fps:.0f} FPS  conf {conf:.2f}", (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(shown, summary, (10, 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Myduino Live Detection", shown)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key in (ord("+"), ord("=")):
        conf = min(0.95, conf + 0.05)
    elif key == ord("-"):
        conf = max(0.05, conf - 0.05)
    elif key == ord("s"):
        cv2.imwrite("live_saved.jpg", shown)
        print("Saved live_saved.jpg")

cap.release()
cv2.destroyAllWindows()
