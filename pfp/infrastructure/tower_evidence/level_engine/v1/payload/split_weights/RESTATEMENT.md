# Restatement: `split_weights`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A row of exact pairs has size one. A split of its frame is a family of
tables, each self-mirrored and idempotent, which sum to the unit table and
are pairwise orthogonal. The weight of each outcome of the split is the
size of its table applied to the row; every reported weight is recomputed
that way. The weight rule is the rule checked; it is not claimed to be
forced.

## Refused case

A reported weight that is not the size of its table applied to the row.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| slot, outcome, val, entry | supplied object-language datum | the frame and the row |
| split | supplied object-language datum | the split's tables |
| weight | supplied object-language datum | the reported weights |
| entries_given, one_entry, split_given, one_split, weights_given, one_weight | derived definition | relational requirements over the claim |
| unit_size, split_members, complete, weights_exact | derived definition | value clauses, decided over exact values |
| products and sizes of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The declared class is two-slot frames.
