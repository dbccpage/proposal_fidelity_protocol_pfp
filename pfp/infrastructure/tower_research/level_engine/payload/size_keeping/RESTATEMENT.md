# Restatement: `size_keeping`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A square table of exact pairs keeps size exactly when its mirrored transpose
times the table is the unit table, and the table times its mirrored
transpose is too. This is decided on the whole table, never by sampling
rows. Each carried test row comes with a claimed image, which must be the
table times the row.

## Refused case

The shear `[[1, 1], [0, 1]]` does not keep size, although it keeps the size
of the row `(1, 0)`.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| slot, probe, val | supplied object-language datum | the frame, the test rows and the exact values |
| cell, test, image | supplied object-language datum | the table, each test row and its claimed image |
| cells_given, one_cell, tests_given, one_test, images_given, one_image, typed | derived definition | relational requirements over the claim |
| size_keeping, image_exact | derived definition | value clauses, decided over exact values |
| products of tables of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The table is static data: it is not a step of the
sealed grammar, and nothing here claims it is one.
