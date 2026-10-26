"""Integration, parity, and adversarial mutation tests for the isolated Python-to-Rust FFI seam.

AuthorityEffect: None (const).
"""

from __future__ import annotations

import pytest

from omega_engine_operating_system.adapters.rust_host.ffi import (
    RUNTIME_OUTCOME_SCHEMA,
)
from omega_engine_operations.domain.rop.result import Ok
from omega_engine_pfp.ffi import get_default_host


def _outcome(crossing, action: str, *, success: bool = True):
    """Retain the complete native outcome before inspecting its inner result."""
    assert isinstance(crossing, Ok), crossing
    outcome = crossing.value
    assert set(outcome) == {
        "schema_version",
        "action",
        "success",
        "result",
        "error",
        "authority_effect",
    }
    assert outcome["schema_version"] == RUNTIME_OUTCOME_SCHEMA
    assert outcome["action"] == action
    assert outcome["success"] is success
    assert outcome["authority_effect"] == "None"
    if success:
        assert outcome["error"] is None
    else:
        assert outcome["result"] is None
        assert isinstance(outcome["error"], str)
    return outcome


def test_ffi_binary_discovery():
    host = get_default_host()
    assert host.binary_path.is_file()


def test_ffi_canonical_wire_and_digest():
    host = get_default_host()
    sample = {"zebra": 1, "apple": 2}
    wire_outcome = _outcome(host.canonical_wire(sample), "canonical_wire")
    wire = wire_outcome["result"]
    assert wire[0] == "omega-canonical-v1"
    assert wire[1] == "mapping"

    json_outcome = _outcome(host.canonical_json(sample), "canonical_json")
    canon_json = json_outcome["result"]
    assert "apple" in canon_json
    assert "zebra" in canon_json

    digest_outcome = _outcome(
        host.domain_digest("test.domain", sample), "domain_digest"
    )
    digest = digest_outcome["result"]
    assert len(digest) == 64


def test_ffi_null_wire_roundtrip_retains_native_outcomes():
    host = get_default_host()
    wire_outcome = _outcome(host.canonical_wire(None), "canonical_wire")
    null_outcome = _outcome(
        host.canonical_unwire(wire_outcome["result"]), "canonical_unwire"
    )
    assert null_outcome["result"] == wire_outcome["result"]
    assert null_outcome["result"] == ["omega-canonical-v1", "null", None]
    assert null_outcome["success"] is True


def test_ffi_finite_float_transport_retains_the_action_owned_refusal():
    host = get_default_host()
    outcome = _outcome(
        host.canonical_wire({"value": 1.25}), "canonical_wire", success=False
    )
    # This is the native action's current message, not an OEOS mathematical
    # judgment that the finite input is itself nonfinite.
    assert outcome["error"] == "non-finite floats are not canonical"


def test_ffi_parse_unified_diff_and_gates():
    host = get_default_host()
    patch = """--- a/src/lib.rs
+++ b/src/lib.rs
@@ -1,1 +1,1 @@
-old
+new
"""
    diff_outcome = _outcome(host.parse_unified_diff(patch), "parse_unified_diff")
    diff_res = diff_outcome["result"]
    assert diff_res["is_valid"] is True
    assert diff_res["touched_paths"] == ["src/lib.rs"]

    # Create proposal
    proposal_crossing = host.create_code_change_proposal(
        task_id="task_py_ffi_01",
        objective="Refactor parser via Rust FFI",
        base_revision="HEAD",
        owned_paths=["src/lib.rs"],
        protected_paths=[".canon"],
        candidate_budget=3,
        operation_budget=10,
    )
    proposal_outcome = _outcome(proposal_crossing, "create_code_change_proposal")
    run_root = proposal_outcome["result"]
    assert run_root["task_id"] == "task_py_ffi_01"
    assert run_root["authority_effect"] == "None"

    # Submit patch
    submit_crossing = host.submit_patch_candidate(
        run_root=run_root,
        expected_task_packet_sha256=run_root["task_packet_sha256"],
        candidate_id="cand_py_01",
        producer_id="py_agent",
        patch_text=patch,
    )
    submit_outcome = _outcome(submit_crossing, "submit_patch_candidate")
    submit_res = submit_outcome["result"]
    updated_root = submit_res["run_root"]
    patch_art = submit_res["patch_artifact"]
    assert "cand_py_01" in updated_root["candidate_ids"]

    # Evaluate gates
    gates_crossing = host.evaluate_patch_gates(
        run_root=updated_root,
        expected_task_packet_sha256=updated_root["task_packet_sha256"],
        expected_run_root_digest=submit_res["run_root_digest"],
        patch_artifact=patch_art,
    )
    gates_outcome = _outcome(gates_crossing, "evaluate_patch_gates")
    receipts = gates_outcome["result"]
    assert len(receipts) == 3
    assert all(r["disposition"] == "PASS" for r in receipts)


