# TASK: C012 Cellular Sheaf Cohomology $H^0$ and $H^1$ over $\mathbb{Q}$

**AuthorityEffect:** None  
**Challenge ID:** `c012_cellular_sheaf_h0_h1`  
**Tier:** T2  
**Target Inference Budget:** $< \$0.05$ (50,000 $\mu$USD)  
**Hard Ceiling:** $\le \$0.50$ (500,000 $\mu$USD)  
**Model Ceiling:** Open weights $\le 70\text{B}$ parameters, `allow_fallbacks: False`  
**Protocol:** SG-CP v1 (Symbol Game Challenge Protocol v1)  

---

## 1. Formal Problem Definition

A cellular sheaf $\mathcal{F}$ over the field of rational numbers $\mathbb{Q}$ on a directed graph $G = (V, E)$ attaches:
1. To each vertex $v \in V$, a finite-dimensional stalk vector space $\mathcal{F}(v) = \mathbb{Q}^{d_v}$ with dimension $d_v \in \{0, 1, 2, 3, 4\}$.
2. To each directed edge $e = (u, v) \in E$, a finite-dimensional stalk vector space $\mathcal{F}(e) = \mathbb{Q}^{d_e}$ with dimension $d_e \in \{0, 1, 2, 3, 4\}$.
3. To each incidence of a vertex with an edge:
   - Tail restriction matrix: $F_{u \unlhd e} \in \mathbb{Q}^{d_e \times d_u}$
   - Head restriction matrix: $F_{v \unlhd e} \in \mathbb{Q}^{d_e \times d_v}$

### Cochain Complexes and the Coboundary Operator
- The space of 0-cochains is $C^0(G; \mathcal{F}) = \bigoplus_{v \in V} \mathcal{F}(v) \cong \mathbb{Q}^{\dim C^0}$, where $\dim C^0 = \sum_{v \in V} d_v \le 240$.
- The space of 1-cochains is $C^1(G; \mathcal{F}) = \bigoplus_{e \in E} \mathcal{F}(e) \cong \mathbb{Q}^{\dim C^1}$, where $\dim C^1 = \sum_{e \in E} d_e \le 240$.

The **cellular coboundary operator** $\delta: C^0(G; \mathcal{F}) \to C^1(G; \mathcal{F})$ is defined on each edge $e = (u, v)$ for a 0-cochain section $x = (x_v)_{v \in V}$ by:
$$(\delta x)_e = F_{v \unlhd e} x_v - F_{u \unlhd e} x_u \in \mathbb{Q}^{d_e}$$
where the head enters with sign $+1$ and the tail enters with sign $-1$.

### Sheaf Cohomology Groups
- **Zeroth Cohomology ($H^0$, Global Sections):**
  $$H^0(G; \mathcal{F}) = \ker \delta = \{ x \in C^0(G; \mathcal{F}) : \delta x = 0 \}$$
  $$\dim H^0 = \dim C^0 - \operatorname{rank}(\delta)$$
- **First Cohomology ($H^1$, Obstruction Space):**
  $$H^1(G; \mathcal{F}) = C^1(G; \mathcal{F}) / \operatorname{im} \delta$$
  $$\dim H^1 = \dim C^1 - \operatorname{rank}(\delta)$$
- **Euler-Poincaré Formula:**
  $$\dim H^0 - \dim H^1 = \dim C^0 - \dim C^1$$

### Target Cochain Feasibility & The Fredholm Alternative
For each target 1-cochain $b \in C^1$, the solver must determine whether the linear system $\delta x = b$ is solvable:
1. **$b \in \operatorname{im} \delta$ (glues: true):** The solver must return an exact 0-cochain section $x \in C^0$ satisfying $\delta x = b$.
2. **$b \notin \operatorname{im} \delta$ (glues: false):** The solver must return an exact dual obstruction witness $\eta \in C^1$ satisfying $\delta^T \eta = 0$ (annihilating $\operatorname{im} \delta$) and $\langle \eta, b \rangle \neq 0$.

---

## 2. Coordinate Ordering Conventions

