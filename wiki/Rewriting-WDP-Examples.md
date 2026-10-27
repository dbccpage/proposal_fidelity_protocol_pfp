# WDP rewriting: examples

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-WDP.md) · [DDC operations](Rewriting-WDP-DDC.md)

## Example 1: exact repair on a path

A path `v0 → v1 → v2 → v3` carries an edge defect that comes from the potential:

```text
φ = (v0: 0, v1: 2, v2: −1, v3: 5)
x = d0 φ = (2, −3, 6)
```

The defect is exact (Φ₁ = 0, Γ₂ = 0), so **E** applies. Root `v0` at 0 and
integrate along the edges to recover `φ`. Subtract:

```text
x − d0 φ = (0, 0, 0)
```

The receipt records the potential as its witness and the repaired defect as all
zeros. Applying E again changes nothing.

## Example 2: the residual that will not go away

Take a triangle with one cycle and no filled face, and put circulation 3 around
it. The face defect is zero, but Φ₁ = 3: no potential removes it.

- **E is refused**, because the defect is not exact.
- **R applies.** It records one independent cycle with circulation 3 and leaves
  Φ₁ = 3 and Γ₂ = 0 unchanged.
- To go further you must change the carrier, for example by filling the face,
  which needs a licensed **Λ** or **C** step. That is a different problem, not
  a repair of this one.

This is the same lesson as the [C4 square](Rewriting-PFP-Residual-Repair.md):
moving the residual around does not make it smaller.

## Example 3: three claims that look alike

Over Q, let `d0(t) = (t, 0)` and `d1(a, b) = b`.

- The chain law holds: `d1(d0(t)) = 0`.
- The raw repair class of `(a, b)` keeps `b`, since only the first coordinate can
  be repaired.
- All closed classes have `b = 0`.
- The identity map is homotopic to zero through the maps `H1(a,b) = a` and
  `H2(t) = (0, t)`. Yet the identity and the zero map send `(0, 1)` to different
  raw repair classes.

This one small example separates three different claims: a chain law, an
explicit homotopy, and equality of closed classes. A rewrite that preserves one
need not preserve the others.

## Example 4: which edits keep balance?

Four terms and the filled directed triangle 012, starting from zero excess.
Predict the effect of: an assertion on 01, an assertion on 10, adding a term,
and identifying 0 with 3. Then ask whether your answer holds for **every**
balanced input, not just the zero table. The general rules are:

- Growth keeps all old faces.
- An assertion update must avoid every marked directed arc.
- A merge must leave no surviving face touching the merged vertex.
- A new filling equation must lie in the rational span of the existing ones.

**Falsifier.** Fill 013, 023 and 123, and set only the excess on 20 to one. The
other three faces balance, but the new 012 equation fails. Reverse arcs are
independent, so balance on three faces does not give the fourth for free.

**The point.** Keeping balance and descending in the gradient quotient are
different protected questions. A particular input and output answer is a third.

## Example 5: refusal is absorbing

Ask for **E** on a defect whose face circulation is non-zero.

1. **M**: refused with reason `REFUSED_NON_ZERO_CURL`. The state is frozen.
2. Asking for **E** again is refused again, because nothing changed.
3. Only **C** (expose more context), **Λ** (a licensed lift) or **T** (seal the
   trace) may follow.

```json
{
  "operation": "M",
  "attempted_operation": "E",
  "reason_code": "REFUSED_NON_ZERO_CURL",
  "cochain_state_frozen": true,
  "permitted_next_operations": ["C", "Λ", "T"],
  "authority_effect": "None"
}
```

## What this does not show

None of these diagnostics authorises a Genesis extension, and they give no
physical interpretation. General covers, coherent higher fillers and the quantum
bridge remain open obligations in the WDP claim ledger.
