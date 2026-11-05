#!/bin/bash
# Run ONCE on each Jetson after cloning this folder:
#     bash setup-lab.sh <teacher address:port> <class key>
# The teacher page prints the exact line (for example:  bash setup-lab.sh 192.168.0.10:8800 1a2b3c4d).
# Needs internet. Safe to run again. It installs JupyterLab and the lab agent. The agent starts by itself whenever the
# Jetson starts, reports to the teacher page, and starts each student's JupyterLab when the teacher assigns the student.
# The rest of the setup (CuPy, PyTorch, Ultralytics) is done in the Lab 0 notebook, where the students can watch it.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEACHER="$1"; KEY="$2"
[ -n "$TEACHER" ] || read -r -p "Teacher page address (for example 192.168.0.10:8800): " TEACHER
[ -n "$KEY" ] || read -r -p "Class key (shown on the teacher PC): " KEY
case "$TEACHER" in *:*) ;; *) TEACHER="$TEACHER:8800" ;; esac

echo "== Myduino Jetson Orin Nano Super Lab: setup of this Jetson =="
echo "== 1. Python tools =="
sudo apt update
sudo apt install -y python3-venv python3-pip git curl

echo "== 2. Python environment =="
mkdir -p ~/venvs
[ -d ~/venvs/jetson ] || python3 -m venv --system-site-packages ~/venvs/jetson
grep -q "alias jet=" ~/.bashrc || echo "alias jet='source ~/venvs/jetson/bin/activate'" >> ~/.bashrc
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

echo "== 3. The lab agent =="
printf '{"teacher": "%s", "key": "%s"}\n' "$TEACHER" "$KEY" > ~/.lab_agent.json
chmod 600 ~/.lab_agent.json
sudo tee /etc/systemd/system/myduino-lab-agent.service > /dev/null <<UNIT
[Unit]
Description=Myduino lab agent (starts the JupyterLab of the students)
After=network-online.target
Wants=network-online.target

[Service]
User=$(id -un)
WorkingDirectory=$HERE
ExecStart=/usr/bin/python3 $HERE/labs/agent.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable myduino-lab-agent > /dev/null 2>&1
sudo systemctl restart myduino-lab-agent
sleep 3
if curl -s -m 5 "http://$TEACHER/" > /dev/null; then
  echo "The teacher page at $TEACHER answers. Refresh the teacher page: this Jetson should be in the list."
else
  echo "Cannot reach the teacher page at $TEACHER. Check that the teacher PC is on, on the same network,"
  echo "and that Windows Firewall allows port 8800. The agent keeps trying by itself."
fi

echo
echo "Setup finished. Next: the teacher puts a student on this Jetson, and the student opens the address from the teacher page."
echo "The first student runs Part 0 of the Lab 0 notebook, which installs PyTorch, CuPy and Ultralytics (once for this Jetson)."
echo "Open a NEW terminal if you want to use the  lab  command (lab cameras, lab check)."
