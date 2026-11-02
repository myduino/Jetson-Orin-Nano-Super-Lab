#!/bin/bash
# Lab 5: NVIDIA CUDA with Python.   Run a part with:   lab 5 A   (or B, F)
# Parts C, D and E are done in the notebook that Part A opens.

LAB_TITLE="NVIDIA CUDA with Python"
PARTS=(
  "A|Check CUDA, then open the Lab 5 notebook"
  "B|Check CuPy (the notebook has the rest of Parts B to E)"
  "C|In the notebook (start it with: lab 5 A)"
  "D|In the notebook (start it with: lab 5 A)"
  "E|In the notebook (start it with: lab 5 A)"
  "F|Check the power mode, then run the comparison in the notebook"
)

partA() {
  title "Part A, Step 1: Create the workspace"
  run cd ~/jetson-labs
  run mkdir -p lab5
  run cd lab5
  pause
  title "Part A, Step 2: Look for the CUDA compiler"
  run "ls /usr/local/ | grep cuda"
  if ! command -v nvcc >/dev/null 2>&1; then
    say "nvcc is not on your PATH yet. Adding it now (and for new terminals)."
    run 'export PATH=/usr/local/cuda/bin:$PATH'
    grep -q "/usr/local/cuda/bin" ~/.bashrc || echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
  fi
  run nvcc --version
  pause
  title "Part A, Steps 3 and 4: jtop and the notebook"
  say "Step 3: open jtop in a second terminal tab (Ctrl + Shift + T, then type  jtop ) and watch the GPU line."
  say "Step 4: JupyterLab opens next, in the Lab 5 notebook folder. Leave this terminal open."
  say "To stop JupyterLab later, come back here, press Ctrl + C and answer y."
  pause
  run bash "$HERE/run_jupyter.sh" 5
}

partB() {
  title "Part B, Steps 1 and 2: Check CuPy"
  run "pip list 2>/dev/null | grep -i -E '^(numpy|cupy-cuda12x|torch) '"
  run 'python -c "import cupy as cp; print(cp.__version__); print(cp.arange(5) * 2)"'
  say "Step 3 (the GPU properties) is in the notebook. Open it with:  lab 5 A"
  pause
}

partF() {
  title "Part F, Step 1: Check the power mode"
  run sudo nvpmodel -q
  say "Steps 2 to 4 (the timing) are in the notebook. Open it with:  lab 5 A"
  pause
}

partNB() {
  say "This part is done in the Lab 5 notebook. Open it with:  lab 5 A"
}

main() {
  case "$1" in
    A) partA ;;
    B) partB ;;
    C|D|E) partNB ;;
    F) partF ;;
    *) show_parts ;;
  esac
}
