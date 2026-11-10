# Task: C021 Q40-R Quantum Stabilizer Ground State Challenge

**AuthorityEffect:** None. **Protocol:** [SG-CP v1](../../01_challenge_protocol.md). **Domain:** c_quantum. **Tier:** T2.

---

## 1. Problem Definition

Given an $n$-qubit finite quantum system with $1 \le n \le 8$ and at most $M \le 24$ terms, determine the ground state energy and eigenspace degeneracy of the Hamiltonian:

$$H = \sum_{i=1}^M w_i \frac{I - s_i P_i}{2}$$

where:
- $n \in \{1, \dots, 8\}$ is the number of qubits.
- $P_i \in \{I, X, Y, Z\}^{\otimes n}$ is an $n$-qubit Pauli word.
- $s_i \in \{-1, +1\}$ is the target eigenvalue of term $i$.
- $w_i = [p_i, q_i] \in \mathbb{Q}^+$ is an exact positive rational weight with integers $p_i > 0$ and $q_i > 0$.

Terms may include pure identity words ($I^{\otimes n}$), repeated words, opposing target signs on the same word (frustration), and unused qubits.

---

## 2. Mathematical Formalism & Output Rules

### Commuting Family (`SOLVED`)
If every pair of terms $(P_i, P_j)$ pairwise commutes ($P_i P_j = P_j P_i$ for all $1 \le i < j \le M$), the Hamiltonian is solvable via stabilizer algebra:

1. **Independent Generator Basis**:
   Extract a maximum independent set of commuting generators $G_1, \dots, G_k$ ($k \le n$) using $\mathbb{F}_2$ Gaussian elimination on the $2n$-dimensional binary symplectic representation of the Pauli group:
   $$v(P) = (x_0, \dots, x_{n-1}, z_0, \dots, z_{n-1}) \in \mathbb{F}_2^{2n}$$
   where $I \mapsto (0, 0), X \mapsto (1, 0), Y \mapsto (1, 1), Z \mapsto (0, 1)$.
   Pure identity terms ($I^{\otimes n}$) are skipped from the generator basis.
   The `basis` list must report the input string IDs of the chosen generators.

2. **Phase-Tracked Decomposition**:
   Every term $P_i$ decomposes as:
   $$P_i = \sigma_i \prod_{j=1}^k G_j^{e_{ij}}$$
   where $e_{ij} \in \{0, 1\}$ and $\sigma_i \in \{-1, +1\}$.
   Phase tracking must strictly obey single-qubit multiplication with powers of $i \pmod 4$:
   $$Y = iXZ, \quad XY = iZ, \quad YX = -iZ, \quad XZ = -iY, \quad ZX = iY, \quad YZ = iX, \quad ZY = -iX$$
   The generator mask for term $i$ is an integer $m_i = \sum_{j=0}^{k-1} e_{ij} 2^j$.

3. **Joint Eigenvalue Assignment Search**:
   An assignment $b \in \{-1, +1\}^k$ specifies the simultaneous eigenvalues of the generators $G_1, \dots, G_k$.
   The assignment is encoded as an integer bitmask $m \in [0, 2^k - 1]$:
   - bit $j = 0 \implies b_j = +1$
   - bit $j = 1 \implies b_j = -1$
   Under assignment $b$, term $P_i$ has eigenvalue $\lambda_i = \sigma_i \prod_{j=1}^k b_j^{e_{ij}} \in \{-1, +1\}$.
   The penalty contributed by term $i$ is:
   $$\text{penalty}_i(b) = w_i \frac{1 - s_i \lambda_i}{2} = \begin{cases} 0 & \text{if } \lambda_i = s_i \\ w_i & \text{if } \lambda_i \neq s_i \end{cases}$$
   The total energy for assignment $b$ is $E(b) = \sum_{i=1}^M \text{penalty}_i(b)$.
   Identity terms contribute $w_i(1 - s_i)/2$ identically to all assignments.

4. **Ground Energy & Degeneracy**:
   - $E_0 = \min_{b} E(b) \in \mathbb{Q}$, expressed as a reduced coprime pair `[num, den]` with $den > 0$.
   - `minimizers`: sorted list of assignment bitmasks $m \in [0, 2^k - 1]$ achieving $E_0$.
   - `degeneracy`: exact integer ground eigenspace dimension:
     $$\text{degeneracy} = |\text{minimizers}| \cdot 2^{n - k}$$

### Noncommuting Family (`OUT_OF_SCOPE`)
If any pair of terms $(P_i, P_j)$ anticommutes ($P_i P_j = -P_j P_i$), the system is noncommuting and outside the stabilizer ground state scope:
- Return `status: "OUT_OF_SCOPE"`.
- Provide an explicit `witness: [id_a, id_b]` containing the string IDs of two terms that anticommute, sorted in lexicographical string order ($id_a < id_b$).

### Malformed or Out-of-Bounds (`UNKNOWN`)
If the case violates structural, schema, or bound constraints, return `status: "UNKNOWN"` with an exact refusal code from the closed list.

---

## 3. Closed Refusal List

When returning `UNKNOWN`, the `refusal_code` must be one of:

1. `NUM_QUBITS_OUT_OF_BOUNDS`: Number of qubits $n < 1$ or $n > 8$ (or not an integer).
2. `TERM_COUNT_OUT_OF_BOUNDS`: Number of terms $M < 0$ or $M > 24$ (or terms not a list).
3. `INVALID_WEIGHT`: Weight is not a 2-element integer array `[num, den]` with $num > 0$ and $den > 0$ (e.g. negative, zero, float, bool).
4. `DUPLICATE_TERM_ID`: Two or more terms have identical string `id`.
5. `MALFORMED_PAULI_WORD`: Pauli word has length $\neq n$, contains characters outside `{'I', 'X', 'Y', 'Z'}`, or is not a string.
6. `INVALID_TARGET_SIGN`: Target sign is not in $\{+1, -1\}$ (or is bool).
7. `INVALID_TERM_ID`: Term ID is missing, empty, or not a string.
8. `MALFORMED_CASE_STRUCTURE`: Input is not a JSON object or missing required keys (`id`, `n`, `terms`).

---

## 4. Input & Output JSON Schemas

### Input Schema
```json
{
  "id": "h_07",
  "n": 3,
  "terms": [
    {
      "id": "t_a",
      "P": "XYZ",
      "w": [3, 2],
      "target": 1
    },
    {
      "id": "t_b",
      "P": "ZZI",
      "w": [1, 1],
      "target": -1
    }
  ]
}
```

### Output Schema: `SOLVED`
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

### Output Schema: `OUT_OF_SCOPE`
```json
{
  "id": "ex06",
  "status": "OUT_OF_SCOPE",
  "witness": ["t_x", "t_z"]
}
```

### Output Schema: `UNKNOWN`
```json
{
  "id": "ex10",
  "status": "UNKNOWN",
  "refusal_code": "NUM_QUBITS_OUT_OF_BOUNDS"
}
```

---

## 5. Deliverable Requirements

Participants must provide a frozen Python module exposing:

```python
def solve(case: dict) -> dict:
    ...
```

- Standard library only (`fractions`, `itertools`, `dataclasses`, `json`, `math`, etc.).
- No external solvers or linear programming libraries (`scipy`, `numpy`, `cvxpy`, etc.).
- No file writes, no network calls, no subprocess spawning inside `solve`.
- Strictly adheres to the input and output JSON wire format.
