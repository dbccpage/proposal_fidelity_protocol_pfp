# Quiz 16: Local green, global red on a three-cycle

**Status:** worked finite exercises; model responses remain proposals.\
**AuthorityEffect:** None. **GenesisEffect:** None.\
**Response profile:** `quiz-packet-v1`; exact mathematics and bindings are declared outside the wire.

## Seed prompt

> The carrier has vertices a,b,c. Variables take values in F2={0,1}; addition is
> XOR. The three edge constraints are x_a+x_b=1, x_b+x_c=1, x_c+x_a=1.
> Supply a local witness for every edge, then decide whether one global assignment
> satisfies all edges. Exhibit the obstruction. A repair is a separate proposal.

## Puzzle 16.1 — Three local witnesses

**Answer:** assign `(0,1)` on each independently oriented edge `(a,b)`, `(b,c)`,
`(c,a)`. Each two-variable problem passes. These choices disagree on overlaps:
for example the first uses `b=1`, the second `b=0`. Three local passes therefore
supply no global section.

Suggested packet: `ans<local<3>,overlap<conflict>,global<open>,ae0>`.

## Puzzle 16.2 — Obstruction without enumeration

Add the three equations in F2.

**Answer:** each vertex occurs twice, so the left side is 0; the right side is
`1+1+1=1`. Thus any global assignment would require `0=1`. This is an exact
inconsistency witness for this declared finite carrier. Enumerating the eight
assignments independently returns zero satisfying assignments.

Suggested packet: `ans<cycle_sum<1>,global_solutions<0>,obstruction<nonzero>>`.

**Mutation:** omit the third edge from the checker. The remaining path has two
solutions; accepting that result for the original problem is a coverage failure.
Require equality of declared and checked edge IDs, not just a count supplied by
an evaluator.

## Puzzle 16.3 — Retain tied repairs

The host permits changing exactly one edge right-hand side. Every such change has
cost 1. List **all** least-cost repairs and their solution counts.

**Answer:** toggle `ab`, `bc`, or `ca` from 1 to 0: three tied repairs, two global
assignments each. Cost 0 is impossible by the cycle sum, so the optimum is 1.
Pinning `x_a=0` leaves one solution in each repaired problem. That pin is an
additional declaration; it is not a consequence of the original problem.

Suggested packet: `ans<cost<1>,repairs<ab,bc,ca>,solutions_each<2>,ae0>`.

**Mutation:** return only repair `ca` and claim uniqueness. It is a valid repair
proposal but an incomplete minimum census.

## Puzzle 16.4 — Does renaming repair the obstruction?

Rename `a→b`, `b→c`, `c→a`, transporting every edge and value consistently.

**Answer:** the cycle sum remains 1. A faithful relabeling preserves this
obstruction. Changing one right-hand side is a changed problem, whereas relabeling
alone is not a repair. The proposal, its evaluation and permission to apply it
remain separate records.

## Grading and scope

Four puzzles, 0–3 points each: correct result, explicit witness, and preserved
carrier/scope. Maximum 12. This is a finite affine constraint example over F2;
it makes no general claim that every natural-language conflict has this form.
