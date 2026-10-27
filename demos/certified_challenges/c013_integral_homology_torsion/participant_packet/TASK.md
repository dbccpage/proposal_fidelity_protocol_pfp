# TASK: C013 Integral Homology with Torsion and Smith Normal Form Certificates

**AuthorityEffect:** None
**Challenge ID:** `c013_integral_homology_torsion`
**Tier:** T2
**Target Inference Budget:** $< \$0.05$ (50,000 $\mu$USD)
**Hard Ceiling:** $\le \$0.50$ (500,000 $\mu$USD)
**Model Ceiling:** Open weights $\le 70\text{B}$ parameters, `allow_fallbacks: False`
**Protocol:** SG-CP v1 (Symbol Game Challenge Protocol v1)

---

## 1. Formal Problem Definition

Given a finite abstract simplicial complex $K$, given by its simplices over integer vertex labels, of dimension at most 3:
Orient each simplex $\sigma = [v_0, v_1, \dots, v_k]$ by increasing vertex label ($v_0 < v_1 < \dots < v_k$). The boundary operator $\partial_k: C_k(K; \mathbb{Z}) \to C_{k-1}(K; \mathbb{Z})$ is the standard alternating sum:
$$\partial_k [v_0, \dots, v_k] = \sum_{i=0}^k (-1)^i [v_0, \dots, \widehat{v}_i, \dots, v_k]$$

The solver must compute for each degree $n \le \dim K$:
$$H_n(K; \mathbb{Z}) \cong \mathbb{Z}^{\beta_n} \oplus \mathbb{Z}/t_1 \oplus \dots \oplus \mathbb{Z}/t_s$$
with $t_i > 1$ and strict divisibility chain $t_1 \mid t_2 \mid \dots \mid t_s$.

Here:
- $\beta_n = \dim C_n - \operatorname{rank}(\partial_n) - \operatorname{rank}(\partial_{n+1})$ is the $n$-th Betti number.
- The torsion coefficients $t_i$ are the invariant factors strictly greater than 1 of $\partial_{n+1}$.
- Euler-Poincaré theorem: $\sum_{n} (-1)^n \beta_n = \sum_n (-1)^n |K_n|$.

### Exact Unimodular Smith Normal Form (SNF) Certificates
For each non-trivial boundary map $\partial_k: C_k \to C_{k-1}$ ($k \ge 1$), the certificate must provide unimodular integer matrices $U_k$ and $V_k$, their exact integer inverses $U_k^{-1}$ and $V_k^{-1}$, and diagonal invariant factors $D_k = [d_1, \dots, d_r]$ satisfying:
1. **Unimodularity:** $U_k U_k^{-1} = I_{|K_{k-1}|}$ and $V_k V_k^{-1} = I_{|K_k|}$ (guaranteeing $\det(U_k), \det(V_k) \in \{+1, -1\}$).
2. **Smith Diagonal Factorization:** $U_k \cdot \partial_k \cdot V_k = \operatorname{diag}(D_k)$.
3. **Divisibility Chain:** $d_i > 0$ and $d_1 \mid d_2 \mid \dots \mid d_r$.

---

## 2. Bounds and Constraints

- Total simplices $|K| \le 1000$ (bound: |K| <= 1000).
- Dimension $\dim K \le 3$ (bound: dim K <= 3).
- Vertex labels: integers $v$ with $|v| \le 10000$.
- Pure Python standard library only (no external CAS/LP/SymPy/SciPy imports).
- Python standard library JSON / RFC 8785 canonical form.

---

## 3. Deliverable and Output Schema

The frozen solver `solver.py` must expose `solve(case: dict) -> dict`.

### Success Payload (`SOLVED`)
```json
{
  "id": "ex08",
  "status": "SOLVED",
  "homology": [
    {"n": "0", "betti": "1", "torsion": []},
    {"n": "1", "betti": "0", "torsion": ["2"]},
    {"n": "2", "betti": "0", "torsion": []}
  ],
  "snf": [
    {
      "boundary": "1",
      "U": [["1", ...]],
      "U_inv": [["1", ...]],
      "V": [["1", ...]],
      "V_inv": [["1", ...]],
      "D": ["1", ...]
    },
    {
      "boundary": "2",
      "U": [["1", ...]],
      "U_inv": [["1", ...]],
      "V": [["1", ...]],
      "V_inv": [["1", ...]],
      "D": ["1", "2"]
    }
  ]
}
```

### Out-of-Scope Payload (`OUT_OF_SCOPE`)
When an input complex is not closed under taking faces, the solver must identify the missing face:
```json
{
  "id": "ex19",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "missing_face": ["1", "3"],
    "of_simplex": ["1", "2", "3"]
  }
}
```

### Refusal Payload (`UNKNOWN`)
For inputs violating declared budget/bounds or schemas:
```json
{
  "id": "case_id",
  "status": "UNKNOWN",
  "refusal": "SIMPLEX_COUNT_OUT_OF_BOUNDS",
  "refusal_code": "SIMPLEX_COUNT_OUT_OF_BOUNDS"
}
```

### Closed Refusal Enum
- `SIMPLEX_COUNT_OUT_OF_BOUNDS`
- `DIMENSION_OUT_OF_BOUNDS`
- `COEFFICIENT_BOUND_EXCEEDED`
- `MALFORMED_INPUT`
- `MALFORMED_CASE_STRUCTURE`
- `CERTIFICATE_TOO_LARGE`
