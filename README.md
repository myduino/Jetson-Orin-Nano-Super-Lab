# Myduino Jetson Orin Nano Super Lab (JetPack 6.2)

Hands-on lab code for the Myduino Jetson Orin Nano Super Training Bundle. No Linux background needed.
The lab manuals (PDF files) are in Google Classroom.

## Start Here (on the Jetson)

Once per Jetson (needs internet, takes about a minute):

```bash
cd ~
git clone https://github.com/myduino/Jetson-Orin-Nano-Super-Lab.git
cd Jetson-Orin-Nano-Super-Lab
bash setup.sh        # Python environment and JupyterLab only
```

No `git`? On GitHub press **Code, then Download ZIP**, extract it in your Home folder and rename the folder to `Jetson-Orin-Nano-Super-Lab`.

Then open a **new terminal** (or connect with `ssh orin_nano@<address of the Jetson>`). The teacher makes a class once (`lab class add a`), and then each student types:

```bash
lab start yourname class a camera 0
```

Use the same name every time, the class name and the camera number your teacher gives you. It prints a link: open it in the browser and the Start Here page with all the lab notebooks appears. **Everything else happens in the browser.** The Linux commands, the Python code and the live camera all run inside the notebooks, and the commands are shown step by step. The big install (CuPy, PyTorch, Ultralytics) is Part 0 of the Lab 0 notebook, so the students watch it happen. Only the Python packages are shared by the students of a Jetson. Each student downloads their own models (Part 0b).

**The student folder is the environment.** `~/myduino-jetson-lab/<class>/<student>/` holds the notebooks, the pictures, the engines, the AI models, and the Jupyter, IPython and shell settings of that student. Each student also has **their own JupyterLab port** (8801, 8802, ...), chosen once and kept in `.port`, so the port is the same in every session. Type `exit` in the SSH terminal when you finish. Updating this folder never changes the answers, and other students cannot overwrite your work by accident. `lab reset 4` (in a JupyterLab Terminal tab) gives you a fresh copy of the Lab 4 notebook.

Other `lab` commands: `lab cameras` (which cameras are free), `lab me` (who you are).

## Course Flow

| Lab | Title | Where you work |
|---|---|---|
| 0 | See It First: AI Vision Demo (with the one-time setup) | Jupyter notebook |
| 1 | Introduction to Jetson Orin Nano Super (JetPack 6.2) | Jupyter notebook |
| 2 | Ubuntu Linux Essentials (Part 1) | Jupyter notebook (and a Terminal tab for nano) |
| 3 | Ubuntu Linux Essentials (Part 2) | Jupyter notebook |
| 4 | Python on Jetson | Jupyter notebook |
| 5 | NVIDIA CUDA with Python | Jupyter notebook |
| 6 | Image Processing with OpenCV | Jupyter notebook |
| 7 | AI Vision and Inference | Jupyter notebook |
| 8 | Optimisation with TensorRT | Jupyter notebook |
| 9 | Mini Project | Jupyter notebook |

## Folders

- `labs/`: the master notebooks of the labs (`labs/lab2_linux1/lab2_linux1.ipynb` and so on) and `start_here.ipynb`. Students work on copies in their own folder.
- `lab.sh` and `labs/lib.sh`: the `lab` command (`lab start`, `lab cameras`, and the teacher commands). `labs/teacher.py` is the teacher web page.
- `labs/labview.py`: helpers for the notebooks (camera, live video, `sudo` login, one TensorRT build at a time).
- `labs/lab0_demo/demo.py`: the Lab 0 AI vision game.
- `setup.sh`, `verify_setup.py`: the one-time setup of the Jetson (`setup.sh`) and the check used by Lab 0.

## Starting Again

If you break something, delete this folder and clone it again. Your own work is in `~/myduino-jetson-lab/<class>/<your name>`.

## Status

Tested on a Jetson Orin Nano Super with JetPack 6.2, Labs 0 to 9.

## For the Teacher

Several students can use one Jetson at the same time (2 to 3 is the safe number), each from their own laptop over SSH. Different classes can use it in different sessions, and every class has its own folder.

**Once per Jetson:** `bash setup.sh`, then one student (or you) runs Part 0 of the Lab 0 notebook.

**Before a class:**

```bash
lab class add a                  # make the class (students cannot make one by mistake)
lab teacher                      # the teacher web page (asks you to choose a teacher password the first time)
lab cameras                      # the cameras that are plugged in (up to 3)
```

**What the student does** (the same every time):

```bash
ssh orin_nano@<address of the Jetson>     # on the laptop
lab start siti class a camera 0           # on the Jetson: siti's folder in class a, camera 0, siti's JupyterLab
```

`lab start` prints a JupyterLab link for the student's laptop browser and gives a shell with the Python environment on and the prompt `(a/siti)`. Typing `exit` stops that student's JupyterLab and frees the camera.

**The teacher page** (`lab teacher`, then open the address it prints, on port 8800): the cameras and who uses them, and for each class every student with their **port**, state (working or offline), camera, folder size, last use and a link to their JupyterLab. The teacher can make a class and stop a session whose connection was lost. It asks for the teacher password. Deleting stays in the terminal, where you type the name to confirm.

**The same in the terminal:**

```bash
lab classes               # the table of classes: students, size, last used, how many are working now
lab class a               # the students of class a: port, camera, size, last used, state
lab stop a siti           # free the JupyterLab and camera of a student whose connection was lost
lab clean a siti          # delete one student's folder (ask them to copy their work first)
lab clean a               # delete the whole class
lab check                 # reset the board for the next session
```

- Cameras are numbered 0, 1, 2 in the order they are found. A camera can be used by one student at a time. A student who asks for a camera that is taken gets a message.
- Each student builds their own TensorRT engines in Lab 8. Only one build runs at a time, because a build uses most of the 8 GB memory. The next student waits.
- `lab check` shows changes in the course folder and offers to undo them, sets the power mode to MAXN SUPER, clears the command history, shows the running students and lists the classes.
- The camera labs (6, 7 Part D, 8 Part D, 9) and all the timing tests (Lab 5 F, Lab 7 E, Lab 8 C and E) give the best results when only one student runs them at a time.
- `sudo` in a notebook: the student types the password once in a hidden box (`labview.sudo_login()`). It stays in that notebook's memory only.
- Anyone who has a student's JupyterLab link, or the teacher password, can run commands on the Jetson. Use a classroom network. The teacher page is plain HTTP.
