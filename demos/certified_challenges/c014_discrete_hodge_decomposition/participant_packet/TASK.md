# TASK: C014 Exact Discrete Hodge Decomposition

**AuthorityEffect:** None
**Challenge ID:** `c014_discrete_hodge_decomposition`
**Tier:** T2
**Target Inference Budget:** $< \$0.05$ (50,000 $\mu$USD)
**Hard Ceiling:** $\le \$0.50$ (500,000 $\mu$USD)
**Model Ceiling:** Open weights $\le 70\text{B}$ parameters, `allow_fallbacks: False`
**Protocol:** SG-CP v1 (Symbol Game Challenge Protocol v1)

---

## 1. Formal Problem Definition

Given an oriented 2-complex $K = (V, E, F)$ with integer incidence matrices:
- $\delta_0: C^0 \to C^1$ of size $|E| \times |V|$
- $\delta_1: C^1 \to C^2$ of size $|F| \times |E|$ satisfying the chain complex condition $\delta_1 \cdot \delta_0 = 0$
- an edge flow $f \in \mathbb{Q}^E$
- positive rational edge weights $W_1 = \operatorname{diag}(w_e)$ defining the weighted inner product:
  $$\langle a, b \rangle_{W_1} = \sum_{e \in E} w_e a_e b_e$$

The solver must compute potentials $\phi \in \mathbb{Q}^V$, $\psi \in \mathbb{Q}^F$, and harmonic flow $h \in \mathbb{Q}^E$ satisfying:
$$f = \delta_0 \phi + W_1^{-1} \delta_1^T \psi + h$$
with:
- $\delta_1 h = 0$ (curl-free / closed)
- $\delta_0^T W_1 h = 0$ (co-closed / divergence-free)

### Orthogonality Invariants
Under $\langle \cdot, \cdot \rangle_{W_1}$, the three parts $g = \delta_0 \phi$, $c = W_1^{-1} \delta_1^T \psi$, and $h$ are pairwise orthogonal:
$$\langle g, c \rangle_{W_1} = 0, \quad \langle g, h \rangle_{W_1} = 0, \quad \langle c, h \rangle_{W_1} = 0$$

### Harmonic Space Basis
The solver must also report:
- `harmonic_dim`: the dimension of the harmonic space $\mathcal{H}^1 = \ker(\delta_1) \cap \ker(\delta_0^T W_1)$, which equals the first rational Betti number:
  $$b_1(K; \mathbb{Q}) = |E| - \operatorname{rank}(\delta_0) - \operatorname{rank}(\delta_1)$$
- `harmonic_basis`: an exact linearly independent basis $\{b_1, \dots, b_k\}$ of $\mathcal{H}^1$ over $\mathbb{Q}$.

---

## 2. Bounds and Constraints

- $|V| \le 80$ (bound: |V| <= 80).
- $|E| \le 200$ (bound: |E| <= 200).
- $|F| \le 150$ (bound: |F| <= 150).
- Flow entries: rational numbers with $|numerator| \le 999$ and $|denominator| \le 999$.
- Weight entries: positive rational numbers $w_e > 0$ with denominator $\le 12$.
- Pure Python standard library only (no external CAS/LP/SymPy/SciPy imports).
- Python standard library JSON / RFC 8785 canonical form.

---

## 3. Deliverable and Output Schema

The frozen solver `solver.py` must expose `solve(case: dict) -> dict`.

### Rational Wire Format

Every rational in an answer (`phi`, `psi`, `h`, `harmonic_basis` entries) is written as a canonical string, and `harmonic_dim` as a canonical non-negative integer string:
- Integers: `"0"`, `"1"`, `"-5"` (no trailing `"/1"`, no leading zeros, and zero is `"0"`, never `"-0"`).
- Non-integer fractions: `"5/12"`, `"-3/4"`, in lowest terms (coprime numerator and denominator, denominator $> 1$, sign on the numerator only). A non-reduced string such as `"2/4"` or `"2/2"` is rejected.
- Plain JSON integers are also accepted. Binary floating point (`0.5`, `1.0`) and Booleans are rejected.

### Success Payload (`SOLVED`)
```json
{
  "id": "ex01",
  "status": "SOLVED",
  "phi": {"v0": "0", "v1": "1/3"},
  "psi": {},
  "h": {"e0_1": "1/3", "e1_2": "1/3", "e2_0": "1/3"},
  "harmonic_dim": "1",
  "harmonic_basis": [
    {"e0_1": "1", "e1_2": "1", "e2_0": "1"}
  ]
}
```

### Out-of-Scope Payload (`OUT_OF_SCOPE`)
When an input complex is not an oriented chain complex ($\delta_1 \cdot \delta_0 \neq 0$), the solver must identify the nonzero entry:
```json
{
  "id": "ex19",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "reason": "D1_D0_NONZERO",
    "face": "f0",
    "vertex": "v0"
  }
}
```

### Refusal Payload (`UNKNOWN`)
For inputs violating declared bounds or schemas:
```json
{
  "id": "case_id",
  "status": "UNKNOWN",
  "refusal": "VERTEX_COUNT_OUT_OF_BOUNDS",
  "refusal_code": "VERTEX_COUNT_OUT_OF_BOUNDS"
}
```

### Closed Refusal Enum
- `VERTEX_COUNT_OUT_OF_BOUNDS`
- `EDGE_COUNT_OUT_OF_BOUNDS`
- `FACE_COUNT_OUT_OF_BOUNDS`
- `COEFFICIENT_BOUND_EXCEEDED`
- `WEIGHT_DENOMINATOR_EXCEEDED`
- `WEIGHT_NON_POSITIVE`
- `MALFORMED_INPUT`
- `MALFORMED_CASE_STRUCTURE`
- `BUDGET_EXHAUSTED`

The judge accepts an `UNKNOWN` only when the named condition holds for the case (for example `VERTEX_COUNT_OUT_OF_BOUNDS` requires $|V| > 80$, `WEIGHT_DENOMINATOR_EXCEEDED` a weight whose denominator exceeds 12). `BUDGET_EXHAUSTED` records a harness event, not an answer: it carries no witness the judge can check, so it is never scored as a valid result for a case within the declared bounds. A case within the bounds needs `SOLVED` or, when $\delta_1 \cdot \delta_0 \neq 0$, `OUT_OF_SCOPE`.
