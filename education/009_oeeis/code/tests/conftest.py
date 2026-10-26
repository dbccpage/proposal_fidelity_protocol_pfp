"""Test fixtures and path configuration for Epistemic Immune System (Track 050).

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent
MODULE_ROOT = next(
    (p for p in HERE.parents if (p / "levels").is_dir() or (p / "grammar").is_dir()),
    HERE.parents[1],
)
REPO_ROOT = next(
    (p for p in HERE.parents if (p / ".git").exists() or (p / "pixi.toml").exists()),
    HERE.parents[4],
)

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
