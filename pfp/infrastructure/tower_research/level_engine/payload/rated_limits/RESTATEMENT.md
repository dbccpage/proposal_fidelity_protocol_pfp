# Restatement: `rated_limits`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A rational sequence `a_n = P(n) / Q(n)` carries a claimed limit `L` and a
claimed rate `C / n`. The claim is quantified: for every integer `n >= n0`,
`Q(n) > 0` and `|a_n - L| <= C / n`, the hypothesis kept inside it. It is
decided for every such `n`, never on the listed samples: each side reduces
to a polynomial that must be nonnegative (or positive) at every integer from
`n0` on. Each declared modulus `(epsilon, N)` must follow from the rate
(`epsilon > 0`, `N >= n0`, `C <= epsilon N`), and each sample must be
exact.

## Refused case

A claim that rests on a finite table of samples, with no rate.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| top, bottom and their values | supplied object-language datum | the coefficients of `P` and `Q`, constant first |
| limit, rate, modulus, index, sample and their values | supplied object-language datum | the claim's constants and samples |
| starts, after, at | supplied object-language datum | where the claim starts, where each modulus holds, where each sample sits |
| start_given, one_start, after_given, one_after, at_given, one_at | derived definition | relational requirements over the claim |
| well_formed, rated, denominator_positive, bound_holds, modulus_ok, samples_exact | derived definition | clauses decided outside the grammar |
| the Cauchy bound and the scan below it | metatheory apparatus | the harness's exact decision for every `n` |
| `ExactRat.QN.nonneg_from`, `pos_from` | proved theorem | the kernel's claim for every `n >= n0`, by induction on forward differences |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The kernel proves a holding claim for every `n >= n0`
from its forward differences at `n0`, and refutes a failing one at a
witness; where no difference certificate exists at `n0`, the clause stays
computed. The positive `(n + 2) / (3n)` meets `1/3 + (2/3) / n` with
equality at every `n >= 1`.
