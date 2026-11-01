import torch
import tensorrt
import ultralytics

print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("TensorRT version:", tensorrt.__version__)
print("Ultralytics version:", ultralytics.__version__)
