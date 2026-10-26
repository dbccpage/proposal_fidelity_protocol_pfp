"""Colour-vocabulary reconciliation module for the Woland stage.

Reconciles the three distinct colour namespaces:
1. Turn reply RESIDUAL_COLOUR in {Open, Closed, Exact}
2. Seat capability colours in {Audit, Receipt, State, Code, Ledger}
3. Council residual_sort (e.g. isolation_residual, gauge_break_residual, etc.)

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from typing import Sequence

TURN_REPLY_RESIDUAL_COLOURS = frozenset({"Open", "Closed", "Exact"})
SEAT_CAPABILITY_COLOURS = frozenset({"Audit", "Receipt", "State", "Code", "Ledger"})
RESIDUAL_CODE = re.compile(r"^[a-z][a-z0-9_]*$")


def project_residuals_to_codes(
    turn_residual_colour: str,
    council_residual_sort: str = "",
    extra_codes: Sequence[str] = (),
) -> tuple[str, ...]:
    """Map turn reply colour + council residual sort to canonical AgentResult residual_codes."""
    codes: list[str] = []

    # Map turn reply colour
    if type(turn_residual_colour) is not str or turn_residual_colour not in TURN_REPLY_RESIDUAL_COLOURS:
        raise ValueError("turn residual colour is not in the canonical vocabulary")
    codes.append(f"colour_{turn_residual_colour.lower()}")

    # Map council residual sort if provided
    if council_residual_sort:
        if type(council_residual_sort) is not str:
            raise TypeError("council residual sort must be an exact string")
        clean_sort = council_residual_sort.strip().lower()
        if not clean_sort or RESIDUAL_CODE.fullmatch(clean_sort) is None:
            raise ValueError("council residual sort is not canonical")
        codes.append(clean_sort)

    for code in extra_codes:
        if type(code) is not str or code != code.strip() or RESIDUAL_CODE.fullmatch(code) is None:
            raise ValueError("extra residual code is not canonical")
        if code not in codes:
            codes.append(code)

    return tuple(sorted(set(codes)))


def validate_seat_capabilities(
    seat_colours: Sequence[str],
    operation_colours: Sequence[str],
) -> bool:
    """Assert that a seat carries all required capability colours for its operations."""
    seat_set = set(seat_colours)
    operation_set = set(operation_colours)
    if not seat_set.issubset(SEAT_CAPABILITY_COLOURS):
        return False
    if not operation_set.issubset(SEAT_CAPABILITY_COLOURS):
        return False
    return operation_set.issubset(seat_set)
