"""Read-only triage helper; writes only its own evidence ledger when requested."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "pilots/anomalon_woland"
LEDGER = Path(__file__).with_name("numbered_000_050_reads.json")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="*")
    p.add_argument("--primary", nargs=2, type=int)
    p.add_argument("--range", nargs=2, type=int)
    args = p.parse_args()
    paths = [ROOT / x for x in args.paths]
    if args.primary:
        for i in range(args.primary[0], args.primary[1] + 1):
            paths.extend(x for x in (BASE / f"pilot_{i:07d}").iterdir() if x.name in ("README.md", "spec.yaml"))
    prior = json.loads(LEDGER.read_text()) if LEDGER.exists() else []
    for path in paths:
        if "seed" in path.name.lower() or "private" in path.name.lower():
            raise ValueError("Protected or seed-named paths are excluded")
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        rel = path.relative_to(ROOT).as_posix()
        print(f"\nFILE {rel} SHA256 {digest(path)} LINES {len(lines)}")
        bounds = args.range or [1, len(lines)]
        for n, line in enumerate(lines, 1):
            if bounds[0] <= n <= bounds[1]:
                print(f"{n}: {line}")
        entry = {"path": rel, "lines": bounds, "sha256": digest(path), "review_level": "selected_text_emitted_for_review" if args.range else "full_text_emitted_for_review"}
        prior = [x for x in prior if not (x["path"] == rel and x["lines"] == bounds)] + [entry]
    LEDGER.write_text(json.dumps(prior, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
