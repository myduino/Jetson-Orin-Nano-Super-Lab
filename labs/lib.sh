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

# ---- Notebooks (lab start / lab reset) ----
# The notebooks in this folder are the master copies. Students work on copies in ~/jetson-labs/labN,
# so "git pull" or cloning again never touches their answers.
LAB_WORK=~/jetson-labs

# notebook_of N: path of the master notebook of lab N (empty if the lab has none yet)
notebook_of() { ls "$HERE"/labs/lab"$1"_*/lab"$1"_*.ipynb 2>/dev/null | head -n 1; }

# sync_notebooks: refresh Start_Here and copy each lab notebook once (never overwrites a student copy)
sync_notebooks() {
  mkdir -p "$LAB_WORK"
  cp "$HERE/labs/start_here.ipynb" "$LAB_WORK/Start_Here.ipynb"
  local nb b n
  for nb in "$HERE"/labs/lab[0-9]_*/lab[0-9]_*.ipynb; do
    [ -f "$nb" ] || continue
    b="$(basename "$nb")"; n="${b:3:1}"
    mkdir -p "$LAB_WORK/lab$n"
    [ -f "$LAB_WORK/lab$n/$b" ] || cp "$nb" "$LAB_WORK/lab$n/$b"
  done
}

# lab_start [N]: open JupyterLab on Start_Here, or straight on the notebook of lab N
lab_start() {
  if [ ! -f ~/venvs/jetson/bin/activate ]; then
    echo "The course environment is missing. Run  bash $HERE/setup.sh  first."; return 1
  fi
  source ~/venvs/jetson/bin/activate
  sync_notebooks
  local first="Start_Here.ipynb" b
  if [ -n "$1" ]; then
    b="$(basename "$(notebook_of "$1")" 2>/dev/null)"
    if [ -n "$b" ] && [ "$b" != "." ]; then first="lab$1/$b"
    else echo "Lab $1 has no notebook yet. Opening Start_Here instead."; fi
  fi
  say "Opening JupyterLab on the Jetson screen. Leave this terminal open while you work."
  say "To stop: come back here, press Ctrl + C and answer y."
  cd "$LAB_WORK" || return 1
  jupyter lab "$first"
}

# lab_reset N: put a fresh copy of the notebook of lab N in ~/jetson-labs (your old copy is kept as .old)
lab_reset() {
  local src b dest
  src="$(notebook_of "$1")"
  if [ -z "$1" ] || [ -z "$src" ]; then echo "Usage:  lab reset <lab number>   (only labs with a notebook)"; return 1; fi
  b="$(basename "$src")"; dest="$LAB_WORK/lab$1/$b"
  mkdir -p "$LAB_WORK/lab$1"
  if [ -f "$dest" ]; then mv "$dest" "$dest.old"; echo "Your old copy was kept as $dest.old"; fi
  cp "$src" "$dest"
  echo "Fresh notebook: $dest"
}
