"""Tool Result Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolResult:
    call_id: str
    tool_name: str
    content: Any
    is_error: bool = False
