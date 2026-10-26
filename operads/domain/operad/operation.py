"""
Operation Value Objects and Invariants for Coloured Operads.
============================================================

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .colours import Colour, ColourSignature
from .errors import ArityMismatchError


@dataclass(frozen=True)
class OperationId:
    """Unique identifier for an operad operation or skill."""
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("OperationId value must be a non-empty string.")

    @property
    def is_unit(self) -> bool:
        return self.value.startswith("id_")

    @classmethod
    def unit_for(cls, colour: Colour | str) -> OperationId:
        c_name = colour.name if isinstance(colour, Colour) else str(colour)
        return cls(f"id_{c_name}")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))


@dataclass(frozen=True)
class OperationSignature:
    """Complete structural signature of an operadic operation."""
    op_id: OperationId
    signature: ColourSignature
    equivariant: bool = False
    residual_effect: str = "unknown"

    @property
    def arity(self) -> int:
        return self.signature.arity

    @property
    def source(self) -> tuple[Colour, ...]:
        return self.signature.source

    @property
    def source_colours(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.signature.source)

    @property
    def target(self) -> Colour:
        return self.signature.target

    @property
    def target_colour(self) -> str:
        return self.signature.target.name

    @classmethod
    def unit(cls, colour: Colour | str) -> OperationSignature:
        c = colour if isinstance(colour, Colour) else Colour(str(colour))
        return cls(
            op_id=OperationId.unit_for(c),
            signature=ColourSignature(source=[c], target=c),
            equivariant=True,
            residual_effect="identity",
        )

    @property
    def is_unit(self):
        return self.residual_effect == "identity" and self.arity == 1 and self.source[0] == self.target and self.op_id == OperationId.unit_for(self.target)

    @classmethod
    def create(cls, op_id, source, target, arity=None, equivariant=False, residual_effect="unknown"):
        if arity is not None and arity != len(source):
            raise ArityMismatchError("declared arity differs from ordered sources")
        return cls(OperationId(op_id), ColourSignature(source,target),equivariant,residual_effect)

    def to_dict(self):
        return {"skill_id":self.op_id.value,"arity":self.arity,"source_colours":list(self.source_colours),"target_colour":self.target_colour,"equivariant":self.equivariant,"residual_effect":self.residual_effect}

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.op_id == other.op_id
            and self.signature == other.signature
            and self.equivariant == other.equivariant
            and self.residual_effect == other.residual_effect
        )

    def __hash__(self) -> int:
        return hash((type(self), self.op_id, self.signature, self.equivariant, self.residual_effect))
