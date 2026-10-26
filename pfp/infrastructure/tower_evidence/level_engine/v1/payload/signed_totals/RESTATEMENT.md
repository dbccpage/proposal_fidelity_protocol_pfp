# Restatement: `signed_totals`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite list of exact signed terms comes with a cancellation record: pairs
of terms that are exact opposites, and a rest. Every term is used exactly
once; each pair sums to exactly zero and is not zero; the rest is all of one
sign; and the claimed total is the exact sum.

## Refused case

The terms `2, -1, -1` with total `0` and no pairs: the total is zero, but the
rest has terms of both signs, so nothing has cancelled.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| term, val, weight | supplied object-language datum | the terms and their exact values |
| paired, rest, total | supplied object-language datum | the cancellation record and the claimed total |
| weights_given, one_weight, typed, pairs_typed, total_given, one_total | derived definition | relational requirements over the claim |
| partition, opposite_pairs, rest_one_sign, total_exact | derived definition | value clauses, decided over exact values |
| sums of exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. A zero total is never taken as a record by itself.
