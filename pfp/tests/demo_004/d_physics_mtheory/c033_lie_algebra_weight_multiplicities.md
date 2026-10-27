# C033: Weight Multiplicities of Simple Lie Algebras

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that returns exact weight multiplicities and tensor-product decompositions for
> irreducible representations of simple Lie algebras of rank at most 4, for under $0.50.

## 2. Why This Task

Freudenthal's recursion gives the multiplicity of every weight in an irreducible representation from its highest weight. The Weyl dimension formula gives the total dimension as an exact rational product. Their agreement, Σ over dominant weights of multiplicity × Weyl-orbit size = dimension, is a cheap global check. A tensor-product decomposition is checked by multiplying characters exactly. Producing the numbers is error-prone: inner products need the right symmetric form, orbit sizes need the right stabilizers, and B-type and C-type label conventions are easy to swap.

This is the group-theory layer beneath C032 and C040. It stresses OEWAS (Engine Workflows, Agents, Skills) recursion with host arithmetic, and OEEIS (Engine Epistemic Immune System) screening of multiplicity tables that are dimensionally consistent but wrong weight by weight.

## 3. Formal Problem and Bounds

Algebras: A₁–A₄, B₂–B₄, C₃–C₄, D₄, G₂, F₄. Weights are given by Dynkin labels in the Bourbaki node order, which `TASK.md` fixes with a diagram for each type.

Query types:

1. **Character:** given an integral weight λ, return the irreducible representation whose extremal weights include λ: its dominant highest weight, its dimension, and every dominant weight μ with its multiplicity m_λ(μ). Dimension at most 10⁶.
2. **Tensor product:** given λ and μ, return every ν with multiplicity N^ν_{λμ} > 0, where dim λ · dim μ ≤ 10⁶.

All arithmetic is exact over Q. Weyl group orders for the orbit-size check: |W(A₄)| = 120, |W(B₄)| = |W(C₄)| = 384, |W(D₄)| = 192, |W(G₂)| = 12, |W(F₄)| = 1152.

Reference values (standard):

- A₂: 3 ⊗ 3̄ = 8 ⊕ 1 and 3 ⊗ 3 = 6 ⊕ 3̄; the zero weight of the adjoint 8 has multiplicity 2.
- A₁: spin j ⊗ spin j′ = ⊕ spin k, for k from |j − j′| to j + j′ in integer steps.
- G₂: the smallest nontrivial representation has dimension 7 and the adjoint 14; 7 ⊗ 7 = 1 ⊕ 7 ⊕ 14 ⊕ 27.
- Every other hidden value is computed by the judge's two checkers at packet-build time.

Edge cases: the trivial representation; the adjoint (multiplicity of the zero weight equals the rank); B₂ against C₂ label order; D₄ triality; a non-dominant input weight (the solver must move it to the dominant chamber); a fractional label (malformed).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Inputs and outputs:

```json
{"case_id": "la_04", "algebra": "A2", "query": "character", "weight": [1, 1]}
{"id": "la_04", "status": "SOLVED", "highest_weight": [1, 1], "dimension": 8,
 "dominant_multiplicities": [[[1, 1], 1], [[0, 0], 2]]}
{"case_id": "la_05", "algebra": "G2", "query": "tensor", "left": [1, 0], "right": [1, 0]}
{"id": "la_05", "status": "SOLVED", "decomposition": [[[0, 0], 1], [[1, 0], 1], [[0, 1], 1], [[2, 0], 1]]}
{"id": "la_06", "status": "OUT_OF_SCOPE", "witness": {"kind": "non_integral_label", "index": 1}}
{"id": "la_07", "status": "UNKNOWN", "refusal_code": "DIMENSION_OUT_OF_BOUNDS"}
```

