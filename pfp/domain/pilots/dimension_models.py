"""Pydantic V2 Domain Models and Sync Engine for PFP Dimension Register.

AuthorityEffect: None.
Governing schema: pfp.dimension-register.v1
Canonical path: omega_engine_woland/tests/pilots/dimensions/dimension_register.yaml
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Set, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class DimensionVocabulary(_Frozen):
    buckets: Dict[StrictStr, StrictStr]
    costs: Dict[StrictStr, StrictStr]
    owners: List[StrictStr]


class DimensionEntry(_Frozen):
    id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9_]*$")]
    group: Annotated[StrictStr, Field(min_length=1, max_length=100)]
    what: Annotated[StrictStr, Field(min_length=1)]
    levels: Union[StrictStr, StrictInt, float]
    n: Annotated[int, Field(ge=0)]
    bucket: Annotated[StrictStr, Field(min_length=1)]
    cost: Annotated[StrictStr, Field(min_length=1)]
    owner: Annotated[StrictStr, Field(min_length=1)]
    why: Annotated[StrictStr, Field(min_length=1)]


class OutcomeEntry(_Frozen):
    id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9_]*$")]
    what: Annotated[StrictStr, Field(min_length=1)]
    kind: Annotated[StrictStr, Field(min_length=1)]


class RegistrySyncReport(_Frozen):
    is_in_sync: bool
    missing_dimension_ids: List[StrictStr]
    observed_parameters_count: int
    registered_dimensions_count: int
    details: Dict[StrictStr, Any]


class DimensionRegister(_Frozen):
    schema_: Literal["pfp.dimension-register.v1"] = Field(alias="schema", default="pfp.dimension-register.v1")
    authority_effect: Literal["None"] = "None"
    status: StrictStr
    vocabulary: DimensionVocabulary
    dimensions: List[DimensionEntry]
    outcomes: List[OutcomeEntry]

    @classmethod
    def from_yaml(cls, content: str) -> DimensionRegister:
        if not isinstance(content, str):
            raise TypeError("from_yaml requires YAML text; use load_yaml_model for a path")
        raw = yaml.safe_load(content.lstrip("\ufeff"))
        return cls.model_validate(raw)

    def to_yaml(self) -> str:
        data = self.model_dump(by_alias=True)
        return yaml.safe_dump(data, sort_keys=False)

    @property
    def dimension_ids(self) -> Set[str]:
        return {d.id for d in self.dimensions}

    @property
    def outcome_ids(self) -> Set[str]:
        return {o.id for o in self.outcomes}

    def get_dimension(self, dimension_id: str) -> Optional[DimensionEntry]:
        for d in self.dimensions:
            if d.id == dimension_id:
                return d
        return None

    def audit_pilot_matrix_sync(self, matrix_data: Dict[str, Any]) -> RegistrySyncReport:
        """Audit whether all pilot parameters in a matrix are tracked in the dimension register."""
        known_dims = self.dimension_ids
        observed_params: Set[str] = set()

        # Check top-level task keys
        for top_key in ("task_family", "difficulty_rung", "host_checker"):
            if top_key in matrix_data:
                observed_params.add(top_key)

        # Check per-pilot parameters
        pilots = matrix_data.get("pilots", [])
        for p in pilots:
            if not isinstance(p, dict):
                continue
            for k in p.keys():
                # Filter out pure indexing/administrative keys
                if k not in (
                    "pilot_index", "pilot_id", "prompt_id", "variation_id",
                    "name", "results_path", "seed_prompt", "expected_outcome",
                    "governing_specification", "governing_strategy", "stratum",
                    "dialect_tier", "syntactic_category", "boundary_format",
                    "input_typing", "parent_prompt_id", "generation_id",
                    "phase", "split", "checker_id", "mode", "results_summary",
                ):
                    observed_params.add(k)

            # Check input_typing sub-keys if present
            input_typing = p.get("input_typing")
            if isinstance(input_typing, dict):
                for ik in input_typing.keys():
                    observed_params.add(ik)

        missing = sorted(list(observed_params - known_dims))
        return RegistrySyncReport(
            is_in_sync=len(missing) == 0,
            missing_dimension_ids=missing,
            observed_parameters_count=len(observed_params),
            registered_dimensions_count=len(known_dims),
            details={"observed_params": sorted(list(observed_params)), "missing": missing},
        )

    def with_registered_dimensions(self, new_entries: List[DimensionEntry]) -> DimensionRegister:
        """Return an immutable updated copy with newly registered dimensions appended."""
        existing_ids = self.dimension_ids
        updated_dims = list(self.dimensions)
        for entry in new_entries:
            if entry.id not in existing_ids:
                updated_dims.append(entry)
                existing_ids.add(entry.id)

        data = self.model_dump(by_alias=True)
        data["dimensions"] = [d.model_dump() for d in updated_dims]
        return DimensionRegister.model_validate(data)


__all__ = [
    "DimensionEntry",
    "DimensionRegister",
    "DimensionVocabulary",
    "OutcomeEntry",
    "RegistrySyncReport",
]
