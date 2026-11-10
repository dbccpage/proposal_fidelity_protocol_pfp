"""Validate only this audit's receipts and frozen source custody; no source imports."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
PREFIX = "additional_operads_core_remaining"


def load(suffix):
    return json.loads((HERE / (PREFIX + suffix)).read_text(encoding="utf-8"))


scope = load("_scope.json")
report = load(".json")
rows = {row["path"]: row for row in scope["files"]}
reviews = {row["path"]: row for row in report["file_reviews"]}
assert len(rows) == len(reviews) == 534
assert set(rows) == set(reviews)
assert report["status"] == "completed" and report["pending_paths"] == []
read = {}
for entry in load("_read_ledger.json"):
    if entry.get("output_truncated"):
        continue
    assert entry["sha256"] == rows[entry["path"]]["sha256"]
    read.setdefault(entry["path"], set()).update(
        line for start, end in entry["reviewed_lines"] for line in range(start, end + 1)
    )

for path, row in rows.items():
    body = (ROOT / path).read_bytes()
    assert hashlib.sha256(body).hexdigest() == row["sha256"] == reviews[path]["sha256"], path
    assert len(body.decode("utf-8").splitlines()) == row["lines"], path
    review = reviews[path]
    assert review["source_line_count"] == row["lines"] and review["assessment"].strip()
    if review["full_source_read"]:
        assert read.get(path) == set(range(1, row["lines"] + 1)), path
        assert review["reviewed_lines"] == ([[1, row["lines"]]] if row["lines"] else [])
        assert review["parsed_value_read"] is False
    else:
        assert path.endswith(".json") and review["reviewed_lines"] == []
        assert review["parsed_value_read"] is True
        assert review["review_level"] == "bounded_automated_parsed_artifact_review"

for section in ("claims", "findings"):
    for item in report[section]:
        for pin in item["source_evidence"]:
            assert pin["path"] in rows
            assert pin["sha256"] == rows[pin["path"]]["sha256"]
            assert reviews[pin["path"]]["full_source_read"] is True
            assert all(1 <= start <= end <= rows[pin["path"]]["lines"] for start, end in pin["lines"])
ids = [item["id"] for section in ("claims", "findings") for item in report[section]]
assert len(ids) == len(set(ids)) == 27
probes = load("_probes.json")
assert len(probes["probes"]) == 13
assert all(item["status"] == "counterexample_confirmed" for item in probes["probes"])
assert probes["counts"]["full_suites_run"] == 0
for pin in probes["sources"]:
    assert pin["sha256"] == rows[pin["path"]]["sha256"]
    assert reviews[pin["path"]]["full_source_read"] is True
    assert all(1 <= start <= end <= rows[pin["path"]]["lines"] for start, end in pin["lines"])
probe_ids = {item["id"] for item in probes["probes"]}
assert all(set(item.get("probe_ids", [])) <= probe_ids for item in report["findings"])
artifacts = load("_artifacts.json")
assert len(artifacts["summary"]["checks"]) == 16
assert all(value is True for value in artifacts["summary"]["checks"].values())

# Exact helper/receipt pointers are custody only, not additional semantic reads.
def validate_local_pins(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value and value["path"].startswith("dag/reviews/" + PREFIX):
            assert hashlib.sha256((ROOT / value["path"]).read_bytes()).hexdigest() == value["sha256"]
        for child in value.values():
            validate_local_pins(child)
    elif isinstance(value, list):
        for child in value:
            validate_local_pins(child)


validate_local_pins(report)
full = [item for item in reviews.values() if item["full_source_read"]]
bounded = [item for item in reviews.values() if not item["full_source_read"]]
assert len(full) == 530 and len(bounded) == 4
assert sum(item["source_line_count"] for item in full) == 81046
assert sum(item["source_line_count"] for item in bounded) == 5656
result = {
    "status": "passed",
    "method": "Stdlib metadata/hash/range verification only; no source imports or production effects.",
    "report_sha256": hashlib.sha256((HERE / (PREFIX + ".json")).read_bytes()).hexdigest(),
    "markdown_sha256": hashlib.sha256((HERE / (PREFIX + ".md")).read_bytes()).hexdigest(),
    "frozen_source_paths_unchanged": len(rows),
    "all_full_body_ranges_covered_by_nontruncated_read_receipts": True,
    "all_claim_finding_probe_source_pins_valid": True,
    "all_report_local_artifact_pins_valid": True,
    "summary": report["summary"],
    "file_extensions": dict(sorted(Counter(Path(path).suffix for path in rows).items())),
    "limits": "Receipt validation is not a new source execution, theorem proof, external-resource validation or full catalog prose reading.",
}
(HERE / (PREFIX + "_validation.json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
