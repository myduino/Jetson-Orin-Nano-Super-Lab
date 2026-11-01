import sys
import torch
from ultralytics import YOLO

image = sys.argv[1] if len(sys.argv) > 1 else "bus.jpg"
device = 0 if torch.cuda.is_available() else "cpu"

model = YOLO("yolo26n-cls.pt")
result = model(image, device=device, verbose=False)[0]

print(f"Image: {image}   Image size: {result.orig_shape}")
print(f"Model knows {len(result.names)} classes")
print("Top 5 guesses:")
for rank, i in enumerate(result.probs.top5, start=1):
    print(f"  {rank}. {result.names[i]:<20} {float(result.probs.data[i]) * 100:5.1f} %")
print(f"Inference time: {result.speed['inference']:.1f} ms")
