# Restatement: `far_blind`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A joined row of size one sits on a frame of two near slots and two far
slots. The near factor has one split, and each far choice has its own split
of the far factor; every split is a complete family of self-mirrored
idempotent tables. The weight of near outcome `p` and far outcome `q` under
far choice `y` is the size of the near table for `p` times the row times the
transposed far table for `q`, the row read as a near-by-far table. A claimed
table of weights must be exactly that, and its near weights, summed over
the far outcomes, must not depend on the far choice.

## Refused case

A claimed table whose near weights move with the far choice, with no
selection of far outcomes declared.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| bit, val | supplied object-language datum | the two-element index and the exact values |
| joint, near, far | supplied object-language datum | the row and the splits |
| weight | supplied object-language datum | the claimed table |
| joint_given, one_joint, near_given, one_near, far_given, one_far, weights_given, one_weight | derived definition | relational requirements over the claim |
| splits_valid, far_choice_blind, table_exact | derived definition | value clauses, decided over exact values |
| products of tables of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Selections of far outcomes are not in the declared
class.
