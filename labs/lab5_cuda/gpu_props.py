import cupy as cp

props = cp.cuda.runtime.getDeviceProperties(0)
name = props["name"]
if isinstance(name, bytes):
    name = name.decode()

print("CuPy version:", cp.__version__)
print("GPU count:", cp.cuda.runtime.getDeviceCount())
print("Name:", name)
print("Compute capability:", props["major"], props["minor"])
print("Multiprocessors (SMs):", props["multiProcessorCount"])
print("Max threads per block:", props["maxThreadsPerBlock"])
print("Warp size:", props["warpSize"])
free, total = cp.cuda.runtime.memGetInfo()
print(f"Free / total memory: {free / 1024**3:.2f} / {total / 1024**3:.2f} GB")
