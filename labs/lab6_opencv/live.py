import time
import cv2
from labview import Viewer, open_camera

cap = open_camera()
view = Viewer()

mode = "normal"
fps = 0.0
last = time.perf_counter()

print("Keys: n = normal, g = gray, b = blur, e = edges, s = save picture, q = quit")
while True:
    ok, frame = cap.read()
    if not ok:
        print("No frame from the camera.")
        break

    if mode == "gray":
        shown = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    elif mode == "blur":
        shown = cv2.GaussianBlur(frame, (21, 21), 0)
    elif mode == "edges":
        shown = cv2.Canny(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 50, 150)
    else:
        shown = frame.copy()

    now = time.perf_counter()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - last))
    last = now
    cv2.putText(shown, f"{mode}  {fps:.0f} FPS", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, 255 if mode in ("gray", "edges") else (0, 255, 0), 2)

    view.show("Myduino Live", shown)
    key = view.key()
    if key == ord("q"):
        break
    elif key == ord("n"):
        mode = "normal"
    elif key == ord("g"):
        mode = "gray"
    elif key == ord("b"):
        mode = "blur"
    elif key == ord("e"):
        mode = "edges"
    elif key == ord("s"):
        cv2.imwrite("saved.png", shown)
        print("Saved saved.png")

cap.release()
view.close()
