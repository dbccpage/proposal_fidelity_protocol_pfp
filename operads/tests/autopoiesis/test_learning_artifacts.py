"""Actual artifact loading, the city scheduling, and deployment retrieval."""

from __future__ import annotations

import json

import pytest

from pfp.domain.value_objects.seat_turn import SeatTurnReplyV1
from adversary.domain.providers.types import BudgetExceeded
from adversary.stage.domain import SceneGraphV1, SceneSpecV1, SceneTransitionV1
from operads.domain.autopoiesis.learning import (
    CallerContext,
    LearningBlocked,
    artifact_text_digest,
)
from operads.infrastructure.autopoiesis.agent_learning import (
    ArtifactRuntime,
    call_parent,
    compile_workflow_graph,
)
from operads.infrastructure.autopoiesis.git_learning import command
from operads.infrastructure.autopoiesis.learning_runtime import (
    build_learning_completion,
)


class Budget:
    def __init__(self, remaining=100):
        self.remaining_microusd = remaining


class FixtureExecutor:
    """Deterministic transport fixture; never evidence of live model quality."""

    def __init__(self, budget):
        self.budget_controller = budget
        self.calls = []

    def __call__(self, request):
        self.calls.append(request)
        self.budget_controller.remaining_microusd -= 1
        output = "BLOCKED" if "Check the manifest before passing" in request.prompt_text else "PASS"
        return SeatTurnReplyV1(
            json.dumps({"output": output, "status": "PASS"}),
            {},
            model="fixture-model",
            provider="fixture",
        )


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return path


@pytest.fixture
def artifacts(tmp_path):
    skill = "operads/skills/manifest/SKILL.md"
    agent = "operads/agents/manifest.md"
    rule = "operads/rules/manifest.md"
    text = "Check the manifest before passing"
    write(tmp_path, skill, "---\nname: manifest\ndescription: Verify manifests\n---\n" + text)
    write(tmp_path, rule, text)
    write(
        tmp_path,
        agent,
        "---\nname: manifest\nmodel: inherit\ntools: []\n"
        "licensed_skills: [manifest]\nlicensed_colours: [State]\n---\nVerify the source.",
    )
    graph = SceneGraphV1(
        "check",
        (
            SceneSpecV1("check", "Check", ("checker",), ("PASS", "HOLD", "REFUSE"), 1),
            SceneSpecV1("report", "Report", ("checker",), ("PASS", "HOLD", "REFUSE"), 1, True),
        ),
        (SceneTransitionV1("next", "check", "report", ("PASS",), (), 0),),
    )
    workflow = "operads/domain/autopoiesis/profiles/manifest.json"
    write(
        tmp_path,
        workflow,
        json.dumps(
            {
                "name": "manifest_flow",
                "graph": graph.to_dict(),
                "seats": {"checker": {"agent": agent, "trust_domain": "TESTER"}},
                "max_steps": 3,
            }
        ),
    )
    return {"RULE": rule, "SKILL": skill, "AGENT": agent, "WORKFLOW": workflow}


@pytest.mark.parametrize("kind", ["RULE", "SKILL", "AGENT", "WORKFLOW"])
def test_artifact_routes_execute_loaded_content(tmp_path, artifacts, kind):
    budget = Budget()
    executor = FixtureExecutor(budget)
    runtime = ArtifactRuntime(
        tmp_path, executor, CallerContext("fixture", "fixture-model", "parent", budget)
    )
    result = runtime.run(kind, artifacts[kind], "Validate this missing manifest")
    assert result.output == "BLOCKED"
    assert artifacts[kind] in result.invoked
    assert len(executor.calls) == (2 if kind == "WORKFLOW" else 1)
    assert budget.remaining_microusd == 100 - len(executor.calls)
    if kind in {"AGENT", "WORKFLOW"}:
        assert artifacts["SKILL"] in result.invoked


def test_missing_executor_and_different_budget_are_blocked():
    context = CallerContext("fixture", "fixture-model", "parent", Budget())
    with pytest.raises(LearningBlocked, match="EXECUTOR_UNAVAILABLE"):
        call_parent(None, context, seat="test", prompt="test")
    with pytest.raises(LearningBlocked, match="BUDGET_BINDING"):
        call_parent(FixtureExecutor(Budget()), context, seat="test", prompt="test")


