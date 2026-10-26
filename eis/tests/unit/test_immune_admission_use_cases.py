"""Use cases around the moved EPIC-002 and PHARMACY-001 domain modules.

`activate_learned_guard` obtains the second signal from a host sensor run on
the subject bytes and the admission state from a port, so neither can be a
caller-supplied boolean. `assess_antibody` computes eligibility only.
"""

from __future__ import annotations

import json

import pytest

from omega_engine_epistemic_immune_system.domain.external_admission import (
    AdmissionError,
    AntibodyObservationV1,
)
from omega_engine_epistemic_immune_system.domain.guard_activation import (
    ActivationRefusal,
    DetectorHitRefV1,
)
from omega_engine_epistemic_immune_system.infrastructure.mssn_ports import (
    HostPayloadDangerSensor,
    NullDangerSensor,
)
from omega_engine_epistemic_immune_system.tests.auth_support import health
from omega_engine_epistemic_immune_system.use_cases.antibody_admission import assess_antibody
from omega_engine_epistemic_immune_system.use_cases.guard_activation import (
    activate_learned_guard,
    subject_digest,
)

PROFILE = "sha256:" + "b" * 64
CONTENT = json.dumps({"verified": True, "phi1": "0"}, sort_keys=True)


def digest(character: str) -> str:
    return "sha256:" + character * 64


class GuardState:
    def __init__(self, admitted: bool, suspended: bool = False) -> None:
        self.admitted, self.suspended = admitted, suspended

    def is_externally_admitted(self, spec_id: str, subject_scope: str) -> bool:
        return self.admitted

    def is_suspended(self, spec_id: str, subject_scope: str) -> bool:
        return self.suspended


def hit_for(content: str) -> DetectorHitRefV1:
    return DetectorHitRefV1(
        hit_id=digest("c"),
        spec_id="spec_alpha",
        failure_code="code_beta",
        subject_id=subject_digest(content),
    )


def test_a_host_observed_protected_field_activates_the_guard() -> None:
    receipt = activate_learned_guard(
        PROFILE,
        "spec_alpha",
        hit_for(CONTENT),
        CONTENT,
        subject_scope="scope_one",
        sensor=HostPayloadDangerSensor(),
        guard_state=GuardState(admitted=True),
        host_health=health(),
    )
    assert receipt.disposition == "FINDING"
    assert "PROTECTED_FIELD_VIOLATION" in receipt.independence_basis


def test_a_clean_payload_gives_no_danger_signal() -> None:
    clean = json.dumps({"candidate": "x"})
    with pytest.raises(ActivationRefusal) as caught:
        activate_learned_guard(
            PROFILE,
            "spec_alpha",
            hit_for(clean),
            clean,
            subject_scope="scope_one",
            sensor=HostPayloadDangerSensor(),
            guard_state=GuardState(admitted=True),
        )
    assert caught.value.code == "NO_DANGER_SIGNAL"


def test_prose_with_no_host_check_cannot_activate() -> None:
    with pytest.raises(ActivationRefusal) as caught:
        activate_learned_guard(
            PROFILE,
            "spec_alpha",
            hit_for("prose"),
            "prose",
            subject_scope="scope_one",
            sensor=NullDangerSensor(),
            guard_state=GuardState(admitted=True),
        )
    assert caught.value.code == "NO_DANGER_SIGNAL"


def test_admission_and_suspension_come_from_the_port() -> None:
    for state, code in ((GuardState(False), "NOT_EXTERNALLY_ADMITTED"), (GuardState(True, True), "SUSPENDED")):
        with pytest.raises(ActivationRefusal) as caught:
            activate_learned_guard(
                PROFILE,
                "spec_alpha",
                hit_for(CONTENT),
                CONTENT,
                subject_scope="scope_one",
                sensor=HostPayloadDangerSensor(),
                guard_state=state,
            )
        assert caught.value.code == code


def test_a_hit_about_other_bytes_is_a_subject_mismatch() -> None:
    with pytest.raises(ActivationRefusal) as caught:
        activate_learned_guard(
            PROFILE,
            "spec_alpha",
            hit_for("other bytes"),
            CONTENT,
            subject_scope="scope_one",
            sensor=HostPayloadDangerSensor(),
            guard_state=GuardState(admitted=True),
        )
    assert caught.value.code == "SUBJECT_MISMATCH"


def test_a_hit_of_another_guard_is_refused() -> None:
    with pytest.raises(ValueError, match="guard being activated"):
        activate_learned_guard(
            PROFILE,
            "spec_other",
            hit_for(CONTENT),
            CONTENT,
            subject_scope="scope_one",
            sensor=HostPayloadDangerSensor(),
            guard_state=GuardState(admitted=True),
        )


class Ledger:
    def __init__(self, observations: tuple[AntibodyObservationV1, ...]) -> None:
        self.observations = observations

    def observations_for(self, candidate_digest: str) -> tuple[AntibodyObservationV1, ...]:
        return self.observations


PAYLOAD = {
    "candidate_digest": digest("a"),
    "producer_system": "ooutwire_seeder",
    "source_manifest_digest": digest("b"),
    "positive_fixture_digest": digest("c"),
    "negative_fixture_digest": digest("d"),
}


def test_ten_replays_are_one_observation_and_not_eligible() -> None:
    replays = tuple(
        AntibodyObservationV1(observation_digest=digest("1"), observer_id="host", run_id=f"run_{i}")
        for i in range(10)
    )
    report = assess_antibody(PAYLOAD, ledger=Ledger(replays), required_distinct=2)
    assert report["observation_records"] == 10
    assert report["distinct_observations"] == [digest("1")]
    assert report["eligible_for_external_review"] is False
    assert report["status"] == "CANDIDATE"


def test_two_distinct_observations_are_eligible_but_stay_candidate() -> None:
    pair = tuple(
        AntibodyObservationV1(observation_digest=digest(c), observer_id="host", run_id="run")
        for c in "12"
    )
    report = assess_antibody(PAYLOAD, ledger=Ledger(pair), required_distinct=2)
    assert report["eligible_for_external_review"] is True
    assert report["status"] == "CANDIDATE"
    assert report["AuthorityEffect"] == "None"


def test_a_payload_missing_a_fixture_digest_is_refused() -> None:
    payload = dict(PAYLOAD)
    del payload["negative_fixture_digest"]
    with pytest.raises(AdmissionError) as caught:
        assess_antibody(payload, ledger=Ledger(()), required_distinct=2)
    assert caught.value.code == "MISSING_BINDING"
