"""The dual-signal activation law, and the collapse it exists to refuse.

`EPIC-OE-IMMUNE-002` states four conjuncts for activating a learned guard, then
names the way implementations get it wrong:

> An implementation must name which inputs are independent. Counting the same
> predicate twice, deriving the danger bit from the detector match, or accepting
> a model-authored danger flag is `TWO_SIGNAL_COLLAPSE`.

That is the difficulty worth testing. A two-signal rule is trivial to satisfy in
form and easy to satisfy *vacuously*: a guard that reads its own detector output
twice passes every conjunct while standing on one signal. Tests that only walk
the happy path and check "two things were present" would pass such an
implementation.

So the collapses are tested one by one, and each is a separate mistake:

1. the danger receipt's evidence is the detector's own finding digest;
2. the danger receipt's observer is the detector spec;
3. the danger receipt was authored by a model rather than observed by a host.

Every refusal is paired with a permitted case. A gate that refuses everything
satisfies every refusal test and proves nothing about what it admits.

Moved on 2026-09-29 with the implementation, from
`projects/ms_majorana/code/tests/unit/test_dual_signal_activation.py`.
The hit and profile are real OEWAS anti-skill V2 objects; the OEEIS domain
reads them through `DetectorHitRefV1` and the profile digest. The danger
registry gained MALFORMED_PAYLOAD, shared with the screening path.
"""

from __future__ import annotations

import pytest

from eis.domain.guard_activation import (
    ACTIVATION_DISPOSITIONS,
    DANGER_SIGNAL_KINDS,
    FORBIDDEN_DANGER_PRODUCERS,
    REFUSAL_CODES,
    ActivationRefusal,
    DangerSignalReceiptV1,
    DetectorHitRefV1,
    GuardActivationReceiptV1,
    evaluate_activation,
)
from operads.domain.anti_skills.anti_skill_v2 import (
    AntiSkillActivationProfileV1,
    AntiSkillHitV1,
)


def digest(character: str) -> str:
    return "sha256:" + character * 64


SUBJECT = digest("a")


def make_profile() -> AntiSkillActivationProfileV1:
    return AntiSkillActivationProfileV1(
        profile_id="profile_alpha",
        registry_id=digest("b"),
        active_spec_ids=("spec_alpha",),
        subject_scopes=("scope_one",),
    )


def make_hit(**overrides) -> DetectorHitRefV1:
    fields = {
        "spec_id": "spec_alpha",
        "failure_code": "code_beta",
        "disposition": "FINDING",
        "subject_id": SUBJECT,
        "protected_fields": ("subject_id",),
    }
    fields.update(overrides)
    return DetectorHitRefV1.from_hit(AntiSkillHitV1(**fields))


def make_danger(**overrides) -> DangerSignalReceiptV1:
    fields = {
        "signal_kind": "REPLAY_FAILURE",
        "observer_id": "host_replayer",
        "subject_id": SUBJECT,
        "evidence_digest": digest("c"),
    }
    fields.update(overrides)
    return DangerSignalReceiptV1(**fields)


def activate(**overrides):
    call = {
        "profile": make_profile(),
        "hit": make_hit(),
        "danger": make_danger(),
        "externally_admitted": True,
        "suspended": False,
    }
    call.update(overrides)
    return evaluate_activation(
        call["profile"].profile_digest,
        call["hit"],
        call["danger"],
        externally_admitted=call["externally_admitted"],
        suspended=call["suspended"],
        **{k: v for k, v in call.items()
           if k not in {"profile", "hit", "danger", "externally_admitted", "suspended"}},
    )


# --------------------------------------------------------------------------
# The law admits
# --------------------------------------------------------------------------


def test_two_independent_signals_activate_the_guard():
    """The permitted case. Without it every refusal below proves nothing."""
    receipt = activate()
    assert isinstance(receipt, GuardActivationReceiptV1)
    assert receipt.disposition == "FINDING"


def test_the_receipt_names_why_the_signals_are_independent():
    """The epic: "An implementation must name which inputs are independent"."""
    receipt = activate()
    assert "host_replayer" in receipt.independence_basis
    assert "REPLAY_FAILURE" in receipt.independence_basis
    assert "spec_alpha" in receipt.independence_basis


def test_the_receipt_binds_all_three_inputs_by_digest():
    """A composition that carries digests cannot contradict its owners."""
    profile, hit, danger = make_profile(), make_hit(), make_danger()
    receipt = evaluate_activation(
        profile.profile_digest, hit, danger, externally_admitted=True, suspended=False
    )
    assert receipt.profile_digest == profile.profile_digest
    assert receipt.hit_id == hit.hit_id
    assert receipt.danger_receipt_id == danger.receipt_id
    assert receipt.subject_id == hit.subject_id


