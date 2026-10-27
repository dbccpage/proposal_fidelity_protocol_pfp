# Empirical Findings: Challenge C055 Assignment Problems with Dual Potentials

> **Notice (2026-09-29).** `stealth/space-bunny-alpha` ("Space Bunny") is a new free
> stealth model offered on OpenRouter as of 2026-09-28. The provider does not disclose
> its identity, size or training. Results with it are exploratory: they fall outside
> the challenge protocol SG-CP v1, whose §2 admits only open-weight models of at most
> 70B parameters, and they may not be reproducible after the stealth period. This
> description replaces the one in the note of 2026-09-28. Every `PASS_TO_MASTER` label
> in this note is a reference self-score: the challenge's own reference solver passed
> its own package's checkers. It says nothing about any model. No paper in this
> collection has audited the other figures in this note. The audit behind these
> notices is recorded in the collection's `verification/residuals.md`, section 8.

> **Note (2026-09-28).** `stealth/space-bunny-alpha` is an unidentified model offered
> anonymously on OpenRouter; its results cannot be reproduced. No paper in this
> collection has audited the figures in this note.

**AuthorityEffect:** None  
**Domain:** f_program_synthesis  
**Tier:** T1  
**Protocol:** SG-CP v1  
**Gate Verdict:** `PASS_TO_MASTER` (Run ID: `c055_eval_1790645603`)  
**Reference Solver Commitment Digest:** `9d8a4162f0f3bcc290eead85beb08d61ef0389db3d2518f18f080a224e07d9ae`  

---

## 1. Challenge & Verification Summary

Challenge C055 benchmarks automated synthesis of exact integer assignment solvers over $n \times n$ cost matrices ($1 \le n \le 60$) with entries $|c_{ij}| \le 10^{18}$ and forbidden entries (`null`), returning checkable certificates under linear programming duality and Hall's Marriage Theorem:
- **Optimal branch (feasible assignment):** Returns an optimal permutation $\sigma$ of $\{0, \dots, n-1\}$ using only allowed entries, exact dual node potentials $u, v \in \mathbb{Z}^n$ satisfying complementary slackness bounds ($u_i + v_j \le c_{ij}$ for min, or $u_i + v_j \ge c_{ij}$ / negated dual for max), and total optimal objective value $\sum u_i + \sum v_j = \sum c_{i, \sigma(i)} = \text{value}$.
- **Infeasible branch (no perfect matching):** Returns a certified Hall violator row subset $S \subset \{0, \dots, n-1\}$ satisfying $|N(S)| < |S|$, where $N(S)$ denotes the column neighborhood of $S$ in the allowed bipartite subgraph.
- **Out of Scope branch:** Rejects ragged rows, non-square matrices, or non-numeric entries.

### Verification Gate Results
- **Hidden Base & Control Evaluation:** 64/64 cases passed (100.0%) across:
  - 32 Base cases: dense square min, dense square max, matrices with forbidden entries, complete bipartite graphs, Hall-infeasible matrices, negative cost entries, large integers ($10^9$ to $10^{18}$), multiple optimal permutations (ties), and edge dimensions ($n=1, 2, 4, 8, 12$).
  - 16 Relabel and Gauge Controls: row permutations with costs adjusted, column permutations, constant potential shifts ($u_i \leftarrow u_i + \delta, v_j \leftarrow v_j - \delta$), uniform cost additions, and transposition gauge invariance.
  - 16 Poisoned Cases: deceptive prompt claims of infeasibility, non-square rectangular inputs, ragged rows, non-numeric strings, and float values.
- **Dual Independent Checker Agreement:** 100% agreement between the exact dual-slackness/Hall-evaluator checker and independent matching/potential certifier.
- **Hostile Mutation Kill Rate:** 48/48 hostile mutations killed (100.0%) with zero runtime crashes across swapped permutation entries, forbidden entry usage, dual inequality violations, sum-of-potentials drift, invalid Hall violator sets ($|N(S)| \ge |S|$), and float/non-canonical string formatting.

---

## 2. Empirical Model Benchmark (10-Problem Matrix Sweep)

Frontier stealth reasoning model **Space Bunny Alpha** (`stealth/space-bunny-alpha`) was evaluated alongside open dense baselines **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 diverse assignment problem challenge cases.

