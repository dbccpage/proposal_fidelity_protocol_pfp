# Restatement: `table_roots`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A claimed polynomial and claimed roots are accepted only with the square
table they come from. The polynomial must be `det(xI - A)` of that table,
computed exactly, and each claimed root must be a root of it.

## Refused case

A root asserted with no table at all (the root 2 of `x^2 + 1`) is refused:
there is nothing for it to be a root of.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| slot, val, entry | supplied object-language datum | the table and its exact values |
| coef, root | supplied object-language datum | the claimed coefficients and roots |
| table_given, entries_complete, one_entry, entries_typed, one_coef, coef_typed | derived definition | relational requirements over the claim |
| polynomial, roots_vanish | derived definition | value clauses, decided over exact values (shared with the table polynomial level) |
| the Faddeev-LeVerrier recurrence over exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The polynomial and root clauses, and their Lean
definitions, are the table polynomial level's own; this level adds that a
claim with no table is refused before anything is computed.
