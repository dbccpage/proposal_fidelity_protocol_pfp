# Restatement: `refined_sums`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A polynomial integrand on `[0, 1]` has an exact integral `I`. At depth `k`
the mesh has `2^k` equal cells, and `S_k` is the left-end sum. The claimed
estimate `|S_k - I| <= C 2^-k` must hold at every depth `k >= k0`, decided
for every depth, not at the listed ones. The left sum is a polynomial in
the width `h` of degree at most the integrand's; interpolating it at
`h = 1/N`, `N = 1, ..., d + 1`, gives the error polynomial `g` with
`S(h) = I + h g(h)`, and the claim is `|g(2^-k)| <= C`. Each listed sum must
be the exact left sum.

## Refused case

Convergence inferred from listed meshes, with no constant.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| coef, constant, index, sum and their values | supplied object-language datum | the integrand, the constant, depths and listed sums |
| starts, at | supplied object-language datum | the start depth and where each listed sum sits |
| start_given, one_start, at_given, one_at | derived definition | relational requirements over the claim |
| well_formed, rated, sums_exact, every_depth | derived definition | clauses decided outside the grammar |
| interpolation of the left sums | metatheory apparatus | the reduction to the error polynomial |
| `ExactRat.QN.halving_bound` | proved theorem | the bound at every `1 / 2^k`, `k >= k0`, by induction |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The kernel re-decides the listed sums, checks the
error polynomial against the left sums at its interpolation nodes, and
proves the bound on it at every depth `k >= k0` (or refutes it at a
witness depth). That the left sum is a polynomial in the width, of degree
at most the integrand's, is the reduction the checker also uses; it is
stated, not proved here. The positive is `x^2` with `C = 1/2` from depth 1:
the error polynomial is `-1/2 + h/6`.
