# Task: Challenge C054 — Exact Linear Systems with Inconsistency Witnesses

## Formal Problem

Given a matrix $A \in \mathbb{Q}^{m \times n}$ and vector $b \in \mathbb{Q}^m$ ($0 \le m, n \le 40$) with rational entries `p/q` or integers `c`:

1. **If the system $A x = b$ is CONSISTENT:**
   Compute:
   - A particular rational solution vector $x \in \mathbb{Q}^n$ satisfying:
     $$A x = b$$
   - A certified nullspace basis $N \in \mathbb{Q}^{n \times (n-r)}$ as a list of $n-r$ column vectors satisfying:
     $$A N = 0$$
   - The matrix rank $r = \operatorname{rank}(A) \in [0, \min(m, n)]$.
   - A rank certificate minor: row indices $R$ and column indices $K$ with $|R| = |K| = r$ such that:
     $$\det A[R, K] \ne 0$$
   - A nullspace minor: row indices $J \subset \{0, \dots, n-1\}$ with $|J| = n - r$ such that:
     $$\det N[J, :] \ne 0$$
   - Dimensional invariant: $\operatorname{rank} + \operatorname{len}(\operatorname{null\_basis}) = n$.

2. **If the system $A x = b$ is INCONSISTENT:**
   Compute a certified left-null inconsistency witness vector $y \in \mathbb{Q}^m$ satisfying:
   $$y^T A = 0 \quad \text{and} \quad y^T b \ne 0$$
   (by Farkas' Lemma / Rouché-Capelli Theorem, the existence of such $y$ certifies that no solution $x$ can exist, since $0 = y^T A x = y^T b \ne 0$).

3. **If the input is MALFORMED or OUT OF SCOPE (ragged rows, dimension mismatch between $A$ and $b$, non-numeric entry):**
   Return status `"OUT_OF_SCOPE"`.

## Output Format

RFC 8785 JSON:
```json
{
  "case_id": "ls_ex_01",
  "status": "SOLVED",
  "kind": "CONSISTENT",
  "x": ["1", "0", "0"],
  "null_basis": [["-2", "1", "0"], ["-3", "0", "1"]],
  "rank": 1,
  "rank_rows": [0],
  "rank_cols": [0],
  "null_rows": [1, 2]
}
```
For inconsistent systems:
```json
{
  "case_id": "ls_ex_02",
  "status": "SOLVED",
  "kind": "INCONSISTENT",
  "y": ["-2", "1"]
}
```
For malformed or invalid inputs:
```json
{
  "case_id": "ls_ex_12",
  "status": "OUT_OF_SCOPE",
  "witness": {"reason": "ROW_LENGTH_MISMATCH", "row": 1}
}
```
