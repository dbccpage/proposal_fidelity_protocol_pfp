"""StructureBench reads Adversary's payload-nested DDA steps and never counts a
vacuous or unreached constraint as decided.

Two defects:

* C3 read ``phi_1`` / ``gamma_2`` only at the top level of the terminal
  ``dda_actions.jsonl`` line. The Adversary emitter
  (``adversary/use_cases/persistence.py``) writes each step as
  ``{"parent_sha256", "payload": {...}, "record_sha256", "sequence"}`` with
  those fields under ``payload``, so a genuine PASS_TO_MASTER bout could never
  be decided.
* Constraints that were not evaluated -- a non-PASS verdict, no actions, absent
  files or keys -- were reported ``SATISFIED`` and counted as decided.

The fixtures below write bundles in the emitter's shape by hand; no Adversary code
runs.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from operads.structurebench import (
    CONSTRAINT_IDS,
    ConstraintOutcome,
    ConstraintResult,
    StructureBenchEvaluator,
    StructureBenchReport,
    audit_gate_incidence,
)

TIMESTAMPS = ("2026-09-29T10:00:00Z", "2026-09-29T10:00:01Z")
_ACTS = ("I", "II", "III", "IV", "V", "VI", "VII")


def _dda_line(sequence: int, parent: str | None, payload: dict[str, Any], **top: Any) -> tuple[str, str]:
    """One record exactly as persistence.py writes it (plus optional top-level extras)."""
    sorted_payload = {k: payload[k] for k in sorted(payload, key=lambda s: s.encode("utf-8"))}
    material = json.dumps(
        {"sequence": sequence, "parent_sha256": parent, "payload": sorted_payload},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    record_sha256 = hashlib.sha256(material).hexdigest()
    record: dict[str, Any] = {
        "sequence": sequence,
        "parent_sha256": parent,
        "payload": sorted_payload,
        "record_sha256": record_sha256,
    }
    if "timestamp" in sorted_payload:
        record["timestamp"] = sorted_payload["timestamp"]
    record.update(top)
    return json.dumps(record, sort_keys=True), record_sha256


def _step_payload(timestamp: str | None, **fields: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "after_class": "closed",
        "authority_effect": "None",
        "before_class": "open",
        "carrier_hash": "c" * 64,
        "letter": "T",
        "receipt_sha256": "r" * 64,
        "witness_hash": None,
    }
    if timestamp is not None:
        payload["timestamp"] = timestamp
    payload.update(fields)
    return payload


def _write_bundle(
    root: Path,
    *,
    verdict: str | None = "PASS_TO_MASTER",
    terminal_fields: dict[str, Any] | None = None,
    terminal_top: dict[str, Any] | None = None,
    lean4_proof_hash: str | None = "a" * 64,
    dda_text: str | None = None,
    selected_candidate_id: str | None = "cand_1",
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    novella = []
    for act in _ACTS:
        novella.append(f"# Act {act}: scene")
        novella.append(f"turn at {TIMESTAMPS[0]} and {TIMESTAMPS[1]}")
    (root / "novella.md").write_text("\n".join(novella) + "\n", encoding="utf-8")

    if dda_text is None:
        first, head = _dda_line(0, None, _step_payload(TIMESTAMPS[0], phi_1="1", gamma_2="1"))
        fields = {"phi_1": "0", "gamma_2": "0"} if terminal_fields is None else terminal_fields
        last, _ = _dda_line(1, head, _step_payload(TIMESTAMPS[1], **fields), **(terminal_top or {}))
        dda_text = first + "\n" + last + "\n"
    (root / "dda_actions.jsonl").write_text(dda_text, encoding="utf-8")

    keys: dict[str, Any] = {"receipt_id": "receipt_1", "task_key": "task_1"}
    if selected_candidate_id is not None:
        keys["selected_candidate_id"] = selected_candidate_id
    summary = dict(keys)
    if verdict is not None:
        summary["terminal_verdict"] = verdict
    (root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = dict(keys)
    for name in ("novella.md", "dda_actions.jsonl", "summary.json"):
        receipt[f"{name.split('.')[0]}_sha256"] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if lean4_proof_hash is not None:
        receipt["lean4_proof_hash"] = lean4_proof_hash
    (root / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return root


def _outcome(report: StructureBenchReport, constraint_id: str) -> ConstraintResult:
    return next(r for r in report.results if r.constraint_id == constraint_id)


# -- C3 reads the payload -------------------------------------------------


def test_a_adversary_shaped_pass_to_master_bundle_is_decided_and_clean(tmp_path: Path) -> None:
    """Counterexample: phi_1 and gamma_2 under `payload` were reported unreachable."""
    report = StructureBenchEvaluator(_write_bundle(tmp_path / "b")).evaluate()

    c3 = _outcome(report, "C3_PASS_TO_MASTER_OBLIGATIONS")
    assert c3.outcome is ConstraintOutcome.SATISFIED, c3.detail
    assert report.coverage() == (11, 11)
    assert report.is_clean(), report.render()


def test_a_payload_nested_nonzero_terminal_step_is_violated(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "b", terminal_fields={"phi_1": "1/2", "gamma_2": "0"})
    c3 = StructureBenchEvaluator(bundle)._c3_pass_to_master()
    assert c3.outcome is ConstraintOutcome.VIOLATED
    assert "payload phi_1='1/2'" in c3.detail


def test_top_level_and_payload_that_disagree_are_unmet(tmp_path: Path) -> None:
    bundle = _write_bundle(
        tmp_path / "b",
        terminal_fields={"phi_1": "1", "gamma_2": "0"},
        terminal_top={"phi_1": 0, "gamma_2": 0},
    )
    c3 = StructureBenchEvaluator(bundle)._c3_pass_to_master()
    assert c3.outcome is ConstraintOutcome.VIOLATED
    assert "disagrees on phi_1" in c3.detail


def test_top_level_and_payload_that_agree_are_satisfied(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "b", terminal_top={"phi_1": 0, "gamma_2": "0"})
    c3 = StructureBenchEvaluator(bundle)._c3_pass_to_master()
    assert c3.outcome is ConstraintOutcome.SATISFIED, c3.detail


def test_a_boolean_or_float_zero_under_payload_is_not_exact(tmp_path: Path) -> None:
    for name, fields in (
        ("bool", {"phi_1": "0", "gamma_2": False}),
        ("float", {"phi_1": 0.0, "gamma_2": "0"}),
    ):
        bundle = _write_bundle(tmp_path / name, terminal_fields=fields)
        c3 = StructureBenchEvaluator(bundle)._c3_pass_to_master()
        assert c3.outcome is ConstraintOutcome.VIOLATED, (name, c3.detail)


# -- nothing absent or vacuous is decided ---------------------------------


def test_a_bundle_with_every_c3_field_absent_is_not_decided(tmp_path: Path) -> None:
    """No terminal verdict, no phi_1/gamma_2 anywhere, no lean4_proof_hash."""
    bundle = _write_bundle(
        tmp_path / "b", verdict=None, terminal_fields={}, lean4_proof_hash=None
    )
    report = StructureBenchEvaluator(bundle).evaluate()

    c3 = _outcome(report, "C3_PASS_TO_MASTER_OBLIGATIONS")
    assert c3.outcome is ConstraintOutcome.UNVERIFIABLE
    assert report.coverage()[0] == 10
    assert not report.is_clean()


def test_pass_to_master_with_phi_and_gamma_absent_everywhere_is_unverifiable(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "b", terminal_fields={})
    c3 = StructureBenchEvaluator(bundle)._c3_pass_to_master()
    assert c3.outcome is ConstraintOutcome.UNVERIFIABLE
    assert "`phi_1`" in c3.detail and "`gamma_2`" in c3.detail


def test_a_non_pass_verdict_is_not_applicable_and_not_counted(tmp_path: Path) -> None:
    """Counterexample: a COMPOSTED bout with no C3 evidence was a decided SATISFIED."""
    bundle = _write_bundle(
        tmp_path / "b", verdict="COMPOSTED", terminal_fields={}, lean4_proof_hash=None
    )
    report = StructureBenchEvaluator(bundle).evaluate()

    c3 = _outcome(report, "C3_PASS_TO_MASTER_OBLIGATIONS")
    assert c3.outcome is ConstraintOutcome.NOT_APPLICABLE
    assert report.coverage() == (10, 11)
    assert c3 not in report.by_outcome(ConstraintOutcome.SATISFIED)
    assert not report.is_clean()
    assert "not applicable     : 1" in report.render()


def test_a_bundle_with_no_actions_decides_neither_action_constraint(tmp_path: Path) -> None:
    report = StructureBenchEvaluator(_write_bundle(tmp_path / "b", dda_text="")).evaluate()

    for constraint_id in ("C1_JSONL_ONE_OBJECT_PER_LINE", "C2_NOVELLA_ACTION_BIJECTION"):
        assert _outcome(report, constraint_id).outcome is ConstraintOutcome.NOT_APPLICABLE
    assert _outcome(report, "C3_PASS_TO_MASTER_OBLIGATIONS").outcome is ConstraintOutcome.VIOLATED


def test_actions_without_timestamps_are_not_silently_skipped(tmp_path: Path) -> None:
    first, head = _dda_line(0, None, _step_payload(TIMESTAMPS[0], phi_1="1", gamma_2="1"))
    last, _ = _dda_line(1, head, _step_payload(None, phi_1="0", gamma_2="0"))
    bundle = _write_bundle(tmp_path / "b", dda_text=first + "\n" + last + "\n")

    result = StructureBenchEvaluator(bundle)._c2_novella_action_bijection()

    assert result.outcome is ConstraintOutcome.UNVERIFIABLE
    assert "1 of 2 action lines" in result.detail


def test_absent_files_leave_encoding_and_key_order_unverified(tmp_path: Path) -> None:
    """With three of four files missing, 'every artifact is UTF-8' was a vacuous pass."""
    bundle = tmp_path / "b"
    bundle.mkdir()
    (bundle / "receipt.json").write_text('{"a": 1}\n', encoding="utf-8")

    report = StructureBenchEvaluator(bundle).evaluate()

    assert _outcome(report, "C1_UTF8_NO_BOM").outcome is ConstraintOutcome.UNVERIFIABLE
    assert _outcome(report, "C1_JSON_KEYS_SORTED").outcome is ConstraintOutcome.UNVERIFIABLE


def test_a_bijection_key_in_neither_document_is_not_checked(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "b", selected_candidate_id=None)
    result = StructureBenchEvaluator(bundle)._c2_bijection()
    assert result.outcome is ConstraintOutcome.UNVERIFIABLE
    assert "selected_candidate_id" in result.detail


# -- the tallies ----------------------------------------------------------


def _report(outcomes: dict[str, ConstraintOutcome]) -> StructureBenchReport:
    return StructureBenchReport(
        results=tuple(
            ConstraintResult(cid, outcomes.get(cid, ConstraintOutcome.SATISFIED), f"{cid} fixture")
            for cid in CONSTRAINT_IDS
        )
    )


def test_coverage_counts_only_satisfied_and_violated() -> None:
    report = _report(
        {
            "C1_UTF8_NO_BOM": ConstraintOutcome.VIOLATED,
            "C2_HASH_BINDING": ConstraintOutcome.UNVERIFIABLE,
            "C3_PASS_TO_MASTER_OBLIGATIONS": ConstraintOutcome.NOT_APPLICABLE,
        }
    )
    assert report.coverage() == (9, 11)


class _RecordingHost:
    def __init__(self) -> None:
        self.q_matrix: list[list[str]] | None = None

    def lggr_soundness(self, d_matrix, q_matrix):
        self.q_matrix = q_matrix

        class _Outcome:
            is_ok = True

            @staticmethod
            def unwrap():
                return {"result": {"sound": True, "d_rank": 3, "qd_rank": 3, "witness": None}}

        return _Outcome()


def test_the_gate_incidence_projector_observes_only_decided_gates() -> None:
    report = _report(
        {
            "C2_HASH_BINDING": ConstraintOutcome.UNVERIFIABLE,
            "C3_PASS_TO_MASTER_OBLIGATIONS": ConstraintOutcome.NOT_APPLICABLE,
            "C1_UTF8_NO_BOM": ConstraintOutcome.VIOLATED,
        }
    )
    host = _RecordingHost()
    audit_gate_incidence(report, host=host)

    assert host.q_matrix is not None
    diagonal = {cid: host.q_matrix[i][i] for i, cid in enumerate(CONSTRAINT_IDS)}
    assert diagonal["C2_HASH_BINDING"] == "0"
    assert diagonal["C3_PASS_TO_MASTER_OBLIGATIONS"] == "0"
    assert diagonal["C1_UTF8_NO_BOM"] == "1"
    assert sum(1 for value in diagonal.values() if value == "1") == 9
