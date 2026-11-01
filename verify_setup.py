"""Checks the setup. Run inside the (jetson) environment."""
import importlib, platform, subprocess

def show(name, value):
    print(f"{name:<22}{value}")

show("Python", platform.python_version())
for mod in ["numpy", "scipy", "cv2", "cupy", "torch", "torchvision", "ultralytics", "tensorrt", "onnx"]:
    try:
        m = importlib.import_module(mod)
        show(mod, getattr(m, "__version__", "ok"))
    except Exception as e:
        show(mod, f"MISSING ({type(e).__name__})")
try:
    import numpy, torch, cv2
    show("numpy is 1.x", numpy.__version__.startswith("1."))
    show("CUDA for PyTorch", torch.cuda.is_available())
except Exception:
    pass
out = subprocess.run("pip list 2>/dev/null | grep -i opencv", shell=True, capture_output=True, text=True).stdout
show("pip opencv (want none)", out.strip() or "none")
print("\nExpect: numpy 1.x, CUDA True, no pip opencv-python.")
