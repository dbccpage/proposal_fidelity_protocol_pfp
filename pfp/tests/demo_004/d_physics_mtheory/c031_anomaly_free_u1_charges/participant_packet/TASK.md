# TASK: Anomaly-Free Chiral U(1) Charge Assignments (C031)

**Domain:** `d_physics_mtheory`  
**Protocol:** SG-CP v1 (Symbol Game Challenge Protocol)  
**Tier:** T3 (Hard ceiling: $1.00, Optimization target: $0.05, Open weights <= 70B parameters)  
**AuthorityEffect:** None  

---

## 1. Physical & Mathematical Foundations

In a four-dimensional $U(1)$ gauge theory coupled to $n$ left-handed Weyl fermions carrying integer charges $q_i \in \mathbb{Z} \setminus \{0\}$, quantum anomaly cancellation requires simultaneous vanishing of the mixed gauge-gravitational and cubic gauge anomalies:

1. **Linear mixed gauge-gravitational anomaly:**
   $$\sum_{i=1}^n q_i = 0$$

2. **Cubic gauge anomaly:**
   $$\sum_{i=1}^n q_i^3 = 0$$

### 1.1 Physical Invariants

- **Non-zero Integer Charges:** Every charge is a non-zero integer $q_i \in [-Q, Q] \setminus \{0\}$.
- **Primitivity:** The charge spectrum must be primitive:
  $$\gcd(|q_1|, |q_2|, \dots, |q_n|) = 1$$
  Excludes global lattice rescalings ($g > 1$).
- **Chirality vs. Vector-Like Triviality:**
  A charge assignment is **vector-like** if its multiset equals its negation:
  $$\operatorname{Counter}(q_1, \dots, q_n) = \operatorname{Counter}(-q_1, \dots, -q_n)$$
  In a vector-like spectrum, every positive charge pairs with an opposite charge ($q, -q$), allowing gauge-invariant Dirac mass terms without symmetry breaking.
  A spectrum is **chiral** if and only if:
  $$\operatorname{Counter}(q_1, \dots, q_n) \neq \operatorname{Counter}(-q_1, \dots, -q_n)$$
  Vector-like solutions are strictly rejected.

### 1.2 Canonical Representative Rule

The physical symmetry group acting on assignments is $S_n \times \mathbb{Z}_2$ (fermion permutation and global charge conjugation $q \mapsto -q$). The canonical representative is defined as:
$$\operatorname{canonical}(q) = \min(\operatorname{sort}(q), \operatorname{sort}(-q)) \quad \text{(lexicographical order)}$$
For example, for charges $(1, 5, -7, -8, 9)$:
- $\operatorname{sort}(q) = [-8, -7, 1, 5, 9]$
- $\operatorname{sort}(-q) = [-9, -5, -1, 7, 8]$
- Since $-9 < -8$, the canonical representative is strictly $[-9, -5, -1, 7, 8]$.

### 1.3 Algebraic Identity for $n \le 4$

For $n \le 4$, no chiral integer solution exists. With $q_4 = -(q_1 + q_2 + q_3)$, the cubic sum factors identically as:
$$(a + b + c)^3 - a^3 - b^3 - c^3 = 3(a + b)(b + c)(c + a) = 0$$
Over the non-zero integers, this forces at least one pair sum to vanish, collapsing all solutions into vector-like pairs $\{q_1, -q_1, q_3, -q_3\}$. Thus for $n \le 4$, the chiral solution count is always 0.

---

## 2. Query Modalities

The frozen module interface is:
```python
def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    ...
```

The solver must support two query types:

1. **`enumerate`** ($n \le 10, Q \le 12$):
   Given $n$ and bound $Q$, find every distinct canonical chiral primitive assignment and return `count` and the lexicographically sorted list `solutions`.
2. **`complete`** ($n \le 12, Q \le 2\cdot 10^6$):
   Given $k$ fixed charges ($1 \le k < n$), find $n - k$ further non-zero charges within bound $Q$ such that the combined multiset forms a primitive chiral solution, or state `claim: "NO_COMPLETION"`.

---

## 3. Schemas & Refusal Catalog

### 3.1 Input Wire Schemas

```json
// Enumerate Query
{"id": "u1_01", "query": "enumerate", "n": 5, "bound": 10}

// Complete Query
{"id": "u1_02", "query": "complete", "n": 7, "bound": 10, "fixed": [5, -8, 2]}
```

### 3.2 Output Wire Schemas

```json
// Enumerate Output
{
  "id": "u1_01",
  "status": "SOLVED",
  "count": 2,
  "solutions": [
    [-10, -4, -2, 7, 9],
    [-9, -5, -1, 7, 8]
  ]
}

// Complete Output (Solvable)
{
  "id": "u1_02",
  "status": "SOLVED",
  "completion": [1, -7, 9, -2]
}

// Complete Output (Certified Impossible)
{
  "id": "u1_03",
  "status": "SOLVED",
  "completion": null,
  "claim": "NO_COMPLETION"
}

// OUT_OF_SCOPE Output (Parameter Domain Violation)
{
  "id": "u1_04",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "fixed_charge_exceeds_bound",
    "index": 1,
    "charge": 15,
    "bound": 10
  }
}

// UNKNOWN Output (Malformed Structure or Out-Of-Bounds Refusal)
{
  "id": "u1_05",
  "status": "UNKNOWN",
  "refusal_code": "BOUND_OUT_OF_BOUNDS"
}
```

### 3.3 Closed Refusal Catalog

- **`MALFORMED_CASE_STRUCTURE`**: Non-dictionary input, missing required keys, or non-integer charges.
- **`MALFORMED_QUERY_TYPE`**: Query is not `"enumerate"` or `"complete"`.
- **`N_OUT_OF_BOUNDS`**: $n < 1$ or ($n > 10$ for `enumerate`) or ($n > 12$ for `complete`).
- **`BOUND_OUT_OF_BOUNDS`**: Bound $< 1$ or ($> 12$ for `enumerate`) or ($> 2\cdot 10^6$ for `complete`).
- **`SEARCH_NOT_FINISHED`**: Search timeout (permitted only on large bounds $Q \ge 10^5$).
- **`INVALID_CHARGE_SPECTRUM`**: Invariant violation in proposed spectrum.
- **`VECTOR_LIKE_TRIVIAL`**: Multiset is vector-like.
- **`NON_PRIMITIVE_SPECTRUM`**: GCD of charges is $> 1$.
- **`BOUND_EXCEEDED`**: Charge magnitude exceeds bound $Q$.
- **`NO_COMPLETION`**: Certified non-existence of chiral primitive completion.

Structured OUT_OF_SCOPE Witness Kinds:
- `fixed_charge_exceeds_bound`: A fixed charge $|f_i| > Q$.
- `fixed_charge_zero`: A fixed charge $f_i = 0$.
- `too_many_fixed_charges`: Number of fixed charges $\ge n$.

---

## 4. Claim Hygiene & Epistemic Boundaries

- **What this evaluates:** Whether a solver can systematically enumerate and complete integer solutions to the Diophantine system $\sum q_i = 0, \sum q_i^3 = 0$ under primitivity, chirality, and canonical sorting within declared bounds.
- **What this does not evaluate:** Real-world phenomenology, string vacuum selection, dark sector U(1) gauge groups, or continuum field theories.
- **Narrowest defensible claim:** "The candidate algorithm correctly identified or completed chiral anomaly-free integer charge assignments on the evaluated queries."
