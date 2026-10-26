"""Filesystem and Ruff adapters for the Python quality inventory."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence


class FileSystemPythonInventoryRepository:
    """Read Python source without following directory symlinks."""

    def discover_python(self, target: str, excluded_directories: Sequence[str]) -> tuple[str, ...]:
        root = Path(target).resolve()
        if root.is_file():
            return (str(root),) if root.suffix == ".py" else ()
        if not root.is_dir():
            raise ValueError(f"inventory target does not exist: {target}")
        excluded = set(excluded_directories)
        discovered: list[str] = []
        for current, directories, filenames in os.walk(root, followlinks=False):
            directories[:] = sorted(
                name
                for name in directories
                if name not in excluded and not (Path(current) / name).is_symlink()
            )
            for filename in sorted(filenames):
                candidate = Path(current) / filename
                if candidate.suffix != ".py":
                    continue
                if candidate.is_symlink():
                    raise ValueError(f"symbolic-link Python source refused: {candidate}")
                discovered.append(str(candidate.resolve()))
        return tuple(discovered)

    def read_text(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")


class RuffComplexityAnalyzer:
    """Run Ruff's canonical C901 implementation as an injected adapter."""

    def c901_findings(self, target: str, maximum: int) -> tuple[tuple[str, int, str], ...]:
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--isolated",
                "--select",
                "C901",
                "--output-format",
                "json",
                "--config",
                f"lint.mccabe.max-complexity={maximum}",
                target,
            ),
            check=False,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if completed.returncode not in (0, 1):
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise ValueError(f"Ruff C901 execution failed ({completed.returncode}): {detail}")
        try:
            payload = json.loads(completed.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise ValueError(f"Ruff emitted invalid JSON: {exc}") from exc
        findings: list[tuple[str, int, str]] = []
        for item in payload:
            findings.append(
                (
                    str(Path(item["filename"]).resolve()),
                    int(item["location"]["row"]),
                    str(item["message"]),
                )
            )
        return tuple(findings)
