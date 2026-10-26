"""Production-bound finite checker controls; no model or provider is involved."""

import hashlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from omega_engine_pfp.domain.aggregates.code_change_attestation import (
    ASSUMPTIONS_SHA256,
    SOURCE_ASSUMPTIONS,
)
from omega_engine_pfp.domain.exceptions import CanonicalizationError
from omega_engine_pfp.ffi import RustSymbolGameHost, find_omega_symbol_game_binary
from omega_engine_pfp.infrastructure import code_change_checker
from omega_engine_pfp.infrastructure.code_change_checker import (
    NativeCheckerTrust,
    SourceBoundCodeChangeChecker,
)
from omega_engine_pfp.use_cases.code_change import (
    CreateCodeChangeProposalUseCase,
    SubmitPatchCandidateUseCase,
)


@pytest.fixture(scope="module")
def trust():
    binary = find_omega_symbol_game_binary()
    return NativeCheckerTrust(
        binary_path=binary,
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
    )


def _session(*, candidate_budget=4, revision="a" * 40):
    return CreateCodeChangeProposalUseCase().execute(
        task_id="source-bound-finite",
        objective="Change the finite example",
        base_revision=revision,
        owned_paths=("src/x.py",),
        protected_paths=("README.md",),
        candidate_budget=candidate_budget,
    )


def _bound(session, *, path="src/x.py", value=1):
    _, bound = SubmitPatchCandidateUseCase().execute(
        session=session,
        producer_id="untrusted-model",
        patch_text=f"--- a/{path}\n+++ b/{path}\n@@ -1,1 +1,1 @@\n-x = 0\n+x = {value}\n",
    )
    return bound


def _checker(trust, *, session=None, source=b"x = 0\n", **kwargs):
    return SourceBoundCodeChangeChecker(
        session=session or _session(),
        run_id="finite-run",
        source_files=(("src/x.py", source),),
        trust=trust,
        **kwargs,
    )


def test_real_native_checker_returns_scoped_source_bound_result(trust):
    checker = _checker(trust)
    bound = _bound(_session())
    request = checker.prepare(bound, attempt_id="attempt-0")
    result = checker.check(request, bound).unwrap()

    assert result.diagnostic_status == "PASS"
    assert result.authorization_status == "HOST_CONFIGURED_CHECKER"
    assert result.authority_effect == "None"
    assert result.request.candidate_id == bound.candidate.candidate_id
    assert result.request.patch_sha256 == bound.patch.patch_sha256
    assert result.residual_obligations
    assert checker.native_calls == 3
    evidence = json.loads(result.evidence_json)
    assert [item["action"] for item in evidence] == [
        "create_code_change_proposal",
        "submit_patch_candidate",
        "evaluate_patch_gates",
    ]
    assert all(r["disposition"] == "PASS" for r in evidence[-1]["outcome"]["result"])
    assert result.request.assumptions_sha256 == ASSUMPTIONS_SHA256


