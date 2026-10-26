# Restatement: `boundary_chain`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed alternating boundary and its signless variant are
re-run from the pinned clone, read only; nothing here is attributed to the
seed.

## Obligation

For a complex whose cells are listed by degree, the declared maps between
consecutive degrees must chain: one map per degree above zero, each with one
row per cell of the lower degree and one column per cell of the higher. Each
composite of consecutive maps must be zero. Each map must be the signed
boundary of the cells, and every face of a cell must be a declared cell.

Here the complex is the filled tetrahedron on the points 0 to 3, with every
face, plus one side from 3 to 4 that bounds nothing. The maps are the sealed
alternating boundary.

## Refused case

A nonzero composite of consecutive maps is refused: the same cells with every
sign dropped (the sealed signless boundary) compose to a nonzero map.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed alternating and signless boundaries | supplied object-language datum | re-run from the pinned clone (`derivation.boundary_cancellation`) |
| the filled tetrahedron with a tail side | externally imposed challenge | the declared complex |
| cells_replayed, chained, composites_zero, boundary_replayed | derived definition | clauses decided on the replayed sealed facts |
| `BoundaryCancellation.d2_zero_unrestricted`, `d2_zero_facets`, `signless_countermodel` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The sign convention is declared in the sealed module, not derived. The tail
side bounds nothing, so a change to its own boundary coefficient leaves every
composite zero: only the boundary clause refuses it. The composites are
decided over exact rationals, where the signless composite is nonzero; over
the field of two elements it would vanish.
