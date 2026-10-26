# Restatement: `ordered_splits`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A row of size one meets two complete splits, one after the other. The weight
of first outcome `p` then second outcome `q` is the size of the second
table times the first table times the row: the row is changed by the first
split before the second acts. The weights of `q` given `p` are that row of
weights divided by the weight of `p` alone, and a first outcome of weight
zero has no conditional weights: zero is never divided through. The weights
in the other order are claimed and recomputed too.

## Refused case

The products of the two separate weights claimed as the joint weights: for
splits that do not commute they match neither order.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| bit, val, entry | supplied object-language datum | the index, the exact values and the row |
| first, second | supplied object-language datum | the two splits |
| weight, given, back | supplied object-language datum | the claimed joint, conditional and reversed weights |
| entries_given and the ten other relational clauses | derived definition | relational requirements over the claim |
| unit_size, splits_valid, sequential_exact, conditionals_exact, reverse_exact | derived definition | value clauses, decided over exact values |
| products of tables of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The declared class is two-slot frames with two-member
splits.
