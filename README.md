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

**1. On the teacher's PC (Windows or Mac):** no Python, no Git and no terminal. Download the app from the [latest release](https://github.com/myduino/Jetson-Orin-Nano-Super-Lab/releases/latest):

- Windows: [myduino-jetson-lab.exe](https://github.com/myduino/Jetson-Orin-Nano-Super-Lab/releases/latest/download/myduino-jetson-lab.exe) (double-click; no install). If Windows asks about the network, choose Allow. If SmartScreen warns, choose More info, then Run anyway.
- Mac with Apple chip (M1 or newer): [myduino-jetson-lab-mac-arm64.dmg](https://github.com/myduino/Jetson-Orin-Nano-Super-Lab/releases/latest/download/myduino-jetson-lab-mac-arm64.dmg). Intel Mac: [myduino-jetson-lab-mac-x64.dmg](https://github.com/myduino/Jetson-Orin-Nano-Super-Lab/releases/latest/download/myduino-jetson-lab-mac-x64.dmg). Open it and drag the app to Applications. The first time, right-click the app, choose Open, then Open again (the app is not signed).

**2. Add each Jetson in the portal (no terminal on the Jetson).** Open the app: the window is the teacher portal. Under **Jetsons**, type the Jetson's IP address, user name and password (find the IP on the Jetson with `hostname -I`) and click **Add**. Then click **SETUP**. The app connects over SSH, downloads the course folder (only the student part) to `~/Jetson-Orin-Nano-Super-Lab`, and runs `labs-setup.sh`, which installs JupyterLab and the lab agent (the agent starts by itself whenever the Jetson starts). The steps show live in the portal, and the Jetson turns **online** when it is done (a few minutes). The password is saved on the teacher PC so SETUP can be run again later (it updates the Jetson). The Jetson needs internet, the same network as the teacher PC, and SSH on (it is on by default).

By hand instead, on the Jetson: `git clone https://github.com/myduino/Jetson-Orin-Nano-Super-Lab.git ~/Jetson-Orin-Nano-Super-Lab && bash ~/Jetson-Orin-Nano-Super-Lab/labs-setup.sh <teacher PC address:8800> <class key> jetson_01` (the app window shows the class key).

**3. Each student sets up their own environment:** when a student first starts, the agent makes their own Python environment (`.venv` in their folder, 2 to 3 minutes; the teacher page shows "preparing"). Then the student runs the **Lab 0 notebook**: **Part 0** installs the system programs once for the whole Jetson (the first student does it, the others skip it), and **Part 0b** installs CuPy, PyTorch, Ultralytics and the AI models into **the student's own environment** (about 10 minutes and 1.5 GB each, with the steps visible). Students can do Part 0b at the same time.

## Every class

1. Switch on the Jetsons (network cable or Wi-Fi) and plug in the cameras (up to 3 for each Jetson). Double-click **Myduino Jetson Lab** on your PC. The window is the teacher portal.
2. Once, in the **Students** tab: make a class, add the students' names, and for each student choose the **Jetson** and the **camera**.
3. Each time before the class: open the portal, go to **Students**, open the class tab and click **Start Lab**. The Jetsons start the Jupyter of that class's students, and each Jetson card shows who uses it.
4. Tell each student their address and PIN: "Amira, awak masuk 192.168.0.234:8881, PIN 482913".
5. When the class ends, ask the students to save and click **End Lab** on the class tab (or close the app window with the X, which asks to end every running class). The student sessions stop and students cannot open Jupyter. Their files stay. Another class can then use the same Jetsons and cameras.
6. After the course, **Remove** the students (it deletes their folders on the Jetson). Python and the installed packages stay.

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

- `labs-student/`: the master notebooks of the labs (`labs-student/lab2_linux1/lab2_linux1.ipynb` and so on) and `start_here.ipynb`. Each student works on copies in their own folder.
- `labs-teacher/`: where to download the teacher app (Windows `.exe`, Mac `.dmg`). The programs are in the GitHub Releases, not in the repository.
- `labs-student/agent.py`: the lab agent (runs on each Jetson). `labs-setup.sh` installs it as a service (`myduino-lab-agent`). It makes each student's folder and Python environment and starts their JupyterLab.
- `labs-student/labview.py`: helpers for the notebooks (camera, live video, `sudo` login, one TensorRT build at a time).
- `labs-student/lab0_demo/demo.py`: the Lab 0 AI vision game.
- `labs-student/verify_setup.py`: the check used by Lab 0.

## Notes for the teacher

- The Jetsons and the teacher PC must be on the same network and reach each other. Some school Wi-Fi blocks devices from talking to each other: use a switch or router with cables, or a Wi-Fi without client isolation. Give the teacher PC a fixed IP address, or the Jetsons lose it after a restart.
- If the teacher PC is switched off or the app is closed, each Jetson stops its student sessions after 15 minutes without news. Student files stay.
- Several students can share a Jetson (2 to 3 is the safe number). Give each of them a different camera. The camera labs (6, 7 Part D, 8 Part D, 9) and the timing tests (Lab 5 F, Lab 7 E, Lab 8 C and E) give the best results when only one student runs them at a time.
- Each student builds their own TensorRT engines in Lab 8. Only one build runs at a time, because a build uses most of the 8 GB memory. The next student waits.
- `sudo` in a notebook: the student types the password once in a hidden box (`labview.sudo_login()`). It stays in that notebook's memory only.
- Anyone who has a student's address and PIN can run commands on that Jetson, and the teacher portal opens only on the teacher PC itself. Use a classroom network. Student pages use plain HTTP.

## Starting Again

If you break something on a Jetson, delete the course folder and clone it again, then run `labs-setup.sh` again. The student folders (with their environments) are in `~/myduino-jetson-lab` and are not touched.

## Status

## The labs

| Labs | Topic | Notes |
|---|---|---|
| 0 to 3 | Demo, the Jetson, Linux | |
| 4 to 6 | Python, CUDA, OpenCV | |
| 7 to 9 | AI vision, TensorRT, mini project | |
| 10 to 15 | Tracking, pose, segmentation and zones, OCR and QR, your own model, deploy and alarm | Camera |
| 16 to 18 | Speech to text, keyword spotting, text to speech | USB microphone (the webcam microphone works) and a speaker |
| 19 to 21 | Local chatbot, ask the camera, voice assistant | Uses llama.cpp (built by `labs-setup.sh`); one student per Jetson starts the server in Lab 19 and the others use it |
| 22 to 24 | AIoT with the ESP32-S3 over MQTT, smart door, sensor streams and dashboard | The Jetson does the AI, the ESP32 does the IoT. A virtual ESP32 is built in, so the labs run before the board arrives. |
| 25 | Capstone | |

The program for the ESP32-S3 is in `labs-student/esp32/` (`main.py` and `config.py`). The pins in `config.py` are placeholders: change them to match your wiring.

Tested on a Jetson Orin Nano Super with JetPack 6.2, Labs 0 to 9 (the earlier terminal version). The teacher page, the agent and the notebook flow were tested with stand-ins and have not run on real hardware yet.

The new Labs 10 to 25 have been tested only with simulations (a fake MQTT broker, a virtual ESP32, synthetic sounds and pictures). They have not yet run on the Jetson with a real microphone, an ESP32 board and the downloaded models.
