"""Host replay (stage 7) of the stage 6 witnesses decides the terminal. AuthorityEffect: None.

A host-accepted witness is an open obstruction, a wrong prediction is a discard,
and no model field is read as the run's terminal.
"""

import json

import pytest
from pydantic import ValidationError

from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPipelineFailure, PfpPipelineStep
from omega_engine_pfp.domain.kernel.result import RefusalCode, TerminalStatus
from omega_engine_pfp.domain.stages.host_stages import (
    admit_record,
    hand_off_record,
    receipt_record,
    selection_record,
)
from omega_engine_pfp.domain.stages.stages import (
    ChallengeReplay,
    ReplayOutcome,
    Stage5Response,
    Stage6Response,
    Stage8Response,
    WitnessReplay,
    replay_outcome,
)
from omega_engine_pfp.infrastructure.providers import (
    OfflineDeterministicPfpProvider,
    SeedHostVerifier,
)
from omega_engine_pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from omega_engine_pfp.use_cases.execute_stage_pipeline import ExecuteStagePipelineUseCase
from omega_engine_pfp.use_cases.pfp_stages import RunPfpPipelineUseCase

CANDIDATE = {"proposal": "the candidate"}


@pytest.mark.parametrize("expected,accepted,same,outcome", [
    (True, True, False, ReplayOutcome.OPEN_OBSTRUCTION),
    (False, True, False, ReplayOutcome.OPEN_OBSTRUCTION),
    (False, False, False, ReplayOutcome.CONTROL),
    (True, False, False, ReplayOutcome.DISCARDED),
    (True, True, True, ReplayOutcome.DISCARDED),
    (False, False, True, ReplayOutcome.DISCARDED),
])
def test_outcome_follows_host_facts_only(expected, accepted, same, outcome):
    assert replay_outcome(expected, accepted, same) is outcome
    witness = WitnessReplay(index=0, candidate_id="c", expected_accept=expected, host_accepted=accepted,
                            same_as_candidate=same, outcome=outcome)
    assert witness.prediction_matched is (expected is accepted)


def test_a_record_cannot_relabel_an_accepted_witness():
    with pytest.raises(ValidationError, match="REPLAY_OUTCOME_MISMATCH"):
        WitnessReplay(index=0, candidate_id="c", expected_accept=True, host_accepted=True,
                      same_as_candidate=False, outcome=ReplayOutcome.DISCARDED)
    with pytest.raises(ValidationError, match="REPLAY_INDEX_MISMATCH"):
        ChallengeReplay(demo_id="d", stage=6, witnesses=(WitnessReplay(
            index=1, candidate_id="c", expected_accept=False, host_accepted=False,
            same_as_candidate=False, outcome=ReplayOutcome.CONTROL),))


def test_fail_open_defaults_are_gone():
    with pytest.raises(ValidationError, match="challenges"):
        Stage6Response(demo_id="d", should_continue=True)
    with pytest.raises(ValidationError, match="disposition"):
        Stage8Response(demo_id="d")
    with pytest.raises(ValidationError, match="SELECTION_RECORD_MISMATCH"):
        Stage8Response(demo_id="d", disposition="SELECT", selected_candidate_id=None,
                       survivors=[], rule="STAGE5_SURVIVORS_LESS_STAGE7_OBSTRUCTIONS")
    record = Stage8Response(demo_id="d", disposition="SELECT", selected_candidate_id="c",
                            survivors=["c"], rule="STAGE5_SURVIVORS_LESS_STAGE7_OBSTRUCTIONS")
    assert record.seat == "seat_the_master" and "should_continue" not in record.model_dump()


class Graded(SeedHostVerifier):
    """The seed checker accepts exactly the proposals named in `accepted`."""

    def __init__(self, accepted, unavailable=False):
        super().__init__()
        self.accepted, self.unavailable = accepted, unavailable

    def _evaluate(self, demo_id, candidate):
        from omega_engine_pfp.infrastructure.pilot_runners.mssn_checks import GateResult
        reasons = ["CHECKER_UNAVAILABLE"] if self.unavailable else []
        if candidate["proposal"] not in self.accepted:
            reasons.append("REJECTED")
        return GateResult(seed_id=demo_id, passed=not reasons, failure_reasons=reasons)


