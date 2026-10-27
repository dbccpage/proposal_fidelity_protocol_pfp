#!/usr/bin/env python3
"""Programmatic Python anti-pattern, Clean Architecture, and pitfall scanner.

Driven by the `python_development_office` engine reassembled beside this file.

Previously this was a shim onto
`operads.frontend.cli.python_dev_cli`, reached by inserting
`parents[4]` (the repository root) onto `sys.path`. That package is not in
CODA, and `.agents/COPY.md` forbids importing it here, so the engine now lives
in `scripts/python_development_office/`.

Run from anywhere::

    python operads/skills/techne-code-python-code-reviewer/scripts/python_antipattern_scanner.py <path> [--json]

AuthorityEffect: None. A clean scan is a measurement, not a review.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from python_development_office.frontend.cli import main  # noqa: E402

__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
