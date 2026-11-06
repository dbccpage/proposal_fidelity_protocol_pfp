# C016: Cohomology Rings: Telling Spaces Apart with Cup Products

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that decides whether cup products distinguish hidden pairs of complexes with
> equal Betti numbers, with explicit witness classes on both sides, for under $1.

## 2. Why This Task

Betti numbers cannot tell the torus T² from the wedge S¹ ∨ S¹ ∨ S²: both have (1, 2, 1). The cup product can. On T², for generators α, β of H¹, the product α ⌣ β generates H². On the wedge, every product H¹ × H¹ → H² is zero, because the degree-1 classes come from the circles and products of classes from different wedge summands vanish. The same holds one level up: CP² and S² ∨ S⁴ both have Betti numbers (1, 0, 1, 0, 1), but the square of the generator of H²(CP²) generates H⁴, while on S² ∨ S⁴ that square is zero (Hatcher 2002, §3.2).

Generation is hard: the solver must find cocycle representatives in degrees 1, 2 and 4, form Alexander–Whitney products on ordered simplices, and prove a class is nonzero or zero. Verification is cheap once witnesses are given: a nonzero product is certified by a cycle on which it evaluates to a nonzero number, and a zero product by a cochain whose coboundary it is. The challenge stresses the Symbol Game's exact host, OEWAS (Engine Workflows, Agents, Skills) synthesis, and no OEEIS (Engine Epistemic Immune System) mechanism beyond the refusal path. A pass shows the game can produce a certified cup-product discriminator. Equal cup-product data never proves two spaces are the same.

## 3. Formal Problem and Bounds

Input: two finite simplicial complexes X and Y, given by maximal simplices, dimension ≤ 4, with equal rational Betti numbers, and a degree pair (p, q) with p + q ≤ 4. Work over Q. Order vertices by label; for cochains a ∈ C^p and b ∈ C^q the Alexander–Whitney product is

[a ⌣ b](v₀, …, v_{p+q}) = a[v₀, …, v_p] · b[v_p, …, v_{p+q}].

It induces a well-defined bilinear map H^p × H^q → H^{p+q}. For each complex, report the rank of this map (the dimension of the span of all products of basis classes in H^{p+q}), with certificates. The pair is `DISTINGUISHED` if the ranks differ, and `NOT_DISTINGUISHED_BY_THIS_PRODUCT` otherwise.

Reference facts (Hatcher 2002, Chapter 3): rank of H¹ × H¹ → H² is 1 on T² and 0 on S¹ ∨ S¹ ∨ S²; rank of H² × H² → H⁴ is 1 on CP² and 0 on S² ∨ S⁴. CP² has a 9-vertex triangulation (Kühnel and Banchoff 1983); T² has a 7-vertex triangulation. Wedge triangulations are built and checked by the second checker at packet-build time.

The hidden set must contain the two named pairs under several triangulations each, pairs that are two triangulations of the same space (must not be distinguished), pairs where the answer depends on the product of two different classes rather than a square, and a pair where only a subdivision differs.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, run in the U09 sandbox:

```json
{"status": "SOLVED", "verdict": "DISTINGUISHED", "X": {"rank": "1", "basis_p": ["<cocycle>", "<cocycle>"], "basis_q": ["<cocycle>", "<cocycle>"], "nonzero": [{"i": "0", "j": "1", "cycle": "<chain>", "value": "1"}]}, "Y": {"rank": "0", "basis_p": ["<cocycle>", "<cocycle>"], "basis_q": ["<cocycle>", "<cocycle>"], "primitives": [{"i": "0", "j": "1", "gamma": "<cochain>"}]}}
{"status": "OUT_OF_SCOPE", "witness": {"reason": "BETTI_MISMATCH", "degree": "2"}}
{"status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"}
```

