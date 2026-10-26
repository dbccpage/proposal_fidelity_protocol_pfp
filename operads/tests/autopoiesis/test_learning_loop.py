"""Behavioral regressions for evidence capture, admission and budget custody."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest

from omega_engine_operads.application.autopoiesis.learning import LearningService
from omega_engine_operads.domain.autopoiesis.learning import (
    CallerContext,
    EvaluationCase,
    FileChange,
    LearningBlocked,
    LearningCandidate,
)
from omega_engine_operads.infrastructure.autopoiesis.agent_learning import (
    CommandEvaluationSuite,
)
from omega_engine_operads.infrastructure.autopoiesis.git_learning import (
    GitLearningWorkspace,
    command,
)
from omega_engine_operads.infrastructure.autopoiesis.intake import capture_episode
from omega_engine_operads.infrastructure.autopoiesis.learning_runtime import (
    build_learning_completion,
)


class Budget:
    def __init__(self, remaining=100):
        self.remaining_microusd = remaining


class CapturedProposal:
    def __init__(self, candidate):
        self.candidate = candidate
        self.calls = 0

    def propose(self, episode, sources, catalog, context):
        assert all(s.sha256 in sources for s in episode.sources)
        self.calls += 1
        return self.candidate


class RecordingPublisher:
    def __init__(self):
        self.calls = []

    def publish(self, workspace, candidate, validation):
        assert command(Path(workspace), "git", "rev-parse", "HEAD") == validation["commit"]
        self.calls.append(validation)
        return "https://github.com/example/fixture/pull/1"


def episode_at(tmp_path, store, content=None):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            content
            if content is not None
            else {
                "corrections": [
                    {"confidence": "HIGH", "text": "Require a manifest before returning PASS."}
                ],
                "successful_approaches": ["Check exact source bytes first."],
            }
        ),
        encoding="utf-8",
    )
    return capture_episode((source,), "codex", "revision", store.vault)


def test_corrections_and_successes_preserve_all_sources(tmp_path, store):
    episode = episode_at(tmp_path, store)
    assert episode.corrections == ("Require a manifest before returning PASS.",)
    assert episode.successes == ("Check exact source bytes first.",)
    assert json.loads(store.vault.get_file(episode.sources[0].sha256))["corrections"]
    decimal = episode_at(
        tmp_path, store, {"score": 0.5, "errors": [{"observed": 1e-9}]}
    )
    assert decimal.errors == ('{"observed":1e-09}',)
    many = tmp_path / "many.json"
    many.write_text(json.dumps({"errors": [str(i) for i in range(30)]}), encoding="utf-8")
    assert len(capture_episode((many,), "claude", "revision", store.vault).errors) == 30


def test_missing_empty_and_malformed_input_never_pass(tmp_path, store):
    with pytest.raises(LearningBlocked, match="SOURCE_EVIDENCE_MISSING"):
        capture_episode((), "codex", "revision", store.vault)
    bad = tmp_path / "bad.json"
    bad.write_text('{"corrections":', encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        capture_episode((bad,), "codex", "revision", store.vault)
    bad.write_text('{"corrections": [false]}', encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        capture_episode((bad,), "codex", "revision", store.vault)
    bad.write_text("", encoding="utf-8")
    with pytest.raises(LearningBlocked, match="EMPTY"):
        capture_episode((bad,), "codex", "revision", store.vault)


def test_empty_capture_and_missing_runtime_have_immutable_receipts(tmp_path):
    command(tmp_path, "git", "init", "-b", "main")
    command(tmp_path, "git", "config", "user.email", "test@example.invalid")
    command(tmp_path, "git", "config", "user.name", "Test")
    (tmp_path / "file").write_text("base", encoding="utf-8")
    command(tmp_path, "git", "add", "file")
    command(tmp_path, "git", "commit", "-m", "base")
    completion = build_learning_completion(tmp_path)
    empty = completion.import_paths((), host="codex")
    assert empty["overall_status"] == "BLOCKED"
    source = tmp_path / "input.json"
    source.write_text('{"corrections":["Fix the check"]}', encoding="utf-8")
    captured = completion.import_paths((source,), host="codex")
    assert captured["overall_status"] == "BLOCKED"
    assert captured["reason"] == "CALLER_CONFIGURATION_MISSING"
    receipts = list((completion.service.store.root / "receipts").glob("*.json"))
    assert len(receipts) == 2


def configured(repo, tmp_path, store, *, broken=False):
    episode = episode_at(tmp_path, store)
    candidate = LearningCandidate(
        "CODE_GATE",
        "gate.py",
        "Require a manifest",
        "Reject absent source evidence.",
        (
            FileChange(
                "gate.py", "import sys\nprint('BLOCKED' if sys.argv[1] == 'missing' else 'PASS')\n"
            ),
        ),
        "manifest",
        "missing",
        (episode.sources[0].sha256,),
        ("manifest",),
    )
    cases = tuple(
        EvaluationCase(
            name, role, "", json.dumps({"returncode": 0, "stdout": expected}, sort_keys=True)
        )
        for name, role, expected in (
            ("missing", "motivating", "BLOCKED"),
            ("present", "applicable", "PASS"),
            ("unrelated", "non_applicable", "PASS"),
        )
    )
    suite = CommandEvaluationSuite(
        "manifest",
        cases,
        ("gate.py",),
        {c.case_id: [sys.executable, "gate.py", c.case_id] for c in cases},
    )
    if broken:
        candidate = replace(candidate, changes=(FileChange("gate.py", "print('BLOCKED')\n"),))
    proposer, publisher = CapturedProposal(candidate), RecordingPublisher()
    service = LearningService(
        store, GitLearningWorkspace(repo, tmp_path / "candidates"), proposer, (suite,), publisher
    )
    context = CallerContext("fixture", "fixture-model", "parent-budget", Budget())
    return service, episode, context, proposer, publisher


def test_real_git_and_command_replay_admit_only_repaired_behavior(repo, tmp_path, store):
    service, episode, context, proposer, publisher = configured(repo, tmp_path, store)
    result = service.run(episode, context)
    assert result["overall_status"] == "VALIDATED", result
    assert result["deployed"] is False
    assert len(publisher.calls) == 1
    assert [r["passed"] for r in result["validation"]["before"]] == [False, True, True]
    assert all(r["passed"] for r in result["validation"]["after"])
    oracle = json.loads(store.vault.get_file(result["validation"]["oracle_source_sha256"]))
    assert {c["role"] for c in oracle["cases"]} == {"motivating", "applicable", "non_applicable"}
    observed = result["validation"]["after"][0]
    assert json.loads(store.vault.get_file(observed["observation_sha256"]))["output"]
    assert command(repo, "git", "show", "HEAD:gate.py").endswith("else 'PASS')")
    assert service.run(episode, context)["receipt_id"] == result["receipt_id"]
    assert (
        service.run(replace(episode, repository_revision="later-revision"), context)["receipt_id"]
        == result["receipt_id"]
    )
    assert proposer.calls == 1


def test_existing_file_must_be_read_before_editing(repo, tmp_path, store):
    service, episode, _, proposer, _ = configured(repo, tmp_path, store)
    workspace = service.workspace
    suite = service.evaluations["manifest"]
    assert "gate.py" not in workspace.catalog(episode)
    with pytest.raises(LearningBlocked, match="EXISTING_ARTIFACT_NOT_READ"):
        workspace.prepare("unread", proposer.candidate, suite)
    assert "import sys" in workspace.catalog(episode, allowed_paths=suite.allowed_paths)["gate.py"]


def test_skill_candidate_runs_real_packaging_and_budget_gate(repo, tmp_path, store, monkeypatch):
    scripts = (
        "omega_engine_operations/use_cases/packaging/sync_cross_host_skills.py",
        "omega_engine_operads/skill_operad/skill_compiler/budget_gate.py",
    )
    implementation_root = Path(__file__).resolve().parents[3]
    # The production composition root injects recovery/locking dependencies;
    # load it from the implementation under test, with writes pinned to checkout.
    monkeypatch.setenv("PYTHONPATH", str(implementation_root))
    for relative in scripts:
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((implementation_root / relative).read_bytes())
    (repo / "omega_engine").mkdir()
    (repo / "omega_engine/README.md").write_text(
        "Repository marker for the packaging harness.", encoding="utf-8"
    )
    command(repo, "git", "add", "--", *scripts, "omega_engine/README.md")
    command(repo, "git", "commit", "-m", "install real packaging tools")
    command(repo, "git", "push", "origin", "main")
    service, episode, _, proposer, _ = configured(repo, tmp_path, store)
    artifact = "omega_engine_operads/skills/fixture/SKILL.md"
    content = "---\nname: fixture\ndescription: Check manifests\n---\nCheck the manifest before passing.\n"
    candidate = replace(
        proposer.candidate,
        kind="SKILL",
        artifact_id=artifact,
        changes=(FileChange(artifact, content),),
    )
    suite = service.evaluations["manifest"]
    suite.allowed_paths = (artifact,)
    workspace = service.workspace
    workspace.catalog(episode, allowed_paths=suite.allowed_paths)
    checkout = workspace.prepare("skill-packaging", candidate, suite)
    commit = workspace.apply(checkout, candidate, suite)
    workspace.verify(checkout, commit)
    for host in (".agents", ".claude", ".codex", ".grok"):
        assert (checkout / host / "skills/fixture/SKILL.md").read_text(encoding="utf-8") == content


def test_held_out_regression_blocks_publication(repo, tmp_path, store):
    service, episode, context, _, publisher = configured(repo, tmp_path, store, broken=True)
    result = service.run(episode, context)
    assert result["overall_status"] == "BLOCKED"
    assert result["reason"] == "BENEFIT_OR_RUNTIME_INVOCATION_NOT_ESTABLISHED"
    assert not publisher.calls
    repaired = replace(
        service.proposer.candidate,
        changes=(
            FileChange(
                "gate.py", "import sys\nprint('BLOCKED' if sys.argv[1] == 'missing' else 'PASS')\n"
            ),
        ),
    )
    service.proposer.candidate = repaired
    assert service.run(episode, context, retry=True)["overall_status"] == "VALIDATED"


def test_concurrent_duplicate_completion_runs_once(repo, tmp_path, store):
    service, episode, context, proposer, publisher = configured(repo, tmp_path, store)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: service.run(episode, context), range(2)))
    assert results[0]["receipt_id"] == results[1]["receipt_id"]
    assert len(publisher.calls) == proposer.calls == 1


def test_budget_exhaustion_and_recursion_do_not_call_proposer(repo, tmp_path, store):
    service, episode, context, proposer, _ = configured(repo, tmp_path, store)
    context.budget.remaining_microusd = 0
    assert service.run(episode, context)["reason"] == "PARENT_BUDGET_EXHAUSTED"
    recursive = replace(episode, origin="autop")
    assert service.run(recursive, context)["reason"] == "RECURSION_SUPPRESSED"
    with store.connect() as db:
        assert db.execute("SELECT count(*) FROM jobs").fetchone()[0] == 1
    assert proposer.calls == 0
    context.budget.remaining_microusd = 100
    assert service.run(episode, context, retry=True)["overall_status"] == "VALIDATED"


def test_missing_miner_evaluator_and_proposal_are_distinct(repo, tmp_path, store):
    service, episode, context, proposer, publisher = configured(repo, tmp_path, store)
    service.proposer = None
    assert service.run(episode, context)["reason"] == "PROPOSER_UNAVAILABLE"
    service.proposer = proposer
    suites = service.evaluations
    service.evaluations = {}
    assert (
        service.run(episode, context, retry=True)["reason"] == "INDEPENDENT_EVALUATOR_UNAVAILABLE"
    )
    proposer.candidate = None
    service.evaluations = suites
    assert service.run(episode, context, retry=True)["overall_status"] == "NO_CHANGE"
    assert not publisher.calls


def test_model_dependent_cases_require_three_paired_trials(repo, tmp_path, store):
    service, episode, context, _, _ = configured(repo, tmp_path, store)
    suite = service.evaluations["manifest"]
    suite.model_dependent = True
    result = service.run(episode, context)
    assert result["overall_status"] == "VALIDATED", result
    assert result["validation"]["trials"] == 3
    assert len(result["validation"]["before"]) == len(result["validation"]["after"]) == 9


def test_budget_stops_between_cases_and_preserves_partial_evidence(repo, tmp_path, store):
    service, episode, context, _, publisher = configured(repo, tmp_path, store)
    original = service.evaluations["manifest"]

    class ChargedCommands(CommandEvaluationSuite):
        def run(self, root, candidate, case, context, trial):
            observed = super().run(root, candidate, case, context, trial)
            context.budget.remaining_microusd -= 10
            return observed

    service.evaluations["manifest"] = ChargedCommands(
        original.evaluation_id, original.cases, original.allowed_paths, original.commands
    )
    context.budget.remaining_microusd = 20
    result = service.run(episode, context)
    assert result["overall_status"] == "BLOCKED"
    assert result["reason"] == "PARENT_BUDGET_EXHAUSTED"
    assert len(result["evaluation_attempts"]) == 2
    assert not publisher.calls


def test_evaluator_mutation_of_tracked_source_is_rejected(repo, tmp_path, store):
    service, episode, context, _, publisher = configured(repo, tmp_path, store)
    original = service.evaluations["manifest"]

    class MutatingCommands(CommandEvaluationSuite):
        def run(self, root, candidate, case, context, trial):
            observed = super().run(root, candidate, case, context, trial)
            with (Path(root) / "gate.py").open("a", encoding="utf-8") as output:
                output.write("\n# evaluator changed the candidate\n")
            return observed

    service.evaluations["manifest"] = MutatingCommands(
        original.evaluation_id, original.cases, original.allowed_paths, original.commands
    )
    result = service.run(episode, context)
    assert result["overall_status"] == "FAILED"
    assert "evaluator changed tracked files" in result["reason"]
    assert not publisher.calls


def test_linked_parent_source_is_rejected(tmp_path, store):
    target = tmp_path / "real"
    target.mkdir()
    (target / "source.json").write_text('{"corrections":["check input"]}', encoding="utf-8")
    link = tmp_path / "linked"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("OS does not grant symlink creation")
    with pytest.raises(ValueError, match="linked"):
        capture_episode((link / "source.json",), "codex", "revision", store.vault)
