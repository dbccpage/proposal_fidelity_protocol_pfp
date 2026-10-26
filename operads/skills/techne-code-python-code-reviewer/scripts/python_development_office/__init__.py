"""
python_development_office — Clean Architecture and Python pitfall scanner,
reassembled inside the techne-code-python-code-reviewer skill folder.

**AuthorityEffect:** None. Findings are measurements. A clean scan is not a
review, not a proof, and not admission of anything.

Reassembled 2026-08-17 from `dbccpage/anomalonpy` `6f39bd7042`, where this
engine was spread across four layers of the `omega_engine_operations`
application (`domain/`, `use_cases/`, `infrastructure/`,
`controllers/`, `frontend/cli/`). `.agents/COPY.md` forbids importing
`omega_engine_operations` into CODA to make a skill work, so the slice was
copied here with its layer boundaries intact and its imports rewritten.

Standard library only.

Layers:

- ``domain``          — findings, severities, module info, architecture config
- ``use_cases``       — project walk, AST visitor, rule registry, output
- ``infrastructure``  — config loading
- ``controllers``     — audit orchestration
- ``frontend``        — the CLI

See ``../README.md`` for what changed relative to upstream.
"""

from __future__ import annotations

__version__ = "0.1.0+coda"

AUTHORITY_EFFECT = "None"
