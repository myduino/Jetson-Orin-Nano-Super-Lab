#!/bin/bash
# Helper functions for the lab scripts (lab.sh loads this file). Do not run it on its own.

CT=$'\033[1;36m'   # headings
CC=$'\033[1;33m'   # the command that is being run
CN=$'\033[0m'

title() { printf '\n%s== %s ==%s\n' "$CT" "$*" "$CN"; }
say()   { printf '%s%s%s\n' "$CT" "$*" "$CN"; }

# run: show the command, then run it, so you see exactly what was typed for you.
run() {
  local show="$*" tilde='~'
  printf '%s$ %s%s\n' "$CC" "${show//"$HOME"/$tilde}" "$CN"
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

# ---- Students: everybody has their own folder ----
# ~/students/<name>/lab1 ... lab9   the work of one student (notebooks, pictures, engines)
# ~/students/_shared/               model files and the teacher's TensorRT engines, for everybody
# LAB_HOME is the folder of the student who is working in THIS terminal. The lab scripts use it, so
# two students on one Jetson never write into each other's folder.
STUDENTS="$HOME/students"
SHARED="$STUDENTS/_shared"
SESSIONS="$HOME/.lab_sessions"     # which student works in which terminal
SHARE_DIR="$HOME/.lab_share"       # JupyterLab servers started by the teacher (lab share)
LAB_HOME="${LAB_HOME:-$STUDENTS/name}"

# clean_name: letters, numbers and _ only, lower case, at most 20 characters
clean_name() { printf '%s' "$1" | tr 'A-Z' 'a-z' | sed 's/[^a-z0-9_]/_/g; s/^_*//; s/_*$//' | cut -c1-20; }

# valid_name: not empty and not only digits (a number means a lab number)
valid_name() {
  case "$1" in ''|*[!a-z0-9_]*) return 1 ;; esac
  case "$1" in *[!0-9]*) return 0 ;; esac
  return 1
}

list_students() {
  local d
  for d in "$STUDENTS"/*/; do
    [ -d "$d" ] || continue
    d="${d%/}"; d="${d##*/}"
    case "$d" in _*) ;; *) echo "$d" ;; esac
  done
}

# prepare_student NAME: set LAB_HOME and make the folders (no questions, no side effects on the terminal)
prepare_student() {
  local n
  export LAB_HOME="$STUDENTS/$1"
  mkdir -p "$SHARED/models" "$SHARED/engines" "$SESSIONS"
  for n in 1 2 3 4 5 6 7 8 9; do mkdir -p "$LAB_HOME/lab$n"; done
  [ -e "$LAB_HOME/models" ] || ln -s "$SHARED/models" "$LAB_HOME/models"
}

# use_student NAME: this terminal now belongs to NAME
use_student() {
  local fresh=""
  [ -d "$STUDENTS/$1" ] || fresh=1
  prepare_student "$1"
  [ -n "$fresh" ] && echo "Welcome, $1! Your folder is made: $LAB_HOME"
  echo "$1" > "$SESSIONS/$PPID"
  echo "$1" > ~/.lab_student
}

# choose_student [NAME]: ask who is working (or take NAME) and use that student
choose_student() {
  local name="$1" last existing
  mkdir -p "$STUDENTS" "$SESSIONS"
  last="$(cat ~/.lab_student 2>/dev/null)"
  if [ -n "$name" ]; then
    name="$(clean_name "$name")"
    valid_name "$name" || { echo "Use letters, for example:  lab start ali"; return 1; }
  else
    existing="$(list_students | tr '\n' ' ')"
    [ -t 0 ] || { name="$last"; [ -n "$name" ] || { echo "Tell me who you are:  lab start <your name>"; return 1; }; }
    while [ -z "$name" ]; do
      [ -n "$existing" ] && echo "Students on this Jetson: $existing"
      read -r -p "Your name${last:+ (press Enter for $last)}: " name
      [ -z "$name" ] && name="$last"
      name="$(clean_name "$name")"
      valid_name "$name" || { echo "Please type letters, for example: ali"; name=""; }
    done
  fi
  use_student "$name"
}

# ensure_student: used by every lab command, so LAB_HOME is always a student's folder
ensure_student() {
  local name f
  for f in "$SESSIONS"/*; do      # forget terminals that are closed
    [ -f "$f" ] || continue
    kill -0 "${f##*/}" 2>/dev/null || rm -f "${SESSIONS:?}/${f##*/}"
  done
  if [ "${LAB_HOME%/*}" = "$STUDENTS" ] && [ -d "$LAB_HOME" ]; then return 0; fi   # set by lab start (JupyterLab terminals)
  name="$(cat "$SESSIONS/$PPID" 2>/dev/null)"
  if [ -n "$name" ] && [ -d "$STUDENTS/$name" ]; then use_student "$name"; return 0; fi
  choose_student
}

# ---- Notebooks (lab start / lab reset) ----
# The notebooks in the course folder are the master copies. Each student works on copies in their own
# folder, so "git pull" or cloning again never touches their answers.

