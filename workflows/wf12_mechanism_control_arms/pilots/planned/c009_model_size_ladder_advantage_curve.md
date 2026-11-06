# C009: Model-Size Ladder: Where Does the Game Help Most

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to measure the
> arm A minus arm B success gap on five anchor challenges across a 0.5B-to-70B model ladder,
> and locate where it peaks, for under $1.

## 2. Why This Task

A structured host loop could help most where a model is too weak to hold the task alone but strong enough to act on host feedback. Too small, and no scaffold helps (the 0.5B repair matrix reached zero in no arm); too large, and the model may not need it. That predicts an interior peak in the A−B gap, but the estate has no measurement: every existing comparison used one model. The [Q40 review](../00_q40_review.md) also showed how easily unmatched arms manufacture a gap, so the ladder must be matched rung by rung.

The five anchors span different kinds of work, each with an exact checker: [C021](../c_quantum/c021_q40_r_synthesis_as_intended.md) (stabilizer solver synthesis), [C011](../b_cohomology/c011_cycle_rank_ladder_coboundary_repair.md) (minimum-L1 coboundary repair), [C051](../f_program_synthesis/c051_exact_lp_solver_with_duals.md) (exact LP with dual and Farkas certificates), [C061](../g_chem_bio/c061_redox_equation_balancing.md) (equation balancing) and [C071](../h_economics/c071_bimatrix_all_nash_equilibria.md) (all Nash equilibria of bimatrix games). The challenge stresses the Symbol Game turn driver across scales, OEWAS (Engine Workflows, Agents, Skills) cost allocation (U21), and the OEEIS (Engine Epistemic Immune System) only as far as each anchor uses it. A pass gives a per-anchor advantage curve. It does not rank models in general.

## 3. Formal Problem and Bounds

For each anchor a and rung r, the measured quantity is the paired gap G(a, r) = success_A(a, r) − success_B(a, r) over that anchor's hidden base cases, where success is the anchor's own pass criterion per case. Cases are identical across rungs, so comparisons across rungs are paired too.

Each C009 cell is a reduced configuration of its anchor: same checker and hidden base cases, fewer seeds and a smaller budget (below). It is not a re-run of the anchor's capability gate, and a C009 cell passing or failing says nothing about the anchor's own pass.

Ladder (total parameters, pinned in the U06 registry):

| Rung | Model | Where |
| --- | --- | --- |
| 0.5B | `Qwen/Qwen2.5-0.5B-Instruct` | local |
| 3B | `Qwen/Qwen2.5-3B-Instruct` | local |
| 7B | `qwen/qwen-2.5-7b-instruct` | hosted, local copy for arm F |
| 8B | `meta-llama/llama-3.1-8b-instruct` | hosted |
| 14B / 32B | Qwen3-14B, Qwen3-32B (exact IDs pinned at packet-build time) | hosted |
| 70B | `meta-llama/llama-3.3-70b-instruct` | hosted |

`Qwen2.5-72B` is over the ceiling and is rejected. A rung with no pinned route is dropped and reported as dropped, never replaced with a nearby model.

## 4. Deliverable and Output Contract

Per cell, the frozen deliverable is exactly the anchor's deliverable (a synthesized `solve` for C021, C051 and C071; a repair pipeline for C011; a balancing pipeline for C061) under the anchor's output contract, plus a `ladder_cell.json` recording anchor, rung, arm, seed, pinned model, per-cell budget and the anchor's judge-packet hash. The ladder report is a table of G(a, r) with exact intervals and the raw per-case outcomes.

## 5. Participant Packet

Each anchor's participant packet, unchanged, plus `LADDER.md` (rungs, per-cell budget, seeds) and one `accounting.json` per cell.

## 6. Judge Packet

Each anchor's judge packet, unchanged: hidden base cases, relabel controls, poisoned cases, exact checker, second checker and mutation suite. The ladder adds no hidden cases, so every rung is scored on the same bytes. Relabel controls are reported per cell and never pooled.

## 7. Arms and Baselines

- **A: Symbol Game** and **B: Ordinary iterative** are the measured pair in every cell.
- **C: Representation ablation** and **D: Repeated sampling** run at three rungs only (3B, 8B, 70B) to keep the budget, which shows whether any gap is the representation or the sampling.
- **E: No-model baseline:** each anchor's deterministic tool, run once (it has no rung).
- **F: Local mechanism:** at the 7B rung only, arm A plus the best frozen control from [C004](c004_grammar_masked_decode_ladder.md) (grammar-masked moves), to check whether a Layer-2 control shifts where the gap peaks.

## 8. Budget, Models and Provenance

