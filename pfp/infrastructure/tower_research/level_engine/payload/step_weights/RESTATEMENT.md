# Restatement: `step_weights`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A hosted table gives an exact weight to every step from one state to another
(the step from a state to itself included). Every weight is nonnegative, and
the weights leaving each state sum to exactly one.

## Refused case

A row of weights summing to three halves is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| state, val, weight | supplied object-language datum | the states, the exact values and the weight of each step |
| complete, one_weight, typed | derived definition | relational requirements over the claim |
| nonnegative, rows_sum_to_one | derived definition | value clauses, decided over exact values |
| sums over exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The value clauses are decided outside the grammar; the
kernel re-decides them for every fixture whose relational clauses hold.
