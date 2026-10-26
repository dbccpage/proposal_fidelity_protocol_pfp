# Restatement: `dual_endpoints`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two finite endpoints each have a start, final states, and at most one move
per state, action (send or receive) and kind of message. A joint step fires
when one endpoint sends a kind and the other receives the same kind; both
move. Every joint state reachable from the two starts is decided: the two
never both wait only to receive, whatever one may send the other can
receive, every reachable joint state has a joint step or has both endpoints
final, and some reachable joint state has both final.

## Refused case

Two endpoints that both wait to receive at the start.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| here, there, kind | supplied object-language datum | the endpoints' states and the kinds of message |
| here_start, there_start, here_final, there_final | supplied object-language datum | starts and final states |
| here_send, here_receive, there_send, there_receive | supplied object-language datum | the moves |
| starts_given, one_here_start, one_there_start, one_here_send, one_here_receive, one_there_send, one_there_receive | derived definition | relational requirements over the claim |
| no_mutual_wait, sends_matched, never_stuck, end_reached | derived definition | clauses decided outside the grammar, over the reachable joint states |
| breadth-first exploration of a finite joint automaton | metatheory apparatus | the harness's check, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The exploration is finite: at most the product of the
two state counts.
