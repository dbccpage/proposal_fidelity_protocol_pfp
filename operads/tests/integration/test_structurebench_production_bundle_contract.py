"""Actual native persistence -> evaluator evidence, with independent disk-byte oracles.

The proof-hash token below is a structural fixture, not a checked Lean proof.
This file invokes the existing host only through persist_bout_run_folder.
"""

import hashlib
import json

import pytest

from omega_engine_epistemic_immune_system.domain.pharmacy_catalog import PharmacyCatalogRepository
from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import (
    filesystem_catalog_bytes,
)
from omega_engine_woland.infrastructure.estates.oeeis_immune import OeeisImmuneAdapter
from omega_engine_woland.use_cases.persistence import (
    persist_bout_run_folder, persist_bout_run_folder_historical,
)
from omega_engine_operads.structurebench import (
    ConstraintOutcome,
    StructureBenchEvaluator,
)

TIMESTAMPS = ("2026-10-10T00:00:00Z", "2026-10-10T00:00:01Z")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pretty(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def independent_tape(steps):
    """Mirror the published byte format without production/native tape helpers."""
    lines = []
    parent = None
    for sequence, payload in enumerate(steps):
        material = {"sequence": sequence, "parent_sha256": parent, "payload": payload}
        parent = digest(
            json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
                "utf-8"
            )
        )
        record = dict(material, record_sha256=parent)
        if "timestamp" in payload:
            record["timestamp"] = payload["timestamp"]
        lines.append(json.dumps(record, sort_keys=True, ensure_ascii=True).encode("utf-8") + b"\n")
    return b"".join(lines), parent


def persist(root, run_key, *, candidate_id=None, missing=None, phi="0", verdict="PASS_TO_MASTER", historical=False):
    """One finite structural challenge: terminal exact zeros with seven scenes."""
    candidate_id = candidate_id or "candidate:" + run_key
    summary = {
        "task_key": "task:" + run_key,
        "selected_candidate_id": candidate_id,
        "terminal_verdict": verdict,
    }
    if missing == "terminal_verdict":
        del summary["terminal_verdict"]
    steps = [
        {"timestamp": TIMESTAMPS[0], "gamma_2": "1", "phi_1": "1", "after_class": "open"},
        {"timestamp": TIMESTAMPS[1], "gamma_2": "0", "phi_1": phi, "after_class": "closed"},
    ]
    if missing in {"phi_1", "gamma_2"}:
        del steps[-1][missing]
    novella = "".join(
        f"# Act {act}: scene\nturn at {TIMESTAMPS[0]} and {TIMESTAMPS[1]}\n"
        for act in ("I", "II", "III", "IV", "V", "VI", "VII")
    )
    tape, head = independent_tape(steps)
    receipt = {key: summary[key] for key in ("task_key", "selected_candidate_id")}
    if historical:
        material = {"schema": "omega.woland.bout-receipt-id.v1", "dda_actions_sha256": digest(tape),
                    "novella_sha256": digest(novella.encode("utf-8")), "summary_core_sha256": digest(pretty(summary))}
        identity = "sha256:" + digest(json.dumps(material, sort_keys=True, separators=(",", ":")).encode())
        summary["receipt_id"] = receipt["receipt_id"] = identity
    if missing != "lean4_proof_hash":
        receipt["lean4_proof_hash"] = digest(b"syntactic proof-hash fixture; Lean kernel not run")
    writer = persist_bout_run_folder_historical if historical else persist_bout_run_folder
    result = writer(root, run_key, receipt, novella, steps, summary)
    assert result.is_ok, result.unwrap_err() if result.is_err else None
    run = result.unwrap()
    assert (run / "ddc.jsonl").read_bytes() == tape
    narrative_name = "novella.md" if historical else "uns.md"
    head_name = "dda_head_sha256" if historical else "ddc_head_sha256"
    names = ("novella.md", "dda_actions.jsonl", "ddc.jsonl", "summary.json") if historical else ("uns.md", "uts.jsonl", "ddc.jsonl", "summary.json")
    if historical:
        assert (run / "dda_actions.jsonl").read_bytes() == tape
    else:
        assert not list(run.glob("dda*"))
        summary["bundle_schema_version"] = "omega.woland.reported-run-bundle.v2"
        material = {"schema": "omega.woland.bout-receipt-id.v3", "ddc_sha256": digest(tape),
                    "uns_sha256": digest(novella.encode("utf-8")),
                    "summary_core_sha256": digest(pretty(summary)),
                    "uts_sha256": digest((run / "uts.jsonl").read_bytes())}
        summary["receipt_id"] = "sha256:" + digest(json.dumps(material, sort_keys=True, separators=(",", ":")).encode())
    assert (run / narrative_name).read_bytes() == novella.encode("utf-8")
    assert (run / "summary.json").read_bytes() == pretty(summary)
    emitted = json.loads((run / "receipt.json").read_text(encoding="utf-8"))
    assert emitted["receipt_id"] == summary["receipt_id"]
    assert emitted["selected_candidate_id"] == candidate_id
    assert emitted[head_name] == head
    assert emitted["ddc_trace_hash"] == "sha256:" + digest(tape)
    for filename in names:
        assert emitted[filename.split(".")[0] + "_sha256"] == digest((run / filename).read_bytes())
    return run


