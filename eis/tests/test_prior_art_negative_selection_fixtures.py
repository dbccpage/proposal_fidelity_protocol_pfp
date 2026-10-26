"""Finite fixture experiment through authenticated custody, never self-admission."""

import json
from dataclasses import asdict

import pytest

from omega_engine_epistemic_immune_system.domain.external_admission import AdmissionError
from omega_engine_epistemic_immune_system.domain.thymus import ThymusGate
from omega_engine_epistemic_immune_system.domain.value_objects import DetectorRule
from omega_engine_epistemic_immune_system.infrastructure.authenticated_custody import (
    AuthenticatedEisLedger,
    NativeAttestationVerifier,
)
from omega_engine_epistemic_immune_system.infrastructure.mssn_ports import PatternMatcher
from omega_engine_epistemic_immune_system.infrastructure.native_domain import native_admission
from omega_engine_epistemic_immune_system.tests.auth_support import (
    NOW,
    binding,
    digest,
    policy,
    signed,
)
from omega_engine_epistemic_immune_system.use_cases.antibody_admission import assess_antibody
from omega_engine_operads.infrastructure.storage.receipt_ledger import (
    GENESIS_DIGEST,
    ReceiptLedger,
)

HEALTHY = '{"schema_version":"fixture.receipt.v1","status":"OPEN_RESIDUAL"}'
DEFECT = "ACCEPTED"
RULE = DetectorRule(
    rule_id="fixture-detector", target_epitope="narrative receipt", match_pattern="^ACCEPTED$"
)
RULE_BYTES = json.dumps(asdict(RULE), sort_keys=True, separators=(",", ":")).encode()
RULE_BINDING = {
    **binding(),
    "rule_digest": digest(RULE_BYTES),
    "subject_digest": digest(RULE_BYTES),
}


@pytest.fixture
def experiment(tmp_path):
    request = native_admission(
        "parse_request",
        payload={
            "candidate_digest": digest(RULE_BYTES),
            "producer_system": "fixture-runner",
            "source_manifest_digest": binding()["source_digest"],
            "positive_fixture_digest": digest(DEFECT.encode()),
            "negative_fixture_digest": digest(HEALTHY.encode()),
        },
    )
    with ReceiptLedger(str(tmp_path / "observations.sqlite3")) as ledger:
        clock = [NOW]
        verifier = NativeAttestationVerifier(policy(), clock=lambda: clock[0])
        store = AuthenticatedEisLedger(
            ledger, verifier, RULE_BINDING, pinned_tip=GENESIS_DIGEST, rule_bytes=RULE_BYTES
        )
        expected = {**RULE_BINDING, "subject_digest": request["request_id"]}
        yield request, ledger, store, expected, clock


def test_finite_negative_selection_then_observations_still_require_external_admission(experiment):
    request, ledger, store, expected, _ = experiment
    matcher = PatternMatcher()
    rule = DetectorRule(**json.loads(RULE_BYTES))
    assert matcher.match_antigen(DEFECT, (rule,))
    assert not matcher.match_antigen(HEALTHY, (rule,))
    assert ThymusGate([HEALTHY]).evaluate_rule(rule, matcher).is_admitted
    # Local self-panel terminology does not grant operational admission.
    assert not ThymusGate([DEFECT]).evaluate_rule(rule, matcher).is_admitted
    first = signed("observation", "DEFECT_OBSERVED", "run-1", expected=expected)
    store.append_observation(request, first)
    view = store.observation_ledger(request)
    assert not assess_antibody(request, ledger=view, required_distinct=2)[
        "eligible_for_external_review"
    ]
    store.append_observation(
        request, signed("observation", "DEFECT_OBSERVED", "run-2", expected=expected)
    )
    report = assess_antibody(request, ledger=view, required_distinct=2)
    assert report["eligible_for_external_review"] and report["status"] == "CANDIDATE"
    assert report["AuthorityEffect"] == "None"
    assert store.admission_status()["status"] == "CANDIDATE"
    assert len(ledger) == 2


@pytest.mark.parametrize("case", ["forged", "narrative", "candidate", "fixture", "source"])
def test_malformed_or_transplanted_evidence_is_not_recorded(experiment, case):
    request, ledger, store, expected, _ = experiment
    if case in ("candidate", "fixture", "source"):
        expected[
            {"candidate": "rule_digest", "fixture": "subject_digest", "source": "source_digest"}[
                case
            ]
        ] = digest(b"foreign")
    report = signed(
        "observation",
        "DEFECT_OBSERVED",
        "run-1",
        expected=expected,
        raw=b"ACCEPTED" if case == "narrative" else None,
    )
    if case == "forged":
        report["attestation"]["signature_hex"] = "00" * 64
    with pytest.raises(AdmissionError):
        store.append_observation(request, report)
    assert len(ledger) == 0


def test_replay_and_changed_fixture_cannot_reuse_a_verified_view(experiment):
    request, ledger, store, expected, _ = experiment
    first = signed("observation", "DEFECT_OBSERVED", "run-1", expected=expected)
    store.append_observation(request, first)
    with pytest.raises(AdmissionError, match="REPLAY"):
        store.append_observation(request, first)
    # A new signature/event ID over identical observed bytes remains one observation.
    store.append_observation(
        request,
        signed(
            "observation",
            "DEFECT_OBSERVED",
            "run-2",
            expected=expected,
            raw=bytes.fromhex(first["evidence_hex"]),
        ),
    )
    view = store.observation_ledger(request)
    report = assess_antibody(request, ledger=view, required_distinct=2)
    assert len(report["distinct_observations"]) == 1
    assert not report["eligible_for_external_review"]
    changed = {k: v for k, v in request.items() if k != "request_id"}
    changed["negative_fixture_digest"] = digest(b"other healthy fixture")
    with pytest.raises(AdmissionError, match="BINDING_MISMATCH"):
        assess_antibody(changed, ledger=view, required_distinct=2)
    assert len(ledger) == 2


def test_expired_observations_stay_in_history_but_fresh_evidence_recovers_eligibility(experiment):
    request, ledger, store, expected, clock = experiment
    store.append_observation(
        request, signed("observation", "DEFECT_OBSERVED", "old", expected=expected)
    )
    old_tip = store.pinned_tip
    clock[0] = NOW + 50
    view = store.observation_ledger(request)
    report = assess_antibody(request, ledger=view, required_distinct=2)
    assert report["distinct_observations"] == []
    for event in ("fresh-1", "fresh-2"):
        store.append_observation(
            request,
            signed("observation", "DEFECT_OBSERVED", event, expected=expected, issued=clock[0]),
        )
    assert assess_antibody(request, ledger=view, required_distinct=2)[
        "eligible_for_external_review"
    ]
    assert len(ledger) == 3 and next(ledger.entries()).entry_digest == old_tip
    assert store.admission_status()["status"] == "CANDIDATE"
