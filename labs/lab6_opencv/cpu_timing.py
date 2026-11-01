import time
import cv2
import numpy as np

sizes = [(320, 240), (640, 480), (1280, 720), (1920, 1080)]

for w, h in sizes:
    img = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
    cv2.GaussianBlur(img, (15, 15), 0)            # warm-up
    start = time.perf_counter()
    for _ in range(20):
        cv2.GaussianBlur(img, (15, 15), 0)
    ms = (time.perf_counter() - start) / 20 * 1000
    print(f"{w} x {h}: Gaussian blur {ms:.2f} ms  ({1000 / ms:.0f} per second)")
