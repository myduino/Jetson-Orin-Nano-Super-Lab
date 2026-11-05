# Myduino Jetson Orin Nano Super Lab (JetPack 6.2)

Hands-on lab code for the Myduino Jetson Orin Nano Super Training Bundle. No Linux background needed.
The lab manuals (PDF files) are in Google Classroom. Every lab is also a notebook, and the notebooks are the main way to learn.

## How the class works

```
Teacher PC (Windows)                      Jetson 1, Jetson 2, ...
 the teacher page  <------ reports ------  the lab agent (starts by itself when the Jetson starts)
 classes, students ------- assigns ------> a JupyterLab for each student, with the camera the teacher chose
```

The teacher puts each student on a Jetson and a camera, on the teacher page. The page shows an **address** (for example `192.168.0.234:8881`) and a **PIN** for the student. The student opens the address in a browser, types the PIN once, and works in their own JupyterLab. **No SSH, no terminal and no command are needed to start.** Everything happens in the browser: the Linux commands, the Python code and the live camera all run inside the notebooks.

## Setup (once)

**1. On the teacher's Windows PC** (needs Python 3: `winget install Python.Python.3.12`, and Git):

```powershell
git clone https://github.com/myduino/Jetson-Orin-Nano-Super-Lab.git
cd Jetson-Orin-Nano-Super-Lab
powershell -ExecutionPolicy Bypass -File .\setup-teacher.ps1
```

The first time, it asks you to choose a teacher password. It prints the address of the teacher page and a **class key**, and keeps running: leave that window open while you teach. It opens port 8800 in Windows Firewall (run PowerShell as Administrator once if it cannot). On Mac or Linux use `bash setup-teacher.sh`.

**2. On each Jetson** (open a terminal, once):

```bash
cd ~
git clone https://github.com/myduino/Jetson-Orin-Nano-Super-Lab.git
cd Jetson-Orin-Nano-Super-Lab
bash setup-lab.sh <address of the teacher page> <class key>
```

The teacher page prints this exact line. `setup-lab.sh` installs JupyterLab and the lab agent, and the agent starts by itself whenever the Jetson starts. Refresh the teacher page: the Jetson appears in the list.

**3. Install the AI software, once for each Jetson:** put one student (or yourself) on the Jetson and run **Part 0 of the Lab 0 notebook**. It installs CuPy, PyTorch and Ultralytics with visible steps, and takes 20 to 40 minutes. Then every student runs Part 0b, which downloads their own AI models (about 60 MB).

No `git`? On GitHub press **Code, then Download ZIP** and extract it.

## Every class

1. Switch on the Jetsons (network cable or Wi-Fi) and plug in the cameras (up to 3 for each Jetson). Start the teacher page on your PC.
2. On the teacher page: make a class, add the students' names, and for each student choose the **Jetson** and the **camera**.
3. Tell each student their address and PIN: "Amira, awak masuk 192.168.0.234:8881, PIN 482913".
4. After the course, **Remove** the students (it deletes their folders on the Jetson). Python and the installed packages stay.

The teacher page shows: every Jetson (online or not, IP address, cameras and who uses them), every class with every student's address, PIN and state (running or not), and buttons to make a class, add students, change a PIN, and remove a student or a class. If a Jetson was off, the students on it start again by themselves when it comes back.

## The student folder is the environment

`~/myduino-jetson-lab/<class>/<student>/` on the Jetson holds the notebooks, pictures, engines, the AI models, and the Jupyter, IPython and shell settings of one student. Only the Python packages (`~/venvs/jetson`) are shared, because PyTorch is several GB. Each student has their own port (8881, 8882, ...), which stays the same. Students share one Linux account, so a student could delete another's folder by hand: this is a classroom, not a secure system.

## Course Flow

| Lab | Title |
|---|---|
| 0 | See It First: AI Vision Demo (with the one-time setup) |
| 1 | Introduction to Jetson Orin Nano Super (JetPack 6.2) |
| 2 | Ubuntu Linux Essentials (Part 1) |
| 3 | Ubuntu Linux Essentials (Part 2) |
| 4 | Python on Jetson |
| 5 | NVIDIA CUDA with Python |
| 6 | Image Processing with OpenCV |
| 7 | AI Vision and Inference |
| 8 | Optimisation with TensorRT |
| 9 | Mini Project |

## Folders

- `labs/`: the master notebooks of the labs (`labs/lab2_linux1/lab2_linux1.ipynb` and so on) and `start_here.ipynb`. Each student works on copies in their own folder.
- `labs/teacher_server.py`: the teacher page (runs on the teacher PC). `setup-teacher.ps1` and `setup-teacher.sh` start it.
- `labs/agent.py`: the lab agent (runs on each Jetson). `setup-lab.sh` installs it as a service (`myduino-lab-agent`).
- `labs/labview.py`: helpers for the notebooks (camera, live video, `sudo` login, one TensorRT build at a time).
- `labs/lab0_demo/demo.py`: the Lab 0 AI vision game.
- `lab.sh`, `labs/lib.sh`: the small `lab` command (`lab me`, `lab reset 4` in a JupyterLab Terminal tab; `lab cameras` and `lab check` for the teacher).
- `verify_setup.py`: the check used by Lab 0.

## Notes for the teacher

- The Jetsons and the teacher PC must be on the same network and reach each other. Some school Wi-Fi blocks devices from talking to each other: use a switch or router with cables, or a Wi-Fi without client isolation. Give the teacher PC a fixed IP address, or the Jetsons lose it after a restart.
- If the teacher PC is switched off, the running JupyterLabs continue, but you cannot change who is where.
- Several students can share a Jetson (2 to 3 is the safe number). Give each of them a different camera. The camera labs (6, 7 Part D, 8 Part D, 9) and the timing tests (Lab 5 F, Lab 7 E, Lab 8 C and E) give the best results when only one student runs them at a time.
- Each student builds their own TensorRT engines in Lab 8. Only one build runs at a time, because a build uses most of the 8 GB memory. The next student waits.
- `sudo` in a notebook: the student types the password once in a hidden box (`labview.sudo_login()`). It stays in that notebook's memory only.
- Anyone who has a student's address and PIN can run commands on that Jetson, and anyone who knows the teacher password can change the classes. Use a classroom network. Both pages use plain HTTP.
- `lab check` on a Jetson shows changes in the course folder and offers to undo them, sets the power mode to MAXN SUPER, clears the command history and lists the student folders.

## Starting Again

If you break something on a Jetson, delete the course folder and clone it again, then run `setup-lab.sh` again. The student folders are in `~/myduino-jetson-lab` and are not touched.

## Status

Tested on a Jetson Orin Nano Super with JetPack 6.2, Labs 0 to 9 (the earlier terminal version). The teacher page, the agent and the notebook flow were tested with stand-ins and have not run on real hardware yet.
