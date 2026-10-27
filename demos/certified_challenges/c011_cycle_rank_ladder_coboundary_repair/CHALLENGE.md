# C011: Cycle-Rank Ladder: Minimum-L1 Coboundary Repair

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that returns a minimum-weight L1 repair making a 1-cochain exact, with a
> potential and an LP dual certificate, on hidden graphs of cycle rank 1 to 16, for under $0.50.

## 2. Why This Task

This is the Symbol Game's home problem written as a certificate task. The live traces show where models break: on the diamond (b₁ = 2) a 7B model reached Φ₁ = 0 with host guidance; on K4 (b₁ = 3) it fixed one cycle and fell into the AM-4 stationary attractor (`research/mssn_sn_tower/demos/anti_morphism_observations.md`). Reaching Φ₁ = 0 is also not the same as a minimal repair. Repairing each fundamental cycle on its own chord reaches zero, but when a tree edge lies on several cycles, repairing that shared edge can be cheaper. So generation is hard in two ways (find an exact cochain; find the cheapest one), while verification is cheap: a potential and a dual circulation certify optimality in linear time.

The challenge stresses the Symbol Game's retraction loop and strict descent, OEWAS (Engine Workflows, Agents, Skills) task decomposition by cycles (U13), and the OEEIS (Engine Epistemic Immune System) kinetic proofreading gate. A pass shows the game can produce a certified minimum-L1 repair solver up to b₁ = 16. It does not show anything about degree-2 obstructions, which belong to [C019](c019_h2_obstruction_extension.md).

## 3. Formal Problem and Bounds

Input: a directed graph G = (V, E) without self-loops (parallel edges allowed), claims c ∈ Q^E, weights w ∈ Q^E with w_e > 0. For φ ∈ Q^V, (δφ)_e = φ(head) − φ(tail). The obstruction is

Φ₁(c) = min over φ ∈ Q^V of Σ_e w_e |c_e − (δφ)_e|,

and c is exact iff Φ₁(c) = 0. The repair is r = c − δφ*, so c − r is a coboundary. LP duality gives

Φ₁(c) = max { Σ_e c_e y_e : y a circulation (net flow zero at every vertex), |y_e| ≤ w_e },

because ⟨δφ, y⟩ = 0 for every circulation y. A pair (φ, y) with y feasible and Σ w_e |r_e| = Σ c_e y_e certifies optimality; equivalently, complementary slackness holds (y_e = w_e · sign(r_e) wherever r_e ≠ 0). When c and w are integral, an integral optimal φ exists, because incidence matrices are totally unimodular.

Cycle rank b₁ = |E| − |V| + (number of connected components). Bounds: 1 ≤ b₁ ≤ 16, |V| ≤ 60, |c_e| ≤ 10^6 except a subfamily with |c_e| up to 10^20 (beyond 64-bit), weight denominators ≤ 12.

**Worked public example (checked by hand for this spec).** The Round-4e diamond: a→b = 1, b→c = 2, c→a = 3, b→d = 1, d→a = 2, with weights equal to the claims (1, 2, 3, 1, 2). Then Φ₁ = 8. A primal optimum repairs a→b by 4 and b→c by 2 (cost 4 + 2·2 = 8), with potential φ(a) = 0, φ(b) = −3, φ(c) = −3, φ(d) = −2. A dual optimum is y = (a→b 1, b→c 2, c→a 2, b→d −1, d→a −1), a circulation within the weights with Σ c_e y_e = 1 + 4 + 6 − 1 − 2 = 8. Repairing only the chords c→a and d→a reaches zero at cost 3·6 + 2·4 = 26.

The hidden set must contain already-exact cochains (Φ₁ = 0, empty repair, y = 0), forests (b₁ = 0 in one component), disconnected graphs, parallel edges, ties with several optimal repairs (any optimum is accepted), and the 10^20 subfamily.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, synthesized by the arm, run in the sandbox (U09):

