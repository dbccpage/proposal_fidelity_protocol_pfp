# Restatement: `cell_faces`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A hosted two-dimensional cell lists three points, and every side of every cell
is present. A side lists two distinct points.

## Refused case

A two-dimensional cell given two elements is refused: sealed admission refuses
the arity.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| pt | supplied object-language datum | a sort |
| side | supplied object-language datum | a binary relation |
| cell | supplied object-language datum | a ternary relation |
| side_first, side_last, side_outer, side_ends | derived definition | closure requirements |
| side_distinct | derived definition | a denial requirement |

## Notes

Distinctness of a cell's points is carried by side_distinct: a repeated point
yields a degenerate side. A missing side is never added by a response; that
would edit the claim.
