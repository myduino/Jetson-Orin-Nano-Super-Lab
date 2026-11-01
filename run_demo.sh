#!/bin/bash
# Starts the Myduino AI Vision Demo from this folder:   bash run_demo.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source ~/venvs/jetson/bin/activate 2>/dev/null || echo "Run 'bash setup.sh' first."
cd "$HERE/labs/lab0_demo" || exit 1
python demo.py "$@"
