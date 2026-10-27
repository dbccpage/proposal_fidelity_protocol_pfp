# C033: Weight Multiplicities of Simple Lie Algebras

**AuthorityEffect:** None. **Status:** active. **Domain:** d_physics_mtheory. **Tier:** T2.
**Budget:** $0.50 billed inference per arm ($0.05 target). **Models:** open weights, at most 70B total parameters.
**Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

---

## 1. Challenge Overview

Implement an exact mathematical solver for representations of simple Lie algebras of rank at most 4:
- $A_1, A_2, A_3, A_4$ ($SU(2), SU(3), SU(4), SU(5)$)
- $B_2, B_3, B_4$ ($SO(5), SO(7), SO(9)$)
- $C_3, C_4$ ($Sp(6), Sp(8)$)
- $D_4$ ($SO(8)$)
- $G_2$ (rank 2 exceptional)
- $F_4$ (rank 4 exceptional)

The solver must answer two fundamental representation theory query types:
1. **`character` query**: Given an integral weight $\lambda$, determine:
   - The unique dominant highest weight $\lambda^+$ (by reflecting $\lambda$ into the dominant chamber if non-dominant).
   - The exact total representation dimension $\dim V(\lambda^+)$ via the Weyl dimension formula.
   - The exact dominant weight multiplicities $m_{\lambda^+}(\mu)$ for all dominant weights $\mu \preceq \lambda^+$ via Freudenthal's recursion formula.
2. **`tensor` query**: Given two integral weights $\lambda$ and $\mu$, decompose the tensor product $V(\lambda^+) \otimes V(\mu^+)$ into irreducible components with exact Littlewood-Richardson multiplicities via the Brauer-Klimyk rule.

All calculations must be performed over exact rationals $\mathbb{Q}$ and integers $\mathbb{Z}$ using the Python standard library only (no external CAS or solver packages).

---

## 2. Bourbaki Node Ordering & Cartan Conventions

Weights are given by their Dynkin labels $[\lambda_1, \ldots, \lambda_r]$ in the Bourbaki node order, where $\lambda_i = \langle \lambda, \alpha_i^\vee \rangle = \frac{2(\lambda, \alpha_i)}{(\alpha_i, \alpha_i)}$.

A weight is dominant if and only if $\lambda_i \ge 0$ for all $i = 1, \ldots, r$.

### Cartan Matrices $A_{ij} = \langle \alpha_i, \alpha_j^\vee \rangle = \frac{2(\alpha_i, \alpha_j)}{(\alpha_j, \alpha_j)}$

- **$A_r$ ($r=1,2,3,4$)**: Standard chain $1 - 2 - \cdots - r$. $A_{i,i}=2$, $A_{i,i+1}=A_{i+1,i}=-1$. Symmetrizers: $d = [1, \ldots, 1]$.
- **$B_r$ ($r=2,3,4$)**: Node $r$ is the short root. $A_{i,i}=2$, $A_{i,i+1}=A_{i+1,i}=-1$ for $i < r-1$; $A_{r-1, r}=-2, A_{r, r-1}=-1$. Symmetrizers: $B_2: [2, 1]$, $B_3: [2, 2, 1]$, $B_4: [2, 2, 2, 1]$.
  - In $B_2$, $[1, 0]$ is the vector ($5$), and $[0, 1]$ is the spinor ($4$).
- **$C_r$ ($r=3,4$)**: Node $r$ is the long root. $A_{r-1, r}=-1, A_{r, r-1}=-2$. Symmetrizers: $C_3: [1, 1, 2]$, $C_4: [1, 1, 1, 2]$.
  - Note the label swap between $B_2$ and $C_2$: In $C_2$, $[1, 0]$ is the fundamental ($4$), and $[0, 1]$ is the vector ($5$).
- **$D_4$**: Node 2 is the central branching node: $A_{2,1}=A_{1,2}=-1$, $A_{2,3}=A_{3,2}=-1$, $A_{2,4}=A_{4,2}=-1$. Symmetrizers: $d = [1, 1, 1, 1]$.
  - Triality permutes outer nodes 1 (vector $8_v$), 3 (spinor $8_s$), and 4 (conjugate spinor $8_c$), leaving adjoint $[0, 1, 0, 0]$ ($28$) fixed.
