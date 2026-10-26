# Restatement: `ordered_log`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

One merged, append-only log holds finitely many events, each at a node with
a scalar clock and a list of parents. Every parent must be an event of the
log, appended before the event that names it; an event's clock must exceed
each parent's clock; and at each node the clocks must strictly increase in
log order.

## Refused case

An event that names a parent appended after it.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| entry, node, logged, at, parent | supplied object-language datum | the log, in declared order, and its events |
| an entry's clock | supplied object-language datum | an exact value on the element |
| parents_logged, at_given, one_node, parent_typed | derived definition | relational requirements over the claim |
| well_formed, parents_earlier, clocks_rise, node_order | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. A parent missing from the log is refused natively
(a closure over the logged entries); the order clauses read positions and
clocks and are re-decided by the kernel.
