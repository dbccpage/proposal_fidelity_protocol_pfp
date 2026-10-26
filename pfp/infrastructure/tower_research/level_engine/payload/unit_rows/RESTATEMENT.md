# Restatement: `unit_rows`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A row of exact pairs is given in a declared frame, one entry per slot. The
row is a unit row exactly when its size, the sum over its entries `a + b i`
of `a * a + b * b`, is exactly one.

## Refused case

The row `(1, i)` does not have size one: its size is two. (Squaring each
entry without its mirror would give zero, which is not a size.)

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| slot, val, entry | supplied object-language datum | the frame, the exact values and the row's entries |
| entries_given, one_entry, typed | derived definition | relational requirements over the claim |
| unit_size | derived definition | the value clause, decided over exact values |
| sizes of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The value clause is decided outside the grammar; the
kernel re-decides it for every fixture whose relational clauses hold.