To ensure bit-level deterministic reproducibility between solver, dual checkers, and tests, cochain vectors follow a strict coordinate ordering:
1. **0-Cochains ($C^0$):**
   - Coordinates are sorted in the order declared in `case["vertices"]`.
   - Vertex $v_i$ occupies the index range $[o_V(v_i), o_V(v_i) + d_{v_i})$, where $o_V(v_i) = \sum_{j < i} d_{v_j}$.
2. **1-Cochains ($C^1$):**
   - Coordinates are sorted in the order declared in `case["edges"]`.
   - Edge $e_k$ occupies the index range $[o_E(e_k), o_E(e_k) + d_{e_k})$, where $o_E(e_k) = \sum_{l < k} d_{e_l}$.

---

## 3. Canonical Rational String Format (RFC 8785)

All rational numbers in JSON payloads must be formatted canonically:
- Integers: `"0"`, `"1"`, `"-5"` (no trailing `"/1"`, no leading `"+"`, no leading zeros like `"05"` or `"-05"`, no `"-0"`).
- Non-integer rationals: `"num/den"` where:
  - `den > 1`
  - `gcd(|num|, den) == 1` (fully reduced, e.g. `"2/4"` is rejected)
  - No negative sign in denominator
  - No explicit positive sign `"+"`
  - No decimal point `.` or scientific notation `e`
  - No whitespace anywhere in the string

---

## 4. Closed Refusal & Out-Of-Scope Catalog

### Refusal Codes (`status: "UNKNOWN"`)
1. `VERTEX_COUNT_OUT_OF_BOUNDS`: $|V| < 1$ or $|V| > 30$.
2. `EDGE_COUNT_OUT_OF_BOUNDS`: $|E| < 0$ or $|E| > 60$.
3. `STALK_DIM_OUT_OF_BOUNDS`: Any $d_v, d_e \notin [0, 4]$ or $\dim C^0 > 240$ or $\dim C^1 > 240$.
4. `COEFFICIENT_BOUND_EXCEEDED`: Any matrix coefficient $|p| > 99$ or $|q| > 99$.
5. `MALFORMED_RESTRICTION_MATRIX`: Non-canonical, non-numeric, or non-rectangular restriction matrix entries.
6. `MALFORMED_TARGET_COCHAIN`: Target cochain length $\ne \dim C^1$ or invalid rational string.
7. `MALFORMED_CASE_STRUCTURE`: Non-mapping root, missing required keys, or duplicate vertex/edge IDs.
8. `DISCONNECTED_GRAPH`: Graph has multiple components when connectivity is required.
9. `BUDGET_EXHAUSTED`: Arm inference budget exceeded before completion. This records a harness event, not an answer: it carries no witness the judge can check, so the judge never scores it as a valid result.

### Out-Of-Scope Reasons (`status: "OUT_OF_SCOPE"`)
1. `RESTRICTION_SHAPE_MISMATCH`: Restriction matrix row count $\ne d_e$ or column count $\ne d_v$.
2. `SELF_LOOP`: Edge has $u == v$.
3. `UNKNOWN_ENDPOINT`: Edge references an endpoint not declared in `vertices`.

---

## 5. Input and Output Schema

### Solved Case Output
```json
{
  "id": "ex01_solved_constant_tree",
  "status": "SOLVED",
  "h0_dim": "1",
  "h0_basis": [["1", "1", "1"]],
  "h1_dim": "0",
  "h1_complement": [],
  "targets": [
    {
      "glues": true,
      "x": ["0", "1", "2"]
    }
  ]
}
```

### Out-Of-Scope Output
```json
{
  "id": "ex17_oos_restriction_shape_mismatch",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "edge": "e1",
    "endpoint": "v0",
    "expected_shape": [2, 1],
    "actual_shape": [3, 1],
    "reason": "RESTRICTION_SHAPE_MISMATCH"
  }
}
```

### Unknown Refusal Output
```json
{
  "id": "ex19_unknown_vertex_count_out_of_bounds",
  "status": "UNKNOWN",
  "refusal": "VERTEX_COUNT_OUT_OF_BOUNDS",
  "refusal_code": "VERTEX_COUNT_OUT_OF_BOUNDS"
}
```
