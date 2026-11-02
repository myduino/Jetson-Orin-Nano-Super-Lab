#!/bin/bash
# Starts JupyterLab on the Jetson screen:   bash run_jupyter.sh      (same as:  lab start)
# Add a lab number to open that lab's notebook:   bash run_jupyter.sh 5
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$HERE/lab.sh" start "$@"
