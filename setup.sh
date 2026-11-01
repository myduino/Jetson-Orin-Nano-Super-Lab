#!/bin/bash
# Run ONCE after cloning this folder:   bash setup.sh
# Needs internet. Safe to run again.  NOT TESTED ON A JETSON YET.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== 1. System packages =="
sudo apt update
sudo apt install -y python3-venv python3-pip python3-opencv v4l-utils nano tree htop git

echo "== 2. Python environment =="
mkdir -p ~/venvs
[ -d ~/venvs/jetson ] || python3 -m venv --system-site-packages ~/venvs/jetson
grep -q "alias jet=" ~/.bashrc || echo "alias jet='source ~/venvs/jetson/bin/activate'" >> ~/.bashrc
source ~/venvs/jetson/bin/activate
pip install --upgrade pip
pip install "numpy<2" jupyterlab

echo "== 3. CuPy (Lab 5) =="
pip install cupy-cuda12x || echo "CuPy did not install. Tell your instructor."

echo "== 4. PyTorch with GPU =="
# True only if PyTorch imports AND a real calculation runs on the GPU
gpu_ok() { python -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() and float((torch.ones(64,64,device='cuda')@torch.ones(64,64,device='cuda')).sum())==262144.0 else 1)" 2>/dev/null; }
if gpu_ok; then
  echo "PyTorch with GPU support is already installed."
else
  echo "Installing the Jetson build of PyTorch (JetPack 6.2, CUDA 12.6). This is a large download."
  pip install torch torchvision --index-url https://pypi.jetson-ai-lab.io/jp6/cu126 --force-reinstall
  pip install "numpy<2"
  if gpu_ok; then
    echo "PyTorch with GPU support is working."
  else
    echo
    echo "PyTorch is installed but cannot run on the GPU (or the install failed)."
    echo "A missing library (for example cuDSS) can cause this. Run: python -c \"import torch\" and send the message to your instructor."
    echo "Do NOT run a plain 'pip install torch'. Tell your instructor what is shown above."
    exit 1
  fi
fi

echo "== 5. Ultralytics =="
pip install ultralytics
pip uninstall -y opencv-python opencv-python-headless 2>/dev/null
pip install "numpy<2"

echo "== 6. Lab workspace =="
mkdir -p ~/jetson-labs
for n in 1 2 3 4 5 6 7 8 9; do mkdir -p ~/jetson-labs/lab$n; done

echo "== 7. Check =="
python "$HERE/verify_setup.py"
echo
echo "Setup finished. Start the demo with:   bash run_demo.sh"
