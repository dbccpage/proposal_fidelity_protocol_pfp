# C010: Repeated-Sampling Frontier and Cost per Verified Success

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to trace
> coverage@k and cost per verified success for best-of-N, iterative and hybrid strategies at
> fixed budget points, and find which strategy is cheapest per verified success, for under $0.50.

## 2. Why This Task

Repeated sampling is the obvious baseline for any task with a cheap exact verifier. Brown et al. (2024, *Large Language Monkeys*) found that coverage, the fraction of problems solved by at least one of k samples, keeps rising with k over several orders of magnitude, and that in domains with automatic verifiers this converts directly into solved problems. The [Q40 review](../00_q40_review.md) noted that the Q40 synthesis trial never tried it, although its budget allowed several hundred attempts. Every Symbol Game claim should therefore be read against the sampling frontier: if best-of-N reaches the same success for the same money, the game's structure has shown no additional benefit (protocol §9, "A and D tie").

This challenge draws that frontier once, carefully, so later challenges can cite it. It stresses the governed provider path and its cost records, the Symbol Game's iterative loop, OEWAS (Engine Workflows, Agents, Skills) compute allocation (U21), and none of the OEEIS (Engine Epistemic Immune System) mechanisms. A pass gives a cost-per-verified-success frontier for this task pool. It does not show that any strategy is best elsewhere.

## 3. Formal Problem and Bounds

The task pool is 120 hidden certificate-bearing cases, 40 from each of three families with exact input-only certificate checks: minimum-L1 coboundary repair ([C011](../b_cohomology/c011_cycle_rank_ladder_coboundary_repair.md), b₁ ≤ 6), integral homology with Smith normal form certificates ([C013](../b_cohomology/c013_integral_homology_torsion.md), complexes of at most 60 simplices) and equation balancing ([C061](../g_chem_bio/c061_redox_equation_balancing.md)). Because each certificate is checked from the case input alone, any arm may verify its own candidates at inference time; that check is not the judge, which rescores everything independently.

For a strategy with n samples per case of which c verify, coverage@k is estimated with the unbiased estimator 1 − C(n − c, k) / C(n, k) (Chen et al. 2021), for k ≤ n.

Budget points per arm: **$0.01, $0.10 and $0.50**. The catalog summary names a $1 point; the T2 ceiling is $0.50 per arm, and the protocol forbids relaxing a ceiling. The $1 point is therefore not run under this spec. Running it needs C010 re-tiered to T3 in `catalog.yaml` first.

## 4. Deliverable and Output Contract

The frozen deliverable per arm is a strategy (`strategy.json`: sampler settings, N or turn policy, stop rule, how a verified candidate is chosen) plus `solve.py` that answers each case with the family's output contract (for example the C011 `SOLVED` object with potential, repair and dual certificate), or `UNKNOWN` with `BUDGET_EXHAUSTED` or `NO_VERIFIED_CANDIDATE`. The frontier report gives, per strategy and budget point, coverage@k curves, verified-success counts and cost per verified success with intervals, and every sample's raw text and verdict.

## 5. Participant Packet

- `TASK.md` with the three families' contracts, the estimator and the budget points.
- `examples/`: 30 public cases (10 per family) with exact input and output JSON.
- `runner.py`, `accounting.json` with one row per call.

## 6. Judge Packet

- **Hidden base cases:** the 120 cases above.
- **Relabel controls:** 24 cases (8 per family) under each family's relabelling.
- **Poisoned but schema-valid:** 12 cases per family from those families' own poisoned sets, for example C011 cases where a zero-reaching repair is not minimal.
- **Exact checkers:** the three families' Rust checkers.
- **Independent second checkers:** the three families' second checkers.
- **Checker mutation suite:** each family's suite, plus a sampled answer copied from another case (valid shape, wrong case).

## 7. Arms and Baselines

- **A: Symbol Game (hybrid).** The U05 turn driver with k parallel first proposals, then iterative host-guided repair of the best-scoring candidate, per the U21 allocation rule.
- **B: Ordinary iterative.** One trajectory of propose, check and repair.
- **C: Representation ablation.** Arm A's hybrid with plain-text packets.
- **D: Repeated sampling.** Independent samples at the pre-registered temperature, each verified by the input-only check; stop at the first verified sample or at the budget point.
- **E: No-model baseline.** The families' deterministic solvers; cost is tool time only.
- **F: Local mechanism.** Arm D on the local copy of the primary model with the best grammar control from [C004](c004_grammar_masked_decode_ladder.md), to show how an exact decoding control moves the sampling frontier.

