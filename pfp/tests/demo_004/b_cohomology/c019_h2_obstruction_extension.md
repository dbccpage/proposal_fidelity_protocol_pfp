# C019: Degree-2 Obstructions at Scale

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that, on hidden 2-complexes with up to 32 cavities, either extends a 2-cochain
> to a 1-cochain potential or returns a certified H² obstruction, for under $1.

## 2. Why This Task

Demo 6 (`research/mssn_sn_tower/demos/demo_6/6_demo.md`) moved the Symbol Game's certificates from degree 1 to degree 2 on two small complexes: a hollow tetrahedron (b₂ = 1) and two tetrahedra fused along a septum (b₂ = 2). A target 2-cochain B with nonzero flux through a closed cavity cannot be written as d₁A for any 1-cochain A, because ⟨d₁A, Z⟩ = ⟨A, ∂Z⟩ = 0 for every 2-cycle Z. The degree-2 obstruction Φ₂ was certified by LP duality with the Rust `omega_functional` `Phi2Functional`. This challenge scales that from 2 cavities to 32 and from 7 faces to thousands, where shared septa, nested shells and integer torsion make the witness hard to find and easy to check.

The challenge stresses the Symbol Game's degree-2 host, OEWAS (Omega Engine Workflows, Agents, Skills) decomposition by cavities (U13), and the OEEIS (Omega Engine Epistemic Immune System) refusal path. A pass shows the game can produce a certified degree-2 extension-or-obstruction solver. It does not give "flux" or "cavity" any physical meaning.

## 3. Formal Problem and Bounds

Input: an oriented 2-complex K = (V, E, F) with integer boundary maps ∂₁ and ∂₂ (∂₁∂₂ = 0), coboundaries d₀ = ∂₁ᵀ and d₁ = ∂₂ᵀ, a target B ∈ Q^F, positive rational face weights ω, and a coefficient mode (`Q` or `Z`).

**Mode Q.** Output either `EXTENDS` with A ∈ Q^E and d₁A = B exactly, or `OBSTRUCTED` with a 2-cycle Z ∈ Q^F (∂₂Z = 0) and ⟨B, Z⟩ ≠ 0. Over Q exactly one of these holds, because on a 2-complex the orthogonal complement of im d₁ is ker ∂₂ = H₂(K; Q). In both cases also return

Φ₂(B) = min over A of Σ_f ω_f |B_f − (d₁A)_f| = max { ⟨B, y⟩ : ∂₂y = 0, |y_f| ≤ ω_f },

with a primal A and a dual 2-cycle y attaining equal values (Φ₂ = 0 exactly when B extends).

**Mode Z.** B is integral and A must be integral. Integral extension can fail even when rational extension succeeds: H²(K; Z) can have torsion. For RP², H²(RP²; Z) = Z/2 (Hatcher 2002). An integral obstruction is certified by a modulus m ≥ 2 and an integer chain Z with ∂₂Z ≡ 0 (mod m) and ⟨B, Z⟩ ≢ 0 (mod m): if B = d₁A with A integral, then ⟨B, Z⟩ = ⟨A, ∂₂Z⟩ ≡ 0 (mod m).

Reference cases from Demo 6 (public): the hollow tetrahedron with B = (1/4, −1/4, 1/4, −1/4) and unit weights has Φ₂ = 1 with dual y = (1, −1, 1, −1); the fused tetrahedra with B = (0, −1/3, 1/3, −1/3, 1/3, −1/3, 1/3) have Φ₂ = 2 with dual the outer shell Z₁ + Z₂.

Bounds: b₂ from 1 to 32, |F| ≤ 5,000, |E| ≤ 7,500, B entries rationals with numerator and denominator at most 999. The hidden set must contain stacked and nested shells, cavities sharing septa, a complex with b₂ = 0 (every B extends over Q), RP² and other torsion cases in mode Z, targets whose fluxes through individual cavities cancel in the outer shell (zero total flux, still obstructed), and exact targets with large entries.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, run in the U09 sandbox:

