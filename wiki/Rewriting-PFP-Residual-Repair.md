# PFP rewriting: residual repair

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-PFP.md) · [Dialects and pilot](Rewriting-PFP-Dialects.md)

This page works through one fixed task: repairing a proposal **without changing
its mathematical question**. It uses the C4 square from the finite-QM workflow.

## The fixed task

A square with vertices 0–3, edges `01, 12, 23, 03`, and one face
`01 + 12 + 23 − 03`. The observed edge values are:

```text
c = (2, −3, 5, 7)
```

A correct certificate:

```text
potential   a = (0, 2, −1, 4)
dual        w = (−1, −1, −1, 1)
phi1 = 3          gamma2 = 3
```

The face sum is `2 + (−3) + 5 − 7 = −3`, so `gamma2 = 3`, and the best possible
residual cost is `phi1 = 3`.

## Two meanings of "repair"

- **Cochain repair** subtracts vertex differences `d0*a` from the edge list. It
  keeps the same question.
- **Proposal repair** replaces an incorrect certificate with a correct one.

Neither allows changing the observations so that a wanted answer passes.

## Diagnosis 1: well-formed but false

A candidate prints `phi1 = 0` with every potential coordinate 0. The JSON is
well formed. But recomputing the residual gives `(2, −3, 5, 7)`, with cost 17.
**A well-formed object can carry a false claim.**

## Diagnosis 2: a feasible bound that is too low

The proposer sends the right potential but the zero dual:

```text
a = (0, 2, −1, 4)     residual r = (0, 0, 0, 3)     achieved cost 3
w = (0, 0, 0, 0)      d0ᵀw = 0     max|w| = 0     w·c = 0
```

The zero dual is **feasible**, since it balances and every coordinate is at most
1 in size. But its lower bound is 0, so a gap of 3 remains. Printing `phi1 = 0`
does not close it. A complete fix supplies a feasible dual that reaches 3, such
as `(−1, −1, −1, 1)`.

Is `(−1, −1, −1, 0)` an acceptable substitute because each coordinate is small?
**No.** It does not balance at vertices 0 and 3.

## Four operations, four obligations

| Operation | Example | Same or changed? | Evidence needed |
| --- | --- | --- | --- |
| Reversible representation | Encode 3 as `{num:3, den:1}` and decode | Same value on the admitted domain | The decoder recovers it; malformed input is rejected |
| Witness replacement | Swap the zero dual for one that reaches 3 | Same task, new certificate | Recheck every predicate under a new binding |
| Exact cochain subtraction | Replace `c` with `c − d0*a` | Same quotient class, new representative | Show `c − r = d0*a` on the fixed carrier and norm |
| Observation change | Replace the 7 with 4 | A different input with a different optimum | New task provenance; no credit on the old task |

### The last row, worked

With `c' = (2, −3, 5, 4)`, the face sum is `2 + (−3) + 5 − 4 = 0`, so
`gamma2' = 0`. The potential `(0, 2, −1, 4)` gives `d0*a = (2, −3, 5, 4)` and
residual zero, so `phi1' = 0`. The original task still has face sum −3,
`gamma2 = 3` and `phi1 = 3`. **The zero belongs to a different problem.**

## Why exact repair cannot erase the optimum

Let `r = c − d0*a`. For any potential `b`, `r − d0*b = c − d0*(a + b)`, and `a + b`
ranges over all potentials as `b` does. So:

```text
min over b of |r − d0*b|₁  =  min over u of |c − d0*u|₁  =  3
d1*r  =  d1*c − d1*d0*a  =  d1*c  =  −3
```

The subtraction moved the whole residual onto the direct edge. It did not make
the obstruction smaller. Claiming that exact subtraction drives both diagnostics
to zero contradicts these identities.

## From diagnosis to a replacement turn

1. Keep the original work unit, response bytes and check result. Record the type
   of failure: schema, binding, mathematical witness, or missing infrastructure.
2. If repair is allowed, prepare a new attempt at stage `P3_REPAIR` with the
   permitted failure code, for example `--stage P3_REPAIR --failure-code G3_WITNESS`.
3. Copy `task_id`, `attempt_id` and `input_sha256` from **that** new preparation,
   not the earlier one. Send a **complete** replacement (potential, dual, `phi1`,
   `gamma2`) with those three fields. Never send only the changed coordinate.
4. Check the replacement with the same attempt, stage and failure-code arguments
   used to prepare it. Preparing a prompt is not a check; its status is `NOT_RUN`.
   The [workflow walkthrough](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/education/004_oepfp/docs/23_finite_qm_workflow_walkthrough.md)
   has the exact commands.
5. Respect the two-candidate limit and record what remains open.

## Practice

**Faded.** A candidate submits `a = (0, 2, −1, 3)` with the correct dual. Fill in
`d0*a`, the residual, the achieved cost and the dual objective.

*Answer:* `d0*a = (2, −3, 4, 3)`, residual `(0, 0, 1, 4)`, cost 5, dual
objective 3. The bound is valid, but the gap is 2. Changing `phi1` to 5 does not
prove optimality.

**Classify the error in each statement:**

1. "My new wording is clearer, so the model must now answer correctly."
2. "The JSON parses, so its dual certifies the optimum."
3. "The decoded values are the same, so the response bytes are unchanged."
4. "The checker accepted a finite certificate, so the quantum bridge is
   established."

*Key:* a heuristic taken for a measured gain; syntax taken for feasibility;
equal meaning taken for equal bytes; a finite check taken for a physical claim.
