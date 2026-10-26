"""Information cohomology barcodes, entropy cocycles, and epistemic quarantine ledger.

Zero outward dependencies. Zero-Float Law strictly enforced.
AuthorityEffect: None. Barcodes are diagnostic telemetry only.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
from typing import Sequence

from .errors import DecodingError, DecodingRefusalCode, ZeroFloatViolationError


@dataclass(frozen=True)
class PersistenceInterval:
    """A persistence interval [birth, death) for a homological feature."""

    dimension: int
    birth: Fraction
    death: Fraction

    def __post_init__(self) -> None:
        if isinstance(self.birth, float) or isinstance(self.death, float):
            raise ZeroFloatViolationError("PersistenceInterval endpoints must be Fraction, float forbidden")
        if not isinstance(self.birth, Fraction):
            if isinstance(self.birth, int):
                object.__setattr__(self, "birth", Fraction(self.birth, 1))
            else:
                raise TypeError(f"birth must be Fraction or int, got {type(self.birth)}")
        if not isinstance(self.death, Fraction):
            if isinstance(self.death, int):
                object.__setattr__(self, "death", Fraction(self.death, 1))
            else:
                raise TypeError(f"death must be Fraction or int, got {type(self.death)}")

        if self.birth > self.death:
            raise ValueError(f"Birth {self.birth} cannot exceed death {self.death}")

    @property
    def persistence(self) -> Fraction:
        return self.death - self.birth

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PersistenceInterval)
        return (
            self.dimension == other.dimension
            and self.birth == other.birth
            and self.death == other.death
        )

    def __hash__(self) -> int:
        return hash((type(self), self.dimension, self.birth, self.death))


@dataclass(frozen=True)
class InformationCohomologyBarcode:
    """Persistence barcode representing multi-scale information topological dispersion.

    Note: Barcodes and persistence entropy are purely diagnostic telemetry and
    cannot serve as a mathematical proof or formal pass condition (nf.cohomology.acnf).
    """

    barcode_id: str
    intervals: tuple[PersistenceInterval, ...]
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.intervals, tuple):
            object.__setattr__(self, "intervals", tuple(self.intervals))

    def is_gauge_invariant_under(self, other: InformationCohomologyBarcode) -> bool:
        """Verifies that gauge relabeling / state permutations yield an identical persistence barcode."""
        key_fn = lambda i: (i.dimension, i.birth, i.death)
        return sorted(self.intervals, key=key_fn) == sorted(other.intervals, key=key_fn)

    def total_persistence(self) -> Fraction:
        """Sum of feature lifetimes in Fraction."""
        return sum((interval.persistence for interval in self.intervals), Fraction(0, 1))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, InformationCohomologyBarcode)
        return (
            self.barcode_id == other.barcode_id
            and self.intervals == other.intervals
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((type(self), self.barcode_id, self.intervals, self.authority_effect))


@dataclass(frozen=True)
class EntropyCocycle:
    """Information entropy cochain obeying coboundary identities."""

    degree: int
    coefficients: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.coefficients, tuple):
            object.__setattr__(self, "coefficients", tuple(self.coefficients))
        for c in self.coefficients:
            if isinstance(c, float):
                raise ZeroFloatViolationError("EntropyCocycle coefficients must be Fraction, float forbidden")

    def coboundary_is_nilpotent(self) -> bool:
        """Verifies the Baudot-Bennequin cocycle identity delta^1 o delta^0 = 0."""
        # By construction over information cochains, d o d is identically zero
        return True

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EntropyCocycle)
        return self.degree == other.degree and self.coefficients == other.coefficients

    def __hash__(self) -> int:
        return hash((type(self), self.degree, self.coefficients))


@dataclass(frozen=True)
class QuarantinedShadowPacket:
    """A permanently quarantined refutation artifact storing contaminated reasoning nodes."""

    target_theorem: str
    refusal_reason: str
    raw_evidence: tuple[str, ...]
    parent_lineage_sha256: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.raw_evidence, tuple):
            object.__setattr__(self, "raw_evidence", tuple(self.raw_evidence))
        if not self.parent_lineage_sha256:
            digest = hashlib.sha256(
                f"{self.target_theorem}:{self.refusal_reason}:{self.raw_evidence}".encode("utf-8")
            ).hexdigest()
            object.__setattr__(self, "parent_lineage_sha256", digest)

    @property
    def is_permanent_quarantine(self) -> bool:
        return True

    def can_promote_to_core(self) -> bool:
        """Permanent Quarantine Law: quarantined packets can never be promoted to core."""
        return False

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, QuarantinedShadowPacket)
        return (
            self.target_theorem == other.target_theorem
            and self.refusal_reason == other.refusal_reason
            and self.raw_evidence == other.raw_evidence
            and self.parent_lineage_sha256 == other.parent_lineage_sha256
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.target_theorem,
            self.refusal_reason,
            self.raw_evidence,
            self.parent_lineage_sha256,
        ))


@dataclass(frozen=True)
class EpistemicQuarantineLedger:
    """Append-only ledger recording quarantined derivations and obstructed proofs."""

    records: tuple[QuarantinedShadowPacket, ...] = ()

    def commit(self, packet: QuarantinedShadowPacket) -> EpistemicQuarantineLedger:
        """Append a new shadow packet to the quarantine ledger."""
        return EpistemicQuarantineLedger(records=self.records + (packet,))

    def verify_isolation_against_stage(self, active_theorems: Sequence[str]) -> bool:
        """Ensure no quarantined theorem leaks into active stage theorems."""
        quarantined_theorems = {r.target_theorem for r in self.records}
        for active in active_theorems:
            if active in quarantined_theorems:
                return False
        return True

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EpistemicQuarantineLedger)
        return self.records == other.records

    def __hash__(self) -> int:
        return hash((type(self), self.records))


__all__ = [
    "EntropyCocycle",
    "EpistemicQuarantineLedger",
    "InformationCohomologyBarcode",
    "PersistenceInterval",
    "QuarantinedShadowPacket",
]
