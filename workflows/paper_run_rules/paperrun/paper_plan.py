"""Freeze a paper carrier and plan its required review stages (read-only).

Trimmed port of the internal planning use case: the program-profile overlay is
not ported. AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Protocol

from paperrun.carrier import LocalPaperCarrier
from paperrun.paper_run_graph import (
    ClaimKind,
    ObligationDisposition,
    PaperRunGraph,
    RunPlan,
)
from paperrun.services import (
    ObligationPolicyService,
    StagePipelinePlanningService,
)


class PaperCarrierPort(Protocol):
    """Carrier loader: tree hash and claim reader."""

    def compute_tree_hash(self, paper_root: Path | str) -> str: ...

    def parse_claims(self, paper_root: Path | str) -> list[Any]: ...


def freeze_carrier(
    paper_root: Path | str,
    *,
    carrier_port: Optional[PaperCarrierPort] = None,
) -> PaperRunGraph:
    """Freeze content-addressed carrier and build claim/obligation graph (read-only)."""
    port = carrier_port or LocalPaperCarrier()
    root_p = Path(paper_root).resolve()
    carrier_hash = port.compute_tree_hash(root_p)
    claims = port.parse_claims(root_p)
    obligations = ObligationPolicyService.derive_obligations(claims)

    return PaperRunGraph(
        paper_root=str(root_p),
        carrier_hash=carrier_hash,
        claims=claims,
        obligations=obligations,
    )


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
    na = sum(1 for o in g.obligations if o.disposition == ObligationDisposition.NOT_APPLICABLE)
    if na:
        notes.append(f"{na} obligations marked not_applicable (LEAN_TOY / lean_na_reason).")
    notes.append("Coverage % is not claim faithfulness (policy floor only if declared).")
    plan = RunPlan(
        graph=g,
        required_stage_ids=[],
        skipped_stage_ids=[],
        uncovered_notes=notes,
        budget_rounds_default=max(1, int(rounds)),
    )
    return recompute_plan_stages(plan, dev_only=dev_only)


__all__ = [
    "PaperCarrierPort",
    "freeze_carrier",
    "plan_paper",
    "recompute_plan_stages",
]
