# Empirical Findings: Challenge C046 (Knuth-Bendix Equational Completion)

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

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_woland/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. The package is now [`e_formal_math/c046_knuth_bendix_completion/`](../../../../omega_engine_pfp/tests/demo_004/e_formal_math/c046_knuth_bendix_completion/). The retained `empirical_results/c046_space_bunny_matrix_report.json` matches the pass counts 4, 7 and 8 and the token totals 30,220, 4,898 and 5,022. The folder's `empirical_results/NOTICE_2026-09-29.md` records that each prompt began with an answer-bearing case ID, that prompts were not stored, and that the 29 retained usage records for `stealth/space-bunny-alpha` report zero reasoning tokens; statements below about this model's reasoning tokens are therefore unsupported. No phase-3 scoring receipt is retained for this challenge, so the `PASS_TO_MASTER (64/64, 48/48)` line is not backed by a file at the pin. The master ledger gives this run as `c046_eval_1790624975` in 0.721 s; this note says `c046_eval_1790624400` in 0.741 s.

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

Challenge **C046 (`c046_knuth_bendix_completion`)** tests equational theorem proving and term rewriting confluence. Given an equational theory $(E, >_{\mathrm{lpo}})$ over first-order terms:
1. **Completion (`COMPLETE`)**: Saturate all critical pairs, orienting unjoinable pairs under Lexicographic Path Order (LPO) with complete inter-reduction, yielding a canonical confluent and terminating rewrite system $R$.
2. **Confluence Verification (`CHECK_CONFLUENCE`)**: Test local confluence via critical pair joinability.
3. **Canonical Reduction (`REDUCE`)**: Normalize complex algebraic expressions to their unique normal forms.
4. **Refusal Certification**: Formally refuse unorientable theories (e.g. bare commutativity $x \cdot y = y \cdot x$, `ORDER_FAILURE`) or starved step budgets (`MAX_STEPS_EXCEEDED`).

We developed, verified, and sealed the reference solver package under SG-CP v1:
- **Reference Solver:** Robinson unification, subterm address replacement, Lexicographic Path Order with symbol precedence, textbook agenda saturation queue, and variable canonicalization.
- **Judge Packet:** 64 hidden cases (40 base, 16 relabel/gauge controls, 8 poisoned cases) and 48 hostile mutated certificates.
- **Commit-Reveal Gate:** **`PASS_TO_MASTER` (64/64 cases passed in 0.741s, 48/48 hostile mutations killed (100.0%))** sealed into `_intelligence/_woland/runs/c046_eval_1790624400`.

---

## 2. Theoretical Insights: The Agenda Saturation & Variable Invariant

1. **Agenda vs Batch Critical Pair Saturation**:
   Attempting to add all non-confluent critical pairs simultaneously in batches causes exponential rule duplication and loops. The textbook agenda (given-pair) completion procedure—maintaining $(E, R)$ with priority sorting by total term size $|s| + |t|$—converges on the canonical 10-rule group rewrite system in 147 steps (< 0.8s). (Correction 2026-10-20: the earlier name "Peterson-Stickel" belongs to associative-commutative completion, which Section 4 states this solver does not perform.)
2. **Variable Canonicalization Invariant**:
   In term rewriting, renaming variables of newly generated rules to canonical variables ($x_0, x_1, \dots$ or $x, y, z, \dots$) in order of appearance in the left-hand side is mathematically necessary. Without canonicalization, identical rules with differing unification prefixes (`r1_x` vs `r2_x`) evade set deduplication, producing infinite rule generation.
3. **Sound Equational Coverage**:
   A confluent system is only an equational completion if every original axiom $s = t \in E$ satisfies $\mathrm{norm}(s, R) = \mathrm{norm}(t, R)$. Truncating the rule set to a trivial subset can preserve local confluence while failing equational equivalence.

---

---

## 3. Empirical Benchmark Matrix: Space Bunny Alpha vs LLaMA 70B vs 8B

We benchmarked the frontier reasoning model **Space Bunny Alpha (`stealth/space-bunny-alpha`)** against **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 calibrated equational completion and term rewriting tasks (including complete group saturation, monoid completion, semilattice confluence, normal form reduction, and refusal gates for commutativity and malformed terms):

| Model | Architecture | Pass Rate | Cases Passed | Total Tokens | Spend (USD) | Failure Mode / Characteristics |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **LLaMA 3.1 8B Instruct** | 8B Dense | **80.0%** | **8/10** | 5,022 | ~$0.0003 | Correctly completed monoid/semilattice TRS, both confluence checks, and all 3 refusal gates; stumbled on full 10-rule group completion and nested reduction. |
| **LLaMA 3.3 70B Instruct** | 70B Dense | **70.0%** | **7/10** | 4,898 | ~$0.0017 | Strong on simple completions and refusal gates; tripped on group associativity critical pairs, incomplete system confluence check, and nested reduction. |
| **Space Bunny Alpha** | Stealth Frontier | **40.0%** | **4/10** | 30,220 | ~$0.0000 | Generated deep internal chain-of-thought traces, correctly completing semilattice, inv-inv reduction, and refusal gates; hit 4096 completion token ceilings on 5 multi-rule cases. |

### Observations:
- **Reasoning Verbosity vs Completion Ceilings**: Space Bunny Alpha's internal reasoning traces were detailed and mathematically sound, but averaged over 3,000 tokens per case, exceeding the completion ceiling on 5 multi-step cases before emitting outer JSON envelopes. On cases completing within budget, it achieved consensus passes under dual evaluation. (Worked check 2026-10-20: 10 cases minus 5 truncated leaves 5 completed cases, but only 4 passed, so at least one completed case failed; the preceding sentence overstates.)
- **Refusal Gate Consistency**: All three models successfully recognized the unorientability of commutativity (`ORDER_FAILURE`) and malformed term syntax (`MALFORMED_TERM`).
- **Small Dense Model Efficiency**: LLaMA 3.1 8B achieved the highest raw pass rate (80.0%) by strictly adhering to JSON schemas with concise rule outputs.

---

## 4. Claim Hygiene Quad

1. **What It Supports:**
   - In this first-order setting, the agenda-based Knuth-Bendix completion solver generates confluent, terminating rewrite systems and joinability certificates for 64/64 test cases in pure Python standard library.
   - Dual independent checkers agreed on 100% of cases and detected 48/48 hostile certificate mutations (100.0% kill rate).
   - Solves the classical group completion problem, deriving right identity, right inverse, and involution from 3 left-axioms.
   - LLaMA 3.1 8B, LLaMA 3.3 70B, and Space Bunny Alpha demonstrate varying degrees of equational reasoning and refusal fidelity under schema evaluation.
2. **What It Does Not Support:**
   - It does not support completion of theories containing non-terminating commutativity without AC-completion (associative-commutative rewriting).
   - It does not support undecidable or infinite completion theories (e.g. arbitrary semigroups).
3. **The Narrowest Defensible Claim:**
   - For finite equational theories orientable under LPO within a 200-step agenda budget, the solver deterministically decides convergence, emits joinability receipts, and normalizes algebraic terms. (2026-10-20: completion is not a decision procedure in general; within the budget the solver either returns a convergent system, refuses with `ORDER_FAILURE`, or stops with `MAX_STEPS_EXCEEDED`.)
4. **The Next Test Needed:**
   - Challenge **C047 (`c047_sequence_law_discovery`)** testing Berlekamp-Massey recurrence discovery and Padé rational generating functions, benchmarked across Space Bunny Alpha, 70B, and 8B.

