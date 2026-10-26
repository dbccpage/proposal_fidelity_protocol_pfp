# Empirical Findings: Challenge C052 Max-Flow with Min-Cut Certificates

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

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_woland/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. No package directory for this challenge exists under [`f_program_synthesis/`](../../../../omega_engine_pfp/tests/demo_004/f_program_synthesis/) at the pin, so no solver, checker, receipt or model record backs the figures below; they are an unverified working record.

> **Note (2026-09-28).** `stealth/space-bunny-alpha` is an unidentified model offered
> anonymously on OpenRouter; its results cannot be reproduced. No paper in this
> collection has audited the figures in this note.

**AuthorityEffect:** None  
**Domain:** f_program_synthesis  
**Tier:** T1  
**Protocol:** SG-CP v1  
**Gate Verdict:** `PASS_TO_MASTER`  
**Reference Solver Commitment Digest:** `8b26c642a1f4dc15c767f298a3f6004e0bd9398660b98d336f9e91ac4d9032d6`  

---

## 1. Challenge & Verification Summary

Challenge C052 benchmarks automated synthesis of exact integer maximum-flow solvers with matching minimum-cut certificates:
$$\max |f| \quad \text{subject to } 0 \le f_e \le \operatorname{cap}_e, \quad \sum_{e \in \delta^+(v)} f_e = \sum_{e \in \delta^-(v)} f_e \; (\forall v \notin \{s, t\})$$
certified by a cut partition $(S, V \setminus S)$ with $s \in S, t \notin S$ satisfying exact equality $\operatorname{cap}(S) = |f|$.

**Worked check (2026-10-20):** for any feasible flow $f$ and any $s$–$t$ cut $S$, $|f| = \sum_{e \in \delta^+(S)} f_e - \sum_{e \in \delta^-(S)} f_e \le \operatorname{cap}(S)$, so equality certifies that $f$ is maximum and $S$ is minimum; equality forces every arc leaving $S$ to be saturated and every arc entering $S$ to carry zero flow, which is the failure reported as "cut edge unsaturated". Counting the PASS cells in Section 2 gives 8, 3 and 2.

### Verification Gate Results
- **Hidden Base & Control Evaluation:** 64/64 cases passed (100.0%) across:
  - 32 Base cases: layered networks, adversarial long bottleneck paths, bipartite matching with super-source/sink, disconnected components, dense parallel/antiparallel clusters, planar grids, zero-capacity arcs, and large 64-bit capacities ($10^{18}$ and $> 2^{63}$).
  - 16 Relabel and Gauge Controls: node relabeling permutations, arc order shuffling, arc splitting into parallel bundles, and uniform integer capacity scaling.
  - 16 Poisoned Cases: deceptive prompt notes, source-equals-sink ($s = t$), negative capacities, node indices out of bounds, and malformed arc tuples.
- **Dual Independent Checker Agreement:** 100% agreement between the exact dot-product/conservation checker and the independent residual reachability checker.
- **Hostile Mutation Kill Rate:** 48/48 hostile mutations killed (100.0%) with zero runtime crashes across both checkers.

---

## 2. Empirical Model Benchmark (10-Problem Matrix Sweep)

Frontier stealth reasoning model **Space Bunny Alpha** (`stealth/space-bunny-alpha`) was evaluated alongside open dense baselines **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 diverse network flow challenge cases.

