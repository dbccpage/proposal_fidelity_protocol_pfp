"""External admission: candidate by default, and repetition is not evidence.

Three of `EPIC-OE-PHARMACY-001`'s six criteria, each with the decisive mutation
the epic itself names.

1. **Nothing self-admits.** "A freshly farmed antibody is `CANDIDATE` regardless
   of path." *Mutation:* set `pharmacy_status="admitted"` at the seeder.
2. **A single observation cannot promote.** "An antibody with one supporting
   observation stays `CANDIDATE` however many times that observation is
   replayed." *Mutation:* replay one defect ten times.
3. **The request binds what the atlas says it binds**, "and refuses when any is
   absent". *Mutation:* omit the negative fixture digest.

Criterion 2 is the same mistake `IMMUNE-002` calls `TWO_SIGNAL_COLLAPSE`, one
domain over: counting records instead of identities makes repetition look like
corroboration. Sprint 009 refused a detector that read its own output twice;
this refuses a pharmacy that reads one defect ten times.

`N` is not chosen here. The epic lists the threshold as an open obligation, so
`is_promotable` requires it as a keyword argument with no default.

Moved on 2026-09-29 with the implementation, from
`projects/ms_majorana/code/tests/unit/test_external_admission.py`.
"""

from __future__ import annotations

import pytest

from eis.domain.external_admission import (
    PHARMACY_STATUS_CANDIDATE,
    REQUIRED_BINDINGS,
    AdmissionError,
    AntibodyObservationV1,
    ExternalAdmissionRequestV1,
    distinct_observations,
    farm_candidate,
    is_promotable,
)


def digest(character: str) -> str:
    return "sha256:" + character * 64


def make_request(**overrides) -> ExternalAdmissionRequestV1:
    fields = {
        "candidate_digest": digest("a"),
        "producer_system": "ooutwire_seeder",
        "source_manifest_digest": digest("b"),
        "positive_fixture_digest": digest("c"),
        "negative_fixture_digest": digest("d"),
    }
    fields.update(overrides)
    return ExternalAdmissionRequestV1(**fields)


def observation(character: str, run: str = "run_one") -> AntibodyObservationV1:
    return AntibodyObservationV1(
        observation_digest=digest(character), observer_id="host_detector", run_id=run
    )


# --------------------------------------------------------------------------
# Criterion 1 -- nothing self-admits
# --------------------------------------------------------------------------


def test_a_farmed_antibody_is_a_candidate():
    request = farm_candidate(
        digest("a"), "ooutwire_seeder", digest("b"), digest("c"), digest("d")
    )
    assert request.status == PHARMACY_STATUS_CANDIDATE


def test_the_farming_path_has_no_status_argument():
    """Criterion 1 enforced by absence, not by validation.

    A status parameter that is checked can be passed wrongly by a caller who
    reads the check as advisory. A parameter that does not exist cannot.
    """
    import inspect

    from eis.domain import (
        external_admission as external_admission_v1,
    )

    signature = inspect.signature(external_admission_v1.farm_candidate)
    assert "status" not in signature.parameters


@pytest.mark.parametrize("status", ["ADMITTED", "admitted", "ACTIVE", "RETIRED"])
def test_a_request_entering_as_anything_but_candidate_is_refused(status):
    """The epic's mutation: set `pharmacy_status="admitted"` at the seeder."""
    with pytest.raises(AdmissionError) as excinfo:
        make_request(status=status)
    assert excinfo.value.code == "SELF_ADMISSION"
    assert "transition" in str(excinfo.value)


# --------------------------------------------------------------------------
# Criterion 2 -- a single observation cannot promote
# --------------------------------------------------------------------------


def test_replaying_one_observation_ten_times_yields_one_observation():
    """The epic's mutation, verbatim: "replay one defect ten times"."""
    replays = tuple([observation("1")] * 10)
    assert len(replays) == 10
    assert len(distinct_observations(replays)) == 1


def test_ten_replays_of_one_defect_do_not_promote():
    request = make_request()
    replays = tuple([observation("1")] * 10)
    assert is_promotable(request, replays, required_distinct=2) is False


def test_replays_under_different_run_ids_still_do_not_promote():
    """Distinctness is the observed event, not the record around it.

    Ten runs replaying the same defect are ten records of one observation. If
    `run_id` counted, a loop would manufacture corroboration.
    """
    replays = tuple(
        AntibodyObservationV1(
            observation_digest=digest("1"),
            observer_id="host_detector",
            run_id=f"run_{index}",
        )
        for index in range(10)
    )
    assert len(distinct_observations(replays)) == 1
    assert is_promotable(make_request(), replays, required_distinct=2) is False


def test_two_genuinely_distinct_observations_promote():
    """The permitted case. Without it every refusal above proves nothing."""
    request = make_request()
    pair = (observation("1"), observation("2"))
    assert is_promotable(request, pair, required_distinct=2) is True


def test_the_threshold_has_no_default():
    """`N` is an open obligation; the caller must state it."""
    import inspect

    from eis.domain import (
        external_admission as external_admission_v1,
    )

    parameter = inspect.signature(
        external_admission_v1.is_promotable
    ).parameters["required_distinct"]
    assert parameter.default is inspect.Parameter.empty
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


