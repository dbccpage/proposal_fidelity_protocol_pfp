# Restatement: `weighted_update`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Hosted weights over alternatives are updated by observations, in their
declared order. The starting weights are nonnegative and sum to one; every
likelihood lies between zero and one. For each observation, the evidence is
the sum over alternatives of current weight times likelihood, and it must not
be zero. Each declared result must be the current weight times the
likelihood, divided by the evidence, recomputed exactly.

## Refused case

An observation whose evidence is zero (likelihood zero under every
alternative that still has weight) is refused: there is nothing to divide by.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| alt, obs, val | supplied object-language datum | alternatives, observations in order, exact values |
| prior, likely, after | supplied object-language datum | starting weights, likelihoods, declared results |
| prior_given, one_prior, likely_given, one_likely, after_given, one_after, typed | derived definition | relational requirements over the claim |
| prior_normal, likely_in_range, evidence_positive, results_exact | derived definition | value clauses, decided over exact values |
| products, sums and inverses over exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The value clauses are decided outside the grammar; the
kernel re-decides them for every fixture whose relational clauses hold.
