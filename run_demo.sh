#!/bin/bash
# Starts the Myduino AI Vision Demo from this folder:   bash run_demo.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source ~/venvs/jetson/bin/activate 2>/dev/null || echo "Run 'bash setup.sh' first."
cd "$HERE/labs/lab0_demo" || exit 1
# Use the model files that setup.sh downloaded, so the demo needs no internet.
# The fast engine from Lab 8 is used too, if it exists.
[ -f yolo26n.pt ] || cp ~/jetson-labs/models/yolo26n.pt . 2>/dev/null
[ -f yolo26n_fp16.engine ] || cp ~/jetson-labs/lab8/yolo26n_fp16.engine . 2>/dev/null
python demo.py "$@"
