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
lab start yourname   # (new terminal) your JupyterLab with the lab notebooks
```

No `git`? On GitHub press **Code, then Download ZIP**, extract it in your Home folder and rename the folder to `Jetson-Orin-Nano-Super-Lab`.

After setup, open a **new terminal**. Every time you work, open a terminal (or connect with `ssh orin_nano@<address of the Jetson>`) and type `lab start yourname camera 0` (use the same name every time, and the camera number your teacher gives you). It prints a link: open it in the browser and the Start Here page with all the lab notebooks appears. Type `exit` when you finish. Your own copies are saved in your own folder, `~/students/<your name>`, so updating this folder never changes your answers and other students on the same Jetson cannot overwrite your work. `lab reset 4` gives you a fresh copy of the Lab 4 notebook.

A helper called `lab` also types the lab commands for you:

```bash
lab start yourname camera 0   # your folder, your camera and your JupyterLab
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

If you break something, delete this folder and clone it again. Your own work is in `~/students/<your name>`.

The notebooks of Labs 5, 6 and 7 (and the pictures they save) are inside this folder. Copy `labs/lab5_cuda`, `labs/lab6_opencv` and `labs/lab7_ai_vision` to a safe place first if you want to keep your results.

## Status

Tested on a Jetson Orin Nano Super with JetPack 6.2, Labs 0 to 9.

## For the Teacher

Several students can use one Jetson at the same time (2 to 3 is the safe number), each from their own laptop over SSH, and different students can use it in different sessions.

**What the student does** (the same every time):

```bash
ssh orin_nano@<address of the Jetson>     # on the laptop
lab start siti camera 0                   # on the Jetson: siti's folder, camera 0, siti's JupyterLab
```

`lab start` prints a JupyterLab link for the student's laptop browser and gives a shell with the Python environment on and the prompt `(siti)`. Typing `exit` stops that student's JupyterLab and frees the camera. Programs that show live video print a second link for the browser, and the keys are pressed in the terminal.

**What the teacher does:**

```bash
lab cameras               # the cameras that are plugged in (up to 3) and who uses them
lab clean                 # list the students and their folder sizes
lab clean siti            # delete one student's folder (ask them to copy their work first)
lab stop siti             # free the JupyterLab and camera of a student whose connection was lost
lab check                 # reset the board for the next session
lab mail                  # once: the spare mail account that sends the Lab 9 alert emails
lab mail test you@example.com   # send a test email
```

- **Lab 9 alert emails:** run `lab mail` once. It asks for the SMTP server, the port, the sender address and an app password, and keeps them in `~/.lab_mail`. Use a spare account made for the class (for Gmail: turn on 2-step verification and make an app password), never a personal account: the students share the Linux account and could read the file. Students only type their own address in the Lab 9 notebook. The Jetson needs internet for the emails. `lab mail test <your address>` checks it. If no class account is set up, the notebook asks the student for a spare account instead.
- Cameras are numbered 0, 1, 2 in the order they are found. A camera can be used by one student at a time. A student who asks for a camera that is taken gets a message.
- Each student builds their own TensorRT engines in Lab 8. Only one build runs at a time, because a build uses most of the 8 GB memory. The next student waits.
- `lab check` shows changes in the course folder and offers to undo them, sets the power mode to MAXN SUPER, clears the command history, shows the running students and lists the folders.
- The camera labs (6, 7 Part D, 8 Part D, 9) and all the timing tests (Lab 5 F, Lab 7 E, Lab 8 C and E) give the best results when only one student runs them at a time.
- Anyone who has a student's JupyterLab link can run commands on the Jetson. Use a classroom network.
- The model files are in `~/students/_shared`.
