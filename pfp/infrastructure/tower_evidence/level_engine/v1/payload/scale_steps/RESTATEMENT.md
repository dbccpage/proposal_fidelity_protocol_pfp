# Restatement: `scale_steps`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

An exact reading is given on the points of a fine scale. Each coarsening
step maps every point of one scale to a block of the next, and the reading
there is the block average. The error of a map is the largest distance
between a reading and the coarse reading of its image. Each step claims an
error bound, which must not be below its error. A jump across scales
declares its map, which must be the composite of the steps between, and a
loss bound, which must not be below its error and must not exceed the sum
of the bounds of the steps it composes.

## Refused case

A jump across scales given with no loss bound.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| point, first_block, second_block, val, reads | supplied object-language datum | the scales and the fine reading |
| first, second, first_bound, second_bound | supplied object-language datum | the steps and their bounds |
| near_jump, far_jump, near_jump_bound, far_jump_bound | supplied object-language datum | the jumps and their bounds |
| reads_given and the eleven other relational clauses | derived definition | relational requirements over the claim |
| composite_maps, bounds_hold, bounds_composed | derived definition | value clauses, decided over exact values |
| block averages and largest distances | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Block averaging is the coarse reading and the largest
distance is the error, as declared.
