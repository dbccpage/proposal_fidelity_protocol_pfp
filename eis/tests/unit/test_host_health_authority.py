"""PR #63 review, item 6: declared versus authenticated host-health records."""
from dataclasses import replace

import pytest

from eis.domain.guard_activation import ActivationRefusal, DangerSignalReceiptV1, DetectorHitRefV1
from eis.use_cases.two_signal_regulation import (
    HostHealthAuthority,
    HostHealthReceiptV1,
    evaluate_guard_activation,
)

SUBJECT = "sha256:" + "1" * 64
PROFILE = "sha256:" + "9" * 64
HIT = DetectorHitRefV1(hit_id="sha256:" + "a" * 64, spec_id="spec_test", failure_code="fail_test", subject_id=SUBJECT)
DANGER = DangerSignalReceiptV1(signal_kind="REPLAY_FAILURE", observer_id="HOST_CHECK", subject_id=SUBJECT,
                               evidence_digest="sha256:" + "b" * 64)


def activate(receipt, authority):
    return evaluate_guard_activation(PROFILE, HIT, DANGER, externally_admitted=True, suspended=False,
                                     host_health=receipt, authority=authority)


def test_issued_record_authenticates_once():
    authority = HostHealthAuthority()
    receipt = authority.issue(observer_id="HOST_WATCHDOG", status="HEALTHY", subject_id=SUBJECT, profile_digest=PROFILE)
    activate(receipt, authority)
    with pytest.raises(ActivationRefusal) as replay:
        activate(receipt, authority)
    assert replay.value.code == "HOST_HEALTH_UNVERIFIED"


def test_caller_constructed_record_is_refused_under_an_authority():
    forged = HostHealthReceiptV1(observer_id="HOST_WATCHDOG", status="HEALTHY", subject_id=SUBJECT,
                                 profile_digest=PROFILE, nonce="00" * 16, mac="ff" * 32)
    with pytest.raises(ActivationRefusal) as exc:
        activate(forged, HostHealthAuthority())
    assert exc.value.code == "HOST_HEALTH_UNVERIFIED"


def test_altered_or_foreign_record_is_refused():
    issuer, other = HostHealthAuthority(), HostHealthAuthority()
    receipt = issuer.issue(observer_id="HOST_WATCHDOG", status="UNHEALTHY", subject_id=SUBJECT, profile_digest=PROFILE)
    assert not issuer.authenticate(replace(receipt, status="HEALTHY"), consume=False)
    assert not other.authenticate(receipt, consume=False)


def test_digest_fields_must_be_canonical():
    with pytest.raises(ValueError):
        HostHealthReceiptV1(observer_id="HOST_WATCHDOG", status="HEALTHY", subject_id="sha256:anything",
                            profile_digest=PROFILE)


def test_malformed_mac_or_nonce_is_refused_not_raised():
    """PR #66 follow-up review: a non-hex or non-ASCII mac, or a non-string/empty nonce, must
    fail authentication rather than raise out of hmac.compare_digest or the membership test."""
    authority = HostHealthAuthority()
    good = authority.issue(observer_id="HOST_WATCHDOG", status="HEALTHY", subject_id=SUBJECT, profile_digest=PROFILE)
    assert authority.authenticate(replace(good, mac="z" * 64), consume=False) is False
    assert authority.authenticate(replace(good, mac="ÿ" * 64), consume=False) is False
    assert authority.authenticate(replace(good, nonce=12345), consume=False) is False
    assert authority.authenticate(replace(good, nonce=""), consume=False) is False
    # The real record still authenticates: the guards reject only the malformed ones.
    assert authority.authenticate(good, consume=False) is True


def test_a_transient_downstream_refusal_does_not_spend_the_nonce():
    """PR #66 follow-up review: the single-use nonce is spent only after activation proceeds, so
    a caller-side mismatch does not burn a valid receipt and a corrected retry still activates."""
    authority = HostHealthAuthority()
    receipt = authority.issue(observer_id="HOST_WATCHDOG", status="HEALTHY", subject_id=SUBJECT, profile_digest=PROFILE)
    other_subject = "sha256:" + "2" * 64
    wrong_hit = replace(HIT, subject_id=other_subject)
    with pytest.raises(ActivationRefusal) as mismatch:
        evaluate_guard_activation(PROFILE, wrong_hit, DANGER, externally_admitted=True, suspended=False,
                                  host_health=receipt, authority=authority)
    assert mismatch.value.code == "SUBJECT_MISMATCH"
    # The nonce survived the transient refusal: the corrected call authenticates and activates,
    # and only then is the nonce consumed, so a replay is refused.
    activate(receipt, authority)
    with pytest.raises(ActivationRefusal) as replay:
        activate(receipt, authority)
    assert replay.value.code == "HOST_HEALTH_UNVERIFIED"
