# Restatement: `joint_rank`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A joined row on a frame of two near slots and two far slots is read as the
two by two table whose entry at near slot `i` and far slot `j` is the row's
entry there. The row has size exactly one, and a claimed rank must equal the
rank of that table, computed by exact elimination over pairs.

## Refused case

A row that is the product of a near row and a far row, such as
`(3/5, 0, 4/5, 0)`, has a table of rank one; it cannot claim rank two.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| near, far, val, entry | supplied object-language datum | the joined frame, the exact values and the row's entries |
| rank | supplied object-language datum | the claimed rank |
| entries_given, one_entry, typed, rank_given, one_rank | derived definition | relational requirements over the claim |
| unit_size, rank_exact | derived definition | value clauses, decided over exact values |
| elimination and determinants over exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The declared class is two by two joined frames. The
kernel computes the rank from the determinant and the entries, an
independent route from the engine's elimination; both must agree on every
evaluated fixture.
