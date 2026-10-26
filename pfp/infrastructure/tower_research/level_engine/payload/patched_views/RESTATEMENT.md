# Restatement: `patched_views`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

One table of fixed width, read as a set of rows, is changed by a delta of
insertions and deletions, and a view selects the rows holding a given token
in a given column. The old view must be the view of the old table; the
delta must apply (deletions were there, insertions were not, and no row is
both); every row removed between the two tables must be recorded as
deleted; the old table less the deletions, with the insertions, must be the
new table; and the patched view must be the view recomputed on the new
table, never the producer's patch arithmetic.

## Refused case

A nonempty deletion omitted from the delta.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| column, token, row, holds | supplied object-language datum | the rows and their cells |
| old, new, inserted, deleted | supplied object-language datum | the two tables and the delta |
| old_view, patched, view_on, view_is | supplied object-language datum | the view and its two claimed results |
| view_given, one_view_column, one_view_token, cells_total, one_cell, old_view_complete, old_view_within, old_view_selected, deleted_were_there, inserted_were_not, delta_disjoint, inserted_arrive, patched_complete, patched_within, patched_selected | derived definition | relational requirements over the claim |
| rows_distinct, deletions_recorded, delta_exact | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Both views are carried by derivability: a view is a
closure over the selection. What needs "not in" (the omitted deletion and
the exact delta) is decided outside the grammar and re-decided by the
kernel.
