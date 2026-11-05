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

**1. On the teacher's PC (Windows or Mac):** no Python, no Git and no terminal. Copy the app from the folder `myduino-jetson-lab/` of this repository:

- Windows: `myduino-jetson-lab.exe` (double-click; no install). If Windows asks about the network, choose Allow. If SmartScreen warns, choose More info, then Run anyway.
- Mac with Apple chip (M1 or newer): `myduino-jetson-lab-mac-arm64.dmg`. Intel Mac: `myduino-jetson-lab-mac-x64.dmg`. Open it and drag the app to Applications. The first time, right-click the app, choose Open, then Open again (the app is not signed).

The app window shows the **class key**. Use it in step 2.

**2. On each Jetson** (open a terminal, once):

```bash
cd ~
git clone https://github.com/myduino/Jetson-Orin-Nano-Super-Lab.git
cd Jetson-Orin-Nano-Super-Lab
bash setup-lab.sh <address of the teacher page> <class key>
```

The teacher page prints this exact line. `setup-lab.sh` installs JupyterLab and the lab agent, and the agent starts by itself whenever the Jetson starts. Refresh the teacher page: the Jetson appears in the list.

**3. Each student sets up their own environment:** when a student first starts, the agent makes their own Python environment (`.venv` in their folder, 2 to 3 minutes; the teacher page shows "preparing"). Then the student runs the **Lab 0 notebook**: **Part 0** installs the system programs once for the whole Jetson (the first student does it, the others skip it), and **Part 0b** installs CuPy, PyTorch, Ultralytics and the AI models into **the student's own environment** (about 10 minutes and 1.5 GB each, with the steps visible). Students can do Part 0b at the same time.

No `git`? On GitHub press **Code, then Download ZIP** and extract it.

## Every class

1. Switch on the Jetsons (network cable or Wi-Fi) and plug in the cameras (up to 3 for each Jetson). Open **Myduino Jetson Lab** on your PC and click **START LAB**. The teacher portal opens and the Jetsons start the student sessions.
2. On the teacher page: make a class, add the students' names, and for each student choose the **Jetson** and the **camera**.
3. Tell each student their address and PIN: "Amira, awak masuk 192.168.0.234:8881, PIN 482913".
4. When the class ends, ask the students to save, then click **END LAB**. Every student session on every Jetson stops and students cannot open Jupyter. Their files stay. The next class starts again with **START LAB**.
5. After the course, **Remove** the students (it deletes their folders on the Jetson). Python and the installed packages stay.

The teacher page shows: every Jetson (online or not, IP address, cameras and who uses them), every class with every student's address, PIN and state (running or not), and buttons to make a class, add students, change a PIN, and remove a student or a class. If a Jetson was off, the students on it start again by themselves when it comes back.

## What the lab leaves on a Jetson

Only two folders of the lab live in the home folder of a Jetson:

- `~/Jetson-Orin-Nano-Super-Lab`: the cloned repo (the code and the master notebooks).
- `~/myduino-jetson-lab`: everything else, as `<class>/<student>/`, plus the agent's settings (`.agent.json`), the shared locks (`.locks`) and one shared download cache for pip (`.cache/pip`, which makes the second student's install faster).

**The student folder is the environment.** `~/myduino-jetson-lab/<class>/<student>/` holds the notebooks, pictures, engines, the AI models, the Python environment (`.venv`, about 2 GB with PyTorch) and all the settings, history and temporary files of one student. A student's JupyterLab and its Terminal tab run with `HOME` set to that folder, so `~` is the student folder and no program writes anywhere else. A student who installs or breaks a package only affects their own environment. Removing a student on the teacher page deletes all of it. Each student has their own port (8881, 8882, ...), which stays the same. Students share one Linux account, so a student could delete another's folder by hand: this is a classroom, not a secure system.

Outside those two folders there are only two things, because Linux needs them: the system programs that Part 0 of Lab 0 installs with `apt` (OpenCV, camera tools, jtop, and so on), and one service file, `/etc/systemd/system/myduino-lab-agent.service`, that starts the agent when the Jetson starts. To remove the service: `sudo systemctl disable --now myduino-lab-agent && sudo rm /etc/systemd/system/myduino-lab-agent.service`.

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
- `myduino-jetson-lab/`: the teacher app (Windows `.exe`, Mac `.dmg`). Only the built programs are kept here.
- `labs/agent.py`: the lab agent (runs on each Jetson). `setup-lab.sh` installs it as a service (`myduino-lab-agent`). It makes each student's folder and Python environment and starts their JupyterLab.
- `labs/labview.py`: helpers for the notebooks (camera, live video, `sudo` login, one TensorRT build at a time).
- `labs/lab0_demo/demo.py`: the Lab 0 AI vision game.
- `lab.sh`, `labs/lib.sh`: the small `lab` command (`lab me` and `lab reset 4` in a JupyterLab Terminal tab, where `lab` is ready; for the teacher: `bash lab.sh cameras` and `bash lab.sh check` in this folder).
- `verify_setup.py`: the check used by Lab 0.

## Notes for the teacher

- The Jetsons and the teacher PC must be on the same network and reach each other. Some school Wi-Fi blocks devices from talking to each other: use a switch or router with cables, or a Wi-Fi without client isolation. Give the teacher PC a fixed IP address, or the Jetsons lose it after a restart.
- If the teacher PC is switched off or the app is closed, each Jetson stops its student sessions after 15 minutes without news. Student files stay.
- Several students can share a Jetson (2 to 3 is the safe number). Give each of them a different camera. The camera labs (6, 7 Part D, 8 Part D, 9) and the timing tests (Lab 5 F, Lab 7 E, Lab 8 C and E) give the best results when only one student runs them at a time.
- Each student builds their own TensorRT engines in Lab 8. Only one build runs at a time, because a build uses most of the 8 GB memory. The next student waits.
- `sudo` in a notebook: the student types the password once in a hidden box (`labview.sudo_login()`). It stays in that notebook's memory only.
- Anyone who has a student's address and PIN can run commands on that Jetson, and the teacher portal opens only on the teacher PC itself. Use a classroom network. Student pages use plain HTTP.
- `lab check` on a Jetson shows changes in the course folder and offers to undo them, sets the power mode to MAXN SUPER, clears the command history and lists the student folders.

## Starting Again

If you break something on a Jetson, delete the course folder and clone it again, then run `setup-lab.sh` again. The student folders (with their environments) are in `~/myduino-jetson-lab` and are not touched.

## Status

Tested on a Jetson Orin Nano Super with JetPack 6.2, Labs 0 to 9 (the earlier terminal version). The teacher page, the agent and the notebook flow were tested with stand-ins and have not run on real hardware yet.
