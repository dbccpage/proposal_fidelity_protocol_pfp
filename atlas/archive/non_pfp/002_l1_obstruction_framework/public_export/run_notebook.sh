#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m jupyter notebook jupyter_notebooks/000_l1_obstruction_framework.ipynb
