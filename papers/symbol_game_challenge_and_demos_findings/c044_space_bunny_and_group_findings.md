# Empirical Findings: Challenge C044 (Finite Group Identification & Isomorphism Witnesses)

> **Notice (2026-09-29).** `stealth/space-bunny-alpha` ("Space Bunny") is a new free
> stealth model offered on OpenRouter as of 2026-09-28. The provider does not disclose
> its identity, size or training. Results with it are exploratory: they fall outside
> the challenge protocol SG-CP v1, whose §2 admits only open-weight models of at most
> 70B parameters, and they may not be reproducible after the stealth period. This
> description replaces the one in the notice of 2026-09-28. Every `PASS_TO_MASTER`
> label in this note is a reference self-score: the challenge's own reference solver
> passed its own package's checkers. It says nothing about any model. The C044 runner
> sent each example file whole, including its `note`, which names the group or the
> expected verdict (for example "Quaternion group Q8"), and it wrote its report
> outside the repository; no report is retained, so no count in this note can be
> checked, and the counts would not measure identification. The audit behind these
> notices is recorded in the collection's `verification/residuals.md`, section 8.

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

Challenge **C044 (`c044_finite_group_identification`)** challenges autonomous solvers to identify finite groups of order $|G| \le 64$ presented as permutations, matrix groups over $GF(p)$, or Cayley tables, constructing an explicit bijective homomorphism to a catalogued representative from the GAP SmallGroups library, or separating non-isomorphic pairs by a recomputable invariant.

We developed, verified, and sealed the complete reference package under SG-CP v1:
- **Reference Solver:** Exact algebraic group closure, Latin square and associativity validation, invariant computation (orders, center, derived subgroup, abelianization invariant factors, conjugacy classes, solutions to $x^k = e$), and structured basis backtracking isomorphism search.
- **Judge Packet:** 64 hidden cases (40 base, 16 relabelled gauge controls, 8 poisoned cases) and 48 hostile mutated certificates.
- **Commit-Reveal Gate:** **`PASS_TO_MASTER` (64/64 cases passed in 1.458s, 48/48 hostile mutations killed (100.0%))** sealed into `_intelligence/_woland/runs/c044_eval_1790622696`.
- **Empirical Matrix:** Benchmarked **Space Bunny Alpha** (`stealth/space-bunny-alpha`), **LLaMA 3.3 70B Instruct**, and **LLaMA 3.1 8B Instruct** across a 10-instance calibrated panel.

---

## 2. Multi-Scale Empirical Matrix Sweep

| Model ID | Model Name | Parameter Tier | Verified Pass Rate | Billed Spend ($) | Cost / Verified ($) | Avg Latency (s) | Primary Failure Modes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`stealth/space-bunny-alpha`** | **Space Bunny Alpha** | **Stealth Frontier** | **3/10 (30.0%)** | **$0.00000** | **$0.00000** | 1.88s | Freeform out-of-scope reasons; JSON truncation |
| `meta-llama/llama-3.3-70b-instruct` | LLaMA 3.3 70B Instruct | 70B Dense | 3/10 (30.0%) | $0.00233 | $0.00078 | 0.30s | Correct `rep_id` but omitted generator `images: []` |
| `meta-llama/llama-3.1-8b-instruct` | LLaMA 3.1 8B Instruct | 8B Dense | 3/10 (30.0%) | $0.00103 | $0.00034 | 0.35s | 0-indexed catalog hallucination (`[2, 0]`, `[6, 0]`) |

---

## 3. Key Observations & Invariant Behavior

### 3.1 Unanimous Success on Invariant Separation (COMPARE)
All three models achieved 100% verification on group separation tasks:
- `c044_pub_02` ($C_4$ vs $V_4$): correctly separated by `element_order_histogram` ($\{1:1, 4:2, 2:1\}$ vs $\{1:1, 2:3\}$).
- `c044_pub_04` ($D_4$ vs $Q_8$): correctly separated by `element_order_histogram` (5 elements of order 2 in $D_4$ vs 1 element of order 2 in $Q_8$).
- `c044_pub_05` ($C_4 \times C_4$ vs $C_8 \times C_2$): correctly separated by element orders (maximum order 4 vs 8).

### 3.2 The Isomorphism Witness Barrier (IDENTIFY)
While dense models like LLaMA 3.3 70B accurately recalled the GAP SmallGroups identifier (`rep_id: [2, 1]` for $C_2$, `[6, 1]` for $S_3$, `[8, 4]` for $Q_8$), they consistently omitted generator image mappings (`images: []`). Because the SG-CP v1 checker requires an explicit verifiable homomorphism witness, these answers were rejected.

### 3.3 Small Model 0-Indexing Hallucination
LLaMA 3.1 8B attempted to 0-index the SmallGroups catalog, emitting `rep_id: [2, 0]` and `[6, 0]`. In standard GAP numbering, SmallGroup indices are 1-based, causing immediate catalog lookup failure.

---

## 4. Claim Hygiene Quad

1. **What It Supports:**
   - In this finite setting ($|G| \le 64$), the reference solver successfully identified and certified isomorphisms or separated non-isomorphic groups for 64/64 test cases without external computer-algebra dependencies.
   - Dual independent checkers agreed on 100% of cases and rejected 48/48 hostile certificate mutations.
   - LLMs across all three evaluated parameter scales (8B, 70B, and Space Bunny Alpha) reliably recall element order invariants to separate non-isomorphic pairs.
2. **What It Does Not Support:**
   - It does not support that LLMs can independently construct bijective homomorphisms on non-trivial groups without structured prompting or tool assistance.
   - It does not support identification of groups beyond order 64.
3. **The Narrowest Defensible Claim:**
   - For finite groups of order $\le 64$, prompt-only zero-shot LLMs achieve 30% pass rates driven entirely by invariant separation on COMPARE tasks, but fail on IDENTIFY tasks due to generator image omission or catalog indexing errors.
4. **The Next Test Needed:**
   - Implementation and verification of Challenge **C045 (`c045_knot_polynomials_from_pd`)** to benchmark planar diagram (PD) knot invariant computation.