# notebook_of N: path of the master notebook of lab N (empty if the lab has none yet)
notebook_of() { ls "$HERE"/labs/lab"$1"_*/lab"$1"_*.ipynb 2>/dev/null | head -n 1; }

# sync_notebooks: refresh Start_Here and copy each lab notebook once (never overwrites a student copy)
sync_notebooks() {
  cp "$HERE/labs/start_here.ipynb" "$LAB_HOME/Start_Here.ipynb"
  local nb b n
  for nb in "$HERE"/labs/lab[0-9]_*/lab[0-9]_*.ipynb; do
    [ -f "$nb" ] || continue
    b="$(basename "$nb")"; n="${b:3:1}"
    mkdir -p "$LAB_HOME/lab$n"
    [ -f "$LAB_HOME/lab$n/$b" ] || cp "$nb" "$LAB_HOME/lab$n/$b"
  done
}

# lab_start [NAME] [N]: open JupyterLab in the folder of NAME, on Start_Here or on the notebook of lab N
lab_start() {
  local name="" labn="" a first="Start_Here.ipynb" b
  for a in "$@"; do
    case "$a" in ''|*[!0-9]*) name="$a" ;; *) labn="$a" ;; esac
  done
  if [ -n "$name" ]; then choose_student "$name" || return 1; else ensure_student || return 1; fi
  if [ ! -f ~/venvs/jetson/bin/activate ]; then
    echo "The course environment is missing. Run  bash $HERE/setup.sh  first."; return 1
  fi
  source ~/venvs/jetson/bin/activate
  sync_notebooks
  if [ -n "$labn" ]; then
    b="$(basename "$(notebook_of "$labn")" 2>/dev/null)"
    if [ -n "$b" ] && [ "$b" != "." ]; then first="lab$labn/$b"
    else echo "Lab $labn has no notebook yet. Opening Start_Here instead."; fi
  fi
  say "Opening JupyterLab for $(basename "$LAB_HOME") on the Jetson screen. Leave this terminal open while you work."
  say "To stop: come back here, press Ctrl + C and answer y."
  cd "$LAB_HOME" || return 1
  jupyter lab "$first"
}

# lab_reset N: put a fresh copy of the notebook of lab N in your folder (your old copy is kept as .old)
lab_reset() {
  local src b dest
  src="$(notebook_of "$1")"
  if [ -z "$1" ] || [ -z "$src" ]; then echo "Usage:  lab reset <lab number>   (only labs with a notebook)"; return 1; fi
  b="$(basename "$src")"; dest="$LAB_HOME/lab$1/$b"
  mkdir -p "$LAB_HOME/lab$1"
  if [ -f "$dest" ]; then mv "$dest" "$dest.old"; echo "Your old copy was kept as $dest.old"; fi
  cp "$src" "$dest"
  echo "Fresh notebook: $dest"
}

# ---- Teacher: share JupyterLab with the laptops of the students ----
port_busy() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
share_alive() { [ -f "$SHARE_DIR/$1.pid" ] && kill -0 "$(cat "$SHARE_DIR/$1.pid")" 2>/dev/null; }

share_list() {
  local f n ip host any=""
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"; host="$(hostname 2>/dev/null)"; host="${host%.local}"
  for f in "$SHARE_DIR"/*.port; do
    [ -f "$f" ] || continue
    n="${f##*/}"; n="${n%.port}"; any=1
    if share_alive "$n"; then
      printf '%s%-12s%s http://%s:%s/?token=%s\n' "$CT" "$n" "$CN" "${ip:-$host}" "$(cat "$f")" "$(cat "$SHARE_DIR/$n.token")"
      printf '             or http://%s.local:%s/?token=%s\n' "$host" "$(cat "$f")" "$(cat "$SHARE_DIR/$n.token")"
    else
      printf '%-12s not running (start it again with:  lab share %s)\n' "$n" "$n"
    fi
  done
  [ -n "$any" ] || echo "No student is shared. Start with:  lab share ali siti budi"
}

share_stop() {
  local names="$*" f n pid
  if [ -z "$names" ]; then
    for f in "$SHARE_DIR"/*.pid; do [ -f "$f" ] || continue; n="${f##*/}"; names="$names ${n%.pid}"; done
  fi
  for n in $names; do
    n="$(clean_name "$n")"
    [ -n "$n" ] || continue
    if share_alive "$n"; then
      pid="$(cat "$SHARE_DIR/$n.pid")"; pkill -P "$pid" 2>/dev/null; kill "$pid" 2>/dev/null
      echo "Stopped the JupyterLab of $n"
    fi
    rm -f "${SHARE_DIR:?}/${n:?}.pid" "${SHARE_DIR:?}/${n:?}.port" "${SHARE_DIR:?}/${n:?}.token"
  done
}