def outcome(report, constraint):
    return next(result for result in report.results if result.constraint_id == constraint)


def test_actual_native_persistence_is_fully_measured_and_hash_bound(tmp_path):
    run = persist(tmp_path, "measured")
    report = StructureBenchEvaluator.evaluate_run_folder(run)
    assert report.coverage() == (11, 11)
    assert report.is_clean(), report.render()
    assert outcome(report, "C2_HASH_BINDING").outcome is ConstraintOutcome.SATISFIED
    assert "4 declared artifacts" in outcome(report, "C2_HASH_BINDING").detail


@pytest.mark.parametrize("missing", ["phi_1", "gamma_2", "lean4_proof_hash", "terminal_verdict"])
def test_native_persisted_missing_terminal_binding_is_held_not_satisfied(tmp_path, missing):
    run = persist(tmp_path, "held-" + missing, missing=missing)
    report = StructureBenchEvaluator.evaluate_run_folder(run)
    assert (
        outcome(report, "C3_PASS_TO_MASTER_OBLIGATIONS").outcome is ConstraintOutcome.UNVERIFIABLE
    )
    assert report.coverage() == (10, 11)
    assert not report.is_clean()
    recovery = persist(tmp_path, "recovered-" + missing)
    assert StructureBenchEvaluator.evaluate_run_folder(recovery).is_clean()


def test_native_non_pass_verdict_remains_not_applicable(tmp_path):
    report = StructureBenchEvaluator.evaluate_run_folder(
        persist(tmp_path, "refused", verdict="REFUSED")
    )
    assert (
        outcome(report, "C3_PASS_TO_MASTER_OBLIGATIONS").outcome is ConstraintOutcome.NOT_APPLICABLE
    )
    assert report.coverage() == (10, 11)
    assert not report.is_clean()


def test_cross_run_receipt_transplant_cannot_bind_another_candidate(tmp_path):
    first = persist(tmp_path, "run-a", candidate_id="candidate:a")
    second = persist(tmp_path, "run-b", candidate_id="candidate:b")
    original = (second / "receipt.json").read_bytes()
    (second / "receipt.json").write_bytes((first / "receipt.json").read_bytes())
    report = StructureBenchEvaluator.evaluate_run_folder(second)
    assert outcome(report, "C2_RECEIPT_SUMMARY_BIJECTION").outcome is ConstraintOutcome.VIOLATED
    assert outcome(report, "C2_HASH_BINDING").outcome is ConstraintOutcome.VIOLATED
    assert not report.is_clean()
    (second / "receipt.json").write_bytes(original)
    assert StructureBenchEvaluator.evaluate_run_folder(second).is_clean()
    recovery = persist(tmp_path, "run-b-recovery", candidate_id="candidate:b")
    assert StructureBenchEvaluator.evaluate_run_folder(recovery).is_clean()


@pytest.mark.parametrize(
    "breakage", ["missing", "changed_bytes", "changed_uts_bytes"]
)
def test_native_single_ddc_and_uts_are_required_and_bound(tmp_path, breakage):
    run = persist(tmp_path, "ddc-control")
    path = run / "ddc.jsonl"
    original = path.read_bytes()
    receipt_path = run / "receipt.json"
    original_receipt = receipt_path.read_bytes()
    if breakage == "missing":
        path.unlink()
    elif breakage == "changed_uts_bytes":
        path = run / "uts.jsonl"
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
    else:
        path.write_bytes(original + b"\n")

    report = StructureBenchEvaluator.evaluate_run_folder(run)
    assert outcome(report, "C2_HASH_BINDING").outcome is ConstraintOutcome.VIOLATED
    assert not report.is_clean()
    path.write_bytes(original)
    receipt_path.write_bytes(original_receipt)
    assert StructureBenchEvaluator.evaluate_run_folder(run).is_clean()


