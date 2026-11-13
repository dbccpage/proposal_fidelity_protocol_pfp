# Task: Challenge C055 — Assignment Problems with Dual Potentials

## Formal Problem

Given an $n \times n$ cost matrix $C$ with $1 \le n \le 60$, integer entries $|c_{ij}| \le 10^{18}$, and `null` marking forbidden pairs, along with optional optimization sense `"sense": "min"` (default) or `"sense": "max"`:

1. **If a perfect matching of allowed entries exists (OPTIMAL):**
   Compute:
   - A permutation $\sigma$ of $\{0, \dots, n-1\}$ using only allowed entries ($C[i][\sigma(i)] \ne \text{null}$).
   - Dual potentials $u \in \mathbb{Z}^n$ and $v \in \mathbb{Z}^n$ satisfying:
     - For minimization:
       $$u_i + v_j \le c_{ij} \quad \text{for every allowed } (i, j)$$
       $$\sum_{i=0}^{n-1} u_i + \sum_{j=0}^{n-1} v_j = \sum_{i=0}^{n-1} c_{i,\sigma(i)} = \text{value}$$
     - For maximization:
       Potentials certify the negated problem (costs $c' = -c$, minimizing $c'$ with $u_i + v_j \le -c_{ij}$ and $\sum u + \sum v = -\text{value}$) or equivalently $u_i + v_j \ge c_{ij}$ with $\sum u + \sum v = \text{value}$.
   - The total optimal assignment value.

2. **If no perfect matching of allowed entries exists (NO_PERFECT_ASSIGNMENT):**
   Compute a certified Hall violator row subset $S \subset \{0, \dots, n-1\}$ satisfying:
   $$|N(S)| < |S|$$
   where $N(S) = \{ j \mid \exists i \in S, C[i][j] \ne \text{null} \}$ is the set of columns accessible to rows in $S$.

3. **If the matrix is MALFORMED or OUT OF SCOPE (non-square, ragged rows, non-numeric entries, Boolean entries, or a `sense` other than `"min"` or `"max"`):**
   Return status `"OUT_OF_SCOPE"`.

## Output Format

RFC 8785 JSON:
```json
{
  "case_id": "as_ex_01",
  "status": "SOLVED",
  "kind": "OPTIMAL",
  "sigma": [1, 0, 2],
  "u": ["3", "2", "2"],
  "v": ["0", "-2", "0"],
  "value": "5"
}
```
For infeasible matrices:
```json
{
  "case_id": "as_ex_04",
  "status": "SOLVED",
  "kind": "NO_PERFECT_ASSIGNMENT",
  "hall_rows": [0, 1]
}
```
For malformed matrices:
```json
{
  "case_id": "as_ex_12",
  "status": "OUT_OF_SCOPE",
  "witness": {"reason": "ROW_LENGTH_MISMATCH"}
}
```