# --------------------------------------------------------------------------
# TWO_SIGNAL_COLLAPSE -- three distinct mistakes
# --------------------------------------------------------------------------


def test_collapse_when_the_danger_evidence_is_the_detector_finding():
    """One signal counted twice."""
    hit = make_hit()
    danger = make_danger(evidence_digest=hit.hit_id)
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(hit=hit, danger=danger)
    assert excinfo.value.code == "TWO_SIGNAL_COLLAPSE"
    assert "counted twice" in str(excinfo.value)


def test_collapse_when_the_danger_observer_is_the_detector_spec():
    """The danger bit derived from the match."""
    danger = make_danger(observer_id="spec_alpha")
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(danger=danger)
    assert excinfo.value.code == "TWO_SIGNAL_COLLAPSE"
    assert "derived from the match" in str(excinfo.value)


def test_collapse_when_the_danger_observer_is_the_detector_failure_code():
    danger = make_danger(observer_id="code_beta")
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(danger=danger)
    assert excinfo.value.code == "TWO_SIGNAL_COLLAPSE"


@pytest.mark.parametrize("producer", sorted(FORBIDDEN_DANGER_PRODUCERS))
def test_a_model_authored_danger_flag_is_refused_at_construction(producer):
    """The third collapse, refused before it can reach the gate.

    A model proposing a danger signal is a model authorising its own
    activation. Refused when the receipt is built, so no code path exists that
    could pass one to `evaluate_activation` at all.
    """
    with pytest.raises(ValueError, match="may not be authored by"):
        make_danger(producer_kind=producer)


def test_only_a_host_may_produce_a_danger_signal():
    with pytest.raises(ValueError, match="must be HOST"):
        make_danger(producer_kind="SOMETHING_ELSE")


def test_a_distinct_observer_and_evidence_are_permitted():
    """The independence check must be able to pass."""
    danger = make_danger(observer_id="host_manifest_scanner", evidence_digest=digest("d"))
    receipt = activate(danger=danger)
    assert receipt.danger_receipt_id == danger.receipt_id


# --------------------------------------------------------------------------
# The other three conjuncts, each refused by its own code
# --------------------------------------------------------------------------


def test_a_guard_without_external_admission_does_not_activate():
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(externally_admitted=False)
    assert excinfo.value.code == "NOT_EXTERNALLY_ADMITTED"


def test_a_danger_signal_without_a_detector_match_does_not_activate():
    """The epic's acceptance condition, stated in its own words."""
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(hit=None)
    assert excinfo.value.code == "NO_DETECTOR_MATCH"


def test_a_detector_match_without_a_danger_receipt_stays_a_finding():
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(danger=None)
    assert excinfo.value.code == "NO_DANGER_SIGNAL"
    assert "stays a" in str(excinfo.value)


def test_a_suspended_guard_does_not_activate():
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(suspended=True)
    assert excinfo.value.code == "SUSPENDED"


def test_signals_observing_different_subjects_do_not_activate():
    """Two signals about two subjects are not two signals about one."""
    danger = make_danger(subject_id=digest("e"))
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(danger=danger)
    assert excinfo.value.code == "SUBJECT_MISMATCH"


def test_each_conjunct_has_its_own_refusal_code():
    """A single generic refusal would not say which conjunct failed."""
    seen = set()
    for kwargs in (
        {"externally_admitted": False},
        {"hit": None},
        {"danger": None},
        {"suspended": True},
    ):
        with pytest.raises(ActivationRefusal) as excinfo:
            activate(**kwargs)
        seen.add(excinfo.value.code)
    assert len(seen) == 4
    assert seen <= REFUSAL_CODES


# --------------------------------------------------------------------------
# Authority ceiling
# --------------------------------------------------------------------------


def test_activation_may_select_only_finding_hold_or_refuse():
    assert ACTIVATION_DISPOSITIONS == {"FINDING", "HOLD", "REFUSE"}
    for disposition in sorted(ACTIVATION_DISPOSITIONS):
        assert activate(disposition=disposition).disposition == disposition


@pytest.mark.parametrize("effect", ["REPAIR", "ADMIT", "MERGE", "PUBLISH", "EXECUTE"])
def test_activation_cannot_select_an_external_effect(effect):
    """The epic: it "cannot repair, admit, merge, publish, or execute"."""
    with pytest.raises(ValueError, match="not closed"):
        activate(disposition=effect)


