"""Verification suite for Window 5 Wave 1 Shard B (Paper 008 Part 2).

AuthorityEffect: None.

Targets four audit derivations in Paper 008:
1. AUDIT-P008-012 (ATL-P008-012): Retained September 28 mutation-suite counts
   (40, 40, 45 across C011, C021, C031), active repository execution (40, 51,
   45 mutations plus dual-checker and C031 reference-solver suites), and
   untested-failure-mode boundaries.
2. AUDIT-P008-015 (ATL-P008-015): Absence of retained C001 measurement receipts
   and verification that mcnemar_arms_evaluation.py runs on a 200-case
   synthetic fixture with modulo-5 injected failures.
3. AUDIT-P008-016 (ATL-P008-016): Eight archived K4 traces (SHA-256 and Git
   blob bindings, n=1 per cell, prompt-supplied repair targets in scratchpad
   and hinted conditions, absence of stored final post-move host output, and
   exact weighted L1 terminal Phi1 = 8, 6 and 5, 7 replay).
4. AUDIT-P008-019 (ATL-P008-019): Offline runner isolation (zero socket calls,
   zero credential file reads, external-only writes) and OfflineStubClient
   3, 6, 3, 6 of 6 verdict match counts across conditions without model
   measurement.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import importlib
import importlib.util
import io
import itertools
import json
import re
import shutil
import socket
import sys
import tempfile
import types
import urllib.request
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PFP008_ROOT = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "008_pfp_mssn_tower_challenges_and_retraction_benchmarks"
)
_PFP008_DOCS = _PFP008_ROOT / "docs"
_PFP008_CODE = _PFP008_ROOT / "code"
_PFP008_TRACES_DIR = _PFP008_DOCS / "source_archive" / "k4_traces"
_CERTIFIED_CHALLENGES_DIR = _REPO_ROOT / "workflows" / "tasks" / "certified_challenges"
_C001_DIR = (
    _REPO_ROOT
    / "workflows"
    / "wf12_mechanism_control_arms"
    / "pilots"
    / "c001_attention_distractor_mask"
)

_ARCHIVE_SPEC_TARGETS: tuple[tuple[str, Path], ...] = (
    ("retraction_benchmark_runner", _PFP008_CODE / "retraction_benchmark_runner.py"),
)

_CHALLENGE_PACKAGE_PREFIXES: tuple[str, ...] = (
    "c011_cycle_rank_ladder_coboundary_repair",
    "c021_q40_r",
    "c031_anomaly_free_u1_charges",
    "eis",
    "workflows",
)

# Populated lazily inside the autouse fixture; untouched at import time.
_LAZY_ARCHIVE_CACHE: dict[str, Any] = {}

_K4_VERTICES: tuple[str, ...] = ("a", "b", "c", "d")
_K4_EDGES: tuple[tuple[str, str, int, int], ...] = (
    ("a", "b", 1, 1),
    ("b", "c", 2, 2),
    ("c", "a", 3, 3),
    ("b", "d", 1, 1),
    ("d", "a", 2, 2),
    ("c", "d", 1, 1),
)
_K4_DECLARED_WEIGHTS: dict[str, int] = {f"{u}->{v}": w for u, v, w, _ in _K4_EDGES}
_K4_INITIAL_CLAIMS: dict[str, int] = {f"{u}->{v}": c for u, v, _, c in _K4_EDGES}
_K4_EXACT_REPAIR: dict[str, int] = {
    "a->b": 1,
    "b->c": 2,
    "c->a": -3,
    "b->d": -3,
    "d->a": 2,
    "c->d": -5,
}
_CREDENTIAL_MARKERS: tuple[str, ...] = (
    ".env",
    ".netrc",
    ".gitcookies",
    "id_rsa",
    "id_ed25519",
    "credentials",
)
_NEURAL_IMPORT_ROOTS: frozenset[str] = frozenset(
    {"torch", "transformers", "accelerate", "onnxruntime", "openai", "httpx", "urllib"}
)


def _load_archive_module_from_spec(
    monkeypatch: pytest.MonkeyPatch, module_name: str, file_path: Path
) -> Any:
    """Load an archived Python module via spec_from_file_location without writing bytecode."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to build module spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _bind_isolated_shard_b_modules(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Any:
    """Bind Paper 008 archive modules and isolate bytecode/tempdir state for all tests."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    isolated_tmp = tmp_path / "_isolated_tmp"
    isolated_tmp.mkdir(parents=True, exist_ok=True)
    for env_var in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.setenv(env_var, str(isolated_tmp))
    monkeypatch.setattr(tempfile, "tempdir", str(isolated_tmp))

    if importlib.util.find_spec("yaml") is None:
        yaml_stub = types.ModuleType("yaml")
        yaml_stub.safe_load = json.loads  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "yaml", yaml_stub)

    monkeypatch.syspath_prepend(str(_CERTIFIED_CHALLENGES_DIR))
    snapshot_keys = set(sys.modules)

    if not _LAZY_ARCHIVE_CACHE:
        for mod_name, mod_path in _ARCHIVE_SPEC_TARGETS:
            _LAZY_ARCHIVE_CACHE[mod_name] = _load_archive_module_from_spec(
                monkeypatch, mod_name, mod_path
            )
    else:
        for mod_name, mod_obj in _LAZY_ARCHIVE_CACHE.items():
            monkeypatch.setitem(sys.modules, mod_name, mod_obj)

    yield

    for key in list(sys.modules):
        if key not in snapshot_keys and key.startswith(_CHALLENGE_PACKAGE_PREFIXES):
            sys.modules.pop(key, None)


def _get_runner_mod() -> Any:
    """Return the fixture-injected retraction_benchmark_runner module."""
    return sys.modules["retraction_benchmark_runner"]


def _admitted_archive_bytes(raw_bytes: bytes, expected_len: int) -> bytes:
    """Return raw archive bytes matching expected_len across CRLF or LF checkouts."""
    if len(raw_bytes) == expected_len:
        return raw_bytes
    crlf_bytes = raw_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return crlf_bytes if len(crlf_bytes) == expected_len else raw_bytes.replace(b"\r\n", b"\n")


def _git_blob_sha1(content_bytes: bytes) -> str:
    """Compute the standard Git blob SHA-1 digest over raw content bytes."""
    header = f"blob {len(content_bytes)}\0".encode("ascii")
    return hashlib.sha1(header + content_bytes, usedforsecurity=False).hexdigest()


def _extract_root_imports(source_text: str) -> set[str]:
    """Return top-level imported package names from a Python source string."""
    tree = ast.parse(source_text)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _infer_k4_condition(task_id_or_name: str) -> str:
    """Infer the K4 benchmark condition label from a trace task_id or filename."""
    for cond in ("partially_masked", "scratchpad", "hinted", "baseline"):
        if cond in task_id_or_name:
            return cond
    raise ValueError(f"Unrecognized K4 condition in {task_id_or_name}")


def _compute_k4_phi1(claims: dict[str, int]) -> int:
    """Compute exact weighted L1 coboundary distance on K4 via spanning-tree potentials."""
    best: int | None = None
    edge_keys = list(_K4_DECLARED_WEIGHTS)
    for tree_edges in itertools.combinations(edge_keys, 3):
        potentials: dict[str, int] = {"a": 0}
        progressed = True
        while progressed:
            progressed = False
            for edge_key in tree_edges:
                u, v = edge_key.split("->")
                val = int(claims.get(edge_key, 0))
                if u in potentials and v not in potentials:
                    potentials[v] = potentials[u] + val
                    progressed = True
                elif v in potentials and u not in potentials:
                    potentials[u] = potentials[v] - val
                    progressed = True
        if len(potentials) != len(_K4_VERTICES):
            continue
        cost = sum(
            weight * abs(int(claims.get(ek, 0)) - (potentials[ek[3]] - potentials[ek[0]]))
            for ek, weight in _K4_DECLARED_WEIGHTS.items()
        )
        if best is None or cost < best:
            best = cost
    if best is None:
        raise RuntimeError("No spanning tree found on K4")
    return best


def _extract_json_move_from_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return parsed_move from a K4 trace row, falling back to JSON extraction on raw_response."""
    parsed_move = row.get("parsed_move")
    if isinstance(parsed_move, dict):
        return parsed_move
    raw_reply = str(row.get("raw_response", ""))
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_reply, flags=re.DOTALL)
    candidate = (
        fenced.group(1) if fenced else raw_reply[raw_reply.find("{") : raw_reply.rfind("}") + 1]
    )
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("Expected JSON object move")
    return parsed


