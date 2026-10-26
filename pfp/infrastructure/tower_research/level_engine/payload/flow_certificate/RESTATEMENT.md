# Restatement: `flow_certificate`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two halves, both replayed.

- A hosted table of arcs carries, on each arc, a positive weight `w`, a load
  `c` and a flow `y`, a level `s` on each node, and a declared price. The
  primal value at the levels is the sum over arcs of
  `w |c - (s(head) - s(tail))|`. The flow is feasible when it balances at
  every node (inflow equals outflow) and `|y| <= w` on every arc; its dual
  value is the sum of `c y`. The gap must be zero, and the declared price
  must be the dual value.
- A plain set, a pointed set with its base, and one spare point. The unit
  sends each plain point into the plain set with the spare point added; the
  counit sends the kept points and the spare point into the kept points. Both
  round trips are replayed pointwise: freely pointing and then collapsing
  returns every plain point, and forgetting and then pointing returns every
  kept point; the counit sends the spare point to the base.

## Refused case

A flow whose dual value equals the primal value but that does not balance at
every node is refused: a zero gap is not a certificate without feasibility.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| node, arc, val | supplied object-language datum | the hosted table of arcs and its exact values |
| weight, load, carry, level, price | supplied object-language datum | per-arc weight, load and flow; per-node level; the declared price |
| pt, plain, kept, spare, base | supplied object-language datum | the plain set, the pointed set, the spare point and the base |
| unit, counit | supplied object-language datum | the two declared maps |
| weighted, loaded, carried, leveled and their one_* companions | derived definition | relational requirements over the first half |
| left_round_trip, right_round_trip, pointed, one_unit, one_counit | derived definition | the round trips, relational over the second half |
| within_capacity, balanced, zero_gap, price_matches | derived definition | value clauses, decided over exact values |
| sums and absolute values over exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The round trips are decided by derivability; the value
clauses outside the grammar, and the kernel re-decides them for every
fixture whose relational clauses hold.
