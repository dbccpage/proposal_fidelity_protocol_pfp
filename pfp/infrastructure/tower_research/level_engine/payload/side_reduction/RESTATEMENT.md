# Restatement: `side_reduction`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A joined row on a frame of two near slots and two far slots has size one.
Its one-side reduction is the near table `R[i][j] = sum over far slots k of
s[i, k] times the mirror of s[j, k]`. A claimed reduction must have trace
exactly one, be self-mirrored with nonnegative diagonal and determinant, and
equal the recomputed reduction.

## Refused case

A reduction that changes the trace, such as `[[1/4, 0], [0, 1/2]]` for a row
of size one.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| near, far, val, joint | supplied object-language datum | the joined row |
| reduced | supplied object-language datum | the claimed reduction |
| joint_given, one_joint, reduced_given, one_reduced | derived definition | relational requirements over the claim |
| unit_size, trace_one, nonnegative, reduced_exact | derived definition | value clauses, decided over exact values |
| sums of products of exact pairs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The declared class is two by two joined frames and
rows (not mixtures of rows). The reduction's nonnegativity is decided from
its diagonal and determinant, which suffices for two by two tables.
