"""Run the receiving side's ``ledger --check`` from this directory, in its
default context (no clone argument).  Exits with its code.

AuthorityEffect: None
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def main() -> int:
    cli = "research.mssn_sn_tower.code.python.reach.cli"
    return subprocess.run([sys.executable, "-m", cli, "ledger", "--check"], cwd=REPO, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
