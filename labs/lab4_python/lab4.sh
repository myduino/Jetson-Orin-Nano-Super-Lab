#!/bin/bash
# Lab 4: Python on Jetson.   Run a part with:   lab 4 A   (or B, C, D, E)
# This file is loaded by lab.sh. It shows each command and then runs it for you.

LAB_TITLE="Python on Jetson"
PARTS=(
  "A|Run your first Python (calculator, hello.py, an error)"
  "B|Virtual environments and pip"
  "C|Python basics: run basics1.py, basics2.py and basics3.py"
  "D|NumPy arrays, speed test and your CPU baseline"
  "E|JupyterLab"
)

LABDIR="$(dirname "$SCRIPT")"
WORK=~/jetson-labs/lab4

partA() {
  deactivate 2>/dev/null     # Part A shows the system Python, so the course environment is off here
  title "Part A, Step 1: Create the workspace and check Python"
  run cd ~/jetson-labs
  run mkdir -p lab4
  run cd lab4
  run python3 --version
  run which python3
  say "The next command should say: python: command not found"
  run python --version
  pause
  title "Part A, Step 2: Use Python as a calculator"
  for e in '2 + 3 * 4' '10 / 3' '10 // 3' '10 % 3' '2 ** 10' '"Jetson" + " Nano"'; do
    printf '%s>>> %s%s\n' "$CC" "$e" "$CN"
    python3 -c "print($e)"
  done
  run "python3 -c 'print(\"Hello, Jetson!\")'"
  pause
  title "Part A, Step 3: Your first script"
  cd "$WORK"
  run "printf 'name = input(\"What is your name? \")\nprint(\"Hello,\", name)\nprint(\"Welcome to the Jetson Orin Nano Super!\")\n' > hello.py"
  run cat hello.py
  say "Type your name when it asks."
  run python3 hello.py
  pause
  title "Part A, Step 4: Break it on purpose"
  run "sed 's/print(\"Hello,\", name)/print(\"Hello, name)/' hello.py > hello_broken.py"
  run cat hello_broken.py
  run "python3 hello_broken.py < /dev/null"
  say "Read the last line of the error message and the line number. hello.py itself is still correct."
  pause
}

partB() {
  title "Part B, Step 1: Check the venv tools"
  run "python3 -m venv --help | head -n 2"
  run pip3 --version
  pause
  title "Part B, Step 2: Create the environment (it already exists, so this is safe)"
  run mkdir -p ~/venvs
  run python3 -m venv --system-site-packages ~/venvs/jetson
  run ls ~/venvs/jetson
  pause
  title "Part B, Step 3: Activate it"
  run source ~/venvs/jetson/bin/activate
  run which python
  run python --version
  pause
  title "Part B, Step 4: Check NumPy"
  run "pip list | grep -i numpy"
  run pip show numpy
  pause
  title "Part B, Step 5: Save and restore a package list"
  run cd "$WORK"
  run "pip freeze --local > requirements.txt"
  run "head -n 15 requirements.txt"
  pause
  title "Part B, Step 6: The jet shortcut"
  say "setup.sh already added the shortcut line to ~/.bashrc. Here it is:"
  run "grep 'alias jet' ~/.bashrc"
  say "Type  jet  in a new terminal to turn the environment on. Type  deactivate  to turn it off."
  pause
}

partC() {
  title "Part C: Python basics"
  mkdir -p "$WORK"
  for f in basics1.py basics2.py basics3.py; do
    [ -f "$WORK/$f" ] || cp "$LABDIR/$f" "$WORK/$f"
  done
  run cd "$WORK"
  title "Script 1: Variables and maths"
  run cat basics1.py
  run python basics1.py
  pause
  title "Script 2: Lists, conditions and loops"
  run cat basics2.py
  run python basics2.py
  pause
  title "Script 3: Functions, files and errors"
  run cat basics3.py
  run python basics3.py
  pause
  say "Now try the changes in the Try It Yourself table. Open a file with:  nano basics1.py"
}

partD() {
  mkdir -p "$WORK"
  for f in arrays.py speed.py baseline.py; do
    [ -f "$WORK/$f" ] || cp "$LABDIR/$f" "$WORK/$f"
  done
  run cd "$WORK"
  title "Part D, Steps 1 and 2: NumPy arrays and a tiny image (like typing at the >>> prompt)"
  run python arrays.py
  pause
  title "Part D, Step 3: Compare a Python loop with NumPy (three runs)"
  run python speed.py
  run python speed.py
  run python speed.py
  pause
  title "Part D, Step 4: Record your CPU baseline for Lab 5 (run it twice, record the second run)"
  say "First check your power mode:"
  run sudo nvpmodel -q
  run python baseline.py
  run python baseline.py
  pause
}

partE() {
  title "Part E, Step 1: Check JupyterLab"
  run jupyter lab --version
  pause
  title "Part E, Step 2: Start JupyterLab"
  say "The browser opens on the Jetson screen. Leave this terminal open while you use JupyterLab."
  say "To stop it later, come back here, press Ctrl + C and answer y."
  pause
  mkdir -p "$WORK"
  run cd "$WORK"
  run jupyter lab
}

main() {
  case "$1" in
    A) partA ;;
    B) partB ;;
    C) partC ;;
    D) partD ;;
    E) partE ;;
    *) show_parts ;;
  esac
}
