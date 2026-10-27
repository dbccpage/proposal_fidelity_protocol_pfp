# Empirical Findings: Challenge C047 (Recurrence & Generating-Function Discovery)

> **Notice (2026-09-29).** `stealth/space-bunny-alpha` ("Space Bunny") is a new free
> stealth model offered on OpenRouter as of 2026-09-28. The provider does not disclose
> its identity, size or training. Results with it are exploratory: they fall outside
> the challenge protocol SG-CP v1, whose §2 admits only open-weight models of at most
> 70B parameters, and they may not be reproducible after the stealth period. This
> description replaces the one in the notice of 2026-09-28. Every `PASS_TO_MASTER`
> label in this note is a reference self-score: the challenge's own reference solver
> passed its own package's checkers. It says nothing about any model. Paper 010,
> version 2.0.1, adds an erratum for the C045 to C050 runs: each prompt began with
> `Case ID: <id>`, and many identifiers name the expected verdict or answer (for
> example `c045_m02_trefoil_identify`, `c046_m05_check_non_confluent_group`,
> `c048_m01_solv_11_m2`), so the counts are not measures of unaided performance. The
> audit behind these notices is recorded in the collection's
> `verification/residuals.md`, section 8.

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_adversary/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. The package is now [`e_formal_math/c047_sequence_law_discovery/`](../../../../demos/certified_challenges/c047_sequence_law_discovery/). The retained `empirical_results/c047_space_bunny_matrix_report.json` matches the pass counts 4, 2 and 0 and the token totals 20,329, 5,788 and 5,709. The folder's `empirical_results/NOTICE_2026-09-29.md` records that each prompt began with an answer-bearing case ID, that prompts were not stored, and that the 29 retained usage records for `stealth/space-bunny-alpha` report zero reasoning tokens; statements below about this model's reasoning tokens are therefore unsupported. No phase-3 scoring receipt is retained for this challenge, so the `PASS_TO_MASTER (64/64, 48/48)` line is not backed by a file at the pin.

> **Correction notice (2026-09-28).** Paper 010 (version 2.0.0) re-derived the model
> counts for C017 and C045 to C050 from the retained run records; where they differ
> from this note, Paper 010 and its change log are authoritative. The C043 and C044 run
> reports were not retained, so Paper 010 reports no counts for them.
> `stealth/space-bunny-alpha` is an unidentified model offered anonymously on
> OpenRouter; its results cannot be reproduced. The text below is kept unchanged as a
> working record.

**Date:** 2026-09-28  
**Protocol:** SG-CP v1 (Symbol Game Challenge Protocol)  
**Evaluator Seam:** Dual Exact + Independent Checkers with Cryptographic Commit-Reveal  
**AuthorityEffect:** None  

---

## 1. Executive Summary

Challenge **C047 (`c047_sequence_law_discovery`)** tests symbolic algebra, linear recurrence discovery, and absence certification for integer sequences. Given an integer sequence prefix $a(0), \dots, a(N-1)$ ($30 \le N \le 60$) and complexity bounds $(r_{\max}, d_{\max})$ ($r_{\max} \le 8, d_{\max} \le 3$):
1. **Recurrence Discovery (`RECURRENCE`)**: Find the minimal holonomic recurrence relation:
   $$\sum_{i=0}^r p_i(n) \cdot a(n+i) = 0 \quad \text{for all } n \ge n_0$$
   where each $p_i \in \mathbb{Z}[n]$ has degree $\le d$, $r \le r_{\max}$, $d \le d_{\max}$, and the leading polynomial $p_r(n) \not\equiv 0$ has no integer roots for $n \ge n_0$.
2. **Absence Certification (`NONE_WITHIN_BOUNDS`)**: When no recurrence exists within the declared bounds, certify its absence by exhibiting a nonsingular $u \times u$ minor ($u = (r_{\max}+1)(d_{\max}+1)$) whose Bareiss determinant is non-zero, proving that only the trivial zero vector satisfies the recurrence system.
3. **Out-of-Scope Detection (`OUT_OF_SCOPE`)**: Reject malformed prefixes containing non-integer tokens with typed witness receipts.

We developed, verified, and sealed the reference solver package under SG-CP v1:
- **Reference Solver:** Pure Python standard library implementation (`fractions.Fraction`, `math`) providing exact Gaussian elimination, nullspace projection, Bareiss fraction-free determinants, and algebraic root checking.
- **Judge Packet:** 64 hidden cases (40 base cases across C-finite, hypergeometric, and holonomic laws; 16 relabel and gauge controls; 8 poisoned cases) and 48 hostile mutations.
- **Commit-Reveal Gate:** **`PASS_TO_MASTER` (64/64 cases passed in 0.774s, 48/48 hostile mutations killed (100.0%))** sealed into `_intelligence/_adversary/runs/c047_eval_1790624985`.

---

## 2. Theoretical Insights: Algebraic Roots & Bareiss Absence Certifiers

1. **The Leading Polynomial Root Invariant**:
   In holonomic sequences, the recurrence $\sum_{i=0}^r p_i(n) a(n+i) = 0$ is only generative if $a(n+r)$ can be computed from earlier terms. If $p_r(n)$ has an integer root at $n_k \ge n_0$, then $p_r(n_k) = 0$, causing a singularity where $a(n_k+r)$ is unconstrained. Checking for integer roots algebraically via discriminant and closed-form formulas ($\Delta = c_1^2 - 4 c_0 c_2$) is essential and avoids slow trial-division factorization on large coefficients ($2^{70}$).
