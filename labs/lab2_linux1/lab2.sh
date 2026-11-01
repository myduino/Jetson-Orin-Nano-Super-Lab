#!/bin/bash
# Lab 2: Ubuntu Linux Essentials, Part 1.   Run a part with:   lab 2 A   (or B, C, D, E, F)
# This file is loaded by lab.sh. It shows each command and then runs it for you.

partA() {
  title "Part A, Step 2: Run your first commands"
  run whoami
  run hostname
  run date
  run pwd
  pause
}

partB() {
  title "Part B, Step 1: List files in different ways"
  run cd ~
  run ls
  run ls -l
  run ls -a
  run ls -lh
  pause
  title "Part B, Step 2: Move around with cd"
  run cd /
  run ls
  run cd /etc
  run ls
  run cd ~
  run pwd
  run cd /usr
  run cd ..
  run pwd
  run cd -
  pause
  title "Part B, Step 3: Look inside five system folders (first 8 items of each)"
  for d in /etc /usr /var /dev /tmp; do
    run "cd $d"
    run "ls | head -n 8"
  done
  run cd ~
  pause
}

partC() {
  title "Part C, Step 1: Check the tree tool"
  run tree --version
  pause
  title "Part C, Step 2: Build your lab workspace"
  run cd ~
  run mkdir -p jetson-labs
  run cd jetson-labs
  run mkdir -p lab2
  run cd lab2
  run mkdir -p notes scripts data
  run ls
  pause
  title "Part C, Step 3: Create files"
  run touch data/sample.txt
  run touch notes/todo.txt
  run ls -l data notes
  pause
  title "Part C, Step 4: Copy, move and rename"
  run cp data/sample.txt data/sample_copy.txt
  run mv data/sample_copy.txt notes/
  run mv notes/sample_copy.txt notes/backup.txt
  run ls data notes
  pause
  title "Part C, Step 5: Delete files and folders"
  run mkdir -p temp
  run touch temp/old.txt
  run rm temp/old.txt
  run rmdir temp
  run rm notes/backup.txt
  run ls
  pause
  title "Part C, Step 6: View the result as a tree"
  run cd ~/jetson-labs
  run tree lab2
  pause
}

partD() {
  mkdir -p ~/jetson-labs/lab2/notes
  title "Part D, Step 1: Write and read a small file"
  run cd ~/jetson-labs/lab2
  run 'echo "Hello Jetson" > notes/hello.txt'
  run 'echo "Linux is fun" >> notes/hello.txt'
  run cat notes/hello.txt
  pause
  title "Part D, Step 2: Read system files"
  run cat /etc/os-release
  run head -n 3 /proc/meminfo
  say "Next the file opens in less. Press Space for the next page and q to quit."
  pause
  run less /etc/nvpmodel.conf
}

partE() {
  mkdir -p ~/jetson-labs/lab2/notes
  title "Part E, Step 1: Create the file and open it in nano"
  run cd ~/jetson-labs/lab2/notes
  run "printf 'Board: Jetson Orin Nano Super\nJetPack: 6.2\nPower mode: MAXN SUPER\nStudent: (your name)\n' > board_info.txt"
  say "The file now has four lines. nano opens next. Change the last line to your own name."
  say "Then press Ctrl + O, Enter, and Ctrl + X to save and exit."
  pause
  run nano board_info.txt
  run cat board_info.txt
}

partF() {
  title "Part F: Get help and work faster"
  say "man ls opens the manual. Press q to quit it."
  pause
  run man ls
  run "ls --help | head -n 15"
  HISTFILE=~/.bash_history; set -o history; history -r 2>/dev/null
  run "history | tail -n 10"
}

main() {
  case "$1" in
    A) partA ;;
    B) partB ;;
    C) partC ;;
    D) partD ;;
    E) partE ;;
    F) partF ;;
    *) parts_help C "A B C D E F" ;;
  esac
}
