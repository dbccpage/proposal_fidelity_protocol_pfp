# Task: C023 Clifford Circuit Synthesis from Tableaux

**AuthorityEffect:** None. **Protocol:** [SG-CP v1](../../01_challenge_protocol.md). **Domain:** c_quantum. **Tier:** T2.

---

## 1. Problem Definition

Given an $n$-qubit target Clifford tableau $T$ on $n$ qubits ($1 \le n \le 12$) specified by the conjugated images of the canonical generators:
- $\{T(X_0), T(X_1), \dots, T(X_{n-1})\}$
- $\{T(Z_0), T(Z_1), \dots, T(Z_{n-1})\}$
along with an integer `gate_budget` $B$:

1. **Validity & Symplecticity Check**:
   Verify that the $2n$ images satisfy the standard symplectic commutation relations:
   - $[T(X_i), T(Z_j)] \neq 0$ (they anticommute) if and only if $i = j$.
   - $[T(X_i), T(X_j)] = 0$ for all $i < j$.
   - $[T(Z_i), T(Z_j)] = 0$ for all $i < j$.
   - Dimension check: $1 \le n \le 12$.
   If any condition fails, return status `OUT_OF_SCOPE` with a certified defect witness (identifying the violating pair of generators).

2. **Circuit Synthesis**:
   Synthesize a sequence of elementary Clifford gates from the canonical gate set:
   - `["H", q]`: Hadamard gate on qubit $q$.
   - `["S", q]`: Phase gate on qubit $q$.
   - `["CNOT", c, t]`: Controlled-NOT gate with control $c$ and target $t$ ($c \neq t$).

   The circuit is applied **left-to-right**: if `circuit = [g_1, g_2, ..., g_m]`, the unitary is $U = g_m \cdots g_2 g_1$, and each operator transforms as $U P U^\dagger$.

   The conjugation actions on Pauli operators under left-to-right gate applications are:
   - **$H(q)$**:
     - $X_q \mapsto Z_q$
     - $Z_q \mapsto X_q$
     - $Y_q \mapsto -Y_q$
   - **$S(q)$**:
     - $X_q \mapsto Y_q$
     - $Y_q \mapsto -X_q$
     - $Z_q \mapsto Z_q$
   - **$\mathrm{CNOT}(c, t)$**:
     - $X_c \mapsto X_c X_t$
     - $X_t \mapsto X_t$
     - $Z_c \mapsto Z_c$
     - $Z_t \mapsto Z_c Z_t$
     - $Y_c \mapsto Y_c X_t$
     - $Y_t \mapsto Z_c Y_t$
   - Pauli corrections in the $\{H, S, \mathrm{CNOT}\}$ gate set:
     - $Z = S^2$
     - $X = H S^2 H$
     - $Y = S X S^\dagger = S H S^2 H S^3$

3. **Gate Budget & Exactness**:
   The circuit length must satisfy $m \le B$. The circuit must reproduce every target image exactly, including its sign bit ($\pm 1$).

---

## 2. Input Specification

A JSON object with schema:
```json
{
  "id": "c023_case_001",
  "num_qubits": 2,
  "gate_budget": 6,
  "images": {
    "X0": "+XX",
    "X1": "+IX",
    "Z0": "+ZI",
    "Z1": "+ZZ"
  }
}
```

- `id`: Unique case identifier string.
- `num_qubits`: Integer $n \in [1, 12]$.
- `gate_budget`: Maximum allowed gate count $B \ge 0$.
- `images`: Dictionary mapping `"X0"..."X{n-1}"` and `"Z0"..."Z{n-1}"` to Pauli strings of length $n + 1$ (sign `+` or `-`, followed by $n$ Pauli letters from `{I, X, Y, Z}`).

---

## 3. Output Specification

### Successful Synthesis (`SOLVED`)
```json
{
  "id": "c023_case_001",
  "status": "SOLVED",
  "circuit": [
    ["CNOT", 0, 1]
  ]
}
```

- `status`: `"SOLVED"`.
- `circuit`: List of gate tuples `["H", q]`, `["S", q]`, or `["CNOT", c, t]`.
- Length of circuit $\le \text{gate\_budget}$.

### Out of Scope Malformed Inputs (`OUT_OF_SCOPE`)
```json
{
  "id": "c023_case_bad",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "pair": ["X0", "Z1"],
    "expected": "commute"
  }
}
```

### Resource / Budget Refusal (`UNKNOWN`)
```json
{
  "id": "c023_case_tight",
  "status": "UNKNOWN",
  "refusal_code": "GATE_BUDGET_NOT_MET",
  "best_gate_count": 42
}
```

---

## 4. Verification Protocol

The judge packet employs dual independent checkers:
1. **Checker 1 (Exact Row-wise $\mathbb{F}_2$ Simulation)**: Fast tableau state simulator tracking $X, Z$ bit vectors and deterministic Pauli signs under Clifford conjugation.
2. **Checker 2 (Independent Dense Unitary / Backward Propagation)**: Independent verification path comparing circuit matrix action directly against the target tableau.
