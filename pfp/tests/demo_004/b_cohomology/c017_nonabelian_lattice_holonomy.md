# C017: Nonabelian Lattice Holonomy and Flatness

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that, for hidden S₃, Q₈ and SL(2, F₃) connections on lattices, returns a
> flattening gauge or a plaquette with nontrivial holonomy, for under $0.50.

## 2. Why This Task

For abelian groups, flatness and gauge-triviality reduce to the coboundary questions of [C011](c011_cycle_rank_ladder_coboundary_repair.md). For nonabelian groups the order of multiplication matters: the holonomy around a plaquette is an ordered product, it changes by conjugation under a change of base point or gauge, and a solver that multiplies in the wrong order or tests only an abelian invariant (sign, determinant) gives confident wrong answers. S₃ (order 6), the quaternion group Q₈ (order 8) and SL(2, F₃) (order 24) are the smallest useful test groups; Q₈ is a subgroup of SL(2, F₃), and SL(2, F₃) is isomorphic to the binary tetrahedral group.

Generation is hard: the solver must choose a spanning tree, gauge-fix along it, multiply loops in the right order and separate "not flat" from "flat but not trivial" on a torus. Verification is cheap: the checker multiplies each plaquette once and applies a gauge. The challenge stresses the Symbol Game's exact host, OEWAS (Omega Engine Workflows, Agents, Skills) synthesis, and no OEEIS (Omega Engine Epistemic Immune System) mechanism beyond the refusal path. A pass shows the game can produce a certified nonabelian flatness solver. It is not a lattice gauge theory result.

## 3. Formal Problem and Bounds

Input: an L × M square lattice (2 ≤ L, M ≤ 12) with open or periodic boundaries; a finite group G ∈ {S₃, Q₈, SL(2, F₃)} given by named elements and a full multiplication table; and a group element U_{uv} on each oriented edge, with U_{vu} = U_{uv}⁻¹. The holonomy of a closed path v₀ → v₁ → … → v_k = v₀ is U_{v₀v₁} U_{v₁v₂} ⋯ U_{v_{k−1}v₀}. A gauge g: V → G acts by U'_{uv} = g_u U_{uv} g_v⁻¹, conjugating holonomies at the base point.

Outputs:

1. `NOT_FLAT` with a plaquette (four vertices in order) whose holonomy is not the identity.
2. `PURE_GAUGE` with a gauge g such that every g_u U_{uv} g_v⁻¹ is the identity. For open boundaries, every flat connection is pure gauge, since the lattice is simply connected.
3. `FLAT_NONTRIVIAL` (periodic boundaries only): all plaquettes are trivial, but the holonomies A and B around the two noncontractible cycles from a declared base point are not both the identity. The certificate is the two loops and their holonomies. For a flat connection on the torus, A and B commute, because the fundamental group of the torus is abelian.

Representations the checker uses: S₃ as 3 × 3 permutation matrices over Q; Q₈ as 2 × 2 matrices over the Gaussian rationals; SL(2, F₃) either through a new GF(3) scalar type or through its binary tetrahedral form as 2 × 2 matrices over the Gaussian rationals (unit quaternions with half-integer coordinates). The second checker verifies the chosen representation's multiplication table against the case's table at packet-build time.

The hidden set must contain connections whose plaquette holonomies all lie in the commutator subgroup (the 3-cycles in S₃, which have sign +1), plaquettes whose holonomy is the central element −1 of Q₈ or SL(2, F₃), cases where reversing the multiplication order changes the flatness verdict, flat periodic connections with nontrivial commuting A and B, and pure-gauge connections disguised by a random gauge.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, run in the U09 sandbox:

```json
{"status": "SOLVED", "verdict": "NOT_FLAT", "plaquette": ["3,4", "4,4", "4,5", "3,5"], "holonomy": "-1"}
{"status": "SOLVED", "verdict": "PURE_GAUGE", "gauge": {"0,0": "e", "0,1": "i"}}
{"status": "SOLVED", "verdict": "FLAT_NONTRIVIAL", "base": "0,0", "loop_a": ["0,0", "1,0"], "hol_a": "j", "loop_b": ["0,0", "0,1"], "hol_b": "-1"}
{"status": "OUT_OF_SCOPE", "witness": {"edge": "2,3->2,4", "reason": "INVERSE_MISMATCH"}}
```

Element names follow the case's table. The example lists are abbreviated. A certificate is complete when the checker's ordered product over the named plaquette is not the identity (`NOT_FLAT`), the gauged connection is the identity on every edge (`PURE_GAUGE`), or every plaquette is trivial and the named loops are noncontractible with the stated holonomies, not both the identity (`FLAT_NONTRIVIAL`). `OUT_OF_SCOPE` covers inputs where U_{vu} is not the inverse of U_{uv}, or the table is not a group.

