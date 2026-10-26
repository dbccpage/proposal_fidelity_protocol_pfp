"""Domain error catalog for the Packets Bounded Context."""

from __future__ import annotations

from dataclasses import dataclass

from .value_objects import RefusalCode


@dataclass(frozen=True)
class PacketDomainError:
    """Base error for packet domain violations."""
    code: RefusalCode
    message: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PacketDomainError)
        return self.code == other.code and self.message == other.message

    def __hash__(self) -> int:
        return hash((type(self), self.code, self.message))


@dataclass(frozen=True)
class MalformedWireError(PacketDomainError):
    pass


@dataclass(frozen=True)
class StageFloorViolationError(PacketDomainError):
    pass


@dataclass(frozen=True)
class ArityMismatchError(PacketDomainError):
    pass


@dataclass(frozen=True)
class NonconservativeLiftError(PacketDomainError):
    pass