def test_ffi_gauge_board_classification():
    host = get_default_host()
    d0 = {
        "rows": 3,
        "cols": 3,
        "data": [
            True,
            False,
            False,
            False,
            True,
            False,
            False,
            False,
            True,
        ],
    }
    d1 = {
        "rows": 1,
        "cols": 3,
        "data": [False, False, False],
    }
    cochain = [True, False, False]
    gauge_outcome = _outcome(
        host.classify_gauge_board(d0, d1, cochain), "classify_gauge_board"
    )
    verdict = gauge_outcome["result"]
    assert "GaugeExact" in verdict


def test_ffi_scoring_and_ranking():
    host = get_default_host()
    obs = ["obs_1", "obs_2", "obs_3"]
    p1 = {
        "proposal_id": "p1",
        "repaired_obstruction_ids": ["obs_1"],
        "cochain_delta": [],
        "structural_cost": "1",
        "kill_triggers": [],
        "admitted_constructors_used": [],
        "dual_witness_ref": None,
        "authority_effect": "None",
    }
    p2 = {
        "proposal_id": "p2",
        "repaired_obstruction_ids": ["obs_1", "obs_2", "obs_3"],
        "cochain_delta": [],
        "structural_cost": "1/2",
        "kill_triggers": [],
        "admitted_constructors_used": [],
        "dual_witness_ref": "dual_cert_42",
        "authority_effect": "None",
    }
    rank_outcome = _outcome(
        host.rank_candidate_proposals(obs, [p1, p2]), "rank_candidate_proposals"
    )
    ranked = rank_outcome["result"]
    assert len(ranked) == 2
    assert ranked[0]["proposal_id"] == "p2"
    assert ranked[0]["is_exact_candidate"] is True


# =========================================================================
# Mutation, Fuzzing, and Security Fail-Closed Refusal Tests
# =========================================================================


def test_ffi_mutation_invalid_action_refuses():
    host = get_default_host()
    outcome = _outcome(
        host.invoke("nonexistent_action_xyz", {}),
        "nonexistent_action_xyz",
        success=False,
    )
    assert "unsupported runtime action" in outcome["error"]


def test_ffi_mutation_empty_domain_refuses():
    host = get_default_host()
    outcome = _outcome(
        host.domain_digest("", {"test": 123}), "domain_digest", success=False
    )
    assert "digest domain must be non-empty" in outcome["error"]


@pytest.mark.parametrize(
    "bad_path",
    [
        "../escape.rs",
        "sub/../../secret.rs",
        "path\\with\\backslashes.rs",
        "/absolute/root.rs",
        "C:/Windows/System32.rs",
        "src//double_slash.rs",
        "src/trailing_dot./mod.rs",
        "src/CON/mod.rs",
        "src/NUL.rs",
        "src/AUX/data.rs",
        "src/COM1/port.rs",
        "src/LPT1/printer.rs",
    ],
)
def test_ffi_mutation_path_traversal_attacks_fail_closed(bad_path: str):
    host = get_default_host()
    malicious_patch = f"""--- a/{bad_path}
+++ b/{bad_path}
@@ -1,1 +1,1 @@
-old
+new
"""
    parse_outcome = _outcome(
        host.parse_unified_diff(malicious_patch), "parse_unified_diff"
    )
    res = parse_outcome["result"]
    assert res["is_valid"] is False
    assert (
        "forbidden" in res["error_message"].lower()
        or "unsafe" in res["error_message"].lower()
        or "reserved" in res["error_message"].lower()
    )


