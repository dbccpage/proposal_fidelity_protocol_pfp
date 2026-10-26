# Restatement: `face_products`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Links between corners each carry a transport: a permutation of one finite
set of labels. A face is a closed walk of steps, each reading a link forward
or, through the inverse transport, backward; consecutive steps meet and the
walk ends where it starts. A face's claimed product must be the product of
its step transports taken in walk order. With three or more labels the
product is not a function of the unordered set of links.

## Refused case

An open walk offered as a face: it has no product to claim.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| label, corner, link, from, to, moves | supplied object-language datum | the labels, the links and their transports |
| step, along, against | supplied object-language datum | the face's walk, in declared step order |
| product | supplied object-language datum | the claimed product |
| ends_given, one_from, one_to, moves_given, one_move, claim_given, one_claim | derived definition | relational requirements over the claim |
| links_permute, walk_closed, ordered_product | derived definition | clauses decided outside the grammar |
| composition of finite maps | metatheory apparatus | the harness's check, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. One face per claim.
