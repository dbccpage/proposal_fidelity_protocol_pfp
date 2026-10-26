"""Planar substitution over the skill garden's coloured operad.

`EPIC-OE-OEWAS-003` deliverable 1 asks for a `PlanarSubstitutionEvaluator` for
$n$-ary compositions $\\theta \\circ_i \\phi$, and deliverable 2 for an
`AssociativityWitnessRegistry` "verifying that every declared composition path
possesses an exact witness composite operation".

The two are one thing. Substitution is admissible exactly when the colour
$\\phi$ produces matches the colour $\\theta$ expects at slot $i$; associativity
is the statement that two ways of nesting three admissible substitutions land on
the same composite. A registry that stored witnesses without deciding
admissibility would be a list of claims, so this computes the composite and the
witness is the composite itself.

Every skill in the garden declares `operad_source_colours`,
`operad_target_colour` and `operad_arity`. Measured across 110 skills: no field
is missing, no arity disagrees with its own source list, and exactly ten colours
appear in either position. The vocabulary is closed and the declarations are
self-consistent, which is what makes composition decidable at all.

**This module does not grade.** Skills do declare `invocation:` as `entry` or
`discipline`. A missing line is not entry. There is no
`TwoLayerGradingValidator` and no grade field on `OperadOperation`.
Entry-over-entry refusal is `validate_composition_grading` over that declared
field, and `ENTRY_OVER_ENTRY` in the Rust kernel. An omitted Rust
`InvocationGrade` defaults to `Discipline`.

The immune-guarded variants of `substitute` are in the application layer
(`application/immune_guards.py`), which asks the Epistemic Immune System through
a port; this domain module does not import it.

`AuthorityEffect: None`.
"""

from __future__ import annotations

from dataclasses import dataclass

# The ten colours, measured from the garden and matching the vocabulary
# `EPIC-OE-OEWAS-RUST-001` pins ("Ten colours | Shared Python/Rust vocabulary
# fixture | Reorder, omit, or add one colour"). Closed: an operation whose
# colour is outside this set cannot be composed with anything, and silently
# admitting it would make composability depend on spelling.
OPERAD_COLOURS = frozenset(
    {
        "Audit",
        "Code",
        "Contract",
        "Diagram",
        "Ledger",
        "Paper",
        "Post",
        "Proof",
        "Receipt",
        "State",
    }
)


class SubstitutionError(RuntimeError):
    """A typed refusal naming why a substitution is inadmissible."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class OperadOperation:
    """One operation: the colours it consumes, and the colour it produces."""

    name: str
    source_colours: tuple[str, ...]
    target_colour: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise SubstitutionError("BAD_NAME", "name must be a nonempty string")
        if type(self.source_colours) is not tuple:
            raise SubstitutionError(
                "BAD_SOURCES", "source_colours must be an exact tuple"
            )
        unknown = sorted(set(self.source_colours) - OPERAD_COLOURS)
        if unknown:
            raise SubstitutionError(
                "UNKNOWN_COLOUR",
                f"{self.name} declares source colours outside the closed "
                f"vocabulary: {unknown}",
            )
        if self.target_colour not in OPERAD_COLOURS:
            raise SubstitutionError(
                "UNKNOWN_COLOUR",
                f"{self.name} declares target colour {self.target_colour!r}, "
                "which is outside the closed vocabulary",
            )

    @property
    def arity(self) -> int:
        """Derived, never declared separately.

        An operation whose arity is a field can disagree with its own source
        list -- the defect sprint 006 found in the fibration table, where a row
        declared 7 beside eight names. Here the two cannot disagree because
        there is only one of them.
        """
        return len(self.source_colours)


def substitute(theta: OperadOperation, index: int, phi: OperadOperation) -> OperadOperation:
    """Compute $\\theta \\circ_i \\phi$, or refuse.

    Admissible exactly when $\\phi$'s target colour is the colour $\\theta$
    expects at slot `index`. The composite consumes $\\theta$'s inputs with slot
    `index` replaced by all of $\\phi$'s, in place -- which is what makes the
    substitution *planar*: the order of the remaining inputs is preserved.
    """
    if type(theta) is not OperadOperation or type(phi) is not OperadOperation:
        raise SubstitutionError("BAD_OPERATION", "both arguments must be operations")
    if type(index) is not int or type(index) is bool:
        raise SubstitutionError("BAD_INDEX", "index must be an exact integer")
    if not 0 <= index < theta.arity:
        raise SubstitutionError(
            "INDEX_OUT_OF_RANGE",
            f"{theta.name} has arity {theta.arity}; slot {index} does not exist",
        )
    expected = theta.source_colours[index]
    if phi.target_colour != expected:
        raise SubstitutionError(
            "COLOUR_MISMATCH",
            f"{theta.name} expects {expected!r} at slot {index}, but "
            f"{phi.name} produces {phi.target_colour!r}",
        )
    return OperadOperation(
        name=f"({theta.name} o_{index} {phi.name})",
        source_colours=(
            theta.source_colours[:index]
            + phi.source_colours
            + theta.source_colours[index + 1 :]
        ),
        target_colour=theta.target_colour,
    )


def is_admissible(theta: OperadOperation, index: int, phi: OperadOperation) -> bool:
    """Whether a substitution would be admitted, without raising."""
    try:
        substitute(theta, index, phi)
    except SubstitutionError:
        return False
    return True


def associativity_witness(
    theta: OperadOperation,
    i: int,
    phi: OperadOperation,
    j: int,
    psi: OperadOperation,
) -> OperadOperation:
    """Witness that nesting order does not matter, or refuse.

    The operad axiom: substituting `psi` into `phi`'s slot `j` and the result
    into `theta`'s slot `i` must equal substituting `phi` into `theta` first and
    then `psi` into the slot `phi` now occupies -- which has shifted to
    ``i + j``, because `phi`'s inputs were spliced in ahead of it.

    The witness is the composite itself. Returning it rather than a boolean means
    a caller that wants the proof gets the object, and a caller that wants the
    verdict can still ask.
    """
    inner = substitute(phi, j, psi)
    left = substitute(theta, i, inner)

    outer = substitute(theta, i, phi)
    right = substitute(outer, i + j, psi)

    if left.source_colours != right.source_colours:
        raise SubstitutionError(
            "ASSOCIATIVITY_VIOLATED",
            f"nesting order changed the composite's inputs: "
            f"{left.source_colours} vs {right.source_colours}",
        )
    if left.target_colour != right.target_colour:
        raise SubstitutionError(
            "ASSOCIATIVITY_VIOLATED",
            f"nesting order changed the composite's output: "
            f"{left.target_colour} vs {right.target_colour}",
        )
    return left



def admissible_substitutions(
    operations: tuple[OperadOperation, ...],
) -> tuple[tuple[str, int, str], ...]:
    """Every (theta, slot, phi) the garden admits."""
    return tuple(
        (theta.name, index, phi.name)
        for theta in operations
        for index in range(theta.arity)
        for phi in operations
        if phi.target_colour == theta.source_colours[index]
    )


__all__ = [
    "OPERAD_COLOURS",
    "OperadOperation",
    "SubstitutionError",
    "admissible_substitutions",
    "associativity_witness",
    "is_admissible",
    "substitute",
]
