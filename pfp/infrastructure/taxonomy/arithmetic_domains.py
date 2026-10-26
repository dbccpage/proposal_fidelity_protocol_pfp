"""PFP Infrastructure - Arithmetic & Coefficient Domains Taxonomy.

AuthorityEffect: None.
Canonical specification of algebraic structures and coefficient domains admitted in PFP mathematical problem formulations.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from omega_engine_pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_arithmetic_domain_enum_members() -> dict[str, str]:
    """Load canonical arithmetic domain category identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "arithmetic_domains.yaml"
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
                        return members
            except Exception:
                pass
    return {
        "EXACT_INTEGER": "EXACT_INTEGER",
        "EXACT_RATIONAL": "EXACT_RATIONAL",
        "FINITE_FIELD_GF2": "FINITE_FIELD_GF2",
        "MODULAR_RING_ZN": "MODULAR_RING_ZN",
        "BOOLEAN_ALGEBRA": "BOOLEAN_ALGEBRA",
    }


ArithmeticDomainEnum: type[Enum] = Enum(
    "ArithmeticDomainEnum",
    _load_arithmetic_domain_enum_members(),
    type=str,
    module=__name__,
)
ArithmeticDomainEnum.__doc__ = (
    "Canonical enum of admitted algebraic coefficient domains loaded directly from YAML."
)


class ArithmeticDomainDefinition(BaseModel):
    """Strongly typed specification of an algebraic coefficient domain."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Domain token (e.g. 'EXACT_RATIONAL')")
    is_field: bool = Field(
        default=False, description="Whether algebraic structure is a formal field"
    )
    characteristic: int | None = Field(
        default=None, description="Algebraic characteristic (0, 2, or None for non-fields)"
    )
    description: str = Field(default="", description="Mathematical specification of the structure")


class ArithmeticDomainRegistry:
    """Catalog of algebraic coefficient domains loaded from canonical YAML with dynamic extension."""

    _instance: ArithmeticDomainRegistry | None = None

    def __init__(self) -> None:
        self._domains: dict[str, ArithmeticDomainDefinition] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> ArithmeticDomainRegistry:
        if cls._instance is None:
            cls._instance = ArithmeticDomainRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "arithmetic_domains.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    for item in data["categories"]:
                        try:
                            defn = ArithmeticDomainDefinition.model_validate(item)
                            self._domains[defn.id] = defn
                        except Exception:
                            pass
                    break

        if not self._domains:
            for ad_val in ArithmeticDomainEnum:
                self._domains[ad_val.value] = ArithmeticDomainDefinition(
                    id=ad_val.value,
                    is_field=ad_val.value in {"EXACT_RATIONAL", "FINITE_FIELD_GF2"},
                    characteristic=0
                    if ad_val.value == "EXACT_RATIONAL"
                    else (2 if ad_val.value == "FINITE_FIELD_GF2" else None),
                )

    def register(self, defn: ArithmeticDomainDefinition) -> None:
        self._domains[defn.id] = defn

    def is_valid(self, domain_id: str) -> bool:
        return domain_id in self._domains

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._domains.keys())

    def get(self, domain_id: str) -> ArithmeticDomainDefinition | None:
        return self._domains.get(domain_id)


# Pre-resolved constants
VALID_ARITHMETIC_DOMAINS = ArithmeticDomainRegistry.get_instance().all_ids()


def get_valid_arithmetic_domains() -> frozenset[str]:
    return ArithmeticDomainRegistry.get_instance().all_ids()
