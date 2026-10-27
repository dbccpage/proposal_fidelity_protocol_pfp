# Task: Challenge C053 — Bareiss Fraction-Free Matrix Inversion

## Formal Problem

Given an $n \times n$ matrix $A \in \mathbb{Q}^{n \times n}$ ($1 \le n \le 30$) with rational entries `p/q` or integers `c`:

1. **If $A$ is INVERTIBLE ($\det(A) \ne 0$):**
   Compute:
   - The exact determinant $\det(A)$ in $\mathbb{Q}$.
   - The exact adjugate matrix $\operatorname{adj}(A) \in \mathbb{Q}^{n \times n}$ satisfying:
     $$A \cdot \operatorname{adj}(A) = \operatorname{adj}(A) \cdot A = \det(A) \cdot I_n$$
   - The exact inverse matrix $A^{-1} \in \mathbb{Q}^{n \times n}$ satisfying:
     $$A \cdot A^{-1} = I_n \quad \text{where } (A^{-1})_{ij} = \frac{\operatorname{adj}(A)_{ij}}{\det(A)}$$

2. **If $A$ is SINGULAR ($\det(A) = 0$):**
   Compute:
   - `det: "0"`
   - A certified non-zero right null vector $v \in \mathbb{Q}^n \setminus \{0\}$ satisfying:
     $$A v = 0$$

3. **If $A$ is MALFORMED or OUT OF SCOPE ($m \ne n$, empty matrix, non-numeric entry):**
   Return status `"OUT_OF_SCOPE"`.

## Output Format

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
For singular matrices:
```json
{
  "case_id": "bf_ex_02",
  "status": "SOLVED",
  "kind": "SINGULAR",
  "det": "0",
  "null_vector": ["-2", "1"]
}
```
For malformed or non-square matrices:
```json
{
  "case_id": "bf_ex_07",
  "status": "OUT_OF_SCOPE",
  "witness": {"reason": "NOT_SQUARE"}
}
```
