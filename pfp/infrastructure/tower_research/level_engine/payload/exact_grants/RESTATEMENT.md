# Restatement: `exact_grants`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Requests are decided against an independent grant table issued by one
declared authority. Every grant must be issued by that authority, and no
grant may name a pattern of resources or actions. A request is allowed
exactly when an authority grant names its party, resource and action
verbatim: an allowed request must have such a grant, and a denied one must
not.

## Refused case

A grant a party issues to itself, used to allow its own request: a
privilege escalation.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| party, resource, action, request | supplied object-language datum | the names and the requests |
| authority, grants, pattern | supplied object-language datum | the grant table, and which names are patterns |
| request_of, allow, deny | supplied object-language datum | each request and its claimed decision |
| authority_given, one_authority, issued_by_authority, exact_resource, exact_action, allow_granted, deny_ungranted, one_request, grants_typed, request_typed | derived definition | relational requirements over the claim |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Nothing is decided over values: every clause is
carried by derivability, and each is bitten by a fixture. The authority's
own identity is taken as given, not authenticated.
