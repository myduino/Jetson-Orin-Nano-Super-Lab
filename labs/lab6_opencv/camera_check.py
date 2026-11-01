import cv2

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    raise SystemExit("Cannot open the camera. Check the USB cable and /dev/video0.")

print("Default size:", cap.get(cv2.CAP_PROP_FRAME_WIDTH), "x", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("Default FPS :", cap.get(cv2.CAP_PROP_FPS))

# The first frames are often dark while the camera adjusts
for _ in range(15):
    ok, frame = cap.read()

ok, frame = cap.read()
if not ok:
    raise SystemExit("The camera opened but gave no picture.")

cv2.imwrite("snapshot.jpg", frame)
print("Saved snapshot.jpg", frame.shape)
cap.release()
