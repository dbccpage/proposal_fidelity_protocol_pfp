"""Read retained dissent without turning later model agreement into a verdict."""

from __future__ import annotations

import hashlib

from .teamwork import TeamworkRun, next_action


def finding_dispositions(run: TeamworkRun) -> dict:
    """Derive a view of existing observations; create no governance records.

    OPEN compares exact finding text with the current unresolved frontier. It
    does not identify two issues as mathematically equivalent. A later observed
    repair attempt carries the objection; its presence never proves resolution.
    """
    report = {
        "schema_version": "core.adversary.finding-dispositions.v1",
        "authority_effect": "None", "entries": [],
        "scope": "Retained observations and observed attempts; no verified resolution or council authority.",
    }
    if run.schema_version not in ("core.adversary.teamwork.v2", "core.adversary.teamwork.v3", "core.adversary.teamwork.v4"):
        return {**report, "status": "LEGACY_UNMEASURED", "open_findings": []}
    continuation = run.continuation_status  # Replays action and PFP bindings before readback.
    actions = []
    for index, observation in enumerate(run.observations):
        prefix = run.model_copy(update={"observations": run.observations[:index],
            "continuations": tuple(point for point in run.continuations
                                   if point.after_observations <= index)})
        action = next_action(prefix)
        if action is None:
            raise ValueError("FINDING_HISTORY_INVALID: an observation lacks a pending action")
        actions.append((action, observation))
    entries = []
    open_findings = continuation["open_findings"]
    for index, (action, observation) in enumerate(actions):
        for finding in observation.findings:
            attempts = [{"action_id": later.action_id, "kind": later.kind,
                "worker": result.worker, "blocked": result.blocked,
                "result_candidate_sha256": _candidate_digest(result.content)}
                for later, result in actions[index + 1:]
                if later.kind in ("build", "repair") and finding in later.findings]
            disposition = ("OPEN" if finding in open_findings else (
                "CARRIED_TO_REPAIR" if attempts else "RETAINED_HISTORY"))
            entries.append({"finding": finding, "source_action_id": action.action_id,
                "role_id": action.role_id, "worker": observation.worker,
                "candidate_sha256": _candidate_digest(action.candidate),
                "candidate_artifacts": dict(action.artifacts), "source_blocked": observation.blocked,
                "disposition": disposition, "repair_attempts": attempts,
                "resolution_verified": False})
    return {**report, "status": "DERIVED_FROM_REPLAYED_HISTORY",
        "open_findings": open_findings, "entries": entries}


def _candidate_digest(candidate: str) -> str:
    return hashlib.sha256(candidate.encode("utf-8")).hexdigest()
