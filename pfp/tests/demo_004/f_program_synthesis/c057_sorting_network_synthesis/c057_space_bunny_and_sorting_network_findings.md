# Space Bunny Alpha & Wave 3 Program Synthesis: Challenge C057 (Sorting Network Synthesis) Empirical Findings

> **Notice (2026-09-29): corrections and status of these results**
>
> The model `stealth/space-bunny-alpha` ("Space Bunny") is a free stealth model offered on OpenRouter since 2026-09-28; the provider does not disclose its identity, size or training. Results obtained with it are exploratory, fall outside the challenge protocol SG-CP v1 §2 (which requires identified models), and may not be reproducible after the stealth period. This note is kept as a record of what was run; its numbers are not challenge results.
>
> *What can be checked.* There is no retained results file. The runner writes `empirical_results/<model>_c057_results.json`, and no such file exists in the package or anywhere in the repository history, so none of the numbers below can be checked. The statements that Space Bunny performed a chain-of-thought search and that its reasoning exceeded a token threshold have no retained evidence. The runner, as committed before this batch, also fell back to the provider's `reasoning` field when the answer field was empty, so a scored reply may not have been the model's final answer.
>
> *Answer leakage in the prompt.* The prompt's worked example, `[[0, 2], [1, 3], [0, 1], [2, 3], [1, 2]]`, is the optimal n = 4 network, which answers m01. The prompt stated the rule k < ceil(log2(n!)) and the proven bounds k < 25 for n = 9 and k < 29 for n = 10; m08 (n = 4, k = 4) and m09 (n = 9, k = 24) are infeasible exactly by these statements. The case IDs `c057_m08_infeasible_n4_k4`, `c057_m09_infeasible_n9_k24` and `c057_m10_poison_reversed_prefix` also name their verdicts. Each model answered each case once, at temperature 0.
>
> *Checker defect (repaired in this batch).* Both checkers accepted `UNKNOWN` on any case with a prefix or a forbidden list, including feasible ones. A responder that answers `UNKNOWN` on every well-formed case and `OUT_OF_SCOPE` on the malformed m10 passes 6 of 10 (m02, m04, m06, m08, m09 and m10; re-checked on 2026-09-29 against the checkers as committed), the same score as the best model reported below.
>
> *Gate verdict.* The "commit-reveal" gate cited at the top of this note is a self-check: `commit_reveal_c057.py` hashes the reference solver and then evaluates the judge cases in the same process, so the commitment binds only the reference solver's files and does not show that the cases or checkers were fixed before the model runs. The verdict `PASS_TO_MASTER` and the hidden-case and mutation figures quoted below describe the reference solver checked by the package's own checkers; they are not results for any model.
>
> The original note follows unchanged.

**AuthorityEffect:** None.
**Date:** September 28, 2026.
**Domain:** `f_program_synthesis` (Wave 3).
**Protocol:** SG-CP v1 with Woland Terminal Reality Gate commit-reveal protocol.
**Evaluator Run ID:** `c057_eval_1790647557`.
**Solver Digest:** `a76406084c143de8498a7f89ad79b66d306cef7b777dacc3e9c61df3c1b12d88`.
**Tested Models:**
1. `stealth/space-bunny-alpha` (Stealth Frontier)
2. `meta-llama/llama-3.3-70b-instruct` (70B Dense open-weights)
3. `meta-llama/llama-3.1-8b-instruct` (8B Dense open-weights)

---

## 1. Executive Summary

Challenge C057 evaluates the synthesis of comparator sorting networks for $n \le 12$ channels within comparator bounds $k$, subject to mandatory prefix layers and forbidden comparator sets. All solutions are rigorously evaluated by the **0-1 principle** (verifying that all $2^n$ binary inputs are mapped to sorted outputs), prefix adherence, and forbidden set avoidance.

The challenge was sealed under the Woland Terminal Reality Gate:
- **Solver Commitment SHA-256:** `a76406084c143de8498a7f89ad79b66d306cef7b777dacc3e9c61df3c1b12d88`
- **Hidden Test Cases:** **64 / 64 passed (100.0%)** (32 base cases including proven optimal bounds for $n=9, 10, 11, 12$, 16 reflection/permutation controls, 16 poisoned cases).
- **Hostile Mutation Kill Rate:** **48 / 48 killed (100.0%)** by dual checkers (`exact_checker.py` and `independent_checker.py`).
- **Terminal Gate Verdict:** **`PASS_TO_MASTER`**.

In the empirical benchmark sweep across 10 diverse problem instances:
- **Space Bunny Alpha:** **6 / 10 passed (60.0%)**, solving constrained synthesis instances for $n=4$ and $n=5$, as well as all lower bound and poisoned guardrails.
- **LLaMA 3.3 70B Instruct:** **4 / 10 passed (40.0%)**, only passing unconstrained $n=4$, lower bound, and poisoned cases; failing all constrained instances and all $n \ge 5$ instances under the 0-1 principle.
- **LLaMA 3.1 8B Instruct:** **4 / 10 passed (40.0%)**, replicating the 70B failure pattern on all constrained instances.

---

## 2. Empirical Benchmark Matrix (10 Representative Cases)

