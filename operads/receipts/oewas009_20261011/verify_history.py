"""Read-only byte verification of all migrated originals and frozen NARA copies."""

import hashlib
import json
from pathlib import Path

root = Path.cwd()
base = Path(__file__).resolve().parent
inventory_path = root / "_ic/odni/migrations/oewas007/inventory.json"
inventory = json.loads(inventory_path.read_bytes())
failures = []
comparisons = 0
for row in inventory["files"]:
    paths = [
        row["destination"],
        "_ic/nara/historical/oewas007/" + row["source"].removeprefix("_intelligence/"),
    ]
    for relative in paths:
        path = root / relative
        comparisons += 1
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != row["sha256"]:
            failures.append({"path": relative, "expected": row["sha256"], "actual": actual})
record = {
    "schema_version": "core.oewas009.historical-byte-check.v1",
    "inventory_sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
    "source_revision": inventory["source_revision"],
    "source_file_count": len(inventory["files"]),
    "comparisons": comparisons,
    "mismatches": failures,
    "authority_effect": "None",
}
(base / "historical_bytes.json").write_text(
    json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n"
)
print(json.dumps({"comparisons": comparisons, "mismatches": len(failures)}))
raise SystemExit(bool(failures))
