# Restatement: `named_frames`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Several frames are declared, each a two by two table of exact pairs whose
columns are the frame's slots written in the standard frame; each table must
keep size. A row is given by its coordinates in one named frame. The
coordinates have size one, and the claimed row in the standard frame is the
named table times the coordinates.

## Refused case

Coordinates with no frame named: the same coordinates denote different rows
in different frames, so an unnamed frame leaves the row undetermined.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| frame, slot, val, cell | supplied object-language datum | the declared frames and their tables |
| named, coord, row | supplied object-language datum | the named frame, the coordinates and the claimed row |
| named_given, one_named, cells_given, one_cell, coords_given, one_coord, row_given, one_row | derived definition | relational requirements over the claim |
| frames_size_keeping, unit_coordinates, row_exact | derived definition | value clauses, decided over exact values |
| products of tables of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The declared class is two-slot frames over exact
pairs.
