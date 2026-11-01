import cupy as cp

add_squares = cp.ElementwiseKernel(
    "float32 x, float32 y",    # inputs
    "float32 z",               # output
    "z = x * x + y * y",       # runs once for every element
    "add_squares",
)

x = cp.arange(10, dtype=cp.float32)
y = cp.ones(10, dtype=cp.float32)
z = add_squares(x, y)
print(z)
