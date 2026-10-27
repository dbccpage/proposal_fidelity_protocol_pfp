"""EPIC-OE-OEWAS-007: StructureBench over the four-file bout bundle.

A PASS_TO_MASTER summary with a receipt lean4_proof_hash of null is C3
VIOLATED. persist_bout_run_folder writes the other three files first, then a
SHA-256 receipt with sorted keys. Debate arbitration stays unbuilt.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from operations.domain.rop.result import Ok
from adversary.infrastructure.native import DefaultNativeOperationPort
from adversary.use_cases.persistence import persist_bout_run_folder
from operads.structurebench import (
    ConstraintOutcome,
    StructureBenchEvaluator,
)
from operads.structurebench import evaluator as evaluator_module
from operads.tests.unit.test_structurebench_no_vacuous_decisions import (
    _write_bundle,
)

REPO = Path(__file__).resolve().parents[3]
FORBIDDEN = ("PolarizedDebateArbitrator", "CorpusGroundedDiscoveryEngine")


def test_module_prose_does_not_call_hash_binding_unreachable() -> None:
    text = evaluator_module.__doc__ or ""
    method = StructureBenchEvaluator._c1_keys_sorted.__doc__ or ""
    assert "unreachable" not in text.lower()
    assert "written *first*" not in text
    assert "no `sort_keys`" not in text
    assert "does not do this" not in method
    assert "no `sort_keys`" not in method
    assert "SHA-256" in text
    assert "BLAKE3" in text


def test_null_lean4_proof_hash_on_pass_to_master_is_c3_violated(tmp_path: Path) -> None:
    root = _write_bundle(tmp_path / "b")
    receipt_path = root / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["lean4_proof_hash"] = None
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    c3 = StructureBenchEvaluator(root)._c3_pass_to_master()
    assert c3.outcome is ConstraintOutcome.VIOLATED
    assert c3.detail == "`lean4_proof_hash` is empty"


def test_unsorted_keys_without_sort_keys_are_c1_violated(tmp_path: Path) -> None:
    root = _write_bundle(tmp_path / "b", verdict="REFUSED")
    raw = {
        "z_key": 1,
        "a_key": 2,
        "task_key": "task_1",
        "receipt_id": "receipt_1",
        "selected_candidate_id": "cand_1",
    }
    (root / "receipt.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    c1 = StructureBenchEvaluator(root)._c1_keys_sorted()
    assert c1.outcome is ConstraintOutcome.VIOLATED
    assert "receipt.json" in c1.detail


def test_persist_writes_sorted_sha256_receipt_after_the_other_files(tmp_path: Path) -> None:
    receipt = {
        "z_field": "later",
        "a_field": "earlier",
        "lean4_proof_hash": None,
        "task_key": "bout007",
        "receipt_id": "r007",
        "selected_candidate_id": "c007",
    }
    summary = {
        "z_sum": 1,
        "a_sum": 0,
        "terminal_verdict": "REFUSED",
        "task_key": "bout007",
        "receipt_id": "r007",
        "selected_candidate_id": "c007",
    }
    result = persist_bout_run_folder(
        tmp_path,
        "bout007",
        receipt,
        "# Novella\n",
        [],
        summary,
        native_support=DefaultNativeOperationPort(),
    )
    assert isinstance(result, Ok)
    run = result.unwrap()
    receipt_text = (run / "receipt.json").read_text(encoding="utf-8")
    loaded = json.loads(receipt_text)
    summary_loaded = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    assert list(loaded) == sorted(loaded)
    assert list(summary_loaded) == sorted(summary_loaded)
    assert loaded["lean4_proof_hash"] is None
    assert "blake3" not in receipt_text.lower()
    for name, field in (
        ("uns.md", "uns_sha256"),
        ("ddc.jsonl", "ddc_sha256"),
        ("uts.jsonl", "uts_sha256"),
        ("summary.json", "summary_sha256"),
    ):
        digest = hashlib.sha256((run / name).read_bytes()).hexdigest()
        assert loaded[field] == digest
        assert len(digest) == 64
    c1 = StructureBenchEvaluator(run)._c1_keys_sorted()
    assert c1.outcome is ConstraintOutcome.SATISFIED


def test_bout_service_still_sets_a_null_proof_hash() -> None:
    source = (REPO / "adversary" / "use_cases" / "bout_service.py").read_text(
        encoding="utf-8"
    )
    assert "lean4_proof_hash=None" in source


def test_debate_arbitration_and_corpus_discovery_stay_absent() -> None:
    package = REPO / "operads"
    assert (package / "debate").exists() is False
    defined: set[str] = set()
    for path in (
        package / "structurebench" / "evaluator.py",
        REPO / "adversary" / "use_cases" / "persistence.py",
        REPO / "adversary" / "use_cases" / "bout_service.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        defined.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    assert defined.isdisjoint(FORBIDDEN)
