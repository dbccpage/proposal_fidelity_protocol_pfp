# Restatement: `carried_reversal`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed transposition and collision are re-run from the
pinned clone, read only; nothing here is attributed to the seed.

## Obligation

A reversal of typed arrows is total, is an involution, reverses endpoints,
keeps every obstruction mark, and is contravariant on composites: whenever
`h` is the composite of `f` then `g`, the reversal of `h` is the composite of
the reversal of `g` then the reversal of `f`.

Here the arrows are the composition closure of the sealed symmetric datum on
the two-point carrier: every ordered pair of points, loops included. The
reversal of an arrow is the arrow of its transposed pair. An arrow carries an
obstruction when it collides under the carrier's identity map: it is a loop.

## Refused case

A reversal that reverses endpoints but drops an obstruction mark is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed two-point datums, transpose and collision | supplied object-language datum | re-run from the pinned clone (`derivation.primdiff`) |
| arrows as the composition closure of the symmetric datum | externally imposed challenge | the declared reading of the datum as typed arrows |
| a mark as collision under the identity map | externally imposed challenge | the declared reading of an obstruction |
| arrows_replayed, dagger_is_transpose, composites_replayed | derived definition | clauses decided on the replayed sealed facts |
| `PrimDiff.swap_carries_D2_to_D2rev`, `swap_auto_of_S2_not_of_D2`, `collision_transpose_invariant`, `swap_twice_restores_D2` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

On the directed datum alone the reversal is not an arrow: its closure is one
arrow, and that arrow's transposed pair is not in it. The sealed
`swap_auto_of_S2_not_of_D2` says the same thing for the carrier swap.