Cochains and chains are sparse maps from simplices (sorted vertex tuples) to canonical rationals. The certificate is complete when, on each side: the basis cocycles are cocycles and their classes are independent and span H^p and H^q (checked against the checker's own dimensions); for a claimed rank r, r products have independent classes, shown by cycles z_k with a nonsingular r × r matrix of values ⟨α_i ⌣ β_j, z_k⟩; and every product not in that span is shown zero or dependent, in the simplest case by a primitive γ with δγ = α_i ⌣ β_j. `OUT_OF_SCOPE` covers pairs whose Betti numbers differ (the witness names a degree).

## 5. Participant Packet

- `TASK.md` with the ordering convention, the product formula, the certificate rules and a worked T² example.
- `examples/`: 12 public cases with exact input and output JSON: T² against S¹ ∨ S¹ ∨ S² (one triangulation each), S² ∨ S⁴ against itself, two tori, and two `OUT_OF_SCOPE` pairs. CP² appears only in the hidden set.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 24 pairs.
- **Relabel controls:** 12. Vertex relabelling, which changes the Alexander–Whitney product at cochain level but not the rank; swapping X and Y.
- **Poisoned but schema-valid:** 8. Two triangulations of the same space of different sizes (a solver guessing from size fails); pairs where squares vanish but a mixed product does not; a T² triangulation whose natural cocycle representatives happen to have a zero product on one face but not in cohomology.
- **Exact checker:** new Rust code. `core_homology`'s `cohomology_report` covers only H^0 and H^1, and `cup_product.rs` and `cohomology_algebra.rs` are best-effort shells (`cup_product.rs` uses an `f64` shell field), so neither can check this challenge. The new checker computes H^n for n ≤ 4 over `BigRational`, verifies cocycle and coboundary conditions, forms exact Alexander–Whitney products and evaluates them on cycles.
- **Independent second checker:** a separately written Python `Fraction` implementation computing the rank of the product map from scratch, without using the submitted witnesses.
- **Checker mutation suite:** a "cocycle" with δα ≠ 0 on one simplex; a cycle z with ∂z ≠ 0; a product value off by a sign because the vertex order was ignored; a primitive γ with δγ ≠ α ⌣ β; a claimed rank above the true one.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis of the cohomology, product and witness search.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** The second checker's rank computation extended to emit witnesses. No such tool exists in the estate today; building it is part of packet construction, and it is expected to solve every case.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3-32B (route pinned in U06). $1.00 per arm through `BudgetController`; every call records provider, model ID, generation ID, tokens and billed cost. The sandbox provides the Python standard library only. U10 is recommended, as the [Q40 review](../00_q40_review.md) explains.

## 9. Pass Gates and Statistics

- **Capability gate:** 24/24 hidden pairs with complete certificates on both sides, all relabel controls consistent, all poisoned pairs correct, on at least 2 of 3 seeds.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05.
- **Degree split:** success on degree-(1, 1) pairs against degree-(2, 2) pairs, per arm.
- **Economics:** cost per verified success.

## 10. Interpretation

- **A passes, B fails:** the game adds capability for certified cup-product computations at this budget.
- **Arms pass T² and fail CP²:** degree-2 representatives on a 4-complex are the bottleneck.
- **Solvers distinguish same-space pairs:** they used a non-invariant (size, cochain-level zeros); the certificate rules should have caught it, so check the checker first.
- **E matches A:** useful automation, no incremental model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; the refusal path only.
- **Antimorphisms expected:** AM-2-style absolute claims ("the ring is determined by Betti numbers"); cochain-level zeros reported as cohomology zeros; sign errors from ignoring the vertex order; witness cycles that are not closed (AM-FSP-2).
- **Layer 2:** grammar-constrained JSON allowed equally. **Layer 1, scratch space:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, `Λ` (lift from cohomology classes to cocycle representatives), `I` (evaluate products on cycles), then `D`/`M` over candidate solvers, `E` when every public certificate replays, `T`. Logged measures: public pairs failed, rank errors, invalid witnesses by kind.

Operands this challenge should yield:

```text
operand evaluate_on_top_cycle.v1 | kind: move | when: testing whether a top-degree product is nonzero | do: evaluate it on a fundamental cycle | check: a nonzero value certifies a nonzero class
operand wedge_products_vanish.v1 | kind: move | when: classes come from different wedge summands | do: produce gamma with delta gamma = product | check: delta gamma equals the product exactly
operand rank_not_size.v1 | kind: guard | when: two complexes differ in size | do: compare only invariant ranks | check: same-space pairs are not distinguished
```

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_homology` (`cohomology.rs` for degrees 0 and 1, `cochain.rs`, `coboundary.rs`, `simplicial.rs`; `cup_product.rs` and `cohomology_algebra.rs` as shells to be replaced).
- `engine/crates_rs/core_linear_algebra` for exact ranks.
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: none in the catalog. Checker work: exact cohomology in degrees 2 to 4 and exact cup products in `core_homology`; this is the largest prerequisite and blocks `packet_built`.

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose cup-product ranks and witness classes replay exactly on hidden pairs, distinguishing T² from S¹ ∨ S¹ ∨ S² and CP² from S² ∨ S⁴.
- **Does not support:** that complexes with equal cup-product data are homotopy equivalent; any statement about full ring isomorphism; any physical reading of the spaces.
- **Narrowest defensible claim:** the frozen solver returned replayable cup-product certificates and correct verdicts on the measured number of hidden pairs.
- **Next test:** cup products over F₂ and Steenrod squares, and the spectral-sequence machinery of [C020](c020_spectral_sequence_double_complex.md).
