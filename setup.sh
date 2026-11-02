#!/bin/bash
# Run ONCE after cloning this folder:   bash setup.sh
# Needs internet. Safe to run again.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Myduino Jetson Orin Nano Super Lab: setup =="
echo "== 1. System packages =="
sudo apt update
sudo apt install -y python3-venv python3-pip python3-opencv v4l-utils nano tree htop git

echo "== 1b. jtop monitor (Lab 1) =="
# jetson-stats goes into the system Python, so it must run before the venv is activated
command -v jtop >/dev/null 2>&1 || sudo -H pip3 install -U jetson-stats || echo "jtop did not install. Tell your instructor."

echo "== 2. Python environment =="
mkdir -p ~/venvs
[ -d ~/venvs/jetson ] || python3 -m venv --system-site-packages ~/venvs/jetson
grep -q "alias jet=" ~/.bashrc || echo "alias jet='source ~/venvs/jetson/bin/activate'" >> ~/.bashrc
# "lab 2 C" runs the commands of Lab 2, Part C for you (see lab.sh). Open a new terminal after setup.
sed -i '/^alias lab=/d' ~/.bashrc
echo "alias lab='bash \"$HERE/lab.sh\"'" >> ~/.bashrc
source ~/venvs/jetson/bin/activate
pip install --upgrade pip
pip install "numpy<2" jupyterlab ipywidgets
# OpenCV on the Jetson changes how the CPU handles tiny numbers, so NumPy prints a harmless
# "smallest subnormal" warning. Hide only that one message in this environment.
SITE="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
echo 'import warnings; warnings.filterwarnings("ignore", message="The value of the smallest subnormal")' > "$SITE/myduino_quiet.pth"
# The lab programs and notebooks import labview (camera and live video). This makes it available everywhere in the environment.
echo "$HERE/labs" > "$SITE/myduino_labs.pth"

echo "== 3. CuPy (Lab 5) =="
# CuPy 14 needs NumPy 2, but the Jetson libraries need NumPy 1, so use CuPy 13
pip install "cupy-cuda12x<14" "numpy<2" || echo "CuPy did not install. Tell your instructor."

echo "== 4. PyTorch with GPU =="
# True only if PyTorch imports AND a real calculation runs on the GPU
gpu_ok() { python -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() and float((torch.ones(64,64,device='cuda')@torch.ones(64,64,device='cuda')).sum())==262144.0 else 1)" 2>/dev/null; }
# True if PyTorch imports and reports a GPU (even if the test calculation failed)
sees_gpu() { python -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; }
# Newer PyTorch builds from the Jetson index need the cuDSS library, which plain JetPack does not include.
# This installs it into the course environment and makes the environment find it.
needs_cudss() { python -c "import torch" 2>&1 | grep -q "libcudss"; }
# Makes every new "jet" session find cuDSS (the line is added to the environment once)
persist_cudss() {
  CUDSS_DIR="$(dirname "$(find ~/venvs/jetson -name 'libcudss.so.0' | head -n 1)")"
  [ -d "$CUDSS_DIR" ] || return 1
  grep -q "CUDSS_DIR" ~/venvs/jetson/bin/activate || echo "export LD_LIBRARY_PATH=\"$CUDSS_DIR:\$LD_LIBRARY_PATH\"  # CUDSS_DIR (added by setup.sh)" >> ~/venvs/jetson/bin/activate
  export LD_LIBRARY_PATH="$CUDSS_DIR:$LD_LIBRARY_PATH"
}
fix_cudss() {
  echo "PyTorch needs the cuDSS library. Installing it into the course environment."
  pip install "nvidia-cudss-cu12==0.7.1.6" --no-deps || return 1
  persist_cudss
}
# A PyTorch from an earlier run may be installed but only missing cuDSS
if ! gpu_ok && needs_cudss; then fix_cudss; fi
if gpu_ok; then
  echo "PyTorch with GPU support is already installed."
