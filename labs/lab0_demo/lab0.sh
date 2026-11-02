#!/bin/bash
# Lab 0: See It First.   Run the demo with:   lab 0 A
# (The one-time setup in Part 0 is typed by hand, because the lab shortcut does not exist before it.)

LAB_TITLE="See It First"
PARTS=(
  "A|Start the AI vision demo (needs the USB camera)"
)

partA() {
  title "Part A: Start the demo"
  say "Wait about 20 seconds while the AI model loads. A window then opens with the camera picture (over SSH: a link for your laptop browser)."
  run bash "$HERE/run_demo.sh"
}

main() {
  case "$1" in
    A) partA ;;
    *) show_parts ;;
  esac
}
