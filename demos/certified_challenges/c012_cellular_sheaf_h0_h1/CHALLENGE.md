# C012: Cellular Sheaf Cohomology H^0 and H^1

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that returns H^0 and H^1 of hidden cellular sheaves on graphs over Q, with
> explicit bases and, for each target cochain, a gluing or an obstruction witness, for under $0.50.

## 2. Why This Task

A cellular sheaf on a graph attaches a vector space to each vertex and edge and a linear restriction map to each incidence. Global sections (H^0) are the consistent assignments; H^1 measures which edge data cannot come from vertex data. It generalizes the scalar coboundary problem of [C011](c011_cycle_rank_ladder_coboundary_repair.md): with one-dimensional stalks and identity restrictions it is exactly that problem, and with nontrivial restrictions it models consensus under local change of coordinates (Hansen and Ghrist 2019). Generation is hard because the solver must assemble a block coboundary matrix with correct signs and orientations and handle rank drops; verification is cheap because membership, independence and rank are exact linear algebra over Q.

The challenge stresses the Symbol Game's exact host, OEWAS (Engine Workflows, Agents, Skills) decomposition by components and cycles (U13), and the OEEIS (Engine Epistemic Immune System) only through the host's refusal path. A pass shows the game can produce a certified sheaf-cohomology solver on graphs. It does not cover sheaves on higher-dimensional complexes.

## 3. Formal Problem and Bounds

Input: a directed graph G = (V, E); for each vertex v a stalk dimension d_v ≥ 0 and for each edge e a dimension d_e ≥ 0; for each edge e = (u, v) two restriction matrices F_{u⊴e} ∈ Q^{d_e × d_u} and F_{v⊴e} ∈ Q^{d_e × d_v}. Cochains: C^0 = ⊕_v Q^{d_v}, C^1 = ⊕_e Q^{d_e}. The coboundary is

(δx)_e = F_{v⊴e} x_v − F_{u⊴e} x_u, for e = (u, v).

Then H^0 = ker δ and H^1 = C^1 / im δ, with dim H^1 = dim C^1 − rank δ. By rank–nullity, dim H^0 − dim H^1 = dim C^0 − dim C^1.

Reference values the hidden set uses, each of which the checker recomputes:

- **Constant sheaf Q^d** (all restrictions the identity): dim H^0 = d · (number of components) and dim H^1 = d · b₁, the ordinary graph cohomology with coefficients Q^d.
- **Line sheaf on an n-cycle** with nonzero scalar restrictions: let h be the product around the cycle of the ratios F_{head⊴e} / F_{tail⊴e}, with each ratio inverted when the edge is traversed against its orientation. Then dim H^0 = dim H^1 = 1 if h = 1, and 0 otherwise.

For each case the solver also receives up to three target cochains b ∈ C^1 and must return, for each, either x with δx = b (the data glue) or η ∈ C^1 with δᵀη = 0 and ⟨η, b⟩ ≠ 0 (an obstruction witness; η annihilates im δ, so b ∉ im δ).

Bounds: |V| ≤ 30, |E| ≤ 60, stalk dimensions ≤ 4, dim C^0 and dim C^1 ≤ 240, matrix entries rationals with numerator and denominator at most 99 in absolute value. The hidden set must contain zero-dimensional stalks, non-injective restrictions, disconnected graphs, cycles with h = 1 reached by non-identity maps, parallel edges, and targets that are exact only after a change of representative.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, synthesized by the arm and run in the U09 sandbox:

```json
{"status": "SOLVED", "h0_dim": "2", "h0_basis": [["1", "0", "1", "0"], ["0", "1", "0", "1"]], "h1_dim": "1", "h1_complement": [["0", "0", "1"]], "targets": [{"glues": true, "x": ["1", "0", "2", "0"]}, {"glues": false, "eta": ["1", "-1", "1"]}]}
{"status": "OUT_OF_SCOPE", "witness": {"edge": "e3", "reason": "RESTRICTION_SHAPE_MISMATCH"}}
{"status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"}
```

Vectors use the case's declared ordering of stalk coordinates. The certificate is complete when: each H^0 basis vector satisfies δx = 0 and the vectors are independent; `h0_dim` equals the number of vectors; the `h1_complement` vectors together with the columns of δ span C^1 and have exactly dim C^1 vectors in total (so their classes form a basis of H^1); each `glues` answer satisfies δx = b exactly; each obstruction satisfies δᵀη = 0 and ⟨η, b⟩ ≠ 0. The checker recomputes rank δ independently, so a basis that is valid but short is caught.

## 5. Participant Packet