elif sees_gpu; then
  # PyTorch is fine but the test calculation failed, for example because the GPU memory is full.
  # Do NOT replace a PyTorch that already sees the GPU.
  echo
  echo "PyTorch sees the GPU, but a test calculation on it failed."
  echo "Close JupyterLab, the browser and other programs, then run  bash setup.sh  again."
  echo "The error was:"
  python -c "import torch; print((torch.ones(64,64,device='cuda')@torch.ones(64,64,device='cuda')).sum())" 2>&1 | tail -n 3
  exit 1
else
  echo "Installing the Jetson build of PyTorch (JetPack 6.2, CUDA 12.6). This is a large download."
  pip install torch torchvision --index-url https://pypi.jetson-ai-lab.io/jp6/cu126 --force-reinstall
  pip install "numpy<2"
  if needs_cudss; then fix_cudss; fi
  if gpu_ok; then
    echo "PyTorch with GPU support is working."
  else
    echo
    echo "PyTorch is installed but cannot run on the GPU (or the install failed)."
    echo "A missing library can cause this. Run: python -c \"import torch\" and send the message to your instructor."
    echo "Do NOT run a plain 'pip install torch'. Tell your instructor what is shown above."
    exit 1
  fi
fi

# If cuDSS is already in the environment (for example from an earlier run), make sure it is found in every session
if find ~/venvs/jetson -name 'libcudss.so.0' 2>/dev/null | grep -q .; then persist_cudss; fi

echo "== 5. Ultralytics =="
# -U because an older Ultralytics may already be on the board and YOLO26 needs a recent one
pip install -U ultralytics
pip uninstall -y opencv-python opencv-python-headless 2>/dev/null
echo "Note: pip may now print a red ERROR about opencv-python. This is expected and harmless. The course uses the OpenCV that comes with JetPack."
# The SciPy that comes with Ubuntu is too old for NumPy 1.26 and prints a warning
# onnx and onnxslim are needed by the TensorRT export in Lab 8 (Ultralytics would install them during the lab otherwise)
pip install "numpy<2" "cupy-cuda12x<14" "scipy>=1.11,<1.15" "onnx>=1.12.0,<2.0.0" "onnxslim>=0.1.82"

echo "== 5b. AI model files (Lab 7) =="
# Downloaded once here, so the labs need no internet. Safe to run again (files that exist are not downloaded again).
mkdir -p ~/students/_shared/models ~/students/_shared/engines
( cd ~/students/_shared/models && python -c "from ultralytics import YOLO; [YOLO(n) for n in ('yolo26n-cls.pt', 'yolo26n.pt', 'yolo26s.pt')]" ) \
  || echo "The model files did not download. Check the internet and run this script again, or tell your instructor."
# The two sample pictures that come with Ultralytics (bus.jpg and zidane.jpg), kept beside the models
( cd ~/students/_shared/models && python -c "import glob, os, shutil, ultralytics; a = os.path.join(os.path.dirname(ultralytics.__file__), 'assets'); [shutil.copy(f, '.') for f in glob.glob(a + '/*.jpg')]" ) \
  || echo "The sample pictures were not copied. Tell your instructor."
echo "Model files in ~/students/_shared/models: $(ls ~/students/_shared/models/*.pt 2>/dev/null | wc -l) of 3"

echo "== 6. Lab workspace =="
# Every student gets a folder of their own when they type "lab start" (~/students/<name>).
# A folder from an earlier version of this course: keep the models, leave the rest where it is.
if [ -d ~/jetson-labs ] && [ ! -L ~/jetson-labs ]; then
  for f in ~/jetson-labs/models/*; do [ -e "$f" ] && [ ! -e ~/students/_shared/models/"${f##*/}" ] && cp -R "$f" ~/students/_shared/models/; done
  echo "Your old folder ~/jetson-labs was not changed. Copy files from it to your own folder if you need them."
fi

echo "== 7. Check =="
python "$HERE/verify_setup.py"
echo
echo "Setup finished. Start the demo with:   bash run_demo.sh"
