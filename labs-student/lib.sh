#!/bin/bash
# Helper functions of the lab command (lab.sh loads this file). Do not run it on its own.
# The students do not use the lab command to start: the teacher puts each student on a Jetson (teacher page) and
# the lab agent (labs-student/agent.py) starts the student's JupyterLab. The lab command is for small jobs on the Jetson.

CT=$'\033[1;36m'   # headings
CN=$'\033[0m'

title() { printf '\n%s== %s ==%s\n' "$CT" "$*" "$CN"; }
say()   { printf '%s%s%s\n' "$CT" "$*" "$CN"; }

# The student folder is the whole environment of a student: ~/myduino-jetson-lab/<class>/<student>/
ROOT="${LAB_ROOT:-$HOME/myduino-jetson-lab}"          # LAB_ROOT is set inside a student's JupyterLab, where $HOME is the student folder

# ensure_student: lab me and lab reset only work in a JupyterLab Terminal tab of a student (LAB_HOME is set there)
ensure_student() {
  case "$LAB_HOME" in "$ROOT"/*/*) [ -d "$LAB_HOME" ] && return 0 ;; esac
  echo "Open a Terminal tab inside your JupyterLab (File, New, Terminal) and type the command there."
  return 1
}

# notebook_of N: path of the master notebook of lab N (empty if the lab has none)
notebook_of() { ls "$HERE"/labs-student/lab"$1"_*/lab"$1"_*.ipynb 2>/dev/null | head -n 1; }

# lab_reset N: put a fresh copy of the notebook of lab N in your folder (your old copy is kept as .old)
lab_reset() {
  local src b dest
  src="$(notebook_of "$1")"
  if [ -z "$1" ] || [ -z "$src" ]; then echo "Usage:  lab reset <lab number>"; return 1; fi
  b="$(basename "$src")"; dest="$LAB_HOME/lab$1/$b"
  mkdir -p "$LAB_HOME/lab$1"
  if [ -f "$dest" ]; then mv "$dest" "$dest.old"; echo "Your old copy was kept as $dest.old"; fi
  cp "$src" "$dest"
  echo "Fresh notebook: $dest"
}

# ---- Cameras: up to 3 USB cameras ----
# A USB camera makes two device files (for example /dev/video0 and /dev/video1), so the camera NUMBERS of the
# teacher page (0, 1, 2) are not the video numbers. camera_nodes lists the real cameras in order.
CAM_SYS="${LAB_SYSFS:-/sys/class/video4linux}"
CAM_DEV="${LAB_DEV:-/dev}"

# camera_nodes: one line for each camera: "number device name"
camera_nodes() {
  local d i=0
  for d in $(ls -d "$CAM_SYS"/video* 2>/dev/null | sed 's/.*video//' | sort -n); do
    [ "$(cat "$CAM_SYS/video$d/index" 2>/dev/null)" = "0" ] || continue
    echo "$i $CAM_DEV/video$d $(cat "$CAM_SYS/video$d/name" 2>/dev/null)"
    i=$((i+1))
  done
}

cameras_show() {
  local n dev name any=""
  while read -r n dev name; do
    [ -n "$n" ] || continue; any=1
    printf '  camera %s   %s   %s\n' "$n" "$dev" "${name:-?}"
  done < <(camera_nodes)
  [ -n "$any" ] || echo "  No USB camera found. Plug it in firmly and try again."
}

# ---- Teacher: reset this Jetson for the next class ----
lab_check() {
  local yes="" c s
  [ "$1" = "--yes" ] && yes=1
  ask() { [ -n "$yes" ] && return 0; local a; read -r -p "$1 [y/N] " a; [ "$a" = y ] || [ "$a" = Y ]; }
  title "1. The course folder ($HERE)"
  if [ -n "$(git -C "$HERE" status --short 2>/dev/null)" ]; then
    git -C "$HERE" status --short
    ask "Undo these changes?" && { git -C "$HERE" restore . ; git -C "$HERE" clean -fd -q; echo "Restored."; }
  else
    echo "No changes. The course folder is clean."
  fi
  if git -C "$HERE" status --short --ignored 2>/dev/null | grep -q '^!!'; then
    echo "Files made while running the labs (not part of the course):"
    git -C "$HERE" status --short --ignored | grep '^!!'
    ask "Delete them?" && { git -C "$HERE" clean -fdX -q -- labs-student; echo "Deleted."; }
  fi
  title "2. Power mode"
  if command -v nvpmodel >/dev/null 2>&1; then
    sudo nvpmodel -q
    ask "Set MAXN SUPER (mode 2) for the next session?" && sudo nvpmodel -m 2
  else
    echo "(nvpmodel is not available here)"
  fi
  title "3. Command history"
  ask "Clear the saved command history of this account?" && { : > ~/.bash_history; history -c 2>/dev/null; echo "Cleared. Open terminals save their history again when they close."; }
  title "4. The lab agent and the cameras"
  if command -v systemctl >/dev/null 2>&1; then echo "Agent: $(systemctl is-active myduino-lab-agent 2>/dev/null)"; fi
  cameras_show
  title "5. Student folders on this Jetson"
  for c in "$ROOT"/*/; do
    [ -d "$c" ] || continue
    for s in "$c"*/; do [ -d "$s" ] && printf '  %-28s %s\n' "${c%/}" "$(du -sh "${s%/}" 2>/dev/null | cut -f1)  ${s%/}" | sed "s#$ROOT/##g"; done
  done
  echo "Remove students (and their folders) on the teacher page."
}
