"""Decisive PFP gate mutants, self-tolerance, and bounded feedback transfer.

These are host fixtures, never claimed as neural observations. AuthorityEffect: None.
"""

import json

import pytest

from omega_engine_woland.tests.pilots.challenge_suite.__main__ import HARNESS_MUTANTS
from omega_engine_woland.tests.pilots.challenge_suite.catalog import load_plan
from omega_engine_woland.tests.pilots.challenge_suite.catalog import prompt_for
from omega_engine_pfp.infrastructure.adapters.pfp_proposals import SymbolGameProposalAdapter
from omega_engine_pfp.use_cases.pfp_prompt import stimulus, task_contract
from omega_engine_pfp.use_cases.pfp_proposal import (
    CheckProposalUseCase,
    ProposalCheck,
    repair_feedback,
)
from omega_engine_pfp.use_cases.pfp_stages import PfpStagePolicy


def envelope():
    return dict(
        derived_under_policy="SPK-001",
        summary=dict(
            narrowest_defensible_thesis="Host fixture",
            evidence_scope="Finite equation",
            next_concrete_test="Check independent witness",
        ),
        process_integrity=dict(
            seed_allows_theory_refutation=True, detected_prompt_biases=[], should_continue=False
        ),
        sections=[],
        answer=dict(x=2, y=1),
    )


def primal(case, answer):
    return (
        type(answer.get("x")) is int
        and type(answer.get("y")) is int
        and 2 * answer["x"] + answer["y"] == case["b"],
        "Equation check",
    )


def independent(case, answer):
    if type(answer.get("x")) is not int or type(answer.get("y")) is not int:
        return False, "Exact integers required"
    return answer["y"] == case["b"] - answer["x"] - answer["x"], "Independent elimination"


JUDGES = (("primal", primal), ("elimination", independent))


@pytest.mark.parametrize("name", HARNESS_MUTANTS)
def test_gate_mutant(name):
    value = envelope()
    judges = JUDGES
    if name == "bare_answer":
        value = value["answer"]
    elif name == "wrong_policy":
        value["derived_under_policy"] = "SPK-002"
    elif name == "missing_answer":
        del value["answer"]
    elif name == "scalar_answer":
        value["answer"] = 5
    elif name == "missing_summary":
        del value["summary"]
    elif name == "empty_thesis":
        value["summary"]["narrowest_defensible_thesis"] = " "
    elif name == "numeric_summary":
        value["summary"]["evidence_scope"] = 1
    elif name == "extra_summary_key":
        value["summary"]["host_accepted"] = True
    elif name == "missing_integrity":
        del value["process_integrity"]
    elif name == "integer_boolean":
        value["process_integrity"]["should_continue"] = 1
    elif name == "string_boolean":
        value["process_integrity"]["should_continue"] = "true"
    elif name == "wrong_biases_type":
        value["process_integrity"]["detected_prompt_biases"] = "none"
    elif name == "numeric_bias":
        value["process_integrity"]["detected_prompt_biases"] = [1]
    elif name == "nonempty_sections":
        value["sections"] = ["claim"]
    elif name == "extra_envelope_key":
        value["accepted"] = True
    elif name == "wrong_witness":
        value["answer"]["x"] = 3
    elif name == "unwarranted_refusal":
        value["answer"] = {"status": "UNKNOWN"}
    elif name == "checker_exception":

        def broken(case, answer):
            raise RuntimeError("checker broke")

        judges = (("broken", broken),)
    elif name == "checker_disagreement":
        judges = (JUDGES[0], ("disagree", lambda c, a: (False, "no")))
    elif name == "missing_checker":
        judges = ()
    raw = json.dumps(value)
    if name == "duplicate_json_key":
        raw = raw.replace('"answer":', '"answer":{},"answer":')
    elif name == "nan":
        raw = raw.replace('"x": 2', '"x": NaN')
    elif name == "infinite_number":
        raw = raw.replace('"x": 2', '"x": 1e999')
    elif name == "fenced_json":
        raw = "```json\n" + raw + "\n```"
    elif name == "trailing_prose":
        raw += "\nI passed."
    result = CheckProposalUseCase().execute({"b": 5}, raw, judges)
    assert result.status != "HOST_ACCEPTED"
    if name in ("checker_exception", "checker_disagreement"):
        assert result.status == "CHECKER_DEFECT"
        assert repair_feedback(result) is None


def test_alternative_witnesses_are_self_tolerant():
    for x, y in ((2, 1), (1, 3), (0, 5), (-1, 7)):
        value = envelope()
        value["answer"] = {"x": x, "y": y}
        assert (
            CheckProposalUseCase().execute({"b": 5}, json.dumps(value), JUDGES).status
            == "HOST_ACCEPTED"
        )


