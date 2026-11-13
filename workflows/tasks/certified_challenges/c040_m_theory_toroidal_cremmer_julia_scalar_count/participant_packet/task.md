# Challenge C040: M-Theory on Tori — Cremmer-Julia Scalar Counting

AuthorityEffect: None. Status: active. Domain: d_physics_mtheory. Tier: T4.
Budget: $2.00 billed inference ceiling, $0.20 target cost. Models: open weights, at most 70B total parameters.
Protocol: SG-CP v1.

## 1. Challenge Overview

Eleven-dimensional supergravity compactified on a $k$-dimensional torus $T^k$ ($1 \le k \le 8$, spacetime dimension $D = 11 - k$) possesses the hidden Cremmer-Julia global exceptional symmetry $E_{k(k)}$ whose scalar fields parametrize the Riemannian symmetric coset space $E_{k(k)} / K$, where $K$ is the maximal compact subgroup.

This challenge evaluates whether an open-weights model ($\le 70\text{B}$) can synthesize the dimensional reduction of eleven-dimensional supergravity and verify agreement between two decoupled mathematical routes:
1. **Field-Theoretic Reduction & Hodge Dualization:** Direct combinatorial field counting of the metric $g_{MN}$ and 3-form potential $C_{MNP}$ decomposed onto $T^k$, combined with spacetime Hodge dualization in $D = 11 - k$ dimensions.
2. **Lie Algebra & Representation Theory:** Exact Cartan decomposition of the split real form $\mathfrak{e}_{k(k)} = \mathfrak{k} \oplus \mathfrak{p}$, demonstrating that the scalar coset dimension $\dim \mathfrak{p} = \dim E_{k(k)} - \dim K$ matches the total scalar count, alongside the adjoint representation branching under $K$.

## 2. 11D Supergravity Field Content

In eleven dimensions ($M, N = 0, \dots, 10$), the on-shell field content consists of:
- Spacetime metric $g_{MN}$: $11 \times 12 / 2 - 1 - 21 = 44$ on-shell physical degrees of freedom.
- 3-form gauge field $C_{MNP}$: $\binom{9}{3} = 84$ on-shell physical degrees of freedom.
- Gravitino $\Psi_M$: 128 on-shell fermionic degrees of freedom ($16 \times 8 = 128$).
Total bosonic degrees of freedom: $44 + 84 = 128$, matching the 128 fermionic degrees of freedom.

## 3. Toroidal Reduction on $T^k$ ($D = 11 - k$)

Under compactification on a flat torus $T^k$ with coordinates $y^i$ ($i = 1, \dots, k$) and noncompact spacetime coordinates $x^\mu$ ($\mu = 0, \dots, D-1$):

### Metric Decomposition:
- Internal metric components $g_{ij}$: $\frac{k(k+1)}{2}$ scalar fields.
- Off-diagonal components $g_{\mu i}$: $k$ Kaluza-Klein vector gauge bosons in $D$ dimensions.
- Spacetime metric $g_{\mu\nu}$: graviton in $D$ dimensions.

### 3-Form Field Decomposition:
- Internal components $C_{ijk}$: $\binom{k}{3}$ scalar fields.
- 1-index internal components $C_{\mu ij}$: $\binom{k}{2}$ vector fields.
- 2-index internal components $C_{\mu\nu i}$: $k$ two-form potentials.
- Pure spacetime component $C_{\mu\nu\rho}$: 1 three-form potential.

## 4. Spacetime Hodge Dualization Rules in $D$ Dimensions

In $D$ spacetime dimensions, a $p$-form gauge potential $A_p$ has an exterior field strength $F_{p+1} = d A_p$ of degree $p+1$. The Hodge dual field strength $*F_{p+1}$ has degree $D - (p + 1) = D - p - 1$.
The dual gauge potential $\tilde{A}$ satisfies $d\tilde{A} = *F$, hence its potential degree is $(D - p - 2)$.

### Dualization to Scalar (0-Form):
A $p$-form potential dualizes to a scalar if and only if:
$$D - p - 2 = 0 \iff p = D - 2$$

- For $D = 5$ ($k = 6$): $p = 5 - 2 = 3$. The spacetime 3-form $C_{\mu\nu\rho}$ dualizes to 1 scalar.
- For $D = 4$ ($k = 7$): $p = 4 - 2 = 2$. The $k=7$ two-form potentials $C_{\mu\nu i}$ dualize to 7 scalars.
- For $D = 3$ ($k = 8$): $p = 3 - 2 = 1$. All vector fields in $D=3$ dualize to scalars!
  - 8 Kaluza-Klein vectors $g_{\mu i}$ dualize to 8 scalars.
  - 28 vectors $C_{\mu ij}$ dualize to 28 scalars.
  - Two-forms carry no propagating local degrees of freedom in $D=3$.
- For $D \ge 6$ ($k \le 5$): No differential forms dualize to scalars because $p = D - 2 \ge 4$, whereas 11D supergravity possesses no potentials of degree $\ge 4$.

### Dualization to Vector (1-Form):
A $p$-form potential dualizes to a vector field if and only if:
$$D - p - 2 = 1 \iff p = D - 3$$

