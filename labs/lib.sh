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
# ~/students/_shared/               the model files, for everybody
# LAB_HOME is the folder of the student who is working in THIS terminal. The lab scripts use it, so
# two students on one Jetson never write into each other's folder.
STUDENTS="$HOME/students"
SHARED="$STUDENTS/_shared"
SESSIONS="$HOME/.lab_sessions"     # which student works in which terminal
SHARE_DIR="$HOME/.lab_share"       # the JupyterLab server of each working student
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
  mkdir -p "$SHARED/models" "$SESSIONS"
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

# ---- Cameras: up to 3 USB cameras, one for each student ----
# A USB camera makes two device files (for example /dev/video0 and /dev/video1), so the camera NUMBERS of the
# labs (0, 1, 2) are not the video numbers. camera_nodes lists the real cameras in order.
CAM_SYS="${LAB_SYSFS:-/sys/class/video4linux}"
CAM_DEV="${LAB_DEV:-/dev}"
CAM_LOCKS="$HOME/.lab_cameras"

# camera_nodes: one line for each camera: "number device name"
camera_nodes() {
  local d i=0
  for d in $(ls -d "$CAM_SYS"/video* 2>/dev/null | sed 's/.*video//' | sort -n); do
    [ "$(cat "$CAM_SYS/video$d/index" 2>/dev/null)" = "0" ] || continue
    echo "$i $CAM_DEV/video$d $(cat "$CAM_SYS/video$d/name" 2>/dev/null)"
    i=$((i+1))
  done
}

# camera_path N: the device file of camera number N
camera_path() { camera_nodes | awk -v n="$1" '$1 == n {print $2}'; }

# camera_user N: who uses camera N now (empty if nobody)
camera_user() {
  local owner opid
  [ -f "$CAM_LOCKS/$1" ] || return 0
  read -r owner opid < "$CAM_LOCKS/$1"
  kill -0 "$opid" 2>/dev/null && echo "$owner"
}

cameras_show() {
  local n dev name user any=""
  while read -r n dev name; do
    [ -n "$n" ] || continue; any=1
    user="$(camera_user "$n")"
    printf '  camera %s   %s   %s   %s\n' "$n" "$dev" "${name:-?}" "${user:+(used by $user)}"
  done < <(camera_nodes)
  [ -n "$any" ] || echo "  No USB camera found. Plug it in firmly and try again."
}

cam_take() {   # cam_take NUMBER STUDENT
  local user
  user="$(camera_user "$1")"
  if [ -n "$user" ] && [ "$user" != "$2" ]; then echo "Camera $1 is used by $user."; return 1; fi
  mkdir -p "$CAM_LOCKS"
  echo "$2 $$" > "$CAM_LOCKS/$1"
}

# cam_release_of STUDENT [any]: free the cameras that THIS session took. With "any" (the teacher) free all of them.
cam_release_of() {
  local f
  for f in "$CAM_LOCKS"/*; do
    [ -f "$f" ] || continue
    [ "$(cut -d' ' -f1 "$f")" = "$1" ] || continue
    if [ "$2" = any ] || [ "$(cut -d' ' -f2 "$f")" = "$$" ]; then rm -f "${CAM_LOCKS:?}/${f##*/}"; fi
  done
}

# ---- A student session: lab start <name> [camera N] ----
# Starts the JupyterLab of the student in the background and opens a shell that is ready to work in:
# the Python environment is on, the folder is the student's own, the camera is the chosen one.
# When the student types "exit" the JupyterLab stops and the camera is free again.
# session_busy NAME: true (and a message) when NAME already works in another terminal
session_busy() {
  local opid
  share_alive "$1" || return 1
  opid="$(cat "$SHARE_DIR/$1.owner" 2>/dev/null)"
  [ -n "$opid" ] && kill -0 "$opid" 2>/dev/null || return 1
  echo "$1 is already working in another terminal (JupyterLab: http://$(my_ip):$(cat "$SHARE_DIR/$1.port")/?token=$(cat "$SHARE_DIR/$1.token"))."
  echo "Use that terminal, or close it first (type exit there)."
}

