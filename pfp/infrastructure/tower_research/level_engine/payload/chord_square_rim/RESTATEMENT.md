# Restatement: `chord_square_rim`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The tree `research/natural_sections` is re-run from
the pinned clone, read only; it is not sealed, and it is admitted for a
replay by the author's ruling of 2026-09-25. Nothing here is attributed to
the seed.

## Obligation

A finite two-dimensional complex has oriented edges and triangular faces.
Its two incidence tables are those of its cells: the edge table puts minus
one at an edge's first corner and one at its second, and the face table puts
one or minus one where a face's walk runs along or against an edge. The
claimed tables must be those tables and must compose to zero. The rim is
exactly the edges with one incident face, with their end corners, and the
cells off the rim are counted.

The complex is the tree's chord square: four corners, the sides 0-1, 1-3,
3-2 and 2-0 and the chord 0-3 in the tree's orientations, and the faces
0-1-3 and 0-3-2 named in its committed receipt. The edge rows are the
tree's edge equation (the value on an edge is the corner value at its
target minus that at its source), and the tree's search finds corner values
for every column. The face rows are the tree's face sums read on each
single-edge assignment, at each modulus it surveys. The rim is the set of
edges on which exactly one face sum is nonzero; it must be the tree's outer
walk, and the tree's own survey must find the outer walk's sum equal to the
two face sums added, on every assignment.

## Refused case

The chord declared on the rim. Both faces run along it, once each way, so it
cancels from the tree's outer walk.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the tree's oriented edges, face sums, edge equation and search, outer walk sum and survey | supplied object-language datum | re-run from the pinned clone (`research/natural_sections`, research-tree evidence) |
| the chord square, faces 0-1-3 and 0-3-2 | supplied object-language datum | the tree's own fixture, as its committed receipt names it |
| edge rows, face rows, rim corners, counts off the rim | derived definition | computed by the replay from the tree's objects |
| tree_cells, rows_compose, rows_replayed, rim_replayed, off_rim_counts | derived definition | clauses decided on each packet |

## Notes

The tree states its face sums over the integers modulo 2, 3 and 4; the
replay reads each row entry as minus one, zero or one. The tree's Lean works
over any group of edge values; this replay cites none of it and rests on the
tree's Python alone. The record books the custody: the witness is
research-tree evidence, not sealed.
