"""Actual native activation must also have authenticated, current host health."""

import pytest

from omega_engine_epistemic_immune_system.domain.guard_activation import ActivationRefusal
from omega_engine_epistemic_immune_system.infrastructure.authenticated_custody import (
    AuthenticatedEisLedger,
    NativeAttestationVerifier,
    SignedHostHealth,
)
from omega_engine_epistemic_immune_system.infrastructure.mssn_ports import HostPayloadDangerSensor
from omega_engine_epistemic_immune_system.tests.auth_support import (
    NOW,
    RULE,
    binding,
    digest,
    policy,
    signed,
)
from omega_engine_epistemic_immune_system.tests.unit.test_immune_admission_use_cases import (
    CONTENT,
    PROFILE,
    GuardState,
    hit_for,
)
from omega_engine_epistemic_immune_system.use_cases.guard_activation import activate_learned_guard
from omega_engine_operads.infrastructure.storage.receipt_ledger import (
    GENESIS_DIGEST,
    ReceiptLedger,
)


def test_missing_host_health_cannot_activate_an_otherwise_admitted_guard():
    with pytest.raises(ActivationRefusal, match="HOST_HEALTH_UNAVAILABLE"):
        activate_learned_guard(
            PROFILE,
            "spec_alpha",
            hit_for(CONTENT),
            CONTENT,
            subject_scope="scope_one",
            sensor=HostPayloadDangerSensor(),
            guard_state=GuardState(admitted=True),
        )


@pytest.mark.parametrize(
    "case,code",
    [
        ("missing", "HOST_HEALTH_UNAVAILABLE"),
        ("missing_config", "HOST_HEALTH_UNVERIFIED"),
        ("unhealthy", "HOST_HEALTH_UNHEALTHY"),
        ("subject", "HOST_HEALTH_UNVERIFIED"),
        ("profile", "HOST_HEALTH_UNVERIFIED"),
        ("source", "HOST_HEALTH_UNVERIFIED"),
        ("forged", "HOST_HEALTH_UNVERIFIED"),
        ("narrative", "HOST_HEALTH_UNVERIFIED"),
        ("expired", "HOST_HEALTH_UNVERIFIED"),
        ("revoked", "HOST_HEALTH_UNVERIFIED"),
    ],
)
def test_real_activation_refuses_unusable_observer_reports(case, code):
    expected = {**binding(), "subject_digest": digest(CONTENT.encode())}
    if case in ("subject", "profile", "source"):
        field = {
            "subject": "subject_digest",
            "profile": "context_digest",
            "source": "source_digest",
        }[case]
        expected[field] = digest(b"foreign")
    report = signed(
        "health",
        "UNHEALTHY" if case == "unhealthy" else "HEALTHY",
        "health-1",
        expected=expected,
        raw=b"ACCEPTED" if case == "narrative" else None,
    )
    if case == "forged":
        report["attestation"]["signature_hex"] = "00" * 64
    trust = policy()
    if case == "revoked":
        trust["keys"][1]["revoked"] = True
    verifier = NativeAttestationVerifier(
        trust, clock=lambda: NOW + (50 if case == "expired" else 0)
    )
    configured = binding()
    if case == "missing_config":
        configured.pop("context_digest")
    host_health = SignedHostHealth(
        verifier, configured, lambda: None if case == "missing" else report
    )
    with pytest.raises(ActivationRefusal, match=code):
        activate_learned_guard(
            PROFILE,
            "spec_alpha",
            hit_for(CONTENT),
            CONTENT,
            subject_scope="scope_one",
            sensor=HostPayloadDangerSensor(),
            guard_state=GuardState(admitted=True),
            host_health=host_health,
        )


def test_persisted_signed_admission_and_fresh_health_are_both_required(tmp_path):
    clock = [NOW]
    verifier = NativeAttestationVerifier(policy(), clock=lambda: clock[0])
    expected = {**binding(), "subject_digest": digest(CONTENT.encode())}
    report = [signed("health", "HEALTHY", "health-1", expected=expected)]
    host_health = SignedHostHealth(verifier, binding(), lambda: report[0])
    with ReceiptLedger(str(tmp_path / "admission.sqlite3")) as ledger:
        store = AuthenticatedEisLedger(
            ledger, verifier, binding(), pinned_tip=GENESIS_DIGEST, rule_bytes=RULE
        )
        store.apply_decision(signed())

        def activate():
            return activate_learned_guard(
                PROFILE,
                "spec_alpha",
                hit_for(CONTENT),
                CONTENT,
                subject_scope="scope_one",
                sensor=HostPayloadDangerSensor(),
                guard_state=store,
                host_health=host_health,
            )

        assert activate().disposition == "FINDING"
        report[0] = signed("health", "UNHEALTHY", "health-2", expected=expected)
        with pytest.raises(ActivationRefusal, match="HOST_HEALTH_UNHEALTHY"):
            activate()
        clock[0] = 110
        report[0] = signed("health", "HEALTHY", "health-3", expected=expected, issued=110)
        assert activate().disposition == "FINDING"
        # Health recovery never changes the admission ledger or bypasses its suspension.
        store.apply_decision(
            signed(
                outcome="SUSPEND",
                event="suspend",
                issued=110,
                previous=store.admission_status()["previous_event"],
            )
        )
        with pytest.raises(ActivationRefusal, match="NOT_EXTERNALLY_ADMITTED|SUSPENDED"):
            activate()
        assert len(ledger) == 2
