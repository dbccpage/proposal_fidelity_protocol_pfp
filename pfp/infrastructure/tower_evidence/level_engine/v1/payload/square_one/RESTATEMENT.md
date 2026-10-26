# Restatement: `square_one`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A two by two table of exact pairs must have real eigenvalues (its trace and
determinant are real and its discriminant `tr^2 - 4 det` is not negative),
be self-mirrored, and square to the unit table. Its split is a family of
tables, one for each claimed eigenvalue: each is self-mirrored and
idempotent, they sum to the unit table and are pairwise orthogonal, and the
table is the sum of each eigenvalue times its split table.

## Refused case

The quarter turn `[[0, -1], [1, 0]]`: its discriminant is -4, so its
eigenvalues are off the real line.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| slot, outcome, val, cell | supplied object-language datum | the table |
| eigen, split | supplied object-language datum | the claimed eigenvalues and split |
| cells_given, one_cell, eigen_given, one_eigen, split_given, one_split | derived definition | relational requirements over the claim |
| real_split, self_mirrored, square_one, split_members, complete, spectral | derived definition | value clauses, decided over exact values |
| products of tables of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The table is static data, not a step of the sealed
grammar.
