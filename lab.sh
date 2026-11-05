#!/bin/bash
# The lab command (small jobs). The students do not start anything: the teacher puts each student on a Jetson on the
# teacher page, and the lab agent starts the student's JupyterLab.
#   In a JupyterLab Terminal tab of a student:
#     lab me         shows who you are and where your folder is
#     lab reset 5    gives you a fresh copy of the Lab 5 notebook
#   On the Jetson (teacher):
#     lab cameras    lists the cameras that are plugged in
#     lab check      reset the board for the next class
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB="$1"
source "$HERE/labs/lib.sh"

case "$LAB" in
  me)           ensure_student && echo "You are $(basename "$LAB_HOME") in class $LAB_CLASS. Your folder: $LAB_HOME"; exit $? ;;
  reset)        ensure_student && lab_reset "$2"; exit $? ;;
  cameras)      echo "Cameras plugged in:"; cameras_show; exit 0 ;;
  check)        lab_check "$2"; exit $? ;;
esac

[ -n "$LAB" ] && echo "Unknown command: lab $LAB"
echo "Students: your teacher gives you an address (IP:port) and a PIN. Open the address in your browser."
echo "Commands: lab me, lab reset <lab number> (in a JupyterLab Terminal tab), lab cameras, lab check (teacher)."
exit 1
