#!/bin/bash
# Lab 6: Image Processing with OpenCV.   Run a part with:   lab 6 A   (or B, G, T)
# Parts C to F are done in the notebook that Part A opens.

LAB_TITLE="Image Processing with OpenCV"
PARTS=(
  "A|Check OpenCV, then open the Lab 6 notebook"
  "B|Find the USB camera and list what it can do"
  "C|In the notebook (start it with: lab 6 A)"
  "D|In the notebook (start it with: lab 6 A)"
  "E|In the notebook (start it with: lab 6 A)"
  "F|In the notebook (start it with: lab 6 A)"
  "G|Live camera view with filters (a window, or a link for your laptop browser)"
  "T|Challenge: track a coloured object (a window, or a link for your laptop browser)"
)

LABDIR="$(dirname "$SCRIPT")"
WORK="$LAB_HOME"/lab6

partA() {
  title "Part A, Step 1: Create the workspace and check OpenCV"
  run cd "$LAB_HOME"
  run mkdir -p lab6
  run cd lab6
  run 'python -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"'
  run 'python -c "import cv2; print(cv2.cuda.getCudaEnabledDeviceCount())"'
  pause
  say "JupyterLab opens next, in the Lab 6 notebook folder. Leave this terminal open."
  say "To stop JupyterLab later, come back here, press Ctrl + C and answer y."
  pause
  run bash "$HERE/run_jupyter.sh" 6
}

partB() {
  title "Part B, Step 1: Plug in and find the camera"
  run "ls /dev/video*"
  run v4l2-ctl --list-devices
  pause
  title "Part B, Step 2: See what the camera can do"
  run "v4l2-ctl -d ${LAB_CAMERA:-/dev/video0} --list-formats-ext | head -30"
  pause
  say "Step 3 (capture a picture) is in the notebook. Open it with:  lab 6 A"
}

partNB() {
  say "This part is done in the Lab 6 notebook. Open it with:  lab 6 A"
}

partG() {
  mkdir -p "$WORK"
  [ -f "$WORK/live.py" ] || cp "$LABDIR/live.py" "$WORK/live.py"
  title "Part G, Step 1: A live view with filters"
  say "On the Jetson's own screen a window opens (press q in it). Over SSH, open the link that the program prints in the browser of your laptop and press the keys here in the terminal."
  pause
  run cd "$WORK"
  run python live.py
}

partT() {
  mkdir -p "$WORK"
  [ -f "$WORK/track.py" ] || cp "$LABDIR/track.py" "$WORK/track.py"
  title "Challenge: track a coloured object"
  say "Show a coloured object to the camera. Press q to quit. On the Jetson's own screen a window opens (press q in it). Over SSH, open the link that the program prints in the browser of your laptop and press the keys here in the terminal."
  pause
  run cd "$WORK"
  run python track.py
}

main() {
  case "$1" in
    A) partA ;;
    B) partB ;;
    C|D|E|F) partNB ;;
    G) partG ;;
    T) partT ;;
    *) show_parts ;;
  esac
}
