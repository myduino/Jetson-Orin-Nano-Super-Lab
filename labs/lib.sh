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

# parts_help: list the parts of a lab when no part letter is given.
parts_help() {
  echo "Usage: lab $LABNUM <part>      for example: lab $LABNUM $1"
  echo "Parts: $2"
}
