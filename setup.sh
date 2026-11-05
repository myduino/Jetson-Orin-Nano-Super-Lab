#!/bin/bash
# Run ONCE after cloning this folder:   bash setup.sh
# Needs internet. Safe to run again. It only installs what JupyterLab needs.
# The rest of the setup (CuPy, PyTorch, Ultralytics, models) is done in the Lab 0 notebook, where you can watch it.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Myduino Jetson Orin Nano Super Lab: setup =="
echo "== 1. Python tools =="
sudo apt update
sudo apt install -y python3-venv python3-pip git

echo "== 2. Python environment =="
mkdir -p ~/venvs
[ -d ~/venvs/jetson ] || python3 -m venv --system-site-packages ~/venvs/jetson
grep -q "alias jet=" ~/.bashrc || echo "alias jet='source ~/venvs/jetson/bin/activate'" >> ~/.bashrc
# "lab start yourname" opens your JupyterLab (see lab.sh). Open a new terminal after this script.
sed -i '/^alias lab=/d' ~/.bashrc
echo "alias lab='bash \"$HERE/lab.sh\"'" >> ~/.bashrc
source ~/venvs/jetson/bin/activate
pip install --upgrade pip
pip install "numpy<2" jupyterlab ipywidgets openpyxl
# OpenCV on the Jetson changes how the CPU handles tiny numbers, so NumPy prints a harmless
# "smallest subnormal" warning. Hide only that one message in this environment.
SITE="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
echo 'import warnings; warnings.filterwarnings("ignore", message="The value of the smallest subnormal")' > "$SITE/myduino_quiet.pth"
# The lab notebooks import labview (camera, live video, sudo). This makes it available everywhere in the environment.
echo "$HERE/labs" > "$SITE/myduino_labs.pth"
mkdir -p ~/myduino-jetson-lab

echo
echo "Setup finished. Open a NEW terminal and type:   lab start yourname class yourclass camera 0"
echo "Then open the link in your browser and follow the Lab 0 notebook to finish the setup."
