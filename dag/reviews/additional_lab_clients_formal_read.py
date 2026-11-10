"""Full-read/custody aid for the assigned original C#, Lab and Lean slice."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = json.loads((ROOT / "dag/file_inventory.json").read_text(encoding="utf-8"))
COVERAGE = json.loads((ROOT / "dag/reviews/coverage.json").read_text(encoding="utf-8"))
INDEX = {r["path"]: r for r in INVENTORY["files"]}
SCOPE = [r for r in COVERAGE["files"] if
         (r["path"].startswith("csharp/") or
          (r["path"].startswith(("pfp_lab/", "lean4/")) and r["substantive_status"] != "full_text_source_review_recorded"))]
OUT = Path(__file__).with_name("additional_lab_clients_formal_read_ledger.json")

def inspect(paths):
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    index = {r["path"]: r for r in previous}
    for path in paths:
        raw = (ROOT / path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == INDEX[path]["sha256"], path
        text = raw.decode("utf-8-sig")
        lines = text.split("\n")
        if lines and lines[-1] == "": lines.pop()
        print("FILE", path, "SHA256", digest, "PHYSICAL_LINES", len(lines))
        for n, line in enumerate(lines, 1): print(str(n) + ": " + line.rstrip("\r"))
        index[path] = {"path": path, "sha256": digest, "reviewed_lines": [1, len(lines)],
                       "emitted_complete_text": True, "full_source_read": False,
                       "assessment": "Full text emitted; semantic assessment must be explicitly supplied."}
    OUT.write_text(json.dumps(list(index.values()), indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        for r in SCOPE:
            raw = (ROOT / r["path"]).read_bytes()
            print(r["path"], len(raw), raw.count(b"\n") + int(bool(raw) and not raw.endswith(b"\n")))
        print("SCOPE_COUNT", len(SCOPE))
    else:
        inspect(sys.argv[1:])