## 5. Participant Packet

- `TASK.md` with the orientation, product-order and gauge conventions and the three verdicts.
- `examples/`: 18 public cases with exact input and output JSON, six per group, covering all three verdicts, a commutator-subgroup trap and a central-element plaquette.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 36 (12 per group).
- **Relabel and gauge controls:** 18. Random gauge transformations (verdict unchanged; certificates transform), relabelled group elements through an automorphism of the group, and lattice reflections.
- **Poisoned but schema-valid:** 12. Commutator-subgroup plaquettes (sign or determinant tests say flat); order-reversal traps; flat periodic connections whose A and B are conjugate but not equal.
- **Exact checker:** `omega_holonomy` (`compute_loop_holonomy`, `is_flat`, `plaquette_curvature`, `apply_gauge_transformation`) over `BigRational` and `GaussianRational`, plus a GF(3) scalar if that route is chosen for SL(2, F₃).
- **Independent second checker:** a separately written Python checker that uses only the case's multiplication table, never matrices.
- **Checker mutation suite:** a plaquette listed in the reverse order with a holonomy computed in the forward order; a gauge that trivializes all but one edge; a `FLAT_NONTRIVIAL` claim on an open lattice; a loop that is contractible; an element name not in the table.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis of the solver.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** Tree gauge-fixing plus plaquette products, wrapped as `solve` from the second checker. Expected to solve every case.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, Qwen3-32B, Gemma 3 27B (route pinned in U06). $0.50 per arm through `BudgetController`; every call records provider, model ID, generation ID, tokens and billed cost. The sandbox provides the Python standard library only. U10 is recommended, as the [Q40 review](../00_q40_review.md) explains.

## 9. Pass Gates and Statistics

- **Capability gate:** 36/36 hidden base cases with complete certificates, all controls consistent, all poisoned cases correct, on at least 2 of 3 seeds.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05.
- **Group split:** success per group, per arm; SL(2, F₃) is expected to be hardest.
- **Economics:** cost per verified success.

## 10. Interpretation

- **A passes, B fails:** the game adds capability for certified nonabelian flatness at this budget.
- **Arms pass S₃ and fail Q₈ or SL(2, F₃):** order errors surface only when more elements fail to commute or when the center is nontrivial.
- **Arms miss `FLAT_NONTRIVIAL`:** they conflated flatness with triviality; global holonomy is the missing concept.
- **E matches A:** useful automation, no incremental model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; the refusal path only.
- **Antimorphisms expected:** order reversal (products multiplied right to left); abelianization (testing sign or determinant only); AM-2-style claims that "flat means pure gauge" on the torus; base-point confusion.
- **Layer 2:** grammar-constrained JSON with element names from the table, allowed equally. **Layer 1, scratch space:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, then `R` (gauge-fix along a spanning tree, projecting the connection onto its loop data), `D`/`M` over candidate solvers, `E` when every public certificate replays, `T`. Logged measures: public cases failed, plaquettes misjudged, order-reversal errors.

Operands this challenge should yield:

```text
operand tree_gauge_fix.v1 | kind: move | when: testing a lattice connection for pure gauge | do: set g along a spanning tree so tree edges become identity; the rest are loop holonomies | check: gauged tree edges equal e
operand multiply_every_plaquette.v1 | kind: guard | when: sign or determinant says flat | do: multiply the plaquette in order anyway | check: product equals e
operand torus_global_holonomy.v1 | kind: move | when: periodic boundary and all plaquettes trivial | do: compute holonomy around both cycles from one base point | check: A and B commute
```

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_holonomy` (`holonomy.rs`, `curvature.rs`, `connection.rs`, `matrix.rs` with `GaussianRational`, `graph.rs`).
- `omega_engine/crates_rs/omega_symbol_game` (ordered loop product host action).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: none in the catalog. Checker work: a GF(3) scalar type or the binary tetrahedral representation for SL(2, F₃).

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose flatness verdicts and gauge or holonomy witnesses replay on hidden S₃, Q₈ and SL(2, F₃) lattice connections.
- **Does not support:** any statement about continuum gauge theory, confinement or physical fields; groups beyond the three tested.
- **Narrowest defensible claim:** the frozen solver returned replayable holonomy and gauge certificates on the measured number of hidden lattices.
- **Next test:** the Z₂ gauge theory and Gauss law of [C039](../d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law.md), and arbitrage as abelian holonomy in [C076](../h_economics/c076_arbitrage_as_holonomy.md).
