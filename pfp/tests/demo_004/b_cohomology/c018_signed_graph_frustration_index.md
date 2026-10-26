# C018: Frustration Index of Signed Graphs

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that returns, for hidden signed graphs, a switching and deleted-edge set with a
> matching lower-bound certificate, or an honest UNKNOWN with bounds, for under $1.

## 2. Why This Task

A signed graph is balanced when every cycle has an even number of negative edges; equivalently, when some switching (flipping the signs of all edges at a set of vertices) makes every edge positive (Harary 1953). The frustration index l(Σ) is the minimum number of edges whose deletion leaves a balanced graph, which equals the minimum number of negative edges over all switchings. It is the Z/2 analogue of [C011](c011_cycle_rank_ladder_coboundary_repair.md): the signs form a 1-cochain σ over Z/2, switchings are coboundaries δs, and l(Σ) is the minimum Hamming weight of σ + δs over s, the lightest representative of the class of σ in H¹(G; Z/2).

Unlike C011, optimality is NP-hard: an all-negative signed graph has l = |E| − maxcut(G), so computing l decides maximum cut (Karp 1972). An upper bound is easy to certify (show the switching). A matching lower bound is not, and a solver that cannot certify one must say `UNKNOWN`. That is the point of the challenge: it rewards honest refusals as much as solutions. It stresses the Symbol Game's exact host and refusal path, OEWAS (Omega Engine Workflows, Agents, Skills) decomposition by blocks (U13), and the OEEIS (Omega Engine Epistemic Immune System) discipline that an uncertified optimum is not reported as one. A pass shows certified optima where certifiable and honest bounds elsewhere. It does not show a polynomial algorithm.

## 3. Formal Problem and Bounds

Input: a simple graph G = (V, E) with a sign σ_e ∈ {+1, −1} on each edge. For a switching s: V → {+1, −1}, the switched sign of e = uv is s_u σ_e s_v. Then l(Σ) = min over s of the number of edges with s_u σ_e s_v = −1.

Lower-bound certificates accepted:

1. **Negative-cycle packing:** k edge-disjoint cycles, each with an odd number of negative edges. Each needs at least one deletion, so l ≥ k.
2. **Exhaustive switching** for |V| ≤ 20: the checker replays all 2^{|V|−1} switchings (s and −s give the same count).
3. **UNSAT proof:** a CNF encoding (declared in the packet) of "some switching has at most l − 1 negative edges", with a DRAT or LRAT proof of unsatisfiability checked by an external proof checker at packet-build time and at scoring.
4. **Block additivity:** l(Σ) is the sum of l over the 2-connected blocks, since every cycle lies in one block; a certificate may be given per block.

`SOLVED` requires the upper bound (switching) and a lower-bound certificate with the same value. Otherwise the answer is `UNKNOWN` with refusal `OPTIMALITY_UNCERTIFIED` and the certified bounds.

Known small value (checked for this spec): the all-negative K4 has l = 6 − maxcut(K4) = 6 − 4 = 2. Any two of its triangles share an edge, so the packing bound gives only 1; the lower bound needs exhaustive switching or an UNSAT proof.

