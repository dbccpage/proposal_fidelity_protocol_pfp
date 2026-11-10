"""Read only frozen original files; record emitted source ranges without running them."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
PREFIX = "additional_operads_core_remaining"
scope = json.loads((HERE / (PREFIX + "_scope.json")).read_text(encoding="utf-8"))
allowed = {row["path"]: row for row in scope["files"]}
ledger_path = HERE / (PREFIX + "_read_ledger.json")
ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
for arg in sys.argv[1:]:
    path, *span = arg.split(":")
    assert path in allowed, path
    raw = (ROOT / path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == allowed[path]["sha256"], path
    lines = raw.decode("utf-8").splitlines()
    a, b = map(int, span[0].split("-")) if span else (1, len(lines))
    assert not lines or 1 <= a <= b <= len(lines)
    print("FILE", path, "SHA256", digest, "RANGE", a, b, "TOTAL", len(lines))
    for n in range(a, b + 1):
        print(f"{n}: {lines[n-1]}")
    ledger.append({"path": path, "sha256": digest, "reviewed_lines": [[a, b]] if lines else [], "full_source_read": not span, "method": "complete_text_emitted" if not span else "source_range_emitted"})
ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
