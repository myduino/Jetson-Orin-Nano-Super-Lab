#!/bin/bash
# Runs the commands of one lab part for you.   Usage:   lab <lab number> <part letter>
# Example:   lab 2 C      (the "lab" shortcut is created by setup.sh; open a new terminal after setup)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB="$1"
PART="$(echo "$2" | tr a-z A-Z)"

if [ -z "$LAB" ]; then
  echo "Usage: lab <lab number> <part letter>      for example: lab 2 C"
  echo "Labs with a script: $(ls "$HERE"/labs/lab*_*/lab[0-9].sh 2>/dev/null | sed 's/.*\/lab\([0-9]\)\.sh/\1/' | tr '\n' ' ')"
  exit 0
fi

SCRIPT=$(ls "$HERE"/labs/lab"$LAB"_*/lab"$LAB".sh 2>/dev/null | head -n 1)
if [ -z "$SCRIPT" ]; then
  echo "There is no script for lab $LAB. Check the number in your manual."
  exit 1
fi

source ~/venvs/jetson/bin/activate 2>/dev/null
source "$HERE/labs/lib.sh"
LABNUM="$LAB"
source "$SCRIPT"
main "$PART"
