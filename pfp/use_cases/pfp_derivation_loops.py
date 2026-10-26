"""Bounded research loops; acceptance never short-circuits requested exploration."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class DerivationLimits:
    loops: int = 5
    microusd: int = 50_000
    tokens: int = 120_000
    seconds: int = 180

    def __post_init__(self):
        if any(type(x) is not int or x <= 0 for x in vars(self).values()):
            raise ValueError("INVALID_DERIVATION_LIMIT")
        if self.loops > 5 or self.microusd > 50_000 or self.tokens > 120_000 or self.seconds > 180:
            raise ValueError("DERIVATION_LIMIT_EXCEEDS_AUTHORIZATION")


class DerivationStop(RuntimeError):
    """An explicit resource or infrastructure terminal, never a silent retry."""


class DerivationPort(Protocol):
    def begin(self, limits: DerivationLimits) -> None: ...
    def propose(self, loop: int, context: dict[str, Any]) -> Any: ...
    def observe(self, loop: int, proposal: Any, context: dict[str, Any]) -> dict[str, Any]: ...
    def finish(self, completed: int, terminal: str, context: dict[str, Any]) -> Any: ...


def run_derivation_loops(port: DerivationPort, limits: DerivationLimits = DerivationLimits()):
    """Each proposal traverses lift, independent check, control and learning stages."""
    port.begin(limits)
    context: dict[str, Any] = {}
    completed = 0
    terminal = "LOOP_LIMIT"
    try:
        for loop in range(1, limits.loops + 1):
            proposal = port.propose(loop, context)
            context = port.observe(loop, proposal, context)
            completed = loop
    except DerivationStop as exc:
        terminal = str(exc)
    return port.finish(completed, terminal, context)
