import cupy as cp

code = r'''
extern "C" __global__
void add_arrays(const float* a, const float* b, float* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        out[i] = a[i] + b[i];
    }
}
'''
add_arrays = cp.RawKernel(code, "add_arrays")

n = 1_000_000
a = cp.random.rand(n, dtype=cp.float32)
b = cp.random.rand(n, dtype=cp.float32)
out = cp.empty_like(a)

threads_per_block = 256
blocks = (n + threads_per_block - 1) // threads_per_block
add_arrays((blocks,), (threads_per_block,), (a, b, out, cp.int32(n)))
cp.cuda.Device().synchronize()

print("Threads per block:", threads_per_block)
print("Blocks:", blocks)
print("Check:", bool(cp.allclose(out, a + b)))
