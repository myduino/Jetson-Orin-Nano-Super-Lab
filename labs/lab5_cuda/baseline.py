import time
import numpy as np

sizes = [256, 512, 1024, 2048]
for n in sizes:
    a = np.random.rand(n, n).astype(np.float32)
    b = np.random.rand(n, n).astype(np.float32)
    start = time.perf_counter()
    c = a @ b
    elapsed = time.perf_counter() - start
    print(f"{n} x {n} matrix multiply: {elapsed * 1000:.1f} ms")