```json
{"status": "SOLVED", "mode": "Q", "verdict": "OBSTRUCTED", "cycle": {"f0": "1", "f1": "-1", "f2": "1", "f3": "-1"}, "pairing": "1", "phi2": "1", "primal_A": {}, "dual_y": {"f0": "1", "f1": "-1", "f2": "1", "f3": "-1"}}
{"status": "SOLVED", "mode": "Z", "verdict": "OBSTRUCTED_INTEGRAL", "modulus": "2", "chain": {"f0": "1", "f1": "1"}, "pairing_mod": "1"}
{"status": "SOLVED", "mode": "Q", "verdict": "EXTENDS", "A": {"e3": "-1/3"}, "phi2": "0"}
{"status": "OUT_OF_SCOPE", "witness": {"reason": "BOUNDARY_NOT_NILPOTENT", "face": "f12"}}
```

Omitted entries are zero. The first example is the Demo 6 hollow tetrahedron; the other two are schematic. The certificate is complete when every stated identity replays exactly: d₁A = B; ∂₂Z = 0 and ⟨B, Z⟩ equals `pairing` ≠ 0; ∂₂y = 0, |y_f| ≤ ω_f and ⟨B, y⟩ = Σ ω_f |B_f − (d₁A)_f| = phi2; ∂₂Z ≡ 0 and ⟨B, Z⟩ ≡ `pairing_mod` ≢ 0 modulo m. `OUT_OF_SCOPE` covers inputs with ∂₁∂₂ ≠ 0.

## 5. Participant Packet

- `TASK.md` with conventions, both modes and the certificate rules.
- `examples/`: 18 public cases with exact input and output JSON: both Demo 6 dossiers with their near-misses, a 4-cavity stack, a nested pair of shells, RP² in mode Z, a b₂ = 0 case, and two `OUT_OF_SCOPE` inputs.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 40, with b₂ spread from 1 to 32 and eight in mode Z.
- **Relabel and gauge controls:** 16. Face and edge relabelling; reversing a face (negates B_f and the cycle entry); adding d₁C to B for a random 1-cochain C (verdict and Φ₂ unchanged; A shifts by C).
- **Poisoned but schema-valid:** 12. Demo 6's near-miss types at scale (a 2-chain leaking through a septum; a dual scaled beyond the weights; a suboptimal dual with nonzero gap; float strings); targets with zero flux through the outer shell but nonzero flux through individual cavities, which a solver testing only total flux calls extendable; mode-Z cases whose rational extension exists.
- **Exact checker:** `omega_functional::phi2` (`Phi2Functional::verify_exact_certificate`, binary `verify_phi2`) for Φ₂ certificates, plus direct `BigInt` checks of d₁A = B, ∂₂Z = 0 and the modular condition.
- **Independent second checker:** Demo 6's Python checker pattern (`research/mssn_sn_tower/demos/demo_6/dossier_1_hollow_tetrahedron_b2_1/checker.py`), generalized and rewritten separately, plus an SNF of ∂₂ via `omega_linear_algebra::smith_normal_form_checked` to confirm torsion in mode Z.
- **Checker mutation suite:** Demo 6's four near-miss refusals (`REFUSED_FLOAT_DETECTED`, `REFUSED_DUAL_NOT_CLOSED_2_CYCLE`, `REFUSED_DUAL_NORM_EXCEEDS_WEIGHT`, `REFUSED_DUALITY_GAP_NONZERO`), plus an `EXTENDS` answer with one face off, a mode-Z chain that is a cycle only over Q, and a modulus of 1.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis with U13 decomposition by cavities (shells and septa as subproblems, integrated through the shared faces).
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** Exact linear solve for A, a kernel basis of ∂₂ for Z, `omega_solvers::solve_weighted_l1_projection` applied to d₁ for Φ₂, and SNF for mode Z, wrapped as `solve`. Expected to solve every case.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3-32B (route pinned in U06). $1.00 per arm through `BudgetController`; every call records provider, model ID, generation ID, tokens and billed cost. The sandbox provides the Python standard library only; the declared time limit must allow a sparse solve at |F| = 5,000, so dense elimination is a real risk the solver has to manage. U10 is recommended, as the [Q40 review](../00_q40_review.md) explains.

