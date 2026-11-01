import time
import cv2

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not cap.isOpened():
    raise SystemExit("Cannot open the camera.")

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
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, 255 if mode == "edges" else (0, 255, 0), 2)

    cv2.imshow("Jetson Live", shown)
    key = cv2.waitKey(1) & 0xFF
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
cv2.destroyAllWindows()
