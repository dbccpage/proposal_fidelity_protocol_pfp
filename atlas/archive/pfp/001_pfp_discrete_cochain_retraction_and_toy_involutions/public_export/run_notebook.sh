#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"
uv run --with jupyter --with ipywidgets --with numpy --with matplotlib jupyter notebook jupyter_notebooks/demo1_holonomy_interactive.ipynb