- **$G_2$**: Node 1 is short, node 2 is long. $A = \begin{pmatrix} 2 & -1 \\ -3 & 2 \end{pmatrix}$. Symmetrizers: $d = [1, 3]$.
  - $[1, 0]$ is the fundamental ($7$), $[0, 1]$ is the adjoint ($14$).
- **$F_4$**: Nodes 1, 2 are long, nodes 3, 4 are short. Symmetrizers: $d = [2, 2, 1, 1]$.
  - $[0, 0, 0, 1]$ is the minimal representation ($26$), $[1, 0, 0, 0]$ is the adjoint ($52$).

---

## 3. Mathematical Formulas

### 1. Simple Reflections
The $i$-th simple reflection on Dynkin labels $w = [w_1, \ldots, w_r]$ acts by:
$$(s_i(w))_j = w_j - w_i A_{ij}$$

### 2. Weyl Dimension Formula
$$\dim V(\lambda) = \prod_{\alpha > 0} \frac{(\lambda + \rho, \alpha)}{(\rho, \alpha)}$$
where $\rho = [1, 1, \ldots, 1]$, and for any root $\alpha = \sum_j c_j \alpha_j$, $(\lambda, \alpha) = \sum_j c_j d_j \lambda_j$.

### 3. Freudenthal's Recursion Formula
For any dominant weight $\mu \prec \lambda$:
$$(\|\lambda + \rho\|^2 - \|\mu + \rho\|^2) m_\lambda(\mu) = 2 \sum_{\alpha > 0} \sum_{k=1}^\infty (\mu + k\alpha, \alpha) m_\lambda(\mu + k\alpha)$$
where the denominator scalar is exact:
$$\|\lambda + \rho\|^2 - \|\mu + \rho\|^2 = \sum_{j=1}^r k_j d_j (\lambda_j + \mu_j + 2) > 0$$
for $\lambda - \mu = \sum_j k_j \alpha_j$.

### 4. Brauer-Klimyk Rule
For tensor products:
$$V(\lambda) \otimes V(\mu) = \bigoplus_{\nu \in \text{wt}(\mu)} m_\mu(\nu) V(\lambda + \nu)$$
where $\gamma = \lambda + \nu + \rho$ is reflected into the dominant chamber via Weyl reflections:
- If $\gamma$ lies on a Weyl chamber wall (any label is 0 under reflection), its contribution is 0.
- Otherwise, $w(\gamma)$ is strictly dominant (all labels $\ge 1$), contributing $(-1)^{\ell(w)} V(w(\gamma) - \rho)$.

---

## 4. Input & Output Schemas

### Input Query: `character`
```json
{
  "case_id": "la_04",
  "algebra": "A2",
  "query": "character",
  "weight": [1, 1]
}
```

### Output: `character` SOLVED
```json
{
  "id": "la_04",
  "status": "SOLVED",
  "highest_weight": [1, 1],
  "dimension": 8,
  "dominant_multiplicities": [
    [[1, 1], 1],
    [[0, 0], 2]
  ]
}
```

### Input Query: `tensor`
```json
{
  "case_id": "la_05",
  "algebra": "G2",
  "query": "tensor",
  "left": [1, 0],
  "right": [1, 0]
}
```

### Output: `tensor` SOLVED
```json
{
  "id": "la_05",
  "status": "SOLVED",
  "decomposition": [
    [[2, 0], 1],
    [[1, 0], 1],
    [[0, 1], 1],
    [[0, 0], 1]
  ]
}
```

### Boundary & Refusal Outputs
- **`OUT_OF_SCOPE`**: Non-integral label (`kind: "non_integral_label"`), unsupported algebra (`kind: "unsupported_algebra"`).
- **`UNKNOWN`**: Dimension bound exceeded ($> 10^6$, `refusal_code: "DIMENSION_OUT_OF_BOUNDS"`), malformed case (`refusal_code: "MALFORMED_CASE_STRUCTURE"`), invalid query (`refusal_code: "INVALID_QUERY_TYPE"`), weight dimension mismatch (`refusal_code: "WEIGHT_DIMENSION_MISMATCH"`).
