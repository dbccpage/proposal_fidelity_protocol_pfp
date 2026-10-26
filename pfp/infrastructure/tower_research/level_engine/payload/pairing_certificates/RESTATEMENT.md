# Restatement: `pairing_certificates`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The trees `research/natural_sections` and
`research/fresh_characters` are re-run from the pinned clone, read only; they
are not sealed, and they are admitted for a replay by the author's ruling of
2026-09-25. Nothing here is attributed to the seed.

## Obligation

A finite list of exact signed terms comes with a cancellation certificate:
its indices split into exact-opposite pairs and a rest. Check that the pairs
and the rest use every index exactly once, that each pair's terms are
nonzero and sum to 0, that the rest holds terms of one sign only (its
nonzero terms are the residual support), and that the claimed total is the
exact sum of the terms.

The positive is natural_sections' pinned witness family (1, 2, -1, -2, 1, 1):
pairs of magnitudes 1 and 2, the rest (1, 1), total 2.

## Refused case

A claimed zero with unpaired signed terms: fresh_characters' smallest
refusing row, the totals of its hit carrier at part count 3, (2, -1, -1),
claimed to total 0 with nothing paired. Its rest holds 2 beside -1. Both
trees' criteria (one sign dominating at every magnitude) and their
brute-force searches find no certificate for it at all.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the pinned witness family and the certificate criteria | supplied object-language datum | natural_sections' sign-repair module, re-run from the pinned clone (research-tree evidence) |
| the least uncertified family with a positive total | supplied object-language datum | natural_sections' committed receipt |
| the refusing row and a certified zero row | supplied object-language datum | fresh_characters' code, and its committed receipt |
| the certificate's index pairs and rest | derived definition | the tree's decomposition placed on indices first-come by the replay |
| partition, opposite_pairs, single_signed_rest, total | derived definition | clauses decided on each packet |

## Notes

The trees' Lean (the criterion theorem, the wedge, the witness certificate)
is not cited; this replay rests on the trees' Python alone. The record books
the custody: the witness is research-tree evidence, not sealed.
