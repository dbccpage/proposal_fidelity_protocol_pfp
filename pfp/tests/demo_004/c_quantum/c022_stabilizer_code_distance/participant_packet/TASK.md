# Task: C022 Stabilizer Code Distance with Lower-Bound Certificates

**AuthorityEffect:** None. **Protocol:** [SG-CP v1](../../01_challenge_protocol.md). **Domain:** c_quantum. **Tier:** T3.

---

## 1. Problem Definition

Given an $n$-qubit stabilizer code defined by $m$ stabilizer generators $S = \langle g_1, \dots, g_m \rangle$ on $n$ qubits ($1 \le n \le 20$, $1 \le m \le n$):

1. **Validity Check**: Verify that the generators form a valid stabilizer group:
   - Pairwise commutation: $[g_i, g_j] = 0$ for all $1 \le i < j \le m$.
   - Linear independence over $\mathbb{F}_2$ under symplectic representation: $\operatorname{rank}_{\mathbb{F}_2}([g_1, \dots, g_m]) = m$.
   - Consistency: $-I^{\otimes n} \notin S$.
   If any condition fails, return status `OUT_OF_SCOPE` with a certified defect witness.

2. **Code Distance $d$ and Logical Operator $L$**:
   Compute the minimum weight $d = \min_{P \in N(S) \setminus S} \mathrm{wt}(P)$ of a non-trivial logical operator commuting with all stabilizers:
   - $P \in \mathcal{P}_n$, $P \neq I^{\otimes n}$.
   - $[P, g_i] = 0$ for all $i \in \{1, \dots, m\}$ ($P$ centralizes $S$).
   - $P \notin S$ ($P$ is not in the stabilizer group).
   Emit the canonical logical word $L$ with $\mathrm{wt}(L) = d$.

3. **Lower Bound**: The claim that no nontrivial logical operator of weight $1 \le w \le d - 1$ exists is certified by the judge, which enumerates every Pauli operator of weight below $d$. Submit `lower_bound: null`. The judge supports claims for which $\sum_{w=1}^{d-1} \binom{n}{w} 3^w \le 10^6$ (every $n \le 20$ with $d \le 5$). An earlier version of this task asked for an LRAT refutation; no LRAT checker was ever run, so that requirement has been withdrawn.

---

## 2. Input Specification

A JSON object with schema:
```json
{
  "id": "c022_case_identifier",
  "num_qubits": 7,
  "generators": [
    "+IIIXXXX",
    "+IXXIIXX",
    "+XIXIXIX",
    "+IIIZZZZ",
    "+IZZIIZZ",
    "+ZIZIZIZ"
  ]
}
```

- `num_qubits`: Integer $n \in [1, 20]$.
- `generators`: List of strings of length $n + 1$ (optional leading sign `+` or `-`, followed by $n$ Pauli characters from `{I, X, Y, Z}`).

---

## 3. Output Specification

### Successful Distance Computation (`SOLVED`)
```json
{
  "id": "c022_case_identifier",
  "status": "SOLVED",
  "distance": 3,
  "logical": "IIIIXXX",
  "lower_bound": null
}
```

- `distance`: Exact integer minimum distance $d \ge 1$.
- `logical`: Pauli string of length $n$ with weight equal to $d$, commuting with all generators and outside $S$.
- `lower_bound`: always `null`.
- `distance` is a JSON integer; booleans and floats are rejected.

### Out of Scope Malformed Inputs (`OUT_OF_SCOPE`)
```json
{
  "id": "c022_case_identifier",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "anticommuting",
    "pair": [0, 2]
  }
}
```
Witness kinds:
- `"anticommuting"`: `{"pair": [i, j]}`
- `"dependent"`: `{"linear_combination": [...]}`
- `"minus_identity"`: `{"subset": [...]}`
- `"full_rank"`: `{}` (no other fields). Use it when the generators form a valid stabilizer group with $m = n$: the code encodes $k = 0$ logical qubits, the centralizer of $S$ equals $S$, and no logical operator exists, so the distance is undefined. The judge accepts it only when $m = n$ and the generators pairwise commute and are independent.

---

## 4. Verification Protocol

The judge packet employs two checkers that share no code with each other or with the reference solver:
1. **Checker 1 (Exact Algebraic)**: Verifies the logical operator (weight, commutation with every generator, exclusion from $S$ by F2 reduction) and enumerates all Pauli operators of weight below $d$ to confirm that none is a nontrivial logical operator.
2. **Checker 2 (Independent Exhaustive)**: Repeats the enumeration with rank-based membership tests and checks the logical operator's properties.

`OUT_OF_SCOPE` is accepted only for a case that has the named defect, with a witness that exhibits it: an anticommuting pair, a nonzero F2 dependency (0/1 vector of length $m$), or a subset of generators whose product is $-I$.
