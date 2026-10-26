# Restatement: `step_squares`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two finite systems each have a next state for every state and a sight
shown by every state. A typed map from the first system's states to the
second's must commute with both: the image of a state's next state is the
next state of its image, and a state and its image show the same sight.
This is checked on every state, never on a starting state only. A claim
that the systems match both ways needs a map back with the same squares,
and both round trips must be the identity.

## Refused case

Two systems claimed to match with no map at all.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| here, there, sight | supplied object-language datum | the two systems' states and the sights |
| here_step, there_step, here_sees, there_sees | supplied object-language datum | the systems |
| sends, returns | supplied object-language datum | the map and the map back |
| bond, both_ways | supplied object-language datum | the claim that the systems match both ways |
| here_steps and the other twenty clauses | derived definition | relational requirements over the claim |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Every clause is carried by derivability over the
hosted claim; nothing is decided over values, so the kernel has nothing to
re-decide. A commuting square through an injective numbering alone is not
enough: the sights must commute too.
