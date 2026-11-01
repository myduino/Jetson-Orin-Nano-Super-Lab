import os
import time
from ultralytics import YOLO

name = "yolo26n"


def build(label, **precision):
    model = YOLO(f"{name}.pt")
    start = time.time()
    path = model.export(format="engine", device=0, **precision)
    new_name = f"{name}_{label}.engine"
    os.replace(path, new_name)   # give each engine its own file name
    size = os.path.getsize(new_name) / 1e6
    print(f"Built {new_name} in {time.time() - start:.0f} s, size {size:.1f} MB")


build("fp32")                    # default precision: 32-bit

try:
    build("fp16", quantize=16)   # 16-bit
except Exception as error:       # older Ultralytics versions use half=True
    print("quantize=16 did not work:", error)
    print("Trying half=True instead")
    build("fp16", half=True)