def _parse_embedded_turn_history(user_turn: str) -> list[tuple[int, str, str, int]]:
    """Extract (turn_idx, move_type, status, phi1) lines from a K4 prompt history block."""
    pattern = re.compile(
        r"^Turn\s+(\d+):\s+([A-Z]+)\s+->\s+([A-Za-z]+)\.\s+Phi_1=(\d+)\.", re.MULTILINE
    )
    return [
        (int(m.group(1)), m.group(2), m.group(3), int(m.group(4)))
        for m in pattern.finditer(user_turn)
    ]


def _step_historical_k4_cut(
    claims: dict[str, int], phi_before: int, proposed_raw: Any
) -> tuple[dict[str, int], str, int]:
    """Evaluate a CUT proposal under the historical K4 host transition rules."""
    if not isinstance(proposed_raw, dict) or any(
        k not in _K4_DECLARED_WEIGHTS for k in proposed_raw
    ):
        return dict(claims), "MoveViolation", phi_before
    candidate = {k: int(v) for k, v in proposed_raw.items()}
    phi_after = _compute_k4_phi1(candidate)
    if phi_after > phi_before:
        return dict(claims), "DefectIncrease", phi_before
    if phi_after == 0 and phi_before > 0:
        status = "ExactRepair"
    elif phi_after < phi_before:
        status = "MonotonicDescent"
    else:
        status = "IdempotentStationary"
    return candidate, status, phi_after


def _step_historical_k4_host(
    claims: dict[str, int], move: dict[str, Any]
) -> tuple[dict[str, int], str, int]:
    """Replay one move under the historical K4 host transition semantics."""
    move_type = str(move.get("move_type", ""))
    phi_before = _compute_k4_phi1(claims)

    if move_type == "ASSERT":
        u = move.get("u", move.get("source"))
        v = move.get("v", move.get("target"))
        val = move.get("value", move.get("claim"))
        edge_key = f"{u}->{v}"
        if edge_key not in _K4_DECLARED_WEIGHTS or val is None:
            return dict(claims), "MoveViolation", phi_before
        updated = dict(claims)
        updated[edge_key] = int(val)
        return updated, "Asserted", _compute_k4_phi1(updated)

    if move_type == "CUT":
        return _step_historical_k4_cut(claims, phi_before, move.get("proposed_claims"))

    if move_type == "VERIFY":
        status = "Verified" if phi_before == 0 else "UnverifiedObstruction"
        return dict(claims), status, phi_before

    return dict(claims), "MoveViolation", phi_before


def _validate_raw_k4_row(
    row: dict[str, Any], idx: int, trace_name: str, history: list[tuple[int, str, str, int]]
) -> None:
    """Validate raw pending host fields and embedded prefix history on one K4 trace row."""
    if (
        row.get("phi1_before") is not None
        or row.get("phi1_after") is not None
        or row.get("admission_status") != "pending"
        or row.get("admitted") is not False
    ):
        raise ValueError(f"Corrupted raw host fields at turn {idx} in {trace_name}")
    embedded = _parse_embedded_turn_history(row["user_turn"])
    if embedded != history:
        raise ValueError(f"Prefix mismatch at turn {idx} in {trace_name}")


