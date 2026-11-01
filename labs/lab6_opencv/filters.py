import cv2
import numpy as np

img = cv2.imread("test.png")

# Add noise so the filters have something to remove
noise = np.random.normal(0, 25, img.shape)
noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
cv2.imwrite("noisy.png", noisy)

box = cv2.blur(noisy, (5, 5))
gauss = cv2.GaussianBlur(noisy, (5, 5), 0)
median = cv2.medianBlur(noisy, 5)
cv2.imwrite("blur_box.png", box)
cv2.imwrite("blur_gauss.png", gauss)
cv2.imwrite("blur_median.png", median)

kernel = np.array([[0, -1, 0],
                   [-1, 5, -1],
                   [0, -1, 0]], dtype=np.float32)
sharp = cv2.filter2D(img, -1, kernel)
cv2.imwrite("sharpen.png", sharp)

def error(a):
    return float(np.mean(np.abs(a.astype(np.float32) - img.astype(np.float32))))

print("Average error compared with the clean image:")
print("  noisy  :", round(error(noisy), 1))
print("  box    :", round(error(box), 1))
print("  gauss  :", round(error(gauss), 1))
print("  median :", round(error(median), 1))
