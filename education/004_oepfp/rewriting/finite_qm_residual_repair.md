# Repair a proposal without changing its mathematical task

AuthorityEffect: None. Source revision: `000ee9b0c234eda74340e424d6cfb3f6ec001df7` (links and fixture values rechecked at `c419cc6beb` on 2026-10-20; the public input bytes are unchanged). This instructional supplement uses the fixed C4 fixture. It records no live model trial or native acceptance.

**Objectives:** classify a rewrite; diagnose a failed witness; prepare a complete replacement under the current task binding. Read [the C4 mathematics](../math/10_finite_qm_certificate_scope.md) first. Use [the workflow walkthrough](../docs/23_finite_qm_workflow_walkthrough.md) for exact commands, response fields and permitted failure codes. The exercises here are pencil work; proposed diagnoses are not observed runtime receipts.

## Keep the original question visible

The original input is `c=(2,-3,5,7)` with edges `01,12,23,03` and one face `01+12+23-03`. A valid mathematical answer is `a=(0,2,-1,4)`, `w=(-1,-1,-1,1)`, `phi1=3`, `gamma2=3`. The [public input](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_public_input.json) and [work unit](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json) own those assumptions and response requirements.

There are two different meanings of repair. A **cochain repair** subtracts vertex differences from the observed edge list. A **proposal repair** replaces an incorrect submitted certificate. Neither grants permission to change the observations to make a desired answer pass. *(Definition.)*

**Probe:** A candidate prints `phi1=0`, with every potential coordinate zero. Is the response's JSON shape enough? No. Recomputing the residual gives `(2,-3,5,7)` with cost 17. A well-formed object can encode a false claim.

## Worked diagnosis: a feasible bound is not always an optimum

Suppose a proposer supplies the correct potential but the zero dual:

```text
a=(0,2,-1,4)
r=(0,0,0,3), achieved cost=3
w=(0,0,0,0)
d0^T*w=0, max(abs(w))=0, dot(w,c)=0
```

The zero dual is feasible, but its lower bound is zero. There is still a gap of three. Changing only the printed `phi1` to zero does not fix that gap. A complete corrected certificate must supply a feasible dual attaining the achieved cost, such as `(-1,-1,-1,1)`, and retain the exact scalar claims. *(Derivation.)*

The learner's job is to discover or reconstruct that witness. A production repair prompt should receive only the workflow's permitted diagnosis, not a hidden expected answer. This public worked example is deliberately unsuitable as an unseen benchmark.

**Micro-check:** Is `(-1,-1,-1,0)` a usable substitute because each coordinate is small enough? No. Conservation fails at vertices 0 and 3. Repair both feasibility and the gap; do not optimize only the displayed objective.

## Four operations with different obligations

| Operation | Example | Preserved or changed? | Required evidence |
| --- | --- | --- | --- |
| Reversible representation | Encode rational 3 as the declared `{num:3,den:1}` object, then decode. | Same scalar on the admitted representation domain. | Decoder recovers the value; reject malformed/noncanonical inputs under the actual contract. |
| Witness replacement | Replace zero dual with a conserved dual attaining 3. | Same mathematical task; a different candidate certificate. | Recompute all predicates and validate the new turn binding. |
| Exact cochain subtraction | Replace `c` by `c-d0*a` in a mathematical analysis. | Same quotient class; generally a different representative. | Show `c-r=d0*a` and preserve the fixed carrier and norm. |
| Observation change | Replace direct edge 7 by 4. | A different input with a different optimum. | New task provenance and source pins; no credit against the original bound task. |

Worked check of the last row: with `c'=(2,-3,5,4)` the face sum is `d1*c' = 2 + (-3) + 5 - 4 = 0`, so `gamma2' = 0`. The potential `a=(0,2,-1,4)` now gives `d0*a=(2,-3,5,4)` and residual `(0,0,0,0)`, so the new optimum is `phi1' = 0`. The original task still has `d1*c = 2 + (-3) + 5 - 7 = -3`, `gamma2 = 3` and `phi1 = 3`. The zero belongs to a different problem. *(Derivation, checked by hand 2026-10-20.)*

