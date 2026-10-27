#!/usr/bin/env python3
"""Thin skill wrapper for segmentation and candidate mining only."""

from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path:
    for candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (candidate / ".agents").is_dir() and (candidate / "engine").is_dir():
            return candidate
    raise RuntimeError("repository root not found")


def _required_ooutwire_output(root: Path) -> Path:
    try:
        index = sys.argv.index("--output")
        raw = sys.argv[index + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit("auto-antiskill requires --output under ooutwire/") from exc
    output = Path(raw)
    if not output.is_absolute():
        output = root / output
    output = output.resolve(strict=False)
    allowed = (root / ".agents" / "antiskills" / "ooutwire").resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        raise SystemExit("auto-antiskill output must be a file under ooutwire/")
    relative = output.relative_to(allowed)
    cursor = allowed
    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise SystemExit("auto-antiskill refuses symlinked output parents")
    if output.exists() and output.is_symlink():
        raise SystemExit("auto-antiskill refuses a symlink output")
    return output


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {
        "mine-candidates",
        "segment-dialogue",
    }:
        raise SystemExit("auto-antiskill permits: segment-dialogue, mine-candidates")
    root = _repo_root()
    _required_ooutwire_output(root)
    sys.path.insert(0, str(root))
    from engine.crates.prompt_civilization.cli import main as runtime_main

    return runtime_main()


if __name__ == "__main__":
    raise SystemExit(main())
