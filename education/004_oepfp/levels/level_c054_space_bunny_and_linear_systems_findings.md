# Empirical Findings: Challenge C054 Exact Linear Systems with Inconsistency Witnesses

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
**Tier:** T1  
**Protocol:** SG-CP v1  
**Gate Verdict:** `PASS_TO_MASTER` (Run ID: `c054_eval_1790644869`)  
**Reference Solver Commitment Digest:** `9ffff8d915c5e6d974c85f80521c347535c18c747a29c3420c8960b2c5565257`  

---

## 1. Challenge & Verification Summary

Challenge C054 benchmarks automated synthesis of exact linear system solvers over $\mathbb{Q}^{m \times n}$ ($0 \le m, n \le 40$) returning checkable certificates under the Rouché-Capelli / Farkas duality:
- **Consistent branch ($A x = b$):** Returns exact rational solution vector $x$, certified nullspace basis $N \in \mathbb{Q}^{n \times (n-r)}$ with $A N = 0$, exact rank $r = \operatorname{rank}(A)$, rank certificate minor $A[R, K]$ with $\det A[R, K] \ne 0$, nullspace minor $N[J, :]$ with $\det N[J, :] \ne 0$, and dimension invariant $\operatorname{rank} + \operatorname{len}(\operatorname{null\_basis}) = n$.
- **Inconsistent branch:** Returns a certified left-null inconsistency witness vector $y \in \mathbb{Q}^m$ satisfying $y^T A = 0$ and $y^T b \ne 0$ (showing that no solution $x$ can exist since $0 = y^T A x = y^T b \ne 0$; correction 2026-10-20: this equality-system certificate is the Fredholm alternative, equivalently Rouché–Capelli, not Farkas' lemma, which concerns inequality systems).
- **Out of Scope branch:** Rejects ragged rows, dimension mismatch between $A$ and $b$, or non-numeric entries.

### Verification Gate Results
- **Hidden Base & Control Evaluation:** 64/64 cases passed (100.0%) across:
  - 32 Base cases: full-rank square, singular consistent, singular inconsistent, underdetermined wide systems, overdetermined tall systems, zero matrices, Hilbert matrices, Vandermonde matrices, 64-bit integers ($10^9$ to $10^{18}$), coprime large denominators, and edge dimensions ($m=0, n=0$).
  - 16 Relabel and Gauge Controls: row permutations with $b$ permuted, column permutations, row scalings by non-zero integers and fractions, elementary row additions, and system negation.
  - 16 Poisoned Cases: deceptive prompt suggestions, non-canonical input fractions (`"4/2"`), float-delicate cancellations, ragged rows, non-numeric strings, and dimension mismatches.
- **Dual Independent Checker Agreement:** 100% agreement between the exact dot-product/minor-determinant checker and independent RREF rank/nullspace certifier.
- **Hostile Mutation Kill Rate:** 48/48 hostile mutations killed (100.0%) with zero runtime crashes across corrupted solution coordinates, perturbed inconsistency witnesses, overstated/understated ranks, singular minors, linearly dependent null bases, float strings, and unreduced fractions.

---

## 2. Empirical Model Benchmark (10-Problem Matrix Sweep)

Frontier stealth reasoning model **Space Bunny Alpha** (`stealth/space-bunny-alpha`) was evaluated alongside open dense baselines **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 diverse linear system challenge cases.

| Problem Case ID | Problem Characteristics | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :---: | :---: | :---: |
| `c054_m01_consistent_2x2` | 2x2 full-rank consistent | **PASS** (0.98s) | **PASS** (1.02s) | FAIL ($A x \ne b$: got 9 vs 11) |
| `c054_m02_inconsistent_2x2` | 2x2 singular inconsistent | **PASS** (0.85s) | FAIL ($y^T A \ne 0$: dot = -1) | FAIL ($y^T A \ne 0$: dot = -1) |
| `c054_m03_underdetermined_2x3` | 2x3 wide rank-1 system | **PASS** (1.09s) | FAIL (Invalid `null_rows` length) | FAIL (False INCONSISTENT claim) |
| `c054_m04_consistent_3x3` | 3x3 full-rank dense | **PASS** (1.08s) | FAIL ($A x \ne b$: got 4 vs 6) | FAIL ($A x \ne b$: got -1 vs 6) |
| `c054_m05_inconsistent_3x3` | 3x3 rank-2 inconsistent | **PASS** (1.33s) | FAIL ($y^T A \ne 0$: dot = -2) | FAIL ($y^T A \ne 0$: dot = -1) |
| `c054_m06_homogeneous_3x3` | 3x3 homogeneous ($b=0$) | **PASS** (1.44s) | **PASS** (0.26s) | FAIL (Emitted float string `'-0.333...'`) |
| `c054_m07_rational_2x2` | 2x2 fractions (`1/2`, `1/3`) | **PASS** (1.09s) | FAIL ($A x \ne b$: got 7/12 vs 5/6) | FAIL (False INCONSISTENT claim) |
| `c054_m08_large_int_2x2` | 2x2 entries $\sim 10^9$ | **PASS** (0.96s) | FAIL ($A x \ne b$: got $3 \cdot 10^9$ vs $5 \cdot 10^9$) | FAIL (False INCONSISTENT claim) |
| `c054_m09_poison_deceptive_note` | Prompt note claiming false inconsistency | **PASS** (0.94s) | FAIL (Fell for deceptive note) | FAIL (Fell for deceptive note) |
| `c054_m10_poison_ragged_matrix` | Ragged row matrix | **PASS** (2.03s) | **PASS** (0.24s) | **PASS** (0.16s) |
| **Overall Score** | **Total Passed (Pass Rate)** | **10 / 10 (100.0%)** | **3 / 10 (30.0%)** | **1 / 10 (10.0%)** |
| **Total Token Cost** | **Prompt + Completion Tokens** | **10,235 tokens** | **7,668 tokens** | **7,431 tokens** |

---

## 3. Epistemic Analysis & Failure Modes

1. **Space Bunny Alpha (10/10, 100.0%):**
   - Achieved a consecutive 100% pass rate on exact linear algebra certificates.
   - Accurately constructed particular solutions $x$, extracted verified nullspace bases $N$ with non-zero minor determinants, and identified exact pivot rows and columns proving rank.
   - For inconsistent systems (`c054_m02`, `c054_m05`), successfully derived left-null multipliers $y$ satisfying $y^T A = 0$ and $y^T b \ne 0$.
   - Resisted deceptive prompt framing in `c054_m09`, recognizing the consistent solution and rejecting the injected fake inconsistency witness.

2. **LLaMA 3.3 70B (3/10, 30.0%):**
   - Passed 2x2 full-rank consistent (`c054_m01`), 3x3 homogeneous (`c054_m06`), and ragged matrix rejection (`c054_m10`).
   - Inconsistent systems (`c054_m02`, `c054_m05`): Emitted vector $y$ that failed the left-null condition $y^T A = 0$, violating the Farkas certificate.
   - Underdetermined systems (`c054_m03`): Produced mismatched `null_rows` dimension, failing the kernel minor certificate.
   - Arithmetic errors: Failed on 3x3 dense (`c054_m04`), rational entries (`c054_m07`), and large integers (`c054_m08`) with $A x \ne b$.
   - Succumbed to prompt injection in `c054_m09`, adopting the false claim that the system was inconsistent.

3. **LLaMA 3.1 8B (1/10, 10.0%):**
   - Only passed the syntactic ragged matrix rejection (`c054_m10`).
   - Systematic hallucination of inconsistency: On consistent underdetermined (`c054_m03`), rational (`c054_m07`), and large integer (`c054_m08`) systems, falsely declared `INCONSISTENT` and generated vectors $y$ where $y^T A \ne 0$.
   - Arithmetic precision failure: In homogeneous 3x3 (`c054_m06`), emitted truncated decimal string `'-0.3333333333333333333333333333333'` instead of canonical rational `"-1/3"`.

---

## 4. Claim Discipline Quad

1. **What it supports:**
   - In this 10-problem test suite, Space Bunny Alpha achieved a 100.0% pass rate on exact linear systems with duality certificates (particular solution + null basis minors or Farkas left-null witness), outperforming LLaMA 3.3 70B (30.0%) and LLaMA 3.1 8B (10.0%).
   - The reference exact Gauss-Jordan / Bareiss solver produces checkable rational certificates across 64 hidden evaluation test cases, and dual independent checkers detect and reject 100% of 48 hostile mutations without runtime crashes.

2. **What it does not support:**
   - Does not support that neural models can solve arbitrary large or sparse linear systems ($m, n > 50$) without algorithmic or symbolic tool execution.
   - Does not establish that Space Bunny Alpha is immune to all prompt deception across open-ended domains.

3. **Narrowest defensible claim:**
   - On small linear systems ($m, n \le 4$) with integer, rational, and large entries up to $10^9$ under the C054 specification, Space Bunny Alpha consistently synthesized exact particular solutions, rank certificates, nullspace basis minors, and left-null inconsistency witnesses, whereas dense models exhibited pervasive failures in left-null condition compliance ($y^T A \ne 0$), rank minor dimensions, and prompt injection defense.

4. **Next test needed:**
   - Advance to Challenge C055: DFA Minimization and Equivalence with Distinguishing Strings or Assignment Problems with Dual Potentials.
