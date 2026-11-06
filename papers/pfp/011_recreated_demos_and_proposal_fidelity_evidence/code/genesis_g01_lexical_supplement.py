"""Separate lexical-policy supplement; does not modify closed G01 evidence."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
AREA = PAPER / "docs/history_recovery/g01/lexical_guard_supplement_v1"


def violations(source: str) -> list[str]:
    """Scan raw source, including comments, for the original forbidden constructs.

    The conservative axiom word scan deliberately also refuses axiom mentions;
    this supplement admits no comment/string exception to the original policy.
    Kernel theorem/type/axiom audits remain distinct obligations.
    """
    found = sorted(set(re.findall(r"\b(?:sorry|admit|unsafe|partial|axiom)\b", source)))
    if re.search(r"(?m)^\s*import\s+Mathlib(?:\.|\s|$)", source):
        found.append("outside-core-import")
    return found


def run() -> dict:
    AREA.mkdir(parents=True, exist_ok=False)
    package = PAPER / "code/native_genesis_g01"
    candidates = {
        "axiom_line_comment": b"-- axiom fabricated : True\n",
        "axiom_block_comment": b"/- axiom fabricated : True -/\n",
        "axiom_nested_comment": b"/- outer /- axiom fabricated : True -/ outer -/\n",
        "sorry_comment": b"-- sorry\n",
        "partial_comment": b"/- partial def forged := 1 -/\n",
        "valid_ResearchG01": (package / "ResearchG01.lean").read_bytes(),
        "valid_Targets": (package / "G01Targets.lean").read_bytes(),
        "valid_control": (package / "G01Mutation_theorem_run_v3_VALID_CONTROL.lean").read_bytes(),
    }
    rows = []
    for name, raw in candidates.items():
        path = AREA / (name + ".lean")
        path.write_bytes(raw)
        hits = violations(raw.decode("utf8"))
        expected = not name.startswith("valid_")
        if bool(hits) != expected:
            raise ValueError("LEXICAL_CONTROL_FAILURE:" + name)
        rows.append({"id": name, "path": path.relative_to(PAPER).as_posix(),
                     "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                     "hits": hits, "expected_rejection": expected, "control_passed": True})
    policy = PAPER / "docs/history_recovery/recovered_sources/g01_reading_f_nonuniqueness_lean.md"
    receipt = {"schema": "paper011.g01-lexical-supplement.v1", "AuthorityEffect": "None",
               "detector_path": Path(__file__).relative_to(PAPER).as_posix(),
               "detector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "policy_path": policy.relative_to(PAPER).as_posix(),
               "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
               "rows": rows, "controls_passed": len(rows), "provider_calls": 0,
               "scope": "Raw lexical supplement, including comment variants. No new Lean compilation or changed historical guard/receipt claim."}
    (AREA / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    return receipt


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
