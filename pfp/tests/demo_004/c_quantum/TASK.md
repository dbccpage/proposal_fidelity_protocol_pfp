# Task C021: Q40-R — The ChatGPT Stabilizer Challenge Run as Specified

**AuthorityEffect:** None. **Protocol:** SG-CP v1. **Domain:** c_quantum. **Tier:** T2.

## 1. Problem Formulation

Input: $n$ qubits with $1 \le n \le 8$ and $M \le 24$ terms. The Hamiltonian is:
$$H = \sum_{i=1}^M \frac{w_i}{2} (I - s_i P_i)$$
where $P_i \in \{I, X, Y, Z\}^{\otimes n}$ is an $n$-qubit Pauli word, $s_i \in \{-1, +1\}$ is the target eigenvalue, and $w_i = \frac{p_i}{q_i} \in \mathbb{Q}^+$ ($p_i, q_i > 0$).

### Classification Outcomes
1. **`SOLVED`**: If every pair $(P_i, P_j)$ commutes, find an independent generator set $G_1, \dots, G_k$ ($k \le n$), exact signed decompositions $P_i = \sigma_i \prod_{j=1}^k G_j^{e_{ij}}$ ($\sigma_i \in \{\pm 1\}$), exact ground-state energy $E_0 \in \mathbb{Q}$, and full ground eigenspace degeneracy:
   $$\text{degeneracy} = |\operatorname{argmin}| \cdot 2^{n - k}$$
   where the energy of an assignment $b \in \{\pm 1\}^k$ is:
   $$E(b) = \sum_{i=1}^M \frac{w_i}{2} \left(1 - s_i \sigma_i \prod_{j=1}^k b_j^{e_{ij}}\right)$$
2. **`OUT_OF_SCOPE`**: If any pair $(P_i, P_j)$ anticommutes, return the lexicographically sorted pair of term IDs as witness.
3. **`UNKNOWN`**: If the case is malformed or outside the bounds ($n > 8$, $M > 24$, nonpositive weight, weight not a `[num, den]` pair, word length $\neq n$, duplicate term `id`), return an explicit refusal code.

## 2. Wire & Canonical JSON Contract

### Input JSON Schema
```json
{
  "id": "h_07",
  "n": 3,
  "terms": [
    {"id": "t_a", "P": "XYZ", "w": [3, 2], "target": 1},
    {"id": "t_b", "P": "ZZI", "w": [1, 1], "target": -1}
  ]
}
```

### Output JSON Shapes

**Solved Case:**
```json
{
  "id": "h_07",
  "status": "SOLVED",
  "energy": [0, 1],
  "degeneracy": 2,
  "basis": ["t_a", "t_b"],
  "decomposition": [
    {"id": "t_a", "mask": 1, "phase": 1},
    {"id": "t_b", "mask": 2, "phase": 1}
  ],
  "minimizers": [2]
}
```

**Out of Scope Case (Anticommuting Terms):**
```json
{
  "id": "h_08",
  "status": "OUT_OF_SCOPE",
  "witness": ["t_a", "t_c"]
}
```

**Refusal Case (Malformed / Out of Bounds):**
```json
{
  "id": "h_09",
  "status": "UNKNOWN",
  "refusal_code": "NUM_QUBITS_OUT_OF_BOUNDS"
}
```

### Closed List of Refusal Codes
- `NUM_QUBITS_OUT_OF_BOUNDS` ($n < 1$ or $n > 8$)
- `TERM_COUNT_OUT_OF_BOUNDS` ($M < 0$ or $M > 24$)
- `DUPLICATE_TERM_ID` (two terms share the same `id`)
- `INVALID_PAULI_WORD` (character not in `{I, X, Y, Z}` or length $\neq n$)
- `INVALID_WEIGHT` (non-positive, non-integer, or denominator $\le 0$)
- `INVALID_TARGET` (target not in $\{-1, 1\}$)
- `BUDGET_EXHAUSTED` (execution cost exceeded declared ceiling)
