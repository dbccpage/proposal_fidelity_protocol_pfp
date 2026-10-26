# Restatement: `edge_endpoints`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Every arc of a hosted directed graph names two present nodes, and the
protected pair stays separated.

## Refused case

An arc to an element that is not present is refused: sealed admission itself
refuses the hosting event.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| node | supplied object-language datum | a sort of the hosted claim |
| arc | supplied object-language datum | a binary relation of the hosted claim |
| protected pair | externally imposed challenge | a separation requirement, not an instance |
| endpoint_source, endpoint_target | derived definition | closure requirements over the claim |
| protect | externally imposed challenge | the sealed separation kind |

## Notes

Claim-only: the class of responses is empty apart from the empty
response, because the claim is frozen and no witness form is declared.
