#!/bin/bash
# Starts JupyterLab on the Jetson screen, in this lab folder:   bash run_jupyter.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source ~/venvs/jetson/bin/activate 2>/dev/null || echo "Run 'bash setup.sh' first."
cd "$HERE" || exit 1
jupyter lab
