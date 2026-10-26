"""Prompt Society and Civilization normative data models (NF-01).

Conforms to normative specification:
`urn:omega:nf:prompt_civilization:society_and_civilization:v1.0.0`

AuthorityEffect: None.
Zero-Float Law: Uses exact rational arithmetic (fractions.Fraction).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
import re
from typing import Sequence

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
RATIONAL_PATTERN = re.compile(r"^-?[0-9]+/[1-9][0-9]*$")


def _scope_covers(scope: str, target: str) -> bool:
    if scope == "*" or scope == target:
        return True
    if scope.endswith(".*"):
        stem = scope[:-2]
        return bool(stem) and (target == stem or target.startswith(stem + "."))
    return False


@dataclass(frozen=True, slots=True)
class AggregateFitnessVectorV1:
    accuracy_rational: str
    cost_rational: str
    robustness_rational: str

    def __post_init__(self) -> None:
        self.validate()

    @staticmethod
    def _parse_rational(s: str) -> Fraction:
        if not isinstance(s, str) or not RATIONAL_PATTERN.match(s):
            raise ValueError(f"INVALID_RATIONAL_FORMAT: {s!r}")
        parts = s.split("/")
        return Fraction(int(parts[0]), int(parts[1]))

    @property
    def accuracy(self) -> Fraction:
        return self._parse_rational(self.accuracy_rational)

    @property
    def cost(self) -> Fraction:
        return self._parse_rational(self.cost_rational)

    @property
    def robustness(self) -> Fraction:
        return self._parse_rational(self.robustness_rational)

    def validate(self) -> None:
        acc = self.accuracy
        cost = self.cost
        rob = self.robustness
        if acc < 0 or acc > 1:
            raise ValueError("ACCURACY_OUT_OF_BOUNDS_0_1")
        if cost < 0:
            raise ValueError("COST_CANNOT_BE_NEGATIVE")
        if rob < 0 or rob > 1:
            raise ValueError("ROBUSTNESS_OUT_OF_BOUNDS_0_1")

    def weakly_dominates(self, other: AggregateFitnessVectorV1) -> bool:
        """Candidate weakly dominates active: acc >= other, cost <= other, rob >= other."""
        return (
            self.accuracy >= other.accuracy
            and self.cost <= other.cost
            and self.robustness >= other.robustness
        )

    def strictly_dominates_any(self, other: AggregateFitnessVectorV1) -> bool:
        """Candidate strictly dominates in at least one coordinate."""
        return (
            self.accuracy > other.accuracy
            or self.cost < other.cost
            or self.robustness > other.robustness
        )

    def pareto_replaces(self, active: AggregateFitnessVectorV1) -> bool:
        """Law of Pareto Conservation (Law 2):
        Candidate replaces active iff weakly dominates on all coordinates
        and strictly dominates on at least one coordinate.
        """
        return self.weakly_dominates(active) and self.strictly_dominates_any(active)


@dataclass(frozen=True, slots=True)
class MigrationPolicyV1:
    max_incoming_per_epoch: int
    taxonomic_admissibility: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.max_incoming_per_epoch < 0:
            raise ValueError("MAX_INCOMING_CANNOT_BE_NEGATIVE")
        if not isinstance(self.taxonomic_admissibility, tuple):
            object.__setattr__(
                self, "taxonomic_admissibility", tuple(self.taxonomic_admissibility)
            )

    def is_migration_allowed(
        self,
        target_domain: str,
        incoming_count: int,
        current_population: int,
    ) -> bool:
        """Law of Bounded Migration (Law 3).

        Migration requires taxonomic admissibility and is bounded by
        min(max_incoming_per_epoch, ceil(current_population / 20)).
        """
        admitted = any(_scope_covers(label, target_domain) for label in self.taxonomic_admissibility)
        if not admitted:
            return False
        if incoming_count > self.max_incoming_per_epoch or incoming_count <= 0:
            return False
        pop_cap = 1 if current_population <= 0 else (current_population + 19) // 20
        effective_cap = max(1, min(self.max_incoming_per_epoch, pop_cap))
        return incoming_count <= effective_cap


@dataclass(frozen=True, slots=True)
class PromptSocietyV1:
    society_id: str
    domain_protocol: str
    family_ids: tuple[str, ...]
    aggregate_fitness_vector: AggregateFitnessVectorV1
    migration_policy: MigrationPolicyV1
    created_utc: str

    def __post_init__(self) -> None:
        if not isinstance(self.family_ids, tuple):
            object.__setattr__(self, "family_ids", tuple(self.family_ids))
        self.validate()

    def validate(self) -> None:
        if not SHA256_PATTERN.match(self.society_id):
            raise ValueError(f"INVALID_SOCIETY_ID_FORMAT: {self.society_id!r}")
        if not self.domain_protocol:
            raise ValueError("EMPTY_DOMAIN_PROTOCOL")
        self.aggregate_fitness_vector.validate()

    def canonical_bytes(self) -> bytes:
        self.validate()
        payload = {
            "society_id": self.society_id,
            "domain_protocol": self.domain_protocol,
            "family_ids": list(self.family_ids),
            "aggregate_fitness_vector": asdict(self.aggregate_fitness_vector),
            "migration_policy": {
                "max_incoming_per_epoch": self.migration_policy.max_incoming_per_epoch,
                "taxonomic_admissibility": list(self.migration_policy.taxonomic_admissibility),
            },
            "created_utc": self.created_utc,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def canonical_digest(self) -> str:
        return f"sha256:{hashlib.sha256(self.canonical_bytes()).hexdigest()}"


@dataclass(frozen=True, slots=True)
class PromptCivilizationV1:
    civilization_id: str
    society_ids: tuple[str, ...]
    global_immune_registry: str
    reservation_budget_pool: int
    governance_epoch: int
    created_utc: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.society_ids, tuple):
            object.__setattr__(self, "society_ids", tuple(self.society_ids))
        self.validate()

    def validate(self) -> None:
        if not SHA256_PATTERN.match(self.civilization_id):
            raise ValueError(f"INVALID_CIVILIZATION_ID_FORMAT: {self.civilization_id!r}")
        if self.reservation_budget_pool < 0:
            raise ValueError("RESERVATION_BUDGET_POOL_CANNOT_BE_NEGATIVE")
        if self.governance_epoch < 0:
            raise ValueError("GOVERNANCE_EPOCH_CANNOT_BE_NEGATIVE")
        if self.authority_effect != "None":
            raise ValueError("AUTHORITY_EFFECT_MUST_BE_NONE")

    def check_budget_solvency(self, total_reserved: int) -> bool:
        """Law of Budget Solvency (Law 4)."""
        if total_reserved > self.reservation_budget_pool:
            raise PermissionError("BUDGET_OVERDRAFT_REFUSED")
        return True

    def canonical_bytes(self) -> bytes:
        self.validate()
        payload = {
            "civilization_id": self.civilization_id,
            "society_ids": list(self.society_ids),
            "global_immune_registry": self.global_immune_registry,
            "reservation_budget_pool": self.reservation_budget_pool,
            "governance_epoch": self.governance_epoch,
            "created_utc": self.created_utc,
            "authority_effect": self.authority_effect,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def canonical_digest(self) -> str:
        return f"sha256:{hashlib.sha256(self.canonical_bytes()).hexdigest()}"
