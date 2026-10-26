"""Strict decoder controls on legacy four-file bundles; no native host runs here.

The nonempty proof-hash fixture is structural metadata, not a checked Lean proof.
Native persistence integration is covered separately.
"""

import hashlib
import json

import pytest

from omega_engine_operads.structurebench import (
    ConstraintOutcome,
    StructureBenchEvaluator,
)

TIMESTAMP = "2026-10-10T00:00:00Z"


def write_bundle(root, terminal):
    root.mkdir()
    novella = "".join(
        f"# Act {act}: scene\nturn at {TIMESTAMP}\n"
        for act in ("I", "II", "III", "IV", "V", "VI", "VII")
    )
    (root / "novella.md").write_text(novella, encoding="utf-8", newline="\n")
    (root / "dda_actions.jsonl").write_bytes(terminal)
    summary = {
        "task_key": "decoder-fixture",
        "receipt_id": "receipt:decoder",
        "selected_candidate_id": "candidate:decoder",
        "terminal_verdict": "PASS_TO_MASTER",
    }
    (root / "summary.json").write_text(
        json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    receipt = {key: value for key, value in summary.items() if key != "terminal_verdict"}
    receipt["lean4_proof_hash"] = "a" * 64
    for name in ("novella.md", "dda_actions.jsonl", "summary.json"):
        receipt[name.split(".")[0] + "_sha256"] = hashlib.sha256(
            (root / name).read_bytes()
        ).hexdigest()
    (root / "receipt.json").write_text(
        json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return root


def result_for(report, constraint):
    return next(result for result in report.results if result.constraint_id == constraint)


def test_duplicate_terminal_phi_key_is_typed_violation(tmp_path):
    terminal = (
        '{"payload":{"gamma_2":"0","phi_1":"1","phi_1":"0"},"timestamp":"' + TIMESTAMP + '"}\n'
    ).encode("utf-8")
    bundle = write_bundle(tmp_path / "bundle", terminal)
    report = StructureBenchEvaluator.evaluate_run_folder(bundle)
    terminal_result = result_for(report, "C3_PASS_TO_MASTER_OBLIGATIONS")
    assert terminal_result.outcome is ConstraintOutcome.VIOLATED
    assert "MALFORMED_JSON" in terminal_result.detail
    assert result_for(report, "C1_JSONL_ONE_OBJECT_PER_LINE").outcome is ConstraintOutcome.VIOLATED
    assert not report.is_clean()


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_nonfinite_or_overflow_json_number_cannot_be_terminal_evidence(tmp_path, token):
    terminal = (
        '{"payload":{"gamma_2":"0","phi_1":"0","scale":'
        + token
        + '},"timestamp":"'
        + TIMESTAMP
        + '"}\n'
    ).encode("utf-8")
    report = StructureBenchEvaluator.evaluate_run_folder(
        write_bundle(tmp_path / "bundle", terminal)
    )
    assert result_for(report, "C3_PASS_TO_MASTER_OBLIGATIONS").outcome is ConstraintOutcome.VIOLATED
    assert not report.is_clean()


@pytest.mark.parametrize(
    "terminal",
    [
        b'{"payload":{"gamma_2":"0","phi_1":"1"},"payload":{"gamma_2":"0","phi_1":"0"},"timestamp":"2026-10-10T00:00:00Z"}\n',
        b'{"payload":{"gamma_2":"0","phi_1":"0","note":"\xff"},"timestamp":"2026-10-10T00:00:00Z"}\n',
        b'{"payload":',
    ],
)
def test_ambiguous_or_malformed_terminal_is_typed_not_satisfied(tmp_path, terminal):
    report = StructureBenchEvaluator.evaluate_run_folder(
        write_bundle(tmp_path / "bundle", terminal)
    )
    c3 = result_for(report, "C3_PASS_TO_MASTER_OBLIGATIONS")
    assert c3.outcome is ConstraintOutcome.VIOLATED
    assert "MALFORMED_JSON" in c3.detail
    assert not report.is_clean()


@pytest.mark.parametrize(
    "filename, key, rejected_value",
    [
        ("summary.json", "terminal_verdict", "REFUSED"),
        ("receipt.json", "lean4_proof_hash", ""),
    ],
)
def test_duplicate_binding_key_in_json_document_is_not_decided_clean(
    tmp_path, filename, key, rejected_value
):
    terminal = ('{"payload":{"gamma_2":"0","phi_1":"0"},"timestamp":"' + TIMESTAMP + '"}\n').encode(
        "utf-8"
    )
    bundle = write_bundle(tmp_path / "bundle", terminal)
    path = bundle / filename
    original = path.read_text(encoding="utf-8")
    key_token = json.dumps(key) + ": "
    assert original.count(key_token) == 1
    ambiguous = original.replace(
        key_token, key_token + json.dumps(rejected_value) + ", " + key_token
    )
    path.write_text(ambiguous, encoding="utf-8", newline="\n")
    report = StructureBenchEvaluator.evaluate_run_folder(bundle)
    assert result_for(report, "C1_JSON_PARSES").outcome is ConstraintOutcome.VIOLATED
    assert (
        result_for(report, "C3_PASS_TO_MASTER_OBLIGATIONS").outcome
        is not ConstraintOutcome.SATISFIED
    )
    assert not report.is_clean()
    path.write_text(original, encoding="utf-8", newline="\n")
    assert StructureBenchEvaluator.evaluate_run_folder(bundle).is_clean()


def test_legacy_four_file_measured_bundle_is_clean_and_held_terminal_is_unmeasured(tmp_path):
    terminal = ('{"payload":{"gamma_2":"0","phi_1":"0"},"timestamp":"' + TIMESTAMP + '"}\n').encode(
        "utf-8"
    )
    clean = StructureBenchEvaluator.evaluate_run_folder(write_bundle(tmp_path / "clean", terminal))
    assert clean.coverage() == (11, 11)
    assert clean.is_clean()
    missing_phi = terminal.replace(b'"phi_1":"0",', b"").replace(b',"phi_1":"0"', b"")
    held = StructureBenchEvaluator.evaluate_run_folder(write_bundle(tmp_path / "held", missing_phi))
    assert (
        result_for(held, "C3_PASS_TO_MASTER_OBLIGATIONS").outcome is ConstraintOutcome.UNVERIFIABLE
    )
    assert held.coverage() == (10, 11)
    assert not held.is_clean()


@pytest.mark.parametrize(
    "breakage",
    [
        "missing",
        "changed_bytes",
        "changed_copy_with_matching_digest",
        "wrong_digest",
        "null_digest",
    ],
)
def test_declared_ddc_copy_and_digest_are_load_bearing(tmp_path, breakage):
    terminal = ('{"payload":{"gamma_2":"0","phi_1":"0"},"timestamp":"' + TIMESTAMP + '"}\n').encode(
        "utf-8"
    )
    bundle = write_bundle(tmp_path / "bundle", terminal)
    ddc = bundle / "ddc.jsonl"
    ddc.write_bytes(terminal)
    receipt_path = bundle / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["ddc_sha256"] = hashlib.sha256(terminal).hexdigest()
    receipt_path.write_text(
        json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    assert StructureBenchEvaluator.evaluate_run_folder(bundle).is_clean()
    if breakage == "missing":
        ddc.unlink()
    elif breakage in {"changed_bytes", "changed_copy_with_matching_digest"}:
        ddc.write_bytes(terminal.replace(b'"phi_1":"0"', b'"phi_1":"1"'))
        if breakage == "changed_copy_with_matching_digest":
            receipt["ddc_sha256"] = hashlib.sha256(ddc.read_bytes()).hexdigest()
    elif breakage == "wrong_digest":
        receipt["ddc_sha256"] = "f" * 64
    else:
        receipt["ddc_sha256"] = None
    receipt_path.write_text(
        json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    report = StructureBenchEvaluator.evaluate_run_folder(bundle)
    assert result_for(report, "C2_HASH_BINDING").outcome is ConstraintOutcome.VIOLATED
    assert not report.is_clean()
