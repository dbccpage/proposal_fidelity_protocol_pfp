# Restatement: `outward_bounds`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Every quantity carries a two-end bound with exact ends. A straight-line
program of steps (add, subtract, multiply, divide) claims a result bound for
each step; later steps use the claimed bounds of earlier ones. Each claimed
bound must contain the exact result bound computed from its operands'
bounds, a divisor's bound must exclude zero, no bound may be empty, and each
claimed end must lie on a declared grid (its denominator divides the grid).
Rounding inward, or to the nearest grid point, fails containment.

## Refused case

An approximation with no bound: a step given no bound at all.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| quantity, val, bound | supplied object-language datum | the quantities and their bounds |
| add, sub, mul, div | supplied object-language datum | the steps |
| grid | supplied object-language datum | the declared grid |
| bounds_given, one_bound, grid_given, one_grid | derived definition | relational requirements over the claim |
| bounds_ordered, divisors_clear, enclosed, on_grid | derived definition | value clauses, decided over exact values |
| arithmetic of exact bounds | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. A decimal never enters: exact intake refuses it.
