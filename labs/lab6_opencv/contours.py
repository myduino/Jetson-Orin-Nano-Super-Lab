import cv2

img = cv2.imread("test.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Everything that is strongly coloured (not the dark background)
mask = cv2.inRange(hsv, (0, 150, 180), (180, 255, 255))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print("Objects found:", len(contours))

out = img.copy()
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < 500:
        continue
    x, y, w, h = cv2.boundingRect(cnt)
    cv2.rectangle(out, (x, y), (x + w, y + h), (255, 0, 255), 2)
    print(f"  box at x={x}, y={y}, width={w}, height={h}, area={area:.0f}")
cv2.imwrite("contours.png", out)