def test_workflow_graph_derives_new_id_but_refuses_a_false_supplied_id(tmp_path, artifacts):
    wire = json.loads((tmp_path / artifacts["WORKFLOW"]).read_text())["graph"]
    expected = wire.pop("graph_id")
    assert compile_workflow_graph(wire).graph_id == expected
    wire["graph_id"] = "false-graph-id"
    with pytest.raises(ValueError):
        compile_workflow_graph(wire)


def test_insufficient_allowance_for_next_provider_turn_is_blocked():
    class RefusingExecutor(FixtureExecutor):
        def __call__(self, request):
            raise BudgetExceeded(requested=101, limit=100)

    budget = Budget()
    context = CallerContext("fixture", "fixture-model", "parent", budget)
    with pytest.raises(LearningBlocked, match="PARENT_BUDGET_EXHAUSTED"):
        call_parent(RefusingExecutor(budget), context, seat="test", prompt="test")
    assert budget.remaining_microusd == 100


def test_workflow_refuses_unknown_seat_and_unlicensed_agent(tmp_path, artifacts):
    budget = Budget()
    runtime = ArtifactRuntime(
        tmp_path,
        FixtureExecutor(budget),
        CallerContext("fixture", "fixture-model", "parent", budget),
    )
    path = tmp_path / artifacts["AGENT"]
    path.write_text(path.read_text().replace("tools: []", "tools: [shell]"), encoding="utf-8")
    with pytest.raises(LearningBlocked, match="CAPABILITY_BINDING"):
        runtime.run("WORKFLOW", artifacts["WORKFLOW"], "Test")
    assert budget.remaining_microusd == 100


def test_merged_retrieval_runs_and_records_actual_usage(tmp_path, artifacts):
    command(tmp_path, "git", "init", "-b", "main")
    command(tmp_path, "git", "config", "user.email", "test@example.invalid")
    command(tmp_path, "git", "config", "user.name", "Test")
    artifact = artifacts["AGENT"]
    entry = {
        "artifact_id": artifact,
        "kind": "AGENT",
        "candidate_id": "candidate",
        "trigger_terms": ["manifest"],
        "files": {
            name: artifact_text_digest((tmp_path / name).read_bytes())
            for name in (artifact, artifacts["SKILL"])
        },
    }
    registry = "operads/registry/autop_artifacts.json"
    write(tmp_path, registry, json.dumps([entry]))
    command(tmp_path, "git", "add", "--", *artifacts.values(), registry)
    command(tmp_path, "git", "commit", "-m", "reviewed artifacts")
    command(tmp_path, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
    budget = Budget()
    completion = build_learning_completion(
        tmp_path,
        executor=FixtureExecutor(budget),
        context=CallerContext("fixture", "fixture-model", "parent", budget),
    )
    assert completion.prepare("Check a missing manifest", "next-run") == "BLOCKED"
    with completion.service.store.connect() as db:
        records = [json.loads(r[0]) for r in db.execute("SELECT payload FROM observations")]
    assert {r["phase"] for r in records} == {"selected", "invoked", "completed"}
    assert any(r["artifact_id"] == artifacts["SKILL"] for r in records)
    assert list((tmp_path / "runs/skill_usage").glob("*.jsonl"))
    source = tmp_path / "parent_run"
    write(
        source, "receipt.json", json.dumps({"task_key": "next-run", "terminal_verdict": "REFUSE"})
    )
    completion.completed(str(source), outcome="REFUSE")
    with completion.service.store.connect() as db:
        observed = [json.loads(r[0]) for r in db.execute("SELECT payload FROM observations")]
    assert any(r["phase"] == "task_completed" and r["outcome"] == "REFUSE" for r in observed)
    assert completion.prepare("unrelated request", "unrelated-run") == ""
    write(tmp_path, artifact, "unreviewed change")
    with pytest.raises(ValueError, match="bytes differ"):
        completion.prepare("manifest", "dirty-run")


def test_unmerged_registry_is_not_retrieved(tmp_path, artifacts):
    command(tmp_path, "git", "init", "-b", "main")
    command(tmp_path, "git", "config", "user.email", "test@example.invalid")
    command(tmp_path, "git", "config", "user.name", "Test")
    command(tmp_path, "git", "add", "--", *artifacts.values())
    command(tmp_path, "git", "commit", "-m", "base")
    command(tmp_path, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
    write(tmp_path, "operads/registry/autop_artifacts.json", "[]")
    budget = Budget()
    executor = FixtureExecutor(budget)
    completion = build_learning_completion(
        tmp_path,
        executor=executor,
        context=CallerContext("fixture", "fixture-model", "parent", budget),
    )
    assert completion.prepare("manifest", "new-run") == ""
    assert not executor.calls
