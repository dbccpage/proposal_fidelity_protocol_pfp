"""Domain exception hierarchy for research run graphs.

AuthorityEffect: None.
"""

from __future__ import annotations


class PaperRunGraphError(ValueError):
    """Illegal graph, plan, or transition."""


__all__ = [
    "PaperRunGraphError",
]
