import time
import cupy as cp

sizes = [256, 512, 1024, 2048]

# Warm-up: the first GPU call loads libraries and prepares the GPU
w = cp.random.rand(64, 64, dtype=cp.float32)
_ = w @ w
cp.cuda.Device().synchronize()

for n in sizes:
    a = cp.random.rand(n, n, dtype=cp.float32)
    b = cp.random.rand(n, n, dtype=cp.float32)
    cp.cuda.Device().synchronize()

    times = []
    for _ in range(5):
        start = time.perf_counter()
        c = a @ b
        cp.cuda.Device().synchronize()
        times.append(time.perf_counter() - start)
    print(f"{n} x {n} matrix multiply: {min(times) * 1000:.2f} ms")
