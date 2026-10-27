"""Native reply-control crossing; model-authored fields remain declarations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from operations.domain.rop.result import Refusal, Result


class ReplyControlPort(Protocol):
    def invoke(self, payload: Mapping[str, Any]) -> Result[Mapping[str, Any], Refusal]:
        """Return the complete native outcome or typed transport refusal."""
        ...
