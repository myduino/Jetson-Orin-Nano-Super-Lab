#!/bin/bash
# Helper functions of the lab command (lab.sh loads this file). Do not run it on its own.

CT=$'\033[1;36m'   # headings
CN=$'\033[0m'

title() { printf '\n%s== %s ==%s\n' "$CT" "$*" "$CN"; }
say()   { printf '%s%s%s\n' "$CT" "$*" "$CN"; }

# ---- Classes and students: the student folder is the whole environment ----
# ~/myduino-jetson-lab/<class>/<student>/   everything of one student:
#     lab1 ... lab9   notebooks, pictures, engines          models/   the AI model files
#     .jupyter/ .ipython/ .config/ .bash_history   the Jupyter, IPython and shell settings
# LAB_HOME is the folder of the student who works in THIS session; LAB_CLASS is the class.
# Only the Python packages (the venv) are shared, because PyTorch is several GB.
ROOT="$HOME/myduino-jetson-lab"
SHARE_DIR="$HOME/.lab_share"       # the JupyterLab server of each working student

# clean_name: letters, numbers and _ only, lower case, at most 20 characters
clean_name() { printf '%s' "$1" | tr 'A-Z' 'a-z' | sed 's/[^a-z0-9_]/_/g; s/^_*//; s/_*$//' | cut -c1-20; }

# valid_name: not empty and not only digits (a number means a lab number)
valid_name() {
  case "$1" in ''|*[!a-z0-9_]*) return 1 ;; esac
  case "$1" in *[!0-9]*) return 0 ;; esac
  return 1
}
valid_class() { case "$1" in ''|*[!a-z0-9_]*) return 1 ;; esac; }

# A session is known by its key "<class>__<student>" (file names), shown as "<class>/<student>"
key_of() { printf '%s__%s' "$1" "$2"; }
show_key() { printf '%s' "${1/__//}"; }

list_classes() {
  local d
  for d in "$ROOT"/*/; do
    [ -d "$d" ] || continue
    d="${d%/}"; d="${d##*/}"
    case "$d" in _*) ;; *) echo "$d" ;; esac
  done
}

list_students() {   # list_students CLASS
  local d
  for d in "$ROOT/$1"/*/; do
    [ -d "$d" ] || continue
    d="${d%/}"; echo "${d##*/}"
  done
}

# last_used DIR: the date of the newest file in DIR
last_used() {
  python3 - "$1" <<'PY'
import os, sys, time
newest = 0
for folder, _, files in os.walk(sys.argv[1]):
    for f in files:
        try:
            newest = max(newest, os.lstat(os.path.join(folder, f)).st_mtime)
        except OSError:
            pass
print(time.strftime("%Y-%m-%d", time.localtime(newest)) if newest else "-")
PY
}

class_add() {   # teacher: lab class add <name>
  local c
  c="$(clean_name "$1")"
  valid_class "$c" || { echo "Use letters or numbers, for example:  lab class add a"; return 1; }
  if [ -d "$ROOT/$c" ]; then echo "Class $c exists already."; return 0; fi
  mkdir -p "$ROOT/$c"
  echo "Class $c is ready. Its students start with:  lab start <name> class $c camera 0"
}

# prepare_student CLASS NAME: set LAB_CLASS and LAB_HOME and make the folders
prepare_student() {
  local n
  export LAB_CLASS="$1" LAB_HOME="$ROOT/$1/$2"
  for n in 1 2 3 4 5 6 7 8 9; do mkdir -p "$LAB_HOME/lab$n"; done
  mkdir -p "$LAB_HOME/models" "$LAB_HOME/.jupyter" "$LAB_HOME/.ipython" "$LAB_HOME/.config"
}