The $1.00 ceiling is per arm across the whole ladder, not per cell. With 5 anchors and 5 hosted rungs there are 25 hosted cells per arm, so each gets an equal pre-registered share of $0.04. That is a tightening of the anchors' own ceilings, which the protocol allows. At the blended rate recorded in the Q40 review for `meta-llama/llama-3.3-70b-instruct` (about $0.00000035 per token), $0.04 buys roughly 110,000 tokens; prices at the other rungs are recorded at packet-build time, not assumed. Local rungs bill $0; their compute is recorded and priced at a pre-registered local rate (U21). `BudgetController` enforces each cell's share before each call, and an exhausted cell ends `UNKNOWN` with `BUDGET_EXHAUSTED`. Every call records provider, model ID, generation ID, tokens and billed cost with `allow_fallbacks: false`.

## 9. Pass Gates and Statistics

- **Validity gate:** every cell's arms A and B were matched on model, route, tools, examples, caps and budget share (checked by U08 from the receipts).
- **Primary metric:** G(a, r) per cell with an exact McNemar test on paired cases, Holm-corrected across the 35 cells (5 anchors by 7 rungs), α = 0.05. Three seeds per cell; the primary seed decides, the others must agree in sign.
- **Peak claim:** a peak at rung r*for anchor a is claimed only if G(a, r*) exceeds G at each adjacent rung under a paired permutation test on per-case gap differences (cases are shared across rungs), Holm-corrected.
- **Economics:** cost per verified success per cell for A and B.

## 10. Interpretation

- **An interior peak on most anchors:** the game helps most in a middle band of model sizes, where feedback can be used but the task cannot be held alone.
- **Gap grows with size:** larger models exploit the host loop better; the scaffold is not a small-model crutch.
- **Gap shrinks to zero at 70B:** at the top of the ceiling the ordinary loop suffices for these anchors.
- **A ties C or D wherever A beats B:** the advantage is the controller or sampling, not the packet representation.
- **All gaps near zero:** these anchors at these budgets do not distinguish the game at any size.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook. Each anchor's own immune hooks (for example kinetic proofreading in C011) run unchanged in arm A at every rung, so any hook effect is part of A.
- **Antimorphisms expected by size:** prose instead of moves at the smallest rungs; AM-4 stationary loops at 7B to 8B (as in Round 5); confident false witnesses (AM-FSP-2) at larger rungs.
- **Layer 2:** grammar-masked moves in arm F at 7B. **Layer 1:** none.
- **Scratch space:** whatever each anchor's arm A uses, unchanged.

## 12. Run Folder, DDC Trace and Operand Mining

Each cell and seed writes RunFolderV1 bundles under `_intelligence/symbol_game/runs/<run_id>/` (U01) tagged with anchor and rung, so mining (U02) can compare DDC words across sizes.

Expected pattern: at small rungs `C M M M T`; in the middle band `C (D|M)* E T` with long `D` runs; at the top `C D E T` with few turns. The size at which `E` first appears regularly is the mining target. Logged measures: each anchor's obstruction measure (Φ₁ for C011, checker failure counts for synthesis anchors), turns, tokens.

Operands this challenge should yield:

```text
operand rung_router.v1 | kind: control | when: a task family has a measured gap curve | do: send it to the cheapest rung whose A success interval clears the target | check: cost per verified success not above the next rung up
operand small_model_grammar.v1 | kind: control | when: the rung is below the gap peak | do: enable grammar-masked moves | check: parseable rate rises and A success does not fall
operand size_specific_antimorphism.v1 | kind: guard | when: the rung is 7B to 8B and a session exceeds 8 turns | do: enable the AM-4 detector | check: stationary repeats per session fall
```

## 13. Estate Reuse and Prerequisites

- `bench/matrix/run_matrix.py` (model sweeps, append-only, gitignored `bench/results/runs.jsonl`) and `bench/matrix/aggregate.py` (paired comparisons with Wilson intervals).
- Each anchor's estate reuse as listed in `catalog.yaml`.
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md) (local rungs and arm F), [U21](../../upgrades/u21_economic_compute_allocation.md) (per-cell budget shares and local compute pricing). The anchors' own extras (U10 and U14 for C021; U13 for C011; U10 for C051) are prerequisites for their cells.

## 14. Claim Hygiene

- **Supports:** for these anchors, rungs and per-cell budgets, where the paired A−B gap is largest and whether it is explained by representation or sampling.
- **Does not support:** a general scaling law; any ranking of model families; any statement about the anchors' own capability gates.
- **Narrowest defensible claim:** at the stated per-cell budget, the A−B gap on anchor a was largest at rung r*, by the measured amount with the stated corrected p.
- **Next test:** give the peak rung the anchor's full budget and seeds, and route new families by the curve (operand `rung_router.v1`) in [C010](c010_repeated_sampling_frontier.md).
