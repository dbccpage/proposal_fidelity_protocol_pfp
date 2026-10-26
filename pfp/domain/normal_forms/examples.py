"""Textbook schemas used by normal-form lessons and examples.

AuthorityEffect: None.
"""

from __future__ import annotations

from .relational import (
    FunctionalDependency,
    RelationalSchema,
    check_2nf,
    check_3nf,
    check_bcnf,
    check_dependency_preservation,
    check_lossless_decomposition,
)


def order_line() -> RelationalSchema:
    """OrderId determines OrderDate, and the key is (OrderId, LineNo)."""
    return RelationalSchema(
        attributes=frozenset({"OrderId", "LineNo", "OrderDate"}),
        dependencies=frozenset(
            {
                FunctionalDependency.from_str("OrderId,LineNo", "OrderDate"),
                FunctionalDependency.from_str("OrderId", "OrderDate"),
            }
        ),
    )


def street_journal_title() -> RelationalSchema:
    """SJ -> T and T -> J. Third normal form holds. Boyce-Codd normal form does not."""
    return RelationalSchema(
        attributes=frozenset({"S", "J", "T"}),
        dependencies=frozenset(
            {
                FunctionalDependency.from_str("S,J", "T"),
                FunctionalDependency.from_str("T", "J"),
            }
        ),
    )


def street_journal_title_split() -> tuple[bool, bool]:
    """Heath split into (T, J) and (S, T).

    Returns whether the split is lossless, then whether it preserves SJ -> T.
    """
    schema = street_journal_title()
    pieces = (frozenset({"T", "J"}), frozenset({"S", "T"}))
    lossless, _ = check_lossless_decomposition(schema, pieces)
    preserved, _ = check_dependency_preservation(schema, pieces)
    return lossless, preserved


def order_line_fails_second_normal_form() -> bool:
    ok, _ = check_2nf(order_line())
    return not ok


def street_journal_title_passes_third_and_fails_boyce_codd() -> bool:
    schema = street_journal_title()
    third, _ = check_3nf(schema)
    boyce, _ = check_bcnf(schema)
    return third and not boyce