## 8. Budget, Models and Provenance

Primary model `meta-llama/llama-3.1-8b-instruct`, replication `meta-llama/llama-3.3-70b-instruct`, hosted with `allow_fallbacks: false`. `BudgetController` enforces each budget point before each call; a strategy that exhausts a point stops there, and the cases it did not reach count as unsolved at that point. Every call records provider, model ID, generation ID, tokens and billed cost. Local compute in arms E and F is priced at the pre-registered local rate. Prices are read at packet-build time, not assumed.

## 9. Pass Gates and Statistics

- **Validity gate:** every counted success is rescored by the judge's checker and second checker; no success is counted from the arm's own check alone.
- **Primary metric:** verified successes at the $0.50 point, A against D, exact McNemar on the 120 paired cases, α = 0.05; three seeds, primary seed decides, sign agreement required.
- **Secondary (Holm):** A against B and C at each budget point; D against B.
- **Frontier:** cost per verified success per strategy and point, with bootstrap intervals over cases; coverage@k curves with the Chen et al. estimator.
- **Crossover:** the lowest budget point at which A's verified count exceeds D's, if any.

## 10. Interpretation

- **D matches or beats A at every point:** repeated sampling explains any success the game has here; the game's structure shows no additional benefit on this pool.
- **A beats D at $0.50 but not at $0.01:** structure pays once there is budget for iteration.
- **B beats D:** iterative repair uses host feedback better than independent draws on these families.
- **F shifts D's frontier down:** an exact decoding control lowers the cost of sampling, independent of the game.
- **E dominates all arms on cost:** useful automation; the model arms add no economic value for these families.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; none used, so the frontier is a clean baseline for later OEEIS challenges.
- **Antimorphisms expected:** duplicate samples (many identical wrong answers at low temperature), and schema-valid false certificates that the input-only check rejects.
- **Layer 2:** grammar control in arm F only. **Layer 1:** none.
- **Scratch space:** none beyond each family's contract.

## 12. Run Folder, DDC Trace and Operand Mining

Each case and strategy writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01) with every sample kept, verified or not (zero data loss).

Expected DDC patterns: arm D is `C (M)* E T` or `C M… T`, with no `D` because samples are independent; arms A and B show `C M D D E T`-style descent. The mining target is the ratio of `D` steps that reduced the family's obstruction measure to `M` refusals, per strategy. Logged measures: per-sample verified flag, the family's obstruction measure, tokens, billed cost.

Operands this challenge should yield:

```text
operand sample_then_repair.v1 | kind: control | when: first-sample verified rate is below 20% | do: draw k samples, then repair the best-scoring one | check: cost per verified success below pure sampling
operand dedupe_before_verify.v1 | kind: control | when: samples repeat | do: verify each distinct canonical answer once | check: checker calls equal distinct answers
operand stop_at_first_verified.v1 | kind: control | when: the certificate check needs only the input | do: stop sampling at the first verified candidate | check: judge rescoring agrees
```

## 13. Estate Reuse and Prerequisites

- `bench/matrix/aggregate.py` (paired comparisons, Wilson intervals, append-only, gitignored `bench/results/runs.jsonl`).
- The checkers named in C011, C013 and C061.
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrade: [U21](../../upgrades/u21_economic_compute_allocation.md). Arm F also needs [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md).

## 14. Claim Hygiene

- **Supports:** for this pool, model pair and the $0.01, $0.10 and $0.50 points, the cost per verified success of sampling, iterative and hybrid strategies, and whether the game beats best-of-N.
- **Does not support:** any claim at $1 (not run); any claim for tasks without an input-only certificate check; general scaling laws.
- **Narrowest defensible claim:** at $0.50 per arm on these 120 cases, the hybrid game arm and best-of-N differed by the measured number of verified successes, with the stated McNemar p and cost per verified success.
- **Next test:** re-tier to T3 and add the $1 point; then use this frontier as arm D's reference in every C-series report.
