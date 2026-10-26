# Restatement: `commuting_checks`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A word over finitely many sites has two parts, each one bit per site. Two
words exchange at a site when one has a first-part one and the other a
second-part one there; they commute when their exchange count is even. A set
of checks must commute pairwise. Each declared error is read against the
checks, one bit per check (the parity of its exchange count with that
check); the readings must be nonzero and pairwise distinct, and each claimed
reading must be the recomputed one.

## Refused case

Two checks that exchange once, a first-part one and a second-part one at the
same site, anticommute and are refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| site, check, error | supplied object-language datum | the sites and the words |
| check_x, check_z, error_x, error_z | supplied object-language datum | the words' ones, part by part |
| reads | supplied object-language datum | the claimed readings |
| check_x_typed, check_z_typed, error_x_typed, error_z_typed, reads_typed | derived definition | relational requirements over the claim |
| checks_commute, readings_distinct, readings_exact | derived definition | clauses decided outside the grammar (they count modulo two) |
| counting modulo two | metatheory apparatus | the harness's check, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. A hosted word has one bit per site by construction.
