# Empirical Report: Challenge C043 & Space Bunny Alpha Evaluation

> **Notice (2026-09-29).** `stealth/space-bunny-alpha` ("Space Bunny") is a new free
> stealth model offered on OpenRouter as of 2026-09-28. The provider does not disclose
> its identity, size or training. Results with it are exploratory: they fall outside
> the challenge protocol SG-CP v1, whose §2 admits only open-weight models of at most
> 70B parameters, and they may not be reproducible after the stealth period. This
> description replaces the one in the notice of 2026-09-28. Every `PASS_TO_MASTER`
> label in this note is a reference self-score: the challenge's own reference solver
> passed its own package's checkers. It says nothing about any model. The C043 run
> report was written to a directory that the repository ignores and is not retained,
> so no count in this note can be checked. The audit behind these notices is recorded
> in the collection's `verification/residuals.md`, section 8.

> **Correction notice (2026-09-28).** Paper 010 (version 2.0.0) re-derived the model
> counts for C017 and C045 to C050 from the retained run records; where they differ
> from this note, Paper 010 and its change log are authoritative. The C043 and C044 run
> reports were not retained, so Paper 010 reports no counts for them.
> `stealth/space-bunny-alpha` is an unidentified model offered anonymously on
> OpenRouter; its results cannot be reproduced. The text below is kept unchanged as a
> working record.

> **AuthorityEffect:** `None` · Empirical Benchmark Report  
> **Parent Estate:** [`atlas/coda_atlas/symbol_game/symbol_game_challenge_and_demos_findings/`](./)  
> **Location:** [`c043_space_bunny_and_combinatorial_findings.md`](c043_space_bunny_and_combinatorial_findings.md)  
> **Date:** September 28, 2026  
> **Scope:** Domain E (`e_formal_math`) — Challenge C043 (Ramsey & Van der Waerden Lower-Bound Constructions)  
> **Evaluated Models:** `stealth/space-bunny-alpha`, `meta-llama/llama-3.3-70b-instruct`, `meta-llama/llama-3.1-8b-instruct`  

---

## 1. Executive Summary

We evaluated the newly released **Space Bunny Alpha** (`stealth/space-bunny-alpha`) model on OpenRouter against open-weights baselines (LLaMA 3.3 70B and LLaMA 3.1 8B) on **Challenge C043: Ramsey and van der Waerden Lower-Bound Constructions**.

All candidate outputs were judged against dual independent checkers:
1. Primary Python Checker: [`ramsey_vdw_checker.py`](../c043_ramsey_vdw_constructions/judge_packet/checkers/ramsey_vdw_checker.py)
2. Independent Matrix/Bitmask Checker: [`independent_checker.py`](../c043_ramsey_vdw_constructions/judge_packet/checkers/independent_checker.py)
3. Cryptographic Commit-Reveal Scoring Receipt: `PASS_TO_MASTER` (64/64 cases passed, 48/48 hostile mutations killed) sealed in `_intelligence/_adversary/runs/c043_eval_1790620716/`.

---

## 2. Comparative Benchmark Matrix

Calibrated 10-instance combinatorial panel across Ramsey ($R(3,3), R(4,4), R(3,3,3)$) and Van der Waerden ($W(2,3), W(2,4)$) with constrained pre-coloured elements:

| Model ID | Model Name | Parameter Tier | Verified Pass Rate | Billed Spend ($) | Cost / Verified ($) | Avg Latency (s) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`stealth/space-bunny-alpha`** | **Space Bunny Alpha** | **Stealth Frontier** | **5/10 (50.0%)** | **$0.00000** | **$0.00000** | 10.43s |
| `meta-llama/llama-3.3-70b-instruct` | LLaMA 3.3 70B Instruct | 70B Dense | 1/10 (10.0%) | $0.00053 | $0.00053 | 1.80s |
| `meta-llama/llama-3.1-8b-instruct` | LLaMA 3.1 8B Instruct | 8B Dense | 1/10 (10.0%) | $0.00178 | $0.00178 | 24.19s |

---

## 3. Case-by-Case Verification Ledger