# student_env: Jupyter, IPython and the AI tools keep their settings in the student's folder, not in the account
student_env() {
  export JUPYTER_CONFIG_DIR="$LAB_HOME/.jupyter/config" JUPYTER_DATA_DIR="$LAB_HOME/.jupyter/data" \
    JUPYTER_RUNTIME_DIR="$LAB_HOME/.jupyter/runtime" JUPYTERLAB_SETTINGS_DIR="$LAB_HOME/.jupyter/settings" \
    JUPYTERLAB_WORKSPACES_DIR="$LAB_HOME/.jupyter/workspaces" IPYTHONDIR="$LAB_HOME/.ipython" \
    YOLO_CONFIG_DIR="$LAB_HOME/.config/Ultralytics" MPLCONFIGDIR="$LAB_HOME/.config/matplotlib"
  mkdir -p "$JUPYTER_CONFIG_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_RUNTIME_DIR" "$JUPYTERLAB_SETTINGS_DIR" \
    "$JUPYTERLAB_WORKSPACES_DIR" "$YOLO_CONFIG_DIR" "$MPLCONFIGDIR"
}

# choose_class [NAME]: sets CHOSEN_CLASS. The class must exist (the teacher makes it with  lab class add).
choose_class() {
  local c="$1" list count
  list="$(list_classes | tr '\n' ' ')"
  if [ -n "$c" ]; then
    c="$(clean_name "$c")"
    if [ ! -d "$ROOT/$c" ] || [ "${c#_}" != "$c" ]; then
      echo "There is no class called $c."
      [ -n "$list" ] && echo "Classes on this Jetson: $list" || echo "Ask your teacher to run:  lab class add $c"
      return 1
    fi
  else
    count="$(echo $list | wc -w | tr -d ' ')"
    if [ "$count" = 0 ]; then echo "There is no class yet. Ask your teacher to run:  lab class add <class name>"; return 1; fi
    if [ "$count" = 1 ]; then c="${list% }"
    else
      [ -t 0 ] || { echo "Which class?  lab start <name> class <class>   (classes: $list)"; return 1; }
      while [ -z "$c" ] || [ ! -d "$ROOT/$c" ]; do
        echo "Classes on this Jetson: $list"
        read -r -p "Your class: " c || return 1
        c="$(clean_name "$c")"
      done
    fi
  fi
  CHOSEN_CLASS="$c"
}

# choose_student CLASS [NAME]: ask who is working (or take NAME) and use that student
choose_student() {
  local c="$1" name="$2" existing
  if [ -n "$name" ]; then
    name="$(clean_name "$name")"
    valid_name "$name" || { echo "Use letters, for example:  lab start ali class $c"; return 1; }
  else
    [ -t 0 ] || { echo "Tell me who you are:  lab start <your name> class $c"; return 1; }
    existing="$(list_students "$c" | tr '\n' ' ')"
    while [ -z "$name" ]; do
      [ -n "$existing" ] && echo "Students in class $c: $existing"
      read -r -p "Your name: " name || return 1
      name="$(clean_name "$name")"
      valid_name "$name" || { echo "Please type letters, for example: ali"; name=""; }
    done
  fi
  local fresh=""
  [ -d "$ROOT/$c/$name" ] || fresh=1
  prepare_student "$c" "$name"
  [ -n "$fresh" ] && echo "Welcome, $name! Your folder is made: $LAB_HOME"
  return 0
}

# ensure_student: for lab me / lab reset, which only work inside a session
ensure_student() {
  case "$LAB_HOME" in "$ROOT"/*/*) [ -d "$LAB_HOME" ] && return 0 ;; esac
  echo "Start your session first:  lab start <your name> class <class>"
  return 1
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

# camera_of KEY: the camera number a working student uses (empty if none)
camera_of() {
  local f owner opid
  for f in "$CAM_LOCKS"/*; do
    [ -f "$f" ] || continue
    read -r owner opid < "$f"
    if [ "$owner" = "$1" ] && kill -0 "$opid" 2>/dev/null; then echo "${f##*/}"; return; fi
  done
}

cameras_show() {
  local n dev name user any=""
  while read -r n dev name; do
    [ -n "$n" ] || continue; any=1
    user="$(camera_user "$n")"
    printf '  camera %s   %s   %s   %s\n' "$n" "$dev" "${name:-?}" "${user:+(used by $(show_key "$user"))}"
  done < <(camera_nodes)
  [ -n "$any" ] || echo "  No USB camera found. Plug it in firmly and try again."
}

