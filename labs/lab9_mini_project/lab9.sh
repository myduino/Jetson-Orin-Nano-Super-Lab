#!/bin/bash
# Lab 9: Mini Project.   The lab is in the notebook:   lab 9 N
# The terminal version (mini_project.py) is for working without the notebook: lab 9 A, B, R. It writes alerts.csv only (the notebook also writes an Excel file).

LAB_TITLE="Mini Project"
PARTS=(
  "N|Open the Lab 9 notebook: the whole lab, with the Excel log"
  "A|Terminal version: create the workspace and copy the model files from Lab 8"
  "B|Terminal version: run the starter program (CSV log only)"
  "R|Terminal version: show the alert pictures and alerts.csv"
)

LABDIR="$(dirname "$SCRIPT")"
WORK="$LAB_HOME"/lab9

partA() {
  title "Part A, Step 1: Create the workspace"
  run cd "$LAB_HOME"
  run mkdir -p lab9
  run cd lab9
  # Copy what exists. A missing Lab 8 engine must not stop the lab: the program then uses yolo26n.pt (slower).
  if [ -f ../lab8/yolo26n_fp16.engine ]; then
    run cp ../lab8/yolo26n_fp16.engine .
  else
    say "No FP16 engine found in $LAB_HOME/lab8. That is fine: the program will use yolo26n.pt (slower)."
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
  say "Show objects to the camera. Press q to quit."
  say "On the Jetson's own screen a window opens (press q in it). Over SSH, open the link that the program prints in the browser of your laptop and press the keys here in the terminal. Close other programs first."
  say "Pictures and alerts.csv are saved in $LAB_HOME/lab9. Use  lab 9 R  afterwards to see them."
  pause
  run cd "$WORK"
  run python mini_project.py
  pause
  partR
}

partN() {
  run bash "$HERE/run_jupyter.sh" 9
}

partR() {
  title "The results in $LAB_HOME/lab9"
  run cd "$WORK"
  run "ls alert_*.jpg"
  run cat alerts.csv
}

main() {
  case "$1" in
    N) partN ;;
    A) partA ;;
    B) partB ;;
    R) partR ;;
    *) show_parts ;;
  esac
}
