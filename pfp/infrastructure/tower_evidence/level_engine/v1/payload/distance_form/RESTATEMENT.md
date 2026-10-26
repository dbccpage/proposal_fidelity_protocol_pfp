# Restatement: `distance_form`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A hosted finite point set declares a squared distance for every ordered pair of
its points; the form built from those squared distances is positive definite.
Incidence is checked before anything is computed from the values.

## Refused case

A form with a negative leading minor and a positive determinant is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| pt | supplied object-language datum | a sort |
| val | supplied object-language datum | value data, each decoded to an exact rational |
| sq | supplied object-language datum | a ternary relation: point, point, value |
| complete, symmetric, one_value, typed | derived definition | relational requirements |
| diagonal_zero, form_positive | deterministic computation | decided over decoded exact values |

## Notes

Answer type M. The sealed grammar does no arithmetic, so the two value clauses
are decided outside it and are hosted, not answered natively. Their Lean
certificates wait for the exact rational library in Lean; until it exists the
row is unresolved.
