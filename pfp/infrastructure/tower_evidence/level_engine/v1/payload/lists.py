"""Hosted lists of naturals: a list is an element, its entries are elements
of one sort carrying their values, and ``of(entry, list)`` places an entry
in a list; the list's order is the declared order of its entries.

AuthorityEffect: None
"""

from __future__ import annotations

from engine.structure import FiniteStructure
from payload.shared import rows


def nat(fs: FiniteStructure, e: int) -> int:
    """An element's value as a natural; -1 when it is not one."""
    v = fs.value(e)
    return v.num if v is not None and v.den == 1 and v.num >= 0 else -1


def entries(fs: FiniteStructure, lst: int, relation: str = "of", sort: str = "entry") -> list[int]:
    mine = {e for e, ll in rows(fs, relation) if ll == lst}
    return [nat(fs, e) for e in fs.elements(sort) if e in mine]
