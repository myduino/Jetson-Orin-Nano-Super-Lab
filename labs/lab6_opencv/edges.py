import sys
import cv2

name = sys.argv[1] if len(sys.argv) > 1 else "test.png"
img = cv2.imread(name)
if img is None:
    raise SystemExit(f"Cannot read {name}")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)

for low, high in [(50, 150), (10, 30), (150, 250)]:
    edges = cv2.Canny(blur, low, high)
    out = f"edges_{low}_{high}.png"
    cv2.imwrite(out, edges)
    print(f"Canny {low}/{high}: {cv2.countNonZero(edges)} edge pixels -> {out}")
