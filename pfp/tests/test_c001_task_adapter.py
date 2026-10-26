"""Original C001 finite witnesses, without claiming the attention experiment ran."""

from collections import Counter
from copy import deepcopy
import json

import pytest

from omega_engine_pfp.tests.demo_004.a_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_public_set,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c001_attention_distractor_mask.solve import solve
from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPromptTemplate
from omega_engine_pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
from omega_engine_pfp.use_cases.pfp_proposal import task_turn_validator


def adapter():
    from omega_engine_woland.tests.pilots.challenge_suite import c001

    return c001


def test_original_public_mix_and_selected_input_are_reproducible():
    owner = adapter()
    rows = owner.case_rows()
    assert len(rows) == 40
    assert Counter(owner.load_case(row)["kind"] for row in rows) == {
        "verdict": 16, "repair": 16, "audit": 8,
    }
    assert owner.load_case(rows[0]) == json.loads(json.dumps(generate_public_set()[0]))
    assert all(row["partition"] == "public" and row["split"] == "development" for row in rows)
    assert len({row["case_id"] for row in rows}) == 40


@pytest.mark.parametrize("field,value", [
    ("sha256", "0" * 64), ("case_sha256", "0" * 64), ("case_id", "another-case"),
    ("index", True), ("index", 40),
])
def test_case_selector_refuses_changed_source_input_or_identity(field, value):
    owner = adapter()
    row = owner.case_rows()[0]
    row[field] = value
    with pytest.raises(ValueError, match="C001_"):
        owner.load_case(row)


@pytest.mark.parametrize("index", [0, 1, 16, 32, 33])
def test_each_original_witness_variant_reaches_the_existing_checker(index):
    owner = adapter()
    case = owner.load_case(owner.case_rows()[index])
    original = deepcopy(case)
    answer = solve(case)
    assert answer["status"] == "SOLVED"
    assert owner.check_answer(case, answer)[0] is True
    assert task_turn_validator(owner.answer_schema(case)).is_valid(answer)
    assert case == original


def test_finite_gate_checks_equations_instead_of_one_stored_potential():
    owner = adapter()
    case = owner.load_case(owner.case_rows()[0])
    answer = solve(case)
    answer["potential"] = {name: str(int(value) + 37) for name, value in answer["potential"].items()}
    assert owner.check_answer(case, answer)[0] is True
    answer["potential"][case["items"][0]] = str(int(answer["potential"][case["items"][0]]) + 1)
    assert owner.check_answer(case, answer)[0] is False


def test_any_valid_single_edge_correction_is_accepted():
    owner = adapter()
    names = list("ABCDEF")
    edges = [[name, names[(index + 1) % 6], 1] for index, name in enumerate(names)]
    case = dict(kind="repair", items=names, edges=edges,
        claims={f"{u}->{v}": "1" if u == "F" else "0" for u, v, _ in edges})
    for edge, value in [(["F", "A"], "0"), (["A", "B"], "-1")]:
        answer = dict(status="SOLVED", kind="repair", edge=edge, value=value)
        assert owner.check_answer(case, answer)[0] is True
    answer["also_edit"] = {"edge": ["F", "A"], "value": "0"}
    assert owner.check_answer(case, answer)[0] is False


@pytest.mark.parametrize("value", [0, 1.0, True, "01", "-0", "+1", "1/1", "0.5"])
def test_potential_wire_requires_original_canonical_integer_strings(value):
    owner = adapter()
    case = owner.load_case(owner.case_rows()[0])
    answer = solve(case)
    answer["potential"][case["items"][0]] = value
    assert owner.check_answer(case, answer)[0] is False


def test_cycle_and_audit_mutations_are_not_false_acceptances():
    owner = adapter()
    rows = owner.case_rows()
    case = owner.load_case(rows[1])
    answer = solve(case)
    answer["cycle"].pop()
    assert owner.check_answer(case, answer)[0] is False
    answer = solve(case)
    answer["cycle"][1] = "UNDECLARED"
    assert owner.check_answer(case, answer)[0] is False
    audit = owner.load_case(rows[33])
    assert owner.check_answer(audit, dict(status="SOLVED", kind="audit", answer="ACCEPT"))[0] is False


@pytest.mark.parametrize("answer", [
    {"status": "UNKNOWN", "refusal": "UNPARSEABLE_AFTER_FUEL"},
    {"status": "OUT_OF_SCOPE", "witness": {"field": "case", "reason": "unsupported"}},
])
def test_original_refusals_are_valid_wire_but_never_correct_solutions(answer):
    owner = adapter()
    case = owner.load_case(owner.case_rows()[0])
    assert task_turn_validator(owner.answer_schema(case)).is_valid(answer)
    assert owner.check_answer(case, answer)[0] is False


def test_public_projection_retains_distractors_without_oracle_material_or_mutation():
    owner = adapter()
    case = generate_public_set()[0]
    case.update(expected_answer=solve(case), oracle_answer="do not expose", private_training_label="do not expose")
    case["claimed_potential"] = solve(case)["potential"]
    before = deepcopy(case)
    projected = owner.public_case(case)
    assert projected["prompt_text"] == case["prompt_text"]
    assert set(projected) == {"case_id", "kind", "prompt_text"}
    host_case = owner.load_case(owner.case_rows()[0])
    assert host_case["distractor_spans"] == [list(span) for span in case["distractor_spans"]]
    assert host_case["edges"] == case["edges"] and host_case["claims"] == case["claims"]
    assert not {"expected_answer", "oracle_answer", "private_training_label"} & projected.keys()
    assert "claimed_potential" not in projected
    task = owner.task_prompt(case)
    prompt = PreparePfpTaskTurnUseCase().execute(
        PfpPromptTemplate("Propose the original C001 finite witness.", "[USER PROMPT]", {}), task, "attempt-1")
    public = json.loads(prompt.user)
    assert public["input"] == projected
    assert "do not expose" not in prompt.user
    assert case == before


def test_scope_keeps_neural_native_and_independent_protocol_obligations_open():
    owner = adapter()
    assert "200 hidden" in owner.task_text()
    assert "McNemar" in owner.task_text()
    assert "tokenizer" in " ".join(owner.OPEN_REQUIREMENTS)
    assert "independent" in " ".join(owner.OPEN_REQUIREMENTS)
    assert "attention" in " ".join(owner.OPEN_REQUIREMENTS)
    assert owner.CHECKER_ID == "c001:python-original-finite-witness-v1"
