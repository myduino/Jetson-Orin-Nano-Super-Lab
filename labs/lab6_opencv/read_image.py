import cv2

img = cv2.imread("test.png")
if img is None:
    raise SystemExit("Cannot read test.png. Run make_image.py first.")

print("Shape:", img.shape)
print("Type:", img.dtype)
print("Pixel at row 100, column 100 (B, G, R):", img[100, 100])
print("Pixel at row 160, column 450 (B, G, R):", img[160, 450])

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print("Gray shape:", gray.shape)
cv2.imwrite("gray.png", gray)
print("Saved gray.png")
