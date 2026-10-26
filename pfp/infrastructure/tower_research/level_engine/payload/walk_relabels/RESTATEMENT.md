# Restatement: `walk_relabels`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge, answered by replaying
research-tree evidence. The trees `research/sign_slice` and
`research/convention_price` are re-run from the pinned clone, read only; they
are not sealed, and they are admitted for a replay by the author's ruling of
2026-09-25. Nothing here is attributed to the seed.

## Obligation

Arrows between objects each carry a transport, a permutation of one finite
set of labels. A walk's composite is its arrows' transports taken in walk
order, and consecutive arrows of the walk meet. A change of labels, one
permutation at every object, moves each arrow's transport at both of its
ends: undone at its source, applied at its target. The walk's composite then
moves the same way at the walk's first and last objects.

The presentation is the trees' census member on the square at occupancy
three: four objects, eight arrows, six labels (the rank orderings), each
transport computed by sign_slice's mover family. The change is a
pointwise-shaped assignment of convention_price's relabel, and the changed
transports are that relabel's own output. The walk goes once around the
square from object 2.

## Refused case

convention_price's recorded first moving assignment: two maps placed at the
two ends of one arrow pair only. Read against the change it carries, each
object's map reaches that pair's end and not the other pair at the same
object, so a change is applied at one end of an arrow only. The tree's section predicate
finds that this assignment moves the member's class, while the pointwise
change keeps it.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| the member, its arrows and transports | supplied object-language datum | sign_slice's mover family, re-run from the pinned clone (research-tree evidence) |
| the four slot maps, the relabel and the conjugation law | supplied object-language datum | convention_price's code, re-run from the pinned clone |
| the recorded first moving assignment | supplied object-language datum | convention_price's committed receipt |
| the pointwise change, the walk, its composite and changed composite | derived definition | computed by the replay through the trees' code |
| walk_meets, composite_exact, both_ends, covariance | derived definition | clauses decided on each packet |

## Notes

The trees' Lean (the two-label parity laws, the re-presentation theorems) is
not cited; this replay rests on the trees' Python alone. The record books the
custody: the witness is research-tree evidence, not sealed.
