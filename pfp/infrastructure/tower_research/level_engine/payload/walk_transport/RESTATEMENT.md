# Restatement: `walk_transport`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Links between corners each carry a transport, a permutation of one finite
set of labels. A walk's composite is its links' transports taken in walk
order, and consecutive links of the walk meet. A change of labels at every
corner moves each link's transport at both of its ends: undone at its first
end, applied at its second. The walk's composite then moves the same way at
the walk's first and last corners.

## Refused case

A change of labels applied at one end of a link only.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| label, corner, link, from, to, moves | supplied object-language datum | the links and their transports |
| stride, walks, composite | supplied object-language datum | the walk and its claimed composite |
| regauge, moved, recomposite | supplied object-language datum | the change of labels and the claimed changed transports and composite |
| ends_given and the other twelve relational clauses | derived definition | relational requirements over the claim |
| walk_meets, composite_exact, both_ends, covariance | derived definition | clauses decided outside the grammar |
| composition of finite maps | metatheory apparatus | the harness's check, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Whether a global section exists is not decided.
