#!/bin/bash
# Run ONCE on each Jetson after cloning this folder:
#     bash labs-setup.sh <teacher address:port> <class key> [name of this Jetson]
# Give each Jetson a different name (for example jetson-01). Without one the name is made from the host name and a short
# code of this Jetson, because Jetsons flashed from the same image have the same host name.
# The teacher page prints the exact line (for example:  bash labs-setup.sh 192.168.0.10:8800 1a2b3c4d).
# Needs internet. Safe to run again. It installs the lab agent. The agent starts by itself whenever the Jetson starts and
# reports to the teacher page. When the teacher puts a student on this Jetson, the agent makes that student's own Python
# environment (JupyterLab, 2 to 3 minutes) in the student's folder and starts their JupyterLab.
# The rest of the setup (CuPy, PyTorch, Ultralytics) is done by each student in the Lab 0 notebook, where they can watch it.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEACHER="$1"; KEY="$2"; NAME="$3"
[ -n "$TEACHER" ] || read -r -p "Teacher page address (for example 192.168.0.10:8800): " TEACHER
[ -n "$KEY" ] || read -r -p "Class key (shown on the teacher PC): " KEY
case "$TEACHER" in *:*) ;; *) TEACHER="$TEACHER:8800" ;; esac
if [ -z "$NAME" ]; then NAME="$(hostname | tr 'A-Z-' 'a-z_')_$(cut -c1-4 /etc/machine-id 2>/dev/null)"; fi
NAME="$(printf '%s' "$NAME" | tr 'A-Z-' 'a-z_' | sed 's/[^a-z0-9_]/_/g' | cut -c1-20)"

echo "== Myduino Jetson Orin Nano Super Lab: setup of this Jetson =="
echo "== 1. Python tools =="
sudo apt update
sudo apt install -y python3-venv python3-pip git curl

echo "== 2. The lab folder =="
# Only two folders of the lab live in the home folder: this one, and ~/myduino-jetson-lab (the students and the settings).
# Older versions of this script wrote an alias into ~/.bashrc and a settings file in the home folder: remove them.
sed -i '/^alias lab=/d;/^alias jet=/d' ~/.bashrc 2>/dev/null
rm -f ~/.lab_agent.json
mkdir -p ~/myduino-jetson-lab

echo "== 3. Power mode =="
command -v nvpmodel > /dev/null && sudo nvpmodel -m 2 && echo "Power mode: MAXN SUPER"

echo "== 4. The lab agent =="
printf '{"teacher": "%s", "key": "%s", "id": "%s"}\n' "$TEACHER" "$KEY" "$NAME" > ~/myduino-jetson-lab/.agent.json
chmod 600 ~/myduino-jetson-lab/.agent.json
sudo tee /etc/systemd/system/myduino-lab-agent.service > /dev/null <<UNIT
[Unit]
Description=Myduino lab agent (starts the JupyterLab of the students)
After=network-online.target
Wants=network-online.target

[Service]
User=$(id -un)
WorkingDirectory=$HERE
ExecStart=/usr/bin/python3 $HERE/labs-student/agent.py
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
echo "Each student then runs Lab 0: Part 0 (system programs, once for this Jetson) and Part 0b (their own AI packages and models)."
