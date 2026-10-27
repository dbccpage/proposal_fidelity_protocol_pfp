# C047: Recurrence and Generating-Function Discovery

**Domain:** e_formal_math
**Tier:** T2
**Protocol:** SG-CP v1

## Problem Description

Given a prefix of an integer sequence $a(0), a(1), \dots, a(N-1)$ (where $30 \le N \le 60$) and complexity bounds $(r_{\max}, d_{\max})$ ($r_{\max} \le 8, d_{\max} \le 3$), discover a minimal recurrence relation:

$$\sum_{i=0}^r p_i(n) \cdot a(n+i) = 0 \quad \text{for all } n \ge n_0$$

where each $p_i(n) = \sum_{j=0}^d c_{i,j} n^j \in \mathbb{Q}[n]$ is a polynomial with integer coefficients in ascending powers of $n$, $r \le r_{\max}$, $d \le d_{\max}$, and the leading polynomial $p_r(n) \not\equiv 0$ has no integer roots for $n \ge n_0$.

If no recurrence exists within the declared bounds, certify its absence by exhibiting a nonsingular $u \times u$ minor ($u = (r_{\max}+1)(d_{\max}+1)$) from index equations beyond the declared start range.

## Output Schema

Your solution must implement `solve(case: dict) -> dict`.

### Success (Recurrence Discovered)
```json
{
  "case_id": "seq_ex_01",
  "status": "SOLVED",
  "kind": "RECURRENCE",
  "start": 0,
  "polys": [
    ["-1"],
    ["-1"],
    ["1"]
  ]
}
```

### Absence Certified (None Within Bounds)
```json
{
  "case_id": "seq_ex_07",
  "status": "SOLVED",
  "kind": "NONE_WITHIN_BOUNDS",
  "order": 2,
  "degree": 1,
  "start_range": [0, 5],
  "minor_rows": [5, 6, 7, 8, 9, 10]
}
```

### Out of Scope (Invalid Term in Prefix)
```json
{
  "case_id": "seq_ex_09",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "reason": "NON_INTEGER_TERM",
    "index": 11
  }
}
```
