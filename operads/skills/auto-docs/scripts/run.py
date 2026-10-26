#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executable runner for auto-docs skill."""

from __future__ import annotations

import sys
from pathlib import Path


def _find_root() -> Path:
    for p in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (p / ".git").exists() and (p / ".agents").exists():
            return p
    return Path(__file__).resolve().parents[4]


def run() -> int:
    repo_root = _find_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from omega_engine_operations.use_cases.packaging.auto_docs_service import (
        main as auto_docs_main,
    )

    return auto_docs_main()


if __name__ == "__main__":
    sys.exit(run())
