# Myduino Jetson Orin Nano Super Lab (JetPack 6.2)

Hands-on lab code for the Myduino Jetson Orin Nano Super Training Bundle. No Linux background needed.
The lab manuals (PDF files) are in Google Classroom.

## Start Here (on the Jetson)

```bash
cd ~
git clone https://github.com/myduino/Jetson-Orin-Nano-Super-Lab.git
cd Jetson-Orin-Nano-Super-Lab
bash setup.sh        # once, needs internet, takes a while
bash run_demo.sh     # Lab 0 AI vision demo
bash run_jupyter.sh  # notebooks for the labs
```

No `git`? On GitHub press **Code, then Download ZIP**, extract it in your Home folder and rename the folder to `Jetson-Orin-Nano-Super-Lab`.

After setup, open a **new terminal**. A helper called `lab` types the lab commands for you:

```bash
lab          # list of the labs and their parts
lab 2        # the parts of Lab 2
lab 2 A      # run Part A of Lab 2
```

The manuals still show every command, so you can also type them yourself.

## Course Flow

| Lab | Title | Where you work |
|---|---|---|
| 0 | See It First: AI Vision Demo | Terminal |
| 1 | Introduction to Jetson Orin Nano Super (JetPack 6.2) | Terminal |
| 2 | Ubuntu Linux Essentials (Part 1) | Terminal |
| 3 | Ubuntu Linux Essentials (Part 2) | Terminal |
| 4 | Python on Jetson | Terminal, then Jupyter |
| 5 | NVIDIA CUDA with Python | Terminal and Jupyter |
| 6 | Image Processing with OpenCV | Terminal and Jupyter |
| 7 | AI Vision and Inference | Terminal and Jupyter |
| 8 | Optimisation with TensorRT | Terminal only |
| 9 | Mini Project | Terminal |

## Folders

- `labs/`: example code for each lab (reference copies). Labs 5, 6 and 7 include a notebook.
- `lab.sh` and `labs/lib.sh`: the `lab` helper. Each lab folder has a script such as `labs/lab2_linux1/lab2.sh`.
- `setup.sh`, `run_demo.sh`, `run_jupyter.sh`, `verify_setup.py`: setup and launchers.

## Starting Again

If you break something, delete this folder and clone it again. Your own work is in `~/jetson-labs`.

The notebooks of Labs 5, 6 and 7 (and the pictures they save) are inside this folder. Copy `labs/lab5_cuda`, `labs/lab6_opencv` and `labs/lab7_ai_vision` to a safe place first if you want to keep your results.

## Status

Tested on a Jetson Orin Nano Super with JetPack 6.2, Labs 0 to 9.
