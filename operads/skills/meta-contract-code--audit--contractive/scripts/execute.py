#!/usr/bin/env python3
"""Executable runner for meta-contract-code--audit--contractive operad metaskill."""
from __future__ import annotations

import sys
from pathlib import Path


def _find_root() -> Path:
    for p in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (p / ".git").exists() and (p / ".agents").exists():
            return p
    return Path(__file__).resolve().parents[4]

repo_root = _find_root()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from omega_engine_operads.frontend.cli.meta_operad_cli import main  # noqa: E402

if __name__ == "__main__":
    sys.argv.insert(1, "meta-contract-code--audit--contractive")
    sys.exit(main())
