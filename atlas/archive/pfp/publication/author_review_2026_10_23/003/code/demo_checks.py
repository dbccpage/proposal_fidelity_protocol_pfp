"""Explicit runtime checks for the demonstration scripts.

``assert`` statements are removed by ``python -O``; these checks are not. A failed
check raises ``DemoCheckError``, so a demonstration script exits with a nonzero
status instead of reporting success.
"""

from __future__ import annotations


class DemoCheckError(RuntimeError):
    """A demonstration expectation did not hold."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DemoCheckError(message)
