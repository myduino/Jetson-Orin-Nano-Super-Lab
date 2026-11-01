#!/bin/bash
# Helper functions for the lab scripts (lab.sh loads this file). Do not run it on its own.

CT=$'\033[1;36m'   # headings
CC=$'\033[1;33m'   # the command that is being run
CN=$'\033[0m'

title() { printf '\n%s== %s ==%s\n' "$CT" "$*" "$CN"; }
say()   { printf '%s%s%s\n' "$CT" "$*" "$CN"; }

# run: show the command, then run it, so you see exactly what was typed for you.
run() {
  printf '%s$ %s%s\n' "$CC" "$*" "$CN"
  eval "$*"
  case "$1" in cd|cd\ *) printf '   (you are now in %s)\n' "$PWD" ;; esac
}

# pause: wait for Enter between steps.
pause() {
  if [ -t 0 ]; then read -r -p $'\nPress Enter to go on... ' _; fi
}

# show_parts: list the parts of the lab that is loaded (each lab script sets LAB_TITLE and PARTS).
show_parts() {
  printf '\n%sLab %s: %s%s\n' "$CT" "$LABNUM" "$LAB_TITLE" "$CN"
  echo "Type  lab $LABNUM <part>  to run a part, for example:  lab $LABNUM ${PARTS[0]%%|*}"
  echo
  for p in "${PARTS[@]}"; do
    printf '  lab %s %s   %s\n' "$LABNUM" "${p%%|*}" "${p#*|}"
  done
  echo
}

# countdown N "message": waits N seconds and shows the time left on one line
countdown() {
  local n=$1 msg=$2
  while [ "$n" -gt 0 ]; do
    printf "\r  %s %2d s " "$msg" "$n"
    sleep 1
    n=$((n-1))
  done
  printf "\r  %s done.      \n" "$msg"
}