```json
{"status": "SOLVED", "phi1": "8", "potential": {"a": "0", "b": "-3", "c": "-3", "d": "-2"}, "repair": {"a->b": "4", "b->c": "2"}, "dual": {"a->b": "1", "b->c": "2", "c->a": "2", "b->d": "-1", "d->a": "-1"}}
{"status": "OUT_OF_SCOPE", "witness": {"edge": "e7", "reason": "NONPOSITIVE_WEIGHT"}}
{"status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"}
```

Rationals are canonical strings (`"-3"`, `"5/12"`; never `"1/1"` or decimals). Omitted repair and dual entries are zero. A certificate is complete when: repair = c − δ(potential) on every edge; the dual is a circulation with |y_e| ≤ w_e; and Σ w_e |r_e| = Σ c_e y_e = phi1. `OUT_OF_SCOPE` covers self-loops, unknown endpoints and nonpositive weights.

## 5. Participant Packet

- `TASK.md` with the definitions above and the canonical rational format.
- `examples/`: 24 public cases with exact input and output JSON: the diamond above, the Round-5 K4 board (unit weights and claim weights), one case per b₁ from 1 to 12, one already exact, one disconnected, two with parallel edges, and three `OUT_OF_SCOPE` inputs.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 48 (three per b₁ from 1 to 16).
- **Relabel and gauge controls:** 24. Vertex renaming; reversing an edge (negates c_e; Φ₁ unchanged; that repair entry flips sign); adding a coboundary δψ to c (Φ₁ unchanged; the potential shifts by ψ).
- **Poisoned but schema-valid:** 16. Cases where chord-only repair reaches zero but costs more than the optimum; cases where the cheapest edge per unit is a shared tree edge; weights that make two different repairs tie; claims near 10^20.
- **Exact checker:** `core_functional`'s `Phi1Functional::verify_exact_certificate`, reached through the `core_symbol_game` binary's `verify_l1_certificate`.
- **Independent second checker:** a separately written Python `Fraction` verifier of the three certificate conditions, plus `exact_solve_l1_primal_dual` recomputing Φ₁ independently of the submission.
- **Checker mutation suite:** a dual with one |y_e| = w_e + 1/12; a dual with one vertex imbalance; a potential off by one at one vertex; phi1 off by 1/12; `"1/1"`; `"0.5"`; a zero-reaching non-optimal repair with a dual that is feasible but has a smaller objective.

## 7. Arms and Baselines

- **A: Symbol Game.** The U05 turn driver synthesizes `solve`, with public-example feedback and U13 decomposition of the task into per-cycle subproblems.
- **B: Ordinary iterative.** Plain-language synthesis with the same tools and history.
- **C: Representation ablation.** A's controller and checks with plain-text packets.
- **D: Repeated sampling.** Independent whole solvers, filtered on public examples, cost-matched.
- **E: No-model baseline.** `core_solvers::solve_weighted_l1_projection` (exact sparse simplex over Q with a dual witness), wrapped as `solve`. It is expected to solve every case; if A matches E, the result is useful automation without an incremental model advantage.

Arm F does not apply (catalog arms A–E).

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, Qwen3-32B, `deepseek/deepseek-r1-distill-llama-70b`; one is pinned before the run with its revision and route in the U06 registry. $0.50 per arm, enforced before each call by `BudgetController`, covering all construction, debugging and selection. Every call records provider, model ID, generation ID, tokens and billed cost with `allow_fallbacks: false`. The sandbox provides the Python standard library only, so no arm can import an LP package. U10 (stateful synthesis) is not a catalog requirement here, but a synthesis arm without it repeats the Q40 failure modes described in [the Q40 review](../00_q40_review.md), so the operator should build this challenge after U10.

## 9. Pass Gates and Statistics

- **Capability gate:** 48/48 hidden base cases with complete certificates, every relabel and gauge control consistent, every poisoned case answered with an optimal certificate, on at least 2 of 3 seeds; all three seeds reported.
- **Differentiation:** per-case exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05, pre-registered.
- **Ladder curve:** per-b₁ success for each arm, to locate where synthesized solvers start to fail (typically when they fall back to chord-only repair).
- **Economics:** cost per verified success per arm.

