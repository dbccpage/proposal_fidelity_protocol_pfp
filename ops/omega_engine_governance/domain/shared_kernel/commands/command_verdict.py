from __future__ import annotations

from dataclasses import dataclass

from ..value_objects.digest import Digest
from ..value_objects.identifier import Identifier
from .command_status import CommandStatus


@dataclass(frozen=True, slots=True)
class CommandVerdict:
    """Strongly-typed result of evaluating or applying a command intent."""

    command_id: Identifier
    status: CommandStatus
    detail: str = ""
    evidence_digest: Digest | None = None
