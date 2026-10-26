# Restatement: `face_walk_products`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The tree `research/natural_sections` is re-run from
the pinned clone, read only; it is not sealed, and it is admitted for a
replay by the author's ruling of 2026-09-25. Nothing here is attributed to
the seed.

## Obligation

Edges between objects each carry a transport, a permutation of one finite
set of labels. A face is a walk of steps, each an edge read along its
orientation or against it (then its transport is inverted), that ends where
it starts. Check that every step names a declared edge and direction, that
every face is closed, and that each claimed product is the face's
transports multiplied in step order.

Two of the tree's objects stand side by side on three labels:

- the chord square: four corners, five edges, and the two triangular faces
  0-1-3 and 0-3-2 of the tree's receipt, at the tree's separating
  assignment of edge values mod 3. The tree's edge equation carries a value
  along an edge by adding the edge value, so each edge's transport is that
  addition. The two face products add 1 and 2; the tree finds no corner
  values solving every edge, while the sum along the outer walk is 0;
- the tree's three-occupant run on the square of four sites: four
  occupations, four moves, each move's transport the permutation of sorted
  indices the tree computes, and the closed walk its receipt records, with
  the recorded product. Its moves do not commute: multiplied in the reverse
  order, the same links give another permutation.

## Refused case

An open walk offered as a face: the first face with its chord step dropped,
0-1-3, ending where it did not start. The chord carries 0 at this
assignment, so the claimed product still matches; closure alone refuses it.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the chord square, its faces, face sums and edge equation | supplied object-language datum | re-run from the pinned clone (`research/natural_sections`, research-tree evidence) |
| the separating assignment (1 on 1-3, 2 on 3-2, 0 elsewhere, mod 3) | supplied object-language datum | the tree's own test of the outer walk |
| the run's moves, transports, recorded closed walk and product | supplied object-language datum | the tree's code and committed receipt |
| each edge value as the addition it performs | derived definition | the replay's reading of the tree's edge equation |
| steps_declared, closed, product_exact | derived definition | clauses decided on each packet |

## Notes

The tree's Lean (the face criterion over any value group, the outer-walk
countermodel, the closed-walk criterion) is not cited; this replay rests on
the tree's Python alone. The record books the custody: the witness is
research-tree evidence, not sealed.
