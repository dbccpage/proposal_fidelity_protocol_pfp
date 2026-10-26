"""RunPlan value object with required stages and budgets.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from omega_engine_woland.domain.research.enums import AUTHORITY_EFFECT
from omega_engine_woland.domain.research.errors import PaperRunGraphError

if TYPE_CHECKING:
    from omega_engine_woland.domain.research.paper_run_graph import PaperRunGraph


class RunPlan(BaseModel):
    """Fully typed Pydantic Value Object: read-only plan with required stages and budgets."""

    model_config = ConfigDict(extra="forbid")

    graph: Any
    required_stage_ids: list[str] = Field(default_factory=list)
    skipped_stage_ids: list[str] = Field(default_factory=list)
    uncovered_notes: list[str] = Field(default_factory=list)
    budget_rounds_default: int = 1
    authority_effect: str = AUTHORITY_EFFECT
    read_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        graph_dict = self.graph.to_dict() if hasattr(self.graph, "to_dict") else dict(self.graph)
        carrier_hash = getattr(self.graph, "carrier_hash", "")
        paper_root = getattr(self.graph, "paper_root", "")
        return {
            "schema_version": "urn:omega:paper_run_graph:run_plan:v0.1",
            "read_only": self.read_only,
            "authority_effect": self.authority_effect,
            "carrier_hash": carrier_hash,
            "paper_root": paper_root,
            "required_stage_ids": list(self.required_stage_ids),
            "skipped_stage_ids": list(self.skipped_stage_ids),
            "budget_rounds_default": self.budget_rounds_default,
            "uncovered_notes": list(self.uncovered_notes),
            "graph": graph_dict,
            "precise_claim": (
                "PaperRunGraph is an authority-neutral interpreter for a finite typed "
                "research-repair calculus (PaperRunGraph v0.1). Not a sheafification monad."
            ),
        }

    def to_yaml(self) -> str:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise PaperRunGraphError("PyYAML required for YAML serialization") from exc
        return yaml.safe_dump(self.to_dict(), sort_keys=False)


__all__ = [
    "RunPlan",
]