# lab_share NAME...: one JupyterLab for each student, on its own port, with its own secret token
lab_share() {
  case "$1" in ''|list) share_list; return ;; stop) shift; share_stop "$@"; return ;; esac
  if [ ! -f ~/venvs/jetson/bin/activate ]; then echo "The course environment is missing. Run setup.sh first."; return 1; fi
  source ~/venvs/jetson/bin/activate
  mkdir -p "$SHARE_DIR"; chmod 700 "$SHARE_DIR"
  local name port token
  for name in "$@"; do
    name="$(clean_name "$name")"
    valid_name "$name" || { echo "Skipping a bad name. Use letters, for example: ali"; continue; }
    if share_alive "$name"; then echo "$name is already shared."; continue; fi
    port=8888
    while port_busy "$port" || grep -qs "^$port\$" "$SHARE_DIR"/*.port; do port=$((port+1)); done
    token="$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')"
    (
      prepare_student "$name"; sync_notebooks
      cd "$LAB_HOME" || exit 1
      nohup jupyter lab --no-browser --ip=0.0.0.0 --port="$port" --ServerApp.token="$token" \
        --ServerApp.allow_remote_access=True Start_Here.ipynb > "$LAB_HOME/.jupyter.log" 2>&1 &
      echo $! > "$SHARE_DIR/$name.pid"
    )
    echo "$port" > "$SHARE_DIR/$name.port"; echo "$token" > "$SHARE_DIR/$name.token"
    chmod 600 "$SHARE_DIR/$name".*
  done
  sleep 1
  echo
  share_list
  echo
  say "Give each student only their own link. Anyone with a link can run commands on the Jetson."
  [ "$(ls "$SHARE_DIR"/*.pid 2>/dev/null | wc -l)" -gt 3 ] && say "More than 3 students share this Jetson (8 GB memory). Use the notebooks of Labs 4 and 5 only."
  say "The camera labs (6, 7 Part D, 8 Part D and 9) and all timing tests need the board to themselves."
}

# ---- Teacher: clean up, check the board, share TensorRT engines ----
lab_clean() {
  local n d size again
  n="$(clean_name "$1")"
  if [ -z "$n" ]; then
    echo "Students on this Jetson:"
    for d in $(list_students); do printf '  %-14s %s\n' "$d" "$(du -sh "$STUDENTS/$d" 2>/dev/null | cut -f1)"; done
    echo "Delete one with:  lab clean <name>"
    return 0
  fi
  if [ ! -d "$STUDENTS/$n" ] || [ "${n#_}" != "$n" ]; then echo "There is no student called $n."; return 1; fi
  if [ ! -t 0 ]; then echo "lab clean asks a question, so run it in a terminal."; return 1; fi
  size="$(du -sh "$STUDENTS/$n" | cut -f1)"
  say "This deletes everything of $n ($size) in $STUDENTS/$n"
  echo "Make sure $n has copied the work to a laptop or a USB drive first."
  read -r -p "Type the name again to delete: " again
  [ "$again" = "$n" ] || { echo "Cancelled. Nothing was deleted."; return 1; }
  share_stop "$n"
  rm -rf "${STUDENTS:?}/${n:?}"
  for d in "$SESSIONS"/*; do
    [ -f "$d" ] && [ "$(cat "$d")" = "$n" ] && rm -f "${SESSIONS:?}/${d##*/}"
  done
  [ "$(cat ~/.lab_student 2>/dev/null)" = "$n" ] && rm -f ~/.lab_student
  echo "Deleted $n."
}

lab_check() {
  local yes="" d
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
    ask "Delete them?" && { git -C "$HERE" clean -fdX -q -- labs; echo "Deleted."; }
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
  title "4. Shared JupyterLab servers"
  share_list
  ask "Stop all of them?" && share_stop
  title "5. Students on this Jetson"
  for d in $(list_students); do printf '  %-14s %s\n' "$d" "$(du -sh "$STUDENTS/$d" 2>/dev/null | cut -f1)"; done
  echo "Delete a student with:  lab clean <name>"
}

# lab_share_engine [remove]: the teacher built the TensorRT engines in Lab 8, now everybody can copy them
lab_share_engine() {
  local f n=0
  mkdir -p "$SHARED/engines"
  if [ "$1" = "remove" ]; then
    for f in yolo26n_fp32.engine yolo26n_fp16.engine; do rm -f "${SHARED:?}/engines/$f"; done
    echo "Shared engines removed. Students build their own in Lab 8."; return 0
  fi
  for f in yolo26n_fp32.engine yolo26n_fp16.engine; do
    [ -f "$LAB_HOME/lab8/$f" ] && { cp "$LAB_HOME/lab8/$f" "$SHARED/engines/"; n=$((n+1)); }
  done
  if [ "$n" -eq 0 ]; then echo "No engines found in $LAB_HOME/lab8. Build them first:  lab 8 B"; return 1; fi
  echo "$n engine file(s) shared. Students now copy them in  lab 8 B  (seconds, not 12 minutes)."
  echo "A student who wants to build their own:  lab 8 B build"
}
