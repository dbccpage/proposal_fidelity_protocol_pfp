# Empirical Findings: Challenge C045 (Knot Polynomials from Planar Diagrams)

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
> `c048_m01_solv_11_m2`), so the counts are not measures of unaided performance. In
> this challenge both checkers accept a refusal with any listed reason on every case,
> so an answer that refuses every panel case passes 10 of 10, more than any model. The
> audit behind these notices is recorded in the collection's
> `verification/residuals.md`, section 8.

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_woland/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. The package is now [`e_formal_math/c045_knot_polynomials_from_pd/`](../../../../omega_engine_pfp/tests/demo_004/e_formal_math/c045_knot_polynomials_from_pd/). The retained `empirical_results/c045_space_bunny_matrix_report.json` matches the pass counts 2, 8 and 3 and the token totals 40,198, 6,507 and 6,812 (averages 4,020, 651 and 681). The folder's `empirical_results/NOTICE_2026-09-29.md` records that each prompt began with an answer-bearing case ID, that prompts were not stored, and that the 29 retained usage records for `stealth/space-bunny-alpha` report zero reasoning tokens; statements below about this model's reasoning tokens are therefore unsupported. No phase-3 scoring receipt is retained for this challenge, so the `PASS_TO_MASTER (64/64, 48/48)` line is not backed by a file at the pin.

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

Challenge **C045 (`c045_knot_polynomials_from_pd`)** evaluates whether autonomous systems can deduce topological invariants of oriented knots from their combinatorial Planar Diagram (PD) presentations without relying on continuous geometric embeddings.

We implemented, verified, and sealed the reference package under SG-CP v1:
- **Reference Solver:** Combinatorial Euler rotation verification ($V - E + F = 2$), Alexander arc matrix reduction, state-sum Kauffman bracket in $\mathbb{Z}[A, A^{-1}]$, Jones polynomial normalization $V(t) = (-A^3)^{-w} \langle K \rangle |_{A = t^{-1/4}}$, and Rolfsen catalog classification up to 7 crossings.
- **Judge Packet:** 64 hidden cases (unknot, trefoil, figure eight, cinquefoil, three-twist, stevedore, 6_2, 6_3, 7_1, with gauge renumberings and invalid edge/planarity controls) and 48 hostile mutated certificates.
- **Commit-Reveal Gate:** **`PASS_TO_MASTER` (64/64 cases passed in 0.427s, 48/48 hostile mutations killed (100.0%))** sealed into `_intelligence/_woland/runs/c045_eval_1790623789`.
- **Empirical Matrix:** Benchmarked **LLaMA 3.3 70B Instruct**, **Space Bunny Alpha** (`stealth/space-bunny-alpha`), and **LLaMA 3.1 8B Instruct** across a 10-instance calibrated panel.

---

## 2. Multi-Scale Empirical Matrix Sweep

| Model ID | Model Name | Parameter Tier | Verified Pass Rate | Billed Spend ($) | Cost / Verified ($) | Avg Tokens | Primary Failure Modes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `meta-llama/llama-3.3-70b-instruct` | LLaMA 3.3 70B Instruct | 70B Dense | **8/10 (80.0%)** | $0.00210 | $0.00026 | 651 | Laurent polynomial state-sum coefficient arithmetic |
| **`stealth/space-bunny-alpha`** | **Space Bunny Alpha** | **Stealth Frontier** | **2/10 (20.0%)** | **$0.00000** | **$0.00000** | 4,020 | Unconstrained reasoning buffer exhaustion (>4,000 tokens) |
| `meta-llama/llama-3.1-8b-instruct` | LLaMA 3.1 8B Instruct | 8B Dense | 3/10 (30.0%) | $0.00095 | $0.00032 | 681 | Literal prompt placeholder mimicry (`power`), writhe arithmetic errors |

---

## 3. Key Observations & Invariant Behavior

### 3.1 High Topology Recognition in 70B Dense Model
LLaMA 3.3 70B Instruct demonstrated high zero-shot performance (80.0%):
- **Identification:** Correctly identified the unknot ($0_1$), right-handed trefoil ($3_1$, writhe +3), figure-eight ($4_1$, achiral), and right-handed cinquefoil ($5_1$, writhe +5).
- **Comparison:** Successfully completed both non-isomorphic separation (`c045_m07`, `DIFFERENT_INVARIANTS`) and cyclic permutation gauge invariance (`c045_m08`, `SAME_INVARIANTS`).
- **Refusal Validation:** Correctly identified corrupted edge multiplicity (`c045_m09`) and non-planar strand routing (`c045_m10`, `NON_PLANAR`).
- **Failure Mode:** Failed only on manual polynomial coefficient state-sums for $3_1$ and $4_1$, where intermediate sign-multiplications in the Kauffman state summation drifted.

### 3.2 Reasoning Buffer Scaling Barrier in Space Bunny Alpha
Space Bunny Alpha exhibited exploratory internal reasoning on knot state sums, generating an average of 4,020 tokens per case. On 7 cases, internal deliberation reached the completion limit before the model emitted the final answer JSON envelope, resulting in empty content returns. On the 2 cases where output generation completed within limits (`c045_m01` and `c045_m09`), it achieved consensus passes under dual evaluation.

**Worked check (2026-10-20):** 7 truncated cases plus 2 completed passing cases account for 9 of the 10 panel cases; the tenth case is not described, so the claim that the model passed every case it completed is not established by this note. For the Euler check on a knot diagram with $n$ crossings, the diagram graph has $V=n$ vertices, $E=2n$ edges and $F=n+2$ faces, so $V-E+F=2$. Cost per verified pass is $0.00210/8=0.0002625$ and $0.00095/3\approx0.000317$, matching the rounded table entries.

### 3.3 Small Model Prompt Placeholder Mimicry
LLaMA 3.1 8B Instruct copied dictionary template keys from the prompt specification literally, emitting keys named `"power"` rather than numeric degree strings (e.g., `"0"`, `"1"`), triggering independent checker type rejections.

---

## 4. Claim Hygiene Quad

1. **What It Supports:**
   - In this discrete knot topology setting (crossings $n \le 7$), the pure Python reference solver certified polynomial invariants, writhe, and classification across 64 hidden cases in 0.427 seconds.
   - Dual independent checkers agreed on 100% of cases and rejected 48/48 hostile certificate mutations.
   - LLaMA 3.3 70B Instruct achieved an 80.0% zero-shot pass rate on knot identification, comparison, and refusal classification.
2. **What It Does Not Support:**
   - It does not support that unassisted models compute exact Laurent polynomial state sums for knots with large crossing counts ($n \ge 8$).
   - It does not support that long-chain reasoning models converge without structured token allocation budgets.
3. **The Narrowest Defensible Claim:**
   - On the 10 evaluated planar diagram knot instances, LLaMA 3.3 70B accurately identified knot topologies, chirality, and planar invalidity, while failing only on multi-term Laurent polynomial state-sum expansions; Space Bunny Alpha passed all cases that completed within its token allocation but exhausted its output buffer on unconstrained multi-crossing state searches.
4. **The Next Test Needed:**
   - Implementation and verification of Challenge **C046 (`c046_knuth_bendix_completion`)** evaluating term rewriting systems, critical pairs, and equational joinability certificates.
