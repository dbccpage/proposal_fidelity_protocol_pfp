# Restatement: `grounded_traces`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A trace of events by several agents must have parent links that form no
cycle, and its evidence links must resolve. Every parent must be an event
of the trace; every event with no parent must carry evidence, its base
witness; every evidence link must name a witness; and every witness's
stamp must be the digest of its content.

## Refused case

A circular dependency without base witness: events that depend on each
other in a cycle, with nothing outside the cycle to rest on.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| event | supplied object-language datum | the trace's events, in declared order |
| agent and its text | supplied object-language datum | the agent that made an event |
| witness and its text | supplied object-language datum | a witness's content |
| stamp and its digest | supplied object-language datum | a witness's claimed digest, an exact 32-byte value |
| by, parent, cites, stamped | supplied object-language datum | who made each event, its parents, its evidence links, each witness's stamp |
| descends | supplied object-language datum | the claimed order: which events each event depends on, directly or not |
| acyclic, parents_known, descends_from_parents, descends_composed, evidence_resolves, agent_given, one_agent, by_typed, stamp_given, one_stamp, stamped_typed | derived definition | relational requirements over the claim |
| roots_grounded, stamps_recomputed | derived definition | clauses decided outside the grammar |
| SHA-256 of a witness's content | metatheory apparatus | a declared convention, computed outside the kernel |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the trace is a hosted
claim, and its circular dependency is refused natively. Acyclicity is
decided by derivability, not by a count or a search outside the grammar:
the claimed order must hold of every parent link (`descends_from_parents`)
and be closed under composition (`descends_composed`), and no event may
descend from itself (`acyclic`). A trace with a cycle has no such order,
whatever order is claimed, since composing around the cycle forces an event
to descend from itself; a trace without one always has one, its parent
links' own composition closure. So the claimed order is a certificate the
engine checks, never a verdict it trusts. By ruling D4 the level's checker
is apparatus, so this record counts in A, never in C.
