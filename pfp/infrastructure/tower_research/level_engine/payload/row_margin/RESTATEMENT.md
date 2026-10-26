# Restatement: `row_margin`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The tree `research/p208b_contextuality_nonlocality`
is re-run from the pinned clone, read only; it is not sealed, and it is
admitted for a replay by the author's ruling of 2026-09-25. Nothing here is
attributed to the seed.

## Obligation

Two parties each hold two rows of unit size, one per choice. The entry for
near choice x and far choice y is the dot product of near row x and far
row y. The total is E00 + E01 + E10 - E11. The bound is the largest total
over all sixteen fixed answer tables (each party answers +1 or -1 to each of
its choices, and the entry is the product of the answers); weighted mixtures
of those tables cannot pass it. Check that every row has size 1, that the
claimed entries are the dot products, that the claimed total is recomputed
from those entries and never read from a label, that the claimed bound is
the enumerated one, and that the claimed margin is the total less the bound.

## Positive

The tree's four declared unit rows in Q^2: near (1, 0) and (0, 1), far
(4/5, 3/5) and (4/5, -3/5). Their entries are 4/5, 4/5, 3/5 and -3/5; the
tree's total is 14/5; the tree's sixteen fixed tables give the bound 2; the
margin is 4/5.

## Refused case

A claim labelled with the total 14/5 whose rows are the tree's first fixed
answer table (every answer +1), written as the one-coordinate rows (1, 0):
its entries are all 1 and total 2, so the label is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the tree's four unit rows, its dot product, its table of weights and the total it reads from it | supplied object-language datum | re-run from the pinned clone (`research/p208b_contextuality_nonlocality`, research-tree evidence) |
| the tree's sixteen fixed answer tables and their totals | supplied object-language datum | the tree's own enumeration |
| a fixed answer table written as one-coordinate rows | derived definition | the answer to choice x is the row (answer, 0), so each entry is the product of the answers |
| unit_rows, entries_replayed, total_replayed, bound_replayed, excess_replayed | derived definition | clauses decided by the tree's code on each packet |

## Notes

No irrational ceiling on the total is computed or claimed. The tree's Lean enters the four entries as literals and
proves that 2 is less than the total and the total less than 4; this replay
cites none of it and rests on the tree's Python alone. The record books the
custody: the witness is research-tree evidence, not sealed.
