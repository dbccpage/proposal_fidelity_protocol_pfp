# C006: Host-Maintained Scratch Space vs Chain of Thought

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to reach an
> exact coboundary repair on boards of cycle rank 3 to 8 more often with a host-maintained
> scratch space than with in-context chain of thought, for under $0.50.

## 2. Why This Task

The Round-5 trace in `research/mssn_sn_tower/demos/anti_morphism_observations.md` is the target. On K4 (cycle rank b₁ = |E| − |V| + 1 = 6 − 4 + 1 = 3) with claims a→b = 1, b→c = 2, c→a = 3, b→d = 1, d→a = 2, c→d = 1, `qwen/qwen-2.5-7b-instruct` asserted all six edges, fixed cycle 1 through the chord c→a = −3, then regressed: it re-asserted edges and repeated an unchanged CUT until fuel ran out at Φ₁ = 8. The two remaining chord values, b→d = −3 and c→d = −5, were never proposed. That is AM-4, the idempotent stationary attractor. On the diamond (b₁ = 2) the same model reached Φ₁ = 0 in 9 turns once the host supplied residuals and decoupling guidance (Round 4e).

The hypothesis is that the model loses track of which cycles are closed, not that it cannot compute one chord. If so, a host that keeps the state (asserted edges, per-cycle residuals, closed chords, the last move's digest) and shows it compactly each turn should break the attractor. Chain of thought keeps that state inside the context, where it competes with history. The challenge stresses the Symbol Game turn loop and cemetery, OEWAS (Omega Engine Workflows, Agents, Skills) working-memory design, and the OEEIS (Omega Engine Epistemic Immune System) AM-4 detector. A pass would show the host ledger beats in-context state tracking on these boards. It would not show that the model understands cohomology.

## 3. Formal Problem and Bounds

A board is a connected directed graph with integer claims c_e and positive integer weights; the goal is an exact cochain c' (Φ₁(c') = 0, i.e. c' = δφ for some potential φ) reached through host-admitted moves under strict descent. Moves are the Symbol Game's `ASSERT`, `CUT` (a proposed full cochain), `LIFT_REQUEST` and `VERIFY`. The host admits a CUT only if Φ₁ strictly decreases or reaches 0, and ends the session at `ACCEPTED_ZERO_DEFECT` after a valid `VERIFY` at Φ₁ = 0, or at `SURVIVOR_OBSTRUCTION` when fuel runs out. Fuel is |E| + 3·b₁ turns.

Board families by cycle rank: K4 (3), K_{3,3} (4), the cube graph Q₃ (5), K5 and the Petersen graph (6), wheels W₇ and W₈ with 7 and 8 rim vertices (7 and 8). Each b₁ value follows from |E| − |V| + 1 and is recomputed by the checker. Claims are drawn so that every fundamental cycle has a nonzero sum and at least one tree edge lies on three or more fundamental cycles.

The hidden set must contain the Round-5 K4 board verbatim, boards where one fundamental cycle is already closed at the start, boards with a chord whose correct value is 0, and relabelled copies.

## 4. Deliverable and Output Contract

The frozen deliverable is a session pipeline: `pipeline.json` (model, route or local revision, prompt templates, scratch-space schema version, decomposition setting, fuel, decoding) and `solve.py` with `def solve(case: dict) -> dict`, which plays one full session and returns:

```json
{"status": "SOLVED", "final_cochain": {"a->b": "1", "c->a": "-3"}, "potential": {"a": "0", "b": "1"}, "turns": "11"}
{"status": "UNKNOWN", "refusal": "SURVIVOR_OBSTRUCTION", "phi1_final": "8", "turns": "15"}
```

`SOLVED` requires the host terminal `ACCEPTED_ZERO_DEFECT` and a potential φ with φ(v) − φ(u) equal to the final claim on every edge. The session transcript, not only the final object, is part of the output.

## 5. Participant Packet

- `TASK.md` with the move grammar, admission rules, fuel and the scratch-space schema.
- `examples/`: 12 public boards (two per b₁ from 3 to 7, excluding the Round-5 board) with exact input JSON, a reference admitted session and its final cochain.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 60 boards (10 per b₁ from 3 to 8).
- **Relabel controls:** 20 boards with renamed vertices and reversed edge orientations (reversing an edge negates its claim).
- **Poisoned but schema-valid:** 12 boards whose prompt history contains a stale, previously admitted CUT (so repeating it is stationary), and boards with a chord that must be set to exactly 0.
- **Exact checker:** Rust `omega_symbol_game` `verify_l1_certificate` and `exact_solve_l1_primal_dual` for Φ₁, plus a potential check.
- **Independent second checker:** Python `Fraction` potential propagation (`bench/head_to_head/host.py`).
- **Checker mutation suite:** a final cochain with one cycle sum of 1, a potential inconsistent with one edge, a `VERIFY` accepted at Φ₁ > 0, and an admitted CUT that increased Φ₁.

## 7. Arms and Baselines

All arms receive the same host facts each turn: Φ₁, the list of asserted edges and the fundamental-cycle residuals. They differ in where state lives.

- **A: Symbol Game with host scratch space (U12).** The host replaces the history with a typed ledger (asserted edges, current claims, per-cycle residuals, closed chords, last move digest, stationary counter) plus the last two turns. With U13, open cycles are offered as chord subturns (`SubTurnChordDecomposition`).
- **B: Chain of thought.** Full history with the same per-turn host facts appended, and an instruction to reason before each move. This matches information and isolates state management.
- **C: Representation ablation.** A's ledger rendered as prose.
- **D: Repeated sampling.** Whole sessions sampled independently, cost-matched to A; a session counts if any sample reaches `ACCEPTED_ZERO_DEFECT`.
- **E: No-model baseline.** The exact nearest-coboundary repair from `exact_solve_l1_primal_dual`; the ceiling.
- **F: Local mechanism.** Arm A on the local `Qwen/Qwen2.5-7B-Instruct` with grammar-masked move decoding (Layer 2), separating move-format failures from state-tracking failures.

