#!/bin/bash
# Lab 7: AI Vision and Inference.   Run a part with:   lab 7 A   (or D)
# Parts B, C and E are done in the notebook that Part A opens.

LAB_TITLE="AI Vision and Inference"
PARTS=(
  "A|Open the Lab 7 notebook (checks, sample pictures and models)"
  "B|In the notebook (start it with: lab 7 A)"
  "C|In the notebook (start it with: lab 7 A)"
  "D|Live detection on the USB camera (a window opens on the Jetson screen)"
  "E|In the notebook (start it with: lab 7 A)"
)

LABDIR="$(dirname "$SCRIPT")"
WORK=~/jetson-labs/lab7

partA() {
  title "Part A, Step 1: Create the workspace"
  run cd ~/jetson-labs
  run mkdir -p lab7
  run cd lab7
  pause
  say "JupyterLab opens next, in the Lab 7 notebook folder. Leave this terminal open."
  say "To stop JupyterLab later, come back here, press Ctrl + C and answer y."
  pause
  run bash "$HERE/run_jupyter.sh"
}

partNB() {
  say "This part is done in the Lab 7 notebook. Open it with:  lab 7 A"
}

partD() {
  mkdir -p "$WORK"
  [ -f "$WORK/live_detect.py" ] || cp "$LABDIR/live_detect.py" "$WORK/live_detect.py"
  [ -f "$WORK/yolo26n.pt" ] || cp ~/jetson-labs/models/yolo26n.pt "$WORK/" 2>/dev/null
  title "Part D, Step 1: Run live detection"
  say "A window opens on the Jetson screen. Press q in the window to quit. Run this on the Jetson desktop, not over SSH."
  say "Close the notebook tab and stop JupyterLab first (Ctrl + C in its terminal) to free memory."
  pause
  run cd "$WORK"
  run python live_detect.py
}

main() {
  case "$1" in
    A) partA ;;
    B|C|E) partNB ;;
    D) partD ;;
    *) show_parts ;;
  esac
}