def _replay_k4_trace(
    trace_path: Path,
    *,
    expected_sha256: str | None = None,
    expected_bytes: int | None = None,
) -> dict[str, Any]:
    """Replay an archived K4 trace file and verify raw fields, prefix turns, and optional digest."""
    raw_bytes = trace_path.read_bytes()
    archive_bytes = (
        _admitted_archive_bytes(raw_bytes, expected_bytes)
        if expected_bytes is not None
        else raw_bytes
    )
    if expected_bytes is not None and len(archive_bytes) != expected_bytes:
        raise ValueError(
            f"Byte length mismatch for {trace_path.name}: {len(archive_bytes)} != {expected_bytes}"
        )
    if expected_sha256 is not None and hashlib.sha256(archive_bytes).hexdigest() != expected_sha256:
        raise ValueError(f"SHA-256 digest mismatch for {trace_path.name}")

    rows = [
        json.loads(line)
        for line in archive_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]
    claims: dict[str, int] = {}
    history: list[tuple[int, str, str, int]] = []
    benchmark_loops = 0
    cut_proposals: list[tuple[int, dict[str, int]]] = []

    for idx, row in enumerate(rows, start=1):
        _validate_raw_k4_row(row, idx, trace_path.name, history)
        move = _extract_json_move_from_row(row)
        move_type = str(move.get("move_type", ""))
        if move_type == "CUT" and isinstance(move.get("proposed_claims"), dict):
            cut_proposals.append(
                (idx, {str(k): int(v) for k, v in move["proposed_claims"].items()})
            )
        claims, status, phi_after = _step_historical_k4_host(claims, move)
        if status in ("IdempotentStationary", "DefectIncrease", "MoveViolation") or (
            move_type == "ASSERT" and idx > 6
        ):
            benchmark_loops += 1
        history.append((idx, move_type, status, phi_after))

    terminal_phi1 = history[-1][3]
    return {
        "rows": rows,
        "condition": _infer_k4_condition(trace_path.name),
        "turns": len(rows),
        "loops": benchmark_loops,
        "terminal_phi1": terminal_phi1,
        "accepted": terminal_phi1 == 0,
        "cut_proposals": cut_proposals,
        "history": history,
        "terminal_claims": claims,
    }


def _verify_and_replay_k4_trace(
    trace_path: Path, source_entry: dict[str, Any]
) -> dict[str, Any]:
    """Verify trace_path against source_index.json SHA-256/bytes and replay the K4 trace."""
    return _replay_k4_trace(
        trace_path,
        expected_sha256=str(source_entry["sha256"]),
        expected_bytes=int(source_entry["bytes"]),
    )


# ---------------------------------------------------------------------------
# 1. AUDIT-P008-012: Mutation suite rejection
# ---------------------------------------------------------------------------


