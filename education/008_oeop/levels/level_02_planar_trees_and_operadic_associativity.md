---
documentation_contract: symbol-game-documentation/v1
title: "OEWAS Level 02: Planar Trees, Partial Composition, and Operadic Associativity Witnesses"
kind: mathematical-reference
level: 2
status: active
maturity: production
claim_status: verified
authority_effect: "None"
source_paths:
  - omega_engine_operads/domain/planar_substitution.py
  - omega_engine_operads/domain/operad/planar.py
  - omega_engine_operads/domain/operad/operad.py
  - omega_engine_operads/domain/operad/errors.py
last_verified: 2026-10-01
---

# OEWAS Level 02: Planar Trees, Partial Composition & Operadic Associativity Witnesses

**AuthorityEffect:** None. Complete mathematical and architectural reference for planar rooted trees, partial operadic composition $\circ_i$, sequential and parallel associativity laws, and composition witnesses; no operational authorization is conferred.

---

## 1. Executive Intuition: Operadic Substitution vs. Unary Composition

In ordinary category theory, morphisms $f: A \to B$ and $g: B \to C$ compose unarily as $g \circ f: A \to C$. Each morphism has exactly one input and one output.

However, realistic multi-agent workflows involve operations that consume **multiple** distinct typed artifacts (such as combining a `Paper`, a `Proof`, and `Code` into an `Audit`) and produce a single output. Such multi-input single-output morphisms live in a **Multicategory** or **Coloured Operad**.

Composition in an operad is not a simple linear chain; it is **planar tree substitution** $\theta \circ_i \phi$, where an operation $\phi$ is plugged into the $i$-th input slot of an operation $\theta$.

---

## 2. The Planar Substitution Equation

Let $\theta \in \mathcal{O}(c_0, \ldots, c_{k-1};\, c_{\mathrm{out}})$ be an operation of arity $k$, and let $\phi \in \mathcal{O}(d_0, \ldots, d_{m-1};\, d_{\mathrm{out}})$ be an operation of arity $m$.

Substitution $\theta \circ_i \phi$ is admissible if and only if:
1. **Index Bound:** $0 \le i < k$.
2. **Colour Matching:** The target colour of $\phi$ exactly matches the colour expected by $\theta$ at slot $i$:
   $$d_{\mathrm{out}} = c_i$$

When admissible, the composite operation $\theta \circ_i \phi$ has:
- **Target Colour:** $c_{\mathrm{out}}$ (the target of $\theta$).
- **Composite Source Sequence:** Slot $i$ of $\theta$ is replaced in-place by the entire sequence of $\phi$'s inputs, preserving planar order:
  $$\operatorname{source}(\theta \circ_i \phi) = (c_0, \ldots, c_{i-1},\, d_0, \ldots, d_{m-1},\, c_{i+1}, \ldots, c_{k-1})$$
- **Derived Arity:**
  $$\operatorname{arity}(\theta \circ_i \phi) = k + m - 1$$

```text
               c_out                                       c_out
                 │                                           │
             ┌───┴───┐                                   ┌───┴───┐
             │   θ   │                                   │   θ   │
             └───┬───┘                                   └───┬───┘
         ┌───────┼───────┐                           ┌───────┼───────┐
         │       │       │                           │       │       │
        c_0     c_i     c_{k-1}                     c_0    d_out    c_{k-1}
                 ▲                                           │
                 │   spliced with                         ┌───┴───┐
                 └── d_out                                │   ϕ   │
                                                          └───┬───┘
                                                      ┌───────┼───────┐
                                                      │       │       │
                                                     d_0     ...   d_{m-1}
```

Because the order of inputs before slot $i$ and after slot $i$ is strictly preserved without crossing or permutation, this composition is **strictly planar**.

---

## 3. The Two Operadic Associativity Laws

In any well-defined operad, tree composition must be associative: the order in which intermediate operations are spliced into a larger tree cannot alter the final composite morphism.

### 3.1 Sequential Associativity (Vertical Nesting)

