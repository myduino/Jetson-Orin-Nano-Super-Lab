import time
import numpy as np
import cupy as cp


def time_cpu(x, repeats):
    start = time.perf_counter()
    for _ in range(repeats):
        y = x * 2.0 + 1.0
    return (time.perf_counter() - start) / repeats * 1000


def time_gpu(x, repeats):
    y = x * 2.0 + 1.0  # warm-up
    cp.cuda.Device().synchronize()
    start = time.perf_counter()
    for _ in range(repeats):
        y = x * 2.0 + 1.0
    cp.cuda.Device().synchronize()
    return (time.perf_counter() - start) / repeats * 1000


for n in [100, 10_000, 1_000_000, 10_000_000]:
    x_cpu = np.random.rand(n).astype(np.float32)
    x_gpu = cp.asarray(x_cpu)
    cpu_ms = time_cpu(x_cpu, 20)
    gpu_ms = time_gpu(x_gpu, 20)
    print(f"{n:>10,} items   CPU {cpu_ms:8.3f} ms   GPU {gpu_ms:8.3f} ms")