def test_ffi_mutation_budget_exhaustion_refuses():
    host = get_default_host()
    patch = """--- a/src/lib.rs
+++ b/src/lib.rs
@@ -1,1 +1,1 @@
-old
+new
"""
    # Create proposal with budget = 1
    proposal_crossing = host.create_code_change_proposal(
        task_id="task_budget_01",
        objective="Budget test",
        base_revision="HEAD",
        owned_paths=["src/lib.rs"],
        protected_paths=[],
        candidate_budget=1,
        operation_budget=10,
    )
    proposal_outcome = _outcome(proposal_crossing, "create_code_change_proposal")
    run_root = proposal_outcome["result"]
    # First submit succeeds
    first_crossing = host.submit_patch_candidate(
        run_root=run_root,
        expected_task_packet_sha256=run_root["task_packet_sha256"],
        candidate_id="cand_01",
        producer_id="agent_1",
        patch_text=patch,
    )
    first_outcome = _outcome(first_crossing, "submit_patch_candidate")
    res1 = first_outcome["result"]
    updated_root = res1["run_root"]

    # Second submit must fail closed with budget exhausted
    second_crossing = host.submit_patch_candidate(
        run_root=updated_root,
        expected_task_packet_sha256=updated_root["task_packet_sha256"],
        candidate_id="cand_02",
        producer_id="agent_1",
        patch_text=patch,
    )
    second_outcome = _outcome(second_crossing, "submit_patch_candidate", success=False)
    assert "exhausted" in second_outcome["error"]


def test_ffi_mutation_protected_paths_gate_fails():
    host = get_default_host()
    patch = """--- a/.canon/rules.yaml
+++ b/.canon/rules.yaml
@@ -1,1 +1,1 @@
-old
+new
"""
    proposal_crossing = host.create_code_change_proposal(
        task_id="task_prot_01",
        objective="Security test",
        base_revision="HEAD",
        owned_paths=[".canon/rules.yaml", "src/lib.rs"],
        protected_paths=[".canon"],
        candidate_budget=3,
        operation_budget=10,
    )
    proposal_outcome = _outcome(proposal_crossing, "create_code_change_proposal")
    run_root = proposal_outcome["result"]
    submit_crossing = host.submit_patch_candidate(
        run_root=run_root,
        expected_task_packet_sha256=run_root["task_packet_sha256"],
        candidate_id="cand_prot_01",
        producer_id="attacker_agent",
        patch_text=patch,
    )
    submit_outcome = _outcome(submit_crossing, "submit_patch_candidate")
    submit_res = submit_outcome["result"]
    gates_crossing = host.evaluate_patch_gates(
        run_root=submit_res["run_root"],
        expected_task_packet_sha256=submit_res["run_root"]["task_packet_sha256"],
        expected_run_root_digest=submit_res["run_root_digest"],
        patch_artifact=submit_res["patch_artifact"],
    )
    gates_outcome = _outcome(gates_crossing, "evaluate_patch_gates")
    receipts = gates_outcome["result"]
    prot_receipt = next(r for r in receipts if r["gate_name"] == "gate_protected")
    assert prot_receipt["disposition"] == "FAIL"
    assert "REFUSAL_PROTECTED_FILE_PATCHED" in prot_receipt["message"]


def test_ffi_mutation_gauge_board_chain_law_violation():
    host = get_default_host()
    # D1 * D0 != 0
    d0 = {
        "rows": 2,
        "cols": 2,
        "data": [True, False, False, True],
    }
    d1 = {
        "rows": 2,
        "cols": 2,
        "data": [True, False, False, True],
    }
    cochain = [True, True]
    gauge_outcome = _outcome(
        host.classify_gauge_board(d0, d1, cochain), "classify_gauge_board"
    )
    verdict = gauge_outcome["result"]
    assert "BoardInvalid" in verdict


def test_ffi_mutation_gauge_board_local_curvature():
    host = get_default_host()
    # Triangle board with curvature
    d0 = {
        "rows": 3,
        "cols": 3,
        "data": [
            True,
            True,
            False,
            False,
            True,
            True,
            True,
            False,
            True,
        ],
    }
    d1 = {
        "rows": 1,
        "cols": 3,
        "data": [True, True, True],
    }
    # a has curvature
    cochain = [True, False, False]
    gauge_outcome = _outcome(
        host.classify_gauge_board(d0, d1, cochain), "classify_gauge_board"
    )
    verdict = gauge_outcome["result"]
    assert "LocalCurvature" in verdict
    assert verdict["LocalCurvature"]["syndrome"] == [True]


def test_ffi_mutation_gauge_board_global_obstruction():
    host = get_default_host()
    # Torus 1-cycle: D1 * a = 0, but a is not in im(D0)
    d0 = {
        "rows": 3,
        "cols": 1,
        "data": [False, False, False],
    }
    d1 = {
        "rows": 1,
        "cols": 3,
        "data": [False, False, False],
    }
    cochain = [True, False, False]
    gauge_outcome = _outcome(
        host.classify_gauge_board(d0, d1, cochain), "classify_gauge_board"
    )
    verdict = gauge_outcome["result"]
    assert "GlobalH1Obstruction" in verdict
    assert verdict["GlobalH1Obstruction"]["separator"] == [True, False, False]


