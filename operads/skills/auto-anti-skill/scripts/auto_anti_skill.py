#!/usr/bin/env python3
"""Thin skill wrapper for segmentation and candidate mining only.

**AuthorityEffect:** None. Canonical skill admitted under ooutwire register Entry 0275.
Executes prompt civilization CLI for dialogue segmentation and candidate mining,
enforcing all outputs strictly under `omega_engine_epistemic_immune_system/antiskills/ooutwire/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

RUNTIME_MODULE = "omega_engine.crates.prompt_civilization.cli"

_ABSENT = f"""\
auto-anti-skill: REFUSED - runtime absent.

  required: {RUNTIME_MODULE}
  status:   failed to import prompt civilization runtime

AuthorityEffect: None.\
"""


def _repo_root() -> Path:
    for candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (candidate / ".agents").is_dir() and (candidate / ".git").exists():
            return candidate
    raise SystemExit("auto-anti-skill: repository root not found")


def _required_ooutwire_output(root: Path) -> Path:
    try:
        index = sys.argv.index("--output")
        raw = sys.argv[index + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit("auto-anti-skill requires --output under ooutwire/") from exc
    output = Path(raw)
    if not output.is_absolute():
        output = root / output
    output = output.resolve(strict=False)
    allowed = (root / "omega_engine_epistemic_immune_system" / "antiskills" / "ooutwire").resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        raise SystemExit("auto-anti-skill output must be a file under ooutwire/")
    relative = output.relative_to(allowed)
    cursor = allowed
    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise SystemExit("auto-anti-skill refuses symlinked output parents")
    if output.exists() and output.is_symlink():
        raise SystemExit("auto-anti-skill refuses a symlink output")
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {
        "mine-candidates",
        "segment-dialogue",
    }:
        raise SystemExit("auto-anti-skill permits: segment-dialogue, mine-candidates")
    root = _repo_root()
    _required_ooutwire_output(root)

    # Provide sensible defaults if not explicitly passed
    cmd = sys.argv[1]
    if cmd == "segment-dialogue" and "--source" not in sys.argv:
        default_source = root / "omega_engine_epistemic_immune_system" / "antiskills" / "fixtures" / "default_transcript.txt"
        sys.argv.extend(["--source", str(default_source)])
    elif cmd == "mine-candidates" and "--episodes" not in sys.argv:
        default_episodes = root / "omega_engine_epistemic_immune_system" / "antiskills" / "fixtures" / "default_episodes.json"
        sys.argv.extend(["--episodes", str(default_episodes)])

    sys.path.insert(0, str(root))
    try:
        from omega_engine.crates.prompt_civilization.cli import main as runtime_main
    except ImportError:
        raise SystemExit(_ABSENT) from None

    return runtime_main()


if __name__ == "__main__":
    raise SystemExit(main())
