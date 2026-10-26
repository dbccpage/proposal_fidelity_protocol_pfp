"""Illegal Transition Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .packet_state import PacketState


class IllegalTransition(ValueError):
    def __init__(
        self, src: PacketState | None, dst: PacketState, detail: str = ""
    ) -> None:
        self.src = src
        self.dst = dst
        super().__init__(f"ILLEGAL_TRANSITION:{src}->{dst}:{detail}")
