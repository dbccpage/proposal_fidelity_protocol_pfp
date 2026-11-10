"""Verify this retained evidence inventory and bytes without network access."""

import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    actual = {
        path.relative_to(root).as_posix(): {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path != root / "manifest.json" and "__pycache__" not in path.parts
    }
    if actual != manifest["files"]:
        raise ValueError("EVIDENCE_INVENTORY_OR_BYTES_CHANGED")
    print(json.dumps({"verified_files": len(actual), "network_calls": 0}))


if __name__ == "__main__":
    main()
