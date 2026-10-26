"""Records the research loop passes between its layers.

The loop's state itself is a checkpoint owned by the Rust controller
(``omega_woland::research_loop``); Python carries it opaquely and never edits it.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Dispatch(str, Enum):
    """What happened to one model request; it decides how the reservation is closed."""

    NOT_SENT = "NOT_SENT"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    REPLIED = "REPLIED"


@dataclass(frozen=True, slots=True)
class LoopSnapshotV1:
    """The controller's answer to one command: the new checkpoint and what comes next."""

    checkpoint: Mapping[str, Any]
    next_action: Mapping[str, Any]
    spent: Mapping[str, Any]
    terminal: str | None
    output: Mapping[str, Any]

    @property
    def state_sha256(self) -> str:
        return str(self.checkpoint["state_sha256"])

    @property
    def run_id(self) -> str:
        return str(self.checkpoint["state"]["admitted"]["mission"]["run_id"])


@dataclass(frozen=True, slots=True)
class DispatchOutcomeV1:
    """One provider request as the Symbol Game transport reports it."""

    dispatch: Dispatch
    refusal: Mapping[str, Any] | None
    raw_path: str | None
    raw_sha256: str | None
    text: str | None
    usage: Mapping[str, Any] | None
    metered_cost_microusd: int | None
    quote_microusd: int | None

    def __post_init__(self) -> None:
        if type(self.dispatch) is not Dispatch:
            raise TypeError("dispatch must be a Dispatch")
        if self.dispatch is Dispatch.REPLIED and self.raw_path is None:
            raise ValueError("a reply is always persisted before it is reported")


@dataclass(frozen=True, slots=True)
class SubmissionV1:
    """The result of submitting one stage response."""

    occurrence_id: str
    raw_path: str
    accepted: bool
    violations: tuple[str, ...]
    snapshot: LoopSnapshotV1


__all__ = ["Dispatch", "DispatchOutcomeV1", "LoopSnapshotV1", "SubmissionV1"]
