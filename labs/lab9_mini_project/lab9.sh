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
  run cp ../lab8/yolo26n_fp16.engine ../lab8/yolo26n.pt .
  [ -f "$WORK/mini_project.py" ] || cp "$LABDIR/mini_project.py" "$WORK/mini_project.py"
  run ls
  say "If the engine is missing, ask your instructor for one, or go on with yolo26n.pt only (slower)."
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
