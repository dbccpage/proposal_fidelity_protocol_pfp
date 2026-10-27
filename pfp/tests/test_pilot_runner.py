"""Current lesson runner contracts; no retired import tree or collection skip."""

import json

import pytest
import yaml

from pfp.infrastructure.pilot_runner import (
    PfpPilotRunner,
    build_p_star_yaml,
    get_ground_truth,
    grade,
    materialize_results,
)

FAMILIES = [
    "linear_algebra",
    "graph_facts",
    "graph_repair",
    "refusal",
    "cochain_defect",
    "magma_associativity",
]


@pytest.mark.parametrize("family", FAMILIES)
def test_seed_is_preserved_in_typed_prompt(family):
    packet = yaml.safe_load(build_p_star_yaml("pilot_fixture", family))
    assert packet["user_prompt"] == get_ground_truth(family)["req_0"]["query"]
    assert packet["lineage"]["family_id"] == family
    assert packet["response_schema"]


@pytest.mark.parametrize("family", FAMILIES)
def test_exact_answers_pass_current_lesson_gate(family):
    truth = get_ground_truth(family)
    replies = []
    for request_id, row in truth.items():
        answer = {"answer": row["expected"]}
        if row["expected"] is None:
            answer.update(status="REFUSED", witness={"remaining": [2, 4]})
        replies.append(
            {"request_id": "pilot_fixture_" + request_id, "raw_reply": json.dumps(answer)}
        )
    result = grade(replies, pilot_id="pilot_fixture", task_family=family)
    assert all(row["status"] == "ACCEPTED" for row in result["results"])


def test_missing_answers_remain_not_run():
    result = grade([], pilot_id="pilot_fixture", task_family="linear_algebra")
    assert all(row["status"] == "NOT_RUN" for row in result["results"])


@pytest.mark.parametrize("raw", ['{"answer":1,"answer":2}', "not json"])
def test_malformed_reply_is_retained_and_refused(raw):
    result = grade(
        [{"request_id": "pilot_fixture_req_0", "raw_reply": raw}],
        pilot_id="pilot_fixture",
        task_family="linear_algebra",
    )
    assert result["results"][0]["status"] == "MALFORMED"
    assert result["results"][0]["raw_reply"] == raw


def test_materialized_prompt_binds_seed_and_schema(tmp_path):
    paths = materialize_results(tmp_path, pilot_id="pilot_fixture", task_family="linear_algebra")
    prompt = yaml.safe_load(paths["p_star"].read_text(encoding="utf-8"))
    seed = yaml.safe_load(paths["seed"].read_text(encoding="utf-8"))
    template = yaml.safe_load(paths["prompt_template"].read_text(encoding="utf-8"))
    assert prompt["user_prompt"] == seed["seed_prompt"]
    assert prompt["response_schema"] == template["response_schema"]
    response = yaml.safe_load(paths["response"].read_text(encoding="utf-8"))
    assert response["evaluation"]["status"] == "NOT_RUN"
    assert response["raw_reply"] is None


def test_runner_routes_to_current_lesson_implementation():
    runner = PfpPilotRunner(pilot_id="pilot_fixture", task_family="linear_algebra")
    assert len(runner.requests()) == 2
    assert all(row["status"] == "NOT_RUN" for row in runner.grade([])["results"])
