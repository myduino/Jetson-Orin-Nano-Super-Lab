import csv
import os
import time
from datetime import datetime

import cv2
import torch
from ultralytics import YOLO

# ---------------- Settings you can change ----------------
TARGET = "person"        # the class to count (any of the 80 class names)
ALERT_AT = 3             # alert when this many or more are in view
CONFIDENCE = 0.40        # confidence limit
COOLDOWN = 5             # seconds between two alerts
MODEL = "yolo26n_fp16.engine"
# ----------------------------------------------------------

device = 0 if torch.cuda.is_available() else "cpu"
if not os.path.exists(MODEL):
    print(f"{MODEL} not found, using yolo26n.pt instead (slower)")
    MODEL = "yolo26n.pt"
model = YOLO(MODEL, task="detect")


def analyse(frame):
    """Run the model on one frame. Return the drawn picture and the count."""
    result = model(frame, conf=CONFIDENCE, device=device, verbose=False)[0]
    count = sum(1 for c in result.boxes.cls if result.names[int(c)] == TARGET)
    return result.plot(), count


def log_alert(count):
    """Add one line to the alerts log file (alerts.csv)."""
    now = datetime.now()
    first = not os.path.exists("alerts.csv")
    with open("alerts.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if first:
            writer.writerow(["time", "class", "count"])
        writer.writerow([now.strftime("%Y-%m-%d %H:%M:%S"), TARGET, count])


def main():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        raise SystemExit("Cannot open the camera.")

    fps = 0.0
    last = time.perf_counter()
    last_alert = 0.0
    print(f"Counting '{TARGET}'. Alert at {ALERT_AT} or more. Press q to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No frame from the camera.")
            break

        shown, count = analyse(frame)
        now = time.perf_counter()
        fps = 0.9 * fps + 0.1 * (1.0 / (now - last))
        last = now

        alert = count >= ALERT_AT
        colour = (0, 0, 255) if alert else (0, 255, 0)
        cv2.putText(shown, f"{TARGET}: {count}   {fps:.0f} FPS", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, colour, 2)

        if alert:
            cv2.putText(shown, "ALERT", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            if now - last_alert > COOLDOWN:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(f"alert_{stamp}.jpg", shown)
                log_alert(count)
                print(f"ALERT: {count} {TARGET} at {stamp}")
                last_alert = now

        cv2.imshow("Mini Project", shown)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
