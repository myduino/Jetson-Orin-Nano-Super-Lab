import cv2

gray = cv2.imread("test.png", cv2.IMREAD_GRAYSCALE)

_, fixed = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
otsu_value, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 5)

cv2.imwrite("th_fixed.png", fixed)
cv2.imwrite("th_otsu.png", otsu)
cv2.imwrite("th_adaptive.png", adaptive)
print("Otsu chose the threshold:", otsu_value)
print("White pixels  fixed:", cv2.countNonZero(fixed),
      " otsu:", cv2.countNonZero(otsu), " adaptive:", cv2.countNonZero(adaptive))
