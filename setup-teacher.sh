#!/bin/bash
# For a teacher PC with Mac or Linux:   bash setup-teacher.sh
# It starts the teacher page. Keep this window open while you teach.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/labs/teacher_server.py"