def test_real_native_failure_is_retained_and_fresh_retry_uses_same_root_and_budget(trust):
    session = _session(candidate_budget=2)
    checker = _checker(trust, session=session, max_native_calls=5)
    rejected = _bound(session, path="README.md")
    first_request = checker.prepare(rejected, attempt_id="attempt-0")
    first = checker.check(first_request, rejected).unwrap()
    assert first.diagnostic_status == "FAIL"
    assert "gate_protected_FAILED" in first.refusal_codes
    assert "gate_ownership_FAILED" in first.refusal_codes

    repaired = _bound(session)
    second_request = checker.prepare(repaired, attempt_id="attempt-1")
    assert second_request.attempt_index == 1
    second = checker.check(second_request, repaired).unwrap()
    assert second.diagnostic_status == "PASS"
    assert checker.native_calls == 5
    first_submit = json.loads(first.evidence_json)[1]["outcome"]["result"]
    second_submit = json.loads(second.evidence_json)[0]["outcome"]["result"]
    assert (
        first_submit["run_root"]["task_packet_sha256"]
        == second_submit["run_root"]["task_packet_sha256"]
    )
    assert len(second_submit["run_root"]["candidate_ids"]) == 2
    assert second_submit["run_root_digest"] != first_submit["run_root_digest"]
    exhausted = checker.check(checker.prepare(repaired, attempt_id="attempt-2"), repaired)
    assert exhausted.unwrap_err().code == "CHECKER_BUDGET_EXHAUSTED"
    assert checker.native_calls == 5
    assert first.diagnostic_status == "FAIL"  # repair never rewrites the failed output


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("checker_id", "unknown-checker", "CHECKER_UNKNOWN"),
        ("source_sha256", "b" * 64, "CHECKER_BINDING_MISMATCH"),
        ("source_revision", "b" * 40, "CHECKER_BINDING_MISMATCH"),
        ("candidate_id", "b" * 64, "CHECKER_BINDING_MISMATCH"),
        ("patch_sha256", "b" * 64, "CHECKER_BINDING_MISMATCH"),
        ("assumptions_sha256", "b" * 64, "CHECKER_BINDING_MISMATCH"),
        ("run_id", "another-run", "CHECKER_BINDING_MISMATCH"),
        ("packet_id", "b" * 64, "CHECKER_BINDING_MISMATCH"),
    ],
)
def test_pre_dispatch_transplants_and_unknown_checker_refuse(trust, field, value, code):
    checker = _checker(trust)
    bound = _bound(_session())
    request = replace(checker.prepare(bound, attempt_id="attempt-0"), **{field: value})
    assert checker.check(request, bound).unwrap_err().code == code
    assert checker.native_calls == 0


def test_malformed_input_and_authority_are_refused_without_native_execution(trust):
    checker = _checker(trust)
    bound = _bound(_session())
    assert checker.check({}, bound).unwrap_err().code == "CHECKER_INPUT_MALFORMED"
    malformed_bound = replace(bound, candidate={"claimed_valid": True})
    request = checker.prepare(bound, attempt_id="attempt-0")
    assert checker.check(request, malformed_bound).unwrap_err().code == "CHECKER_INPUT_MALFORMED"
    tampered_bytes = replace(bound, patch_bytes=bound.patch_bytes + b"changed")
    assert checker.check(request, tampered_bytes).unwrap_err().code == "CHECKER_BINDING_MISMATCH"
    with pytest.raises(CanonicalizationError, match="AuthorityEffect"):
        replace(checker.prepare(bound, attempt_id="attempt-0"), authority_effect="Promote")
    with pytest.raises(CanonicalizationError, match="attempt_index"):
        replace(checker.prepare(bound, attempt_id="attempt-0"), attempt_index=True)
    with pytest.raises(CanonicalizationError, match="frozen lowercase Git"):
        replace(checker.prepare(bound, attempt_id="attempt-0"), source_revision="HEAD")
    assert checker.native_calls == 0


def test_candidate_transplant_cannot_reuse_a_real_accepted_result(trust):
    checker = _checker(trust)
    session = _session()
    bound = _bound(session)
    request = checker.prepare(bound, attempt_id="attempt-0")
    result = checker.check(request, bound).unwrap()
    changed = _bound(session, value=2)

    replay = checker.replay(result, request, changed)
    assert replay.is_err, "accepted evidence migrated to edited candidate bytes"
    assert replay.unwrap_err().code == "CHECKER_BINDING_MISMATCH"
    assert checker.native_calls == 3


def test_source_snapshot_transplant_is_refused_even_with_same_revision_label(trust):
    bound = _bound(_session())
    old = _checker(trust, source=b"x = 0\n")
    request = old.prepare(bound, attempt_id="attempt-0")
    result = old.check(request, bound).unwrap()
    changed = _checker(trust, source=b"x = 999\n")
    assert changed.replay(result, request, bound).unwrap_err().code == "CHECKER_BINDING_MISMATCH"
    assert changed.native_calls == 0


def test_stale_attempt_cannot_authorize_fresh_retry_and_real_replay_makes_zero_calls(
    trust, monkeypatch
):
    checker = _checker(trust)
    bound = _bound(_session())
    request = checker.prepare(bound, attempt_id="attempt-0")
    result = checker.check(request, bound).unwrap()
    fresh = checker.prepare(bound, attempt_id="attempt-1")
    assert checker.replay(result, fresh, bound).unwrap_err().code == "CHECKER_STALE_ATTEMPT"
    stale = replace(fresh, attempt_index=0)
    assert checker.check(stale, bound).unwrap_err().code == "CHECKER_STALE_ATTEMPT"

    def no_host(*args, **kwargs):
        raise AssertionError("replay attempted native/provider execution")

    monkeypatch.setattr(code_change_checker, "RustSymbolGameHost", no_host)
    assert checker.replay(result, request, bound).unwrap() == result
    assert checker.check(request, bound).unwrap() == result
    assert checker.native_calls == 3


