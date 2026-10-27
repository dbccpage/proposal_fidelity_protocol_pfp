"""Integration parity between pure domain policies and native outer adapters."""

from __future__ import annotations

import pytest

from eis.domain.external_admission import (
    AntibodyObservationV1,
    ExternalAdmissionRequestV1,
    distinct_observations,
)
from eis.domain.guard_activation import (
    ActivationRefusal,
    DangerSignalReceiptV1,
    DetectorHitRefV1,
    evaluate_activation,
)
from eis.domain.provisional_promotion import (
    ObservationSupportPolicyV1,
    RawObservationV1,
)
from eis.infrastructure.native_domain import (
    NativeExternalAdmissionPolicy,
    NativeGuardActivationPolicy,
    NativeProvisionalPromotionPolicy,
    native_admission,
)


def digest(character: str) -> str:
    return "sha256:" + character * 64


def test_native_external_admission_adapter_matches_domain_distinctness() -> None:
    observations = tuple(
        AntibodyObservationV1(digest(character), "host", f"run-{index}")
        for index, character in enumerate("121")
    )

    assert distinct_observations(observations) == distinct_observations(
        observations, policy=NativeExternalAdmissionPolicy()
    )


def test_domain_request_identity_matches_native_parser() -> None:
    request = ExternalAdmissionRequestV1(
        candidate_digest=digest("a"),
        producer_system="farm",
        source_manifest_digest=digest("b"),
        positive_fixture_digest=digest("c"),
        negative_fixture_digest=digest("d"),
    )

    native = native_admission("parse_request", payload=request.to_dict())

    assert native["request_id"] == request.request_id


def test_native_guard_adapter_matches_domain_receipt() -> None:
    hit = DetectorHitRefV1(digest("1"), "spec", "FAILURE", digest("2"))
    danger = DangerSignalReceiptV1("REPLAY_FAILURE", "host", digest("2"), digest("3"))
    arguments = {
        "profile_digest": digest("4"),
        "hit": hit,
        "danger": danger,
        "externally_admitted": True,
        "suspended": False,
    }

    assert evaluate_activation(**arguments) == evaluate_activation(
        **arguments, policy=NativeGuardActivationPolicy()
    )


def test_native_guard_adapter_matches_collapse_refusal() -> None:
    hit = DetectorHitRefV1(digest("1"), "spec", "FAILURE", digest("2"))
    danger = DangerSignalReceiptV1("REPLAY_FAILURE", "host", digest("2"), hit.hit_id)
    arguments = {
        "profile_digest": digest("4"),
        "hit": hit,
        "danger": danger,
        "externally_admitted": True,
        "suspended": False,
    }

    with pytest.raises(ActivationRefusal) as pure:
        evaluate_activation(**arguments)
    with pytest.raises(ActivationRefusal) as native:
        evaluate_activation(**arguments, policy=NativeGuardActivationPolicy())

    assert native.value.code == pure.value.code == "TWO_SIGNAL_COLLAPSE"


def test_native_support_adapter_matches_domain_exact_mis() -> None:
    observations = (
        RawObservationV1("one", generating_model_id="shared"),
        RawObservationV1("two", generating_model_id="shared"),
        RawObservationV1("three", scaffold_digest="independent"),
        RawObservationV1("four", precedent_set_digest="also-independent"),
    )

    assert ObservationSupportPolicyV1().compute_support(observations) == ObservationSupportPolicyV1(
        policy=NativeProvisionalPromotionPolicy()
    ).compute_support(observations)
