"""Source-case integration controls for the two retained quantum adapter seams."""

from copy import deepcopy
import json

import pytest

from pfp.infrastructure import challenge_execution as execution
from adversary.tests.pilots.challenge_suite.catalog import digest, load_case


def test_isolated_child_invokes_canonical_pfp_owner(monkeypatch):
    from types import SimpleNamespace

    calls = []

    def child(command, **options):
        calls.append((command, options))
        return SimpleNamespace(returncode=0, stdout=b'{"status":"FIXTURE_VERIFIED"}')

    monkeypatch.setattr(execution.subprocess, "run", child)
    request = {"kind": "NO_LLM", "row": {"challenge": "C005"}}
    assert execution.isolated(request) == {"status": "FIXTURE_VERIFIED"}
    assert calls[0][0] == [execution.sys.executable, "-m",
                           "pfp.infrastructure.challenge_execution"]
    assert json.loads(calls[0][1]["input"]) == request


CHALLENGES = {
    "C023": "c023_clifford_tableau_synthesis",
    "C024": "c024_local_clifford_graph_state_equivalence",
}


def source_row(challenge_id, name):
    source = execution.ROOT / "pfp/tests/demo_004/c_quantum" / (
        CHALLENGES[challenge_id] + "/judge_packet/cases/" + name
    )
    return dict(
        challenge=challenge_id,
        source=source.relative_to(execution.ROOT).as_posix(),
        sha256=digest(source.read_bytes()),
        index=None,
    )


def envelope(answer):
    return json.dumps(dict(
        derived_under_policy="SPK-001",
        summary=dict(
            narrowest_defensible_thesis="Source-case fixture",
            evidence_scope="Original finite quantum judges",
            next_concrete_test="Check actual witness",
        ),
        process_integrity=dict(
            seed_allows_theory_refutation=True, detected_prompt_biases=[], should_continue=False,
        ),
        sections=[],
        answer=answer,
    ))


@pytest.mark.parametrize("challenge_id,name", [
    ("C023", "c023_base_01.json"),
    ("C024", "c024_base_01_eq.json"),
])
def test_actual_source_baseline_uses_original_solver_and_both_judges(challenge_id, name):
    row = source_row(challenge_id, name)
    original = (execution.ROOT / row["source"]).read_bytes()
    result = execution.worker(dict(kind="NO_LLM", row=row))
    assert result["status"] == "FIXTURE_VERIFIED", result
    assert result["answer"]["status"] == "SOLVED"
    assert len(result["judges"]) == 2
    assert all(item["accepted"] for item in result["judges"])
    assert (execution.ROOT / row["source"]).read_bytes() == original


@pytest.mark.parametrize("challenge_id,name", [
    ("C023", "c023_poison_03_commuting_xz_pair.json"),
    ("C024", "c024_poison_04_self_loop_gp.json"),
])
def test_actual_malformed_source_remains_checked_refusal(challenge_id, name):
    result = execution.worker(dict(kind="NO_LLM", row=source_row(challenge_id, name)))
    assert result["status"] == "TYPED_REFUSAL", result
    assert result["answer"]["status"] == "OUT_OF_SCOPE"
    assert len(result["judges"]) == 2
    assert all(item["accepted"] for item in result["judges"])


def test_c024_normalizer_exposes_declared_input_without_mutating_source():
    row = source_row("C024", "c024_base_01_eq.json")
    wrapped = load_case(row)
    original = deepcopy(wrapped)
    normalized = execution.normalized_case("C024", wrapped)
    assert normalized == wrapped["input"]
    assert normalized["id"] == "c024_base_01_eq"
    assert "input" not in normalized
    normalized["g"].append([0, 0])
    assert wrapped == original


@pytest.mark.parametrize("challenge_id", ["C023", "C011", "C005"])
def test_unrelated_challenges_do_not_unwrap_input(challenge_id):
    case = {"input": {"some_domain_field": 4}, "id": "original"}
    assert execution.normalized_case(challenge_id, case) is case


def test_c024_bare_input_remains_supported():
    bare = load_case(source_row("C024", "c024_base_01_eq.json"))["input"]
    assert execution.normalized_case("C024", bare) is bare


@pytest.mark.parametrize("bad", [None, True, [], "{\"num_vertices\":4}"])
def test_c024_wrapper_cannot_coerce_non_object_input(bad):
    with pytest.raises(ValueError, match="INVALID_C024_INPUT_WRAPPER"):
        execution.normalized_case("C024", {"input": bad})


@pytest.mark.parametrize("challenge_id,name,field,value", [
    ("C023", "c023_base_01.json", "circuit", []),
    ("C024", "c024_base_01_eq.json", "sequence", []),
])
def test_schema_shaped_wrong_witness_reaches_original_judges_and_fails(
    challenge_id, name, field, value,
):
    row = source_row(challenge_id, name)
    baseline = execution.worker(dict(kind="NO_LLM", row=row))
    assert baseline["status"] == "FIXTURE_VERIFIED", baseline
    wrong = deepcopy(baseline["answer"])
    wrong[field] = value
    result = execution.worker(dict(kind="PROPOSAL", row=row, raw_reply=envelope(wrong)))
    assert result["status"] == "PROVIDER_COMPLETED", result
    assert result["failure_class"] == "CERTIFICATE"
    assert len(result["judges"]) == 2
    assert not any(item["accepted"] for item in result["judges"])


@pytest.mark.parametrize("challenge_id,name", [
    ("C023", "c023_base_01.json"),
    ("C024", "c024_base_01_eq.json"),
])
def test_isolated_worker_keeps_the_same_source_case_contract(challenge_id, name):
    result = execution.isolated(dict(kind="NO_LLM", row=source_row(challenge_id, name)))
    assert result["status"] == "FIXTURE_VERIFIED", result
    assert len(result["judges"]) == 2
