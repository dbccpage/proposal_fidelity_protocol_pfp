# Restatement: `scoped_release`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite release manifest must cover every claim in its scope: each claim
is linked to a declared test, or held as an unresolved obligation of one of
four closed kinds (open, conjecture, blocked, out of scope). Every link and
every obligation names a claim in scope and a declared test. The declared
frontier must be exactly the claims with no test, so a release cannot call
itself complete while an obligation is open. The release may not certify
itself or declare an authority effect.

## Refused case

A release that declares its own final certification.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| claim, test, kind, release | supplied object-language datum | the manifest's names |
| a kind's place in the closed list | supplied object-language datum | an exact value on the element |
| evidence, held, frontier, self_certified, grants_authority | supplied object-language datum | the manifest's rows |
| not_self_certified, no_authority, evidence_resolves, held_in_scope, frontier_in_scope, frontier_untested | derived definition | relational requirements over the claim |
| covered, types_closed, frontier_complete | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the release is a
hosted claim whose refusal of self-certification is carried by
derivability (a forbidden row), not by a flag. By ruling D4 the level's
checker is apparatus, so this record counts in A, never in C.
