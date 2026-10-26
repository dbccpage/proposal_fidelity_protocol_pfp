"""Composition for explicit host imports and Woland completion notifications."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from omega_engine_operads.application.autopoiesis.learning import LearningService
from omega_engine_operads.domain.autopoiesis.learning import (
    CallerContext,
    artifact_text_digest,
)
from omega_engine_operads.infrastructure.autopoiesis.intake import capture_episode
from omega_engine_operads.infrastructure.skill_garden.transcript_harvester import (
    iter_skill_invocations,
)
from omega_engine_operads.infrastructure.skill_garden.usage_ledger import (
    append_usage_events,
    garden_roster,
    make_usage_event,
    normalize_skill_id,
)

from .agent_learning import (
    ArtifactEvaluationSuite,
    ArtifactRuntime,
    CommandEvaluationSuite,
    SeatLearningProposer,
)
from .git_learning import GitHubLearningPublisher, GitLearningWorkspace, command
from .learning_store import LearningStore


class EvidenceTurnExecutor:
    """Preserve actual requests and replies without creating another budget."""

    def __init__(self, executor, vault):
        self.executor, self.vault = executor, vault
        self.budget_controller = getattr(executor, "budget_controller", None)
        self.trace_refs: list[str] = []

    @property
    def cascade_models(self):
        return getattr(self.executor, "cascade_models", None)

    def __call__(self, request):
        from dataclasses import asdict

        from omega_engine_operads.domain.autopoiesis.learning import canonical

        material = {"request": asdict(request), "origin": "autop"}
        material["request"]["context_bytes"] = request.context_bytes.hex()
        try:
            reply = self.executor(request)
            material["reply"] = asdict(reply)
            material["reply"]["raw_bytes"] = reply.raw_bytes.hex()
        except Exception as exc:
            material["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            raw = canonical(material)
            sha = hashlib.sha256(raw).hexdigest()
            self.vault.put_file(raw, sha)
            self.trace_refs.append(sha)
        return reply


class LearningCompletion:
    def __init__(
        self, repository: Path, service: LearningService, context=None, configuration_reference=None
    ):
        self.repository, self.service, self.context = repository, service, context
        self.configuration_reference = configuration_reference
        self.last_receipt: dict | None = None
        self._selected_by_run: dict[str, dict] = {}

    def import_paths(self, paths, *, host, outcome="UNKNOWN", origin="session", retry=False):
        try:
            revision = command(self.repository, "git", "rev-parse", "HEAD")
            episode = capture_episode(
                tuple(paths),
                host,
                revision,
                self.service.store.vault,
                outcome=outcome,
                origin=origin,
            )
            episode = replace(
                episode,
                caller_configuration_reference=self.configuration_reference,
                caller_budget_reference=self.context.budget_reference if self.context else None,
            )
            self.last_receipt = self.service.run(episode, self.context, retry=retry)
            if host == "claude":
                roster = garden_roster(self.repository)
                events = []
                for path in paths:
                    if path.suffix != ".jsonl":
                        continue
                    for event in iter_skill_invocations(path):
                        skill = normalize_skill_id(event.get("raw", ""), roster)
                        if skill:
                            events.append(
                                make_usage_event(
                                    skill_id=skill,
                                    invoked_at=event.get("invoked_at", "unknown"),
                                    host=host,
                                    session_id=episode.episode_id,
                                )
                            )
                append_usage_events(self.repository, events)
            return self.last_receipt
        except Exception as exc:
            # A failed intake still gets an immutable receipt, but never an
            # invented source episode. It must not alter the parent verdict.
            from omega_engine_operads.domain.autopoiesis.learning import (
                LearningBlocked,
                digest,
            )

            job_id = digest(
                {
                    "paths": [str(p) for p in paths],
                    "failure": str(exc),
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            with self.service.store.connect() as db:
                self.last_receipt = self.service.store.finish(
                    db,
                    job_id,
                    {
                        "overall_status": "BLOCKED"
                        if isinstance(exc, (LearningBlocked, FileNotFoundError))
                        else "FAILED",
                        "mode": "learning",
                        "reason": f"{type(exc).__name__}: {exc}",
                    },
                )
            return self.last_receipt

    def completed(self, run_directory: str, *, outcome: str, origin: str = "session") -> None:
        folder = Path(run_directory)
        parent_receipt = folder / "receipt.json"
        if not parent_receipt.is_file():
            self.import_paths((parent_receipt,), host="woland", outcome=outcome, origin=origin)
            return
        if parent_receipt.is_file():
            raw = parent_receipt.read_bytes()
            try:
                wire = json.loads(raw)
                run_id = wire.get("task_key") if isinstance(wire, dict) else None
            except (ValueError, UnicodeDecodeError):
                run_id = None
            selected = self._selected_by_run.pop(run_id, None)
            if selected:
                self.observe_use(
                    artifact_id=selected["artifact_id"],
                    kind=selected["kind"],
                    phase="task_completed",
                    run_id=run_id,
                    outcome=outcome,
                    source_hash=hashlib.sha256(raw).hexdigest(),
                )
        paths = tuple(
            folder / name
            for name in (
                "receipt.json",
                "summary.json",
                "novella.md",
                "uns.md",
                "dda_actions.jsonl",
                "ddc.jsonl",
                "uts.jsonl",
            )
            if (folder / name).is_file() and (folder / name).stat().st_size
        )
        self.import_paths(paths, host="woland", outcome=outcome, origin=origin)

    def prepare(self, objective: str, run_id: str) -> str:
        """Retrieve only merged, locally identical artifacts for the next run."""
        if self.context is None:
            return ""
        self.context.require_available()
        registry = "omega_engine_operads/registry/autop_artifacts.json"
        # Absence on the fetched deployment ref means no deployed artifacts,
        # even if a candidate worktree contains an experimental registry.
        present = command(
            self.repository, "git", "ls-tree", "--name-only", "origin/main", "--", registry
        )
        if not present:
            return ""
        entries = json.loads(command(self.repository, "git", "show", f"origin/main:{registry}"))
        matches = [
            e
            for e in entries
            if e.get("trigger_terms")
            and all(t.casefold() in objective.casefold() for t in e["trigger_terms"])
        ]
        for entry in sorted(
            matches, key=lambda e: (-sum(map(len, e["trigger_terms"])), e["artifact_id"])
        ):
            if entry["kind"] == "CODE_GATE":
                continue
            for name, expected in entry["files"].items():
                if artifact_text_digest((self.repository / name).read_bytes()) != expected:
                    raise ValueError("deployed artifact bytes differ from the reviewed registry")
            artifact = entry["artifact_id"]
            self._selected_by_run[run_id] = entry
            before = self.context.budget.remaining_microusd
            self.observe_use(
                artifact_id=artifact,
                kind=entry["kind"],
                phase="selected",
                run_id=run_id,
                outcome="SELECTED",
                source_hash=entry["candidate_id"],
            )
            executor = getattr(self.service.proposer, "executor", None)
            result = ArtifactRuntime(
                self.repository, executor, self.context, deployed_ref="origin/main"
            ).run(entry["kind"], artifact, objective)
            for invoked in result.invoked:
                kind = "SKILL" if invoked.startswith("omega_engine_operads/skills/") else entry["kind"]
                self.observe_use(
                    artifact_id=invoked,
                    kind=kind,
                    phase="invoked",
                    run_id=run_id,
                    outcome="EXECUTED",
                    source_hash=entry["candidate_id"],
                )
            self.observe_use(
                artifact_id=artifact,
                kind=entry["kind"],
                phase="completed",
                run_id=run_id,
                outcome="EXECUTED_BENEFIT_NOT_MEASURED",
                source_hash=entry["candidate_id"],
                cost_microusd=before - self.context.budget.remaining_microusd,
            )
            return result.output
        return ""

    def observe_use(
        self,
        *,
        artifact_id: str,
        kind: str,
        phase: str,
        run_id: str,
        outcome: str,
        source_hash: str,
        cost_microusd: int | None = None,
    ) -> None:
        if phase not in {"selected", "invoked", "completed", "task_completed"}:
            raise ValueError("unknown observation phase")
        payload = {
            "artifact_id": artifact_id,
            "kind": kind,
            "phase": phase,
            "run_id": run_id,
            "outcome": outcome,
            "source_hash": source_hash,
            "cost_microusd": cost_microusd,
            "telemetry_coverage": "explicit_events_only",
            "authority_effect": "None",
        }
        self.service.store.observe(payload)
        if kind == "SKILL" and phase == "invoked":
            skill = Path(artifact_id).parent.name
            if skill in garden_roster(self.repository):
                append_usage_events(
                    self.repository,
                    [
                        make_usage_event(
                            skill_id=skill,
                            invoked_at=datetime.now(timezone.utc),
                            host="woland",
                            channel="autop_runtime",
                            session_id=run_id,
                            caller=artifact_id,
                        )
                    ],
                )


def build_learning_completion(
    repository: Path,
    *,
    executor=None,
    context: CallerContext | None = None,
    config_path: Path | None = None,
    store_root: Path | None = None,
) -> LearningCompletion:
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path is not None else {}
    store = LearningStore(store_root or repository / "runs" / "autop_learning")
    from omega_engine_operads.domain.autopoiesis.learning import canonical

    configuration_bytes = canonical(
        {
            "evaluations": config,
            "provider": context.provider if context else None,
            "model": context.model if context else None,
        }
    )
    configuration_reference = hashlib.sha256(configuration_bytes).hexdigest()
    store.vault.put_file(configuration_bytes, configuration_reference)
    if executor is not None:
        executor = EvidenceTurnExecutor(executor, store.vault)
    suites = []
    for spec in config.get("evaluations", []):
        if spec.get("mode", "artifact") == "command":
            suites.append(
                CommandEvaluationSuite(
                    spec["id"], spec["cases"], spec["allowed_paths"], spec["commands"]
                )
            )
        else:
            suites.append(
                ArtifactEvaluationSuite(spec["id"], spec["cases"], spec["allowed_paths"], executor)
            )
    service = LearningService(
        store,
        GitLearningWorkspace(repository, store.root / "workspaces"),
        proposer=SeatLearningProposer(executor, suites) if executor is not None else None,
        evaluations=suites,
        publisher=GitHubLearningPublisher(config["github_repository"])
        if config.get("github_repository")
        else None,
    )
    return LearningCompletion(repository, service, context, configuration_reference)
