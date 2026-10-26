from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_direct_and_module_entrypoints_expose_same_commands() -> None:
    commands = (
        [sys.executable, "omega_engine_pfp/scripts/docs_integrity.py", "--help"],
        [sys.executable, "-m", "omega_engine_pfp.scripts.docs_integrity", "--help"],
    )
    outputs = []
    for command in commands:
        completed = subprocess.run(
            command, cwd=REPO_ROOT, capture_output=True, text=True, check=False
        )
        assert completed.returncode == 0, completed.stderr
        outputs.append(completed.stdout)
    assert all("{inventory,validate}" in output for output in outputs)
