# Restatement: `composed_errors`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Errors from several sources are composed over a finite outcome space with
exact positive weights summing to one. The composed error is the pointwise
sum. Under the algebraic-sum rule the bound must cover the sum of the
sources' worst-case errors; under independence the sources must be pairwise
independent under the weights, decided from their joint law, and the
squared bound must cover the sum of their variances; under justified
dependence the squared bound must cover the variance of the composed error.
No root is taken.

## Refused case

Two correlated sources assumed independent.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| outcome and its weight | supplied object-language datum | exact positive rationals |
| source, cell and its error value | supplied object-language datum | one error per source and outcome |
| bound and its value | supplied object-language datum | an exact nonnegative rational |
| err, total, by_sum, by_independence, by_dependence | supplied object-language datum | the composition claim |
| errors_total, one_error, totals_given, one_total | derived definition | relational requirements over the claim |
| well_formed, independence_justified, sum_bound, variance_bound, composed_exact | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the composition is a
hosted table whose every source-outcome cell is required natively; the
independence refusal is decided exactly from the joint law. By ruling D4
the level's checker is apparatus, so this record counts in A, never in C.