def test_native_duplicate_terminal_token_is_malformed_not_satisfied(tmp_path):
    run = persist(tmp_path, "duplicate-terminal")
    tape = run / "ddc.jsonl"
    original = tape.read_bytes()
    assert original.count(b'"phi_1": "0"') == 1
    tape.write_bytes(original.replace(b'"phi_1": "0"', b'"phi_1": "1", "phi_1": "0"'))
    report = StructureBenchEvaluator.evaluate_run_folder(run)
    assert outcome(report, "C1_JSONL_ONE_OBJECT_PER_LINE").outcome is ConstraintOutcome.VIOLATED
    assert outcome(report, "C3_PASS_TO_MASTER_OBLIGATIONS").outcome is ConstraintOutcome.VIOLATED
    assert not report.is_clean()
    tape.write_bytes(original)
    assert StructureBenchEvaluator.evaluate_run_folder(run).is_clean()


def test_observed_failure_feedback_stays_candidate_and_correlates_to_source_run(tmp_path):
    run = persist(tmp_path / "runs", "failed-candidate", phi="1")
    report = StructureBenchEvaluator.evaluate_run_folder(run)
    failed = outcome(report, "C3_PASS_TO_MASTER_OBLIGATIONS")
    assert failed.outcome is ConstraintOutcome.VIOLATED
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    defect = f"STRUCTUREBENCH {summary['selected_candidate_id']}: {failed.constraint_id}: {failed.detail}"
    immune_root = tmp_path / "immune"
    adapter = OeeisImmuneAdapter(immune_root)
    recorded = adapter.record_candidates((defect,), run_id=run.name, task_id=summary["task_key"])
    assert recorded.is_ok
    assert len(recorded.unwrap()) == 1
    antibody_id = recorded.unwrap()[0]
    catalog_path = PharmacyCatalogRepository.catalog_path(
        immune_root, filesystem_catalog_bytes
    )
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert catalog["last_mined_run_id"] == run.name
    assert catalog["last_mined_task_id"] == summary["task_key"]
    entry = catalog["antibodies"][antibody_id]
    assert entry["target_pattern"] == defect
    assert entry["pharmacy_status"] == "candidate"
    assert entry["authority_effect"] == "None"
    expected_evidence = digest(
        f"{antibody_id}:{defect}:{run.name}:{summary['task_key']}".encode("utf-8")
    )
    assert entry["evidence_sha256"] == expected_evidence
    candidate_path = (
        immune_root
        / "_ic"
        / "nara"
        / "_archive"
        / "telemetry"
        / "antibodies"
        / (antibody_id + ".json")
    )
    assert json.loads(candidate_path.read_text(encoding="utf-8")) == entry
    assert adapter.admitted_guidance().unwrap().lines == ()

    healthy_run = persist(tmp_path / "runs", "healthy-candidate")
    assert StructureBenchEvaluator.evaluate_run_folder(healthy_run).is_clean()
    original_catalog = catalog_path.read_bytes()
    assert (
        adapter.record_candidates((), run_id=healthy_run.name, task_id="healthy-task").unwrap()
        == ()
    )
    assert catalog_path.read_bytes() == original_catalog
    assert adapter.admitted_guidance().unwrap().lines == ()


def test_historical_ddc_copy_with_matching_changed_digest_still_refuses(tmp_path):
    run = persist(tmp_path, "historical-copy-control", historical=True)
    copy = run / "ddc.jsonl"
    copy.write_bytes(copy.read_bytes() + b"\n")
    receipt_file = run / "receipt.json"
    receipt = json.loads(receipt_file.read_bytes())
    receipt["ddc_sha256"] = digest(copy.read_bytes())
    receipt_file.write_bytes(pretty(receipt))
    report = StructureBenchEvaluator.evaluate_run_folder(run)
    assert outcome(report, "C2_HASH_BINDING").outcome is ConstraintOutcome.VIOLATED
