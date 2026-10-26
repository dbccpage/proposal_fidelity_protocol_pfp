"""Domain ports for TurnView Representation (U25).

Defines the bidirectional RepresentationPort for rendering and parsing board views.
AuthorityEffect: None.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import TurnView


@runtime_checkable
class RepresentationPort(Protocol):
    """Port for encoding and decoding TurnView states."""

    @property
    def representation_id(self) -> str:
        """Canonical ID of the representation (e.g. GLYPH_PACKET or PLAIN_TEXT)."""
        ...

    def render(self, view: TurnView) -> str:
        """Render a TurnView to text/serialized representation."""
        ...

    def parse(self, rendered: str) -> TurnView:
        """Parse rendered text back into exact TurnView."""
        ...