Suppose we have three operations $\theta, \phi, \psi$ where $\phi$ is spliced into slot $i$ of $\theta$, and $\psi$ is spliced into slot $j$ of $\phi$.

- **Left Bracketing:** First compose $\theta \circ_i \phi$. In the resulting composite, $\phi$'s input slot $j$ has shifted to position $i + j$ (because $i$ inputs from $\theta$ precede it). Then splice $\psi$:
  $$(\theta \circ_i \phi) \circ_{i + j} \psi$$
- **Right Bracketing:** First compose $\phi \circ_j \psi$. Then splice the composite directly into slot $i$ of $\theta$:
  $$\theta \circ_i (\phi \circ_j \psi)$$

The **Sequential Associativity Axiom** asserts:

$$\boxed{(\theta \circ_i \phi) \circ_{i + j} \psi \equiv \theta \circ_i (\phi \circ_j \psi)}$$

for all $0 \le i < \operatorname{arity}(\theta)$ and $0 \le j < \operatorname{arity}(\phi)$.

### 3.2 Parallel Associativity (Horizontal Disjoint Nesting)

Suppose $\phi$ and $\psi$ are spliced into two distinct slots $i$ and $j$ of $\theta$, with $i < j$.

- **Splicing $i$ then $j$:** Splicing $\phi$ into slot $i$ expands slot $i$ into $m = \operatorname{arity}(\phi)$ inputs. Consequently, the original slot $j$ (which was to the right of $i$) shifts rightward to $j + m - 1$:
  $$(\theta \circ_i \phi) \circ_{j + m - 1} \psi$$
- **Splicing $j$ then $i$:** Splicing $\psi$ into slot $j$ first does not shift slot $i$ (since $i < j$). When $\phi$ is subsequently spliced into slot $i$, its index remains $i$:
  $$(\theta \circ_j \psi) \circ_i \phi$$

The **Parallel Associativity Axiom** asserts:

$$\boxed{(\theta \circ_i \phi) \circ_{j + m - 1} \psi \equiv (\theta \circ_j \psi) \circ_i \phi \quad (i < j)}$$

---

## 4. Code Implementation Walkthrough

The planar composition algorithms live in [`omega_engine_operads/domain/planar_substitution.py`](../../../../omega_engine_operads/domain/planar_substitution.py) and [`domain/operad/planar.py`](../../../../omega_engine_operads/domain/operad/planar.py):

### 4.1 The `substitute` Function

```python
def substitute(theta: OperadOperation, index: int, phi: OperadOperation) -> OperadOperation:
    """Compute theta circle_i phi, or refuse."""
    if type(theta) is not OperadOperation or type(phi) is not OperadOperation:
        raise SubstitutionError("BAD_OPERATION", "both arguments must be operations")
    if type(index) is not int or type(index) is bool:
        raise SubstitutionError("BAD_INDEX", "index must be an exact integer")
    if not 0 <= index < theta.arity:
        raise SubstitutionError(
            "INDEX_OUT_OF_RANGE",
            f"{theta.name} has arity {theta.arity}; slot {index} does not exist",
        )
    expected = theta.source_colours[index]
    if phi.target_colour != expected:
        raise SubstitutionError(
            "COLOUR_MISMATCH",
            f"{theta.name} expects {expected!r} at slot {index}, but "
            f"{phi.name} produces {phi.target_colour!r}",
        )
    return OperadOperation(
        name=f"({theta.name} o_{index} {phi.name})",
        source_colours=(
            theta.source_colours[:index]
            + phi.source_colours
            + theta.source_colours[index + 1 :]
        ),
        target_colour=theta.target_colour,
    )
```

### 4.2 The Associativity Witness: `TreeCompositionWitness`

