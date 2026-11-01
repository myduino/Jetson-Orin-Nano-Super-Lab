import cv2
import numpy as np

img = cv2.imread("test.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

b, g, r = cv2.split(img)
print("Mean of blue, green, red channels:",
      round(float(b.mean()), 1), round(float(g.mean()), 1), round(float(r.mean()), 1))

# Find the red circle using HSV. Red is near hue 0 (and near 180)
low1, high1 = np.array([0, 120, 70]), np.array([10, 255, 255])
low2, high2 = np.array([170, 120, 70]), np.array([180, 255, 255])
mask = cv2.inRange(hsv, low1, high1) | cv2.inRange(hsv, low2, high2)

print("Red pixels found:", int(cv2.countNonZero(mask)))
cv2.imwrite("mask_red.png", mask)
result = cv2.bitwise_and(img, img, mask=mask)
cv2.imwrite("only_red.png", result)
print("Saved mask_red.png and only_red.png")
