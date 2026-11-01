import os
import sys
import torch
from ultralytics import YOLO

image = sys.argv[1] if len(sys.argv) > 1 else "bus.jpg"
device = 0 if torch.cuda.is_available() else "cpu"
files = ["yolo26n.pt", "yolo26n_fp32.engine", "yolo26n_fp16.engine"]
runs = 30

for f in files:
    if not os.path.exists(f):
        print(f"{f}: file not found, skipped")
        continue

    model = YOLO(f, task="detect")
    for _ in range(5):                          # warm-up
        model(image, device=device, verbose=False)

    times = []
    for _ in range(runs):
        r = model(image, device=device, verbose=False)[0]
        times.append(r.speed["inference"])      # milliseconds, model only

    avg = sum(times) / len(times)
    size = os.path.getsize(f) / 1e6
    print(f"{f:<22} {avg:6.1f} ms  {1000 / avg:6.1f} FPS  "
          f"{size:5.1f} MB  objects found: {len(r.boxes)}")
