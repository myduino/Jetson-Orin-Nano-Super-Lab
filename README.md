# Myduino Jetson Orin Nano Super Lab (JetPack 6.2)

Hands-on lab code for the Myduino Jetson Orin Nano Super Training Bundle. No Linux background needed.
The lab manuals (Word files) are in Google Classroom.

## Start Here (on the Jetson)

```bash
cd ~
git clone https://github.com/ariffinzulkifli/jetson-orin-nano-super-lab.git
cd jetson-orin-nano-super-lab
bash setup.sh        # once, needs internet, takes a while
bash run_demo.sh     # Lab 0 AI vision demo
bash run_jupyter.sh  # notebooks for the labs
```

No `git`? On GitHub press **Code, then Download ZIP**, extract it in your Home folder and rename the folder to `jetson-orin-nano-super-lab`.

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
- `setup.sh`, `run_demo.sh`, `run_jupyter.sh`, `verify_setup.py`: setup and launchers.

## Starting Again

If you break something, delete this folder and clone it again.

## Status

The code was checked on a development machine (CPU only), not yet on a Jetson.
