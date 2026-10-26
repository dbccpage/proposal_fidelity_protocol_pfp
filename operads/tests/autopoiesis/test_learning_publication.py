"""Publication recovery with real Git refs and a local GitHub boundary fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_engine_operads.domain.autopoiesis.learning import LearningBlocked
from omega_engine_operads.infrastructure.autopoiesis.git_learning import (
    GitHubLearningPublisher,
    command,
)
from omega_engine_operads.tests.autopoiesis.test_learning_loop import configured


class LocalGitHub:
    def __init__(self):
        self.prs = []
        self.creates = 0
        self.fail_after_push = False

    def __call__(self, root, *args):
        if args == ("git", "remote", "get-url", "origin"):
            return "https://github.com/example/fixture.git"
        if args[0] != "gh":
            return command(root, *args)
        operation = args[2]
        if operation == "list":
            return json.dumps(self.prs)
        if operation == "create":
            if self.fail_after_push:
                raise RuntimeError("GitHub temporarily unavailable")
            self.creates += 1
            body = Path(args[args.index("--body-file") + 1]).read_text(encoding="utf-8")
            self.prs = [
                {
                    "url": "https://github.com/example/fixture/pull/1",
                    "state": "OPEN",
                    "headRefOid": command(root, "git", "rev-parse", "HEAD"),
                    "body": body,
                }
            ]
            return self.prs[0]["url"]
        if operation == "edit":
            self.prs[0]["headRefOid"] = command(root, "git", "rev-parse", "HEAD")
            return ""
        raise AssertionError(args)


def test_publication_and_duplicate_recovery_bind_exact_head(repo, tmp_path, store):
    service, episode, context, _, _ = configured(repo, tmp_path, store)
    github = LocalGitHub()
    service.publisher = GitHubLearningPublisher("example/fixture", github)
    result = service.run(episode, context)
    assert result["overall_status"] == "VALIDATED", result
    assert github.creates == 1
    path = next((tmp_path / "candidates").iterdir())
    candidate = service.proposer.candidate
    again = service.publisher.publish(str(path), candidate, result["validation"])
    assert again == result["pr_url"]
    assert github.creates == 1
    branch = f"refs/heads/codex/autop-{candidate.lesson_id[:20]}"
    assert (
        command(repo, "git", "ls-remote", "origin", branch).split()[0]
        == result["validation"]["commit"]
    )


def test_crash_between_push_and_pr_creation_is_recoverable(repo, tmp_path, store):
    service, episode, context, _, _ = configured(repo, tmp_path, store)
    github = LocalGitHub()
    github.fail_after_push = True
    service.publisher = GitHubLearningPublisher("example/fixture", github)
    failed = service.run(episode, context)
    assert failed["overall_status"] == "FAILED"
    github.fail_after_push = False
    recovered = service.run(episode, context, retry=True)
    assert recovered["overall_status"] == "VALIDATED", recovered
    assert github.creates == 1


def test_moved_remote_head_blocks_update(repo, tmp_path, store):
    service, episode, context, _, _ = configured(repo, tmp_path, store)
    github = LocalGitHub()
    service.publisher = GitHubLearningPublisher("example/fixture", github)
    result = service.run(episode, context)
    candidate = service.proposer.candidate
    branch = f"refs/heads/codex/autop-{candidate.lesson_id[:20]}"
    command(repo, "git", "push", "--force", "origin", f"HEAD:{branch}")
    path = next((tmp_path / "candidates").iterdir())
    with pytest.raises(LearningBlocked, match="PR_HEAD_CHANGED"):
        service.publisher.publish(str(path), candidate, result["validation"])
    assert github.creates == 1


def test_moved_main_requires_revalidation(repo, tmp_path, store):
    service, episode, context, _, _ = configured(repo, tmp_path, store)
    result = service.run(episode, context)
    (repo / "new_base.txt").write_text("new main", encoding="utf-8")
    command(repo, "git", "add", "new_base.txt")
    command(repo, "git", "commit", "-m", "advance base")
    command(repo, "git", "push", "origin", "main")
    path = next((tmp_path / "candidates").iterdir())
    publisher = GitHubLearningPublisher("example/fixture", LocalGitHub())
    with pytest.raises(LearningBlocked, match="BASE_MOVED"):
        publisher.publish(str(path), service.proposer.candidate, result["validation"])