def test_ffi_mutation_kill_condition_trigger():
    host = get_default_host()
    obs = ["obs_1"]
    p_killed = {
        "proposal_id": "p_kill",
        "repaired_obstruction_ids": ["obs_1"],
        "cochain_delta": [],
        "structural_cost": "1",
        "kill_triggers": ["F-01_inherited_meaning"],
        "admitted_constructors_used": [],
        "dual_witness_ref": None,
        "authority_effect": "None",
    }
    score_outcome = _outcome(
        host.score_discrete_proposal(obs, p_killed), "score_discrete_proposal"
    )
    res = score_outcome["result"]
    assert res["is_legal"] is False
    assert "KILL_TRIGGER" in res["refusal_reason"]


def test_ffi_mutation_illegal_authority_effect():
    host = get_default_host()
    obs = ["obs_1"]
    p_authoritative = {
        "proposal_id": "p_auth",
        "repaired_obstruction_ids": ["obs_1"],
        "cochain_delta": [],
        "structural_cost": "1",
        "kill_triggers": [],
        "admitted_constructors_used": [],
        "dual_witness_ref": None,
        "authority_effect": "PROMOTED_AUTHORITY",  # ILLEGAL
    }
    score_outcome = _outcome(
        host.score_discrete_proposal(obs, p_authoritative), "score_discrete_proposal"
    )
    res = score_outcome["result"]
    assert res["is_legal"] is False
    assert res["refusal_reason"] == "AUTHORITY_EFFECT_NON_NONE"


def test_ffi_exact_linear_algebra_delegation():
    host = get_default_host()
    # 2x2 matrix: [[1, 2], [3, 4]] -> det = -2
    det_out = _outcome(
        host.exact_determinant([["1", "2"], ["3", "4"]]),
        "exact_determinant",
    )
    assert det_out["result"]["determinant"] == "-2"

    # Symmetric positive definite matrix: [[2, -1], [-1, 2]]
    spd_mat = [["2", "-1"], ["-1", "2"]]
    pd_out = _outcome(
        host.exact_is_positive_definite(spd_mat),
        "exact_is_positive_definite",
    )
    assert pd_out["result"]["is_positive_definite"] is True

    ldlt_out = _outcome(host.exact_ldlt(spd_mat), "exact_ldlt")
    assert ldlt_out["result"]["pivots"] == ["2", "3/2"]

    minors_out = _outcome(host.exact_leading_minors(spd_mat), "exact_leading_minors")
    assert minors_out["result"]["leading_minors"] == ["2", "3"]

    rank_out = _outcome(host.exact_rank([["1", "2"], ["2", "4"]]), "exact_rank")
    assert rank_out["result"]["rank"] == 1

    char_poly_out = _outcome(host.exact_char_poly([["1", "2"], ["3", "4"]]), "exact_char_poly")
    assert char_poly_out["result"]["coeffs"] == ["-2", "-5", "1"]


def test_ffi_code_change_malformed_protected_paths_is_a_typed_refusal():
    """Counterexample: ``protected_paths: ".canon"`` used to become ``[]``."""
    host = get_default_host()
    payload = {
        "task_id": "task_malformed",
        "objective": "Security test",
        "base_revision": "HEAD",
        "owned_paths": ["src/lib.rs"],
        "protected_paths": ".canon",
        "candidate_budget": 3,
        "operation_budget": 10,
        "required_gates": ["gate_ownership", "gate_syntax"],
    }
    outcome = _outcome(
        host.invoke("create_code_change_proposal", payload),
        "create_code_change_proposal",
        success=False,
    )
    assert outcome["error"].startswith("REFUSAL_CODE_CHANGE_REQUEST_INVALID:")


def test_ffi_code_change_run_root_edited_after_create_is_refused():
    """Counterexample: emptying a run root's protected paths turned the gate to PASS."""
    host = get_default_host()
    patch = "--- a/.canon/rules.yaml\n+++ b/.canon/rules.yaml\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    run_root = _outcome(
        host.create_code_change_proposal(
            task_id="task_bound",
            objective="Security test",
            base_revision="HEAD",
            owned_paths=["src/lib.rs"],
            protected_paths=[".canon"],
            candidate_budget=3,
            operation_budget=10,
        ),
        "create_code_change_proposal",
    )["result"]
    submitted = _outcome(
        host.submit_patch_candidate(
            run_root=run_root,
            expected_task_packet_sha256=run_root["task_packet_sha256"],
            candidate_id="c1",
            producer_id="p1",
            patch_text=patch,
        ),
        "submit_patch_candidate",
    )["result"]
    edited = dict(submitted["run_root"])
    edited["payload"] = dict(edited["payload"], protected_paths=[], owned_paths=[".canon", "src/lib.rs"])
    refused = _outcome(
        host.evaluate_patch_gates(
            run_root=edited,
            expected_task_packet_sha256=run_root["task_packet_sha256"],
            expected_run_root_digest=submitted["run_root_digest"],
            patch_artifact=submitted["patch_artifact"],
        ),
        "evaluate_patch_gates",
        success=False,
    )
    assert refused["error"].startswith("REFUSAL_RUN_ROOT_BINDING_MISMATCH:")