In the G₂ example, [1, 0] denotes the 7 and [0, 1] the 14 under the Bourbaki order pinned in `TASK.md`. A character answer is complete when every dominant weight of the representation appears exactly once with its exact multiplicity and the dimension is correct. A tensor answer is complete when the multiset of ν with multiplicities equals the true decomposition. `OUT_OF_SCOPE` covers non-integral labels and unsupported algebras with an explicit type; `UNKNOWN` covers out-of-bound dimensions.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the Cartan matrix and symmetrizing form for every type, the Bourbaki order, and statements of the Freudenthal and Weyl dimension formulas.
- `examples/`: 12 cases with exact outputs: the A₁ and A₂ reference values, the G₂ values, a B₂ and a C₂ case showing the label swap, the D₄ vector and its two spinor triality images, a non-dominant input, a fractional label and an oversized request.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 30 queries: 18 characters (at least 2 per algebra type) and 12 tensor products, weighted toward representations with multiplicities above 1.
- **Relabel and gauge controls:** 10 controls: the input weight replaced by another weight in its Weyl orbit (for example the lowest weight); Dynkin diagram automorphisms (the A_n flip, which is conjugation, and D₄ triality), with outputs permuted accordingly; the tensor factors swapped.
- **Poisoned-but-schema-valid cases:** 6 cases: B₃ and C₃ with identical label vectors (different algebras, different answers); a weight with a large label where multiplicities grow quickly; an F₄ request whose answer hinges on short against long root lengths.
- **Exact checker (Rust):** Freudenthal's recursion over Q, the Weyl dimension formula, orbit sizes by stabilizer subgroups, and exact character multiplication for tensor products.
- **Independent second checker:** Kostant's multiplicity formula (alternating sum over W with the partition function) for characters, and the Brauer–Klimyk rule for tensor products. It shares no code with the Freudenthal path.
- **Mutation suite:** a multiplicity off by one, a missing dominant weight, a dimension that matches while two multiplicities are swapped, B and C labels exchanged, a tensor decomposition with the right total dimension and a wrong component.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the checker's Freudenthal implementation packaged as a solver. E passes by construction; the challenge measures synthesis of correct group theory. Arm F does not apply.

## 8. Budget, Models and Provenance

$0.50 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, Qwen3 14B, Gemma 3 27B. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 30/30 base and 10/10 controls, both checkers agreeing.
- **Primary metric (pre-registered):** per-case exact-match rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** error rate on non-simply-laced algebras (B, C, G₂, F₄) against simply-laced ones (A, D).

## 10. Interpretation

- Passing A and D but failing B, C, G₂ and F₄ means the symmetrizing form, not the recursion, is wrong.
- Dimensions right with multiplicities wrong means the solver fitted the global check and not the recursion; this is why weight-by-weight comparison is required.
- A pass shows correct computation of classical representation theory, which is textbook material.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a character whose dimension matches the Weyl formula; signal 2 is a weight-level mismatch with the second checker. Together they flag compensating errors.
- **Kinetic proofreading:** dominance, then Weyl dimension, then per-weight multiplicities, then orbit-sum agreement.
- **Thymus:** reject operands that treat B_n and C_n label vectors as interchangeable.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the Cartan matrix, the symmetrized form and the multiplicity table as the recursion descends from the highest weight.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose algebra and weight), `D` (reflect the input weight into the dominant chamber), `I` (integrate the Freudenthal table level by level), `R` (residual: dimension from the table minus the Weyl dimension), `E` when it vanishes and every level is filled, `T`. For tensor products, a second `I R E` cycle over character multiplication. Logged measures: the dimension residual and the number of weight levels completed.

Operands expected: (1) orbit size |W| / |W_μ| with the stabilizer read from zero labels; (2) the symmetrized inner product from the Cartan matrix and root lengths; (3) the B/C label warning; (4) tensor products by Brauer–Klimyk, with reflection back to the dominant chamber and signs.

## 13. Estate Reuse and Prerequisites

- No Lie-algebra module exists in the estate. The Cartan data, Freudenthal, Kostant and Brauer–Klimyk implementations are new Rust work and will be shared with C032 and C040.
- `engine/crates_rs/core_kernel` for exact rationals and `engine/crates_rs/core_linear_algebra` for the inverse Cartan matrix.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize exact weight-multiplicity and tensor-product code for simple Lie algebras of rank at most 4.
- **Does not support:** any physical claim about particle spectra or unification; any claim beyond the listed algebras and bounds.
- **Narrowest defensible claim:** "Arm X matched both independent checkers on k of 30 hidden representation-theory queries."
- **Next test:** C040, which needs the E₇ and E₈ dimensions and the branching to their maximal compact subgroups.
