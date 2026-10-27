"""Evaluate learning through inward collaborator ports. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Sequence

from operads.domain.autopoiesis.learning import (
    CallerContext,
    EvaluationPort,
    LearningBlocked,
    LearningEpisodeV1,
    LearningStorePort,
    LearningWorkspacePort,
    ProposerPort,
    PublisherPort,
    canonical,
    digest,
)


class LearningService:
    """One bounded cycle; collaborators are injected by the composition root."""

    def __init__(
        self,
        store: LearningStorePort,
        workspace: LearningWorkspacePort,
        proposer: ProposerPort | None = None,
        evaluations: Sequence[EvaluationPort] = (),
        publisher: PublisherPort | None = None,
    ) -> None:
        self.store = store
        self.workspace = workspace
        self.proposer = proposer
        self.evaluations = {e.evaluation_id: e for e in evaluations}
        self.publisher = publisher

    def run(
        self, episode: LearningEpisodeV1, context: CallerContext | None, *, retry: bool = False
    ) -> dict:
        if episode.origin == "autop":
            # Preserve a suppression receipt without adding a learning job.
            return self.store.finish_receipt(
                digest(["suppressed", episode.episode_id]),
                {
                    "episode_id": episode.episode_id,
                    "source_hashes": [source.sha256 for source in episode.sources],
                    "mode": "learning",
                    "overall_status": "NO_CHANGE",
                    "reason": "RECURSION_SUPPRESSED",
                },
            )
        job_id = self.store.enqueue(episode)
        with self.store.serial(job_id, retry=retry) as (session, previous):
            if previous is not None:
                return previous
            details = {
                "episode_id": episode.episode_id,
                "mode": "learning",
                "repository_revision": episode.repository_revision,
                "source_hashes": [s.sha256 for s in episode.sources],
            }
            candidate = None
            executor = getattr(self.proposer, "executor", None)
            trace_start = len(getattr(executor, "trace_refs", ()))
            try:
                if context is None:
                    raise LearningBlocked("CALLER_CONFIGURATION_MISSING")
                context.require_available()
                details["caller"] = {
                    "provider": context.provider,
                    "model": context.model,
                    "budget_reference": context.budget_reference,
                    "remaining_before": context.budget.remaining_microusd,
                }
                if self.proposer is None:
                    raise LearningBlocked("PROPOSER_UNAVAILABLE")
                if not self.evaluations:
                    raise LearningBlocked("INDEPENDENT_EVALUATOR_UNAVAILABLE")
                sources = {}
                for source in episode.sources:
                    raw = self.store.vault.get_file(source.sha256)
                    if raw is None:
                        raise LearningBlocked("SOURCE_BYTES_UNAVAILABLE")
                    sources[source.sha256] = raw.decode("utf-8")
                scopes = {
                    p
                    for suite in self.evaluations.values()
                    for p in getattr(suite, "allowed_paths", ())
                }
                catalog = self.workspace.catalog(episode, allowed_paths=scopes)
                candidate = self.proposer.propose(episode, sources, catalog, context)
                if candidate is None:
                    return session.finish(
                        job_id,
                        {**details, "overall_status": "NO_CHANGE", "reason": "NO_SUPPORTED_CHANGE"},
                    )
                details["candidate"] = asdict(candidate)
                if not candidate.source_hashes or not set(candidate.source_hashes).issubset(
                    sources
                ):
                    raise ValueError("candidate source binding is absent or foreign")
                known = session.lookup_lesson(candidate.lesson_id)
                if (
                    known
                    and known.outcome in {"VALIDATED", "REJECTED"}
                    and known.candidate_id == candidate.candidate_id
                ):
                    return session.finish(
                        job_id,
                        {
                            **details,
                            "overall_status": "NO_CHANGE",
                            "reason": "LESSON_ALREADY_REVIEWED",
                            "pr_url": known.url,
                        },
                    )
                suite = self.evaluations.get(candidate.evaluation_id)
                if suite is None:
                    raise LearningBlocked("INDEPENDENT_EVALUATOR_UNAVAILABLE")
                roles = {c.role for c in suite.cases}
                if not {"motivating", "applicable", "non_applicable"}.issubset(roles):
                    raise LearningBlocked("HELD_OUT_CASES_MISSING")
                if candidate.motivating_case not in {
                    c.case_id for c in suite.cases if c.role == "motivating"
                }:
                    raise ValueError("motivating case is not in the fixed evaluation suite")
                if len({c.case_id for c in suite.cases}) != len(suite.cases):
                    raise ValueError("duplicate evaluation case ids")
                oracle_hash = digest([asdict(c) for c in suite.cases])
                oracle = canonical(
                    {
                        "cases": [asdict(c) for c in suite.cases],
                        "commands": getattr(suite, "commands", {}),
                        "allowed_paths": list(getattr(suite, "allowed_paths", ())),
                        "model_dependent": suite.model_dependent,
                    }
                )
                oracle_source_hash = hashlib.sha256(oracle).hexdigest()
                self.store.vault.put_file(oracle, oracle_source_hash)
                path = self.workspace.prepare(job_id, candidate, suite)
                trials = 3 if suite.model_dependent else 1

                details["evaluation_attempts"] = []

                def evaluate(phase: str) -> list[dict]:
                    rows = []
                    for case in suite.cases:
                        for trial in range(trials):
                            context.require_available()
                            observation = suite.run(str(path), candidate, case, context, trial)
                            observation_bytes = canonical(asdict(observation))
                            observation_hash = hashlib.sha256(observation_bytes).hexdigest()
                            self.store.vault.put_file(observation_bytes, observation_hash)
                            rows.append(
                                {
                                    "case": case.case_id,
                                    "role": case.role,
                                    "trial": trial,
                                    "passed": observation.output == case.expected,
                                    "output_sha256": digest(observation.output),
                                    "observation_sha256": observation_hash,
                                    "invoked": list(observation.invoked),
                                }
                            )
                            details["evaluation_attempts"].append({"phase": phase, **rows[-1]})
                    return rows

                before = evaluate("baseline")
                revision = self.workspace.apply(path, candidate, suite)
                after = evaluate("candidate")
                if digest([asdict(c) for c in suite.cases]) != oracle_hash:
                    raise ValueError("evaluation oracle changed")
                self.workspace.verify(path, revision)
                improved = any(
                    not b["passed"] and a["passed"]
                    for b, a in zip(before, after)
                    if a["role"] == "motivating"
                )
                invoked = any(candidate.artifact_id in row["invoked"] for row in after)
                accepted = improved and all(row["passed"] for row in after)
                if candidate.kind in {"AGENT", "WORKFLOW", "SKILL"}:
                    accepted = accepted and invoked
                validation = {
                    "candidate_id": candidate.candidate_id,
                    "commit": revision,
                    "oracle_sha256": oracle_hash,
                    "oracle_source_sha256": oracle_source_hash,
                    "before": before,
                    "after": after,
                    "trials": trials,
                    "model": context.model,
                    "provider": context.provider,
                }
                details["model_trace_hashes"] = list(getattr(executor, "trace_refs", ()))[
                    trace_start:
                ]
                details["validation"] = validation
                details["caller"]["remaining_after"] = context.budget.remaining_microusd
                if not accepted:
                    session.record_lesson(candidate.lesson_id, candidate.candidate_id, "REJECTED")
                    raise LearningBlocked("BENEFIT_OR_RUNTIME_INVOCATION_NOT_ESTABLISHED")
                if self.publisher is None:
                    raise LearningBlocked("PR_PUBLISHER_UNAVAILABLE")
                url = self.publisher.publish(str(path), candidate, validation)
                session.record_lesson(candidate.lesson_id, candidate.candidate_id, "VALIDATED", url)
                return session.finish(
                    job_id,
                    {
                        **details,
                        "overall_status": "VALIDATED",
                        "pr_url": url,
                        "deployed": False,
                        "subsequent_use": "NOT_OBSERVED",
                    },
                )
            except LearningBlocked as exc:
                details["model_trace_hashes"] = list(getattr(executor, "trace_refs", ()))[
                    trace_start:
                ]
                return session.finish(
                    job_id, {**details, "overall_status": "BLOCKED", "reason": str(exc)}
                )
            except Exception as exc:
                details["model_trace_hashes"] = list(getattr(executor, "trace_refs", ()))[
                    trace_start:
                ]
                return session.finish(
                    job_id,
                    {
                        **details,
                        "overall_status": "FAILED",
                        "reason": f"{type(exc).__name__}: {exc}",
                    },
                )