## 10. Interpretation

- **A passes and B fails:** the game adds capability for synthesizing a certified L1 repair solver at this budget.
- **A and B pass; A cheaper:** an efficiency advantage.
- **A ties C:** decomposition and verification do the work; the packet representation adds nothing.
- **A ties D:** sampling whole solvers explains the result.
- **All arms reach zero but fail optimality on poisoned cases:** the models learned exactness, not minimality; the dual certificate is the missing step.
- **E matches A:** useful automation; no incremental model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Kinetic proofreading** (catalog hook; `HopfieldNinioProofreader` in `symbol_game/domain/biochem/proofreading.py`): a candidate solver is admitted only after passing successive independent stages (public examples, the Python certificate verifier, the Rust verifier), each of which can discard it. The proofreading discard rate and the cost of each stage are logged. This is a verification pipeline modelled on proofreading, not a chemical claim.
- **Antimorphisms expected:** AM-4 stationary repeats during synthesis repair turns; AM-5 global sign inversion (negating every claim); chord-only repair reported as optimal; floats in output (the Q40 `int(...)` crash pattern, now a checker mutation).
- **Scratch space (U12, optional):** the per-cycle residual ledger from [C006](../a_mechanism/c006_host_scratch_space_vs_cot.md). **Layer 2:** grammar-constrained certificate JSON is allowed in every arm equally. **Layer 1:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each synthesis attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01) with every candidate solver, its public-example results and every checker verdict.

Expected DDC pattern: `C` (task and examples exposed), `Λ` (U13 lift into per-cycle subproblems), then `D` for candidates that pass more public examples and `M` for refused ones, `I` when per-cycle routines are integrated into one solver, `E` when the certificate checker accepts all public cases, `T` at freeze. Logged measures: public cases failed, Φ₁ residual on failed cases, duality gap on non-optimal answers.

Operands this challenge should yield:

```text
operand dual_before_minimal_claim.v1 | kind: guard | when: a repair reaches Phi1 = 0 on b1 >= 2 | do: construct a dual circulation before claiming minimality | check: sum w|r| equals sum c*y
operand shared_edge_first.v1 | kind: move | when: one edge lies on every open cycle and is cheapest per unit | do: move the common residual onto it first | check: weighted L1 strictly drops
operand slack_edges_fix_potential.v1 | kind: move | when: an optimal dual y is known | do: set r_e = 0 wherever |y_e| < w_e and solve for the potential on those edges | check: complementary slackness holds
```

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_solvers` (`exact_weighted_l1_lp.rs`, `phi1_l1_boundary_solver.rs`) and `engine/crates_rs/core_functional` (`phi1.rs`, `graph_phi1.rs`, `dual_witness.rs`).
- `engine/crates_rs/core_symbol_game` (`verify_l1_certificate`, `exact_solve_l1_primal_dual`).
- `engine/crates_rs/core_solvers/src/hodge_certificate_checker.rs` checks the unit-weight version of these conditions in `f64` with a tolerance; it is not used as a checker here.
- `research/mssn_sn_tower/demos/anti_morphism_observations.md` for the public boards.
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrade: [U13](../../upgrades/u13_cohomological_task_decomposition.md).

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose minimum-L1 repairs and dual certificates pass an exact checker on hidden graphs up to b₁ = 16, and whether the game arm did so more often or more cheaply than the ordinary arm.
- **Does not support:** any statement about degree-2 or higher obstructions; that the model understands cohomology; physical meaning of the cochains.
- **Narrowest defensible claim:** on these hidden cases, the frozen solver from arm A returned certified optimal repairs on the measured number of cases, at the measured cost.
- **Next test:** [C018](c018_signed_graph_frustration_index.md), the Z/2 analogue where optimality becomes NP-hard, and [C019](c019_h2_obstruction_extension.md) for degree 2.