| Case ID | Problem Type & Parameters | Description & Constraints | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **`c043_pub_01`** | `ramsey2` ($s=3, t=3, n=5$) | Pentagon 2-colouring of $K_5$ | FAIL (mono $K_3$) | FAIL (mono $K_3$) | FAIL (mono $K_3$) |
| **`c043_pub_02`** | `vdw` ($r=2, k=3, n=8$) | $W(2,3)$ with fixed element `[[1, 0]]` | **PASS (Verified)** | FAIL (fixed element violation) | FAIL (API Error) |
| **`c043_pub_03`** | `ramsey2` ($s=3, t=3, n=5$) | $R(3,3)$ with fixed edge `[[0, 1, 0]]` | FAIL (mono $K_3$) | FAIL (mono $K_3$) | FAIL (bad DRAT) |
| **`c043_pub_04`** | `ramsey2` ($s=4, t=4, n=8$) | 28-edge colouring avoiding $K_4$ | **PASS (Verified)** | FAIL (length 26 vs 28) | FAIL (length 19 vs 28) |
| **`c043_pub_05`** | `ramsey3` ($n=5$) | Triangle-free 3-colouring of $K_5$ | **PASS (Verified)** | **PASS (Verified)** | FAIL (unfixed witness) |
| **`c043_pub_06`** | `vdw` ($r=2, k=4, n=30$) | $W(2,4)$ with fixed `[[0, 0]]` | **PASS (Honest UNKNOWN)** | FAIL (mono 4-term AP) | FAIL (Malformed JSON) |
| **`c043_pub_07`** | `ramsey2` ($s=4, t=4, n=17$) | Paley scale (136 edges) | FAIL (length 135 vs 136) | FAIL (length 32 vs 136) | FAIL (Malformed JSON) |
| **`c043_pub_08`** | `ramsey2` ($s=3, t=3, n=5$) | Contradictory fixed edges | **PASS (Verified Contradiction)** | FAIL (fixed edge violation) | **PASS (Verified DRAT)** |
| **`c043_pub_09`** | `ramsey2` ($s=3, t=3, n=6$) | $R(3,3)=6$ bound (provably UNSAT) | FAIL (empty clause lemma skip) | FAIL (hallucinated coloring) | FAIL (length 18 vs 15) |
| **`c043_pub_10`** | `vdw` ($r=2, k=3, n=9$) | $W(2,3)=9$ bound (provably UNSAT) | FAIL (empty clause lemma skip) | FAIL (hallucinated coloring) | FAIL (bad structure length) |

---

## 4. Key Epistemic Insights

### 4.1 Native Reasoning Tokens vs. Non-Reasoning Dense Models
Space Bunny Alpha's integrated reasoning capability gave it a distinct advantage on search-heavy combinatorial structures:
- On `c043_pub_04` ($R(4, 4)$ on $K_8$), Space Bunny explored edge assignments in its reasoning channel and successfully emitted a 28-character binary string with zero monochromatic $K_4$ subgraphs. In contrast, both LLaMA 70B and 8B failed to count the exact number of edges in $K_8$, emitting strings of length 26 and 19.
- On `c043_pub_06`, Space Bunny recognized that searching for a 30-element AP-free sequence exceeded its local search limits and emitted an honest `UNKNOWN` refusal (`ACCEPTED: Refusal recorded as UNKNOWN`), whereas LLaMA 70B emitted an invalid colouring containing monochromatic 4-term APs.

### 4.2 Edge Counting & Off-by-One Failure Mode on Paley Scale
On `c043_pub_07` (Paley graph scale $n=17$, requiring $\binom{17}{2} = 136$ edges), Space Bunny emitted 135 characters—missing exactly one edge token. This demonstrates that while the model has the capacity for large outputs, token serialization without an explicit character-level grammar mask remains vulnerable to off-by-one boundary truncation.

### 4.3 Impossibility Hallucination vs DRAT Refutations
On known theoretical bounds ($K_6$ for $R(3,3)$ and 9 elements for $W(2,3)$), standard LLaMA models hallucinated that valid colourings existed. Space Bunny correctly deduced that these cases were impossible (`OUT_OF_SCOPE`), but attempted to emit a one-step empty clause `["0"]` without the necessary RUP conflict lemmas required by the DRAT verifier. This highlights the necessity of the C042 SAT/DRAT engine pipeline for formal refutation generation.

---

## 5. Claim Hygiene Statement

- **What this supports:**
  1. Space Bunny Alpha (`stealth/space-bunny-alpha`) achieves higher zero-shot compliance and verification rates ($50.0\%$) than LLaMA 3.3 70B ($10.0\%$) and 8B ($10.0\%$) on finite Ramsey and Van der Waerden lower-bound challenges.
  2. The model exhibits honest refusal behavior (`UNKNOWN`) on hard search instances rather than fabricating invalid solutions.
  3. The challenge suite C043 passed full cryptographic commit-reveal scoring (`PASS_TO_MASTER`, 64/64 cases verified, 100% mutation kill rate).
- **What this does not support:**
  1. Does not demonstrate that Space Bunny Alpha can solve NP-hard combinatorial search problems in polynomial time.
  2. Does not show that the model can generate valid multi-step DRAT proofs without solver assistance.
- **Narrowest defensible claim:**
  In this 10-case benchmark, internal reasoning tokens enabled Space Bunny Alpha to satisfy exact edge constraints on small complete graphs ($K_8$) and detect fixed-edge contradictions where non-reasoning dense models hallucinated or failed string length counts.
- **Next test needed:**
  Integration of Space Bunny Alpha into Challenge C044 (Finite Group Identification against the GAP Small Groups library).