def test_ffi_code_change_swapped_patch_with_recomputed_digest_is_refused():
    """Forgery (b): swap the admitted bytes and recompute ``patch_sha256``.

    Before, the evaluator compared the artifact's digest with its own text and
    ran the gates on the swapped bytes.
    """
    import hashlib

    host = get_default_host()
    parser_patch = "--- a/src/lib.rs\n+++ b/src/lib.rs\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    canon_patch = "--- a/.canon/rules.yaml\n+++ b/.canon/rules.yaml\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    run_root = _outcome(
        host.create_code_change_proposal(
            task_id="task_swap",
            objective="Security test",
            base_revision="HEAD",
            owned_paths=["src/lib.rs"],
            protected_paths=[".canon"],
            candidate_budget=3,
            operation_budget=10,
        ),
        "create_code_change_proposal",
    )["result"]
    expected = run_root["task_packet_sha256"]
    submitted = _outcome(
        host.submit_patch_candidate(
            run_root=run_root,
            expected_task_packet_sha256=expected,
            candidate_id="c1",
            producer_id="p1",
            patch_text=parser_patch,
        ),
        "submit_patch_candidate",
    )["result"]
    swapped = dict(
        submitted["patch_artifact"],
        patch_text=canon_patch,
        patch_sha256=hashlib.sha256(canon_patch.encode("utf-8")).hexdigest(),
        byte_count=len(canon_patch.encode("utf-8")),
    )
    refused = _outcome(
        host.evaluate_patch_gates(
            run_root=submitted["run_root"],
            expected_task_packet_sha256=expected,
            expected_run_root_digest=submitted["run_root_digest"],
            patch_artifact=swapped,
        ),
        "evaluate_patch_gates",
        success=False,
    )
    assert refused["error"].startswith("REFUSAL_PATCH_NOT_BOUND:")
    honest = _outcome(
        host.evaluate_patch_gates(
            run_root=submitted["run_root"],
            expected_task_packet_sha256=expected,
            expected_run_root_digest=submitted["run_root_digest"],
            patch_artifact=submitted["patch_artifact"],
        ),
        "evaluate_patch_gates",
    )["result"]
    digest = hashlib.sha256(parser_patch.encode("utf-8")).hexdigest()
    assert all(receipt["patch_sha256"] == digest for receipt in honest)


def test_ffi_evaluate_refuses_a_rolling_digest_the_caller_does_not_hold():
    """Submit returns the rolling digest; evaluate refuses any other one.

    A root recomputed by someone else is internally consistent, so only the
    digest the caller kept from its own submit can reject it.
    """
    host = get_default_host()
    patch = "--- a/src/lib.rs\n+++ b/src/lib.rs\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    run_root = _outcome(
        host.create_code_change_proposal(
            task_id="task_rolling",
            objective="Security test",
            base_revision="HEAD",
            owned_paths=["src/lib.rs"],
            protected_paths=[".canon"],
            candidate_budget=3,
            operation_budget=10,
        ),
        "create_code_change_proposal",
    )["result"]
    expected = run_root["task_packet_sha256"]
    submitted = _outcome(
        host.submit_patch_candidate(
            run_root=run_root,
            expected_task_packet_sha256=expected,
            candidate_id="c1",
            producer_id="p1",
            patch_text=patch,
        ),
        "submit_patch_candidate",
    )["result"]
    held = submitted["run_root_digest"]
    assert held == submitted["run_root"]["run_root_digest"]
    assert held != expected
    refused = _outcome(
        host.evaluate_patch_gates(
            run_root=submitted["run_root"],
            expected_task_packet_sha256=expected,
            expected_run_root_digest=expected,
            patch_artifact=submitted["patch_artifact"],
        ),
        "evaluate_patch_gates",
        success=False,
    )
    assert refused["error"].startswith("REFUSAL_EXPECTED_RUN_ROOT_DIGEST_MISMATCH:")