def test_signer_name_digest_and_caller_rewritten_evidence_do_not_authenticate(trust):
    bound = _bound(_session())
    checker = _checker(trust)
    request = checker.prepare(bound, attempt_id="attempt-0")
    result = checker.check(request, bound).unwrap()
    forged = replace(result, evidence_json=b'[{"signer":"trusted","PASS":true}]')
    assert checker.replay(forged, request, bound).unwrap_err().code == "CHECKER_EVIDENCE_UNISSUED"
    another_host_run = _checker(trust)
    assert (
        another_host_run.replay(result, request, bound).unwrap_err().code
        == "CHECKER_EVIDENCE_UNISSUED"
    )
    with pytest.raises(FrozenInstanceError):
        result.authority_effect = "Promote"


def test_changed_or_unavailable_checker_pin_stops_before_execution(trust, tmp_path):
    bound = _bound(_session())
    checker = _checker(replace(trust, binary_sha256="b" * 64))
    assert (
        checker.check(checker.prepare(bound, attempt_id="attempt-0"), bound).unwrap_err().code
        == "CHECKER_PIN_MISMATCH"
    )
    missing = _checker(replace(trust, binary_path=tmp_path / "missing.exe"))
    assert (
        missing.check(missing.prepare(bound, attempt_id="attempt-0"), bound).unwrap_err().code
        == "CHECKER_UNAVAILABLE"
    )
    assert checker.native_calls == missing.native_calls == 0


def test_existing_native_gate_independently_rejects_patch_and_source_transplant(trust):
    bound = _bound(_session())
    checker = _checker(trust)
    result = checker.check(checker.prepare(bound, attempt_id="attempt-0"), bound).unwrap()
    submitted = json.loads(result.evidence_json)[1]["outcome"]["result"]
    root = submitted["run_root"]
    changed = dict(submitted["patch_artifact"])
    changed["patch_text"] = changed["patch_text"].replace("x = 1", "x = 2")
    changed["patch_sha256"] = hashlib.sha256(changed["patch_text"].encode()).hexdigest()
    host = RustSymbolGameHost(binary_path=trust.binary_path)
    rejected = host.evaluate_patch_gates(
        run_root=root,
        expected_task_packet_sha256=root["task_packet_sha256"],
        expected_run_root_digest=submitted["run_root_digest"],
        patch_artifact=changed,
    ).unwrap()
    assert rejected["success"] is False
    assert "REFUSAL_PATCH_NOT_BOUND" in rejected["error"]
    other_source = {**root, "payload": {**root["payload"], "source_revision": "b" * 40}}
    rejected_source = host.evaluate_patch_gates(
        run_root=other_source,
        expected_task_packet_sha256=root["task_packet_sha256"],
        expected_run_root_digest=submitted["run_root_digest"],
        patch_artifact=submitted["patch_artifact"],
    ).unwrap()
    assert rejected_source["success"] is False
    assert "REFUSAL_RUN_ROOT_BINDING_MISMATCH" in rejected_source["error"]


def test_operation_allowance_is_reserved_before_any_native_dispatch(trust):
    checker = _checker(trust, max_native_calls=2)
    bound = _bound(_session())
    assert (
        checker.check(checker.prepare(bound, attempt_id="attempt-0"), bound).unwrap_err().code
        == "CHECKER_BUDGET_EXHAUSTED"
    )
    assert checker.native_calls == 0


def test_pinned_source_map_is_interpretation_with_explicit_limits():
    assert len(SOURCE_ASSUMPTIONS) == 2
    assert "equilibrium" in SOURCE_ASSUMPTIONS[0][-1]
    assert "semantic correctness" in SOURCE_ASSUMPTIONS[1][-1]
    with pytest.raises(CanonicalizationError, match="assumption policy"):
        NativeCheckerTrust(
            binary_path="missing", binary_sha256="a" * 64, assumptions_sha256="b" * 64
        )
