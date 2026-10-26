#!/usr/bin/env python3
"""CLI composition root for the documentation-integrity bounded context."""

from __future__ import annotations

import subprocess
import sys


def _direct_main() -> int:
    if __package__:
        from omega_engine_pfp.documentation_integrity.cli import main

        return main()
    completed = subprocess.run(
        [sys.executable, "-m", "omega_engine_pfp.scripts.docs_integrity", *sys.argv[1:]],
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(_direct_main())