## 9. Pass Gates and Statistics

- **Capability gate:** 40/40 hidden base cases with complete certificates, all controls consistent, all poisoned cases correct, on at least 2 of 3 seeds.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05.
- **Scale curve:** success by b₂ band (1 to 4, 5 to 16, 17 to 32) and by mode, per arm.
- **Economics:** cost per verified success.

## 10. Interpretation

- **A passes, B fails:** the game adds capability for certified degree-2 obstructions at this scale and budget.
- **Arms pass mode Q and fail mode Z:** torsion is the missing concept; rational reasoning was carried over to integers.
- **Arms test only the outer shell and miss cancelling cavity fluxes:** the per-cavity decomposition was skipped; a basis of H₂, not one shell, decides extension.
- **Arms decide extension correctly but return suboptimal Φ₂ duals:** they found a witness but not the best combination of shells.
- **E matches A:** useful automation, no incremental model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; the refusal path, extended from Demo 6's named refusal codes, is the immune analogue.
- **Antimorphisms expected:** leaking 2-chains presented as cycles (AM-FSP-2); float rounding (Demo 6's `0.24999999999999994`); AM-2 absolute claims that a rational extension implies an integral one.
- **Scratch space (U12, optional):** a per-cavity flux ledger. **Layer 2:** grammar-constrained JSON allowed equally. **Layer 1:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, `Λ` (lift into per-cavity subproblems), `R` (project B onto the cycle space to read cavity fluxes), `D`/`M` over candidate solvers, `I` (combine cavity witnesses through shared septa), `E`, `T`. Logged measures: public cases failed, duality gap, leaking-chain norm ‖∂₂Z‖₁ on rejected witnesses.

Operands this challenge should yield:

```text
operand cavity_flux_witness.v1 | kind: move | when: B has nonzero pairing with a closed shell Z | do: return Z as the obstruction | check: boundary of Z is 0 and <B, Z> != 0
operand septum_outer_shell.v1 | kind: move | when: building the Phi2 dual and cavities share a septum face | do: try sums of adjacent shells so the septum cancels | check: the sum is a cycle within the weights and raises <B, y>
operand integral_torsion_mod_m.v1 | kind: guard | when: mode Z and a rational extension exists | do: compute SNF of the boundary map and search mod-m cycles for invariant factors m > 1 | check: <B, Z> nonzero mod m
```

## 13. Estate Reuse and Prerequisites

- `omega_engine_projects/mssn_sn_symgam/demos/demo_6` (packaged demo) and `research/mssn_sn_tower/demos/demo_6/` (dossiers, checkers, near-miss witnesses).
- `omega_engine/crates_rs/omega_functional` (`phi2.rs`, `bin/verify_phi2.rs`), `omega_engine/crates_rs/omega_solvers` (`exact_weighted_l1_lp.rs`), `omega_engine/crates_rs/omega_linear_algebra` (`smith_normal_form.rs`).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrade: [U13](../../upgrades/u13_cohomological_task_decomposition.md).

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose degree-2 extensions, cavity obstructions, Φ₂ certificates and integral torsion witnesses replay exactly on hidden complexes with up to 32 cavities.
- **Does not support:** any physical reading of flux or cavities; obstructions in degree 3 or higher; nonabelian obstruction theory.
- **Narrowest defensible claim:** the frozen solver returned replayable degree-2 certificates on the measured number of hidden complexes at the measured cost.
- **Next test:** 3-complexes (degree-3 obstructions), which need checker work beyond `phi2`, and the spectral-sequence view of the same complexes in [C020](c020_spectral_sequence_double_complex.md).
