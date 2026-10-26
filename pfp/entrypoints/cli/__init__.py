"""CLI presentation layer for symbol_game."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def build_parser() -> Any:
    from .symbol_game import build_parser as implementation

    return implementation()


def main(argv: Sequence[str] | None = None) -> int:
    from .symbol_game import main as implementation

    return implementation(argv)

__all__ = [
    "build_parser",
    "main",
]
