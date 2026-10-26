# Restatement: `isolated_roots`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A rational polynomial and a rational interval name one root when the
interval isolates exactly one. The certificate is the remainder chain: the
polynomial, its derivative, then each negated remainder of the two before
it. Its last member must be constant (no repeated root), the polynomial
must not vanish at either end, and the drop in sign changes of the chain
from the lower end to the upper end must be exactly one. The claimed value
at each end must be the exact value there.

## Refused case

An interval that holds two roots.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| coef, end, claimed and their values | supplied object-language datum | the polynomial, the interval, the claimed end values |
| at | supplied object-language datum | which claimed value belongs to which end |
| claim_given, one_claim, at_typed | derived definition | relational requirements over the claim |
| well_formed, squarefree, ends_not_roots, isolating, values_exact | derived definition | clauses decided outside the grammar |
| the remainder chain | metatheory apparatus | the harness's certificate, recomputed by the kernel |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The chain is a finite family, recomputed and read at
both ends by the kernel over ExactRat. That the count of sign changes
counts roots is the chain's classical reading; the kernel certifies the
count, not that reading.
