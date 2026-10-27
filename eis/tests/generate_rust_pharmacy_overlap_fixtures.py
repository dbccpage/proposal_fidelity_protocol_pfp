"""Freeze shared pharmacy projections before porting additional host checks.

This deliberately records a projection, not complete report equality: Python
and Rust differ in detail quoting, Unicode hashing and some input profiles.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from eis.infrastructure.mssn_pharmacy import (
    DetectionContext,
    detect,
)
from eis.infrastructure.native_pharmacy import NATIVE_CLASS_CODES
from pfp.infrastructure.adapters.mssn_scenarios.immune_fixtures import (
    NEGATIVE_FIXTURES,
    POSITIVE_FIXTURES,
)


def main():
    cases = [*POSITIVE_FIXTURES, *NEGATIVE_FIXTURES]
    for index, (candidate, context) in enumerate([
        ({"verified": True, "public_rationale": "x"}, DetectionContext()),
        ({"outer": {"inner": [{"verified": True}]}}, DetectionContext()),
        ({"receipt_hash": "sha256:" + "b" * 64}, DetectionContext()),
        ({"public_rationale": "by Squier's theorem the system is confluent"}, DetectionContext()),
        ({"public_rationale": "the search was exhaustive"}, DetectionContext(unexplored_branches=2)),
        ({"objections": [{"code": "X"}], "proposed_claim_deltas": ["fix"]}, DetectionContext()),
        ({"public_rationale": "runs in linear time and is optimal"}, DetectionContext()),
        ({"public_rationale": "<think>hidden</think>"}, DetectionContext()),
    ]):
        cases.append({"id": f"shared-extra-{index}", "candidate": candidate, "context": context})
    rows = []
    for case in cases:
        report = detect(case["candidate"], case["context"])
        context = dataclasses.asdict(case["context"])
        # The projection does not claim native support for Python persona roles.
        context.pop("granted_persona_roles", None)
        findings = sorted([
            {"code": finding.failure_class.value, "locus": finding.locus,
             "disposition": finding.disposition.value}
            for finding in report.findings
            if finding.failure_class.value in NATIVE_CLASS_CODES.values()
        ], key=lambda finding: (finding["code"], finding["locus"], finding["disposition"]))
        rows.append({"id": case["id"], "candidate": case["candidate"], "context": context,
            "expected": {"findings": findings, "subject_digest": report.subject_digest,
                "semantic_payload_digest": report.semantic_payload_digest}})
    path = Path(__file__).resolve().parents[2] / "engine/crates_rs/tests/core_prompt_civilization/fixtures/python_pharmacy_overlap_v1.json"
    path.write_text(json.dumps({"vectors": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen {len(rows)} shared pharmacy projection vectors from the Python oracle.")


if __name__ == "__main__":
    main()
