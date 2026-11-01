#!/bin/bash
# Lab 1: Introduction to Jetson Orin Nano Super.   Run a part with:   lab 1 C   (or D, E, F)
# This file is loaded by lab.sh. It shows each command and then runs it for you.

LAB_TITLE="Introduction to Jetson Orin Nano Super"
PARTS=(
  "C|Update the package list (needs the network)"
  "D|Verify the system (release, kernel, memory, disk, Python)"
  "E|Show and change the power mode"
  "F|Monitor the board with jtop"
)

partC() {
  title "Part C: Update the package list"
  say "This needs the network. It may ask for your password."
  run sudo apt update
  pause
}

partD() {
  title "Part D: Verify the system"
  run cat /etc/nv_tegra_release
  run lsb_release -a
  run uname -r
  run free -h
  run df -h /
  run lsblk -d -o NAME,SIZE,MODEL
  run python3 --version
  pause
}

partE() {
  title "Part E: Power modes in the terminal"
  say "sudo may ask for your password."
  say "Show the current power mode:"
  run sudo nvpmodel -q
  say "List the modes available on this board:"
  run grep POWER_MODEL /etc/nvpmodel.conf
  pause
  say "Switch to MAXN SUPER (mode ID 2 on the Orin Nano 8 GB), then confirm:"
  run sudo nvpmodel -m 2
  run sudo nvpmodel -q
  pause
}

partF() {
  title "Part F: Monitor the board with jtop"
  say "jtop opens next. Use the number keys or the arrow keys to move between the pages."
  say "Press q to quit jtop."
  pause
  run jtop
}

main() {
  case "$1" in
    C) partC ;;
    D) partD ;;
    E) partE ;;
    F) partF ;;
    *) show_parts ;;
  esac
}
