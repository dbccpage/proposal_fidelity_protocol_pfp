"""Falsifier and specification tests for Part A: Spine & Adversary.

Covers:
- F-ADVERSARY-01: Act VII diagnostic containment (AuthorityEffect: None).
- F-ADVERSARY-02: Honest terminalization with gate_status=NOT_RUN on preflight refusal.
- F-BIO-01: Duty separation at actor and subject level (ROLE_SEPARATION_REQUIRED).
- F-BIO-02: Kinetic proofreading: no retry-until-pass (STAGE_REENTRY_REFUSED).
- F-RES-01: Judge stability under order swap (JUDGE_ORDER_UNSTABLE).
- F-RES-02: Novella renderer removal leaves host records byte-identical.
- F-RES-08: Per-seat timeout isolation without stalling scheduler.
- F-RES-10: Ingress limits enforced before invocation; reply limit bounded capture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from adversary.infrastructure.native import DefaultNativeOperationPort


def test_validate_swarm_composition_refuses_invalid_ancestry() -> None:
    """Adversary owns its ancestry requirement; the city remains a generic runtime."""
    from adversary.domain.circuit import (
        validate_adversary_swarm_composition,
    )
    from adversary.stage.domain.topology import SwarmCompositionV1

    # Missing Adversary ancestry
    comp_missing_adversary = SwarmCompositionV1(
        swarm_ancestry=["core.generic.swarm.v1"],
        required_skills=["/adversary"],
        runtime="core.adversary.runtime.v1",
        operating_system="core.oeos.host.v1",
        llm_protocol="core.symbol_game.protocol.v2",
        authority_effect="None",
    )
    with pytest.raises(ValueError, match="ADVERSARY_INHERITANCE_REQUIRED"):
        validate_adversary_swarm_composition(comp_missing_adversary)

    # Missing Adversary skill
    comp_missing_skill = SwarmCompositionV1(
        swarm_ancestry=["core.adversary.swarm.v1"],
        required_skills=["/general_assistant"],
        runtime="core.adversary.runtime.v1",
        operating_system="core.oeos.host.v1",
        llm_protocol="core.symbol_game.protocol.v2",
        authority_effect="None",
    )
    with pytest.raises(ValueError, match="ADVERSARY_SKILL_REQUIRED"):
        validate_adversary_swarm_composition(comp_missing_skill)

    # Missing the city runtime
    comp_missing_runtime = SwarmCompositionV1(
        swarm_ancestry=["core.adversary.swarm.v1"],
        required_skills=["/adversary"],
        runtime="core.legacy.runtime.v0",
        operating_system="core.oeos.host.v1",
        llm_protocol="core.symbol_game.protocol.v2",
        authority_effect="None",
    )
    with pytest.raises(ValueError, match="ADVERSARY_RUNTIME_REQUIRED"):
        validate_adversary_swarm_composition(comp_missing_runtime)

    # Missing OEOS host
    comp_missing_host = SwarmCompositionV1(
        swarm_ancestry=["core.adversary.swarm.v1"],
        required_skills=["/adversary"],
        runtime="core.adversary.runtime.v1",
        operating_system="bare_metal",
        llm_protocol="core.symbol_game.protocol.v2",
        authority_effect="None",
    )
    with pytest.raises(ValueError, match="OEOS_HOST_REQUIRED"):
        validate_adversary_swarm_composition(comp_missing_host)

    # Valid composition passes
    valid_comp = SwarmCompositionV1(
        swarm_ancestry=["core.adversary.swarm.v1"],
        required_skills=["/adversary"],
        runtime="core.adversary.runtime.v1",
        operating_system="core.oeos.host.v1",
        llm_protocol="core.symbol_game.protocol.v2",
        authority_effect="None",
    )
    assert validate_adversary_swarm_composition(valid_comp) is True


@pytest.mark.parametrize(
    ("field", "value", "refusal"),
    [
        ("swarm_ancestry", (), "ADVERSARY_INHERITANCE_REQUIRED"),
        ("swarm_ancestry", ("core.generic.swarm.v1",), "ADVERSARY_INHERITANCE_REQUIRED"),
        ("swarm_ancestry", "core.adversary.swarm.v1", "ADVERSARY_INHERITANCE_REQUIRED"),
        ("required_skills", (), "ADVERSARY_SKILL_REQUIRED"),
        ("required_skills", "/adversary", "ADVERSARY_SKILL_REQUIRED"),
        ("runtime", "other-runtime", "ADVERSARY_RUNTIME_REQUIRED"),
        ("operating_system", "bare_metal", "OEOS_HOST_REQUIRED"),
        ("llm_protocol", "", "SYMBOL_GAME_PROTOCOL_REQUIRED"),
        ("llm_protocol", "other-protocol", "SYMBOL_GAME_PROTOCOL_REQUIRED"),
        ("authority_effect", "AUTHORIZED", "AUTHORITY_EFFECT_FORBIDDEN"),
    ],
)
def test_adversary_composition_refuses_before_runtime_construction(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object, refusal: str
) -> None:
    from dataclasses import replace

    from operating_system.adapters import oeos_host
    from adversary import runtime as adversary_runtime
    from adversary.domain.circuit import ADVERSARY_SWARM_COMPOSITION_V1

    calls: list[str] = []

    def forbid_construction(*args: object, **kwargs: object) -> None:
        calls.append("construction")
        raise AssertionError("invalid composition reached an adapter factory")

    monkeypatch.setattr(adversary_runtime, "resolve_intelligence_repo_root", forbid_construction)
    monkeypatch.setattr(adversary_runtime, "load_adversary_council_profile", forbid_construction)
    monkeypatch.setattr(adversary_runtime, "DeterministicSchedulerV1", forbid_construction)
    monkeypatch.setattr(oeos_host, "OeosHostAdapter", forbid_construction)
    invalid = replace(ADVERSARY_SWARM_COMPOSITION_V1, **{field: value})
    # Adversary's composition root is the only one; OEOS no longer composes Adversary.
    with pytest.raises(ValueError, match=f"^{refusal}:"):
        adversary_runtime.build_adversary_runtime(composition=invalid)
    assert calls == []


def test_f_adversary_01_act_vii_authorization_is_non_operative_diagnostic() -> None:
    """F-ADVERSARY-01: Act VII authorization is non-operative diagnostic data.

    Attempting to consume Act VII AUTHORIZED as operational authority or fitness
    credit is refused or counted as zero.
    """
    from operating_system.adapters.prompt_civ.fitness import (
        PromptFitnessCalculatorV1,
    )
    from adversary.domain.circuit import AdversaryGateReceiptV1

    receipt = AdversaryGateReceiptV1(
        run_id="run-001",
        profile_digest="profile-sha256",
        input_packet_digest="in-sha256",
        output_packet_digest="out-sha256",
        gate_status="AUTHORIZED",
        open_residuals=[],
        authority_effect="None",
    )
    assert receipt.authority_effect == "None"

    # Prompt civ fitness must refuse or strictly ignore Act VII AUTHORIZED as task success
    calculator = PromptFitnessCalculatorV1()
    credit = calculator.extract_success_credit(receipt)
    assert credit == 0, "Act VII AUTHORIZED must never grant success credit to prompt fitness"


def test_f_adversary_02_terminalization_contract_honest_failure() -> None:
    """F-ADVERSARY-02: Preflight refusal and execution failure terminate with gate_status=NOT_RUN.

    They cannot masquerade as completed gated runs.
    """
    from adversary.domain.circuit import AdversarySevenActCircuit
    from adversary.stage.application.swarm_runtime import execute_circuit

    circuit = AdversarySevenActCircuit(fail_preflight=True, refusal_code="MISSING_CONFIGURATION")
    gate_receipt = execute_circuit(circuit)

    assert gate_receipt.gate_status == "NOT_RUN"
    assert gate_receipt.refusal_code == "MISSING_CONFIGURATION"
    assert gate_receipt.is_completed_gated_run is False


def test_f_adversary_02_a_packet_without_an_acts_runner_cannot_complete() -> None:
    from adversary.domain.circuit import AdversarySevenActCircuit
    from adversary.stage.application.swarm_runtime import execute_circuit

    circuit = AdversarySevenActCircuit(input_packet={"candidate": "unexecuted"})
    for receipt in (circuit.execute(), execute_circuit(circuit)):
        assert receipt.gate_status == "NOT_RUN"
        assert receipt.refusal_code == "ACTS_RUNNER_REQUIRED"
        assert receipt.is_completed_gated_run is False
        assert receipt.output_packet_digest == ""
        assert receipt.authority_effect == "None"


@pytest.mark.parametrize("failure", ["execution", "async_cancel", "future_cancel", "interrupt"])
def test_f_adversary_02_execution_failure_and_cancellation_never_complete(failure: str) -> None:
    from asyncio import CancelledError as AsyncCancelledError
    from concurrent.futures import CancelledError as FutureCancelledError

    from adversary.domain.circuit import AdversarySevenActCircuit
    from adversary.stage.application.swarm_runtime import execute_circuit

    exceptions = {
        "execution": RuntimeError,
        "async_cancel": AsyncCancelledError,
        "future_cancel": FutureCancelledError,
        "interrupt": KeyboardInterrupt,
    }
    calls: list[str] = []

    def fail_acts(packet: object, profile: object, run_id: str) -> None:
        calls.append(run_id)
        raise exceptions[failure]("deliberate failure")

    receipt = execute_circuit(
        AdversarySevenActCircuit(
            run_id="failed-run", input_packet={"candidate": "x"}, acts_runner=fail_acts
        )
    )
    assert calls == ["failed-run"]
    assert receipt.run_id == "failed-run"
    assert receipt.gate_status == "NOT_RUN"
    expected = "EXECUTION_FAILED" if failure == "execution" else "OPERATOR_CANCELLED"
    assert receipt.refusal_code == expected
    assert receipt.is_completed_gated_run is False
    assert receipt.authority_effect == "None"


def test_generic_circuit_failure_terminalizes_without_a_adversary_receipt_factory() -> None:
    from adversary.stage.application.swarm_runtime import execute_circuit

    class FailedCircuit:
        run_id = "generic-failure"

        def execute(self) -> None:
            raise RuntimeError("failed generic execution")

    receipt = execute_circuit(FailedCircuit())
    assert receipt["run_id"] == "generic-failure"
    assert receipt["gate_status"] == "NOT_RUN"
    assert receipt["refusal_code"] == "EXECUTION_FAILED"
    assert receipt["is_completed_gated_run"] is False
    assert receipt["authority_effect"] == "None"


def test_f_bio_01_duty_separation_at_actor_and_subject_level() -> None:
    """F-BIO-01: Propose actor may not hold Adjudicate for the same subject.

    Two seats backed by the same model lineage count as one actor.
    """
    from adversary.stage.domain.duties import (
        ActorDutyReceiptV1,
        DutyType,
        DutyValidatorV1,
    )

    validator = DutyValidatorV1()
    subject_digest = "sha256:subject_math_proof_123"

    # Actor A proposes
    r1 = ActorDutyReceiptV1(
        actor_id="seat_act_1_model_alpha",
        model_lineage_digest="lineage_gpt_4o_v1",
        duty=DutyType.PROPOSE,
        subject_digest=subject_digest,
        run_id="run-42",
    )
    validator.register_duty(r1)

    # Same actor (or same model lineage) attempting to adjudicate the same subject must be refused
    r2_same_lineage = ActorDutyReceiptV1(
        actor_id="seat_act_4_model_alpha_alt",
        model_lineage_digest="lineage_gpt_4o_v1",  # Same lineage!
        duty=DutyType.ADJUDICATE,
        subject_digest=subject_digest,
        run_id="run-42",
    )
    with pytest.raises(PermissionError, match="ROLE_SEPARATION_REQUIRED"):
        validator.validate_duty_assignment(r2_same_lineage)

    # Distinct actor with different lineage can adjudicate
    r2_distinct = ActorDutyReceiptV1(
        actor_id="seat_act_4_model_beta",
        model_lineage_digest="lineage_claude_3_5_sonnet_v1",
        duty=DutyType.ADJUDICATE,
        subject_digest=subject_digest,
        run_id="run-42",
    )
    assert validator.validate_duty_assignment(r2_distinct) is True


def test_f_bio_02_kinetic_proofreading_no_retry_until_pass() -> None:
    """F-BIO-02: A candidate digest marked REJECTED cannot be re-evaluated by the same frozen set.

    Only INCONCLUSIVE may retry within the declared budget.
    """
    from pfp.gate import (
        CandidateEvaluationGateV1,
        EvaluationDisposition,
    )

    gate = CandidateEvaluationGateV1(frozen_checker_set_id="checker_set_gen_1")
    candidate_digest = "sha256:candidate_packet_77"

    # Stage rejects candidate
    gate.record_verdict(candidate_digest, EvaluationDisposition.REJECTED)

    # Re-submission of the identical candidate to the same frozen checker set in the same generation is refused
    with pytest.raises(PermissionError, match="STAGE_REENTRY_REFUSED"):
        gate.evaluate_candidate(candidate_digest)


def test_f_res_01_judges_stable_under_order_swap() -> None:
    """F-RES-01: Judges are rerun with order swapped; order sensitivity raises JUDGE_ORDER_UNSTABLE."""
    from adversary.domain.circuit import (
        DebateJudgePairV1,
        OrderSensitivityDetectorV1,
    )

    judge_pair = DebateJudgePairV1()
    proposal_a = "Candidate Argument A"
    proposal_b = "Candidate Argument B"

    # Forward evaluation picks A
    forward_verdict = judge_pair.evaluate(first=proposal_a, second=proposal_b)
    assert forward_verdict.winner == "A"

    # Swapped evaluation picks B (meaning judge is biased by order rather than truth)
    swapped_verdict = judge_pair.evaluate(first=proposal_b, second=proposal_a)

    detector = OrderSensitivityDetectorV1()
    result = detector.verify_order_invariance(forward_verdict, swapped_verdict)
    assert result.stable is False
    assert result.diagnostic_code == "JUDGE_ORDER_UNSTABLE"


def test_f_res_02_renderer_removal_leaves_host_records_byte_identical() -> None:
    """F-RES-02: Adversary gate is deterministic host logic, not persona judgment.

    Removing the novella renderer leaves host records byte-identical.
    """
    from adversary.domain.circuit import AdversaryExecutionEngineV1

    engine = AdversaryExecutionEngineV1()
    run_context = {"objective": "factor integer 15", "seed": 42}

    record_with_novella = engine.execute_run(run_context, enable_novella_renderer=True)
    record_without_novella = engine.execute_run(run_context, enable_novella_renderer=False)

    # Host gate receipt and event hashes must be byte-identical
    assert record_with_novella.gate_receipt_digest == record_without_novella.gate_receipt_digest
    assert record_with_novella.host_records_digest == record_without_novella.host_records_digest


def test_f_res_08_seat_timeout_is_per_seat_isolation() -> None:
    """F-RES-08: A seat timeout produces a typed per-seat refusal and does not stall other seats."""
    from adversary.stage.application.swarm_scheduler import SwarmSchedulerV1

    scheduler = SwarmSchedulerV1()
    seats = [
        {"seat_id": "seat_1", "action": "fast_compute"},
        {"seat_id": "seat_2", "action": "infinite_timeout"},
        {"seat_id": "seat_3", "action": "fast_compute"},
    ]

    results = scheduler.execute_parallel_seats(seats, timeout_per_seat_ms=50)

    assert results["seat_1"].status == "COMPLETED"
    assert results["seat_2"].status == "REFUSED"
    assert results["seat_2"].refusal_code == "SEAT_TIMEOUT"
    assert results["seat_3"].status == "COMPLETED"
    assert scheduler.is_stalled is False


def test_f_res_10_ingress_and_reply_limits() -> None:
    """F-RES-10: Ingress limits apply before invocation (0 provider calls).

    1 MiB reply limit captured to CAS + truncation marker then raises REPLY_LIMIT_EXCEEDED.
    """
    from operating_system.adapters.packet_seat import (
        PacketSeatAdapterV1,
        ProviderCallSpy,
    )

    spy = ProviderCallSpy()
    adapter = PacketSeatAdapterV1(provider_gateway=spy)

    # 1. Oversized body (>64 KiB)
    oversized_body = "x" * (65 * 1024)
    with pytest.raises(ValueError, match="REQUEST_BODY_LIMIT_EXCEEDED"):
        adapter.prepare_and_send(body=oversized_body)
    assert spy.call_count == 0, "Provider must not be called when request body exceeds 64 KiB"

    # 2. Oversized field (>16 KiB)
    oversized_field = {"field": "y" * (17 * 1024)}
    with pytest.raises(ValueError, match="REQUEST_FIELD_LIMIT_EXCEEDED"):
        adapter.prepare_and_send(fields=oversized_field)
    assert spy.call_count == 0, "Provider must not be called when request field exceeds 16 KiB"

    # 3. Oversized reply (>1 MiB)
    spy.mock_reply_size = 2 * 1024 * 1024  # 2 MiB reply
    with pytest.raises(RuntimeError, match="REPLY_LIMIT_EXCEEDED"):
        adapter.prepare_and_send(body="valid small request")

    # CAS must have captured the bounded response up to limit with truncation marker
    cas_record = adapter.get_last_captured_cas_record()
    assert cas_record.truncated is True
    assert cas_record.truncation_marker == "REPLY_TRUNCATED_AT_1MIB"
    assert len(cas_record.bytes) <= 1024 * 1024 + 128


def test_e2e_authenticated_oeos_host_adversary_bout(tmp_path: Path) -> None:
    """A REFUSED OEOS host stops the bout before the acts.

    The host parses the request and returns status REFUSED. That Result is
    kept. The gate receipt is NOT_RUN, the seven acts are not written, and
    the authorization audit entry is not recorded.
    """
    import hashlib
    import json

    from operating_system.adapters.oeos_host import (
        OeosHostAdapter,
    )
    from operating_system.adapters.packet_seat import (
        PacketSeatAdapterV1,
        ProviderCallSpy,
    )
    from adversary.domain.circuit import (
        AdversaryGateReceiptV1,
        AdversarySevenActCircuit,
    )
    from adversary.runtime import build_adversary_runtime
    from adversary.stage.application.swarm_runtime import execute_circuit
    from adversary.stage.domain import WorkPacketV1
    from adversary.use_cases.bout_service import (
        create_adversary_circuit_runner,
    )

    # 1. Instantiate OEOS host adapter with audit log tracking
    host_adapter = OeosHostAdapter(host_id="oeos-host-test")
    out_dir = tmp_path / "_intelligence"

    # 2. Build Adversary runtime with injected OEOS host adapter in fixture mode
    rt = build_adversary_runtime(
        output_dir=out_dir,
        fixture_mode=True,
        host=host_adapter,
    )
    assert rt.host is host_adapter

    # 3. Create mock WorkPacketV1 fixture
    epoch_id = "sha256:" + hashlib.sha256(b"e2e_authenticated_bout_epoch").hexdigest()
    packet = WorkPacketV1(
        task_key="task_e2e_authenticated_adversary_bout",
        scene_id="act1_perception",
        objective="Verify end-to-end multi-act bout through OEOS host adapter",
        input_artifact_refs=(),
        acceptance_criteria=("Execute all 7 acts and produce gate receipt",),
        budget_units=50,
        evaluator_epoch_id=epoch_id,
    )

    # 4. Wire AdversarySevenActCircuit with create_adversary_circuit_runner
    circuit = AdversarySevenActCircuit(
        run_id=packet.task_key,
        input_packet=packet,
        profile=rt.profile,
        acts_runner=create_adversary_circuit_runner(
            rt,
            output_dir=out_dir / "_adversary",
            fixture_seats=True,
        native_support=DefaultNativeOperationPort()),
    )

    # 5. Execute circuit through OEADVERSARY execute_circuit seam
    gate_receipt = execute_circuit(circuit)

    assert type(gate_receipt) is AdversaryGateReceiptV1
    assert gate_receipt.run_id == packet.task_key
    assert gate_receipt.is_completed_gated_run is False
    assert gate_receipt.authority_effect == "None"
    assert gate_receipt.gate_status == "NOT_RUN"
    assert gate_receipt.refusal_code == "HOST_REQUEST_REFUSED"

    assert len(host_adapter.audit_log) == 1
    start_entry = host_adapter.audit_log[0]
    assert start_entry["request"]["action"] == "bout_start"
    assert start_entry["request"]["task_key"] == packet.task_key
    assert start_entry["response"]["status"] == "REFUSED"
    assert start_entry["response"]["reason"] == "request was parsed and not admitted"
    assert start_entry["response"]["authority_effect"] == "None"
    assert all(
        entry["request"]["action"] != "gate_authorization_record"
        for entry in host_adapter.audit_log
    )
    assert not (out_dir / "_adversary" / "runs" / packet.task_key).exists()

    # Seat replay stays independent of the refused bout.
    spy = ProviderCallSpy()
    seat = PacketSeatAdapterV1(provider_gateway=spy, storage_dir=tmp_path / "turns")
    seat.execute_turn(body="E2E Mock Prompt Query", turn_id="turn_e2e_01")
    assert spy.call_count == 1
    seat.replay_projections_from_log(turn_id="turn_e2e_01")
    assert spy.call_count == 1, "Replaying projections must make zero additional provider calls"
