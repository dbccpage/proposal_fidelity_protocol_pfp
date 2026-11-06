# C053: Bareiss Fraction-Free Matrix Inversion

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T2.
**Budget:** $0.10 billed inference per arm. **Models:** open weights, at most 70B total parameters.
**Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen exact Bareiss fraction-free matrix inverter whose outputs carry matching determinant and adjugate certificates ($A \cdot \operatorname{adj}(A) = \det(A) I_n$), or a certified non-zero null vector proving singularity ($A v = 0, v \ne 0$), passing hidden evaluation matrices, for under $0.10.

## 2. Why This Task

Exact matrix inversion over $\mathbb{Q}$ admits a self-certifying algebraic receipt:
$$A \cdot \operatorname{adj}(A) = \det(A) \cdot I_n \quad \text{and} \quad A \cdot A^{-1} = I_n$$
A non-zero determinant together with an adjugate matrix satisfying the above equality certifies both the determinant and the exact rational inverse. Conversely, if $A$ is singular ($\det(A) = 0$), a non-zero right null vector $v \in \mathbb{Q}^n \setminus \{0\}$ satisfying $A v = 0$ provides a verifiable certificate of rank deficiency.

The Bareiss algorithm (Bareiss 1968) performs fraction-free Gaussian elimination:
$$M_{i,j}^{(k)} = \frac{M_{k,k}^{(k-1)} M_{i,j}^{(k-1)} - M_{i,k}^{(k-1)} M_{k,j}^{(k-1)}}{M_{k-1,k-1}^{(k-2)}}$$
guaranteeing exact integer divisibility at every stage when applied to integer matrices. This avoids the explosive denominator growth of naive Gaussian elimination and completely eliminates floating-point rounding drift.

## 3. Formal Problem and Bounds

The input is an $n \times n$ matrix $A \in \mathbb{Q}^{n \times n}$ with $1 \le n \le 30$. Entries are given as canonical integers or rational strings `p/q`.

- **INVERTIBLE:** The model returns `status: "SOLVED"`, `kind: "INVERTIBLE"`, the exact determinant `det`, the exact integer or cleared adjugate matrix `adjugate`, and the exact rational inverse matrix `inverse`.
- **SINGULAR:** The model returns `status: "SOLVED"`, `kind: "SINGULAR"`, `det: "0"`, and a certified non-zero null vector `null_vector` satisfying $A v = 0$ with $v \ne 0$.
- **OUT_OF_SCOPE:** Non-square matrices ($m \ne n$), malformed row lengths, or non-numeric entries.

## 4. Output Contract

RFC 8785 JSON:
```json
{
  "case_id": "bf_ex_01",
  "status": "SOLVED",
  "kind": "INVERTIBLE",
  "det": "2",
  "adjugate": [["4", "-2"], ["-1", "1"]],
  "inverse": [["2", "-1"], ["-1/2", "1/2"]]
}
```
For singular cases:
```json
{
  "case_id": "bf_ex_02",
  "status": "SOLVED",
  "kind": "SINGULAR",
  "det": "0",
  "null_vector": ["-2", "1"]
}
```
For malformed / non-square cases:
```json
{
  "case_id": "bf_ex_07",
  "status": "OUT_OF_SCOPE",
  "witness": {"reason": "NOT_SQUARE"}
}
```

## 5. Claim Hygiene

- **Supports:** A named model synthesized a frozen module that returned exact Bareiss matrix determinants, adjugates, and null vectors matching certificates across evaluated hidden test cases.
- **Does not support:** Generalization to infinite-dimensional operators or arbitrary numerical condition numbers without exact rational arithmetic.
- **Narrowest defensible claim:** For matrices up to $30 \times 30$ with exact rational entries, the solver produces verified identity products $A \cdot \operatorname{adj}(A) = \det(A) I_n$ and nullspace vectors.
- **Next test needed:** Advance to Challenge C054: Exact Linear Systems with Inconsistency Witnesses.