class TestMutationSuiteRejection:
    """Verifies AUDIT-P008-012 across historical census records and active suites."""

    def test_historical_census_and_ledger_record_40_40_45_counts(self) -> None:
        """Positive check: historical census and Sept 28 ledger record 40, 40, 45 mutations."""
        census = json.loads(
            (_PFP008_DOCS / "historical_census_inventory.json").read_text(encoding="utf-8")
        )
        assert census["revision"] == "a623568eb0f853b968bc419bf06dfc6af256ab02"
        by_id = {entry["id"]: entry for entry in census["challenges"]}

        expected = {
            "C011": (
                40,
                46,
                "commitments/c011_scoring_receipt.json",
                "c011_cycle_rank_ladder_coboundary_repair",
            ),
            "C021": (
                40,
                46,
                "commitments/c021_q40_r_scoring_receipt.json",
                "c021_q40_r",
            ),
            "C031": (
                45,
                46,
                "commitments/c031_scoring_receipt.json",
                "c031_anomaly_free_u1_charges",
            ),
        }
        for cid, (mut_count, hid_count, receipt_rel, active_pkg) in expected.items():
            rec = by_id[cid]
            assert rec["category"] == "A"
            assert rec["mutation_json_files"] == mut_count
            assert rec["hidden_json_files"] == hid_count
            assert [r["path"] for r in rec["scoring_receipt_files"]] == [receipt_rel]
            # Retained C011/C021/C031 scoring receipts from commit a623568e are absent here
            assert list((_CERTIFIED_CHALLENGES_DIR / active_pkg).rglob("*scoring_receipt.json")) == []

        ledger_text = (_PFP008_ROOT / "paper_claim_ledger.md").read_text(encoding="utf-8")
        assert "PFP008-12" in ledger_text
        for snippet in ("41 passed", "5 passed", "47 passed", "9 passed"):
            assert snippet in ledger_text

    def test_c011_active_suite_rejects_all_40_mutations_and_passes_dual_checkers(self) -> None:
        """Positive check: active C011 rejects all 40 mutations and passes dual-checker tests."""
        c011_mut_mod = importlib.import_module(
            "c011_cycle_rank_ladder_coboundary_repair.judge_packet.mutation_suite.test_c011_checker_mutations"
        )
        c011_dual_mod = importlib.import_module(
            "c011_cycle_rank_ladder_coboundary_repair.tests.test_dual_checkers"
        )

        mut_files = list(c011_mut_mod.MUTATION_FILES)
        assert len(mut_files) == 40
        c011_mut_mod.test_mutation_suite_inventory_count()
        for mut_path in mut_files:
            c011_mut_mod.test_dual_checkers_reject_mutation(mut_path)

        dual_funcs = [
            getattr(c011_dual_mod, name)
            for name in sorted(dir(c011_dual_mod))
            if name.startswith("test_") and callable(getattr(c011_dual_mod, name))
        ]
        assert len(dual_funcs) == 5
        for fn in dual_funcs:
            fn()

    def test_c021_active_suite_rejects_original_40_and_expanded_51_mutations(self) -> None:
        """Positive check: active C021 rejects mut_01..mut_40 (40) and mut_41..mut_51 (51 total)."""
        c021_mut_mod = importlib.import_module(
            "c021_q40_r.judge_packet.mutation_suite.test_c021_checker_mutations"
        )
        c021_dual_mod = importlib.import_module("c021_q40_r.tests.test_dual_checkers")

        mut_files = list(c021_mut_mod.MUTATION_FILES)
        assert len(mut_files) == 51
        assert [p.name for p in mut_files[:40]] == [f"mut_{i:02d}.json" for i in range(1, 41)]
        assert [p.name for p in mut_files[40:]] == [f"mut_{i:02d}.json" for i in range(41, 52)]

        c021_mut_mod.test_mutation_suite_inventory_count()
        for mut_path in mut_files:
            c021_mut_mod.test_dual_checkers_reject_mutation(mut_path)

        # Active C021 case inventory has 44 cases after removing two leaked base cases
        c021_dual_mod.test_judge_cases_inventory_counts()
        assert len(c021_dual_mod.ALL_CASE_FILES) == 44

    def test_c031_active_suite_rejects_all_45_mutations_and_passes_dual_and_reference_tests(
        self,
    ) -> None:
        """Positive check: active C031 rejects all 45 mutations and passes dual + reference suites."""
        c031_mut_mod = importlib.import_module(
            "c031_anomaly_free_u1_charges.judge_packet.mutation_suite.test_c031_checker_mutations"
        )
        c031_dual_mod = importlib.import_module(
            "c031_anomaly_free_u1_charges.tests.test_dual_checkers"
        )
        c031_ref_mod = importlib.import_module(
            "c031_anomaly_free_u1_charges.tests.test_reference_solver"
        )

        mut_files = list(c031_mut_mod.MUTATION_FILES)
        assert len(mut_files) == 45
        c031_mut_mod.test_mutation_suite_inventory_count()
        for mut_path in mut_files:
            c031_mut_mod.test_dual_checkers_reject_mutation(mut_path)
        c031_mut_mod.test_refusal_mutations_specifically_rejected()

        dual_funcs = [
            getattr(c031_dual_mod, name)
            for name in sorted(dir(c031_dual_mod))
            if name.startswith("test_") and callable(getattr(c031_dual_mod, name))
        ]
        assert len(dual_funcs) == 5
        for fn in dual_funcs:
            fn()

        ref_funcs = [
            getattr(c031_ref_mod, name)
            for name in sorted(dir(c031_ref_mod))
            if name.startswith("test_") and callable(getattr(c031_ref_mod, name))
        ]
        assert len(ref_funcs) == 9
        for fn in ref_funcs:
            fn()

    def test_falsification_uncorrupted_certificates_pass_and_disagreement_or_untested_modes_surface(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: valid outputs PASS; single-checker blind spots and case drift surface."""
        c021_dual = importlib.import_module("c021_q40_r.judge_packet.checkers.dual_evaluator")
        c021_solver = importlib.import_module("c021_q40_r.reference_solver.solver")

        case_path = (
            _CERTIFIED_CHALLENGES_DIR
            / "c021_q40_r"
            / "judge_packet"
            / "cases"
            / "base"
            / "case_06.json"
        )
        case = json.loads(case_path.read_text(encoding="utf-8"))
        valid_result = c021_solver.solve(case)
        clean_eval = c021_dual.evaluate_dual(case, valid_result)
        assert clean_eval["verdict"] == "PASS"
        assert clean_eval["agreement"] is True

        # Shared upstream case-encoding corruption prior to solving yields PASS for the altered case,
        # illustrating an untested failure mode outside static certificate-mutation files.
        altered_case = json.loads(json.dumps(case))
        altered_case["terms"][0]["weight"] = [99, 1]
        altered_eval = c021_dual.evaluate_dual(altered_case, c021_solver.solve(altered_case))
        assert altered_eval["verdict"] == "PASS"

        # If a novel fault bypasses one checker while tripping the other, evaluate_dual emits
        # CHECKER_DISAGREEMENT and assert_dual_agreement raises CheckerDisagreementError.
        corrupted_minimizer = dict(valid_result)
        corrupted_minimizer["minimizers"] = [7]
        monkeypatch.setattr(
            c021_dual,
            "verify_spectral_optimality",
            lambda _case, _res: (True, "VALID: simulated blindspot"),
        )
        disagreement = c021_dual.evaluate_dual(case, corrupted_minimizer)
        assert disagreement["verdict"] == "CHECKER_DISAGREEMENT"
        assert disagreement["agreement"] is False
        with pytest.raises(c021_dual.CheckerDisagreementError):
            c021_dual.assert_dual_agreement(case, corrupted_minimizer)


# ---------------------------------------------------------------------------
# 2. AUDIT-P008-015: C001 measurement absence
# ---------------------------------------------------------------------------


class TestC001MeasurementAbsence:
    """Verifies AUDIT-P008-015: C001 has no retained measurement and runs a synthetic fixture."""

    def test_c001_census_and_repository_have_zero_retained_measurement_receipts(self) -> None:
        """Positive check: C001 has zero scoring receipts, traces, or measurement report files."""
        census = json.loads(
            (_PFP008_DOCS / "historical_census_inventory.json").read_text(encoding="utf-8")
        )
        c001_entry = next(item for item in census["challenges"] if item["id"] == "C001")
        assert c001_entry["category"] == "B"
        assert c001_entry["scoring_receipt_files"] == []
        assert c001_entry["hidden_json_files"] == 0
        assert c001_entry["mutation_json_files"] == 0

        inv_raw = json.loads(
            (_REPO_ROOT / "dag" / "file_inventory.json").read_text(encoding="utf-8")
        )
        inv_paths = [item["path"] for item in inv_raw["files"]]
        c001_paths = [p for p in inv_paths if "c001_attention_distractor_mask" in p]
        assert len(c001_paths) > 0
        assert [
            p for p in c001_paths if p.endswith(".jsonl") or "receipt" in p or "report" in p
        ] == []

        pipeline = json.loads((_C001_DIR / "pipeline.json").read_text(encoding="utf-8"))
        assert pipeline["tokenizer_json_sha256"] is None
        assert pipeline["tokenizer_json_sha256_status"] == "UNSET"
        assert pipeline["prompt_template_digest"] is None
        assert pipeline["prompt_template_digest_status"] == "UNSET"

        conditional_run_dir = (
            _REPO_ROOT / "_ic" / "darpa" / "adversary" / "runs" / "c001_mechanism_pilot"
        )
        assert not conditional_run_dir.exists()

        emp_source = (_C001_DIR / "empirical_neural_mcnemar_evaluation.py").read_text(
            encoding="utf-8"
        )
        assert "Execute the full 200 hidden-case sweep on accelerated GPU hardware" in emp_source

    def test_mcnemar_module_flags_and_ast_confirm_synthetic_injected_failure_rule(self) -> None:
        """Positive check: mcnemar_arms_evaluation declares synthetic flags and zero neural imports."""
        from workflows.wf12_mechanism_control_arms.pilots.c001_attention_distractor_mask import (
            mcnemar_arms_evaluation as mcnemar_mod,
        )

        assert mcnemar_mod.IS_SYNTHETIC_FIXTURE is True
        assert mcnemar_mod.IS_EMPIRICAL_MEASUREMENT is False
        assert mcnemar_mod.EVALUATION_TYPE == "SYNTHETIC_VERIFICATION_HARNESS_FIXTURE"

        source_text = (_C001_DIR / "mcnemar_arms_evaluation.py").read_text(encoding="utf-8")
        imported_roots = _extract_root_imports(source_text)
        assert imported_roots.isdisjoint(_NEURAL_IMPORT_ROOTS)
        assert 'case["seed"] % 5 in (0, 1)' in source_text

    def test_mcnemar_200_case_synthetic_fixture_reproduces_exact_contingency_counts(self) -> None:
        """Positive check: 200-case synthetic run yields b=80, c=0, chi2=80, p=1/2^79."""
        from workflows.wf12_mechanism_control_arms.pilots.c001_attention_distractor_mask import (
            case_generator,
            mcnemar_arms_evaluation,
        )

        cases = case_generator.generate_hidden_base_set(base_seed=2026)
        assert len(cases) == 200
        mod5_hits = sum(
            1
            for c in cases
            if bool(c.get("distractor_matches_claim", False) or (c["seed"] % 5 in (0, 1)))
        )
        assert mod5_hits == 80

        report = mcnemar_arms_evaluation.run_mcnemar_hidden_base_arms_evaluation(base_seed=2026)
        assert report["sample_size"] == 200
        assert report["is_synthetic_fixture"] is True
        assert report["is_empirical_measurement"] is False

        f_vs_a = report["comparison_F_distractor_vs_Arm_A"]
        assert f_vs_a["table_2x2"] == {
            "both_pass_a": 120,
            "A_fail_F_pass_b": 80,
            "A_pass_F_fail_c": 0,
            "both_fail_d": 0,
        }
        assert f_vs_a["mcnemar"]["chi2"] == "80"
        assert f_vs_a["mcnemar"]["p_value"] == str(Fraction(1, 2**79))
        assert f_vs_a["mcnemar"]["is_significant_alpha_0_05"] is True

        f_vs_del = report["comparison_F_distractor_vs_F_delete"]
        assert f_vs_del["table_2x2"] == {
            "both_pass_a": 200,
            "Delete_fail_F_pass_b": 0,
            "Delete_pass_F_fail_c": 0,
            "both_fail_d": 0,
        }
        assert f_vs_del["mcnemar"]["chi2"] == "0"
        assert f_vs_del["mcnemar"]["p_value"] == "1"

    def test_falsification_removing_synthetic_seed_modulo_eliminates_arm_a_discordance(
        self,
    ) -> None:
        """Negative control: evaluating Arm A with the deterministic solver collapses b=80 to 0."""
        from workflows.wf12_mechanism_control_arms.pilots.c001_attention_distractor_mask import (
            case_generator,
            mcnemar_arms_evaluation,
        )
        from workflows.wf12_mechanism_control_arms.pilots.c001_attention_distractor_mask.solve import (
            solve as solve_fn,
        )
        from workflows.wf12_mechanism_control_arms.pilots.c001_attention_distractor_mask.solver import (
            verify_certificate,
        )

        cases = case_generator.generate_hidden_base_set(base_seed=2026)
        b_without_injection = 0
        c_without_injection = 0
        for case in cases:
            cert = solve_fn(case)
            f_pass, _ = verify_certificate(case, cert)
            # Without the hardcoded seed % 5 in (0, 1) rule, Arm A uses the same case data
            a_pass, _ = verify_certificate(case, solve_fn(case))
            if f_pass and not a_pass:
                b_without_injection += 1
            elif a_pass and not f_pass:
                c_without_injection += 1

        assert (b_without_injection, c_without_injection) == (0, 0)
        uninjected_stats = mcnemar_arms_evaluation.compute_mcnemar_exact(
            b_without_injection, c_without_injection
        )
        assert uninjected_stats["chi2"] == "0"
        assert uninjected_stats["p_value"] == "1"
        assert uninjected_stats["is_significant_alpha_0_05"] is False


# ---------------------------------------------------------------------------
# 3. AUDIT-P008-016: K4 trace outcomes
# ---------------------------------------------------------------------------


class TestK4TraceOutcomes:
    """Verifies AUDIT-P008-016 across the eight archived K4 JSONL traces."""

    def test_eight_k4_traces_match_source_index_digests_and_n_equals_1_design(self) -> None:
        """Positive check: all 8 K4 traces match source_index.json SHA-256/blob digests at n=1."""
        source_index = json.loads(
            (_PFP008_DOCS / "source_archive" / "source_index.json").read_text(encoding="utf-8")
        )
        assert source_index["capture_review_base"] == "23893fc44162555fa12ceda3e1665982e3d7a14e"

        trace_entries = [
            entry
            for entry in source_index["entries"]
            if entry["path"].startswith("docs/source_archive/k4_traces/")
        ]
        assert len(trace_entries) == 8

        cells_seen: set[tuple[str, str]] = set()
        for entry in trace_entries:
            assert entry["revision"] == "52cb5457f6c485ba548cfd292f6012a941ed22cf"
            trace_file = _PFP008_ROOT / entry["path"]
            archive_bytes = _admitted_archive_bytes(trace_file.read_bytes(), entry["bytes"])
            assert len(archive_bytes) == entry["bytes"]
            assert hashlib.sha256(archive_bytes).hexdigest() == entry["sha256"]
            assert _git_blob_sha1(archive_bytes) == entry["git_blob_sha"]

            rows = [
                json.loads(line)
                for line in archive_bytes.decode("utf-8").splitlines()
                if line.strip()
            ]
            cell = (rows[0]["model"], _infer_k4_condition(trace_file.name))
            assert cell not in cells_seen, f"Duplicate cell {cell}; expected n=1 per cell"
            cells_seen.add(cell)

        expected_models = {"qwen/qwen-2.5-7b-instruct", "meta-llama/llama-3.1-8b-instruct"}
        expected_conditions = {"baseline", "partially_masked", "scratchpad", "hinted"}
        assert cells_seen == {(m, c) for m in expected_models for c in expected_conditions}

    def test_raw_trace_rows_lack_stored_final_post_move_result_and_prompts_differ_by_condition(
        self,
    ) -> None:
        """Positive check: raw JSONL rows store pending host fields and assisted prompts carry targets."""
        trace_files = sorted(_PFP008_TRACES_DIR.glob("*.jsonl"))
        assert len(trace_files) == 8

        joined_prompts_by_condition: dict[str, str] = {}
        for trace_file in trace_files:
            rows = [
                json.loads(line)
                for line in trace_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            for row in rows:
                assert row["phi1_before"] is None
                assert row["phi1_after"] is None
                assert row["admission_status"] == "pending"
                assert row["admitted"] is False

            # Turn T prompt records only Turns 1..T-1; Turn T itself has no stored post-move row
            last_embedded = _parse_embedded_turn_history(rows[-1]["user_turn"])
            assert len(last_embedded) == len(rows) - 1
            cond = _infer_k4_condition(trace_file.name)
            joined_prompts_by_condition.setdefault(
                cond, "\n".join(r["user_turn"] for r in rows)
            )

        for unassisted in ("baseline", "partially_masked"):
            assert "(-2) - 1 = -3" not in joined_prompts_by_condition[unassisted]
            assert "(-2) - 3 = -5" not in joined_prompts_by_condition[unassisted]
            assert "target=-3" not in joined_prompts_by_condition[unassisted]
            assert "target=-5" not in joined_prompts_by_condition[unassisted]
            assert '"c->d": -5' not in joined_prompts_by_condition[unassisted]

        assert "(-2) - 1 = -3" in joined_prompts_by_condition["scratchpad"]
        assert "(-2) - 3 = -5" in joined_prompts_by_condition["scratchpad"]
        assert "target=-3" in joined_prompts_by_condition["hinted"]
        assert "target=-5" in joined_prompts_by_condition["hinted"]
        assert '"c->d": -5' in joined_prompts_by_condition["hinted"]

    def test_proposal_extraction_and_exact_phi1_replay_match_prefix_logs_and_terminal_scores(
        self,
    ) -> None:
        """Positive check: exact repair appears in scratchpad/hinted; terminal Phi1 = 8,6 and 5,7."""
        expected_outcomes: dict[tuple[str, str], tuple[int, int, int, bool, bool]] = {
            ("qwen/qwen-2.5-7b-instruct", "baseline"): (12, 6, 8, False, False),
            ("qwen/qwen-2.5-7b-instruct", "partially_masked"): (12, 5, 6, False, False),
            ("qwen/qwen-2.5-7b-instruct", "scratchpad"): (9, 1, 0, True, True),
            ("qwen/qwen-2.5-7b-instruct", "hinted"): (9, 1, 0, True, True),
            ("meta-llama/llama-3.1-8b-instruct", "baseline"): (12, 5, 5, False, False),
            ("meta-llama/llama-3.1-8b-instruct", "partially_masked"): (12, 4, 7, False, False),
            ("meta-llama/llama-3.1-8b-instruct", "scratchpad"): (12, 4, 0, True, True),
            ("meta-llama/llama-3.1-8b-instruct", "hinted"): (12, 4, 0, True, True),
        }

        source_index = json.loads(
            (_PFP008_DOCS / "source_archive" / "source_index.json").read_text(encoding="utf-8")
        )
        entries_by_name = {
            Path(entry["path"]).name: entry
            for entry in source_index["entries"]
            if entry["path"].startswith("docs/source_archive/k4_traces/")
        }

        for trace_file in sorted(_PFP008_TRACES_DIR.glob("*.jsonl")):
            replay = _verify_and_replay_k4_trace(trace_file, entries_by_name[trace_file.name])
            first_row = replay["rows"][0]
            cell = (first_row["model"], replay["condition"])
            exp_turns, exp_loops, exp_phi1, exp_accept, exp_has_repair = expected_outcomes[cell]

            assert replay["turns"] == exp_turns
            assert replay["loops"] == exp_loops
            assert replay["terminal_phi1"] == exp_phi1
            assert replay["accepted"] == exp_accept

            proposed_exact_repair = any(
                prop == _K4_EXACT_REPAIR for _, prop in replay["cut_proposals"]
            )
            assert proposed_exact_repair is exp_has_repair

    def test_falsification_partial_cut_zero_claim_loophole_and_single_chord_defect_increase(
        self, tmp_path: Path
    ) -> None:
        """Negative control: partial zero CUT, single-chord DefectIncrease, and corrupted trace rejection."""
        assert _compute_k4_phi1(_K4_INITIAL_CLAIMS) == 8
        assert _compute_k4_phi1(_K4_EXACT_REPAIR) == 0

        # Llama baseline Turn 9 / scratchpad Turn 12 partial CUT omits tree edges:
        partial_zero_chords = {"c->a": 0, "b->d": 0, "c->d": 0}
        missing_tree_edges = sorted(set(_K4_DECLARED_WEIGHTS) - set(partial_zero_chords))
        assert missing_tree_edges == ["a->b", "b->c", "d->a"]

        _, hist_status, hist_phi = _step_historical_k4_host(
            dict(_K4_INITIAL_CLAIMS),
            {"move_type": "CUT", "proposed_claims": partial_zero_chords},
        )
        assert hist_status == "ExactRepair"
        assert hist_phi == 0

        # Keeping the asserted tree edges (1, 2, 2) with zero chords yields Phi1 = 5 > 0
        # (attained at zero potential via spanning tree {c->a, b->d, c->d} with residual 1+2+2 = 5).
        preserved_tree_with_zero_chords = {
            "a->b": 1,
            "b->c": 2,
            "c->a": 0,
            "b->d": 0,
            "d->a": 2,
            "c->d": 0,
        }
        assert _compute_k4_phi1(preserved_tree_with_zero_chords) == 5

        # Modifying any single chord to its coboundary value raises Phi1 above 8 -> DefectIncrease
        for chord_edge, target_val, expected_phi in (
            ("c->a", -3, 10),
            ("b->d", -3, 12),
            ("c->d", -5, 14),
        ):
            one_chord = dict(_K4_INITIAL_CLAIMS)
            one_chord[chord_edge] = target_val
            assert _compute_k4_phi1(one_chord) == expected_phi
            _, status, gated_phi = _step_historical_k4_host(
                dict(_K4_INITIAL_CLAIMS),
                {"move_type": "CUT", "proposed_claims": one_chord},
            )
            assert status == "DefectIncrease"
            assert gated_phi == 8

        # Negative checks on JSONL trace copies in tmp_path: corrupted phi1_before or digest mismatch fails
        source_index = json.loads(
            (_PFP008_DOCS / "source_archive" / "source_index.json").read_text(encoding="utf-8")
        )
        sample_entry = next(
            entry
            for entry in source_index["entries"]
            if entry["path"].startswith("docs/source_archive/k4_traces/")
        )
        orig_trace = _PFP008_ROOT / sample_entry["path"]
        admitted_bytes = _admitted_archive_bytes(orig_trace.read_bytes(), sample_entry["bytes"])
        orig_rows = [
            json.loads(line)
            for line in admitted_bytes.decode("utf-8").splitlines()
            if line.strip()
        ]

        corrupted_phi_rows = [dict(r) for r in orig_rows]
        corrupted_phi_rows[0]["phi1_before"] = 8
        corrupted_phi_path = tmp_path / f"corrupted_phi_{orig_trace.name}"
        corrupted_phi_path.write_text(
            "\n".join(json.dumps(r) for r in corrupted_phi_rows) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Corrupted raw host fields"):
            _replay_k4_trace(corrupted_phi_path)

        # Same byte length with one flipped character inside model_turn triggers pure SHA-256 mismatch
        mutated_bytes = admitted_bytes.replace(b'"ASSERT"', b'"ASSERt"', 1)
        assert len(mutated_bytes) == len(admitted_bytes)
        corrupted_digest_path = tmp_path / f"corrupted_digest_{orig_trace.name}"
        corrupted_digest_path.write_bytes(mutated_bytes)
        with pytest.raises(ValueError, match="SHA-256 digest mismatch"):
            _verify_and_replay_k4_trace(corrupted_digest_path, sample_entry)


# ---------------------------------------------------------------------------
# 4. AUDIT-P008-019: Offline runner isolation
# ---------------------------------------------------------------------------


class TestOfflineRunnerIsolation:
    """Verifies AUDIT-P008-019: offline isolation boundaries and 3, 6, 3, 6 stub match counts."""

    def test_offline_stub_matches_3_6_3_6_of_6_verdicts_and_exit_codes(
        self, tmp_path: Path
    ) -> None:
        """Positive check: offline mode matches 3, 6, 3, 6 of 6 verdicts with exit codes 1, 0, 1, 0."""
        runner_mod = _get_runner_mod()
        expected = (
            ("baseline", 3, 1, "offline-stub"),
            ("hinted", 6, 0, "offline-stub"),
            ("scratchpad", 3, 1, "offline-stub"),
            ("exact_oracle", 6, 0, "host"),
        )
        observed_matches: list[int] = []
        for condition, exp_matches, exp_rc, exp_provider in expected:
            out_dir = tmp_path / f"run_{condition}"
            rc = runner_mod.main(["--condition", condition, "--output-dir", str(out_dir)])
            assert rc == exp_rc

            summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
            assert summary["mode"] == "offline-stub"
            assert summary["condition"] == condition
            assert summary["instances"] == 6
            assert summary["matched"] == exp_matches
            observed_matches.append(summary["matched"])

            receipt_rows = [
                json.loads(line)
                for line in (out_dir / "receipts.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            assert len(receipt_rows) == 6
            assert all(r["provider"] == exp_provider for r in receipt_rows)
            assert all(r["cost_usd"] == 0.0 for r in receipt_rows)

        assert tuple(observed_matches) == (3, 6, 3, 6)

    def test_offline_execution_opens_no_socket_and_reads_no_credential_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Positive check: socket and file-open hooks record zero sockets and zero credential reads."""
        runner_mod = _get_runner_mod()

        def _forbid_network(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError(f"Unexpected network/socket call: args={args}, kwargs={kwargs}")

        monkeypatch.setattr(socket, "socket", _forbid_network)
        monkeypatch.setattr(socket, "create_connection", _forbid_network)
        monkeypatch.setattr(socket, "getaddrinfo", _forbid_network)
        monkeypatch.setattr(urllib.request, "urlopen", _forbid_network)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-unused-offline-sentinel")

        for env_var in ("TMPDIR", "TEMP", "TMP"):
            monkeypatch.setenv(env_var, str(tmp_path))
        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))

        opened_records: list[tuple[Path, str]] = []
        real_builtins_open = builtins.open
        real_io_open = io.open
        real_path_open = Path.open

        def _record_open(target: Any, mode: str) -> None:
            if isinstance(target, (str, Path)):
                opened_records.append((Path(target).resolve(), mode))

        def _hooked_builtins_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            _record_open(file, mode)
            return real_builtins_open(file, mode, *args, **kwargs)

        def _hooked_io_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            _record_open(file, mode)
            return real_io_open(file, mode, *args, **kwargs)

        def _hooked_path_open(self_path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            _record_open(self_path, mode)
            return real_path_open(self_path, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _hooked_builtins_open)
        monkeypatch.setattr(io, "open", _hooked_io_open)
        monkeypatch.setattr(Path, "open", _hooked_path_open)

        for condition in runner_mod.CONDITIONS:
            out_dir = tmp_path / f"iso_{condition}"
            runner_mod.main(["--condition", condition, "--output-dir", str(out_dir)])

        # Also exercise default mkdtemp path when --output-dir is omitted (redirected inside tmp_path)
        default_dir = runner_mod.resolve_output_dir(None)
        try:
            assert default_dir.resolve().is_relative_to(tmp_path.resolve())
            assert not default_dir.is_relative_to(runner_mod.PACKAGE_ROOT)
            runner_mod.write_outputs(
                default_dir,
                runner_mod.run_benchmark(condition="hinted"),
                "offline-stub",
            )
        finally:
            shutil.rmtree(default_dir, ignore_errors=True)

        assert len(opened_records) > 0
        runner_resolved = (_PFP008_CODE / "retraction_benchmark_runner.py").resolve()
        ext_roots = (tmp_path.resolve(), default_dir.resolve())

        for path_obj, mode in opened_records:
            lowered = path_obj.name.lower()
            assert not any(marker in lowered for marker in _CREDENTIAL_MARKERS)
            if any(flag in mode for flag in ("w", "a", "x", "+")):
                assert not path_obj.is_relative_to(runner_mod.PACKAGE_ROOT)
                assert any(path_obj.is_relative_to(root) for root in ext_roots)
            elif path_obj.is_relative_to(_REPO_ROOT):
                assert path_obj == runner_resolved

    def test_falsification_package_root_write_fence_live_key_fence_and_stub_substring_sensitivity(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """Negative control: package writes and keyless --live fail with rc=2; stub keys on 'gap='."""
        runner_mod = _get_runner_mod()

        # 1. Writing inside PACKAGE_ROOT is refused with exit code 2
        inside_target = runner_mod.PACKAGE_ROOT / "forbidden_run_output"
        rc_inside = runner_mod.main(["--condition", "hinted", "--output-dir", str(inside_target)])
        assert rc_inside == 2
        assert not inside_target.exists()
        assert "refusing to write inside the package directory" in capsys.readouterr().err

        # 2. --live without OPENROUTER_API_KEY fails with exit code 2 without opening a socket
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setattr(
            socket,
            "create_connection",
            lambda *a, **kw: (_ for _ in ()).throw(AssertionError("Socket opened")),
        )
        rc_live = runner_mod.main(
            [
                "--live",
                "--condition",
                "baseline",
                "--output-dir",
                str(tmp_path / "live_no_key"),
            ]
        )
        assert rc_live == 2
        assert "OPENROUTER_API_KEY" in capsys.readouterr().err

        # 3. OfflineStubClient checks literal substring "gap=" rather than running a model
        stub = runner_mod.OfflineStubClient()
        poisoned_inst = next(
            inst for inst in runner_mod.BENCHMARK_INSTANCES if "poisoned" in inst.task_id
        )
        hinted_prompt = runner_mod.format_prompt(poisoned_inst, "hinted")
        scratch_prompt = runner_mod.format_prompt(poisoned_inst, "scratchpad")

        assert "gap=" in hinted_prompt
        assert stub.complete(hinted_prompt)[0].startswith("VERDICT: CONTRADICTION")
        # Removing "gap=" from the hinted prompt flips the stub output to CONSISTENT
        assert stub.complete(hinted_prompt.replace("gap=", "residual="))[0] == "VERDICT: CONSISTENT"

        # Scratchpad contains "gap = " with spaces, so stub emits CONSISTENT unless compact "gap=" is injected
        assert "gap = " in scratch_prompt and "gap=" not in scratch_prompt
        assert stub.complete(scratch_prompt)[0] == "VERDICT: CONSISTENT"
        assert stub.complete(scratch_prompt.replace("gap = ", "gap="))[0].startswith(
            "VERDICT: CONTRADICTION"
        )
