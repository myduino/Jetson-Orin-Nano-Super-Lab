import time
import numpy as np

n = 1_000_000
data = list(range(n))

start = time.perf_counter()
total = 0
for x in data:
    total += x * 2
loop_time = time.perf_counter() - start

arr = np.arange(n)
start = time.perf_counter()
total_np = (arr * 2).sum()
numpy_time = time.perf_counter() - start

print(f"Python loop : {loop_time * 1000:.1f} ms")
print(f"NumPy       : {numpy_time * 1000:.1f} ms")
print(f"Speed-up    : {loop_time / numpy_time:.0f}x")
