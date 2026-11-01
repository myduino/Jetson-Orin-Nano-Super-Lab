import sys
import cv2
import torch
from ultralytics import YOLO

image = sys.argv[1] if len(sys.argv) > 1 else "bus.jpg"
conf = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
device = 0 if torch.cuda.is_available() else "cpu"

model = YOLO("yolo26n.pt")
result = model(image, conf=conf, device=device, verbose=False)[0]

print(f"Image: {image}   Confidence limit: {conf}")
print(f"Found {len(result.boxes)} objects:")
for box in result.boxes:
    name = result.names[int(box.cls)]
    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
    print(f"  {name:<12} {float(box.conf):.2f}   box: ({x1}, {y1}) to ({x2}, {y2})")

cv2.imwrite("detected.jpg", result.plot())
print("Saved detected.jpg")
