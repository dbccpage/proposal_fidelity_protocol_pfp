"""Domain entities and value objects for coboundary scoring and residual drops.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Mapping

from pfp.domain.shared_kernel.exact import (
    Exact,
    NotExactError,
    coerce_exact,
    is_exact_value,
    to_canonical_string,
)
from pfp.domain.validation import _fail

COBOUNDARY_SCORE_SCHEMA = "core.symbol-game.coboundary-score.v1"
COBOUNDARY_SCORE_FAMILY = "coboundary_score"
AUTHORITY_EFFECT = "None"

REFUSAL_ILLEGAL_PROPOSAL = "ILLEGAL_PROPOSAL"
REFUSAL_AUTHORITY = "AUTHORITY_NON_NONE"
REFUSAL_NEGATIVE_MAGNITUDE = "NEGATIVE_MAGNITUDE"
REFUSAL_EXACT_WITHOUT_DUAL = "EXACT_WITHOUT_DUAL_WITNESS"
REFUSAL_EXACT_WITHOUT_DUAL_WITNESS = "EXACT_WITHOUT_DUAL_WITNESS"
# An exactness claim may not rest on a float. Raised where `is_exact_candidate`
# is asserted over a residual norm that is not an exact rational, so that the
# claim fails closed instead of being decided by whatever the float happens to
# round to.
REFUSAL_INEXACT_EXACTNESS_CLAIM = "INEXACT_EXACTNESS_CLAIM"
# A score result is an exact-measurement value object even when it does not
# claim exactness. Letting a float live in a non-exact result merely delays the
# unsafe conversion until ``to_dict`` and turns a constructor typo into a wire
# failure far from its cause.
REFUSAL_INEXACT_RESIDUAL_NORM = "INEXACT_RESIDUAL_NORM"
# A cochain delta arrived as a float. The residual is formed by subtracting
# these from omega, so admitting one would make the residual inexact and every
# downstream exactness decision meaningless.
REFUSAL_INEXACT_COCHAIN_DELTA = "INEXACT_COCHAIN_DELTA"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _norm_from_wire(wire: Mapping[str, Any], key: str) -> Exact:
    """Read one exact residual norm off the wire.

    Canonical strings are the current form. Bare JSON numbers are accepted for
    wires written before the norms went exact: a finite float is a dyadic
    rational, so the read itself is lossless. It recovers the value that was
    written, which is not the same as recovering the value that was *meant* --
    whatever precision the old float path had already lost is gone. That loss
    is recorded against SPRINT-001-004, not repaired here.
    """
    value = wire[key]
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail(f"{key} must be finite")
        return Fraction(value)
    return coerce_exact(value, field=key)


@dataclass(frozen=True, slots=True)
class CandidateProposal:
    """Candidate repair proposal from an untrusted model turn."""

    proposal_id: str
    repaired_obstruction_ids: tuple[str, ...] = ()
    cochain_delta: tuple[tuple[str, Exact], ...] = ()
    structural_cost: Exact = Fraction(0)
    dual_witness_ref: str | None = None
    kill_triggers: tuple[str, ...] = ()
    admitted_constructors_used: tuple[str, ...] = ()
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not self.proposal_id or not isinstance(self.proposal_id, str):
            _fail("proposal_id must be a non-empty string")
        if isinstance(self.structural_cost, float):
            if not math.isfinite(self.structural_cost):
                _fail("structural_cost must be a non-negative finite number")
            cost = Fraction(self.structural_cost)
        else:
            try:
                cost = coerce_exact(self.structural_cost, field="structural_cost")
            except NotExactError as exc:
                _fail(f"structural_cost must be an exact rational: {exc}")
        if cost < 0:
            _fail("structural_cost must be a non-negative finite number")
        object.__setattr__(self, "structural_cost", cost)
        if self.dual_witness_ref is not None:
            if not isinstance(self.dual_witness_ref, str) or not _SHA256.match(self.dual_witness_ref):
                _fail("dual_witness_ref must be a 64-character lowercase hex digest or None")
        # `repaired_obstruction_ids` is a claim about which obstructions this
        # proposal closes, so it is a set, not a bag. Repeating one id inflated
        # every count downstream: three copies of `obs_1` against three open
        # obstructions scored a full residual drop and `is_exact_candidate`
        # True while repairing exactly one. Scoring can defend itself with
        # `set()`, but the malformed claim is refused here so it cannot reach
        # any other consumer either.
        if type(self.repaired_obstruction_ids) is not tuple or any(
            type(item) is not str or not item
            for item in self.repaired_obstruction_ids
        ):
            _fail("repaired_obstruction_ids must be a tuple of non-empty strings")
        if len(set(self.repaired_obstruction_ids)) != len(
            self.repaired_obstruction_ids
        ):
            _fail("repaired_obstruction_ids must be unique")
        # Deltas are normalized to exact rationals at the boundary, so no
        # inexact term can reach the residual. A float here is refused rather
        # than converted: converting would preserve an upstream rounding error
        # exactly, which is the defect one layer up, not a repair.
        normalized: list[tuple[str, Exact]] = []
        for entry in self.cochain_delta:
            key, value = entry
            try:
                normalized.append((key, coerce_exact(value, field=f"cochain_delta[{key!r}]")))
            except NotExactError as exc:
                _fail(f"{REFUSAL_INEXACT_COCHAIN_DELTA}: {exc}")
        object.__setattr__(self, "cochain_delta", tuple(normalized))


@dataclass(frozen=True, slots=True)
class CoboundaryScoreResult:
    """Host-evaluated score result for a single candidate proposal."""

    proposal_id: str
    # The three residual norms are exact over Q. `is_exact_candidate` is decided
    # by equality with zero on `post_residual_norm`, so carrying it as a float
    # would make the decision a tolerance again by the back door.
    prior_residual_norm: Exact
    post_residual_norm: Exact
    residual_drop: Exact
    # Ranking fields share the Rust frontier's exact representation.
    # A refused proposal has no rational efficiency, represented by None.
    structural_cost: Exact
    normalized_efficiency: Exact | None = None
    is_legal: bool = True
    refusal_reason: str | None = None
    is_exact_candidate: bool = False
    dual_witness_ref: str | None = None
    schema_version: str = field(default=COBOUNDARY_SCORE_SCHEMA)
    family: str = field(default=COBOUNDARY_SCORE_FAMILY)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            _fail("CoboundaryScoreResult must carry AuthorityEffect None")
        if self.schema_version != COBOUNDARY_SCORE_SCHEMA:
            _fail("unsupported schema version")
        if self.family != COBOUNDARY_SCORE_FAMILY:
            _fail("unsupported family")

        # Guard the stronger claim first so a float that happens to equal zero
        # gets the precise exactness refusal expected by callers and tests.
        if self.is_exact_candidate and not is_exact_value(self.post_residual_norm):
            _fail(
                f"{REFUSAL_INEXACT_EXACTNESS_CLAIM}: post_residual_norm is "
                f"{type(self.post_residual_norm).__name__}, not an exact rational"
            )

        for field_name in (
            "prior_residual_norm",
            "post_residual_norm",
            "residual_drop",
        ):
            value = getattr(self, field_name)
            try:
                exact = coerce_exact(value, field=field_name)
            except NotExactError as exc:
                _fail(f"{REFUSAL_INEXACT_RESIDUAL_NORM}: {exc}")
            object.__setattr__(self, field_name, exact)

        if self.prior_residual_norm < 0:
            _fail("prior_residual_norm must be non-negative")
        if self.post_residual_norm < 0:
            _fail("post_residual_norm must be non-negative")

        if isinstance(self.structural_cost, float):
            if not math.isfinite(self.structural_cost):
                _fail("structural_cost must be non-negative")
            cost = Fraction(self.structural_cost)
        else:
            try:
                cost = coerce_exact(self.structural_cost, field="structural_cost")
            except NotExactError as exc:
                _fail(f"structural_cost must be an exact rational: {exc}")
        if cost < 0:
            _fail("structural_cost must be non-negative")
        object.__setattr__(self, "structural_cost", cost)

        if self.normalized_efficiency is not None:
            if isinstance(self.normalized_efficiency, float):
                if not math.isfinite(self.normalized_efficiency):
                    _fail("normalized_efficiency must be finite")
                eff = Fraction(self.normalized_efficiency)
            else:
                try:
                    eff = coerce_exact(self.normalized_efficiency, field="normalized_efficiency")
                except NotExactError as exc:
                    _fail(f"normalized_efficiency must be an exact rational: {exc}")
            object.__setattr__(self, "normalized_efficiency", eff)

        if self.is_exact_candidate:
            # Order matters. The type check comes first so that a float
            # reaching the residual path fails as an inexact *claim*, naming
            # the reason, rather than being silently compared against zero and
            # passing because it happened to round there.
            # Exact equality with zero. A residual of 1e-12 is not exact.
            if self.post_residual_norm != 0:
                _fail("exact candidate requires post_residual_norm == 0")
            if self.dual_witness_ref is None or not _SHA256.match(self.dual_witness_ref):
                _fail(REFUSAL_EXACT_WITHOUT_DUAL_WITNESS)

        if not self.is_legal and self.refusal_reason is None:
            _fail("illegal score result must specify a refusal_reason")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "family": self.family,
            "proposal_id": self.proposal_id,
            # Exact values cross the wire as canonical strings, never as JSON
            # numbers: a JSON number is a float in most readers, and
            # `core-sorted-json-no-float-v1` refuses floats. Same choice the
            # Rust face makes via `#[serde(with = "exact_wire")]`.
            "prior_residual_norm": to_canonical_string(self.prior_residual_norm),
            "post_residual_norm": to_canonical_string(self.post_residual_norm),
            "residual_drop": to_canonical_string(self.residual_drop),
            "structural_cost": to_canonical_string(self.structural_cost),
            "normalized_efficiency": (
                to_canonical_string(self.normalized_efficiency)
                if self.normalized_efficiency is not None
                else None
            ),
            "is_legal": self.is_legal,
            "refusal_reason": self.refusal_reason,
            "is_exact_candidate": self.is_exact_candidate,
            "dual_witness_ref": self.dual_witness_ref,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "CoboundaryScoreResult":
        eff_wire = wire.get("normalized_efficiency")
        return cls(
            proposal_id=str(wire["proposal_id"]),
            prior_residual_norm=_norm_from_wire(wire, "prior_residual_norm"),
            post_residual_norm=_norm_from_wire(wire, "post_residual_norm"),
            residual_drop=_norm_from_wire(wire, "residual_drop"),
            structural_cost=_norm_from_wire(wire, "structural_cost"),
            normalized_efficiency=(
                _norm_from_wire(wire, "normalized_efficiency")
                if eff_wire is not None
                else None
            ),
            is_legal=bool(wire["is_legal"]),
            refusal_reason=(
                None if wire.get("refusal_reason") is None else str(wire["refusal_reason"])
            ),
            is_exact_candidate=bool(wire.get("is_exact_candidate", False)),
            dual_witness_ref=(
                None if wire.get("dual_witness_ref") is None else str(wire["dual_witness_ref"])
            ),
            schema_version=str(wire.get("schema_version", COBOUNDARY_SCORE_SCHEMA)),
            family=str(wire.get("family", COBOUNDARY_SCORE_FAMILY)),
            authority_effect=str(wire.get("authority_effect", "None")),
        )


@dataclass(frozen=True, slots=True)
class ResidualDropV1:
    """One scored residual transition omega -> R."""

    core_mass: float
    residual_mass: float
    delta: float
    relative_drop: float | None
    eliminated_ids: tuple[str, ...]
    opened_ids: tuple[str, ...]
    retained_ids: tuple[str, ...]
    cost: float
    efficiency: float
    residual_colour: str
    dual_witness_present: bool
    legal: bool
    refusal_code: str | None
    authority_effect: str = AUTHORITY_EFFECT

    def to_dict(self) -> dict[str, Any]:
        return {
            "core_mass": self.core_mass,
            "residual_mass": self.residual_mass,
            "delta": self.delta,
            "relative_drop": self.relative_drop,
            "eliminated_ids": list(self.eliminated_ids),
            "opened_ids": list(self.opened_ids),
            "retained_ids": list(self.retained_ids),
            "cost": self.cost,
            "efficiency": self.efficiency,
            "residual_colour": self.residual_colour,
            "dual_witness_present": self.dual_witness_present,
            "legal": self.legal,
            "refusal_code": self.refusal_code,
            "authority_effect": self.authority_effect,
        }


__all__ = [
    "AUTHORITY_EFFECT",
    "COBOUNDARY_SCORE_FAMILY",
    "COBOUNDARY_SCORE_SCHEMA",
    "CandidateProposal",
    "CoboundaryScoreResult",
    "Exact",
    "REFUSAL_AUTHORITY",
    "REFUSAL_EXACT_WITHOUT_DUAL",
    "REFUSAL_EXACT_WITHOUT_DUAL_WITNESS",
    "REFUSAL_ILLEGAL_PROPOSAL",
    "REFUSAL_INEXACT_COCHAIN_DELTA",
    "REFUSAL_INEXACT_EXACTNESS_CLAIM",
    "REFUSAL_INEXACT_RESIDUAL_NORM",
    "REFUSAL_NEGATIVE_MAGNITUDE",
    "ResidualDropV1",
]
