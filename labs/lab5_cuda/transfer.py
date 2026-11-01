import time
import numpy as np
import cupy as cp

n = 4096
a_cpu = np.random.rand(n, n).astype(np.float32)

# Warm-up: the first GPU call loads libraries
_ = cp.asarray(a_cpu)
cp.cuda.Device().synchronize()

start = time.perf_counter()
a_gpu = cp.asarray(a_cpu)
cp.cuda.Device().synchronize()
copy_ms = (time.perf_counter() - start) * 1000

start = time.perf_counter()
b_gpu = a_gpu * 2.0 + 1.0
cp.cuda.Device().synchronize()
calc_ms = (time.perf_counter() - start) * 1000

start = time.perf_counter()
b_cpu = cp.asnumpy(b_gpu)
back_ms = (time.perf_counter() - start) * 1000

print(f"Copy to GPU : {copy_ms:.2f} ms")
print(f"Calculation : {calc_ms:.2f} ms")
print(f"Copy back   : {back_ms:.2f} ms")
