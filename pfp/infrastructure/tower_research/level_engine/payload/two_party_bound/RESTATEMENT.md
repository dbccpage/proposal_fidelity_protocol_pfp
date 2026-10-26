# Restatement: `two_party_bound`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two parties each have two settings; every setting is a real row of size
one, and outcomes are plus or minus one. The correlation of a near setting
with a far setting is the exact dot product of their rows. The total
`E00 + E01 + E10 - E11` is computed from those correlations; the local bound
is the largest total over the sixteen assignments of plus and minus one to
the four settings; and the claimed margin is the total less that bound.
Every claimed number is recomputed.

## Refused case

A total written as a label: correlations that total 2, claimed to total
14/5.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| setting, slot, val, near, far | supplied object-language datum | the setting rows |
| corr, total, bound, excess | supplied object-language datum | the claims |
| near_given, one_near, far_given, one_far, corr_given, one_corr, total_given, bound_given, excess_given | derived definition | relational requirements over the claim |
| unit_rows, correlations_exact, total_exact, bound_exact, excess_exact | derived definition | value clauses, decided over exact values |
| dot products and a maximum over sixteen assignments | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. No ceiling on the total beyond the local bound is
computed or claimed.
