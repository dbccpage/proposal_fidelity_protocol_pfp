"""Host program profile domain model and matching YAML schema.
AuthorityEffect: None. Pure domain model with zero host I/O.
"""

from __future__ import annotations

from typing import Any, Sequence

from pydantic import BaseModel, ConfigDict, Field

from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.research.paper_run_graph import AUTHORITY_EFFECT, PaperRunGraphError


class ProgramProfile(BaseModel):
    """Fully typed Pydantic Value Object and YAML schema for research program profiles."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    estate_paths: list[str] = Field(default_factory=list)
    extra_obligation_kinds: list[str] = Field(default_factory=list)
    default_lanes: list[str] = Field(default_factory=list)
    stage_catalog: str = ""
    authority_effect: str = AUTHORITY_EFFECT
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_yaml(cls, yaml_text: str) -> ProgramProfile:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise PaperRunGraphError("PyYAML required to parse program profile YAML") from exc
        raw = yaml.safe_load(yaml_text)
        if not isinstance(raw, dict):
            raise PaperRunGraphError("invalid program profile YAML: expected mapping")
        ae = str(raw.get("authority_effect") or AUTHORITY_EFFECT)
        if ae not in (AUTHORITY_EFFECT, "None", ""):
            raise PaperRunGraphError("program profile authority_effect must be None")
        return cls.model_validate(raw)

    def to_yaml(self) -> str:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise PaperRunGraphError("PyYAML required to dump program profile YAML") from exc
        return yaml.safe_dump(self.model_dump(), sort_keys=False)


def check_estate_path_membership(
    paper_path_posix: str,
    estate_paths: Sequence[str],
) -> Result[None, Refusal]:
    """Pure domain check: evaluate path membership against estate boundaries without disk I/O."""
    if not estate_paths:
        return Ok(None)
    norm_paper = paper_path_posix.replace("\\", "/").strip("/")
    for rel in estate_paths:
        norm = str(rel).replace("\\", "/").strip("/")
        if norm and (
            f"/{norm}/" in f"/{norm_paper}/"
            or norm_paper.endswith(f"/{norm}")
            or norm_paper.endswith(norm)
            or norm in norm_paper
        ):
            return Ok(None)
    return Err(
        Refusal(
            code="ESTATE_PATH_BREACH",
            message=f"estate path gate: paper {paper_path_posix} is outside declared estate_paths={list(estate_paths)}",
            locus="check_estate_path_membership",
        )
    )


__all__ = [
    "ProgramProfile",
    "check_estate_path_membership",
]