- `TASK.md` with the definition, ordering conventions and certificate rules.
- `examples/`: 20 public cases with exact input and output JSON: constant sheaves on a tree and on K4, line sheaves on cycles with h = 1 and h = −1, a sheaf with a zero stalk, a non-injective restriction, one gluing and one obstructed target, and two `OUT_OF_SCOPE` inputs.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 40.
- **Relabel and gauge controls:** 16. Vertex renaming; reversing an edge together with swapping its two restriction maps and negating the edge's target coordinates; a change of basis on one vertex stalk (x_v ↦ g x_v, restrictions F ↦ F g⁻¹), which preserves dimensions and transforms the certificate.
- **Poisoned but schema-valid:** 12. Cycles where h = 1 only after cancellation of large factors; restriction maps that are rank-deficient in a way that looks invertible at a glance; targets whose obstruction witness must be nonzero on an edge the target does not touch.
- **Exact checker:** `core_homology::cohomology::cohomology_report` on the complex C^0 → C^1 → 0 over `BigRational` (it covers exactly H^0 and H^1, which is all this challenge needs), plus membership and independence checks with `core_linear_algebra`.
- **Independent second checker:** a separately written Python `Fraction` Gaussian elimination. `core_solvers::solver_resolution_free_sheaf_cohomology` uses `f64` with a tolerance and is not a checker; it may appear only as labelled secondary evidence.
- **Checker mutation suite:** an H^0 vector with one coordinate off; a dependent basis; an H^1 complement that fails to span; an η with δᵀη ≠ 0 in one coordinate; an η orthogonal to b; `"2/4"`.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis with U13 decomposition (components, then cycles).
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** The exact checker's own rank computation wrapped as `solve` (dimensions and bases by exact elimination). Expected to solve every case.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, Qwen3-32B, DeepSeek-R1-Distill-Qwen-32B (exact IDs and routes pinned in U06). $0.50 per arm, enforced before each call by `BudgetController`; provider, model ID, generation ID, tokens and billed cost recorded for every call. The sandbox provides the Python standard library only. U10 is recommended for the same reason as in [C011](c011_cycle_rank_ladder_coboundary_repair.md) and [the Q40 review](../00_q40_review.md).

## 9. Pass Gates and Statistics

- **Capability gate:** 40/40 hidden base cases with complete certificates, all controls consistent, all poisoned cases correct, on at least 2 of 3 seeds; all seeds reported.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05.
- **Error taxonomy:** per arm, counts of sign-convention errors, wrong dimensions and invalid witnesses.
- **Economics:** cost per verified success.

## 10. Interpretation

- **A passes, B fails:** the game adds capability for certified sheaf cohomology at this budget.
- **All arms pass constant sheaves and fail twisted cycles:** the models learned graph cohomology, not restriction maps.
- **A ties C or D:** decomposition or sampling explains the result.
- **E matches A:** useful automation, no incremental model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook. The host's refusal path (reject any certificate the checker cannot replay) is the only immune analogue exercised.
- **Antimorphisms expected:** AM-5-style sign inversion of the coboundary (δ with tail and head swapped, which preserves dimensions but breaks witnesses); invalid witnesses (AM-FSP-2) claiming η ⊥ im δ; confusing dim C^1 − rank δ with dim ker δᵀ on the wrong side.
- **Scratch space (U12, optional):** a host ledger of per-component ranks. **Layer 2:** grammar-constrained JSON allowed in every arm equally. **Layer 1:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, `Λ` (split into components and cycle subproblems), `D`/`M` over candidate solvers, `I` (assemble component results by direct sum), `E`, `T`. Logged measures: public cases failed, rank discrepancies against the checker, invalid witnesses.

Operands this challenge should yield:

```text
operand line_sheaf_holonomy.v1 | kind: move | when: rank-1 stalks on a cycle | do: multiply restriction ratios around the cycle; H0 = H1 = 1 iff the product is 1 | check: rank(delta) recomputed exactly
operand fredholm_witness.v1 | kind: move | when: a target b is not in im(delta) | do: return eta in ker(delta^T) with <eta, b> != 0 | check: delta^T eta = 0 exactly
operand component_direct_sum.v1 | kind: decomposition | when: the graph is disconnected | do: solve each component and concatenate | check: dimensions add
```

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_homology` (`cohomology.rs`, `cochain_complex.rs`, exact over `BigRational`) and `engine/crates_rs/core_linear_algebra` (`image_kernel.rs`).
- `engine/crates_rs/core_solvers` (`solver_resolution_free_sheaf_cohomology.rs`, `f64`, secondary only).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrade: [U13](../../upgrades/u13_cohomological_task_decomposition.md).

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose H^0 and H^1 bases and gluing or obstruction witnesses pass an exact checker on hidden sheaves on graphs.
- **Does not support:** sheaf cohomology on higher-dimensional complexes; cohomology over Z or finite fields; any claim about consensus systems beyond the formal model.
- **Narrowest defensible claim:** the frozen solver returned exact, replayable certificates on the measured number of hidden sheaves at the measured cost.
- **Next test:** sheaves on 2-complexes (H^2), which need checker work beyond `cohomology_report`, and the ledger reconciliation form in [C077](../h_economics/c077_ledger_reconciliation_h1.md).