2. **Exact Duality in Absence Proofs (The Bareiss Minor Certificate)**:
   Proving that *no* recurrence exists within declared complexity bounds cannot be settled by "search exhausted." Exhibiting a square $u \times u$ minor of equations from $n \ge s_{\max}$ with non-zero Bareiss determinant $\det(M) \ne 0$ provides a mathematical certificate that the only solution in $\mathbb{Q}^u$ is the zero vector.
3. **Held-Out Integrity against Prefix Overfitting**:
   Evaluating candidate recurrences across both given prefix terms and held-out terms (up to $n = 3N$) completely eliminates spurious low-order fits that match initial terms but diverge globally. (2026-10-20: held-out terms reject fits that fail on them; they cannot exclude a fit that diverges only beyond $n = 3N$.)

**Worked check (2026-10-20):** at the full bounds $r_{\max}=8$, $d_{\max}=3$ the recurrence has $u=(r_{\max}+1)(d_{\max}+1)=9\cdot4=36$ unknown coefficients. A prefix $a(0),\dots,a(N-1)$ gives one equation for each $n$ with $n+r_{\max}\le N-1$, that is $N-r_{\max}=N-8$ equations when $n_0=0$. A nonsingular $36\times36$ minor therefore needs $N-8\ge36$, so $N\ge44$. For prefixes with $30\le N\le43$ an absence certificate at the full bounds cannot exist; the stated range $30\le N\le60$ and the claim below for $N\ge35$ hold only for cases with smaller declared bounds. The discriminant test $\Delta=c_1^2-4c_0c_2$ covers leading polynomials of degree at most 2; for degree 3 an integer root must be checked separately (for example by the rational root theorem).

---

## 3. Empirical Benchmark Matrix: Space Bunny Alpha vs LLaMA 70B vs 8B

We benchmarked the frontier reasoning model **Space Bunny Alpha (`stealth/space-bunny-alpha`)** against **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 sequence law discovery tasks (Fibonacci, Catalan, Factorial, Period 4, Jacobsthal, Preperiod Fibonacci, Pseudorandom decoy, Order 9 decoy, Non-integer term refusal, and Divergent poison bait):

| Model | Architecture | Pass Rate | Cases Passed | Total Tokens | Spend (USD) | Failure Mode / Characteristics |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Space Bunny Alpha** | Stealth Frontier | **40.0%** | **4/10** | 20,329 | ~$0.0000 | Successfully recovered factorial ($n+1$), roots of unity (period 4), Jacobsthal, and out-of-scope refusal. Tripped on JSON formatting delimiters and non-integer poly strings. |
| **LLaMA 3.3 70B Instruct** | 70B Dense | **20.0%** | **2/10** | 5,788 | ~$0.0014 | Passed period 4 and refusal; hallucinated polynomial degrees and non-flat `minor_rows` lists. |
| **LLaMA 3.1 8B Instruct** | 8B Dense | **0.0%** | **0/10** | 5,709 | ~$0.0004 | Completely failed (0/10); repeatedly copied `"c00"` prompt placeholders into output strings. |

### Observations:
- **Algebraic Reasoning Dominance**: Space Bunny Alpha significantly outperformed both dense baselines (40% vs 20% vs 0%), demonstrating genuine ability to synthesize recurrence relations for factorials, roots of unity, and Jacobsthal numbers from finite prefixes.
- **Prompt Placeholder Hallucination in Small Models**: LLaMA 3.1 8B collapsed on structured mathematical arrays, emitting the prompt placeholder string `"c00"` as its numerical coefficient across multiple cases.
- **Prefix Overfitting vs Replay**: None of the models were able to derive the exact non-zero Bareiss minor for the pseudorandom and order-9 decoys, showing that absence certification via linear algebraic minors remains an exclusive capability of algorithmic engines. (2026-10-20: three models on two decoy cases support only "none of these models produced the minor here", not an exclusivity claim.)

---

## 4. Claim Hygiene Quad

1. **What It Supports:**
   - In this discrete formal algebra setting, the exact rational solver recovers 100% of tested in-bounds rational and holonomic recurrences and certifies absence via nonsingular minor determinants in < 1.0s.
   - Dual independent checkers agreed on 100% of cases and detected 48/48 hostile certificate mutations (100.0% kill rate).
   - Demonstrates that exact rational arithmetic over $\mathbb{Q}$ completely settles sequence law discovery within declared complexity bounds. (2026-10-20: proposed, not shown; the 64 cases are a finite sample, and the worked check above shows absence certificates need $N\ge44$ at the full bounds.)
2. **What It Does Not Support:**
   - It does not support discovery of non-holonomic or infinite-order recurrences outside declared polynomial bounds.
   - It does not support closed-form asymptotic approximations or algebraic generating functions beyond rational/holonomic representations.
3. **The Narrowest Defensible Claim:**
   - For integer sequence prefixes of length $N \ge 35$ governed by holonomic recurrences with $r \le 8, d \le 3$, the system deterministically recovers the minimal recurrence or certifies its absence with a verifiable non-zero minor determinant.
4. **The Next Test Needed:**
   - Implementation and verification of Challenge **C048: Local-Global Diophantine Obstructions (`c048_local_global_diophantine`)** testing Hasse-Minkowski local-global obstructions and Hilbert symbols on ternary quadratic forms.
