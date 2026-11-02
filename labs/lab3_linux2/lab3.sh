#!/bin/bash
# Lab 3: Ubuntu Linux Essentials, Part 2.   Run a part with:   lab 3 A   (or B, C, D)
# This file is loaded by lab.sh. It shows each command and then runs it for you.

LAB_TITLE="Ubuntu Linux Essentials, Part 2"
PARTS=(
  "A|Permissions and sudo"
  "B|Install software with apt"
  "C|Network and SSH (find your address, check the SSH server)"
  "D|Monitor the system (uptime, top, tegrastats and more)"
)

partA() {
  title "Part A, Step 1: Create the Lab 3 workspace"
  run cd ~/jetson-labs
  run mkdir -p lab3
  run cd lab3
  run mkdir -p scripts files
  run ls -l
  pause
  title "Part A, Step 2: Read permission strings"
  mkdir -p ~/jetson-labs/lab2/notes
  [ -f ~/jetson-labs/lab2/notes/board_info.txt ] || say "(board_info.txt from Lab 2 Part E is missing, so the first command will show an error.)"
  run ls -l ~/jetson-labs/lab2/notes/board_info.txt
  run ls -l /etc/hostname
  run ls -l /etc/shadow
  run ls -l /bin/ls
  say "The next command should fail with Permission denied. That is the system protecting the password file."
  run cat /etc/shadow
  pause
  title "Part A, Step 3: Make a script executable"
  run cd ~/jetson-labs/lab3
  run "printf '#!/bin/bash\necho \"Hello from the Jetson\"\necho \"Today is \$(date)\"\necho \"I am \$(whoami)\"\n' > scripts/hello.sh"
  run chmod -x scripts/hello.sh
  run cat scripts/hello.sh
  say "Now try to run it. It should fail with Permission denied."
  run ./scripts/hello.sh
  run ls -l scripts/hello.sh
  run chmod +x scripts/hello.sh
  run ls -l scripts/hello.sh
  run ./scripts/hello.sh
  pause
  title "Part A, Step 4: Numeric permissions"
  run 'echo "my secret" > files/secret.txt'
  run ls -l files/secret.txt
  run chmod 600 files/secret.txt
  run ls -l files/secret.txt
  run chmod 644 files/secret.txt
  run ls -l files/secret.txt
  pause
  title "Part A, Step 5: Try sudo"
  say "The first sudo asks for your password. Nothing appears while you type it."
  run whoami
  run sudo whoami
  run ls /root
  run sudo ls /root
  pause
}

partB() {
  title "Part B, Step 1: Update the package list"
  run sudo apt update
  pause
  title "Part B, Step 2: Search and inspect a package"
  run "apt search htop | head -n 10"
  run "apt show htop | head -n 8"
  pause
  title "Part B, Step 3: Install and run"
  run sudo apt install htop -y
  say "htop opens next. Press q to quit it."
  pause
  run htop
  title "Part B, Step 4: Remove and reinstall"
  run sudo apt remove htop -y
  hash -r   # forget the old htop path, so the shell says: command not found
  say "htop should now say: command not found."
  run htop
  run sudo apt install htop -y
  pause
  title "Part B, Step 5: Explore installed packages with pipes"
  run "dpkg -l | wc -l"
  run "dpkg -l | grep -i python3 | head -n 5"
  run "dpkg -l | grep -i nvidia | head -n 10"
  run "dpkg -l | grep nvidia-jetpack"
  pause
  title "Part B, Step 6: Look at NVIDIA's repository"
  run ls /etc/apt/sources.list.d/
  run "cat /etc/apt/sources.list.d/nvidia*"
  pause
}

partC() {
  title "Part C, Step 1: Find your address and test the network"
  run hostname
  run hostname -I
  run "ping -c 4 8.8.8.8"
  run "ping -c 4 google.com"
  pause
  title "Part C, Step 2: Check the SSH server"
  run sudo systemctl status ssh --no-pager
  pause
  title "Part C, Steps 3 and 4: Connect from your laptop (type these on the LAPTOP)"
  IP="$(hostname -I | awk '{print $1}')"
  say "Your Jetson user name is: $(whoami)"
  say "Your Jetson address is:   $IP"
  say "On your laptop, open a terminal and type:"
  printf '    ssh %s@%s\n' "$(whoami)" "$IP"
  say "To copy files with scp, type these on the laptop:"
  printf '    echo "Hello from my laptop" > laptop_note.txt\n'
  printf '    scp laptop_note.txt %s@%s:~/jetson-labs/lab3/files/\n' "$(whoami)" "$IP"
  printf '    scp %s@%s:~/jetson-labs/lab2/notes/board_info.txt .\n' "$(whoami)" "$IP"
  pause
}

partD() {
  title "Part D, Step 1: Quick health checks"
  run uptime
  run free -h
  run df -h /
  run du -sh ~/jetson-labs
  pause
  title "Part D, Step 2: Watch the system live"
  say "top opens next. Press q to quit. Then htop opens. Press q or F10 to quit."
  pause
  run top
  run htop
  title "Part D, Step 3: Find and stop a process"
  run "sleep 300 &"
  run pgrep sleep
  say "Write the number above in your manual. Now stop the process with kill:"
  run 'kill $(pgrep sleep)'
  run "sleep 1; pgrep sleep || echo 'The sleep process is gone.'"
  pause
  title "Part D, Step 4: Watch the Jetson with tegrastats (stops by itself after 10 seconds)"
  run sudo timeout 10 tegrastats
  pause
  title "Part D, Step 5: See the effect of load"
  say "First read the IDLE values: htop opens. Note the busiest core and press q."
  pause
  run htop
  say "Now one CPU core is kept busy with yes. Wait 30 seconds, then read htop again and press q."
  run "yes > /dev/null &"
  pause
  run htop
  run 'kill $(pgrep yes)'
  say "yes is stopped. Part D is finished."
  say "To restart or shut down, type the commands yourself (see Step 6 in the manual)."
}

main() {
  case "$1" in
    A) partA ;;
    B) partB ;;
    C) partC ;;
    D) partD ;;
    *) show_parts ;;
  esac
}
