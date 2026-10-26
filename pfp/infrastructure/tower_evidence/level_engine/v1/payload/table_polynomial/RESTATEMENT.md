# Restatement: `table_polynomial`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A record computes the exact polynomial `det(xI - A)` of a hosted finite
square table `A` of exact entries, and keeps its scope to the table. The
polynomial is computed from the table, never read from the record: the
record's declared coefficients must equal it. Every rational root the record
claims must be a root of it; every interval `[lo, hi]` it claims holds a root
must have `lo < hi` and a sign change of the polynomial across it. The only
supported scope is the table itself.

## Refused case

A root that is irrational, rounded to a rational and claimed as a root, is
refused: the table `[[1, 1], [1, 0]]` gives `x^2 - x - 1`, which has no
rational root, and the claim `809/500` leaves the value `-19/250000`.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| slot, num, entry | supplied object-language datum | the evidence: a square table of exact entries |
| record, coef | supplied object-language datum | the record and its declared coefficients by power |
| root, fence | supplied object-language datum | claimed roots and claimed intervals |
| reach, in_scope | supplied object-language datum | the record's scope; the first element is the table itself |
| entries_complete, one_entry, entries_typed, one_coef, coef_typed, scope_given, one_scope | derived definition | relational requirements over the claim |
| scope_derived | derived definition | the fence requirement, fixed by the evidence type |
| polynomial, roots_vanish, fences_change_sign | derived definition | value clauses, decided over exact values |
| Faddeev-LeVerrier recurrence over exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The value clauses are decided outside the grammar
(hosted, not native); the kernel recomputes the polynomial and re-decides
each of them for every fixture whose relational clauses hold.
