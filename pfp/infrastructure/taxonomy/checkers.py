"""PFP Infrastructure - Checker Contract Identifiers & Schema Registry.

AuthorityEffect: None.
Replaces magic checker strings across runners, identifiers, and evaluation gates.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_checker_enum_members() -> dict[str, str]:
    """Load canonical checker contract identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "checkers.yaml"
        if reg_file.is_file():
            try:
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "checkers" in data:
                    members: dict[str, str] = {}
                    for item in data["checkers"]:
                        if isinstance(item, dict) and "id" in item:
                            cid = str(item["id"])
                            key = cid.replace("-", "_").replace("PFP_", "")
                            members[key] = cid
                            full_key = cid.replace("-", "_")
                            members[full_key] = cid
                    if members:
                        return members
            except Exception:
                pass
    return {
        "01_EXACT_LINALG": "PFP-01-EXACT-LINALG",
        "PFP_01_EXACT_LINALG": "PFP-01-EXACT-LINALG",
        "02_GRAPH_FACTS": "PFP-02-GRAPH-FACTS",
        "PFP_02_GRAPH_FACTS": "PFP-02-GRAPH-FACTS",
        "03_GRAPH_REPAIR": "PFP-03-GRAPH-REPAIR",
        "PFP_03_GRAPH_REPAIR": "PFP-03-GRAPH-REPAIR",
        "14_TYPED_REFUSAL": "PFP-14-TYPED-REFUSAL",
        "PFP_14_TYPED_REFUSAL": "PFP-14-TYPED-REFUSAL",
        "52_COCHAIN_DEFECT": "PFP-52-COCHAIN-DEFECT",
        "PFP_52_COCHAIN_DEFECT": "PFP-52-COCHAIN-DEFECT",
        "55_MAGMA_ASSOC": "PFP-55-MAGMA-ASSOC",
        "PFP_55_MAGMA_ASSOC": "PFP-55-MAGMA-ASSOC",
    }


CheckerContractEnum: type[Enum] = Enum(
    "CheckerContractEnum",
    _load_checker_enum_members(),
    type=str,
    module=__name__,
)
CheckerContractEnum.__doc__ = (
    "Canonical enum of checker contract identifiers loaded directly from YAML."
)

CheckerEnum = CheckerContractEnum


class CheckerContractDefinition(BaseModel):
    """Strongly typed definition of an evaluation checker contract."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Unique checker contract identifier (e.g. 'PFP-01-EXACT-LINALG')")
    task_family: str = Field(description="Associated task family slug")
    description: str = Field(default="", description="Verification semantics")
    response_schema: dict[str, Any] = Field(
        default_factory=dict, description="Expected JSON response schema"
    )


class CheckerContractRegistry:
    """Catalog of checker contracts replacing hardcoded magic dictionaries."""

    _instance: CheckerContractRegistry | None = None

    def __init__(self) -> None:
        self._checkers: dict[str, CheckerContractDefinition] = {}
        self._family_to_checker: dict[str, str] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> CheckerContractRegistry:
        if cls._instance is None:
            cls._instance = CheckerContractRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "checkers.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "checkers" in data:
                    for item in data["checkers"]:
                        try:
                            defn = CheckerContractDefinition.model_validate(item)
                            self._checkers[defn.id] = defn
                            self._family_to_checker[defn.task_family] = defn.id
                        except Exception:
                            pass
                    break

        # Fallback defaults if YAML is missing
        bedrock = {
            "PFP-01-EXACT-LINALG": ("linear_algebra", "Exact rational linear algebra solver"),
            "PFP-02-GRAPH-FACTS": ("graph_facts", "Graph facts and degree oracle"),
            "PFP-03-GRAPH-REPAIR": ("graph_repair", "Chord triangle cycle repair"),
            "PFP-14-TYPED-REFUSAL": ("refusal", "Calibrated refusal certifier"),
            "PFP-52-COCHAIN-DEFECT": ("cochain_defect", "Discrete boundary defect certifier"),
            "PFP-55-MAGMA-ASSOC": ("magma_associativity", "Non-associative magma certifier"),
        }
        for cid, (tf, desc) in bedrock.items():
            if cid not in self._checkers:
                defn = CheckerContractDefinition(id=cid, task_family=tf, description=desc)
                self._checkers[cid] = defn
                self._family_to_checker[tf] = cid

    def register(self, defn: CheckerContractDefinition) -> None:
        self._checkers[defn.id] = defn
        self._family_to_checker[defn.task_family] = defn.id

    def is_valid(self, checker_id: str) -> bool:
        return checker_id in self._checkers

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._checkers.keys())

    def get(self, checker_id: str) -> CheckerContractDefinition | None:
        return self._checkers.get(checker_id)

    def resolve_checker_for_family(self, task_family: str) -> str:
        """Resolve checker ID for a task family, checking dynamic TaskFamilyRegistry as fallback."""
        if task_family in self._family_to_checker:
            return self._family_to_checker[task_family]
        try:
            from pfp.infrastructure.catalogs.task_families import (
                TaskFamilyRegistry,
            )

            fam = TaskFamilyRegistry.get_instance().get(task_family)
            if fam is not None:
                return fam.checker_contract_id
        except Exception:
            pass
        return f"PFP-EXT-{task_family.upper()}"


# Pre-resolved constants
CANONICAL_CHECKERS = CheckerContractRegistry.get_instance().all_ids()


def get_valid_checkers() -> frozenset[str]:
    return CheckerContractRegistry.get_instance().all_ids()
