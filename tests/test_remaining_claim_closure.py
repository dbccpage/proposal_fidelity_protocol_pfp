"""Host checks for the remaining ATL-P012 through ATL-P021 closure.

AuthorityEffect: None.

The Lean kernel print and the frozen Paper 013 replay are executed here.
The Rust checks stay in code/rust/pfp_operads and are executed by cargo.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_LEAN = _REPO / "lean4" / "RemainingClaimClosure.lean"
_REPLAY = (
    _REPO
    / "atlas"
    / "archive"
    / "pfp"
    / "013_pfp_task_bound_claims_and_hallucination_control"
    / "code"
    / "replay.py"
)
_REVIEW = _REPO / "dag" / "reviews" / "additional_remaining_claim_closure.json"
_MATCHED = (
    "ATL-P012-010",
    "ATL-P012-011",
    "ATL-P013-001",
    "ATL-P013-002",
    "ATL-P013-003",
    "ATL-P013-004",
    "ATL-P014-001",
    "ATL-P014-002",
    "ATL-P017-001",
    "ATL-P017-002",
    "ATL-P017-003",
    "ATL-P017-006",
    "ATL-P017-008",
    "ATL-P021-006",
)
_PARTIAL = (
    "ATL-P017-004",
    "ATL-P017-005",
    "ATL-P017-007",
    "ATL-P017-009",
    "ATL-P017-010",
    "ATL-P017-011",
    "ATL-P021-003",
)
_STILL_GAP = (
    "ATL-P012-012",
    "ATL-P014-005",
    "ATL-P017-013",
    "ATL-P020-001",
    "ATL-P020-012",
    "ATL-P021-004",
    "ATL-P021-008",
)


def _lake() -> str:
    home = Path.home() / ".elan" / "bin"
    for name in ("lake.exe", "lake"):
        candidate = home / name
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("lake")
    assert found, "lake executable not found"
    return found


def _matches() -> dict[str, dict]:
    rows = json.loads((_REPO / "atlas" / "atlas_claim_matches.json").read_text(encoding="utf-8"))
    return {row["atlas_id"]: row for row in rows["results"]}


def test_remaining_claim_lean_axioms_are_only_propext_and_quot_sound() -> None:
    source = _LEAN.read_text(encoding="utf-8")
    prints = [line for line in source.splitlines() if line.startswith("#print axioms ")]
    assert len(prints) == 30
    code_tokens = [
        tok
        for line in source.splitlines()
        if not line.strip().startswith(("--", "/-", "*"))
        for tok in line.split()
    ]
    assert "sorry" not in code_tokens
    res = subprocess.run(
        [_lake(), "+leanprover/lean4:v4.35.0", "--dir", "lean4", "env", "lean", str(_LEAN)],
        cwd=_REPO,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert res.returncode == 0, res.stderr + res.stdout
    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(lines) == 30
    for ln in lines:
        assert "sorryAx" not in ln
        assert "Classical.choice" not in ln
        if "depends on axioms:" in ln:
            ax_part = ln.split("depends on axioms:", 1)[1].strip().strip("[]")
            axioms = {a.strip() for a in ax_part.split(",") if a.strip()}
            assert axioms <= {"propext", "Quot.sound"}, ln
        else:
            assert "does not depend on any axioms" in ln


def test_frozen_paper_013_replay_exits_pass_with_zero_provider_calls() -> None:
    res = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(_REPLAY)],
        cwd=_REPLAY.parent,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 0, res.stderr + res.stdout
    payload = json.loads(res.stdout)
    assert payload["status"] == "PASS"
    assert payload["provider_calls"] == 0
    checks = payload["checks"]
    assert checks == {
        "valid_witness": True,
        "wrong_witness_refused": True,
        "wrong_task_refused": True,
        "false_prose_claim_refused": True,
        "unbound_quote_refused": True,
        "mandatory_task_claim_retained": True,
    }


def test_remaining_claim_verdicts_match_the_host_record() -> None:
    review = json.loads(_REVIEW.read_text(encoding="utf-8"))
    expected_ids = {atlas_id.replace("ATL-", "AUDIT-") for atlas_id in (*_MATCHED, *_PARTIAL)}
    assert {row["id"] for row in review["claims"]} == expected_ids
    assert len(review["claims"]) == len(expected_ids)
    rows = _matches()
    for atlas_id in _MATCHED:
        row = rows[atlas_id]
        audit_id = atlas_id.replace("ATL-", "AUDIT-")
        assert row["verdict"] == "matched"
        assert row["nodes"] == [audit_id]
        assert row["relation"] == "states_same_claim_as"
        assert row["proposed_derivation"] is None
        assert (_REPO / "dag" / "derivations" / f"{audit_id.lower().replace('-', '_')}.md").is_file()
        assert not (_REPO / "dag" / "derivations" / f"{atlas_id.lower().replace('-', '_')}.md").exists()
    for atlas_id in _PARTIAL:
        row = rows[atlas_id]
        audit_id = atlas_id.replace("ATL-", "AUDIT-")
        assert row["verdict"] == "partial"
        assert audit_id in row["nodes"]
        assert row["relation"] in {"narrows", "refutes"}
        assert (_REPO / "dag" / "derivations" / f"{audit_id.lower().replace('-', '_')}.md").is_file()
    untouched = rows["ATL-P017-012"]
    assert untouched["verdict"] == "partial"
    assert untouched["proposed_derivation"] is None
    assert untouched["nodes"] == ["PFP-C011-L1-CERTIFICATE", "PAPER008-FEASIBILITY-BEFORE-GAP"]
    assert rows["ATL-P021-003"]["relation"] == "refutes"
    assert rows["ATL-P021-003"]["proposed_derivation"] is None
    assert rows["ATL-P017-007"]["proposed_derivation"] is not None
    assert "PFPDOMAIN-CL26" in rows["ATL-P017-007"]["nodes"]
    for atlas_id in _STILL_GAP:
        assert rows[atlas_id]["verdict"] == "gap"
        assert rows[atlas_id]["nodes"] == []
    headings = (
        "## 1. What this record supports",
        "## 2. What it does not support",
        "## 3. Narrowest claim",
        "## 4. Negative or null controls",
    )
    for atlas_id in (*_MATCHED, *_PARTIAL):
        audit_id = atlas_id.replace("ATL-", "AUDIT-")
        text = (_REPO / "dag" / "derivations" / f"{audit_id.lower().replace('-', '_')}.md").read_text(
            encoding="utf-8"
        )
        for heading in headings:
            assert heading in text


def test_remaining_claim_atlas_check_is_current() -> None:
    res = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", "dag/build_atlas.py", "--check"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    payload = json.loads(res.stdout)
    assert payload["stale"] == []
    assert payload["ledger_rows"] == payload["derivation_nodes"]
    assert payload["ledger_rows"] >= 1546
