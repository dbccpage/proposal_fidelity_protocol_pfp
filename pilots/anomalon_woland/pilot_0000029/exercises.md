# Quiz 17: A cycle that a rational lift hides

Executable migration: [pilot_0000029](README.md), including all four exercises.

**Status:** worked finite exercises; model responses remain proposals.\
**AuthorityEffect:** None. **GenesisEffect:** None.\
**Response profile:** `quiz-packet-v1`; exact mathematics and bindings are declared outside the wire.

## Seed prompt

> Work over Z. Declare C2=Z, C1=Z, C0=Z, with d2=[2] and d1=[0].
> The target cycle is z=1. Decide whether d2*c=z has an integer witness.
> Then repeat over Q, recording exactly what changed. Do not import a geometric
> realization or authorize a carrier change from the algebraic answer.

## Puzzle 17.1 — Nilpotency is not exactness

**Answer:** `d1*d2=[0]`, so this is a chain complex. Every integer in C1 is a
cycle, but boundaries are the even integers. Hence `H1 = Z/2Z`, and `z=1`
represents its nonzero class. `d1*z=0` does not imply an integer preimage exists.

Suggested packet: `ans<chain_law<0>,cycle<closed>,integer_boundary<no>>`.

**Mutation:** a checker reports `exact` solely from `d1*d2=0`. Ask it for `c`:
`2c=1` has no integer solution, since its left side is even.

## Puzzle 17.2 — The tempting half

A candidate offers `c=1/2`.

**Answer:** over Q, `2*(1/2)=1`. Over the declared Z carrier, the candidate has
the wrong coefficient type. The rationally extended complex has `H1=0`, but that
does not erase the original integral torsion obstruction. Preserve the successful
Q calculation and the Z refusal as different scoped results.

Suggested packet: `ans<integer<refused>,rational<witness<half>>,scope_changed,ae0>`.

## Puzzle 17.3 — Minimum integral residual, with ties

Keep the original integer problem. Minimize `|1-2c|` over integers c.

**Answer:** the minimum is 1, attained at **both** `c=0` and `c=1`, with residuals
`+1` and `-1`. Every residual is odd, so zero is excluded and no smaller absolute
value exists. Averaging the two witnesses gives `1/2`, outside Z; averaging their
signed residuals gives zero without solving the original problem.

Suggested packet: `ans<min_abs<1>,minimizers<0,1>,zero<unattainable>>`.

**Mutation:** declare the mean of the two signed residuals to be a repair.
The absolute residual of either admitted witness is still 1.

## Puzzle 17.4 — Same edges, different chain group

Consider vertices 0,1,2 and oriented edges `(01,02,12)` with

```text
d1 = [[-1,-1,0],[1,0,-1],[0,1,1]]
z  = [1,-1,1]
```

First declare no 2-cell. Then independently declare an oriented face whose
boundary column is `d2=[1,-1,1]^T`.

**Answer:** in both cases `d1*z=0`. In the hollow triangle `C2=0`, so the
nonzero z is not a boundary and `H1` has rank 1. In the filled triangle `d2*1=z`
and `H1=0`. A clique-complex builder fills the triangle by policy. The glyph
edges alone do not decide whether the face is admitted.

## Grading and scope

Four puzzles, 0–3 points each: correct calculation, witness/counterexample, and
explicit coefficient or carrier declaration. Maximum 12. These are supplied
finite algebraic realizations, not Genesis-derived stage extensions.