A coordinate reversal is also a representation change only when the corresponding edge value, matrix row, dual coordinate and face coefficient change together. The [orientation exercise](../math/10_finite_qm_certificate_scope.md#faded-exercise-then-independent-transfer) tests that condition.

Rational decoding is reversible at the value level on admitted canonical pairs. It need not recover arbitrary original JSON bytes, whitespace or key order. Byte custody and semantic equality are different obligations. A generic prose rewrite cannot be assumed reversible only because its author calls it equivalent.

## Why exact repair cannot erase this optimum

Let `r=c-d0*a`. For every potential `b`, `r-d0*b=c-d0*(a+b)`. As `b` varies, `a+b` ranges over the same potential space. Thus:

```text
min_b norm1(r-d0*b)=min_u norm1(c-d0*u)=3
d1*r=d1*c-d1*d0*a=d1*c=-3
```

The representation has concentrated the residual on the direct edge; it has not made the quotient obstruction smaller. A claim that both diagnostics must descend to zero under exact subtraction contradicts these identities on the fixed complex. Different problem-changing operations need their own declared contract. *(Derivation.)*

## From diagnosis to a replacement turn

1. Retain the original work unit, response bytes and checking result. Record whether the failure was schema, binding, mathematical witness or unavailable infrastructure; those cases require different actions.
2. If the workflow permits repair, prepare **P3_REPAIR** with a new attempt and the permitted failure code. The walkthrough's `G3_WITNESS` example is guidance syntax, not evidence that this worked certificate failed.
3. Copy the new prepared binding. Supply a complete replacement containing `potential`, `dual_witness`, `phi1` and `gamma2`, with the outer task/attempt/hash fields from that exact turn. Do not send only a changed dual coordinate.
4. Check the retained replacement through the declared owner using matching stage and guidance arguments. Missing infrastructure leaves checking incomplete. Prompt preparation alone has `checker_status=NOT_RUN`.
5. Respect the mode's two-candidate bound. Record the narrow result and unresolved imports; repeated manual preparation is not an automatic budget enforcer.

Six research stages **P0–P5**, eleven public runtime stages, and 101 numbered teaching specifications are separate. P3 is a research workflow label; it does not mean public runtime stage 3. The present assets do not establish automatic execution of every research stage.

## Faded and independent exercises

**Faded:** A candidate submits `a=(0,2,-1,3)` and the original conserved dual. Complete `d0*a=(__,__,__,__)`, residual `(__,__,__,__)`, achieved cost `__` and dual objective `__`. Decide whether this candidate needs replacement.

**Feedback:** `d0*a=(2,-3,4,3)`, residual `(0,0,1,4)`, achieved cost 5 and dual objective 3. The lower bound is valid, but the gap is 2. Restoring a matching potential is one repair; changing `phi1` to 5 does not establish optimality.

**Independent:** Classify each statement and state its missing evidence:

1. "My new wording is clearer, so the model must now answer correctly."
2. "The JSON parses, so its dual witness certifies the optimum."
3. "The same decoded rational values are retained, so the original response bytes are unchanged."
4. "The checker accepted a finite certificate, so the quantum physical bridge is established."

**Teacher key:** These respectively confuse a heuristic with measured improvement, syntax with mathematical feasibility, semantic equality with byte identity, and a finite predicate with an unpaid physical bridge. Ask learners to name the additional check before offering this key.

**Pass criterion:** reconstruct the two-unit gap and explain all four boundary errors. Repeat only the failed subskill: differences, conservation, binding, or scope. A learner who can repeat the answer but cannot diagnose a changed potential has not completed the transfer check.

## Hear the zero dual before the general repair rule

A **dual witness** is a vector offered as a lower bound. **Feasible** means it is conserved, `d0` transpose times `w` equals the zero vector, and every coordinate has absolute value at most 1. Say `d0` as "d zero" and `w` as "w".

Use the zero dual before the general rule. The potential (0, 2, −1, 4) leaves residual (0, 0, 0, 3). The achieved cost is 3. The zero dual (0, 0, 0, 0) is feasible, and its lower bound is 0. The gap is 3 − 0 = 3. A feasible bound of 0 does not certify an optimum of 3.

**Check.** Is the zero dual enough because it is feasible? No. Feasibility without an equal bound leaves the gap of 3. Printing `phi1 = 0` does not close that gap.

### Spoken segment

About 45 seconds. One idea: a feasible lower bound of zero is not the optimum three. No screen is required.

"Keep the question fixed. The direct observation is seven. The potential leaves a residual of three. The zero dual balances, and its lower bound is zero. Zero is not three. The gap stays three. A feasible dual has to reach the achieved cost before it certifies the optimum."

### Video beats

Worked example: achieved cost 3 against the zero dual. Narration matches the spoken segment. No recording has been made. A later recording needs captions and a transcript.

| Time | On screen | Narration |
| --- | --- | --- |
| 00:00 | direct edge 7 | Keep the question fixed. The direct observation is seven. |
| 00:10 | residual 3 | The potential leaves a residual of three. |
| 00:18 | zero dual, bound 0 | The zero dual balances, and its lower bound is zero. |
| 00:28 | 0 is not 3 | Zero is not three. The gap stays three. |
| 00:36 | bound must reach 3 | A feasible dual has to reach the achieved cost before it certifies the optimum. |

## Evidence limits and sources

A heuristic LLM rewrite requires a declared comparison with fixed tasks, scoring, budget, source pins and retained failures. Reversible representation and exact certificate checks do not establish that empirical improvement. This review ran no providers, native judge, build or full suite. The arithmetic is a finite derivation on the supplied rational data. *(Scope.)*

Sources: [prompt compiler](../../../../omega_engine_pfp/infrastructure/finite_qm_prompt.py), [judge adapter](../../../../omega_engine_pfp/infrastructure/finite_qm_cochain_judge.py), [workflow stages and guidance](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/workflow.yaml), [mode and bounds](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/mode.yaml), [Chapter 02 quotient classes](../math/02_math_cochain_complexes_repairs_and_quotients.md), and [Chapter 03 optimality conditions](../math/03_math_obstruction_mass_duality_and_exact_lp.md).
