import numpy as np
import cv2

h, w = 480, 640
img = np.zeros((h, w, 3), dtype=np.uint8)

# Background: a blue to dark gradient (BGR order)
for x in range(w):
    img[:, x] = (int(40 + 120 * x / w), 40, 20)

cv2.rectangle(img, (60, 80), (260, 240), (0, 200, 0), -1)      # green box
cv2.circle(img, (450, 160), 80, (0, 0, 255), -1)               # red circle
cv2.rectangle(img, (340, 300), (580, 420), (0, 220, 255), -1)  # yellow box
cv2.line(img, (30, 455), (610, 445), (255, 255, 255), 3)      # white line
cv2.putText(img, "JETSON", (70, 340), cv2.FONT_HERSHEY_SIMPLEX,
            1.8, (255, 255, 255), 4)

cv2.imwrite("test.png", img)
print("Saved test.png", img.shape)
