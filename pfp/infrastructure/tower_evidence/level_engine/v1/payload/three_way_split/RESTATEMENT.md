# Restatement: `three_way_split`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A hosted complex has points, sides with a tail and a head, and cells with a
signed rim. A load on the sides (1 on each marked side, 0 elsewhere) splits
exactly into three parts: a difference of levels on the points (`d0 p`), a
balanced part `h`, and a rim part (`d1^T q`) from weights on the cells. The
parts are carried as exact values on the elements themselves, and the two
recomputed parts are computed from the complex's own incidence, never read:

- every rim is a closed walk (`d1 d0 = 0`), or no split is defined;
- the balanced part is balanced at every point and around every rim
  (`d0^T h = 0`, `d1 h = 0`);
- the three parts rebuild the load (`d0 p + h + d1^T q` is the load).

The three parts are then pairwise orthogonal.

## Refused case

A split that states no incidence (the whole load claimed as one part, with
no table of tails, heads or rims) is refused: nothing can be recomputed.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| point, side, cell, tail, head | supplied object-language datum | the complex and its sides' ends |
| rim_with, rim_against | supplied object-language datum | each cell's rim, with the sign of each side |
| marked | supplied object-language datum | the load: 1 on each marked side |
| exact values on elements | supplied object-language datum | a point's level, a side's balanced part, a cell's rim weight |
| tail_given, one_tail, head_given, one_head, tail_typed, head_typed, rim_typed, rim_against_typed, marked_typed | derived definition | relational requirements over the claim |
| rims_close, balanced, rebuilds | derived definition | value clauses, decided over exact values |
| sums over exact rationals | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The value clauses are decided outside the grammar
(hosted, not native); the kernel re-decides them for every fixture whose
relational clauses hold.
