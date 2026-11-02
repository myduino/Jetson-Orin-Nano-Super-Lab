#!/bin/bash
# Starts the Myduino AI Vision Demo from this folder:   bash run_demo.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source ~/venvs/jetson/bin/activate 2>/dev/null || echo "Run 'bash setup.sh' first."
cd "$HERE/labs/lab0_demo" || exit 1
# Use the model files that setup.sh downloaded, so the demo needs no internet.
[ -f yolo26n.pt ] || cp ~/students/_shared/models/yolo26n.pt . 2>/dev/null
export PYTHONPATH="$HERE/labs${PYTHONPATH:+:$PYTHONPATH}"
python demo.py "$@"