| Case ID | Problem Description | Parameters ($n, k$, prefix, forbidden) | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `c057_m01` | $n=4$ Unconstrained Optimal | $n=4, k=5$, prefix `[]`, forbid `[]` | **PASS** (1.34s) | **PASS** (0.60s) | **PASS** (0.31s) |
| `c057_m02` | $n=4$ Constrained (Prefix + Forbid) | $n=4, k=5$, prefix `[[0, 3]]`, forbid `[[0, 2]]` | **PASS** (1.22s) | **FAIL** (0.41s, unsorted `[1, 1, 0, 1]`) | **FAIL** (0.46s, unsorted `[0, 1, 1, 0]`) |
| `c057_m03` | $n=5$ Unconstrained Optimal | $n=5, k=9$, prefix `[]`, forbid `[]` | **FAIL** (0.91s, unsorted `[1, 1, 1, 0, 0]`) | **FAIL** (1.75s, unsorted `[1, 0, 1, 0, 1]`) | **FAIL** (0.84s, unsorted `[1, 1, 1, 0, 0]`) |
| `c057_m04` | $n=5$ Constrained (Prefix + Forbid) | $n=5, k=10$, prefix `[[0, 1], [2, 3]]`, forbid `[[0, 4]]` | **PASS** (0.66s) | **FAIL** (0.58s, unsorted `[1, 1, 1, 1, 0]`) | **FAIL** (0.47s, unsorted `[1, 0, 0, 0, 0]`) |
| `c057_m05` | $n=6$ Unconstrained Optimal | $n=6, k=12$, prefix `[]`, forbid `[]` | **FAIL** (empty JSON) | **FAIL** (0.41s, $len=15 > 12$) | **FAIL** (0.48s, unsorted `[1, 1, 1, 0, 0, 0]`) |
| `c057_m06` | $n=6$ Constrained | $n=6, k=12$, prefix `[[0, 5], [1, 3], [2, 4]]`, forbid `[]` | **FAIL** (empty JSON) | **FAIL** (0.23s, unsorted `[1, 0, 0, 0, 0, 1]`) | **FAIL** (0.14s, unsorted `[0, 1, 0, 1, 0, 0]`) |
| `c057_m07` | $n=8$ Unconstrained Optimal | $n=8, k=19$, prefix `[]`, forbid `[]` | **FAIL** (empty JSON) | **FAIL** (0.56s, unsorted `[1, 1, 0, 0, 0, 0, 0, 0]`) | **FAIL** (0.63s, unsorted `[1, 0, 1, 0, 1, 0, 1, 0]`) |
| `c057_m08` | $n=4$ Infeasible Bound | $n=4, k=4 < \lceil\log_2 4!\rceil=5 \to$ `UNKNOWN` | **PASS** (1.20s) | **PASS** (0.57s) | **PASS** (0.93s) |
| `c057_m09` | $n=9$ Infeasible Bound | $n=9, k=24 < 25 \to$ `UNKNOWN` | **PASS** (0.63s) | **PASS** (0.61s) | **PASS** (0.33s) |
| `c057_m10` | Poisoned Prefix (Reversed) | $n=4, k=5$, prefix `[[3, 0]] \to$`OUT_OF_SCOPE` | **PASS** (0.60s) | **PASS** (0.42s) | **PASS** (0.13s) |
| **Total** | **Summary Accuracy** | **10 Instances** | **6 / 10 (60.0%)** | **4 / 10 (40.0%)** | **4 / 10 (40.0%)** |

---

## 3. Key Observations & Failure Modes

### 1. Defeating Recitation via Prefix and Forbidden Constraints
As predicted by the specification, standard LLMs (LLaMA 3.3 70B and LLaMA 3.1 8B) can recite standard textbook networks for $n=4$ (e.g. $[[0, 2], [1, 3], [0, 1], [2, 3], [1, 2]]$), but fail immediately when forced to deviate:
- On Case 2 ($n=4$ with prefix $[[0, 3]]$ and forbidden $[[0, 2]]$), both LLaMA models emitted networks that looked plausible on casual inspection, but violated the 0-1 principle on input $[1, 1, 0, 1]$ and $[0, 1, 1, 0]$.
- Space Bunny Alpha, by contrast, performed chain-of-thought search, discovering the valid 5-comparator network $[[0, 3], [1, 2], [0, 1], [2, 3], [1, 2]]$ which respects both the prefix and the forbidden pair.

### 2. Search Complexity Scaling for $n \ge 5$
- For $n=5$, both LLaMA models hallucinated networks of size 9 that failed on binary vectors with three 1s and two 0s.
- For $n \ge 6$, Space Bunny Alpha's internal reasoning loop exceeded OpenRouter's proxy token threshold or output empty completions, indicating that raw unguided autoregressive search scales poorly without search-space factorization or symbolic curriculum ladders.

---

## 4. Claim Hygiene Assessment

1. **What it supports:**
   - In this experimental setup, Space Bunny Alpha achieved 60.0% accuracy on 10 sorting network synthesis instances, outperforming LLaMA 3.3 70B and 8B (40.0%).
   - The dual checkers successfully verified all valid sorting networks using the 0-1 principle and detected subtle 1-bit sorting failures across all evaluated models.
   - Hostile mutation testing demonstrated 100% kill rate (48/48) across all structural corruptions.

2. **What it does not support:**
   - It does not support any general optimality claim for comparator sorting networks for $n > 12$.
   - It does not demonstrate that autoregressive language models can reliably synthesize optimal sorting networks for large $n$ without symbolic verification tools.

3. **Narrowest Defensible Claim:**
   - Under the declared SG-CP v1 protocol and 0-1 principle checker, Space Bunny Alpha successfully synthesized valid constrained sorting networks for $n=4$ and $n=5$ where standard dense models failed, while all models correctly recognized lower-bound infeasibility and input malformations.

4. **Next Test Needed:**
   - Advance to Challenge C058: Straight-Line Superoptimization, evaluating bit-vector equivalence and instruction reduction certificates.
