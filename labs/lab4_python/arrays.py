# Lab 4, Part D, Steps 1 and 2: the lines you would type at the Python prompt (>>>).
# lab.sh runs this file and shows each line with its result, like the Python prompt does.
import code

LINES = [
    "import numpy as np",
    "a = np.array([1, 2, 3, 4, 5, 6])",
    "a.shape",
    "a.dtype",
    "m = a.reshape(2, 3)",
    "m",
    "m[1]",
    "m[:, 0]",
    "m * 10",
    "m.sum()",
    "m.mean()",
    "m.sum(axis=0)",
    "",
    "# Step 2: a tiny image",
    "img = np.zeros((5, 5), dtype=np.uint8)",
    "img[1:4, 1:4] = 255",
    "img",
    "img.shape",
    "img.dtype",
]

shell = code.InteractiveInterpreter()
for line in LINES:
    if not line:
        print()
        continue
    if line.startswith("#"):
        print(line)
        continue
    print(">>>", line)
    shell.runsource(line)
