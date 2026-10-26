# Restatement: `stage_chain`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
sealed evidence. The sealed repository's own history is re-run from the
pinned clone, read only; nothing here is attributed to the seed.

## Obligation

A chain of stages, each a presentation (generators and equations between
them), with maps between stages, is checked on generators and on every
source equation: every map is defined on all of its source's generators and
lands on generators of its target; a source equation is sent to a
consequence of the target's equations; no map sends two generators its
source keeps apart to one class of its target; and a direct map agrees with
the composite through every intermediate stage.

Here the stages are the sealed possession reading's genesis history, replayed
up to each admission: a stage's generators are its admitted data, named by
their presentation tokens, and it states no equation. The maps are the
consecutive inclusions and the direct one from the first stage to the last.

## Refused case

A map that is injective on generators, into a stage that states an equation
between two of their images, is refused: it identifies data its source keeps
apart.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the sealed history of the possession reading | supplied object-language datum | re-run from the pinned clone (`derivation.engine`, `derivation.model`) |
| stages as presentations of admitted data | externally imposed challenge | the declared reading of a replayed regime as a presentation |
| stages_replayed, maps_total, keeps_equations, keeps_apart, coherent | derived definition | clauses decided on the replayed sealed stages |
| `Derivation.historyF_replays`, `PresentationDescent.faithful_descent_iff_round_trip_coherent`, `faithful_descent_to_coherent` | proved theorem | sealed Lean, cited from the pinned axiom report |

## Notes

The sealed stages state no equation, so on the positive the clause about
sending source equations to consequences holds with nothing to check. It is
still bitten: one stated equation in the middle stage, which the last stage
does not keep, is refused by it.
