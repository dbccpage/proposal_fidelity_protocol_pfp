# Restatement: `mirror_pairs`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

An exact pair `(a, b)` of rationals stands for `a + b i`, with `i i = -1`. A
record states two pairs, their sum, their product and the mirror of each,
and every stated result is recomputed: the sum is `(a + c, b + d)`, the
product `(ac - bd, ad + bc)` and the mirror of `(a, b)` is `(a, -b)`.

## Refused case

A product taken slot by slot, `(ac, bd)`, as if the pair were two untyped
numbers, is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| val | supplied object-language datum | the exact values |
| left, right, sum, product, left_mirror, right_mirror | supplied object-language datum | the stated pairs |
| `i i = -1` | externally imposed challenge | the declared rule of the product |
| `*_given`, `one_*` | derived definition | relational requirements over the claim |
| sum_exact, product_exact, mirrors_exact | derived definition | value clauses, decided over exact values |
| sums and products of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. A decimal scalar never enters: exact intake refuses it
before anything is hosted. The value clauses are decided outside the
grammar; the kernel re-decides them for every fixture whose relational
clauses hold.
