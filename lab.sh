#!/bin/bash
# The lab command. All the labs are notebooks: lab start opens them in your own JupyterLab.
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
source "$HERE/labs/lib.sh"

case "$LAB" in
  start)        lab_start "${@:2}"; exit $? ;;
  me)           ensure_student && echo "You are $(basename "$LAB_HOME"). Your folder: $LAB_HOME"; exit $? ;;
  reset)        ensure_student && lab_reset "$2"; exit $? ;;
  cameras)      echo "Cameras plugged in:"; cameras_show; exit 0 ;;
  stop)         lab_stop "$2"; exit $? ;;
  clean)        lab_clean "$2"; exit $? ;;
  check)        lab_check "$2"; exit $? ;;
esac

[ -n "$LAB" ] && echo "Unknown command: lab $LAB"
echo "Type  lab start <your name> camera 0  to start your JupyterLab. All the labs are notebooks there."
echo "Other commands: lab cameras, lab me, lab reset <lab number>. Teacher: lab clean, lab check, lab stop."
exit 1
