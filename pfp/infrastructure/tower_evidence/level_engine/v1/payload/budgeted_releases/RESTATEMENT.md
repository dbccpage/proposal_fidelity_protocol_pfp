# Restatement: `budgeted_releases`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Releases of a finite table are composed two ways, both decided exactly.
In sequence: no release costs more than the budget remaining before it, and
each claimed remainder is the budget less the costs so far. Jointly: a
reader holding every release can group the records by all the released
columns together, and every class of that joint partition must hold at
least `k` records.

## Refused case

A release that costs more than the budget remaining before it.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| column, record, token, cell | supplied object-language datum | the table |
| release, reveals, ledger, after | supplied object-language datum | the releases and their claimed remainders |
| budget, threshold and all costs and remainders | supplied object-language datum | exact values on elements |
| cells_total, one_cell, reveals_something, reveals_typed, ledger_given, one_ledger | derived definition | relational requirements over the claim |
| well_formed, within_budget, ledger_exact, joint_classes | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. No noise mechanism is modelled and no probabilistic
guarantee is claimed. The kernel re-decides both compositions over
ExactRat and the class counts.
