"""Real Python-sign/Rust-verify and persisted admission/recovery controls."""

import pytest

from eis.domain.external_admission import AdmissionError
from eis.infrastructure.authenticated_custody import (
    AuthenticatedEisLedger,
    NativeAttestationVerifier,
)
from eis.tests.auth_support import (
    NOW,
    RULE,
    binding,
    digest,
    policy,
    signed,
    signing_bytes,
)
from operads.infrastructure.storage.receipt_ledger import (
    GENESIS_DIGEST,
    ReceiptLedger,
)


@pytest.fixture
def custody(tmp_path):
    ledger = ReceiptLedger(str(tmp_path / "eis.sqlite3"))
    clock = [NOW]
    verifier = NativeAttestationVerifier(policy(), clock=lambda: clock[0])
    store = AuthenticatedEisLedger(
        ledger, verifier, binding(), pinned_tip=GENESIS_DIGEST, rule_bytes=RULE
    )
    yield store, ledger, clock, verifier
    ledger.close()


def test_real_signature_and_persisted_admission(custody):
    store, ledger, _, verifier = custody
    assert store.admission_status()["status"] == "CANDIDATE"
    decision = signed()
    expected = digest(signing_bytes(decision["attestation"]))
    assert verifier.verify(decision, binding(), "admission")["statement_digest"] == expected
    tip = store.apply_decision(decision)
    assert store.admission_status()["previous_event"] == expected
    assert store.is_externally_admitted("spec_alpha", "scope_one")
    reopened = AuthenticatedEisLedger(ledger, verifier, binding(), pinned_tip=tip, rule_bytes=RULE)
    assert reopened.admission_status()["status"] == "ADMITTED"
    assert len(ledger) == 1


@pytest.mark.parametrize(
    "field",
    ["spec_id", "scope", "rule_digest", "source_digest", "subject_digest", "context_digest"],
)
def test_every_signed_binding_field_is_checked_before_writing(custody, field):
    store, ledger, _, _ = custody
    wrong = binding()
    wrong[field] = "foreign" if field in ("spec_id", "scope") else digest(b"foreign")
    with pytest.raises(AdmissionError, match="EIS_AUTH_BINDING_MISMATCH"):
        store.apply_decision(signed(expected=wrong))
    assert len(ledger) == 0 and store.pinned_tip == GENESIS_DIGEST


@pytest.mark.parametrize(
    "mutation",
    [
        "signature",
        "evidence",
        "issuer",
        "clock_boolean",
        "future",
        "expired",
        "lifetime",
        "schema",
        "extra_field",
    ],
)
def test_invalid_decisions_never_append(custody, mutation):
    store, ledger, clock, _ = custody
    decision = signed()
    if mutation == "signature":
        decision["attestation"]["signature_hex"] = "00" * 64
    elif mutation == "evidence":
        decision["evidence_hex"] = b"transplant".hex()
    elif mutation == "issuer":
        decision["attestation"]["issuer"] = "model"
    elif mutation == "clock_boolean":
        clock[0] = True
    elif mutation == "future":
        clock[0] = NOW - 1
    elif mutation == "expired":
        clock[0] = NOW + 50
    elif mutation == "lifetime":
        decision["attestation"]["expires_at"] = NOW + 101
    elif mutation == "schema":
        decision["attestation"]["schema_version"] = "different.v1"
    else:
        decision["attestation"]["admitted"] = True
    with pytest.raises(AdmissionError):
        store.apply_decision(decision)
    assert len(ledger) == 0 and store.pinned_tip == GENESIS_DIGEST


def test_suspension_fresh_reinstatement_revocation_and_replay(custody):
    store, ledger, clock, _ = custody
    first = signed()
    store.apply_decision(first)
    with pytest.raises(AdmissionError, match="REPLAY_OR_CHAIN"):
        store.apply_decision(first)
    clock[0] = 110
    second = signed(
        outcome="SUSPEND",
        event="decision-2",
        issued=110,
        previous=store.admission_status()["previous_event"],
    )
    store.apply_decision(second)
    assert store.is_suspended("spec_alpha", "scope_one")
    assert not store.is_externally_admitted("spec_alpha", "scope_one")
    previous = store.admission_status()["previous_event"]
    clock[0] = 170
    with pytest.raises(AdmissionError, match="EXPIRED_OR_FUTURE"):
        store.admission_status()
    third = signed(outcome="REINSTATE", event="decision-3", issued=170, previous=previous)
    store.apply_decision(third)
    assert store.is_externally_admitted("spec_alpha", "scope_one")
    clock[0] = 180
    store.apply_decision(
        signed(
            outcome="REVOKE",
            event="decision-4",
            issued=180,
            previous=store.admission_status()["previous_event"],
        )
    )
    assert store.admission_status()["status"] == "REVOKED"
    with pytest.raises(AdmissionError, match="INVALID_TRANSITION"):
        store.apply_decision(
            signed(
                outcome="REINSTATE",
                event="decision-5",
                issued=180,
                previous=store.admission_status()["previous_event"],
            )
        )
    assert len(ledger) == 4


def test_revoked_key_and_changed_rule_refuse_readback(custody):
    store, ledger, _, _ = custody
    tip = store.apply_decision(signed())
    revoked = policy()
    revoked["keys"][0]["revoked"] = True
    verifier = NativeAttestationVerifier(revoked, clock=lambda: NOW)
    restored = AuthenticatedEisLedger(ledger, verifier, binding(), pinned_tip=tip, rule_bytes=RULE)
    with pytest.raises(AdmissionError, match="SIGNER_NOT_AUTHORIZED"):
        restored.admission_status()
    with pytest.raises(AdmissionError, match="RULE_MISMATCH"):
        AuthenticatedEisLedger(
            ledger, verifier, binding(), pinned_tip=tip, rule_bytes=b"changed rule"
        )
    assert len(ledger) == 1


def test_external_pin_detects_missing_tail_even_after_chain_recalculation(custody):
    store, ledger, _, verifier = custody
    pin = store.apply_decision(signed())
    # Model whole-database replacement. The independent old pin is retained.
    with ReceiptLedger() as replaced:
        with pytest.raises(AdmissionError, match="LEDGER_INCOMPLETE"):
            AuthenticatedEisLedger(replaced, verifier, binding(), pinned_tip=pin, rule_bytes=RULE)
    assert len(ledger) == 1


def test_trust_policy_is_snapshotted_and_empty_policy_refuses(custody):
    _, _, _, _ = custody
    root = policy()
    verifier = NativeAttestationVerifier(root, clock=lambda: NOW)
    root["keys"].clear()
    assert verifier.verify(signed(), binding(), "admission")["outcome"] == "ADMIT"
    with pytest.raises(AdmissionError, match="TRUST_UNCONFIGURED"):
        NativeAttestationVerifier(root, clock=lambda: NOW).verify(signed(), binding(), "admission")
