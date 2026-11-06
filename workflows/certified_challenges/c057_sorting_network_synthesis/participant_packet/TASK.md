# C057: Sorting Network Synthesis

## 1. Task Specification

Synthesize a frozen Python solver `def solve(case: dict) -> dict` that synthesizes comparator sorting networks on $n \le 12$ channels within comparator bounds $k$, adhering to mandatory prefixes and avoiding forbidden comparators. All sorting networks must be verified by the **0-1 principle**.

### The 0-1 Principle
A comparator network sorts every input sequence of arbitrary elements if and only if it sorts all $2^n$ binary sequences $\{0, 1\}^n$ (Knuth, *The Art of Computer Programming*, Vol. 3). For $n \le 12$, this requires verifying at most $2^{12} = 4,096$ binary test vectors.

---

## 2. Input JSON Format

Each case is presented as a JSON object:
```json
{
  "case_id": "sn_ex_01",
  "n": 4,
  "k": 5,
  "prefix": [],
  "forbidden": []
}
```

### Constraints:
- `case_id`: String identifier.
- `n`: Integer channel count with $4 \le n \le 12$.
- `k`: Integer comparator bound with $k \ge 0$.
- `prefix`: List of mandatory comparators $[i, j]$ with $0 \le i < j < n$ that must open the network in the exact specified order.
- `forbidden`: List of forbidden comparators $[i, j]$ with $0 \le i < j < n$ that must NOT appear anywhere in the network.

---

## 3. Output Contract

Your module must return a JSON-serializable dictionary with one of three statuses:

### A. Feasible and Solved (`SOLVED`)
When a valid sorting network of length $\le k$ is synthesized:
```json
{
  "case_id": "sn_ex_01",
  "status": "SOLVED",
  "network": [
    [0, 2],
    [1, 3],
    [0, 1],
    [2, 3],
    [1, 2]
  ]
}
```
**Certificate Invariants:**
1. Length: `len(network) <= k`.
2. Structure: Every element is a pair `[i, j]` of integers satisfying `0 <= i < j < n`.
3. Prefix: `network[:len(prefix)] == prefix`.
4. Forbidden: No comparator in `network` appears in `forbidden`.
5. 0-1 Principle: For all $2^n$ binary inputs $x \in \{0, 1\}^n$, the final values satisfy $x[0] \le x[1] \le \dots \le x[n-1]$.

### B. Proven Infeasible (`UNKNOWN`)
The judge accepts `UNKNOWN` only when no admissible network exists and `code` names one of these proofs, and that proof holds on the case:

1. `BOUND_BELOW_PREFIX_LENGTH`: $k$ is below the length of the prefix;
2. `BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND`: $k < \lceil \log_2(n!) \rceil$;
3. `BOUND_BELOW_PROVEN_OPTIMAL_SIZE`: $k$ is below the proven optimal size for $n$ (5, 9, 12, 16, 19, 25, 29, 35, 39 for $n = 4, \dots, 12$). This table is taken from the literature and is trusted, not re-verified, by the judge: Floyd and Knuth for $n \le 8$; Codish, Cruz-Filipe, Frank and Schneider-Kamp for $n = 9, 10$; Harder for $n = 11, 12$;
4. `FORBIDDEN_ADJACENT_COMPARATOR`: `forbidden` contains an adjacent comparator $[i, i+1]$ (every sorting network contains every adjacent comparator).

When several proofs hold, any one of them is accepted. A missing, generic or wrong code (for example `NO_NETWORK_FOUND_WITHIN_BOUND`, or `BOUND_BELOW_PREFIX_LENGTH` when the prefix fits) is scored as a failure, as is `UNKNOWN` on a feasible case. A prefix or a forbidden list is not by itself a proof. Warranted refusals are counted apart from constructive solutions.

(Corrections, 2026-09-29: earlier versions of the judge accepted `UNKNOWN` on any case with a prefix or a forbidden list, and then on any infeasible case whatever its `code`.)
```json
{
  "case_id": "sn_ex_09",
  "status": "UNKNOWN",
  "code": "BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND"
}
```

### C. Out of Scope (`OUT_OF_SCOPE`)
When the input case violates problem preconditions (e.g. $n < 4$ or $n > 12$, negative $k$, non-integer wires, $i \ge j$, or prefix contains a forbidden comparator):
```json
{
  "case_id": "sn_ex_12",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "reason": "PREFIX_COMPARATOR_NOT_ORDERED",
    "index": 0
  }
}
```

---

## 4. Verification & Testing

Use `runner.py` to evaluate your solver against the 14 public examples in `examples/`.
The judge verifies solutions using both bit-parallel 0-1 evaluation and independent random integer stress testing.