In [`domain/operad/planar.py`](../../../../omega_engine_operads/domain/operad/planar.py#L84-L138):

```python
@dataclass(frozen=True)
class TreeCompositionWitness:
    """Record that both bracketings of one sequential insertion were composed."""
    left_path: str
    right_path: str
    is_associative: bool
    details: str
    left_composite: ColourSignature | None = None
    right_composite: ColourSignature | None = None

    @classmethod
    def verify_sequential_associativity(
        cls,
        f: OperationSignature,
        g: OperationSignature,
        h: OperationSignature,
        i: int,
        j: int,
    ) -> Result[TreeCompositionWitness, OperadAssociativityError]:
        left = _left_bracketing(f.signature, g.signature, h.signature, i, j)
        if left.is_err:
            return Err(OperadAssociativityError(f"left bracketing refused: {left.error.message}"))
        right = _right_bracketing(f.signature, g.signature, h.signature, i, j)
        if right.is_err:
            return Err(OperadAssociativityError(f"right bracketing refused: {right.error.message}"))

        left_sig = left.unwrap()
        right_sig = right.unwrap()
        if left_sig != right_sig:
            return Err(OperadAssociativityError(f"bracketings disagree: {left_sig} vs {right_sig}"))
        return Ok(
            cls(
                left_path=f"({f.op_id} o_{i} {g.op_id}) o_{i + j} {h.op_id}",
                right_path=f"{f.op_id} o_{i} ({g.op_id} o_{j} {h.op_id})",
                is_associative=True,
                details=f"both bracketings composed to {left_sig}",
                left_composite=left_sig,
                right_composite=right_sig,
            )
        )
```

Notice that a witness is not an unverified boolean statement; it computes both algebraic compositions explicitly and verifies that the resulting `ColourSignature` objects match identically.

---

## 5. Typed Refusals: `SubstitutionError`

Whenever an illegal composition is attempted, the engine emits a typed `SubstitutionError`:

| Refusal Code | Cause | Invariant Enforced |
| :--- | :--- | :--- |
| `BAD_OPERATION` | Non-`OperadOperation` object passed | Strict domain object typing |
| `BAD_INDEX` | Index is not an exact integer (e.g. `bool`, `float`, or `str`) | Exact discrete slot addressing |
| `INDEX_OUT_OF_RANGE` | $i < 0$ or $i \ge \operatorname{arity}(\theta)$ | Arity boundary containment |
| `COLOUR_MISMATCH` | $\operatorname{target}(\phi) \neq \operatorname{source}(\theta)[i]$ | Operadic type safety |
| `ASSOCIATIVITY_VIOLATED` | Left and right bracketing yield different signatures | Planar tree associativity |

---

## 6. Concrete Worked Example: Splicing Contract Compliance

Consider two skills:
1. `meta-law-contract-enforcer`: Signature `(Contract, Code) -> Audit` (Arity 2).
2. `nomos-law-contract-manager`: Signature `(State) -> Contract` (Arity 1).

We compose `nomos-law-contract-manager` into slot $i = 0$ of `meta-law-contract-enforcer`:

$$\begin{aligned}
\theta &= \text{meta-law-contract-enforcer}: (\text{Contract}, \text{Code}) \to \text{Audit} \\
\phi &= \text{nomos-law-contract-manager}: (\text{State}) \to \text{Contract} \\
\theta \circ_0 \phi &= (\text{State}, \text{Code}) \to \text{Audit}
\end{aligned}$$

- **Verification:** Target of $\phi$ is `Contract`. Expected at slot 0 of $\theta$ is `Contract`. Match is exact.
- **Resulting Arity:** $2 + 1 - 1 = 2$.
- **Resulting Sources:** `(State, Code)`.

---

## 7. Verification and Local Unit Tests

To run the unit tests verifying planar substitution and operadic associativity:

```powershell
# Retired: OEWAS tests/unit/test_planar_substitution.py has no successor file under omega_engine_operads.
```

### The Level 02 Governance Invariants
- **INV-02-01 (Strict Planarity):** Substitution must never reorder inputs outside slot $i$.
- **INV-02-02 (Associativity Witnessing):** Every multi-step workflow composition must be witness-certified for associativity before admission.
- **INV-02-03 (Exact Refusals):** Illegal compositions must raise typed `SubstitutionError` with code and detail; bare Python exceptions are forbidden.
- **INV-02-04 (Authority Ceiling):** Splicing operations confers no operational authority; `AuthorityEffect: None`.
