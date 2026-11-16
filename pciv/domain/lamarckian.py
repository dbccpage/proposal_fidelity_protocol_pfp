"""Lamarckian Mutation Receipt and Cochain Residual Value Objects (NF-02).

Conforms to normative specification:
`urn:core:nf:prompt_civilization:lamarckian_pfp_adversary_loop:v1.0.0`

Enforces:
- Rule 1: Protected Core Invariance (Core(G_{g+1}) == Core(G_g)).
- Rule 2: Witness Grounding (No antibody injection without verified falsification witness).
- Rule 3: Attenuated Influence (w(alpha, d) = (1/2)^d for 1 <= d <= 10; d > 10 evaporated).

AuthorityEffect: None.
Zero-Float Law: Uses exact rational arithmetic (fractions.Fraction).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

SHA256_PREFIXED_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
RATIONAL_PATTERN = re.compile(r"^-?[0-9]+/[1-9][0-9]*$")
WEIGHT_PATTERN = re.compile(r"^[0-9]+/[1-9][0-9]*$")


def _format_fraction(val: Fraction | int | str) -> str:
    if isinstance(val, str):
        if "/" in val:
            parts = val.split("/")
            f = Fraction(int(parts[0]), int(parts[1]))
            return f"{f.numerator}/{f.denominator}"
        f = Fraction(int(val), 1)
        return f"{f.numerator}/{f.denominator}"
    if isinstance(val, int):
        return f"{val}/1"
    if isinstance(val, Fraction):
        return f"{val.numerator}/{val.denominator}"
    raise TypeError(f"Zero-Float Law: float or non-rational type {type(val)} forbidden")


@dataclass(frozen=True, slots=True)
class CochainResidualV1:
    """Exact rational cochain obstruction triad (Phi_1, Gamma_2, Xi)."""

    phi1: str
    gamma2: str
    xi: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        for name, val in (("phi1", self.phi1), ("gamma2", self.gamma2), ("xi", self.xi)):
            if not isinstance(val, str) or not RATIONAL_PATTERN.match(val):
                raise ValueError(f"INVALID_COCHAIN_RATIONAL: {name}={val!r}")

    @property
    def phi1_fraction(self) -> Fraction:
        parts = self.phi1.split("/")
        return Fraction(int(parts[0]), int(parts[1]))

    @property
    def gamma2_fraction(self) -> Fraction:
        parts = self.gamma2.split("/")
        return Fraction(int(parts[0]), int(parts[1]))

    @property
    def xi_fraction(self) -> Fraction:
        parts = self.xi.split("/")
        return Fraction(int(parts[0]), int(parts[1]))

    @classmethod
    def from_fractions(
        cls,
        phi1: Fraction | int | str = 0,
        gamma2: Fraction | int | str = 0,
        xi: Fraction | int | str = 0,
    ) -> CochainResidualV1:
        return cls(
            phi1=_format_fraction(phi1),
            gamma2=_format_fraction(gamma2),
            xi=_format_fraction(xi),
        )

    def to_dict(self) -> dict[str, str]:
        return {"phi1": self.phi1, "gamma2": self.gamma2, "xi": self.xi}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CochainResidualV1:
        return cls(
            phi1=str(data["phi1"]),
            gamma2=str(data["gamma2"]),
            xi=str(data["xi"]),
        )


@dataclass(frozen=True, slots=True)
class LamarckianMutationReceiptV1:
    """Normative machine receipt certifying a Lamarckian retro-inheritance mutation.

    Schema: `urn:core:nf:prompt_civilization:lamarckian_pfp_adversary_loop:v1.0.0`
    """

    receipt_id: str
    parent_genome_id: str
    child_genome_id: str
    falsification_witness_sha256: str
    cochain_residual: CochainResidualV1
    antibody_id: str
    hop_distance: int
    attenuation_weight: str
    created_utc: str

    def __post_init__(self) -> None:
        self.validate()

    @staticmethod
    def calculate_attenuation_weight(hop_distance: int) -> str:
        """Rule 3: w(alpha, d) = (1/2)^d for 1 <= d <= 10."""
        if hop_distance < 1 or hop_distance > 10:
            raise ValueError(
                f"HOP_DISTANCE_OUT_OF_BOUNDS: hop_distance={hop_distance} must be in [1, 10]"
            )
        denom = 1 << hop_distance
        return f"1/{denom}"

    def payload_dict(self) -> dict[str, Any]:
        """Canonical payload over which receipt_id is digested."""
        return {
            "antibody_id": self.antibody_id,
            "attenuation_weight": self.attenuation_weight,
            "child_genome_id": self.child_genome_id,
            "cochain_residual": {
                "gamma2": self.cochain_residual.gamma2,
                "phi1": self.cochain_residual.phi1,
                "xi": self.cochain_residual.xi,
            },
            "created_utc": self.created_utc,
            "falsification_witness_sha256": self.falsification_witness_sha256,
            "hop_distance": self.hop_distance,
            "parent_genome_id": self.parent_genome_id,
        }

    def canonical_bytes(self) -> bytes:
        """RFC 8785 canonical JSON bytes of the receipt payload."""
        payload = self.payload_dict()
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def canonical_digest(self) -> str:
        """Compute the content-addressed receipt digest."""
        return f"sha256:{hashlib.sha256(self.canonical_bytes()).hexdigest()}"

    def validate(self) -> None:
        if not SHA256_PREFIXED_PATTERN.match(self.receipt_id):
            raise ValueError(f"INVALID_RECEIPT_ID_FORMAT: {self.receipt_id!r}")
        if not SHA256_PREFIXED_PATTERN.match(self.parent_genome_id):
            raise ValueError(f"INVALID_PARENT_GENOME_ID_FORMAT: {self.parent_genome_id!r}")
        if not SHA256_PREFIXED_PATTERN.match(self.child_genome_id):
            raise ValueError(f"INVALID_CHILD_GENOME_ID_FORMAT: {self.child_genome_id!r}")
        if not SHA256_HEX_PATTERN.match(self.falsification_witness_sha256):
            raise ValueError(
                f"INVALID_WITNESS_SHA256_FORMAT: {self.falsification_witness_sha256!r}"
            )
        if not self.antibody_id or not self.antibody_id.strip():
            raise ValueError("ANTIBODY_ID_CANNOT_BE_EMPTY")
        if self.hop_distance < 1 or self.hop_distance > 10:
            raise ValueError(
                f"HOP_DISTANCE_OUT_OF_BOUNDS: hop_distance={self.hop_distance} must be in [1, 10]"
            )
        if not WEIGHT_PATTERN.match(self.attenuation_weight):
            raise ValueError(f"INVALID_ATTENUATION_WEIGHT_FORMAT: {self.attenuation_weight!r}")

        expected_weight = self.calculate_attenuation_weight(self.hop_distance)
        if self.attenuation_weight != expected_weight:
            raise ValueError(
                f"ATTENUATION_WEIGHT_MISMATCH: expected {expected_weight} for hop "
                f"{self.hop_distance}, got {self.attenuation_weight}"
            )

        self.cochain_residual.validate()

        computed_id = self.canonical_digest()
        if self.receipt_id != computed_id:
            raise ValueError(
                f"RECEIPT_ID_DIGEST_MISMATCH: expected {computed_id}, got {self.receipt_id}"
            )

    @classmethod
    def create(
        cls,
        *,
        parent_genome_id: str,
        child_genome_id: str,
        falsification_witness_sha256: str,
        cochain_residual: CochainResidualV1,
        antibody_id: str,
        hop_distance: int = 1,
        attenuation_weight: str | None = None,
        created_utc: str | None = None,
    ) -> LamarckianMutationReceiptV1:
        """Factory creating and sealing an authentic LamarckianMutationReceiptV1."""
        if attenuation_weight is None:
            attenuation_weight = cls.calculate_attenuation_weight(hop_distance)
        if created_utc is None:
            created_utc = datetime.datetime.now(datetime.UTC).isoformat()

        # Compute receipt_id from canonical payload
        payload = {
            "antibody_id": antibody_id,
            "attenuation_weight": attenuation_weight,
            "child_genome_id": child_genome_id,
            "cochain_residual": {
                "gamma2": cochain_residual.gamma2,
                "phi1": cochain_residual.phi1,
                "xi": cochain_residual.xi,
            },
            "created_utc": created_utc,
            "falsification_witness_sha256": falsification_witness_sha256,
            "hop_distance": hop_distance,
            "parent_genome_id": parent_genome_id,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        receipt_id = f"sha256:{hashlib.sha256(raw).hexdigest()}"

        receipt = cls(
            receipt_id=receipt_id,
            parent_genome_id=parent_genome_id,
            child_genome_id=child_genome_id,
            falsification_witness_sha256=falsification_witness_sha256,
            cochain_residual=cochain_residual,
            antibody_id=antibody_id,
            hop_distance=hop_distance,
            attenuation_weight=attenuation_weight,
            created_utc=created_utc,
        )
        receipt.validate()
        return receipt

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict matching normative JSON schema."""
        return {
            "receipt_id": self.receipt_id,
            "parent_genome_id": self.parent_genome_id,
            "child_genome_id": self.child_genome_id,
            "falsification_witness_sha256": self.falsification_witness_sha256,
            "cochain_residual": self.cochain_residual.to_dict(),
            "antibody_id": self.antibody_id,
            "hop_distance": self.hop_distance,
            "attenuation_weight": self.attenuation_weight,
            "created_utc": self.created_utc,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LamarckianMutationReceiptV1:
        """Instantiate and validate from wire dictionary."""
        residual = CochainResidualV1.from_dict(data["cochain_residual"])
        receipt = cls(
            receipt_id=str(data["receipt_id"]),
            parent_genome_id=str(data["parent_genome_id"]),
            child_genome_id=str(data["child_genome_id"]),
            falsification_witness_sha256=str(data["falsification_witness_sha256"]),
            cochain_residual=residual,
            antibody_id=str(data["antibody_id"]),
            hop_distance=int(data["hop_distance"]),
            attenuation_weight=str(data["attenuation_weight"]),
            created_utc=str(data["created_utc"]),
        )
        receipt.validate()
        return receipt


@dataclass(frozen=True)
class ReproducedFailureCaseV1:
    """Minimal parent failure case replayed to test whether a child genome cured the defect."""

    case_id: str
    prompt_utf8_bytes: bytes
    parent_failing_reply_bytes: bytes
    failure_class: str
    witness_sha256: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.case_id) is not str or not self.case_id.strip():
            raise ValueError("REPRODUCED_CASE_ID_REQUIRED")
        if type(self.prompt_utf8_bytes) is not bytes or not self.prompt_utf8_bytes:
            raise ValueError("REPRODUCED_CASE_PROMPT_BYTES_REQUIRED")
        if type(self.parent_failing_reply_bytes) is not bytes or not self.parent_failing_reply_bytes:
            raise ValueError("REPRODUCED_CASE_REPLY_BYTES_REQUIRED")
        if type(self.failure_class) is not str or not self.failure_class.strip():
            raise ValueError("REPRODUCED_CASE_FAILURE_CLASS_REQUIRED")
        hex_part = (
            self.witness_sha256.removeprefix("sha256:")
            if isinstance(self.witness_sha256, str)
            else ""
        )
        if not re.fullmatch(r"[0-9a-f]{64}", hex_part):
            raise ValueError(f"REPRODUCED_CASE_WITNESS_INVALID:{self.witness_sha256!r}")
        if self.authority_effect != "None":
            raise ValueError("AUTHORITY_EFFECT_MUST_BE_NONE")