session_server() {   # session_server NAME FIRST_NOTEBOOK  -> sets SESSION_PORT and SESSION_TOKEN
  local name="$1" first="$2" port token open="--no-browser" opid
  mkdir -p "$SHARE_DIR"; chmod 700 "$SHARE_DIR"
  STARTED_SERVER=""
  session_busy "$name" && return 1
  share_alive "$name" && share_stop "$name" > /dev/null      # a server left behind by a lost connection
  [ -z "$SSH_CONNECTION" ] && [ -n "$DISPLAY" ] && open=""     # at the Jetson screen: open the browser there
  port=8888
  while port_busy "$port" || grep -qs "^$port\$" "$SHARE_DIR"/*.port; do port=$((port+1)); done
  token="$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')"
  (
    cd "$LAB_HOME" || exit 1
    nohup jupyter lab $open --ip=0.0.0.0 --port="$port" --ServerApp.token="$token" \
      --ServerApp.allow_remote_access=True "$first" > "$LAB_HOME/.jupyter.log" 2>&1 &
    echo $! > "$SHARE_DIR/$name.pid"
  )
  echo "$port" > "$SHARE_DIR/$name.port"; echo "$token" > "$SHARE_DIR/$name.token"; echo "$$" > "$SHARE_DIR/$name.owner"
  chmod 600 "$SHARE_DIR/$name".*
  SESSION_PORT="$port"; SESSION_TOKEN="$token"; STARTED_SERVER=1
}

my_ip() { local ip; ip="$(hostname -I 2>/dev/null | awk '{print $1}')"; echo "${ip:-$(hostname 2>/dev/null)}"; }

session_cleanup() {
  [ -n "$SESSION_DONE" ] && return; SESSION_DONE=1
  [ -n "$STARTED_SERVER" ] && share_stop "$SESSION_NAME" > /dev/null
  cam_release_of "$SESSION_NAME"
  [ -n "$SESSION_STREAM" ] && rm -f "${SHARE_DIR:?}/${SESSION_NAME:?}.stream"
  [ -n "$SESSION_RC" ] && rm -f "$SESSION_RC"
}

# lab_start [NAME] [camera N] [LAB]
lab_start() {
  local name="" labn="" cam="" prev="" a first="Start_Here.ipynb" b dev rc ip stream
  for a in "$@"; do
    if [ "$prev" = camera ]; then cam="$a"; prev=""; continue; fi
    case "$a" in
      camera) prev=camera ;;
      ''|*[!0-9]*) name="$a" ;;
      *) labn="$a" ;;
    esac
  done
  [ "$prev" = camera ] && { echo "Which camera?  Type  lab cameras  to see the numbers."; return 1; }
  if [ -n "$name" ]; then choose_student "$name" || return 1; else ensure_student || return 1; fi
  if [ ! -f ~/venvs/jetson/bin/activate ]; then
    echo "The course environment is missing. Run  bash $HERE/setup.sh  first."; return 1
  fi
  SESSION_NAME="$(basename "$LAB_HOME")"; SESSION_DONE=""; SESSION_RC=""; STARTED_SERVER=""; SESSION_STREAM=""
  mkdir -p "$SHARE_DIR"; session_busy "$SESSION_NAME" && return 1
  if [ -n "$cam" ]; then
    case "$cam" in *[!0-9]*) echo "The camera is a number, for example:  lab start $SESSION_NAME camera 0"; return 1 ;; esac
    dev="$(camera_path "$cam")"
    if [ -z "$dev" ]; then echo "There is no camera number $cam. These cameras are plugged in:"; cameras_show; return 1; fi
    cam_take "$cam" "$SESSION_NAME" || { cameras_show; return 1; }
    export LAB_CAMERA="$dev"
  else
    unset LAB_CAMERA
  fi
  trap ':' INT                                   # Ctrl + C stops a program, not this session
  trap 'session_cleanup; exit 143' HUP TERM
  trap 'session_cleanup' EXIT
  source ~/venvs/jetson/bin/activate
  sync_notebooks
  if [ -n "$labn" ]; then
    b="$(basename "$(notebook_of "$labn")" 2>/dev/null)"
    if [ -n "$b" ] && [ "$b" != "." ]; then first="lab$labn/$b"
    else echo "Lab $labn has no notebook yet. Opening Start_Here instead."; fi
  fi
  stream=8800
  while port_busy "$stream" || grep -qs "^$stream\$" "$SHARE_DIR"/*.stream; do stream=$((stream+1)); done
  export LAB_STREAM_PORT="$stream" LAB_HOME
  session_server "$SESSION_NAME" "$first" || { session_cleanup; return 1; }
  echo "$stream" > "$SHARE_DIR/$SESSION_NAME.stream"; SESSION_STREAM=1
  ip="$(my_ip)"
  echo
  say "Hello, $SESSION_NAME!"
  echo "  Your folder:     $LAB_HOME"
  echo "  Your camera:     ${LAB_CAMERA:-none chosen}${cam:+  (camera $cam)}"
  echo "  Your JupyterLab: http://$ip:$SESSION_PORT/?token=$SESSION_TOKEN"
  echo "                   Open this link in the browser of your laptop."
  echo "  Live programs:   http://$ip:$stream/   (the terminal programs print this link too)"
  echo "  When you finish: type  exit  . That stops your JupyterLab and frees the camera."
  echo
  rc="$(mktemp)"; SESSION_RC="$rc"
  cat > "$rc" <<RCEOF
[ -f ~/.bashrc ] && source ~/.bashrc
source ~/venvs/jetson/bin/activate
export LAB_HOME="$LAB_HOME" LAB_STREAM_PORT="$stream"
${LAB_CAMERA:+export LAB_CAMERA="$LAB_CAMERA"}
export PYTHONPATH="$HERE/labs\${PYTHONPATH:+:\$PYTHONPATH}"
cd "$LAB_HOME"
PS1="($SESSION_NAME) \u@\h:\w\\\$ "
RCEOF
  bash --rcfile "$rc" -i
  session_cleanup
  echo "Goodbye, $SESSION_NAME. Your JupyterLab is stopped and the camera is free."
}

# lab_stop NAME: the teacher frees the JupyterLab and the camera of a student whose connection was lost
lab_stop() {
  local n
  n="$(clean_name "$1")"
  [ -n "$n" ] || { echo "Usage:  lab stop <name>"; return 1; }
  share_stop "$n"; cam_release_of "$n" any
  echo "Stopped the session of $n."
}

# ---- Memory: only one TensorRT build at a time ----
BUILD_LOCK="$HOME/.lab_build.lock"
build_acquire() {
  local owner opid shown=""
  while ! mkdir "$BUILD_LOCK" 2>/dev/null; do
    owner="$(cat "$BUILD_LOCK/owner" 2>/dev/null)"; opid="${owner##* }"
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "${BUILD_LOCK:?}"; continue; fi
    if [ -z "$shown" ]; then
      say "${owner% *} is building an engine now. Only one build at a time fits in the 8 GB memory, so you wait here."
      shown=1
    fi
    sleep 10
  done
  echo "$(basename "$LAB_HOME") $$" > "$BUILD_LOCK/owner"
}
build_release() { rm -rf "${BUILD_LOCK:?}"; }

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

# ---- JupyterLab servers of the students ----
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
      printf '%-12s not running (a lost connection? free it with:  lab stop %s)\n' "$n" "$n"
    fi
  done
  [ -n "$any" ] || echo "Nobody is working now."
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
    rm -f "${SHARE_DIR:?}/${n:?}".pid "${SHARE_DIR:?}/${n:?}".port "${SHARE_DIR:?}/${n:?}".token "${SHARE_DIR:?}/${n:?}".owner "${SHARE_DIR:?}/${n:?}".stream
  done
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
  share_stop "$n"; cam_release_of "$n" any
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
  title "4. Students who are working now (JupyterLab and cameras)"
  cameras_show
  share_list
  ask "Stop all of them and free the cameras?" && { share_stop; rm -f "${CAM_LOCKS:?}"/*; }
  title "5. Students on this Jetson"
  for d in $(list_students); do printf '  %-14s %s\n' "$d" "$(du -sh "$STUDENTS/$d" 2>/dev/null | cut -f1)"; done
  echo "Delete a student with:  lab clean <name>"
}