Bounds: |V| ≤ 200, |E| ≤ 1,000. The hidden set must contain balanced graphs (l = 0; the certificate is a switching making all edges positive), trees, all-negative complete graphs, graphs with many bridges and small blocks, and some instances whose optimum the operator could not certify at packet-build time (the correct answer there is `UNKNOWN` with bounds no looser than the operator's).

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, run in the U09 sandbox:

```json
{"status": "SOLVED", "l": "2", "switching": {"a": "+1", "b": "-1"}, "deleted": [["a", "c"], ["b", "d"]], "lower_bound": {"kind": "exhaustive"}}
{"status": "SOLVED", "l": "3", "switching": {"a": "+1"}, "deleted": [["a", "b"]], "lower_bound": {"kind": "packing", "cycles": [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i", "j", "k"]]}}
{"status": "UNKNOWN", "refusal": "OPTIMALITY_UNCERTIFIED", "upper": "41", "lower": "37", "switching": {"a": "-1"}}
{"status": "OUT_OF_SCOPE", "witness": {"edge": ["c", "c"], "reason": "SELF_LOOP"}}
```

Omitted switching entries are +1. The examples are abbreviated. A `SOLVED` certificate is complete when the deleted set is exactly the negative edges after switching, its size is l, and the lower bound replays to l. An `UNKNOWN` answer is scored correct when both bounds replay and the gap is no wider than the operator's certified gap for that case; claiming `SOLVED` on such a case without a valid lower bound is scored wrong.

## 5. Participant Packet

- `TASK.md` with the definitions, the four lower-bound kinds, the CNF encoding and the scoring rule for `UNKNOWN`.
- `examples/`: 20 public cases with exact input and output JSON: balanced graphs, the all-negative K4, cases solved by packing, by exhaustive switching, by block additivity, and two `UNKNOWN` cases with bounds.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 40, including 8 whose optimum is uncertified.
- **Relabel and gauge controls:** 16. Vertex renaming and random switchings of the input (l is invariant; the certificate's switching changes).
- **Poisoned but schema-valid:** 12. Graphs where greedy local switching stalls above the optimum; graphs where the packing bound is not tight; instances with a plausible but wrong "optimal" value in their comment field.
- **Exact checker:** new Rust code: switched-sign counts, cycle validity and edge-disjointness, exhaustive replay for small graphs, and block decomposition, reusing `omega_solvers` for SAT. Whether `solver_cadical_unsat_core.rs` can emit DRAT or LRAT proofs is checked at packet-build time; if not, proofs are produced and checked with an external solver and proof checker (for example drat-trim) run by the operator.
- **Independent second checker:** a separately written Python checker, plus an integer-programming solve at packet-build time to set each case's certified bounds.
- **Checker mutation suite:** a deleted set that differs from the switched negatives by one edge; a packing with two cycles sharing an edge; a "negative" cycle with an even number of negative edges; `SOLVED` with a lower bound one below l; an `UNKNOWN` with a lower bound above the true value.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis with U13 decomposition into blocks.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** Block decomposition, local switching search and a SAT-based lower bound with proofs, wrapped as `solve`. It is not expected to certify every case; E's certified count is the reference.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3-32B (route pinned in U06). $1.00 per arm through `BudgetController`; every call records provider, model ID, generation ID, tokens and billed cost. The sandbox provides the Python standard library and, if the pre-registration allows it, a pinned SAT solver binary; the same binary is then available to every arm. U10 is recommended, as the [Q40 review](../00_q40_review.md) explains.

## 9. Pass Gates and Statistics

- **Capability gate:** 40/40 hidden base cases scored correct (certified optima, or `UNKNOWN` with bounds at least as tight as the operator's), all controls consistent, all poisoned cases correct, on at least 2 of 3 seeds.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05.
- **Honesty metric:** the count of uncertified `SOLVED` claims per arm, reported separately. Any nonzero count is a failure of that seed regardless of other results.
- **Economics:** cost per verified success, and the mean certified gap on uncertified cases.

## 10. Interpretation

- **A passes, B fails:** the game adds capability for certified frustration indices at this budget.
- **An arm matches E's certified count but claims optima it cannot certify:** the honesty gate fails it; the arm guessed.
- **A beats E on certified cases:** the models found lower-bound certificates the deterministic baseline missed, a real incremental advantage.
- **A ties D:** sampling explains the result.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook. The honesty metric is the refusal discipline the immune system exists to enforce: an uncertified optimum is an antigen, and the host rejects it.
- **Antimorphisms expected:** AM-2 absolute claims ("this is optimal") without a certificate; AM-5 global sign inversion (switching every vertex, which changes nothing); packings with shared edges presented as disjoint (AM-FSP-2).
- **Scratch space (U12, optional):** a per-block ledger of bounds. **Layer 2:** grammar-constrained JSON allowed equally. **Layer 1:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, `Λ` (split into blocks), per block `D` steps (local switchings that lower the negative count) and `M` for rejected bounds, `I` (sum block results), then `E T` when bounds meet, or `T` with `UNKNOWN` when they do not. A `T` with `UNKNOWN` is a correct terminal here. Logged measures: current upper bound, best certified lower bound, gap, blocks open.

Operands this challenge should yield:

```text
operand block_additivity.v1 | kind: decomposition | when: the graph has cut vertices | do: solve each 2-connected block and sum | check: total equals the sum of block certificates
operand local_switch_descent.v1 | kind: move | when: a vertex has more negative than positive incident edges after switching | do: switch it | check: negative count strictly drops
operand unknown_with_bounds.v1 | kind: guard | when: upper and lower bounds differ | do: return UNKNOWN with both certificates, never SOLVED | check: honesty count stays 0
```

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_solvers` (`solver_cadical_unsat_core.rs`, SAT via CaDiCaL) and `omega_engine/crates_rs/omega_homology` (`finite_directed_graph.rs`).
- `omega_engine/crates_rs/omega_symbol_game` (`classify_gauge_board`, which classifies an F₂ cochain against given F₂ matrices d0 and d1; the balance test is whether σ, written additively, lies in the image of d0).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrade: [U13](../../upgrades/u13_cohomological_task_decomposition.md). Checker work: the Rust checker in §6 and a proof-checking path for UNSAT certificates.

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver that certifies frustration indices where it can and refuses honestly where it cannot, on hidden signed graphs up to 200 vertices.
- **Does not support:** any polynomial-time claim; optimality of `UNKNOWN` cases; any social or physical interpretation of balance.
- **Narrowest defensible claim:** the frozen solver certified the measured number of optima and returned valid bounds on the rest, with zero uncertified optimality claims.
- **Next test:** weighted signed graphs, and the Z/2 gauge-theory setting of [C039](../d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law.md).