cam_take() {   # cam_take NUMBER KEY
  local user
  user="$(camera_user "$1")"
  if [ -n "$user" ] && [ "$user" != "$2" ]; then echo "Camera $1 is used by $(show_key "$user")."; return 1; fi
  mkdir -p "$CAM_LOCKS"
  echo "$2 $$" > "$CAM_LOCKS/$1"
}

# cam_release_of KEY [any]: free the cameras that THIS session took. With "any" (the teacher) free all of them.
cam_release_of() {
  local f
  for f in "$CAM_LOCKS"/*; do
    [ -f "$f" ] || continue
    [ "$(cut -d' ' -f1 "$f")" = "$1" ] || continue
    if [ "$2" = any ] || [ "$(cut -d' ' -f2 "$f")" = "$$" ]; then rm -f "${CAM_LOCKS:?}/${f##*/}"; fi
  done
}

# ---- JupyterLab servers of the students ----
port_busy() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
share_alive() { [ -f "$SHARE_DIR/$1.pid" ] && kill -0 "$(cat "$SHARE_DIR/$1.pid")" 2>/dev/null; }

# port_taken PORT: true when the folder of ANOTHER student keeps that port
port_taken() {
  local f
  for f in "$ROOT"/*/*/.port; do
    [ -f "$f" ] || continue
    [ "$f" = "$LAB_HOME/.port" ] && continue
    [ "$(cat "$f")" = "$1" ] && return 0
  done
  return 1
}

# student_port: the port of this student's JupyterLab. It is chosen once, kept in the student's folder
# (.port) and shown to the teacher, so it is the same in every session.
student_port() {
  local port
  port="$(cat "$LAB_HOME/.port" 2>/dev/null)"
  if [ -n "$port" ] && ! port_busy "$port" && ! port_taken "$port"; then echo "$port"; return; fi
  port=8801
  while port_busy "$port" || port_taken "$port"; do port=$((port+1)); done
  echo "$port" > "$LAB_HOME/.port"
  echo "$port"
}

share_list() {
  local f k ip host any=""
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"; host="$(hostname 2>/dev/null)"; host="${host%.local}"
  for f in "$SHARE_DIR"/*.port; do
    [ -f "$f" ] || continue
    k="${f##*/}"; k="${k%.port}"; any=1
    if share_alive "$k"; then
      printf '%s%-18s%s port %s   http://%s:%s/?token=%s\n' "$CT" "$(show_key "$k")" "$CN" "$(cat "$f")" "${ip:-$host}" "$(cat "$f")" "$(cat "$SHARE_DIR/$k.token")"
    else
      printf '%-18s not running (a lost connection? free it with:  lab stop %s)\n' "$(show_key "$k")" "$(show_key "$k" | tr '/' ' ')"
    fi
  done
  [ -n "$any" ] || echo "Nobody is working now."
}

# share_stop [KEY ...]: stop the JupyterLab of these sessions (all of them when no key is given)
share_stop() {
  local keys="$*" f k pid
  if [ -z "$keys" ]; then
    for f in "$SHARE_DIR"/*.pid; do [ -f "$f" ] || continue; k="${f##*/}"; keys="$keys ${k%.pid}"; done
  fi
  for k in $keys; do
    [ -n "$k" ] || continue
    if share_alive "$k"; then
      pid="$(cat "$SHARE_DIR/$k.pid")"; pkill -P "$pid" 2>/dev/null; kill "$pid" 2>/dev/null
      echo "Stopped the JupyterLab of $(show_key "$k")"
    fi
    rm -f "${SHARE_DIR:?}/${k:?}".pid "${SHARE_DIR:?}/${k:?}".port "${SHARE_DIR:?}/${k:?}".token "${SHARE_DIR:?}/${k:?}".owner
  done
}

