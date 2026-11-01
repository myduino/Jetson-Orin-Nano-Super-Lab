power_modes = ["15W", "25W", "MAXN SUPER"]
limits = {"15W": 15, "25W": 25, "MAXN SUPER": None}

for mode in power_modes:
    limit = limits[mode]
    if limit is None:
        print(mode, "has no fixed power limit")
    elif limit >= 25:
        print(mode, "is a high power mode")
    else:
        print(mode, "is a low power mode")

count = 0
while count < 3:
    print("Loop number", count)
    count += 1

squares = [n * n for n in range(1, 6)]
print("Squares:", squares)
