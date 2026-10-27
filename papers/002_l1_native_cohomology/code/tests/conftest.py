from __future__ import annotations

import sys
from pathlib import Path

# Ensure code package directory is on sys.path
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))
