#!/bin/bash
# The lab command. All the labs are notebooks: lab start opens them in your own JupyterLab.
#   lab start siti class a camera 0   starts your environment: your folder, your camera, your JupyterLab, a ready shell
#                             (type exit when you finish). Without "camera 0" no camera is chosen.
#   lab cameras    lists the cameras that are plugged in and who uses them
#   lab me         shows who you are and where your folder is
#   lab reset 5    gives you a fresh copy of the Lab 5 notebook
# Teacher:
#   lab class add a       make a class                lab classes   the table of classes
#   lab class a           the students of a class, with port, camera and state
#   lab teacher           the teacher web page (classes, students, ports, who is working)
#   lab clean a siti      delete one student          lab clean a   delete the whole class
#   lab check             reset the board for the next session
#   lab stop a siti       free the JupyterLab and the camera of a student whose connection was lost
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB="$1"
source "$HERE/labs/lib.sh"

case "$LAB" in
  start)        lab_start "${@:2}"; exit $? ;;
  me)           ensure_student && echo "You are $(basename "$LAB_HOME") in class $LAB_CLASS. Your folder: $LAB_HOME"; exit $? ;;
  reset)        ensure_student && lab_reset "$2"; exit $? ;;
  cameras)      echo "Cameras plugged in:"; cameras_show; exit 0 ;;
  classes)      classes_table; exit 0 ;;
  class)        case "$2" in add) class_add "$3" ;; '') classes_table ;; *) class_show "$2" ;; esac; exit $? ;;
  teacher)      exec python3 "$HERE/labs/teacher.py" "$HERE" "${@:2}" ;;
  stop)         lab_stop "$2" "$3"; exit $? ;;
  clean)        lab_clean "$2" "$3"; exit $? ;;
  check)        lab_check "$2"; exit $? ;;
esac

[ -n "$LAB" ] && echo "Unknown command: lab $LAB"
echo "Type  lab start <your name> class <class> camera 0  to start your JupyterLab. All the labs are notebooks there."
echo "Other commands: lab cameras, lab me, lab reset <lab number>. Teacher: lab classes, lab class, lab teacher, lab clean, lab check, lab stop."
exit 1