# ---- A student session: lab start <name> class <class> [camera N] ----
# Starts the JupyterLab of the student in the background and opens a shell that is ready to work in:
# the Python environment is on, the folder is the student's own, the camera is the chosen one.
# When the student types "exit" the JupyterLab stops and the camera is free again.
# session_busy KEY: true (and a message) when this student already works in another terminal
session_busy() {
  local opid
  share_alive "$1" || return 1
  opid="$(cat "$SHARE_DIR/$1.owner" 2>/dev/null)"
  [ -n "$opid" ] && kill -0 "$opid" 2>/dev/null || return 1
  echo "$(show_key "$1") is already working in another terminal (JupyterLab: http://$(my_ip):$(cat "$SHARE_DIR/$1.port")/?token=$(cat "$SHARE_DIR/$1.token"))."
  echo "Use that terminal, or close it first (type exit there)."
}

session_server() {   # session_server KEY FIRST_NOTEBOOK  -> sets SESSION_PORT and SESSION_TOKEN
  local key="$1" first="$2" port token open="--no-browser"
  mkdir -p "$SHARE_DIR"; chmod 700 "$SHARE_DIR"
  STARTED_SERVER=""
  session_busy "$key" && return 1
  share_alive "$key" && share_stop "$key" > /dev/null      # a server left behind by a lost connection
  [ -z "$SSH_CONNECTION" ] && [ -n "$DISPLAY" ] && open=""     # at the Jetson screen: open the browser there
  port="$(student_port)"
  token="$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')"
  (
    cd "$LAB_HOME" || exit 1
    nohup jupyter lab $open --ip=0.0.0.0 --port="$port" --ServerApp.port_retries=0 --ServerApp.token="$token" \
      --ServerApp.allow_remote_access=True "$first" > "$LAB_HOME/.jupyter/server.log" 2>&1 &
    echo $! > "$SHARE_DIR/$key.pid"
  )
  echo "$port" > "$SHARE_DIR/$key.port"; echo "$token" > "$SHARE_DIR/$key.token"; echo "$$" > "$SHARE_DIR/$key.owner"
  chmod 600 "$SHARE_DIR/$key".*
  SESSION_PORT="$port"; SESSION_TOKEN="$token"; STARTED_SERVER=1
}

my_ip() { local ip; ip="$(hostname -I 2>/dev/null | awk '{print $1}')"; echo "${ip:-$(hostname 2>/dev/null)}"; }

session_cleanup() {
  [ -n "$SESSION_DONE" ] && return; SESSION_DONE=1
  [ -n "$STARTED_SERVER" ] && share_stop "$SESSION_KEY" > /dev/null
  cam_release_of "$SESSION_KEY"
  [ -n "$SESSION_RC" ] && rm -f "$SESSION_RC"
}

# lab_link [N]: inside a session the JupyterLab already runs, so show the link of Start_Here or of the notebook of lab N
lab_link() {
  local b path="lab/tree/Start_Here.ipynb" key
  key="$(key_of "$LAB_CLASS" "$(basename "$LAB_HOME")")"
  if [ -n "$1" ]; then
    b="$(basename "$(notebook_of "$1")" 2>/dev/null)"
    if [ -n "$b" ] && [ "$b" != "." ]; then path="lab/tree/lab$1/$b"; else echo "Lab $1 has no notebook yet. Here is Start_Here."; fi
  fi
  sync_notebooks
  echo "Your JupyterLab is running. Open this link in the browser of your laptop:"
  echo "  http://$(my_ip):$(cat "$SHARE_DIR/$key.port")/$path?token=$(cat "$SHARE_DIR/$key.token")"
}

