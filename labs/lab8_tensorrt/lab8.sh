#!/bin/bash
# Lab 8: Optimisation with TensorRT.   Run a part with:   lab 8 A   (or B, C, D, E)
# Part B builds your own engines. If another student is building, you wait (the memory fits one build).
# Everything in this lab runs in the terminal. Close JupyterLab first to free memory.

LAB_TITLE="Optimisation with TensorRT"
PARTS=(
  "A|Create the workspace, check TensorRT and the power mode"
  "B|Build the FP32 and FP16 engines (takes about 12 minutes)"
  "C|Benchmark: compare speed of the model and the engines"
  "D|Live FPS with TensorRT (a window, or a link for your laptop browser)"
  "E|Speed and power modes (switches 15W, 25W and MAXN SUPER, about 2 minutes)"
)

LABDIR="$(dirname "$SCRIPT")"
WORK="$LAB_HOME"/lab8

prepare() {
  mkdir -p "$WORK"
  for f in check_trt.py export_trt.py benchmark_trt.py live_trt.py; do
    [ -f "$WORK/$f" ] || cp "$LABDIR/$f" "$WORK/$f"
  done
  for f in yolo26n.pt bus.jpg; do
    [ -f "$WORK/$f" ] || cp "$LAB_HOME"/models/$f "$WORK/" 2>/dev/null
  done
}

partA() {
  title "Part A, Step 1: Create the workspace"
  run cd "$LAB_HOME"
  run mkdir -p lab8
  prepare
  run cd lab8
  run ls
  pause
  title "Part A, Step 2: Check TensorRT"
  run python check_trt.py
  pause
  title "Part A, Step 3: Check the power mode"
  run sudo nvpmodel -q
  say "The mode should be MAXN_SUPER for Parts A to D."
  pause
}

partB() {
  prepare
  title "Part B, Step 1: Export the FP32 and FP16 engines"
  say "Close your notebooks first (in JupyterLab: Kernel, Shut Down All Kernels). The build needs most of the memory."
  say "This takes about 4 minutes for FP32 and about 8 minutes for FP16. Do not close the terminal."
  say "Red or yellow lines starting with [TRT] are normal."
  pause
  # Building uses most of the 8 GB memory, so students who share the Jetson build one after the other.
  build_acquire
  trap build_release EXIT INT TERM
  run cd "$WORK"
  run python export_trt.py
  build_release
  trap - EXIT INT TERM
  run "ls -lh *.engine *.onnx *.pt"
  pause
}

partC() {
  prepare
  title "Part C, Step 1: Compare speed"
  run cd "$WORK"
  run python benchmark_trt.py
  pause
}

partD() {
  prepare
  title "Part D: Live FPS with TensorRT"
  say "Two runs, one after the other. Press q to quit each run."
  say "On the Jetson's own screen a window opens (press q in it). Over SSH, open the link that the program prints in the browser of your laptop and press the keys here in the terminal. Read the FPS on the screen for each run."
  pause
  run cd "$WORK"
  say "Run 1: the plain PyTorch model"
  run python live_trt.py yolo26n.pt
  say "Run 2: the FP16 TensorRT engine"
  run python live_trt.py yolo26n_fp16.engine
  pause
}

partE() {
  prepare
  title "Part E: Speed and power modes"
  say "For each mode the script switches, waits 10 seconds and runs the benchmark."
  say "Open jtop in a second terminal tab and note the GPU temperature after each run."
  say "sudo may ask for your password."
  pause
  run cd "$WORK"
  run "grep POWER_MODEL /etc/nvpmodel.conf"
  for m in 0 1 2; do
    case $m in 0) name="15W";; 1) name="25W";; 2) name="MAXN SUPER";; esac
    title "Power mode $name (mode $m)"
    run sudo nvpmodel -m $m
    run sudo nvpmodel -q
    countdown 10 "Letting the clocks settle:"
    run "python benchmark_trt.py 2>&1 | grep -E 'FPS'"
    pause
  done
  say "Mode 2 (MAXN SUPER) is active again. Write your results in the table in your manual."
}

main() {
  case "$1" in
    A) partA ;;
    B) partB ;;
    C) partC ;;
    D) partD ;;
    E) partE ;;
    *) show_parts ;;
  esac
}
