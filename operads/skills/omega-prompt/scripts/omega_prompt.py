#!/usr/bin/env python3
"""Thin skill wrapper for review/approval/packetization verbs.

**AuthorityEffect:** None. Canonical skill admitted under ooutwire register Entry 0276.

The runtime it wraps — `omega_engine.crates.prompt_civilization.cli`, 25
modules and ~7,850 lines — was not ported into CODA. Porting it would
stand up an unadmitted proposal's machinery, which is what the ooutwire
register exists to prevent. `OpenObstruction R-PROMPTCIV-ABSENT`.

Reaching the runtime used to raise a bare `ModuleNotFoundError` from inside
`main()`. It now refuses with a typed message that says what is missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

RUNTIME_MODULE = "omega_engine.crates.prompt_civilization.cli"

_ABSENT = f"""\
omega-prompt: REFUSED - runtime absent.

  required: {RUNTIME_MODULE}
  status:   not ported

This wrapper is an admitted skill under omega_engine_operads/skills/omega-prompt/.
Its runtime stays in dbccpage/anomalonpy.
To work on the skill, read SKILL.md and references/ - no runtime needed.
AuthorityEffect: None.\
"""


def _repo_root() -> Path:
    for candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (candidate / ".agents").is_dir() and (candidate / ".git").exists():
            return candidate
    raise SystemExit("omega-prompt: repository root not found")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {
        "approve",
        "packetize",
        "review",
        "validate-registry",
        "--help",
        "-h",
    }:
        raise SystemExit("omega-prompt permits: review, approve, packetize, validate-registry")
    if sys.argv[1] in {"--help", "-h"}:
        print("omega-prompt permits: review, approve, packetize, validate-registry")
        return 0

    root = _repo_root()
    sys.path.insert(0, str(root))
    try:
        from omega_engine.crates.prompt_civilization.cli import main as runtime_main
    except ImportError:
        raise SystemExit(_ABSENT) from None

    return runtime_main()


if __name__ == "__main__":
    raise SystemExit(main())
