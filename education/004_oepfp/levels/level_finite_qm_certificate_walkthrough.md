---
documentation_contract: symbol-game-documentation/v1
title: "Worked certificate: an exact four-edge residual"
kind: instructional-walkthrough
status: active
maturity: instructional
claim_status: finite-derivation
authority_effect: "None"
source_revision: 000ee9b0c234eda74340e424d6cfb3f6ec001df7
source_paths:
  - omega_engine_pfp/fixtures/finite_qm_workflow/c4_public_input.json
  - omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json
last_verified: 2026-10-22
verification_scope: exact integer arithmetic rechecked 2026-10-22 at 305b9690f9 against c4_public_input.json, which is unchanged since c419cc6beb; c4_work_unit.json changed only the sha256 of cochain.rs; native checker not executed
---

# Find an exact repair bound on four edges

AuthorityEffect: None. This is a supplemental worked lesson, not an additional numbered runtime stage. The mathematical claim below concerns the declared finite rational complex. It does not derive a quantum physical theory.

You need signed addition and multiplication. A vector is an ordered list of numbers; a matrix specifies how to combine such a list into another list. By the end, you should be able to construct a potential, recompute its residual, and show optimality using a feasible dual. The [workflow walkthrough](../docs/23_finite_qm_workflow_walkthrough.md) covers actual prompt preparation and response binding.

## First predict the obstacle

There are vertices `0,1,2,3`. Orient the edges as `01,12,23,03`, in that order. Give them values `c = (2,-3,5,7)`. A potential `a=(a0,a1,a2,a3)` predicts differences:

```text
d0*a = (a1-a0, a2-a1, a3-a2, a3-a0)
```

The first three edges form a path from 0 to 3. Their values sum to `2-3+5=4`. The fourth edge asks for `7` over the same endpoints. Predict whether all four can be potential differences simultaneously. They cannot: any potential's differences telescope along the path to its direct endpoint difference.

This explanation uses a supplied oriented graph. It does not claim that a graph, face or orientation follows from an uninterpreted inscription.

## Work the first three edges

Choose `a0=0`. This fixes an arbitrary additive constant, called the gauge. Matching the path edges gives:

```text
a1 = 0+2 = 2
a2 = 2-3 = -1
a3 = -1+5 = 4
a = (0,2,-1,4)
d0*a = (2,-3,5,4)
r = c-d0*a = (0,0,0,3)
norm1(r) = |0|+|0|+|0|+|3| = 3
```

The `L1` norm means the sum of absolute coordinate values. We have constructed a repair whose remaining cost is 3. This gives an upper bound on the smallest possible cost. It does not by itself rule out another potential with cost 2.

**Check before proceeding:** If every potential coordinate increases by 10, what happens to `d0*a`? Nothing: each endpoint difference cancels the added constant. Potentials themselves need not be unique.

## Show that no smaller residual is possible

Use `w=(-1,-1,-1,1)`. This is a dual witness: a set of signed edge weights that will supply a lower bound. Two feasibility checks are necessary.

First, each absolute coordinate is at most 1. Second, its net contribution at every vertex vanishes. In matrix language the second check is `d0^T*w=0`; the superscript `T` means transpose. For this edge order the four coordinates are:

```text
vertex 0: -w01-w03 = 1-1 = 0
vertex 1:  w01-w12 = -1+1 = 0
vertex 2:  w12-w23 = -1+1 = 0
vertex 3:  w23+w03 = -1+1 = 0
```

The dot product multiplies matching coordinates and adds them:

```text
dot(w,c) = (-1)*2 + (-1)*(-3) + (-1)*5 + 1*7 = 3
```

For **any** potential `b`, conservation gives `dot(w,d0*b)=0`. Since `|wi|<=1`, each term `wi*xi` is at most `|xi|`. Therefore:

```text
3 = dot(w,c) = dot(w,c-d0*b) <= norm1(c-d0*b)
```

Every potential leaves cost at least 3, and our constructed potential leaves exactly 3. The optimum is consequently `phi1=3` for this supplied complex. *(Derivation.)* This is why the certificate needs a feasible lower bound as well as a constructed repair.

**Wrong-answer diagnosis:** A vector whose dot product is 3 may fail conservation. Its matching number then gives no bound on all potentials. Check equations before matching objective values.

## Compute the declared face curvature

The input declares one face with signed boundary `01+12+23-03`. Define `d1` by its row `(1,1,1,-1)`. Applied to any potential differences it gives zero:

```text
(a1-a0)+(a2-a1)+(a3-a2)-(a3-a0) = 0
d1*d0 = 0
d1*c = 2-3+5-7 = -3
gamma2 = norm1(d1*c) = 3
```

Thus `phi1=gamma2=3` in this example. Equality here does not establish equality on all complexes or for every choice of norm. Notice also that `phi1` measures a minimized edge residual while `gamma2` measures the face value under the declared face map.

## Encode the mathematical answer

The work unit's `answer` object is:

```json
{
  "potential": [
    {"num":0,"den":1},
    {"num":2,"den":1},
    {"num":-1,"den":1},
    {"num":4,"den":1}
  ],
  "dual_witness": [
    {"num":-1,"den":1},
    {"num":-1,"den":1},
    {"num":-1,"den":1},
    {"num":1,"den":1}
  ],
  "phi1": {"num":3,"den":1},
  "gamma2": {"num":3,"den":1}
}
```

