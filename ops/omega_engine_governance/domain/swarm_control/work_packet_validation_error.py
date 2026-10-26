"""Work Packet Validation Error.

AuthorityEffect: None.
"""

from __future__ import annotations


class WorkPacketValidationError(ValueError):
    def __init__(self, residual: str) -> None:
        self.residual = residual
        super().__init__(residual)