# lab_start [NAME] [class CLASS] [camera N] [LAB]
lab_start() {
  local name="" labn="" cam="" cls="" prev="" a first="Start_Here.ipynb" b dev rc ip
  for a in "$@"; do
    if [ "$prev" = camera ]; then cam="$a"; prev=""; continue; fi
    if [ "$prev" = class ]; then cls="$a"; prev=""; continue; fi
    case "$a" in
      camera|class) prev="$a" ;;
      ''|*[!0-9]*) name="$a" ;;
      *) labn="$a" ;;
    esac
  done
  [ "$prev" = camera ] && { echo "Which camera?  Type  lab cameras  to see the numbers."; return 1; }
  [ "$prev" = class ] && { echo "Which class?  For example:  lab start ali class a camera 0"; return 1; }
  if [ -n "$LAB_IN_SESSION" ]; then      # we are inside a session: do not start a second one
    if [ -n "$name" ] && [ "$(clean_name "$name")" != "$(basename "$LAB_HOME")" ]; then
      echo "You are working as $(basename "$LAB_HOME") (class $LAB_CLASS). Type  exit  first, then  lab start $name"; return 1
    fi
    lab_link "$labn"; return $?
  fi
  choose_class "$cls" || return 1
  choose_student "$CHOSEN_CLASS" "$name" || return 1
  if [ ! -f ~/venvs/jetson/bin/activate ]; then
    echo "The course environment is missing. Run  bash $HERE/setup.sh  first."; return 1
  fi
  SESSION_NAME="$(basename "$LAB_HOME")"; SESSION_KEY="$(key_of "$LAB_CLASS" "$SESSION_NAME")"
  SESSION_DONE=""; SESSION_RC=""; STARTED_SERVER=""
  mkdir -p "$SHARE_DIR"; session_busy "$SESSION_KEY" && return 1
  if [ -n "$cam" ]; then
    case "$cam" in *[!0-9]*) echo "The camera is a number, for example:  lab start $SESSION_NAME class $LAB_CLASS camera 0"; return 1 ;; esac
    dev="$(camera_path "$cam")"
    if [ -z "$dev" ]; then echo "There is no camera number $cam. These cameras are plugged in:"; cameras_show; return 1; fi
    cam_take "$cam" "$SESSION_KEY" || { cameras_show; return 1; }
    export LAB_CAMERA="$dev"
  else
    unset LAB_CAMERA
  fi
  trap ':' INT                                   # Ctrl + C stops a program, not this session
  trap 'session_cleanup; exit 143' HUP TERM
  trap 'session_cleanup' EXIT
  source ~/venvs/jetson/bin/activate
  student_env
  sync_notebooks
  if [ -n "$labn" ]; then
    b="$(basename "$(notebook_of "$labn")" 2>/dev/null)"
    if [ -n "$b" ] && [ "$b" != "." ]; then first="lab$labn/$b"
    else echo "Lab $labn has no notebook yet. Opening Start_Here instead."; fi
  fi
  export LAB_HOME LAB_CLASS LAB_IN_SESSION=1 HISTFILE="$LAB_HOME/.bash_history"
  session_server "$SESSION_KEY" "$first" || { session_cleanup; return 1; }
  ip="$(my_ip)"
  echo
  say "Hello, $SESSION_NAME!  (class $LAB_CLASS)"
  echo "  Your folder:     $LAB_HOME"
  echo "  Your camera:     ${LAB_CAMERA:-none chosen}${cam:+  (camera $cam)}"
  echo "  Your JupyterLab: http://$ip:$SESSION_PORT/?token=$SESSION_TOKEN"
  echo "                   Open this link in the browser of your laptop. Your port, $SESSION_PORT, is always the same."
  echo "  When you finish: type  exit  . That stops your JupyterLab and frees the camera."
  echo
  rc="$(mktemp)"; SESSION_RC="$rc"
  cat > "$rc" <<RCEOF
[ -f ~/.bashrc ] && source ~/.bashrc
source ~/venvs/jetson/bin/activate
export HISTFILE="$LAB_HOME/.bash_history"
${LAB_CAMERA:+export LAB_CAMERA="$LAB_CAMERA"}
export PYTHONPATH="$HERE/labs\${PYTHONPATH:+:\$PYTHONPATH}"
cd "$LAB_HOME"
PS1="($LAB_CLASS/$SESSION_NAME) \u@\h:\w\\\$ "
RCEOF
  bash --rcfile "$rc" -i
  session_cleanup
  echo "Goodbye, $SESSION_NAME. Your JupyterLab is stopped and the camera is free."
}

# lab_stop CLASS NAME: the teacher frees the JupyterLab and the camera of a student whose connection was lost
lab_stop() {
  local c n key
  c="$(clean_name "$1")"; n="$(clean_name "$2")"
  [ -n "$c" ] && [ -n "$n" ] || { echo "Usage:  lab stop <class> <name>"; return 1; }
  key="$(key_of "$c" "$n")"
  share_stop "$key"; cam_release_of "$key" any
  echo "Stopped the session of $c/$n."
}

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

