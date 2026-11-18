#!/usr/bin/env python3
"""Programmatic Python anti-pattern and architecture scanner forwarder.

Delegates to the `python_development_office` engine, which lives in the
`techne-code-python-code-reviewer` skill folder — that skill owns the scanner;
this one borrows it rather than carrying a second copy of ~2,100 lines.

Previously this was a shim onto
`operads.frontend.cli.python_dev_cli`, reached by inserting the
repository root onto `sys.path`. That package is not in CODA, and
`.agents/COPY.md` forbids importing it here.

Run from anywhere::

    python operads/skills/techne-code-python-principal-developer/scripts/python_antipattern_scanner.py <path> [--json]

AuthorityEffect: None. A clean scan is a measurement, not a review.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[2]
_ENGINE_HOME = _SKILLS / "techne-code-python-code-reviewer" / "scripts"

if not (_ENGINE_HOME / "python_development_office").is_dir():
    raise SystemExit(
        "python_development_office engine not found at "
        f"{_ENGINE_HOME / 'python_development_office'}.\n"
        "It is owned by the techne-code-python-code-reviewer skill. If that "
        "skill was culled, either restore it or copy the engine into this "
        "skill's scripts/ folder."
    )

if str(_ENGINE_HOME) not in sys.path:
    sys.path.insert(0, str(_ENGINE_HOME))

from python_development_office.frontend.cli import main  # noqa: E402

__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
