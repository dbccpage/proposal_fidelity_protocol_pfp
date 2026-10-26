# Restatement: `weight_slopes`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A finite family of outcome weights is given, each a polynomial in k
parameters with exact rational coefficients, written on a declared list of
terms (each term a product of powers of the parameters, no two alike). The
weights sum to one identically, and at a declared rational point every
weight is positive. A declared information table, k by k, has no direction
of negative value: it is symmetric and every principal minor is
nonnegative. It is exactly the recomputed table: the sum over outcomes of
the slope along one parameter times the slope along the other, over the
weight, at the point, with exact polynomial slopes.

## Refused case

A declared table with a direction of negative value.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| outcome, parameter, term, number | supplied object-language datum | the family's outcomes, parameters, terms and exact values |
| power | supplied object-language datum | each term's power of each parameter |
| weight | supplied object-language datum | each outcome's coefficient on each term |
| at | supplied object-language datum | the point |
| declared | supplied object-language datum | the declared information table |
| powers_given, one_power, powers_typed, coefficients_given, one_coefficient, coefficients_typed, point_given, one_point, point_typed, table_given, one_table_entry, table_typed | derived definition | relational requirements over the claim |
| terms_well_formed, weights_sum_to_one, positive_at_point, no_negative_direction, table_recomputed | derived definition | value clauses, decided over exact values |
| exact polynomial slopes, values at a point, determinants of principal minors | metatheory apparatus | the harness's exact arithmetic |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The positive has three outcomes in two parameters,
first times second, first less first times second, and one less first, at
the point (1/2, 1/3); the recomputed table is 4 and 9/4 on the diagonal and
0 off it (15 elements). The recomputed table of a family positive at the
point never has a negative direction, so a declared table with one is also
refused as not recomputed.
