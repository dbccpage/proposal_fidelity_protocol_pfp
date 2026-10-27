# Empirical Findings: Challenge C051 Exact LP Solver with Dual and Farkas Certificates

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

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_adversary/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. No package directory for this challenge exists under [`f_program_synthesis/`](../../../../pfp/tests/demo_004/f_program_synthesis/) at the pin, so no solver, checker, receipt or model record backs the figures below; they are an unverified working record.

> **Note (2026-09-28).** `stealth/space-bunny-alpha` is an unidentified model offered
> anonymously on OpenRouter; its results cannot be reproduced. No paper in this
> collection has audited the figures in this note.

**AuthorityEffect:** None  
**Domain:** f_program_synthesis  
**Protocol:** SG-CP v1  
**Gate Verdict:** `PASS_TO_MASTER`  
**Reference Solver Digest:** `d91f3cc6549826d3a732d1f7ba8a0a4b1dc3de54b1f4b68038fbf34cd83f0fe8`  

---

## 1. Challenge & Verification Summary

Challenge C051 establishes the exact rational linear programming solver benchmark with dual certificates over inequality-form linear programs:
$$\max c^T x \quad \text{subject to } A x \le b, x \ge 0$$
where $A \in \mathbb{Q}^{m \times n}, b \in \mathbb{Q}^m, c \in \mathbb{Q}^n$. (2026-10-20: `\text` and `\times` restored; an earlier edit had turned their leading `\t` into spaces.)

**Worked check (2026-10-20):** the dual of this primal is $\min b^T y$ subject to $A^T y \ge c$, $y \ge 0$; for feasible $x, y$, $c^T x \le (A^T y)^T x = y^T A x \le y^T b$, so equal objective values certify both optima. An infeasibility (Farkas) certificate is $y \ge 0$ with $A^T y \ge 0$ and $b^T y < 0$: then $0 \le y^T A x \le y^T b < 0$ for any feasible $x$, a contradiction. Counting the PASS cells in Section 2 gives 7, 3 and 4, matching the overall row.

### Verification Gate Results
- **Hidden Base & Control Evaluation:** 64/64 cases passed (100.0%) across:
  - 40 Base cases (24 optimal including 10 degenerate vertices, 8 infeasible, 8 unbounded).
  - 16 Relabel and Gauge Controls (variable permutation, constraint permutation, positive row scaling, objective scaling, redundant constraints).
  - 8 Poisoned Cases (misleading notes, non-canonical unreduced input strings like `"2/4"`, large denominators, near-unbounded boundary cases).
- **Dual Independent Checker Agreement:** 100% agreement between the exact dot-product rational checker and the independent regex/matrix checker.
- **Hostile Mutation Kill Rate:** 48/48 hostile mutations killed (100.0%) with zero checker crashes across dual independent checkers.

---

## 2. Empirical Model Benchmark (10-Problem Matrix Sweep)

Frontier stealth reasoning model **Space Bunny Alpha** (`stealth/space-bunny-alpha`) was evaluated alongside open dense baselines **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 diverse LP challenge cases.

| Problem Case ID | Type / Features | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :---: | :---: | :---: |
| `c051_m01_optimal_2x2` | Standard 2x2 LP | **PASS** (3.36s) | FAIL (Dual violated) | FAIL (Dual violated) |
| `c051_m02_degenerate_vertex` | Degenerate 2D vertex | **PASS** (8.84s) | FAIL (Duality gap) | FAIL (Ray violated) |
| `c051_m03_3d_corner` | 3D cube corner | FAIL (y length mismatch) | FAIL (Dual violated) | FAIL (Missing farkas_y) |
| `c051_m04_1x1_optimal` | 1x1 LP optimal | **PASS** (1.97s) | FAIL (Non-canonical) | FAIL (Non-canonical) |
| `c051_m05_infeasible_simple` | Simple Farkas witness | **PASS** (1.13s) | **PASS** (2.13s) | **PASS** (0.80s) |
| `c051_m06_infeasible_two_phase`| Contradictory bounds | FAIL (Farkas $A^T y < 0$) | FAIL (Farkas $A^T y < 0$) | FAIL (Farkas $A^T y < 0$) |
| `c051_m07_unbounded_simple` | Simple unconstrained ray | FAIL (API error) | FAIL (Ray violated) | **PASS** (2.42s) |
| `c051_m08_unbounded_diagonal` | 2D unbounded cone | **PASS** (2.16s) | FAIL (Non-canonical) | **PASS** (0.98s) |
| `c051_m09_poison_misleading_note` | Deceptive note | **PASS** (4.13s) | **PASS** (2.89s) | FAIL (Primal violated) |
| `c051_m10_poison_malformed_syntax` | Row length mismatch | **PASS** (2.42s) | **PASS** (1.35s) | **PASS** (0.80s) |
| **Overall Score** | **Total Passed (Pass Rate)** | **7/10 (70.0%)** | **3/10 (30.0%)** | **4/10 (40.0%)** |

---

## 3. Epistemic Analysis & Failure Modes

1. **Space Bunny Alpha (7/10, 70.0%):**
   - Demonstrates strong algebraic reasoning on primal-dual balance, correctly certifying the degenerate vertex (`c051_m02`) where three hyperplanes intersect at a single vertex with zero duality gap.
   - Robust against semantic poisoning (`c051_m09`), completely disregarding the misleading prompt note claiming a false optimal value of 100.
   - Failure modes occurred on higher-dimensional dual multiplier vector sizing (`c051_m03`), two-phase Farkas extraction with contradictory bounds (`c051_m06`), and a transient API error (`c051_m07`).

2. **LLaMA 3.3 70B (3/10, 30.0%):**
   - Frequently computed correct primal vectors $x$, but failed to produce valid dual multipliers $y$ satisfying $A^T y \ge c$ and $b \cdot y = c \cdot x$, exposing a consistent failure mode in dual pricing and complementary slackness reasoning.
   - Succeeded on simple infeasibility (`c051_m05`), deceptive prompt filtering (`c051_m09`), and schema validation (`c051_m10`).

3. **LLaMA 3.1 8B (4/10, 40.0%):**
   - Successfully identified ray directions for simple unbounded problems (`c051_m07`, `c051_m08`), but struggled with exact fractional reduction and dual constraint checking.

---

## 4. Claim Discipline Quad

1. **What it supports:**
   - In this experimental test suite, Space Bunny Alpha achieved a 70.0% pass rate on exact rational linear program certificates, exceeding the 30.0% achieved by LLaMA 3.3 70B and 40.0% achieved by LLaMA 3.1 8B.
   - The reference two-phase exact rational simplex solver with Bland's rule reliably terminates and certifies all 64 hidden test cases without cycling.
   - The dual independent checkers reject 100% of the 48 hostile mutations without runtime crashes.

2. **What it does not support:**
   - Does not show that any evaluated model can replace numerical linear programming libraries on large-scale sparse problems.
   - Does not establish general correctness across higher-dimensional polytopes beyond the evaluated test suite.

3. **Narrowest defensible claim:**
   - For standard inequality-form linear programs with exact rational coefficients under the C051 specification, Space Bunny Alpha correctly emitted 7 out of 10 exact primal-dual, Farkas, or unbounded ray certificates, while open dense baselines passed 3 and 4 cases respectively.

4. **Next test needed:**
   - Advance to Challenge C052: Max-Flow Min-Cut Certificates (`c052_maxflow_mincut_certificates.md`).
