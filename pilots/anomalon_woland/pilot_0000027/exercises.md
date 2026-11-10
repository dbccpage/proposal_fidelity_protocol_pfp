# Quiz 19: Exact LP certificates and a nonunique optimum

**Status:** worked finite exercises; model responses remain proposals.\
**AuthorityEffect:** None. **GenesisEffect:** None.\
**Response profile:** `quiz-packet-v1`; exact mathematics and bindings are declared outside the wire.

## Seed prompt

> Maximize x+y over rational x,y with x>=0, y>=0,
> ub1: x+y<=2, ub2: x<=2, ub3: y<=2.
> Return a primal witness and nonnegative dual multipliers in row order
> (ub1,ub2,ub3). Check all original bounds. Separate optimality from uniqueness.

## Puzzle 19.1 — Complete the certificate

Candidate `(x,y)=(1/2,3/2)` is supplied. Find a matching dual witness.

**Answer:** multipliers `(1,0,0)` give upper bound `x+y<=2`. The candidate is
nonnegative, satisfies all three bounds and attains 2, so the duality gap is zero.
No search for an entire general-purpose LP solver is required for this check.

Quiz wire convention: `rat<p,q>` denotes p/q with q positive; it is not the
historical binary rational codec.

```text
ans<primal<rat<1,2>,rat<3,2>>,dual<1,0,0>,objective<2>,gap<0>,ae0>
```

## Puzzle 19.2 — Does zero gap imply uniqueness?

**Answer:** no. Every `(t,2-t)` for rational `0<=t<=2` is feasible and optimal.
For example `(0,2)` and `(2,0)` are different witnesses with the same objective.
Do not report only one survivor as the unique solution. This is an infinite
rational family; a finite census requires a separately declared discretization.

Suggested packet: `ans<optimal<yes>,unique<no>,witnesses<p0,p1>>`, with p0 and p1
bound to those two points.

## Puzzle 19.3 — A correct objective at an infeasible point

A candidate proposes `(-1,3)` with the same dual witness and objective 2.

**Answer:** it violates `x>=0` and `ub3`. Equal primal and dual objective values
cannot replace primal feasibility. Report both violated constraint IDs. A
checker that omits variable-domain constraints may accept false certificates in
other instances even when all submitted row inequalities hold.

**Mutation:** test `(-1,1)` for the different LP `max x+y`, `x+y<=0`, `x,y>=0`.
The row and objective equality pass, but the nonnegativity contract fails. Bind
the checker to the full declared problem, including variable domains.

## Puzzle 19.4 — Exactness and exhaustion

Compare candidate `(1/2,3/2)` with JSON numeric values `0.5,1.5`. Also suppose a
search stops after finding `(1/2,3/2)` without checking its dual witness.

**Answer:** decimal floating-point input is outside this exercise's exact rational
witness contract even when the values happen to be exactly representable in
binary. Use canonical typed rationals. The interrupted search has a candidate;
only replaying feasibility and the dual certificate establishes this scoped
optimum. Neither result authorizes an external action.

## Grading and scope

Four puzzles, 0–3 points each: complete feasibility, independently checked bound,
and the appropriate uniqueness/evidence boundary. Maximum 12. The original quiz
verifier's LP helper is a fixture helper with incomplete intake checks; see the
review before using it to grade arbitrary submissions.