@dataclass(frozen=True)
class LineageCureReceiptV1:
    """Receipt attesting whether a Lamarckian child genome cured or relapsed on the parent failure."""

    receipt_id: str
    parent_genome_id: str
    child_genome_id: str
    lamarckian_receipt_id: str
    antibody_id: str
    antibody_screened: bool
    antibody_fired_on_parent_failure: bool
    child_signal1_fired: bool
    host_failure_reproduced: bool
    child_checker_receipt_sha256: str
    cure_status: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        for attr in (
            "receipt_id",
            "parent_genome_id",
            "child_genome_id",
            "lamarckian_receipt_id",
            "child_checker_receipt_sha256",
        ):
            val = getattr(self, attr)
            if type(val) is not str or not re.fullmatch(r"sha256:[0-9a-f]{64}", val):
                raise ValueError(f"INVALID_CURE_SHA256_REF:{attr}:{val!r}")
        if type(self.antibody_id) is not str or not self.antibody_id.strip():
            raise ValueError("INVALID_CURE_ANTIBODY_ID")
        for battr in (
            "antibody_screened",
            "antibody_fired_on_parent_failure",
            "child_signal1_fired",
            "host_failure_reproduced",
        ):
            if type(getattr(self, battr)) is not bool:
                raise TypeError(f"{battr} must be an exact bool")
        if self.cure_status not in ("RELAPSED_BURIED", "CURED_ADOPTED"):
            raise ValueError(f"INVALID_CURE_STATUS:{self.cure_status!r}")
        if self.authority_effect != "None":
            raise ValueError("AUTHORITY_EFFECT_MUST_BE_NONE")

    @classmethod
    def create(
        cls,
        *,
        parent_genome_id: str,
        child_genome_id: str,
        lamarckian_receipt_id: str,
        antibody_id: str,
        antibody_screened: bool,
        antibody_fired_on_parent_failure: bool,
        child_signal1_fired: bool,
        host_failure_reproduced: bool,
        child_checker_receipt_sha256: str,
        cure_status: str,
    ) -> LineageCureReceiptV1:
        """Create a content-addressed lineage cure receipt."""
        payload = {
            "antibody_fired_on_parent_failure": antibody_fired_on_parent_failure,
            "antibody_id": antibody_id,
            "antibody_screened": antibody_screened,
            "authority_effect": "None",
            "child_checker_receipt_sha256": child_checker_receipt_sha256,
            "child_genome_id": child_genome_id,
            "child_signal1_fired": child_signal1_fired,
            "cure_status": cure_status,
            "host_failure_reproduced": host_failure_reproduced,
            "lamarckian_receipt_id": lamarckian_receipt_id,
            "parent_genome_id": parent_genome_id,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
        receipt_id = "sha256:" + hashlib.sha256(raw).hexdigest()
        return cls(
            receipt_id=receipt_id,
            parent_genome_id=parent_genome_id,
            child_genome_id=child_genome_id,
            lamarckian_receipt_id=lamarckian_receipt_id,
            antibody_id=antibody_id,
            antibody_screened=antibody_screened,
            antibody_fired_on_parent_failure=antibody_fired_on_parent_failure,
            child_signal1_fired=child_signal1_fired,
            host_failure_reproduced=host_failure_reproduced,
            child_checker_receipt_sha256=child_checker_receipt_sha256,
            cure_status=cure_status,
            authority_effect="None",
        )


__all__ = [
    "CochainResidualV1",
    "LamarckianMutationReceiptV1",
    "LineageCureReceiptV1",
    "ReproducedFailureCaseV1",
]