No arm gets solution-bearing hints (proposed values). The chord list is structural and is given to A, C and F, and appended to B's history, so it is not a difference between arms.

## 8. Budget, Models and Provenance

Primary model `qwen/qwen-2.5-7b-instruct` (the Round-5 model), replication `meta-llama/llama-3.1-8b-instruct`, both hosted through the governed path with `allow_fallbacks: false`; arm F runs the local pinned revision. The $0.50 ceiling per arm is enforced before each call by `BudgetController`. Round 5 cost under $0.001 per 12-turn session, so the budget allows many sessions; the count is fixed in the pre-registration from observed cost. Every call records provider, model ID, generation ID, tokens and billed cost.

## 9. Pass Gates and Statistics

- **Primary metric:** sessions ending `ACCEPTED_ZERO_DEFECT` on the 60 hidden boards, A against B, exact McNemar, α = 0.05, primary seed; same sign on three seeds.
- **Secondary (Holm):** A against C and D; F against A.
- **AM-4 incidence:** the fraction of sessions with at least one stationary repeat (same canonical CUT digest against the same host state digest after a stationary result), per arm, with Wilson intervals.
- **Scaling:** success rate per b₁, per arm; the largest b₁ at which A's rate stays above 50%, reported.
- **Target case:** the Round-5 K4 board is reported individually in every arm and seed.

## 10. Interpretation

- **A beats B, and AM-4 incidence drops:** state kept by the host breaks the stationary attractor that in-context tracking falls into.
- **A beats B and ties C:** the ledger's content matters, not its typed format.
- **A ties D:** repeated sampling of sessions explains the gain; the ledger shows no additional benefit.
- **F beats A:** part of A's failure was move formatting, not state tracking.
- **A's advantage vanishes as b₁ grows:** the ledger postpones but does not remove the multi-constraint limit seen in Round 5.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **AM-4 detector** (catalog hook `antimorphism_AM4`): the `AM-4-STATIONARY-REPEAT` predicate of the proposed EIS finding schema. On firing, the host returns `REQUEST_DIFFERENT_CANDIDATE_OR_LIFT` with the typed diagnostic and no solution. Its near-miss fixture, a repeated CUT after the host state changed, must not fire; that is the thymus-style self check.
- **Treg analogue:** if the detector fires on more than a pre-registered share of turns, it is suspended for the session and the event logged (`TregSupervisor` pattern), so an over-active detector cannot consume the fuel.
- **Other antimorphisms expected:** AM-1 flat CUTs, AM-3 premature cuts, AM-5 global sign inversion.
- **Scratch space (U12):** the typed ledger. **Layer 2:** grammar-masked moves in arm F. **Layer 1:** none.

## 12. Run Folder, DDC Trace and Operand Mining

Each session writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01), including the rendered ledger bytes for every turn, so that what the model saw is on record.

Expected DDC pattern for a solved session: `C` (board exposed), `Λ` (lift into chord subturns, arm A with U13), then per open cycle `D` or `M` steps, `I` (integrate subturn results into one CUT), then `E` and `T`. The AM-4 failure appears as `D M M M …` with unchanged Φ₁. Logged measures: Φ₁, the number of open fundamental cycles, defect count, stationary counter, detector firings.

Operands this challenge should yield:

```text
operand chord_per_open_cycle.v1 | kind: decomposition | when: b1 >= 3 and tree edges are shared | do: fix each open cycle on its own chord, holding tree edges | check: that cycle's residual becomes 0 and Phi1 drops
operand stationary_escape.v1 | kind: guard | when: AM-4 fires | do: offer the list of open cycles and forbid the repeated digest | check: next CUT digest differs and Phi1 strictly drops
operand ledger_not_history.v1 | kind: control | when: sessions exceed 8 turns | do: replace history with the typed ledger plus two turns | check: success rate not below full history
```

## 13. Estate Reuse and Prerequisites

- `research/mssn_sn_tower/demos/anti_morphism_observations.md` (Rounds 4 to 5, the AM-4 schema and fixtures) and the Round-5 trace it cites under `research/mssn_sn_tower/demos/demo_1/traces/`.
- `omega_engine_symbol_game/domain/topology/subturn.py` (`SubTurnChordDecomposition`, `AttentionContextBoundary`, currently a data model only).
- `omega_engine_symbol_game/domain/immune/treg.py`; `omega_engine/crates_rs/omega_symbol_game` (Φ₁ and certificates).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: [U12](../../upgrades/u12_host_scratch_space_working_memory.md), [U13](../../upgrades/u13_cohomological_task_decomposition.md). Arm F also needs [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md).

## 14. Claim Hygiene

- **Supports:** whether a host-kept typed ledger raises the rate of exact repairs on these boards against chain of thought with the same host facts, and how often AM-4 occurs in each.
- **Does not support:** that the model understands cohomology; that the ledger helps on tasks without a cycle structure; that Round 5's single trace was representative.
- **Narrowest defensible claim:** for these models and boards, moving state from context to a host ledger changed the paired solved rate by the measured amount and changed AM-4 incidence by the measured amount.
- **Next test:** long-horizon sessions in [C007](c007_context_compaction_kv_surgery.md) and the ledger inside the full coboundary-repair ladder of [C011](../b_cohomology/c011_cycle_rank_ladder_coboundary_repair.md).
