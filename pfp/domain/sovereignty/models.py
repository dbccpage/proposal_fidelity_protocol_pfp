"""Pure domain models for Three-Layer Sovereignty (Prompt 33).

AuthorityEffect: None.
ZERO-FLOAT Law: Attention mass deltas and coboundary defects in Fraction.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Tuple


@dataclass(frozen=True)
class AttentionMaskInterventionReceipt:
    """Receipt for Layer 1 attention mask causal intervention."""

    layer_name: str
    fluff_positions: Tuple[int, ...]
    carrier_positions: Tuple[int, ...]
    fluff_mass_before: Fraction
    fluff_mass_after: Fraction
    causal_routing_verified: bool
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if isinstance(self.fluff_mass_before, float) or isinstance(
            self.fluff_mass_after, float
        ):
            raise TypeError("ZERO-FLOAT Law: fluff mass must be Fraction, not float")
        if not isinstance(self.fluff_mass_before, Fraction) or not isinstance(
            self.fluff_mass_after, Fraction
        ):
            raise TypeError("ZERO-FLOAT Law: fluff mass must be Fraction")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.layer_name,
            self.fluff_positions,
            self.carrier_positions,
            self.fluff_mass_before,
            self.fluff_mass_after,
            self.causal_routing_verified,
            self.authority_effect,
        ) == (
            other.layer_name,
            other.fluff_positions,
            other.carrier_positions,
            other.fluff_mass_before,
            other.fluff_mass_after,
            other.causal_routing_verified,
            other.authority_effect,
        )


@dataclass(frozen=True)
class CarrierProjectionReceipt:
    """Receipt for Layer 2 logit carrier projection onto probability simplex."""

    carrier_token_ids: Tuple[int, ...]
    vocab_size: int
    support_restricted_100pct: bool
    simplex_l1_norm_constant_one: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.carrier_token_ids,
            self.vocab_size,
            self.support_restricted_100pct,
            self.simplex_l1_norm_constant_one,
        ) == (
            other.carrier_token_ids,
            other.vocab_size,
            other.support_restricted_100pct,
            other.simplex_l1_norm_constant_one,
        )


@dataclass(frozen=True)
class IndependentHostReplayVerdict:
    """Receipt for Layer 3 deterministic host ground truth replay."""

    packet_id: str
    recomputed_phi1: Fraction
    recomputed_gamma2: Fraction
    claimed_phi1: Fraction
    verdict: str  # e.g. "ADMITTED", "REFUSED_COBOUNDARY_DEFECT"
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        for val in (self.recomputed_phi1, self.recomputed_gamma2, self.claimed_phi1):
            if isinstance(val, float):
                raise TypeError("ZERO-FLOAT Law: defects must be Fraction, not float")
            if not isinstance(val, Fraction):
                raise TypeError("ZERO-FLOAT Law: defects must be Fraction instances")

    @property
    def is_admitted(self) -> bool:
        return self.verdict == "ADMITTED"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.packet_id,
            self.recomputed_phi1,
            self.recomputed_gamma2,
            self.claimed_phi1,
            self.verdict,
            self.authority_effect,
        ) == (
            other.packet_id,
            other.recomputed_phi1,
            other.recomputed_gamma2,
            other.claimed_phi1,
            other.verdict,
            other.authority_effect,
        )