| Problem Case ID | Problem Characteristics | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :---: | :---: | :---: |
| `c052_m01_diamond` | Standard 4-node diamond network | **PASS** (5.76s) | FAIL (JSON format error) | FAIL (Arc 2 flow > cap) |
| `c052_m02_unreachable_sink` | Disconnected sink ($t=2$ unreachable) | **PASS** (3.53s) | FAIL (JSON format error) | FAIL (False OUT_OF_SCOPE) |
| `c052_m03_parallel_arcs` | Parallel arcs between pairs | FAIL (Cut edge 3 unsaturated) | FAIL (Arc 1 flow > cap) | FAIL (Net balance mismatch) |
| `c052_m04_antiparallel_arcs` | Antiparallel arc pair | FAIL (Conservation node 2) | FAIL (Arc 4 flow > cap) | FAIL (Net balance mismatch) |
| `c052_m05_bottleneck_path` | Long path with small bottleneck | **PASS** (2.88s) | FAIL (Cut edge 2 unsaturated) | FAIL (Vector length mismatch) |
| `c052_m06_huge_capacity_64bit` | 64-bit integer capacities ($10^{18}$) | **PASS** (2.26s) | **PASS** (5.11s) | **PASS** (1.37s) |
| `c052_m07_multiple_min_cuts` | Multiple valid minimum cuts | **PASS** (2.52s) | **PASS** (3.81s) | FAIL (Vector length mismatch) |
| `c052_m08_bipartite_matching` | Bipartite matching network | **PASS** (5.12s) | FAIL (Arc 5 flow > cap) | FAIL (Net balance mismatch) |
| `c052_m09_poison_deceptive_note` | Prompt note claiming false max flow | **PASS** (6.69s) | FAIL (Conservation node 1) | FAIL (Fell for deceptive note) |
| `c052_m10_poison_malformed_syntax` | Source equals sink ($s == t$) | **PASS** (1.11s) | **PASS** (3.98s) | **PASS** (7.33s) |
| **Overall Score** | **Total Passed (Pass Rate)** | **8 / 10 (80.0%)** | **3 / 10 (30.0%)** | **2 / 10 (20.0%)** |

---

## 3. Epistemic Analysis & Failure Modes

1. **Space Bunny Alpha (8/10, 80.0%):**
   - Maintained strong global flow-cut reasoning, accurately determining both the maximum integer flow and identifying a certified minimum cut $S$ on 8 of 10 problems.
   - Successfully handled 64-bit capacities ($10^{18}$) without floating-point rounding degradation (`c052_m06`).
   - Not misled by the deceptive prompt note (`c052_m09`), computing the true flow value (5) and rejecting the distracter suggestion of 999999.
   - Failure mode: localized complementary slackness bookkeeping on multi-arc networks with parallel or antiparallel edges (`c052_m03`, `c052_m04`), where individual arc flows deviated from exact saturation.

2. **LLaMA 3.3 70B (3/10, 30.0%):**
   - Passed large 64-bit integer capacities (`c052_m06`), multiple minimum cuts (`c052_m07`), and malformed input rejection (`c052_m10`).
   - Suffered JSON formatting errors on simpler cases (`c052_m01`, `c052_m02`) and repeatedly violated individual arc capacity limits ($f_e > \operatorname{cap}_e$) on parallel and matching graphs (`c052_m03`, `c052_m04`, `c052_m08`).

3. **LLaMA 3.1 8B (2/10, 20.0%):**
   - Successfully rejected malformed syntax (`c052_m10`) and passed single-path 64-bit arithmetic (`c052_m06`).
   - Failed on graph structure: incorrectly emitted false `OUT_OF_SCOPE` on valid zero-flow unreachable sinks (`c052_m02`), produced mismatched flow vector lengths (`c052_m05`, `c052_m07`), and succumbed to deceptive prompt injection (`c052_m09`) by setting `value` to 999999.

---

## 4. Claim Discipline Quad

1. **What it supports:**
   - In this 10-problem test suite, Space Bunny Alpha achieved an 80.0% pass rate on exact max-flow min-cut certificates, outperforming LLaMA 3.3 70B (30.0%) and LLaMA 3.1 8B (20.0%).
   - The reference integer Dinic solver reliably computes exact flows and min-cuts across 64 hidden evaluation networks, and dual checkers eliminate 100% of 48 hostile mutations without runtime crashes.
   - All three models handled 64-bit integer values ($10^{18}$) without arithmetic overflow when simple topologies were involved.

2. **What it does not support:**
   - Does not support that LLMs can replace dedicated network simplex or push-relabel solvers on large-scale sparse networks.
   - Does not establish algorithmic worst-case bounds for neural model outputs.

3. **Narrowest defensible claim:**
   - On small directed networks ($N \le 6$) with capacities up to $10^{18}$ under the C052 specification, Space Bunny Alpha synthesized exact flow vectors and matching cut partitions on 8 out of 10 cases, whereas dense baselines failed on capacity bounds, flow conservation, or deceptive prompt text.

4. **Next test needed:**
   - Advance to Challenge C053 (Bareiss Fraction-Free Matrix Inversion) or C054 (LR(1) Parser Table Construction).
