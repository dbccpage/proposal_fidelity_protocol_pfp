"""Pre-flight one generated checker-input bundle against a draft checker.

    python tools/preflight_draft.py <records root> <L###> <checker.py>

Prints one row per disagreement and exits 1 when there is any.  A draft
checker is never the replay of record.

AuthorityEffect: None
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.canon import load_path, sha256_tag  # noqa: E402
from engine.preflight import CheckerPin, preflight  # noqa: E402


def main(argv: list[str]) -> int:
    root, level, checker = Path(argv[0]), argv[1], Path(argv[2])
    doc = load_path(root / "bindings" / "generated" / "checker_input" / f"{level}.json")
    assert isinstance(doc, dict)
    out = preflight(doc, CheckerPin(checker, sha256_tag(checker.read_bytes())))
    rows = out["rows"]
    assert isinstance(rows, list)
    for r in rows:
        print(r)
    print(f"target {out['target']}")
    return 1 if rows else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
