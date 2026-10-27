"""Domain entities and Value Objects for Airy critical carriers and states.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from pfp.domain.shared_kernel.canonical import domain_digest, freeze
from pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from pfp.domain.entities.projection_receipt import Obstruction, ProjectionReceipt


def _is_sha256(value: Any) -> bool:
    return bool(
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_sha256(value: Any, label: str) -> str:
    if not _is_sha256(value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class ComplexScalarV1:
    """Canonical finite complex scalar encoded as two normalized float hexes."""

    real_hex: str
    imag_hex: str

    def __post_init__(self) -> None:
        for label, encoded in (
            ("real_hex", self.real_hex),
            ("imag_hex", self.imag_hex),
        ):
            if type(encoded) is not str:
                raise TypeError(f"{label} must be an exact string")
            try:
                value = float.fromhex(encoded)
            except (ValueError, OverflowError) as exc:
                raise ValueError(f"{label} is not a float-hex value") from exc
            if not math.isfinite(value):
                raise ValueError(f"{label} must encode a finite float")
            if value.hex() != encoded:
                raise ValueError(f"{label} must use normalized float.hex encoding")

    @classmethod
    def from_complex(cls, value: complex) -> "ComplexScalarV1":
        if type(value) is not complex:
            raise TypeError("complex scalar input must be an exact complex value")
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError("complex scalar components must be finite")
        return cls(value.real.hex(), value.imag.hex())

    def to_complex(self) -> complex:
        return complex(float.fromhex(self.real_hex), float.fromhex(self.imag_hex))


@dataclass(frozen=True, slots=True)
class AirySeedSlotV1:
    slot_id: str
    value: ComplexScalarV1

    def __post_init__(self) -> None:
        if type(self.slot_id) is not str or not self.slot_id:
            raise ValueError("Airy slot id must be a non-empty exact string")
        if type(self.value) is not ComplexScalarV1:
            raise TypeError("Airy slot value must be ComplexScalarV1")


@dataclass(frozen=True, slots=True)
class AiryCriticalCarrierV1:
    lambda_scalar: ComplexScalarV1
    slot_ids: tuple[str, ...]
    research_parent_event_id: str
    source_digest: str

    @property
    def carrier_id(self) -> str:
        return "witten-airy-critical-five-slot-v1"

    def __post_init__(self) -> None:
        if type(self.lambda_scalar) is not ComplexScalarV1:
            raise TypeError("Airy carrier lambda must be ComplexScalarV1")
        if self.lambda_scalar.to_complex() == 0.0j:
            raise ValueError("Airy critical carrier requires nonzero lambda")
        if type(self.slot_ids) is not tuple or len(self.slot_ids) != 5:
            raise ValueError("Airy carrier requires exactly five slot ids")
        if any(type(slot_id) is not str or not slot_id for slot_id in self.slot_ids):
            raise ValueError("Airy carrier slot ids must be non-empty exact strings")
        if len(set(self.slot_ids)) != len(self.slot_ids):
            raise ValueError("Airy carrier slot ids must be unique")
        _require_sha256(
            self.research_parent_event_id,
            "research_parent_event_id",
        )
        _require_sha256(self.source_digest, "source_digest")


@dataclass(frozen=True, slots=True)
class AiryCriticalStateV1:
    """Five labeled values; duplicate roots remain distinct carrier slots."""

    slots: tuple[AirySeedSlotV1, ...]

    def __post_init__(self) -> None:
        if type(self.slots) is not tuple or len(self.slots) != 5:
            raise ValueError("Airy critical state requires exactly five slots")
        if any(type(slot) is not AirySeedSlotV1 for slot in self.slots):
            raise TypeError("Airy critical state slots must be AirySeedSlotV1")
        slot_ids = tuple(slot.slot_id for slot in self.slots)
        if len(set(slot_ids)) != len(slot_ids):
            raise ValueError("Airy critical state slot ids must be unique")

    @classmethod
    def from_complex_values(
        cls,
        slot_ids: tuple[str, ...],
        values: tuple[complex, ...],
    ) -> "AiryCriticalStateV1":
        if type(slot_ids) is not tuple or type(values) is not tuple:
            raise TypeError("Airy slot ids and values must be exact tuples")
        if len(slot_ids) != len(values):
            raise ValueError("Airy slot ids and values must have equal length")
        return cls(
            tuple(
                AirySeedSlotV1(slot_id, ComplexScalarV1.from_complex(value))
                for slot_id, value in zip(slot_ids, values)
            )
        )

    @classmethod
    def from_complex_mapping(
        cls,
        values: dict[str, complex],
    ) -> "AiryCriticalStateV1":
        slots = tuple(
            AirySeedSlotV1(slot_id, ComplexScalarV1.from_complex(val))
            for slot_id, val in sorted(values.items())
        )
        return cls(slots)

    def as_complex_mapping(self) -> dict[str, complex]:
        return {slot.slot_id: slot.value.to_complex() for slot in self.slots}

    @property
    def slot_ids(self) -> tuple[str, ...]:
        return tuple(slot.slot_id for slot in self.slots)

    def complex_values(self) -> tuple[complex, ...]:
        return tuple(slot.value.to_complex() for slot in self.slots)


def evaluate_airy_critical_residuals(
    carrier: AiryCriticalCarrierV1,
    state: AiryCriticalStateV1,
) -> tuple[tuple[float, ...], float]:
    """Evaluate critical equation residuals for each slot and return (residuals, max_residual)."""
    lam = carrier.lambda_scalar.to_complex()
    residuals = tuple(
        abs(lam * (value * value - 1.0)) for value in state.complex_values()
    )
    maximum = max(residuals) if residuals else 0.0
    if not math.isfinite(maximum):
        raise ValueError("Airy critical residual must be finite")
    return residuals, maximum


__all__ = [
    "AiryCriticalCarrierV1",
    "AiryCriticalStateV1",
    "AirySeedSlotV1",
    "ComplexScalarV1",
    "evaluate_airy_critical_residuals",
]