def test_every_receipt_carries_authority_effect_none():
    receipt = activate()
    assert receipt.authority_effect == "None"
    assert make_danger().authority_effect == "None"


def test_a_receipt_with_a_non_none_authority_effect_is_refused():
    with pytest.raises(ValueError, match="authority_effect"):
        DangerSignalReceiptV1(
            signal_kind="REPLAY_FAILURE",
            observer_id="host_replayer",
            subject_id=SUBJECT,
            evidence_digest=digest("c"),
            authority_effect="ACTION_LICENSE",
        )


# --------------------------------------------------------------------------
# The danger-signal registry
# --------------------------------------------------------------------------


def test_the_danger_signal_registry_is_closed():
    """`IMMUNE-002-W3`. An open vocabulary is the collapse in another hat.

    MALFORMED_PAYLOAD was added when the registry became shared with the
    screening path (a payload that is not strict JSON is host-observable).
    """
    assert DANGER_SIGNAL_KINDS == {
        "REPLAY_FAILURE",
        "PROTECTED_FIELD_VIOLATION",
        "MANIFEST_CONTAMINATION",
        "MALFORMED_PAYLOAD",
    }


def test_a_signal_kind_outside_the_registry_is_refused():
    with pytest.raises(ValueError, match="closed registry"):
        make_danger(signal_kind="VIBES")


@pytest.mark.parametrize("kind", sorted(DANGER_SIGNAL_KINDS))
def test_every_registered_kind_is_accepted(kind):
    """The registry must admit all of what it declares, or it is smaller than it says."""
    assert make_danger(signal_kind=kind).signal_kind == kind


# --------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------


def test_receipts_are_content_addressed():
    a = make_danger()
    b = make_danger()
    assert a.receipt_id == b.receipt_id
    c = make_danger(observer_id="host_other")
    assert c.receipt_id != a.receipt_id


def test_a_tampered_receipt_id_is_refused():
    good = make_danger()
    with pytest.raises(ValueError, match="does not match canonical content"):
        DangerSignalReceiptV1(
            signal_kind=good.signal_kind,
            observer_id=good.observer_id,
            subject_id=good.subject_id,
            evidence_digest=good.evidence_digest,
            receipt_id=digest("f"),
        )


def test_an_activation_receipt_without_an_independence_basis_is_refused():
    """A receipt that cannot say why its signals are independent is not evidence."""
    with pytest.raises(ValueError, match="independence_basis"):
        GuardActivationReceiptV1(
            profile_digest=digest("b"),
            hit_id=digest("c"),
            danger_receipt_id=digest("d"),
            subject_id=SUBJECT,
            disposition="FINDING",
            independence_basis="",
        )


def test_an_unknown_refusal_code_cannot_be_raised():
    """The refusal vocabulary is closed too."""
    with pytest.raises(ValueError, match="unknown activation refusal code"):
        raise ActivationRefusal("INVENTED_CODE", "nope")


# --------------------------------------------------------------------------
# The hit reference re-validates what it reads
# --------------------------------------------------------------------------


def test_a_hit_reference_refuses_malformed_fields():
    """`from_hit` reads attributes; it must not trust a look-alike object."""

    class Forged:
        hit_id = "not-a-digest"
        spec_id = "spec_alpha"
        failure_code = "code_beta"
        subject_id = SUBJECT

    with pytest.raises(ValueError, match="hit_id"):
        DetectorHitRefV1.from_hit(Forged())


def test_a_profile_that_is_not_a_digest_is_refused():
    with pytest.raises(ValueError, match="profile_digest"):
        evaluate_activation(
            "profile_alpha",
            make_hit(),
            make_danger(),
            externally_admitted=True,
            suspended=False,
        )


def test_receipt_ids_are_unchanged_by_the_move():
    """The canonical id is byte-identical to OEWAS anti-skill canonical_id."""
    from operads.domain.anti_skills.canonical import canonical_id

    danger = make_danger()
    payload = {key: value for key, value in danger.to_dict().items() if key != "receipt_id"}
    assert danger.receipt_id == canonical_id(danger.schema_version, payload)


@pytest.mark.parametrize("observer", ["Spec_Alpha", "SPEC_ALPHA", "Code_Beta"])
def test_collapse_is_detected_whatever_the_letter_case(observer):
    """Counterexample (review, 2026-09-29): identifiers were compared case-sensitively,
    so an observer "Spec_Alpha" passed as distinct from the detector spec "spec_alpha"."""
    with pytest.raises(ActivationRefusal) as excinfo:
        activate(danger=make_danger(observer_id=observer))
    assert excinfo.value.code == "TWO_SIGNAL_COLLAPSE"
