"""PFP Infrastructure - Verification Rules Taxonomy.

AuthorityEffect: None.
Canonical specification of deterministic evaluation rules and oracle verifiers.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from omega_engine_pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_verification_rule_enum_members() -> dict[str, str]:
    """Load canonical verification rule category identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "verification_rules.yaml"
        if reg_file.is_file():
            try:
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    members = {
                        str(item["id"]): str(item["id"])
                        for item in data["categories"]
                        if isinstance(item, dict) and "id" in item
                    }
                    if members:
                        if (
                            "LEAN4_KERNEL_ELABORATION" in members
                            and "LEAN4_KERNEL_VERIFIER" not in members
                        ):
                            members["LEAN4_KERNEL_VERIFIER"] = "LEAN4_KERNEL_ELABORATION"
                        return members
            except Exception:
                pass
    return {
        "STATIC_CELL_BOUNDS_CHECK": "STATIC_CELL_BOUNDS_CHECK",
        "CHAIN_COMPLEX_NILPOTENCY_CHECK": "CHAIN_COMPLEX_NILPOTENCY_CHECK",
        "INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE": "INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE",
        "EXACT_SCALAR_SUBSTITUTION": "EXACT_SCALAR_SUBSTITUTION",
        "DUAL_CIRCULATION_FEASIBILITY": "DUAL_CIRCULATION_FEASIBILITY",
        "ACYCLIC_POTENTIAL_GRADIENT": "ACYCLIC_POTENTIAL_GRADIENT",
        "ASSOCIATIVITY_DIVERGENCE_VERIFIER": "ASSOCIATIVITY_DIVERGENCE_VERIFIER",
        "BOOLEAN_SATISFIABILITY_VERIFIER": "BOOLEAN_SATISFIABILITY_VERIFIER",
        "LEAN4_KERNEL_ELABORATION": "LEAN4_KERNEL_ELABORATION",
        "LEAN4_KERNEL_VERIFIER": "LEAN4_KERNEL_ELABORATION",
    }


VerificationRuleEnum: type[Enum] = Enum(
    "VerificationRuleEnum",
    _load_verification_rule_enum_members(),
    type=str,
    module=__name__,
)
VerificationRuleEnum.__doc__ = (
    "Canonical enum of deterministic verification rules loaded directly from YAML."
)


class VerificationRuleDefinition(BaseModel):
    """Strongly typed specification of a deterministic verification rule."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Rule identifier token (e.g. 'EXACT_SCALAR_SUBSTITUTION')")
    oracle_type: str = Field(default="exact_oracle", description="Category of the verifier engine")
    description: str = Field(default="", description="Formal verification specification")


class VerificationRuleRegistry:
    """Catalog of verification rules loaded from canonical YAML with dynamic extension."""

    _instance: VerificationRuleRegistry | None = None

    def __init__(self) -> None:
        self._rules: dict[str, VerificationRuleDefinition] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> VerificationRuleRegistry:
        if cls._instance is None:
            cls._instance = VerificationRuleRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "verification_rules.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    for item in data["categories"]:
                        try:
                            defn = VerificationRuleDefinition.model_validate(item)
                            self._rules[defn.id] = defn
                        except Exception:
                            pass
                    break

        if not self._rules:
            for vr_val in VerificationRuleEnum:
                self._rules[vr_val.value] = VerificationRuleDefinition(
                    id=vr_val.value,
                    oracle_type="exact_oracle",
                )

    def register(self, defn: VerificationRuleDefinition) -> None:
        self._rules[defn.id] = defn

    def is_valid(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._rules.keys())

    def get(self, rule_id: str) -> VerificationRuleDefinition | None:
        return self._rules.get(rule_id)


# Pre-resolved constants
VALID_VERIFICATION_RULES = VerificationRuleRegistry.get_instance().all_ids()


def get_valid_verification_rules() -> frozenset[str]:
    return VerificationRuleRegistry.get_instance().all_ids()
