# Restatement: `narrowing_handoffs`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Delegation is replayed in its declared order. The principal holds its
declared scope. A handoff may be made only by a holder, and only with a
subset of what the delegator holds at that moment, so an agent handing
itself scope can narrow it but never widen it. A recipient then holds
exactly what it was last handed, and every routed task must fall inside its
agent's final scope.

## Refused case

An agent that widens its own authority.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| agent, perm, principal, starts_with | supplied object-language datum | the principal and its scope |
| handoff, from, to, hands | supplied object-language datum | the handoffs, in declared order |
| task, routes | supplied object-language datum | the routed tasks |
| principal_given, one_principal, from_given, one_from, to_given, one_to, routes_typed | derived definition | relational requirements over the claim |
| no_expansion, rooted, tasks_in_scope | derived definition | clauses decided outside the grammar, over the replay |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the handoffs are hosted
events replayed in order, the admission discipline's shape. By ruling D4
the level's checker is apparatus, so this record counts in A, never in C.