This is the inner mathematical answer, not a complete task-turn response. The outer object must also contain the exact `task_id`, `attempt_id` and `input_sha256` from your own prepared schema. Follow the [workflow walkthrough](../docs/23_finite_qm_workflow_walkthrough.md#4-read-the-binding-before-constructing-a-reply) before submitting it. This lesson supplies the worked answer for teaching; it is unsuitable as an unseen derivation benchmark.

## Transfer exercise

Attempt these before reading the answer discussion. For the changed-input questions, perform pencil work; do not submit a changed problem using the original fixture's binding or source pins.

1. Change only the fourth edge value from `7` to `1`. Keep the first three edges fixed. Compute `d0*a` and `r` for the same potential. What cost does it achieve?
2. Find a feasible dual certifying that this new cost is optimal. State both feasibility checks, its dot product and the new `gamma2`.
3. Change the fourth edge to `4`. Can a zero dual certify the optimum? Explain why a zero dual could not certify the original optimum of 3.
4. For the original data, replace the last dual coordinate by zero. Which vertex equations fail? Why is a matching objective, if supplied separately, insufficient?
5. Explain in two sentences why neither this certificate nor a successful schema check supplies a Hilbert space, a Born rule or permission to deploy a system.

Pass criterion for this lesson: show the residual, conservation equations, norm bound and matching objectives for questions 1–3; identify the failed vertex equations in question 4; preserve the stated scope in question 5. A bare numerical answer is incomplete.

## Answer discussion

For fourth edge `1`, `d0*a` stays `(2,-3,5,4)`, so the residual is `(0,0,0,-3)` and its norm is 3. Choose `w=(1,1,1,-1)`. It is the negative of the original conserved dual, has maximum absolute coordinate 1, and gives `dot(w,c)=2-3+5-1=3`. The face value is `3`, so `gamma2=3`. Equal lower and upper bounds again establish `phi1=3`.

For fourth edge `4`, the same potential matches every edge and the residual is zero. The zero dual is feasible with objective zero; together these certify optimum zero. For the original data its lower bound would be zero, leaving a gap between lower bound zero and achieved cost 3. Feasibility alone is insufficient for an optimality certificate.

With original dual `(-1,-1,-1,0)`, vertices 0 and 3 have net values `1` and `-1`. Thus the dual is not conserved, even though its coordinate bound holds. It cannot cancel `dot(w,d0*b)` for every potential.

The displayed rational arithmetic was independently checked during this review under Python 3.12.10. No native checker was run for this lesson. The [source work unit](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json) explicitly retains the unpaid quantum imports. A finite mathematical check establishes only its stated predicates; a task schema and an authorization policy answer different questions.

## Listen, then watch

The sections above are the reading. This block is the same example in one spoken idea and one short video plan. It was not recorded on 2026-10-22. AuthorityEffect: None.

**Plain opening.** Four measured edges cannot all be height differences. The long path adds to 4. The direct edge says 7. The leftover is 3, and 3 is the best you can do.

**Terms at first use.** A potential is a height on a corner. "D zero" turns heights into edge differences. The residual is measured value minus that difference. The ell-one norm adds absolute values. A dual witness is a second list of edge weights used only as a lower bound. "Phi one" is the smallest residual norm. "Gamma two" is the absolute value of the face sum.

**One number before the general bound.** Heights 0, 2, minus 1 and 4 give differences 2, minus 3, 5 and 4. Subtract from 2, minus 3, 5 and 7. The residual is 0, 0, 0, 3. The norm is 3. Only after that number does the general line apply: every other height list costs at least the dual pairing, which is also 3.

**A check you can fail.** Weights minus 1, minus 1, minus 1 and 0 keep each absolute value at most 1, but they do not balance. Corner 0 is left at plus 1 and corner 3 at minus 1. A pairing computed from those weights is not a lower bound.

**Spoken segment.** Duration: 45 seconds. One idea: the two routes from corner 0 to corner 3 disagree by 3.

> Start at corner zero. Two, then minus three, then plus five. That path adds to four. The direct edge also runs from corner zero to corner three, and it says seven. Seven minus four is three. Heights zero, two, minus one, four predict four on that direct edge. The measurement is seven, so three is left. A second witness, weights minus one, minus one, minus one, plus one, balances at every corner and pairs to three. You cannot do better than three. This is arithmetic on the supplied list. It is not a physical theory.

**Check with no screen.** What is two minus three plus five? If you said seven, you used the direct edge. The path is four. The disagreement with seven is three.

**Video beats.**

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:12 | path = 4 | "Two, minus three, plus five, is four. Pause and say that sum." |
| 0:12–0:22 | direct = 7 | "The direct edge says seven. Seven minus four is three." |
| 0:22–0:35 | leftover 0, 0, 0, 3 | "Heights zero, two, minus one, four leave three on the last edge." |
| 0:35–0:50 | weights balance | "Minus one, minus one, minus one, plus one. They balance. Their pairing is three." |
| 0:50–1:05 | 3 is optimal | "Every height list costs at least three. Ours costs three. Three is optimal." |
| 1:05–1:15 | not physics | "This is rational arithmetic on supplied data. It does not add a physical theory." |

## Expert continuation

Write the four rows of `d0` from the edge list, multiply `d1*d0`, and prove the lower-bound inequality symbolically rather than numerically. Then explore the family with fourth edge `t`: the same path potential leaves residual `t-4`; choose the sign of the dual to obtain `phi1=|t-4|`. Separate the case `t=4`, where several feasible duals can attain the same zero objective. Explain which part of this argument depends on this single-cycle complex before transporting it to a different carrier.

Sources: the [public matrix data](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_public_input.json), [certificate predicates](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json), and [native adapter](../../../../omega_engine_pfp/infrastructure/finite_qm_cochain_judge.py). These sources bind the finite example; this lesson makes no empirical physics claim.