- For $D = 6$ ($k = 5$): $p = 6 - 3 = 3$. The 3-form $C_{\mu\nu\rho}$ dualizes to 1 vector ($5 + 10 + 1 = 16$).
- For $D = 5$ ($k = 6$): $p = 5 - 3 = 2$. The 6 two-forms $C_{\mu\nu i}$ dualize to 6 vectors ($6 + 15 + 6 = 27$).
- For $D = 4$ ($k = 7$): Vectors have $p=1$, which are self-dual in $D=4$ (28 electric vectors, 56 with magnetic duals).
- For $D = 3$ ($k = 8$): 0 propagating vectors (all dualized to scalars).

## 5. Pinned Series: Exceptional Symmetries $E_{k(k)}$ and Maximal Compact Subgroups $K$

| $k$ | $D$ | $E_{k(k)}$ ($G$) | $\dim G$ | $K$ (Maximal Compact) | $\dim K$ | Scalar Coset $\dim(G/K)$ | Adjoint Branching $\operatorname{Adj}(K) \oplus \mathfrak{p}$ |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 10 | $\mathbb{R}^+$ | 1 | $\{1\}$ | 0 | 1 | $\mathbf{1} \to \mathbf{1}$ |
| 2 | 9 | $SL(2, \mathbb{R}) \times \mathbb{R}^+$ | 4 | $SO(2)$ | 1 | 3 | $\mathbf{3} \oplus \mathbf{1} \to \mathbf{1} \oplus \mathbf{3}$ |
| 3 | 8 | $SL(3, \mathbb{R}) \times SL(2, \mathbb{R})$ | 11 | $SO(3) \times SO(2)$ | 4 | 7 | $(\mathbf{8}, \mathbf{1}) \oplus (\mathbf{1}, \mathbf{3}) \to (\mathbf{3}, \mathbf{1}) \oplus (\mathbf{1}, \mathbf{1}) \oplus \mathbf{7}$ |
| 4 | 7 | $SL(5, \mathbb{R})$ | 24 | $SO(5)$ | 10 | 14 | $\mathbf{24} \to \mathbf{10} \oplus \mathbf{14}$ |
| 5 | 6 | $SO(5, 5)$ | 45 | $SO(5) \times SO(5)$ | 20 | 25 | $\mathbf{45} \to (\mathbf{10}, \mathbf{1}) \oplus (\mathbf{1}, \mathbf{10}) \oplus (\mathbf{5}, \mathbf{5})$ |
| 6 | 5 | $E_{6(6)}$ | 78 | $USp(8)$ | 36 | 42 | $\mathbf{78} \to \mathbf{36} \oplus \mathbf{42}$ |
| 7 | 4 | $E_{7(7)}$ | 133 | $SU(8)$ | 63 | 70 | $\mathbf{133} \to \mathbf{63} \oplus \mathbf{70}$ ($\wedge^4(\mathbf{8})$) |
| 8 | 3 | $E_{8(8)}$ | 248 | $SO(16)$ | 120 | 128 | $\mathbf{248} \to \mathbf{120} \oplus \mathbf{128}$ (chiral spinor $\mathbf{128}_s$) |

## 6. Query Schemas & Response Specifications

Each case input supplies:
- `"id"`: string identifier (e.g. `"base_01_scalars_k1"`).
- `"k"`: integer torus dimension ($1 \le k \le 8$).
- `"query"`: string specifying query type: `"scalars"`, `"coset"`, `"branching"`, or `"vectors"`.

### Query 1: `"scalars"`
Returns the exact integer count of scalar fields partitioned by origin:
```json
{
  "id": "base_07_scalars_k7",
  "status": "SOLVED",
  "k": 7,
  "D": 4,
  "scalars": {
    "metric": 28,
    "three_form": 35,
    "dual_C_mu_nu_i": 7,
    "total": 70
  }
}
```

### Query 2: `"coset"`
Returns group names and exact dimensions for $E_{k(k)}$ and $K$:
```json
{
  "id": "base_15_coset_k7",
  "status": "SOLVED",
  "k": 7,
  "D": 4,
  "coset": {
    "G": "E7(7)",
    "dimG": 133,
    "K": "SU(8)",
    "dimK": 63,
    "difference": 70
  }
}
```

### Query 3: `"branching"`
Returns the decomposition of the adjoint representation of $E_{k(k)}$ under $K$ into a list of `[label, dimension]` pairs:
```json
{
  "id": "base_23_branching_k7",
  "status": "SOLVED",
  "k": 7,
  "D": 4,
  "branching": [
    ["adjoint(SU(8))", 63],
    ["wedge4(8)", 70]
  ]
}
```

### Query 4: `"vectors"`
Returns the exact count of propagating vector fields in $D$ dimensions:
```json
{
  "id": "base_28_vectors_k4",
  "status": "SOLVED",
  "k": 4,
  "D": 7,
  "vectors": {
    "metric_kk": 4,
    "three_form": 6,
    "dual_forms": 0,
    "total": 10
  }
}
```

## 7. Refusal Protocol

- For inputs where $k < 1$ or $k > 8$, or $k$ is not an exact integer (e.g. floats, booleans):
  ```json
  {
    "id": "case_id",
    "status": "UNKNOWN",
    "refusal_code": "K_OUT_OF_BOUNDS"
  }
  ```
- For inputs where `"query"` is not in `{"scalars", "coset", "branching", "vectors"}`:
  ```json
  {
    "id": "case_id",
    "status": "UNKNOWN",
    "refusal_code": "UNKNOWN_QUERY_TYPE"
  }
  ```
- No cases in this challenge are `OUT_OF_SCOPE`: every integer $1 \le k \le 8$ has an exact mathematical solution.
