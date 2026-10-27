# WDP rewriting: DDC operations

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-WDP.md) · [Examples](Rewriting-WDP-Examples.md)

The **Discrete Deformation Calculus** (DDC) types every state change with one of
eight letters. Each letter is a rewrite with a precondition, a postcondition and
a receipt.

| Letter | Operation | Acts on | Rule |
| --- | --- | --- | --- |
| **E** | Exact repair | The coboundary part, `im(d0)` | Subtract a potential; carrier unchanged |
| **R** | Residual projection | The harmonic part, `ker(d1)/im(d0)` | Record what remains; Φ₁ and Γ₂ unchanged |
| **C** | Context exposure | The carrier boundary | Enlarge scope; no scope laundering |
| **I** | Integration | The step tape | Commit a valid step with its receipt |
| **Λ** | Structural lift | `Qⁿ → Qⁿ⁺ᵏ` | Extend dimension only through a licensed gate |
| **D** | Scale descent | `Qᵐ → Qⁿ` | Coarsen only with a declared loss ledger |
| **M** | Typed refusal | The control state | Refuse with a reason; state unchanged |
| **T** | Terminalisation | Routing | Seal the trace |

## How the letters connect

```text
Open ──E──▶ (exact defect)        ──▶ I ──▶ Open
Open ──R──▶ (closed residual)     ──▶ I ──▶ Open
Open ──C / Λ / D──▶               ──▶ I ──▶ Open
Open ──M──▶ refused ──C or Λ──▶ Open
                     └──T──▶ sealed
Open ──T──▶ sealed (when nothing lawful remains)
```

## E: exact repair

**Precondition:** Φ₁ = 0 and Γ₂ = 0, and the detector is adequate (not blind).

A defect in `im(d0)` has a potential `φ` with `d0 φ = x`, unique up to a constant
on each connected component. Find it by integrating outward from a root set to
0 along a spanning forest. Then:

```text
x  ↦  x − d0 φ  =  0
```

**Refused if** the carrier changes, the input was not exact, any defect remains
afterwards, or the detector is blind. Applying E twice changes nothing.

## R: residual projection

Not every defect can or should be removed. R records what remains without
erasing it. Over Q the edge cochains split three ways:

```text
C¹  =  im(d0)  ⊕  im(d1ᵀ)  ⊕  H¹
        exact     co-exact     harmonic
```

On one cycle of length `k`, the harmonic part is the mean circulation
`c_H = (1/k) Σ x(e_j)`. On a **graph** (no filled faces), the residual register
has `b₁ = |E| − |V| + c` coordinates, one per independent cycle, and all are
zero exactly when the defect is exact. With filled faces this count is not the
dimension of `H¹` (a filled triangle has `b₁ = 1` but `H¹ = 0`), and the
co-exact part must be accounted for separately.

**Refused if** the carrier, Φ₁ or Γ₂ changes. A secondary tie-break metric may be
used only when Φ₁ and Γ₂ are already equal between candidates. It can never
override a worse primary score.

## M: typed refusal

Refusing is as much a first-class operation as deforming. A refusal records a
reason and leaves the state exactly as it was (proved in Lean as
`Ddc.M_preserves_state`).

- **Intake refusals** happen before admission and never enter the trace.
- **In-trace refusals** happen when an admitted operation cannot proceed.
- **Absorption:** after a refusal, only C, Λ or T may follow. Retrying the same
  operation without new scope, evidence or licence is refused again.
- An M step with no recognised reason code is itself rejected.

## Receipts

Each letter emits a receipt with the operation, status, before-and-after values
and `authority_effect: None`. For example, a residual projection on a triangle:

```json
{
  "operation": "R",
  "status": "RESIDUAL_RETAINED",
  "raw_norm": "3",
  "exact_norm": "0",
  "residual_norm": "3",
  "phi1": "3",
  "gamma2": "0",
  "carrier_nodes": 3,
  "carrier_edges": 3,
  "independent_cycles": 1,
  "fundamental_circulations": ["3"],
  "authority_effect": "None"
}
```

Next: [worked examples](Rewriting-WDP-Examples.md).