| Problem Case ID | Problem Characteristics | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :---: | :---: | :---: |
| `c055_m01_min_2x2` | 2x2 dense minimization | **PASS** (0.77s) | FAIL (Dual sum mismatch: $\sum u + \sum v = 2 \ne 3$) | FAIL (Value mismatch: claimed 3 vs cost 7) |
| `c055_m02_max_2x2` | 2x2 dense maximization | **PASS** (0.86s) | FAIL (Value mismatch: claimed 35 vs cost 50) | FAIL (Value mismatch: claimed 5 vs cost 15) |
| `c055_m03_min_3x3_forbidden` | 3x3 min with `null` entries | **PASS** (0.76s) | FAIL (Dual inequality violated at (2,1): $u_2+v_1=3 > 1$) | FAIL (Chosen forbidden pair at (0, 1)) |
| `c055_m04_hall_infeasible_3x3` | 3x3 Hall infeasible (isolated row) | **PASS** (0.80s) | FAIL (Hall condition failed: $\|N(S)\| = 2 \ge \|S\| = 2$) | FAIL (Hall condition failed: $\|N(S)\| = 2 \ge \|S\| = 2$) |
| `c055_m05_negative_costs_3x3` | 3x3 min with negative weights | **PASS** (0.63s) | FAIL (Dual inequality violated at (1,1): $u_1+v_1=2 > -8$) | FAIL (Value mismatch: claimed -21 vs cost 9) |
| `c055_m06_large_integers_10e9` | 2x2 entries $\sim 10^9$ | **PASS** (1.41s) | FAIL (Value mismatch: claimed $3\cdot 10^9$ vs cost $6\cdot 10^9$) | FAIL (False Hall violator: $\|N(S)\| = 2 \ge \|S\| = 1$) |
| `c055_m07_min_4x4_dense` | 4x4 standard dense min | **PASS** (1.29s) | FAIL (Value mismatch: claimed 14 vs cost 26) | FAIL (Value mismatch: claimed 16 vs cost 22) |
| `c055_m08_hall_infeasible_2x2` | 2x2 Hall infeasible ($\|S\|=2, \|N(S)\|=1$) | **PASS** (0.87s) | **PASS** (0.16s) | **PASS** (0.14s) |
| `c055_m09_poison_deceptive_note` | Prompt note claiming false infeasibility | **PASS** (0.51s) | FAIL (Fell for deception: fake Hall violator) | FAIL (Fell for deception: fake Hall violator) |
| `c055_m10_poison_ragged_matrix` | Ragged row matrix | **PASS** (0.94s) | **PASS** (0.59s) | **PASS** (1.30s) |
| **Overall Score** | **Total Passed (Pass Rate)** | **10 / 10 (100.0%)** | **2 / 10 (20.0%)** | **2 / 10 (20.0%)** |
| **Total Token Cost** | **Prompt + Completion Tokens** | **13,021 tokens** | **7,421 tokens** | **7,396 tokens** |

---

## 3. Epistemic Analysis & Failure Modes

1. **Space Bunny Alpha (10/10, 100.0%):**
   - Maintained a 100% pass rate across all test regimes in Domain F (Program Synthesis).
   - Accurately constructed optimal permutations $\sigma$, valid dual potentials $u, v \in \mathbb{Z}^n$ satisfying $u_i + v_j \le c_{ij}$ without slackness violations, and exact objective sums.
   - For maximization (`c055_m02`), correctly adopted the standard or negated dual formulation, preserving zero duality gap.
   - Handled negative costs (`c055_m05`) and large $10^9$ coefficients (`c055_m06`) without sign errors or precision truncations.
   - Successfully extracted minimal Hall violator row sets $S$ where $|N(S)| < |S|$ on infeasible instances (`c055_m04`, `c055_m08`).
   - Resisted deceptive prompt framing in `c055_m09`, recognizing the feasible 2x2 matrix and refusing the suggested fake Hall violator.

2. **LLaMA 3.3 70B (2/10, 20.0%):**
   - Passed only the simple 2x2 Hall violator (`c055_m08`) and ragged matrix rejection (`c055_m10`).
   - Dual inequality violations: In `c055_m03` and `c055_m05`, emitted potential vectors $u, v$ that severely violated the dual constraint $u_i + v_j \le c_{ij}$, failing the dual certificate.
   - Objective value hallucination: In `c055_m02`, `c055_m06`, and `c055_m07`, the claimed value did not match the actual cost of the chosen permutation $\sum c_{i, \sigma(i)}$.
   - False Hall condition claims: In `c055_m04` and `c055_m09`, submitted row subsets where $|N(S)| \ge |S|$, failing the Hall violator certificate.
   - Vulnerable to prompt injection: In `c055_m09`, accepted the deceptive instruction claiming infeasibility on a strictly feasible matrix.

3. **LLaMA 3.1 8B (2/10, 20.0%):**
   - Passed only `c055_m08` and `c055_m10`.
   - Permutation feasibility failure: In `c055_m03`, selected a forbidden pair ($C[0][1] = \text{null}$).
   - Value arithmetic failures: Failed to compute the correct permutation sum in `c055_m01`, `c055_m02`, `c055_m05`, and `c055_m07`.
   - Infeasibility hallucination: Falsely claimed that the valid $10^9$ matrix (`c055_m06`) was infeasible and emitted an invalid Hall violator ($|N(S)| = 2 \ge |S| = 1$).

---

## 4. Claim Discipline Quad

1. **What it supports:**
   - In this 10-problem test suite, Space Bunny Alpha achieved a 100.0% pass rate on assignment problems with dual potentials and Hall violator certificates, outperforming LLaMA 3.3 70B (20.0%) and LLaMA 3.1 8B (20.0%).
   - The reference integer Hungarian / alternating BFS solver produces exact primal-dual and Hall certificates across 64 hidden evaluation test cases, and dual independent checkers detect and reject 100% of 48 hostile mutations without runtime crashes.

2. **What it does not support:**
   - Does not support that neural models can solve large dense assignment problems ($n > 100$) without algorithmic or symbolic tool execution.
   - Does not demonstrate immunity of Space Bunny Alpha to prompt deception across all possible problem formulations.

3. **Narrowest defensible claim:**
   - On square assignment problems ($n \le 4$) with integer, negative, and large entries up to $10^9$ under the C055 specification, Space Bunny Alpha consistently generated exact optimal permutations, valid dual potentials with zero duality gap, and certified Hall violators, whereas dense baselines frequently violated dual feasibility inequalities ($u_i + v_j \le c_{ij}$) and Hall cardinality conditions ($|N(S)| < |S|$).

4. **Next test needed:**
   - Advance to Challenge C056: DFA Minimization & Equivalence with Distinguishing Strings.
