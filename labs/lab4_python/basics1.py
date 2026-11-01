board = "Jetson Orin Nano Super"
cpu_cores = 6
memory_gb = 8
power_modes = ["15W", "25W", "MAXN SUPER"]

print("Board:", board)
print(f"{board} has {cpu_cores} CPU cores and {memory_gb} GB of memory")
print("Memory per core:", memory_gb / cpu_cores)
print("Whole GB per core:", memory_gb // cpu_cores)
print("Left over:", memory_gb % cpu_cores)
print("Type of cpu_cores:", type(cpu_cores))
print("Number of power modes:", len(power_modes))
