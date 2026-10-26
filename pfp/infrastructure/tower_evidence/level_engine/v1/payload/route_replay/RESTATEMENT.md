# Restatement: `route_replay`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed alternating boundary is re-run from the pinned
clone, read only; nothing here is attributed to the seed.

## Obligation

Each case takes a route, and the route is replayed with its witness. An
exact route carries a potential that rebuilds the load. A route that is
closed but not exact carries a balanced witness that pairs with the load to
a nonzero number, which excludes every potential. An open route has a load
the cell table does not kill. Before any case, the two incidence tables must
compose to zero. A trace of full states (load and route) must repeat where it
declares a cycle; a route code alone certifies nothing.

Here the complex is two triangles on a shared side, the first filled and the
second hollow. Both incidence tables are the sealed alternating boundary of
the complex's sides and filled cells. The balanced witness of the closed
route is the sealed boundary of the hollow triangle.

## Refused case

A load called exact by its route code alone, with no potential, is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed alternating boundary | supplied object-language datum | re-run from the pinned clone (`derivation.boundary_cancellation`) |
| two triangles on a shared side, one filled | externally imposed challenge | the declared complex |
| the three loads and the trace | externally imposed challenge | one load per route; the trace returns to the first case |
| board_replayed, route_is_class, exact_replayed, dual_replayed, open_replayed, repeat_replayed | derived definition | clauses decided on the replayed sealed facts |
| `BoundaryCancellation.d2_zero_unrestricted`, `d2_zero_facets`, `PrimitivePassage.two_rule` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

That the hollow triangle's boundary is balanced is exactly the sealed
boundary-cancellation theorem. The trace's return to its first case is
declared, not derived: replay is deterministic, so the revisited state is
equal, and nothing here finds a cycle in a sealed history.
