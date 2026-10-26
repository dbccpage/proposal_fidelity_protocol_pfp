# C030: Tensor-Network Contraction Order Under a Cost Bound

**Protocol:** SG-CP v1 (§3, §4)  
**Tier:** T3 ($1.00 hard cost ceiling, $0.05 target budget)  
**Domain:** `c_quantum`  
**AuthorityEffect:** None

---

## 1. Problem Statement

Given a tensor network with up to 30 tensors, determine a pairwise contraction sequence such that:
1. The exact replayed contraction cost is $\le B$ (`cost_bound`).
2. Every intermediate tensor size is $\le S$ (`size_bound`), if $S$ is specified.
3. If no sequence meeting the bounds exists, return `UNKNOWN` with `refusal_code: "BOUND_NOT_MET"`. The judge accepts this answer only when infeasibility is verified:
   - for $N \le 12$, by the judge's exact dynamic-programming optimum;
   - for $N > 12$, only with a `witness`. The last contraction step of every order produces the tensor that carries all open legs, and its cost includes every open leg, so with $P$ the product of the open-leg dimensions the judge accepts `{"kind": "open_legs_exceed_size_bound", "open_size": "<P>"}` when $P > S$ and `{"kind": "open_legs_exceed_cost_bound", "open_size": "<P>"}` when $P > B$. An `UNKNOWN` for $N > 12$ without such a witness is rejected, because a search that fails to find an order does not show that none exists.
4. If the input network is malformed (hyperedges where an index appears in $\ge 3$ tensors, dimensions $< 2$, duplicate indices in a single tensor, or $N > 30$), return `OUT_OF_SCOPE` with a structured witness.

---

## 2. Contraction Arithmetic and Rules

### Definitions
- Each tensor has a list of index names.
- Each index $e$ has an integer dimension $\text{dim}(e) \ge 2$.
- Every index appears in either 1 tensor (an open physical leg) or 2 tensors (a contracted bond). Hyperedges (index appearing in $\ge 3$ tensors) are forbidden.
- When contracting tensor $X$ (indices $I$) and tensor $Y$ (indices $J$):
  - **Step Cost:** $\prod_{e \in I \cup J} \text{dim}(e)$.
  - **Resulting Tensor Name:** $XY$ (concatenation in the order contracted).
  - **Resulting Indices:** $I \Delta J = (I \cup J) \setminus (I \cap J)$ (symmetric difference).
  - **Intermediate Size:** $\prod_{e \in I \Delta J} \text{dim}(e)$.
- Outer products ($I \cap J = \emptyset$) are allowed, with step cost equal to the product of all indices.
- All arithmetic is in exact arbitrary-precision integers (costs may exceed $2^{64}$).
- For networks with $N \le 12$, an `"optimal": true` claim is validated against the exact dynamic programming optimum.

---

## 3. Worked 4-Tensor Example

Tensors:
- $A$: indices `["i", "j"]`, dims `{"i": 2, "j": 4}`
- $B$: indices `["j", "k"]`, dims `{"j": 4, "k": 4}`
- $C$: indices `["k", "l"]`, dims `{"k": 4, "l": 2}`
- $D$: indices `["l", "m"]`, dims `{"l": 2, "m": 2}`

Contraction sequence:
1. `["A", "B"]`: cost $\text{dim}(i) \cdot \text{dim}(j) \cdot \text{dim}(k) = 2 \cdot 4 \cdot 4 = 32$.
   Result: `AB`, indices `["i", "k"]`, intermediate size $2 \cdot 4 = 8$.
2. `["AB", "C"]`: cost $\text{dim}(i) \cdot \text{dim}(k) \cdot \text{dim}(l) = 2 \cdot 4 \cdot 2 = 16$.
   Result: `ABC`, indices `["i", "l"]`, intermediate size $2 \cdot 2 = 4$.
3. `["ABC", "D"]`: cost $\text{dim}(i) \cdot \text{dim}(l) \cdot \text{dim}(m) = 2 \cdot 2 \cdot 2 = 8$.
   Result: `ABCD`, indices `["i", "m"]`, terminal open indices.

Total exact cost: $32 + 16 + 8 = 56$.

---

## 4. Input & Output JSON Schemas

### Input Schema
```json
{
  "case_id": "tn_example",
  "tensors": {
    "A": ["i", "j"],
    "B": ["j", "k"],
    "C": ["k", "l"]
  },
  "dims": {
    "i": 2,
    "j": 64,
    "k": 64,
    "l": 2
  },
  "cost_bound": "16384",
  "size_bound": null
}
```

### Output Schema: SOLVED
```json
{
  "id": "tn_example",
  "status": "SOLVED",
  "order": [
    ["A", "B"],
    ["AB", "C"]
  ],
  "total_cost": "8448",
  "optimal": true
}
```

### Output Schema: UNKNOWN (Bound Not Met)
```json
{
  "id": "tn_infeasible",
  "status": "UNKNOWN",
  "refusal_code": "BOUND_NOT_MET",
  "witness": {"kind": "open_legs_exceed_size_bound", "open_size": "32768"}
}
```
The `witness` key is optional for $N \le 12$ and required for $N > 12$; no other keys are allowed.

### Output Schema: OUT_OF_SCOPE
```json
{
  "id": "tn_hyperedge",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "hyperedge",
    "index": "h_shared",
    "tensors": ["D", "E", "F"]
  }
}
```