@pytest.mark.parametrize("bad", [True, 2.0, "2"])
def test_exact_wire_types_reject_coercion(bad):
    value = envelope()
    value["answer"]["x"] = bad
    assert (
        CheckProposalUseCase().execute({"b": 5}, json.dumps(value), JUDGES).status
        != "HOST_ACCEPTED"
    )


def test_feedback_does_not_reveal_judge_answers():
    result = CheckProposalUseCase().execute(
        {"b": 5},
        json.dumps(envelope()),
        (("secret", lambda c, a: (False, "Expected secret answer 938456")),),
    )
    assert "938456" not in repair_feedback(result)


def test_recursive_projection_removes_judge_labels():
    value = {
        "expected_kind": "SOLVED",
        "held_out_terms": [999],
        "input": {"rep_id_expected": "secret", "n": 3},
    }
    assert stimulus(value) == {"input": {"n": 3}}


def test_stimulus_drops_bare_expected_and_keeps_allowed_fields():
    assert stimulus({"expected": 5, "n": 3}) == {"n": 3}


def test_task_examples_cannot_supply_solved_values(tmp_path):
    path = tmp_path / "TASK.md"
    path.write_text('Contract\n```json\n{"answer": {"phi1": "938456"}}\n```', encoding="utf-8")
    result = task_contract(path.read_text(encoding="utf-8"))
    assert "938456" not in result
    assert "phi1" in result


def test_symbol_game_seam_keeps_native_outcome():
    sentinel = object()

    class Host:
        def stabilizer_check(self, case, answer):
            assert case == {"id": "q40"}
            assert answer == {"x": 2, "y": 1}
            return sentinel

    assert (
        SymbolGameProposalAdapter(Host()).verify_q40({"id": "q40"}, json.dumps(envelope()))
        is sentinel
    )


def test_symbol_game_seam_rejects_bare_candidate_before_invocation():
    class Host:
        def stabilizer_check(self, *args):
            pytest.fail("Malformed envelope crossed native seam")

    with pytest.raises(ValueError):
        SymbolGameProposalAdapter(Host()).verify_q40({}, '{"energy": [0,1]}')


def test_repair_bound_and_checker_stop():
    policy = PfpStagePolicy()
    failure = ProposalCheck("PROVIDER_COMPLETED", "CERTIFICATE")
    assert policy.feedback_after(1, failure)
    assert policy.feedback_after(2, failure) is None
    assert policy.feedback_after(1, ProposalCheck("CHECKER_DEFECT", "CHECKER")) is None
    with pytest.raises(ValueError):
        PfpStagePolicy(3)


def test_rendered_schema_requires_every_ingress_field():
    row = next(
        c["cases"][0]
        for f in load_plan()["families"]
        for c in f["challenges"]
        if c["challenge"] == "C011"
    )
    schema = prompt_for(row)["response_schema"]
    assert set(schema["required"]) == set(envelope())


@pytest.mark.parametrize(
    "judge,reason,expected",
    [
        (
            "circulation_checker:verify_circulation_certificate",
            "FAIL: coboundary relation broken",
            "COBOUNDARY_RESIDUAL",
        ),
        (
            "algebraic_checker:verify_certificate",
            "FAIL: Decomposition algebraic mismatch",
            "PAULI_PHASE",
        ),
        ("exact_checker:check_solution", "Invalid status: PROVED", "WIRE_DISCRIMINATOR"),
    ],
)
def test_observed_failure_routes_to_answer_free_rule(judge, reason, expected):
    result = CheckProposalUseCase().execute(
        {"b": 5}, json.dumps(envelope()), ((judge, lambda c, a: (False, reason)),)
    )
    assert result.failure_class == expected
    assert reason not in repair_feedback(result)


def test_redacted_contract_withholds_status_and_phi1_values(tmp_path):
    task = tmp_path / "TASK.md"
    task.write_text('```json\n{"status":"SOLVED","phi1":"938456"}\n```', encoding="utf-8")
    result = task_contract(task.read_text(encoding="utf-8"))
    assert "SOLVED" not in result
    assert "938456" not in result
    assert "status" in result
    assert "phi1" in result


@pytest.mark.parametrize("kind", ["consistency", "cycle_repair"])
def test_exact_c005_schema_survives_example_mining(kind):
    from omega_engine_woland.tests.pilots.challenge_suite.catalog import load_case
    from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.schemas import (
        CONSISTENCY_JSON_SCHEMA,
        CYCLE_REPAIR_JSON_SCHEMA,
    )

    rows = next(
        c["cases"]
        for f in load_plan()["families"]
        for c in f["challenges"]
        if c["challenge"] == "C005"
    )
    row = next(r for r in rows if load_case(r)["kind"] == kind)
    expected = CONSISTENCY_JSON_SCHEMA if kind == "consistency" else CYCLE_REPAIR_JSON_SCHEMA
    assert prompt_for(row)["response_schema"]["properties"]["answer"] == expected["schema"]
