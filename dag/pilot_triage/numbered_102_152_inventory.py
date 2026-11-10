"""Filename-only resolution of capsule source citations using known inventories."""
from pathlib import Path
import json
import subprocess
from numbered_102_152_helper import ROOT, info

manifest = json.loads((ROOT / "dag/migrations/anomalon_pilots_move.json").read_text(encoding="utf-8"))
paths = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
paths += ["pilots/anomalon_woland/" + row["path"] for row in manifest["entries"]]
rows = []
for n in range(102, 153):
    meta = info(n)
    name = meta["source_markdown"].split("/")[-1]
    matches = sorted(set(path for path in paths if path.endswith("/" + name)))
    rows.append({"pilot": meta["pilot_id"], "citation": meta["source_markdown"], "same_filename_matches": matches})
print(json.dumps(rows, indent=2))
Path(__file__).with_name("numbered_102_152_citation_resolution.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
