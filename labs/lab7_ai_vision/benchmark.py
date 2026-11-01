import sys
import time
import torch
from ultralytics import YOLO

image = sys.argv[1] if len(sys.argv) > 1 else "bus.jpg"
device = 0 if torch.cuda.is_available() else "cpu"
names = ["yolo26n.pt", "yolo26s.pt"]
runs = 30

for name in names:
    model = YOLO(name)
    for _ in range(5):                       # warm-up
        model(image, imgsz=640, device=device, verbose=False)

    times = []
    for _ in range(runs):
        r = model(image, imgsz=640, device=device, verbose=False)[0]
        times.append(r.speed["inference"])   # milliseconds, model only

    avg = sum(times) / len(times)
    print(f"{name:<12} average inference: {avg:6.1f} ms   ({1000 / avg:5.1f} FPS)")
