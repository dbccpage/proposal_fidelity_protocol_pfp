#!/usr/bin/env python3
"""Run the Examiner capstone: exact recount and controls on retained records."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from review_counts import recount  # noqa: E402


def main() -> int:
    directory = ROOT / "docs/historical_evidence"
    provenance = json.loads((directory / "provenance.json").read_text())
    for entry in provenance["records"]:
        data = (directory / entry["file"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("retained record digest mismatch: " + entry["file"])
    trace = directory / "demo2_r7_adversarial_debate_1790210039.jsonl"
    rows = [json.loads(line) for line in trace.read_text().splitlines() if line.strip()]
    expected = {(lattice, value) for lattice in ("c5_pentagon", "kagome_cluster")
                for value in (-4, -2, 0, 2, 4)}
    if len(rows) != 10 or {(r["lattice_key"], r["u_val"]) for r in rows} != expected:
        raise ValueError("missing or duplicated trial condition")
    counts = recount(rows)
    changed = json.loads(json.dumps(rows))
    refused = next(row for row in changed if row["proposer_hallucination"])
    refused["adversary_critique"]["adversary_verdict"] = "CONCUR"
    if recount(changed) == counts:
        raise ValueError("changed-verdict control failed")
    changed_counts = recount(changed)
    for row in changed:
        row["adversary_caught_am"] = False
    if recount(changed) != changed_counts:
        raise ValueError("constant-flag control failed")
    gate = json.loads((directory / "adversary_gate_falsifiers.json").read_text())
    report = {
        "status": "PASS", "counts": asdict(counts),
        "exact_fractions": {key: str(value) if value is not None else None
                            for key, value in counts.rates().items()},
        "negative_controls": ["one changed CHALLENGE becomes CONCUR",
                              "constant caught flag does not change cells"],
        "gate_probe_records": len(gate["falsifiers"]),
        "gate_defect_families": len({row["defect"] for row in gate["falsifiers"]}),
        "scope": ("Fresh recount and controls on retained records; "
                  "no model, native checker, or gate replay"),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
