# Restatement: `register_squares`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The tree `research/native_bridge` is re-run from the
pinned clone, read only; it is not sealed, and it is admitted for a replay by
the author's ruling of 2026-09-25. Nothing here is attributed to the seed.

## Obligation

Two finite systems are given, each with a total step and a total reading of
every state. A map sends the states of the first to states of the second, and
a map back may be given. Check that a map is given, and that it is a total map
into the other system's states. Then check on every state, not on one start
state only, that stepping and then mapping agrees with mapping and then
stepping, and that the reading of a state is the reading of its image. A claim
made both ways also needs the map back, its two squares, and both round trips
the identity.

The source system is the tree's toggle: states 0 and 1, and one event that
sends each to the other. The target system is the passage read on the states
the tree's budget register writes the toggle to. Its step at each state is the
budget write the register issues there, replayed by the tree's `preplay`. Its
reading is the tree's `core` of the state. The toggle is read by a constant
reading, the core reading of genesis. The claim is one way.

## Refused case

The two systems called equivalent with no map either way. A second refusal is
the tree's own negative: the toggle read by its own state. The register sends
both states to encodings that share the core of genesis, so a reading that
tells the two states apart is not kept.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the tree's budget register, passage replay and core | supplied object-language datum | re-run from the pinned clone (`research/native_bridge`, research-tree evidence) |
| the toggle on states 0 and 1 with one event | supplied object-language datum | the source system the tree's receipt runs through the register |
| the register's recorded squares, encodings and cores for the toggle | supplied object-language datum | the tree's receipt row, re-run and compared on every evaluation |
| the constant reading | derived definition | the core reading of genesis, which every budget encoding shares |
| mapped, map_total, target_native, step_square, sight_square, both_ways | derived definition | clauses decided on each packet, the squares through the tree's replay and core |

## Notes

The tree's Lean proves the general forms: the register commutes for every
numbered system, every budget encoding has the reading of genesis, and the
toggle read by its own state has no faithful reading-keeping translation.
This replay cites none of it and rests on the tree's Python alone. The record
books the custody: the witness is research-tree evidence, not sealed.