def item(proposal, expected):
    return dict(candidate_id="c", claim="x", witness={"proposal": proposal}, expected_accept=expected,
                required_check="seed checker")


def test_seed_verifier_records_attacks_controls_and_discards_without_failing():
    items = [item("attack", True), item("guess", True), item("control", False),
             item("surprise", False), item("the candidate", True)]
    replay = Graded({"attack", "surprise", "the candidate"}).verify_challenges(
        "d", 6, items, {4: {"candidate_id": "c", "candidate": CANDIDATE}})
    assert [w.outcome for w in replay.witnesses] == [
        ReplayOutcome.OPEN_OBSTRUCTION, ReplayOutcome.DISCARDED, ReplayOutcome.CONTROL,
        ReplayOutcome.OPEN_OBSTRUCTION, ReplayOutcome.DISCARDED]
    assert replay.obstruction_indices == (0, 3)
    assert replay.checked_count == 4


def test_seed_verifier_fails_closed_when_the_checker_is_unavailable_or_the_candidate_is_missing():
    with pytest.raises(ValueError, match="CHALLENGE_CHECKER_UNAVAILABLE"):
        Graded(set(), unavailable=True).verify_challenges(
            "d", 6, [item("a", False)], {4: {"candidate": CANDIDATE}})
    with pytest.raises(ValueError, match="STAGE4_STRUCTURED_WITNESS_REQUIRED"):
        Graded(set()).verify_challenges("d", 6, [item("a", False)], {})


def replay_record(stage, outcomes):
    witnesses = []
    for index, outcome in enumerate(outcomes):
        expected, accepted = {"obstruction": (True, True), "control": (False, False),
                              "discard": (True, False)}[outcome]
        witnesses.append(WitnessReplay(index=index, candidate_id="c", expected_accept=expected,
                                       host_accepted=accepted, same_as_candidate=False,
                                       outcome=replay_outcome(expected, accepted, False)))
    return ChallengeReplay(demo_id="d", stage=stage, witnesses=tuple(witnesses)).model_dump(mode="json")


DECLARATION = {"grammar": "g", "equality_test": "e", "coefficient_profile": "c"}
STORAGE = PfpFileSystemStorageAdapter()
RULES = STORAGE.load_stage_file(9).obligation_rules
ROUTING = STORAGE.load_terminal_routing()
ALL = tuple(range(1, 12))


class Port:
    """Model turns are bare; stage 7 replays `outcomes`; the other host stages use the real rules."""

    def __init__(self, outcomes, declared=True):
        self.outcomes, self.declared = outcomes, declared
        self.calls = []

    def execute_model_stage(self, stage, prior):
        self.calls.append(stage)
        data = {"stage": stage, "demo_id": "d"}
        if stage == 4:
            data["candidate_id"] = "c"
        return PfpPipelineStep(data, True)

    def execute_host_stage(self, stage, prior):
        self.calls.append(stage)
        if stage == 1:
            repair = None if self.declared else {"admission_proposal": {
                **DECLARATION, "missing_declarations": [], "status": "admit"}}
            data = admit_record("d", DECLARATION if self.declared else None, repair)
        elif stage == 5:
            data = {"stage": 5, "demo_id": "d", "host_verdict": "PASS", "exact_checks_passed": True,
                    "surviving_candidates": ["c"]}
        elif stage == 7:
            data = {"stage": 7, "demo_id": "d", "host_replay": replay_record(6, self.outcomes)}
        elif stage == 8:
            data = selection_record("d", prior)
        elif stage == 9:
            data = receipt_record("d", prior, RULES)
        else:
            data = hand_off_record("d", prior[9], ROUTING)
        return PfpPipelineStep(data, True)


@pytest.mark.parametrize("outcomes,declared,terminal,disposition", [
    (("control",), True, "VERIFIED", "SELECT"),
    (("discard", "control"), True, "VERIFIED", "SELECT"),
    (("control",), False, "VERIFIED_WITH_RESIDUALS", "SELECT"),
    ((), True, "VERIFIED_WITH_RESIDUALS", "SELECT"),
    (("discard",), True, "VERIFIED", "SELECT"),
    (("control", "obstruction"), True, "OPEN_OBSTRUCTION", "REJECT"),
])
def test_terminal_is_computed_from_the_replay(outcomes, declared, terminal, disposition):
    port = Port(outcomes, declared)
    run = RunPfpPipelineUseCase().execute(ALL, port)
    assert run.terminal_status == terminal
    # An obstruction does not stop the run: the receipt names the terminal. The evidence plan
    # runs only when the receipt is not VERIFIED.
    assert port.calls == list(ALL if terminal != "VERIFIED" else ALL[:-1])
    assert run.stage_responses[8]["disposition"] == disposition
    assert run.stage_responses[10]["terminal"] == terminal
    assert run.all_stages_passed is (terminal != "OPEN_OBSTRUCTION")


