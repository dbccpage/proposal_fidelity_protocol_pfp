"""Use case workflows for Adversary research carrier freeze, planning, and program overlay.

AuthorityEffect: None. Orchestrates domain services and infrastructure ports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from adversary.domain.research.paper_run_graph import (
    AUTHORITY_EFFECT,
    ClaimKind,
    ObligationDisposition,
    ObligationKind,
    ObligationNode,
    PaperRunGraph,
    PaperRunGraphError,
    RunPlan,
)
from adversary.domain.research.protocols import (
    PaperCarrierPort,
    get_paper_carrier_port,
)
from adversary.domain.services import (
    ObligationPolicyService,
    StagePipelinePlanningService,
)


def freeze_carrier(
    paper_root: Path | str,
    *,
    carrier_port: Optional[PaperCarrierPort] = None,
) -> PaperRunGraph:
    """Freeze content-addressed carrier and build claim/obligation graph (read-only)."""
    port = carrier_port or get_paper_carrier_port()
    root_p = Path(paper_root).resolve()
    carrier_hash = port.compute_tree_hash(root_p)
    claims = port.parse_claims(root_p)
    obligations = ObligationPolicyService.derive_obligations(claims)

    graph = PaperRunGraph(
        paper_root=str(root_p),
        carrier_hash=carrier_hash,
        claims=claims,
        obligations=obligations,
    )
    return graph


def recompute_plan_stages(plan: RunPlan, dev_only: bool = False) -> RunPlan:
    """Refresh required/skipped stages from current graph obligations via domain service."""
    required, skipped, notes = StagePipelinePlanningService.recompute_stages(
        plan.graph.obligations, dev_only=dev_only
    )
    plan.required_stage_ids = required
    plan.skipped_stage_ids = skipped
    for n in notes:
        if n not in plan.uncovered_notes:
            plan.uncovered_notes.append(n)
    return plan


def plan_paper(
    paper_root: Path | str,
    rounds: int = 1,
    dev_only: bool = False,
    *,
    carrier_port: Optional[PaperCarrierPort] = None,
) -> RunPlan:
    """Read-only plan: freeze + required stages only. No package mutation."""
    g = freeze_carrier(paper_root, carrier_port=carrier_port)
    notes: list[str] = []
    if not any(c.kind == ClaimKind.MECHANIZATION for c in g.claims):
        notes.append(
            "No MECHANIZATION claims; stage_3 may be skippable if no lean obligations active."
        )
    na = sum(
        1
        for o in g.obligations
        if o.disposition == ObligationDisposition.NOT_APPLICABLE
    )
    if na:
        notes.append(
            f"{na} obligations marked not_applicable (LEAN_TOY / lean_na_reason)."
        )
    notes.append(
        "Coverage % is not claim faithfulness (policy floor only if declared)."
    )
    plan = RunPlan(
        graph=g,
        required_stage_ids=[],
        skipped_stage_ids=[],
        uncovered_notes=notes,
        budget_rounds_default=max(1, int(rounds)),
    )
    return recompute_plan_stages(plan, dev_only=dev_only)


def plan_with_program(
    paper_root: Path | str,
    program_id: str,
    *,
    rounds: int = 1,
    profiles_dir: Optional[Path] = None,
    enforce_estate: bool = True,
    repo_root: Optional[Path] = None,
    carrier_port: Optional[PaperCarrierPort] = None,
) -> dict[str, Any]:
    """plan_paper + program profile overlays + optional estate path gate."""
    port = carrier_port or get_paper_carrier_port()
    profile = port.load_program_profile(program_id, profiles_dir=profiles_dir)

    if enforce_estate:
        port.enforce_estate_path_gate(paper_root, profile, repo_root=repo_root)

    plan = plan_paper(paper_root, rounds=rounds, carrier_port=port)
    for kind in profile.extra_obligation_kinds:
        try:
            ObligationKind(kind)
        except ValueError as exc:
            raise PaperRunGraphError(
                f"profile {profile.id}: unknown obligation kind {kind!r}"
            ) from exc
        plan.graph.obligations.append(
            ObligationNode(
                obligation_id=f"PROGRAM:{profile.id}:{kind}",
                claim_id=f"PROGRAM-{profile.id.upper()}",
                kind=kind,
                disposition=ObligationDisposition.UNCHECKED.value,
            )
        )
    recompute_plan_stages(plan)
    plan.uncovered_notes = list(plan.uncovered_notes) + [
        f"program={profile.id}: extra obligations {profile.extra_obligation_kinds}",
        f"program estate_paths={profile.estate_paths}",
        "estate_path_gate=enforced" if enforce_estate else "estate_path_gate=skipped",
    ]
    if profile.notes:
        plan.uncovered_notes.append(f"program note: {profile.notes[:200]}")

    payload = plan.to_dict()
    payload["program"] = profile.to_dict()
    payload["authority_effect"] = AUTHORITY_EFFECT
    return payload


__all__ = [
    "freeze_carrier",
    "plan_paper",
    "plan_with_program",
    "recompute_plan_stages",
]
