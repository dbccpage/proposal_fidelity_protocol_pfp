# Empirical Findings: Challenge C053 Bareiss Fraction-Free Matrix Inversion

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

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_woland/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. No package directory for this challenge exists under [`f_program_synthesis/`](../../../../omega_engine_pfp/tests/demo_004/f_program_synthesis/) at the pin, so no solver, checker, receipt or model record backs the figures below; they are an unverified working record. The specification file `f_program_synthesis/c053_assignment_with_potentials.md` uses the number C053 for a different (planned) challenge.

> **Note (2026-09-28).** `stealth/space-bunny-alpha` is an unidentified model offered
> anonymously on OpenRouter; its results cannot be reproduced. No paper in this
> collection has audited the figures in this note.

**AuthorityEffect:** None  
**Domain:** f_program_synthesis  
**Tier:** T1  
**Protocol:** SG-CP v1  
**Gate Verdict:** `PASS_TO_MASTER` (Run ID: `c053_eval_1790643953`)  
**Reference Solver Commitment Digest:** `bd7bf013818d99895c658e55d8f7d1a65343271e7c92914f0c8d2458c39c3b5f`  

---

## 1. Challenge & Verification Summary

Challenge C053 benchmarks automated synthesis of exact fraction-free matrix inversion algorithms over $\mathbb{Q}^{n \times n}$ ($n \le 30$) under the Bareiss recurrence:
$$M^{(k)}_{i,j} = \frac{M^{(k-1)}_{k,k} M^{(k-1)}_{i,j} - M^{(k-1)}_{i,k} M^{(k-1)}_{k,j}}{M^{(k-2)}_{k-1,k-1}}$$
so that, for integer input, every division is exact and no precision is lost. (Correction 2026-10-20: the earlier wording also claimed no coefficient blowup. Bareiss intermediate entries are minors of $A$, so their size is bounded by Hadamard's inequality and grows polynomially in bit length; it is not absent. For rational input, clear denominators first.)

- **Invertible branch ($\det A \ne 0$):** Returns exact canonical determinant string $\det(A)$, integer/rational adjugate matrix $\operatorname{adj}(A)$ satisfying $A \cdot \operatorname{adj}(A) = \det(A) I_n$, and exact reduced rational inverse $A^{-1} = \frac{\operatorname{adj}(A)}{\det(A)}$.
- **Singular branch ($\det A = 0$):** Returns `det: "0"` accompanied by a non-trivial right null vector $v \in \mathbb{Q}^n \setminus \{0\}$ certifying singularity ($A v = 0$).
- **Out of Scope branch:** Rejects non-square matrices ($m \ne n$), ragged rows, or non-numeric entries.

**Worked check (2026-10-20):** the 8B reply for `c053_m08` left the expression $10^9 \cdot 7\cdot10^9 - 2\cdot10^9 \cdot 3\cdot10^9$ unevaluated; it equals $7\cdot10^{18} - 6\cdot10^{18} = 10^{18}$. The 70B string `-7000000000/2000000000000` reduces by $\gcd = 10^9$ to `-7/2000`, as stated. Counting the PASS cells in Section 2 gives 10, 5 and 2.

### Verification Gate Results
- **Hidden Base & Control Evaluation:** 64/64 cases passed (100.0%) across:
  - 32 Base cases: identity matrices, 2x2 and 3x3 dense matrices, upper/lower triangular, diagonal matrices, singular matrices (rank 0, rank 1, rank $n-1$), rational entry matrices, Hilbert matrices, Vandermonde matrices, companion matrices, circulant matrices, large integers ($10^9$ to $10^{18}$), and dimensions up to $n=15$.
  - 16 Relabel and Gauge Controls: row/column permutations with determinant parity tracking ($\det(P A) = \operatorname{sgn}(P) \det(A)$), uniform integer and fraction scaling ($A \mapsto c A \implies \det(c A) = c^n \det(A)$), transpose invariance ($\det(A^T) = \det(A)$), and elementary row additions.
  - 16 Poisoned Cases: deceptive prompt suggestions, rectangular matrices ($2 \times 3, 4 \times 3$), ragged rows, non-numeric strings, and empty matrices.
- **Dual Independent Checker Agreement:** 100% agreement between the exact fraction-free/adjugate checker and independent Gaussian elimination over $\mathbb{Q}$.
- **Hostile Mutation Kill Rate:** 48/48 hostile mutations killed (100.0%) with zero runtime crashes across corrupted determinants, off-diagonal adjugate corruptions, zeroed null vectors, non-kernel vectors, float strings, and unreduced fractions.

---

## 2. Empirical Model Benchmark (10-Problem Matrix Sweep)

Frontier stealth reasoning model **Space Bunny Alpha** (`stealth/space-bunny-alpha`) was evaluated alongside open dense baselines **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 diverse matrix inversion challenge cases.

| Problem Case ID | Problem Characteristics | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :---: | :---: | :---: |
| `c053_m01_identity_2x2` | 2x2 identity matrix | **PASS** (2.14s) | **PASS** (7.16s) | **PASS** (1.28s) |
| `c053_m02_dense_2x2` | 2x2 dense integer matrix | **PASS** (1.32s) | **PASS** (12.48s) | FAIL (Det sign flipped) |
| `c053_m03_singular_2x2` | 2x2 singular rank-1 matrix | **PASS** (0.96s) | **PASS** (1.87s) | FAIL ($A v \ne 0$) |
| `c053_m04_triangular_3x3` | 3x3 upper triangular matrix | **PASS** (5.17s) | FAIL ($A \cdot \operatorname{adj}(A)$ off-diag) | FAIL (Det mismatch: 2 vs -16) |
| `c053_m05_dense_3x3` | 3x3 dense integer matrix | **PASS** (15.54s) | FAIL (Det sign flipped: -1 vs 1) | FAIL (Adjugate error: dot=-2) |
| `c053_m06_singular_rank2_3x3` | 3x3 singular rank-2 matrix | **PASS** (2.05s) | **PASS** (2.92s) | FAIL ($A v \ne 0$) |
| `c053_m07_rational_2x2` | 2x2 matrix with fractions (`"1/4"`, `"1/5"`) | **PASS** (3.41s) | FAIL (Fraction det error: 1/12 vs 1/20) | FAIL (Fraction det error: 1/4 vs 1/20) |
| `c053_m08_large_int_2x2` | 2x2 matrix with entries $10^9$ | **PASS** (3.46s) | FAIL (Unreduced fraction string) | FAIL (Raw arithmetic string output) |
| `c053_m09_poison_deceptive_note` | Prompt note claiming false det & singular | **PASS** (1.98s) | FAIL (Adjugate calculation error) | FAIL (Hallucinated OUT_OF_SCOPE) |
| `c053_m10_poison_rect_matrix` | Rectangular $2 \times 3$ matrix | **PASS** (1.54s) | **PASS** (2.71s) | **PASS** (1.95s) |
| **Overall Score** | **Total Passed (Pass Rate)** | **10 / 10 (100.0%)** | **5 / 10 (50.0%)** | **2 / 10 (20.0%)** |
| **Total Token Cost** | **Prompt + Completion Tokens** | **9,705 tokens** | **6,099 tokens** | **6,013 tokens** |

---

## 3. Epistemic Analysis & Failure Modes

1. **Space Bunny Alpha (10/10, 100.0%):**
   - Achieved a 100% pass rate across the full spectrum of matrix types: 2x2, 3x3 dense, triangular, singular matrices requiring null vectors, rational entries, and $10^9$ magnitude integers.
   - Accurately constructed exact integer adjugate cofactors and computed canonical fraction strings ($p/q$ with $\gcd(|p|, q) = 1$) for inverses without floating-point approximations.
   - Demonstrated complete resistance to prompt injection in `c053_m09`, ignoring deceptive claims of singularity and computing the true determinant (8) and inverse.
   - Correctly identified out-of-scope rectangular matrices (`c053_m10`).

2. **LLaMA 3.3 70B (5/10, 50.0%):**
   - Successfully handled 2x2 integer inversion and singular matrices (`c053_m01`, `c053_m02`, `c053_m03`, `c053_m06`, `c053_m10`).
   - Failed on 3x3 matrix cofactors (`c053_m04`, `c053_m05`), making sign errors in permutation parities and violating the fundamental adjugate identity $A \cdot \operatorname{adj}(A) = \det(A) I$.
   - Failed on rational entries (`c053_m07`) due to arithmetic errors in cross-multiplying fraction denominators.
   - Failed strict canonical fraction formatting on large integers (`c053_m08`), returning unreduced string `-7000000000/2000000000000` instead of `-7/2000`.

3. **LLaMA 3.1 8B (2/10, 20.0%):**
   - Only passed the trivial 2x2 identity matrix (`c053_m01`) and rectangular matrix rejection (`c053_m10`).
   - Failed elementary 2x2 dense determinant sign computation (`c053_m02`).
   - Failed to compute valid null vectors for singular matrices (`c053_m03`, `c053_m06`), returning vectors where $A v \ne 0$.
   - On large integers (`c053_m08`), emitted raw uncomputed arithmetic expressions (`"1000000000*7000000000-2000000000*3000000000"`) instead of performing exact integer multiplication.
   - Fell for deceptive prompt framing in `c053_m09`, erroneously rejecting a valid square matrix as `OUT_OF_SCOPE`.

---

## 4. Claim Discipline Quad

1. **What it supports:**
   - In this 10-problem test suite, Space Bunny Alpha achieved a 100.0% pass rate on exact fraction-free matrix inversion and singular null vector certification, outperforming LLaMA 3.3 70B (50.0%) and LLaMA 3.1 8B (20.0%).
   - The Bareiss fraction-free elimination algorithm implemented in the reference solver provides exact rational arithmetic and cofactor generation across 64 hidden evaluation test cases.
   - Dual independent checkers verify that all 48 hostile mutations (corrupted entries, sign errors, float approximations, and unreduced fractions) are killed with 100.0% accuracy.

2. **What it does not support:**
   - Does not support that neural models can invert arbitrarily large matrices ($n > 10$) without external symbolic or numerical computing tool assistance.
   - Does not establish that Space Bunny Alpha will achieve 100% accuracy on arbitrary ill-conditioned matrices of dimension $n \ge 10$.

3. **Narrowest defensible claim:**
   - On $n \times n$ matrices ($n \le 3$) with integer, rational, and large entries up to $10^9$ under the C053 specification, Space Bunny Alpha consistently synthesized exact determinants, adjugate matrices, rational inverses, and singular null vectors, whereas 70B and 8B dense models exhibited recurrent failure modes in cofactor signs, fraction reduction, and kernel computation.

4. **Next test needed:**
   - Advance to Challenge C054: Exact Linear Systems with Inconsistency Witnesses (Farkas / Rouché-Capelli) or LR(1) Parser Table Construction.