def test_a_threshold_below_two_is_refused():
    """A first sighting is exactly what a detector bug produces."""
    with pytest.raises(AdmissionError) as excinfo:
        is_promotable(make_request(), (observation("1"),), required_distinct=1)
    assert excinfo.value.code == "BAD_THRESHOLD"
    assert "first sighting" in str(excinfo.value)


def test_a_boolean_threshold_is_refused():
    """`True` is an int in Python, and `required_distinct=True` means 1."""
    with pytest.raises(AdmissionError, match="exact integer"):
        is_promotable(make_request(), (observation("1"),), required_distinct=True)


def test_no_observations_do_not_promote():
    assert is_promotable(make_request(), (), required_distinct=2) is False


# --------------------------------------------------------------------------
# Criterion 3 -- the request binds what the atlas says
# --------------------------------------------------------------------------


def test_the_atlas_bindings_are_all_present():
    request = make_request()
    for binding in REQUIRED_BINDINGS:
        assert getattr(request, binding)


@pytest.mark.parametrize("binding", REQUIRED_BINDINGS)
def test_a_request_missing_any_binding_is_refused(binding):
    """The epic's mutation: "omit the negative fixture digest" -- generalised.

    Parameterising over every binding means the check cannot pass by handling
    one field and forgetting another.
    """
    payload = {
        "candidate_digest": digest("a"),
        "producer_system": "ooutwire_seeder",
        "source_manifest_digest": digest("b"),
        "positive_fixture_digest": digest("c"),
        "negative_fixture_digest": digest("d"),
    }
    del payload[binding]
    with pytest.raises(AdmissionError) as excinfo:
        ExternalAdmissionRequestV1.from_mapping(payload)
    assert excinfo.value.code == "MISSING_BINDING"
    assert binding in str(excinfo.value)


def test_a_missing_binding_is_refused_not_defaulted():
    """"Refuses when any is absent" -- absent means absent.

    Defaulting a fixture digest would admit a candidate nobody tested against a
    control.
    """
    payload = {
        "candidate_digest": digest("a"),
        "producer_system": "ooutwire_seeder",
        "source_manifest_digest": digest("b"),
        "positive_fixture_digest": digest("c"),
    }
    with pytest.raises(AdmissionError):
        ExternalAdmissionRequestV1.from_mapping(payload)


def test_identical_fixtures_are_refused():
    """A control that equals the case controls nothing."""
    with pytest.raises(AdmissionError) as excinfo:
        make_request(
            positive_fixture_digest=digest("c"), negative_fixture_digest=digest("c")
        )
    assert excinfo.value.code == "FIXTURES_IDENTICAL"


def test_a_complete_payload_parses():
    """`from_mapping` must be able to succeed, or its refusals prove nothing."""
    request = ExternalAdmissionRequestV1.from_mapping(
        {
            "candidate_digest": digest("a"),
            "producer_system": "ooutwire_seeder",
            "source_manifest_digest": digest("b"),
            "positive_fixture_digest": digest("c"),
            "negative_fixture_digest": digest("d"),
        }
    )
    assert request.status == PHARMACY_STATUS_CANDIDATE


def test_a_non_digest_binding_is_refused():
    with pytest.raises(AdmissionError, match="BAD_DIGEST"):
        make_request(candidate_digest="not-a-digest")


def test_an_empty_producer_system_is_refused():
    with pytest.raises(AdmissionError, match="producer_system"):
        make_request(producer_system="")


# --------------------------------------------------------------------------
# Authority and identity
# --------------------------------------------------------------------------


def test_the_request_carries_authority_effect_none():
    assert make_request().authority_effect == "None"


def test_a_non_none_authority_effect_is_refused():
    with pytest.raises(AdmissionError, match="authority_effect"):
        make_request(authority_effect="ACTION_LICENSE")


def test_requests_are_content_addressed():
    a = make_request()
    b = make_request()
    assert a.request_id == b.request_id
    c = make_request(producer_system="other_system")
    assert c.request_id != a.request_id


def test_a_tampered_request_id_is_refused():
    good = make_request()
    with pytest.raises(AdmissionError, match="does not match canonical content"):
        make_request(request_id=digest("f"))
    assert good.request_id


def test_to_dict_round_trips_through_from_mapping():
    original = make_request()
    assert ExternalAdmissionRequestV1.from_mapping(original.to_dict()) == original


def test_a_malformed_observation_is_refused():
    with pytest.raises(AdmissionError, match="BAD_OBSERVATIONS"):
        distinct_observations(("not an observation",))


def test_observations_must_be_a_tuple():
    with pytest.raises(AdmissionError, match="exact tuple"):
        distinct_observations([observation("1")])


def test_a_digest_with_non_hex_characters_is_refused():
    """The moved module used to accept any 64 characters after `sha256:`."""
    with pytest.raises(AdmissionError, match="BAD_DIGEST"):
        make_request(candidate_digest="sha256:" + "z" * 64)
    with pytest.raises(AdmissionError, match="BAD_DIGEST"):
        make_request(candidate_digest="sha256:" + "A" * 64)
