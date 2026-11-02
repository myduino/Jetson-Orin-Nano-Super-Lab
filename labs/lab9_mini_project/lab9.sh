#!/bin/bash
# Lab 9: Mini Project.   Run a part with:   lab 9 A   (or B, R)
# Parts C, D and E are your own work: change the settings in mini_project.py with nano.

LAB_TITLE="Mini Project"
PARTS=(
  "A|Create the workspace and copy the model files from Lab 8"
  "B|Run the starter program (a window opens on the Jetson screen)"
  "R|Show the results: the alert pictures and alerts.csv"
)

LABDIR="$(dirname "$SCRIPT")"
WORK=~/jetson-labs/lab9

partA() {
  title "Part A, Step 1: Create the workspace"
  run cd ~/jetson-labs
  run mkdir -p lab9
  run cd lab9
  # Copy what exists. A missing Lab 8 engine must not stop the lab: the program then uses yolo26n.pt (slower).
  if [ -f ../lab8/yolo26n_fp16.engine ]; then
    run cp ../lab8/yolo26n_fp16.engine .
  else
    say "No FP16 engine found in ~/jetson-labs/lab8. That is fine: the program will use yolo26n.pt (slower)."
    say "For the faster engine, run  lab 8 B  first (about 12 minutes), then  lab 9 A  again."
  fi
  if [ -f ../lab8/yolo26n.pt ]; then
    run cp ../lab8/yolo26n.pt .
  elif [ -f ../models/yolo26n.pt ]; then
    run cp ../models/yolo26n.pt .
  else
    say "yolo26n.pt was not found. Run  bash ~/Jetson-Orin-Nano-Super-Lab/setup.sh  or ask your instructor."
  fi
  [ -f "$WORK/mini_project.py" ] || cp "$LABDIR/mini_project.py" "$WORK/mini_project.py"
  run ls
  pause
}

partB() {
  mkdir -p "$WORK"
  [ -f "$WORK/mini_project.py" ] || cp "$LABDIR/mini_project.py" "$WORK/mini_project.py"
  title "Part B: Run the starter program"
  say "A window opens on the Jetson screen. Show objects to the camera. Press q in the window to quit."
  say "Run this on the Jetson desktop, not over SSH. Close other programs first."
  say "Pictures and alerts.csv are saved in ~/jetson-labs/lab9. Use  lab 9 R  afterwards to see them."
  pause
  run cd "$WORK"
  run python mini_project.py
  pause
  partR
}

partR() {
  title "The results in ~/jetson-labs/lab9"
  run cd "$WORK"
  run "ls alert_*.jpg"
  run cat alerts.csv
}

main() {
  case "$1" in
    A) partA ;;
    B) partB ;;
    R) partR ;;
    *) show_parts ;;
  esac
}
