#!/bin/bash
# Runs the commands of one lab part for you.
#   lab start      opens JupyterLab with the lab notebooks (lab start 5 opens Lab 5)
#   lab reset 5    gives you a fresh copy of the Lab 5 notebook
#   lab            shows the list of labs
#   lab 2          shows the parts of Lab 2
#   lab 2 C        runs Part C of Lab 2
# (The "lab" shortcut is made by setup.sh. Open a new terminal after setup.)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB="$1"
PART="$(echo "$2" | tr a-z A-Z)"
source "$HERE/labs/lib.sh"

TITLES=(
  "0|See It First"
  "1|Introduction to Jetson Orin Nano Super"
  "2|Ubuntu Linux Essentials, Part 1"
  "3|Ubuntu Linux Essentials, Part 2"
  "4|Python on Jetson"
  "5|NVIDIA CUDA with Python"
  "6|Image Processing with OpenCV"
  "7|AI Vision and Inference"
  "8|Optimisation with TensorRT"
  "9|Mini Project"
)

find_script() { ls "$HERE"/labs/lab"$1"_*/lab"$1".sh 2>/dev/null | head -n 1; }

case "$LAB" in
  start) lab_start "$2"; exit $? ;;
  reset) lab_reset "$2"; exit $? ;;
esac

if [ -z "$LAB" ]; then
  printf '\n%sMyduino Jetson Orin Nano Super Lab%s\n' "$CT" "$CN"
  echo "Type  lab start  to open JupyterLab with all the lab notebooks."
  echo "Type  lab <number> <part>  to run a part, for example:  lab 2 C"
  echo
  for t in "${TITLES[@]}"; do
    n="${t%%|*}"; name="${t#*|}"
    script="$(find_script "$n")"
    if [ -z "$script" ]; then
      printf '%sLab %s  %s%s   (not ready yet)\n\n' "$CT" "$n" "$name" "$CN"
      continue
    fi
    printf '%sLab %s  %s%s\n' "$CT" "$n" "$name" "$CN"
    ( source "$script"; for p in "${PARTS[@]}"; do printf '    lab %s %s   %s\n' "$n" "${p%%|*}" "${p#*|}"; done )
    echo
  done
  echo
  exit 0
fi

SCRIPT="$(find_script "$LAB")"
if [ -z "$SCRIPT" ]; then
  echo "Lab $LAB has no script. Type the commands from your manual, or type  lab  to see the list."
  exit 1
fi

source ~/venvs/jetson/bin/activate 2>/dev/null
LABNUM="$LAB"
source "$SCRIPT"
if [ -z "$PART" ]; then
  show_parts
  exit 0
fi
main "$PART"
