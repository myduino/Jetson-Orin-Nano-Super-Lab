import time
import torch

device = "cuda"
sizes = [256, 512, 1024, 2048]

# Warm-up
w = torch.rand(64, 64, device=device)
_ = w @ w
torch.cuda.synchronize()

for n in sizes:
    a = torch.rand(n, n, device=device)
    b = torch.rand(n, n, device=device)
    torch.cuda.synchronize()

    times = []
    for _ in range(5):
        start = time.perf_counter()
        c = a @ b
        torch.cuda.synchronize()
        times.append(time.perf_counter() - start)
    print(f"{n} x {n} matrix multiply: {min(times) * 1000:.2f} ms")