# ---- Teacher: classes, clean up, check the board ----
# classes_table: one line for each class
classes_table() {
  local c n size used working f k
  printf '%s  %-16s %-9s %-8s %-12s %s%s\n' "$CT" CLASS STUDENTS SIZE "LAST USED" "WORKING NOW" "$CN"
  for c in $(list_classes); do
    n="$(list_students "$c" | wc -l | tr -d ' ')"
    size="$(du -sh "$ROOT/$c" 2>/dev/null | cut -f1)"
    working=0
    for f in "$SHARE_DIR"/"$c"__*.pid; do
      [ -f "$f" ] || continue
      k="${f##*/}"; k="${k%.pid}"; share_alive "$k" && working=$((working+1))
    done
    printf '  %-16s %-9s %-8s %-12s %s\n' "$c" "$n" "$size" "$(last_used "$ROOT/$c")" "$working"
  done
  [ -n "$(list_classes)" ] || echo "  No class yet. Make one with:  lab class add <name>"
}

# class_show CLASS: the students of one class, with their port, camera and state
class_show() {
  local c s key port state cam
  c="$(clean_name "$1")"
  [ -d "$ROOT/$c" ] || { echo "There is no class called $c."; return 1; }
  printf '%s  Class %s%s\n' "$CT" "$c" "$CN"
  printf '  %-16s %-6s %-8s %-8s %-12s %s\n' STUDENT PORT SIZE CAMERA "LAST USED" STATE
  for s in $(list_students "$c"); do
    key="$(key_of "$c" "$s")"; port="$(cat "$ROOT/$c/$s/.port" 2>/dev/null)"
    if share_alive "$key"; then state="working"; cam="$(camera_of "$key")"; else state="-"; cam=""; fi
    printf '  %-16s %-6s %-8s %-8s %-12s %s\n' "$s" "${port:--}" "$(du -sh "$ROOT/$c/$s" 2>/dev/null | cut -f1)" "${cam:--}" "$(last_used "$ROOT/$c/$s")" "$state"
  done
  [ -n "$(list_students "$c")" ] || echo "  No student yet."
}

# lab_clean [CLASS [NAME]]: no argument lists the classes; a class deletes the class; a class and a name deletes one student
lab_clean() {
  local c n target size again s
  c="$(clean_name "$1")"; n="$(clean_name "$2")"
  if [ -z "$c" ]; then
    classes_table
    echo
    echo "See the students of a class:   lab class <class>"
    echo "Delete one student:            lab clean <class> <name>"
    echo "Delete the whole class:        lab clean <class>"
    return 0
  fi
  if [ ! -d "$ROOT/$c" ] || [ "${c#_}" != "$c" ]; then echo "There is no class called $c."; return 1; fi
  if [ -n "$n" ]; then target="$ROOT/$c/$n"; else target="$ROOT/$c"; fi
  if [ ! -d "$target" ]; then echo "There is no student called $n in class $c."; return 1; fi
  if [ ! -t 0 ]; then echo "lab clean asks a question, so run it in a terminal."; return 1; fi
  size="$(du -sh "$target" | cut -f1)"
  say "This deletes everything in $target ($size)"
  echo "Make sure the students copied their work to a laptop or a USB drive first."
  again="${n:-$c}"
  read -r -p "Type \"$again\" to delete: " s
  [ "$s" = "$again" ] || { echo "Cancelled. Nothing was deleted."; return 1; }
  if [ -n "$n" ]; then
    share_stop "$(key_of "$c" "$n")"; cam_release_of "$(key_of "$c" "$n")" any
  else
    for s in $(list_students "$c"); do share_stop "$(key_of "$c" "$s")"; cam_release_of "$(key_of "$c" "$s")" any; done
  fi
  rm -rf "${target:?}"
  echo "Deleted $target."
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
  title "5. Classes on this Jetson"
  classes_table
  echo "Delete a class or a student with:  lab clean <class> [name]"
}
