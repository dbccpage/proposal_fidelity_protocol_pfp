# Restatement: `loop_products`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A hosted cell on five corners carries a squared length for each pair of
corners, and its form based at the first corner
(`G[i][j] = (d(0,i) + d(0,j) - d(i,j)) / 2`) has positive leading minors.
Quarter turns act on three axes (a fourth axis is fixed by every turn): each
turn sends every axis to one axis with a sign, and must be a rotation (its
four by four table is orthogonal with determinant one). A loop of turns
around a hinge (three corners) closes exactly when the ordered product of
its tables is the identity; a turn taken back is its transpose. A loop
declared closed must have the identity as its ordered product, and a loop
declared open must not.

## Refused case

A summary that forgets the order does not decide closure: the loop
`g, h, g back, h back` of two quarter turns sharing an axis has signed count
zero for each turn, yet its ordered product is not the identity, so
declaring it closed is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| corner, len, span, hinge | supplied object-language datum | the cell, its squared lengths and the hinge |
| axis, turn, image, flips | supplied object-language datum | the turns, as signed images of axes |
| single, bracket, single_shut, bracket_shut | supplied object-language datum | the loops and which are declared closed |
| a fourth axis fixed by every turn | externally imposed challenge | the declared class of turns |
| spans_typed, one_span, image_given, one_image, image_typed, flips_typed, hinge_typed, single_typed, loops_typed, shut_is_loop, single_shut_is_loop | derived definition | relational requirements over the claim |
| gram_positive, turns_rotate, ordered_closure, open_stays_open | derived definition | value clauses, decided over exact values |
| products, determinants and minors over exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The running product of a loop would be a witness of
arity three (step, axis, axis), but it needs more items than the three the
search may use, so it is computed, not searched. The value clauses are
decided outside the grammar; the kernel re-decides them for every fixture
whose relational clauses hold.
