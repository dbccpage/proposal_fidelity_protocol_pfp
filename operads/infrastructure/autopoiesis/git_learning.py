"""Isolated candidate checkouts and exact-commit GitHub PR delivery."""

from __future__ import annotations

import fnmatch
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

from omega_engine_operations.use_cases.packaging.sync_cross_host_skills import HOST_SKILL_ROOTS
from omega_engine_operads.domain.autopoiesis.learning import (
    LearningBlocked,
    artifact_text_digest,
)


def command(root: Path, *args: str) -> str:
    result = subprocess.run(
        args,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed ({result.returncode}): {result.stderr[-2000:]}")
    return result.stdout.strip()


def safe_path(root: Path, relative: str) -> Path:
    name = PurePosixPath(relative)
    if (
        not relative
        or "\\" in relative
        or ":" in relative
        or name.is_absolute()
        or any(p in {"..", ".git"} for p in name.parts)
    ):
        raise ValueError("candidate path escapes its workspace")
    destination = root.joinpath(*name.parts)
    if not destination.resolve().is_relative_to(root.resolve()):
        raise ValueError("candidate path resolves outside its workspace")
    for parent in (destination, *destination.parents):
        if parent == root.parent:
            break
        if parent.is_symlink() or (
            parent.exists() and getattr(parent.stat(), "st_file_attributes", 0) & 0x400
        ):
            raise ValueError("candidate path traverses a link")
    return destination


def git_blob(root: Path, reference: str) -> bytes:
    result = subprocess.run(["git", "show", reference], cwd=root, capture_output=True, check=True)
    return result.stdout


class GitLearningWorkspace:
    def __init__(self, repository: Path, workspaces: Path, *, base_ref: str = "origin/main"):
        self.repository = repository.resolve()
        self.workspaces = workspaces.resolve()
        self.base_ref = base_ref

    def catalog(self, episode, *, allowed_paths=()) -> dict[str, str]:
        # Read committed artifacts, never another agent's dirty edits. All
        # names are offered; relevant full packages get progressively loaded.
        command(self.repository, "git", "fetch", "origin", "main")
        self.proposal_base = command(self.repository, "git", "rev-parse", self.base_ref)
        paths = command(
            self.repository,
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            self.proposal_base,
            "--",
            "omega_engine_operads/rules",
            "omega_engine_operads/skills",
            "omega_engine_operads/workflows",
            "omega_engine_operads/agents",
            "omega_engine_operads/domain/autopoiesis/profiles",
        ).splitlines()
        paths = [
            p
            for p in paths
            if p.endswith("SKILL.md") or any(part in p for part in (
                "/rules/", "/agents/", "/profiles/", "/workflows/"
            ))
        ]
        scoped = {
            p
            for p in command(
                self.repository, "git", "ls-tree", "-r", "--name-only", self.proposal_base
            ).splitlines()
            if any(fnmatch.fnmatchcase(p, pattern) for pattern in allowed_paths)
        }
        paths = sorted(set(paths) | scoped)
        words = set(
            re.findall(
                r"[a-z]{4,}",
                " ".join((*episode.corrections, *episode.errors, *episode.successes)).lower(),
            )
        )
        ranked = sorted(
            paths,
            key=lambda p: (
                p not in scoped,
                -len(words.intersection(re.findall(r"[a-z]{4,}", p.lower()))),
                p,
            ),
        )
        catalog = {"artifact_paths": "\n".join(paths)}
        for path in ranked[:12]:
            catalog[path] = command(self.repository, "git", "show", f"{self.proposal_base}:{path}")
        self.catalog_paths = set(catalog) - {"artifact_paths"}
        return catalog

    def prepare(self, job_id, candidate, suite) -> Path:
        if not getattr(suite, "allowed_paths", ()):
            raise LearningBlocked("EVALUATION_SCOPE_MISSING")
        for change in candidate.changes:
            safe_path(self.repository, change.path)
            if not any(fnmatch.fnmatchcase(change.path, p) for p in suite.allowed_paths):
                raise ValueError(f"candidate changes an unevaluated path: {change.path}")
            if change.path.startswith((
                ".github/", "omega_engine_operads/registry/workflows/", ".agents/registry/workflows/"
            )):
                raise ValueError("candidate cannot add remote CI or executable host catalogs")
            if change.path not in self.catalog_paths and command(
                self.repository,
                "git",
                "ls-tree",
                "--name-only",
                self.proposal_base,
                "--",
                change.path,
            ):
                raise LearningBlocked("EXISTING_ARTIFACT_NOT_READ: " + change.path)
        command(self.repository, "git", "fetch", "origin", "main")
        if command(self.repository, "git", "rev-parse", self.base_ref) != self.proposal_base:
            raise LearningBlocked("BASE_MOVED_SINCE_PROPOSAL")
        self.workspaces.mkdir(parents=True, exist_ok=True)
        sizes = command(self.repository, "git", "ls-tree", "-r", "-l", self.base_ref).splitlines()
        tracked_bytes = sum(
            int(row.split(None, 4)[3]) for row in sizes if row.split(None, 4)[3].isdigit()
        )
        if shutil.disk_usage(self.workspaces).free < tracked_bytes + 512 * 1024 * 1024:
            raise LearningBlocked("INSUFFICIENT_DISK_FOR_CANDIDATE_CHECKOUT")
        # Recovery gets a new checkout. Never reset/delete an old candidate
        # that may contain evidence from an interrupted validation.
        from uuid import uuid4

        path = self.workspaces / f"{job_id[:12]}-{uuid4().hex[:8]}"
        command(self.repository, "git", "worktree", "add", "--detach", str(path), self.base_ref)
        return path

    def apply(self, path: Path, candidate, suite) -> str:
        if command(path, "git", "status", "--porcelain", "--untracked-files=no"):
            raise ValueError("baseline evaluator changed tracked files")
        changed = []
        for change in candidate.changes:
            target = safe_path(path, change.path)
            if target.exists() and target.read_text(encoding="utf-8") == change.content:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(change.content.encode("utf-8"))
            changed.append(change.path)
            if change.path.startswith(("omega_engine_operads/skills/", "omega_engine_operads/rules/", "omega_engine_operads/agents/")):
                source_prefix = "omega_engine_operads/"
                suffix = change.path[len(source_prefix) :]
                for host_skills in HOST_SKILL_ROOTS:
                    host = host_skills.split("/")[0]
                    if change.path == f"{host}/{suffix}":
                        continue
                    if not command(path, "git", "ls-files", "--", host):
                        raise ValueError(f"untracked host roster entry: {host}")
                    mirrored = safe_path(path, f"{host}/{suffix}")
                    mirrored.parent.mkdir(parents=True, exist_ok=True)
                    mirrored.write_bytes(change.content.encode("utf-8"))
                    changed.append(f"{host}/{suffix}")
        if not changed:
            raise LearningBlocked("CANDIDATE_HAS_NO_CHANGE")
        registry = path / "omega_engine_operads/registry/autop_artifacts.json"
        entries = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else []
        entries = [e for e in entries if e["artifact_id"] != candidate.artifact_id]
        entries.append(
            {
                "artifact_id": candidate.artifact_id,
                "kind": candidate.kind,
                "lesson_id": candidate.lesson_id,
                "candidate_id": candidate.candidate_id,
                "trigger_terms": list(candidate.trigger_terms),
                "files": {
                    c.path: artifact_text_digest(c.content.encode("utf-8"))
                    for c in candidate.changes
                },
            }
        )
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(
            json.dumps(sorted(entries, key=lambda e: e["artifact_id"]), indent=2) + "\n",
            encoding="utf-8",
        )
        changed.append("omega_engine_operads/registry/autop_artifacts.json")
        for host_skills in HOST_SKILL_ROOTS:
            relative = host_skills.split("/")[0] + "/registry/autop_artifacts.json"
            if not command(path, "git", "ls-files", "--", host_skills):
                raise ValueError(f"untracked host roster entry: {host_skills}")
            target = safe_path(path, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(sorted(entries, key=lambda e: e["artifact_id"]), indent=2) + "\n",
                encoding="utf-8",
            )
            changed.append(relative)
        packages = sorted({p.split("/")[2] for p in changed if p.startswith("omega_engine_operads/skills/")})
        if packages:
            command(
                path,
                sys.executable,
                "-m",
                "omega_engine_operations.controllers.skill_mirror_cli",
                "--root",
                str(path),
                "--skills",
                ",".join(packages),
            )
            command(
                path,
                sys.executable,
                "omega_engine_operations/use_cases/packaging/sync_cross_host_skills.py",
                "--check",
                "--skills",
                ",".join(packages),
            )
            command(
                path,
                sys.executable,
                "omega_engine_operads/skill_operad/skill_compiler/budget_gate.py",
                "--skills",
                ",".join(packages),
            )
            roots = [f"{host}/{package}" for host in HOST_SKILL_ROOTS for package in packages]
            changed.extend(command(path, "git", "diff", "--name-only", "--", *roots).splitlines())
            changed.extend(
                command(
                    path, "git", "ls-files", "--others", "--exclude-standard", "--", *roots
                ).splitlines()
            )
        command(path, "git", "add", "--", *sorted(set(changed)))
        command(path, "git", "diff", "--cached", "--check")
        command(path, "git", "commit", "-m", f"AutoP: {candidate.lesson[:100]}")
        return command(path, "git", "rev-parse", "HEAD")

    def verify(self, path: Path, revision: str) -> None:
        if command(path, "git", "rev-parse", "HEAD") != revision:
            raise ValueError("candidate commit moved during evaluation")
        if command(path, "git", "status", "--porcelain", "--untracked-files=no"):
            raise ValueError("evaluation mutated candidate files")


class GitHubLearningPublisher:
    def __init__(self, repository: str, command_runner=command):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("expected owner/repository")
        self.repository = repository
        self.command = command_runner

    def publish(self, workspace: str, candidate, validation: dict) -> str:
        command = self.command
        root = Path(workspace)
        head = command(root, "git", "rev-parse", "HEAD")
        if head != validation["commit"] or command(root, "git", "status", "--porcelain", "-uno"):
            raise ValueError("publication requires the clean evaluated commit")
        remote_url = command(root, "git", "remote", "get-url", "origin")
        expected_urls = {
            f"https://github.com/{self.repository}",
            f"https://github.com/{self.repository}.git",
            f"git@github.com:{self.repository}.git",
        }
        if remote_url not in expected_urls:
            raise LearningBlocked("GITHUB_DESTINATION_DIFFERS_FROM_ORIGIN")
        command(root, "git", "fetch", "origin", "main")
        if command(root, "git", "rev-parse", "HEAD^") != command(
            root, "git", "rev-parse", "origin/main"
        ):
            raise LearningBlocked("BASE_MOVED_REVALIDATION_REQUIRED")
        branch = f"codex/autop-{candidate.lesson_id[:20]}"
        found = json.loads(
            command(
                root,
                "gh",
                "pr",
                "list",
                "--repo",
                self.repository,
                "--head",
                branch,
                "--state",
                "all",
                "--json",
                "url,state,headRefOid,body",
            )
        )
        if found and found[0]["state"] == "MERGED":
            if f"<!-- autop-lesson:{candidate.lesson_id} -->" not in found[0]["body"]:
                raise LearningBlocked("PR_OWNERSHIP_NOT_ESTABLISHED")
            branch += "-" + candidate.candidate_id[:12]
            found = json.loads(
                command(
                    root,
                    "gh",
                    "pr",
                    "list",
                    "--repo",
                    self.repository,
                    "--head",
                    branch,
                    "--state",
                    "all",
                    "--json",
                    "url,state,headRefOid,body",
                )
            )
        remote = command(root, "git", "ls-remote", "origin", f"refs/heads/{branch}")
        remote_head = remote.split()[0] if remote else ""
        if found:
            pr = found[0]
            if pr["state"] != "OPEN":
                raise LearningBlocked("PREVIOUS_PR_CLOSED_REVIEW_REQUIRED")
            if f"<!-- autop-lesson:{candidate.lesson_id} -->" not in pr["body"]:
                raise LearningBlocked("PR_OWNERSHIP_NOT_ESTABLISHED")
            if remote_head != pr["headRefOid"]:
                raise LearningBlocked("PR_HEAD_CHANGED")
            if pr["headRefOid"] == head:
                return pr["url"]
        elif remote_head:
            # Recover a crash after push but before PR creation. Only replace
            # our own evidence-bound candidate branch, never an unrelated ref.
            command(root, "git", "fetch", "origin", f"refs/heads/{branch}")
            registry = json.loads(
                command(root, "git", "show", "FETCH_HEAD:omega_engine_operads/registry/autop_artifacts.json")
            )
            if not any(
                e.get("lesson_id") == candidate.lesson_id
                and e.get("candidate_id") == candidate.candidate_id
                for e in registry
            ):
                raise LearningBlocked("EXISTING_BRANCH_OWNERSHIP_NOT_ESTABLISHED")
        command(
            root,
            "git",
            "push",
            f"--force-with-lease=refs/heads/{branch}:{remote_head}",
            "origin",
            f"HEAD:refs/heads/{branch}",
        )
        body = (
            f"<!-- autop-lesson:{candidate.lesson_id} -->\n"
            f"{candidate.lesson}\n\n{candidate.rationale}\n\n"
            f"Kind: {candidate.kind}; artifact: {candidate.artifact_id}.\n\n"
            f"Locally validated commit: `{head}`. Fixed oracle: `{validation['oracle_sha256']}`. "
            f"Trials per case: {validation['trials']}.\n\n"
            "Motivating, held-out applicable, and non-applicable cases passed. "
            "This is scoped replay evidence; subsequent production benefit is not yet observed.\n\n"
            f"Candidate: `{candidate.candidate_id}`. AuthorityEffect: None.\n"
        )
        body_path = (
            Path(command(root, "git", "rev-parse", "--absolute-git-dir")) / "autop-pr-body.md"
        )
        body_path.write_text(body, encoding="utf-8")
        if found:
            command(root, "gh", "pr", "edit", found[0]["url"], "--body-file", str(body_path))
            return found[0]["url"]
        try:
            return command(
                root,
                "gh",
                "pr",
                "create",
                "--repo",
                self.repository,
                "--base",
                "main",
                "--head",
                branch,
                "--title",
                f"AutoP: {candidate.lesson[:100]}",
                "--body-file",
                str(body_path),
            )
        except RuntimeError:
            recovered = json.loads(
                command(
                    root,
                    "gh",
                    "pr",
                    "list",
                    "--repo",
                    self.repository,
                    "--head",
                    branch,
                    "--state",
                    "open",
                    "--json",
                    "url,headRefOid,body",
                )
            )
            if (
                len(recovered) == 1
                and recovered[0]["headRefOid"] == head
                and f"<!-- autop-lesson:{candidate.lesson_id} -->" in recovered[0]["body"]
            ):
                return recovered[0]["url"]
            raise