def test_a_forged_replay_record_is_refused():
    class Forged(Port):
        def execute_host_stage(self, stage, prior):
            step = super().execute_host_stage(stage, prior)
            if stage == 7:
                step.data["host_replay"]["witnesses"][0]["outcome"] = "CONTROL"
            return step

    with pytest.raises(PfpPipelineFailure) as error:
        RunPfpPipelineUseCase().execute(ALL, Forged(("obstruction",)))
    assert error.value.code == "HOST_CHECK_FAILED" and error.value.stage == 7


class Attacker(OfflineDeterministicPfpProvider):
    """Canonical fixture stages, with one stage 6 witness the host will accept."""

    def __init__(self, expected):
        self.expected = expected

    def generate_candidate(self, packet, temperature=0.0):
        response = json.loads(super().generate_candidate(packet, temperature))
        if packet.stage == 6:
            selected = json.loads(packet.user)["prior_artifacts"]["4"]["candidate_id"]
            response["challenges"] = [dict(candidate_id=selected, claim="another proposal passes",
                                           witness={"proposal": "attack"}, expected_accept=self.expected,
                                           required_check="seed checker")]
        return json.dumps(response)


class AcceptingHost:
    def verify(self, demo_id, prior_responses):
        return Stage5Response(demo_id=demo_id, should_continue=True, host_verdict="PASS",
                              exact_checks_passed=True, surviving_candidates=[prior_responses[4]["candidate_id"]])

    def verify_challenges(self, demo_id, stage, items, prior_responses):
        return Graded({"attack"}).verify_challenges(demo_id, stage, items, prior_responses)


@pytest.mark.parametrize("expected", [True, False])
def test_canonical_pipeline_routes_an_accepted_witness_to_open_obstruction(expected):
    storage = PfpFileSystemStorageAdapter()
    owner = ExecuteStagePipelineUseCase(storage, Attacker(expected), catalog=storage,
                                        host_verifier=AcceptingHost())
    result = owner.run_pipeline("demo_000", {"raw_seed": "<>"})
    assert result.is_ok, result.error
    receipt = result.unwrap()
    assert receipt.final_terminal_status == TerminalStatus.OPEN_OBSTRUCTION
    # The obstruction is recorded and the run goes on: selection rejects, the receipt routes it.
    assert receipt.completed_stages == ALL
    assert receipt.stage_responses[8]["disposition"] == "REJECT"
    replay = ChallengeReplay.model_validate(receipt.stage_responses[7]["host_replay"])
    assert replay.obstruction_indices == (0,)
    assert replay.witnesses[0].prediction_matched is expected


def test_canonical_pipeline_refuses_witnesses_without_a_host_replay():
    class NoReplay(AcceptingHost):
        verify_challenges = None

    storage = PfpFileSystemStorageAdapter()
    owner = ExecuteStagePipelineUseCase(storage, Attacker(True), catalog=storage, host_verifier=NoReplay())
    result = owner.run_pipeline("demo_000", {"raw_seed": "<>"})
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert result.unwrap_err().stage == 7


def test_a_model_cannot_supply_its_own_host_replay():
    class Smuggler(Attacker):
        def generate_candidate(self, packet, temperature=0.0):
            response = json.loads(super().generate_candidate(packet, temperature))
            if packet.stage == 6:
                response["host_replay"] = replay_record(6, ("control",))
            return json.dumps(response)

    storage = PfpFileSystemStorageAdapter()
    owner = ExecuteStagePipelineUseCase(storage, Smuggler(True), catalog=storage,
                                        host_verifier=AcceptingHost())
    result = owner.run_pipeline("demo_000", {"raw_seed": "<>"})
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert result.unwrap_err().stage == 6
