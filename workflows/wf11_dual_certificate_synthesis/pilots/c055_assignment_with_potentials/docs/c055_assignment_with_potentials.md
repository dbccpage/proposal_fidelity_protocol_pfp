# C055: Assignment Problems with Dual Potentials

**AuthorityEffect:** None. **Status:** active. **Domain:** f_program_synthesis. **Tier:** T1.
**Budget:** $0.10 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen Hungarian-method solver whose assignments carry dual potentials proving optimality, or a Hall violator proving that no perfect assignment exists, for under $0.10.

## 2. Why This Task

The Hungarian method (Kuhn 1955) is textbook, and its certificate is the whole point. Potentials `u` and `v` with `u_i + v_j ≤ c_ij` on allowed entries, summing to the assignment's cost, prove optimality by LP duality. If some rows cannot be matched, a Hall violator proves it: a row set `S` with fewer allowed columns than rows.

Models often write a solver that finds the right permutation but cannot produce valid potentials, and that is exactly what the checker catches. This is a T1 warm-up for the synthesis loop, like C052. It stresses the Symbol Game's typed residuals (which dual inequality failed, and by how much), the OEWAS (Omega Engine Workflows, Agents, Skills) sampling-and-selection step, and the OEEIS (Omega Engine Epistemic Immune System) on "optimal" claims without duals. A pass shows certified synthesis. It does not show a fast solver.

## 3. Formal Problem and Bounds

An `n × n` cost matrix `C` with `n ≤ 60`, integer entries `|c_ij| ≤ 10¹⁸`, and `null` marking a forbidden pair. Sums can exceed `2⁶³`. The objective is to minimize `Σ_i c_{i,σ(i)}` over permutations `σ` that use only allowed pairs (or maximize if `"sense": "max"`).

- **OPTIMAL:** `σ` together with `u ∈ ℤⁿ` and `v ∈ ℤⁿ` such that:
  - For minimization (`sense == "min"` or omitted):
    $$u_i + v_j \le c_{ij} \quad \text{for every allowed } (i, j)$$
    $$\sum_{i=0}^{n-1} u_i + \sum_{j=0}^{n-1} v_j = \sum_{i=0}^{n-1} c_{i,\sigma(i)} = \text{value}$$
  - For maximization (`sense == "max"`):
    Potentials certify the negated problem (costs $c' = -c$, minimizing $c'$ with $u_i + v_j \le -c_{ij}$ and $\sum u + \sum v = -\text{value}$) or equivalently $u_i + v_j \ge c_{ij}$ with $\sum u + \sum v = \text{value}$.
- **NO_PERFECT_ASSIGNMENT:** a row set `S \subset \{0, \dots, n-1\}` with $|N(S)| < |S|$, where $N(S)$ is the set of columns allowed to some row in $S$ (Hall's condition).

The hidden set must contain:
- negative costs;
- ties with many optimal assignments (any valid answer is accepted);
- costs above `2⁵³` and `10¹⁸`;
- `n = 1`;
- a single allowed entry per row;
- forbidden patterns that pass a row-count check but fail Hall's condition;
- maximization cases flagged `"sense": "max"`.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model, makes no model calls at scoring, and runs in the U09 sandbox. Integers are canonical strings; `σ` is a list of column indices.

```json
{"case_id": "as_ex_01", "sense": "min", "cost": [["4","1","3"],["2","0","5"],["3","2","2"]]}
{"case_id": "as_ex_01", "status": "SOLVED", "kind": "OPTIMAL", "sigma": [1,0,2], "u": ["3","2","2"], "v": ["0","-2","0"], "value": "5"}
{"case_id": "as_ex_04", "sense": "min", "cost": [["1",null,null],["2",null,null],["1","1","1"]]}
{"case_id": "as_ex_04", "status": "SOLVED", "kind": "NO_PERFECT_ASSIGNMENT", "hall_rows": [0,1]}
{"case_id": "as_ex_07", "status": "OUT_OF_SCOPE", "witness": {"reason": "NOT_SQUARE", "row": 2}}
{"case_id": "as_ex_09", "status": "UNKNOWN", "code": "ITERATION_LIMIT"}
```

A certificate is complete when:
- `σ` is a permutation using only allowed entries;
- every dual inequality holds exactly on allowed entries;
- `Σ u + Σ v = value`;
- `value` equals the permutation's cost;
- For `NO_PERFECT_ASSIGNMENT`, the checker computes $N(S)$ itself and verifies $|N(S)| < |S|$.

## 5. Participant Packet

- `task.md` with the JSON Schema.
- 14 public examples with verbatim input and output JSON.
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 32 matrices: random, low-rank (many ties), sparse allowed patterns, infeasible/Hall violators, and maximization cases.
- **Relabel and gauge controls:** 16. Row and column permutations, transposition, adding a constant to one row, scaling, and uniform additive shifts.
- **Poisoned cases:** 16. Prompt notes claiming false optimum, non-square matrices, ragged rows, empty matrices, all-null columns, and non-numeric entries.
- **Exact checker:** Verifies permutation bijection, allowed entry check, exact dual inequalities $u_i + v_j \le c_{ij}$, sum equality $\sum u + \sum v = \text{cost}(\sigma)$, and Hall violator $|N(S)| < |S|$.
- **Independent second checker:** Independent Edmonds/Hopcroft bipartite matching and LP/Hungarian verification.
- **Hostile mutation suite:** 48 mutations rejected (100%).
