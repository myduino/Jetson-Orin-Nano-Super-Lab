#!/bin/bash
# Runs the commands of one lab part for you.
#   lab start siti camera 0   starts your environment: your folder, your camera, your JupyterLab, a ready shell
#                             (type exit when you finish). Without "camera 0" no camera is chosen.
#   lab cameras    lists the cameras that are plugged in and who uses them
#   lab me         shows who you are and where your folder is
#   lab reset 5    gives you a fresh copy of the Lab 5 notebook
# Teacher:
#   lab clean siti        delete the folder of a student     lab clean   lists the students
#   lab check             reset the board for the next session
#   lab stop siti         free the JupyterLab and the camera of a student whose connection was lost
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
  start)        lab_start "${@:2}"; exit $? ;;
  me)           ensure_student && echo "You are $(basename "$LAB_HOME"). Your folder: $LAB_HOME"; exit $? ;;
  reset)        ensure_student && lab_reset "$2"; exit $? ;;
  cameras)      echo "Cameras plugged in:"; cameras_show; exit 0 ;;
  stop)         lab_stop "$2"; exit $? ;;
  clean)        lab_clean "$2"; exit $? ;;
  check)        lab_check "$2"; exit $? ;;
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

ensure_student || exit 1
export EXTRA="$3"
export PYTHONPATH="$HERE/labs${PYTHONPATH:+:$PYTHONPATH}"
source ~/venvs/jetson/bin/activate 2>/dev/null
LABNUM="$LAB"
source "$SCRIPT"
if [ -z "$PART" ]; then
  show_parts
  exit 0
fi
main "$PART"
