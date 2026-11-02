import cv2
from labview import Viewer, open_camera
import numpy as np

cap = open_camera(mjpg=False)
view = Viewer()

# Blue objects. Change these numbers to track another colour.
low = np.array([100, 120, 70])
high = np.array([130, 255, 255])
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

print("Hold a blue object in front of the camera. Press q to quit.")
while True:
    ok, frame = cap.read()
    if not ok:
        break
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, low, high)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        biggest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(biggest) > 800:
            x, y, w, h = cv2.boundingRect(biggest)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"centre ({x + w // 2}, {y + h // 2})", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    view.show("Myduino Colour Tracker", frame)
    view.show("Mask", mask)
    if view.key() == ord("q"):
        break

cap.release()
view.close()
