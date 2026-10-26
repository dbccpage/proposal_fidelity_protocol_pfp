# C014: Exact Discrete Hodge Decomposition

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that splits edge flows on hidden 2-complexes into gradient, curl and harmonic
> parts over Q, with exact orthogonality certificates, for under $0.50.

## 2. Why This Task

Every edge flow on a 2-complex splits uniquely into a gradient part (from vertex potentials), a curl part (from face potentials) and a harmonic part, which is orthogonal to both; the harmonic space has dimension b₁ over Q (Eckmann 1944; see Lim 2020 for a modern account). This is the L2 counterpart of the L1 repair in [C011](c011_cycle_rank_ladder_coboundary_repair.md) and the structure behind the harmonic residuals the Symbol Game reports. In the estate it exists only as float diagnostics: `omega_engine/crates_rs/omega_solvers/src/solver_hodge_primal_dual_decomp.rs` is labelled "FLOAT DIAGNOSTICS ONLY" and must not certify. An exact version needs rational linear solves and careful sign conventions, which is hard to get right; checking it is a few exact matrix-vector products.

The challenge stresses the Symbol Game's exact host, OEWAS (Omega Engine Workflows, Agents, Skills) synthesis, and no OEEIS (Omega Engine Epistemic Immune System) mechanism beyond the refusal path. A pass shows the game can produce a certified exact Hodge solver. It does not give the parts any physical meaning.

## 3. Formal Problem and Bounds

Input: an oriented 2-complex K = (V, E, F) with integer incidence matrices δ₀: C^0 → C^1 and δ₁: C^1 → C^2 satisfying δ₁δ₀ = 0, a flow f ∈ Q^E, and positive rational edge weights W₁ = diag(w_e) defining the inner product ⟨a, b⟩ = Σ w_e a_e b_e (default all 1). Output: φ ∈ Q^V, ψ ∈ Q^F and h ∈ Q^E with

f = δ₀φ + W₁⁻¹δ₁ᵀψ + h, δ₁h = 0, δ₀ᵀW₁h = 0.

The three parts g = δ₀φ, c = W₁⁻¹δ₁ᵀψ and h are pairwise orthogonal under ⟨·,·⟩: ⟨g, c⟩ = φᵀδ₀ᵀδ₁ᵀψ = 0 because δ₁δ₀ = 0; ⟨g, h⟩ = φᵀδ₀ᵀW₁h = 0; ⟨c, h⟩ = ψᵀδ₁h = 0. Hence g, c and h are unique, though φ and ψ are not (φ up to locally constant functions, ψ up to ker δ₁ᵀ). One route: φ solves δ₀ᵀW₁δ₀φ = δ₀ᵀW₁f, and ψ solves δ₁W₁⁻¹δ₁ᵀψ = δ₁f.

Also required: dim of the harmonic space, which equals b₁(K; Q) = |E| − rank δ₀ − rank δ₁, and a basis of it.

Bounds: |V| ≤ 80, |E| ≤ 200, |F| ≤ 150, flow entries rationals with numerator and denominator at most 999, weight denominators ≤ 12. The hidden set must contain graphs with no faces (ψ empty, c = 0), complexes with b₁ = 0 (h = 0), a hollow triangle next to a filled one (the filled face removes one harmonic dimension), disconnected complexes, pure gradient and pure harmonic flows, and nonuniform weights.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, run in the U09 sandbox:

```json
{"status": "SOLVED", "phi": {"v0": "0", "v1": "1/3"}, "psi": {"f0": "-2/3"}, "h": {"e0": "1/3", "e1": "1/3"}, "harmonic_dim": "1", "harmonic_basis": [{"e0": "1", "e1": "1", "e2": "1"}]}
{"status": "OUT_OF_SCOPE", "witness": {"reason": "D1_D0_NONZERO", "face": "f2", "vertex": "v4"}}
{"status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"}
```

The example values are schematic. Omitted entries are zero; rationals are canonical strings. The certificate is complete when the decomposition identity and both harmonic conditions hold exactly, `harmonic_dim` equals the checker's b₁, and the basis vectors are independent and harmonic. `OUT_OF_SCOPE` covers inputs with δ₁δ₀ ≠ 0 (an unoriented or inconsistently oriented face), with one nonzero entry as witness.

## 5. Participant Packet

- `TASK.md` with orientation conventions, the weighted inner product and the certificate rules.
- `examples/`: 20 public cases with exact input and output JSON: a triangle hollow and filled, a square with one diagonal, a tetrahedron surface (b₁ = 0), a torus triangulation (b₁ = 2), a graph with no faces, two weighted cases, and one inconsistent orientation.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 40.
- **Relabel and gauge controls:** 16. Vertex and edge relabelling; reversing an edge (negates that coordinate of f, of the parts and of δ rows); reversing a face (negates ψ at that face); adding a locally constant function to φ (the parts do not change).
- **Poisoned but schema-valid:** 12. Complexes where the unweighted and weighted decompositions differ, so a solver ignoring W₁ fails; flows whose harmonic part is small relative to f (exact arithmetic must not lose it); complexes with a face whose boundary uses an edge twice with opposite signs.
- **Exact checker:** new, small Rust code over `BigRational` using `omega_linear_algebra` for products and ranks. It checks the identity, δ₁h = 0, δ₀ᵀW₁h = 0, and b₁. No exact Hodge checker exists in the estate today, and `omega_engine/crates_rs/omega_solvers/src/hodge_certificate_checker.rs` checks an L1 certificate in `f64`, so neither is usable as is.
- **Independent second checker:** a separately written Python `Fraction` implementation that recomputes g, c and h by solving the two normal equations and compares parts, not potentials.
- **Checker mutation suite:** an h with δ₁h ≠ 0 in one face; an h orthogonal only under unit weights; a φ that shifts part of the flow into c; `harmonic_dim` off by one; a dependent harmonic basis; a float `0.3333`.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis of the solver.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** The second checker's normal-equation solve, wrapped as `solve`. Expected to solve every case.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, Qwen3-32B, Gemma 3 27B (route pinned in U06). $0.50 per arm through `BudgetController`; every call records provider, model ID, generation ID, tokens and billed cost. The sandbox provides the Python standard library only. U10 is recommended, as the [Q40 review](../00_q40_review.md) explains.

## 9. Pass Gates and Statistics

- **Capability gate:** 40/40 hidden base cases, all controls consistent, all poisoned cases correct, on at least 2 of 3 seeds.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05.
- **Error taxonomy:** weights ignored, wrong face orientation, harmonic dimension wrong, float contamination.
- **Economics:** cost per verified success.

## 10. Interpretation

- **A passes, B fails:** the game adds capability for exact Hodge decomposition at this budget.
- **Arms pass unweighted cases and fail weighted ones:** the models learned the textbook special case; the adjoint under W₁ is the missing step.
- **A ties C or D:** representation or sampling is not the source of any gain.
- **E matches A:** useful automation, no incremental model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; the refusal path only.
- **Antimorphisms expected:** float solves presented as exact; AM-5-style orientation sign flips; a harmonic part computed as "whatever is left over" without checking δ₀ᵀW₁h = 0.
- **Layer 2:** grammar-constrained JSON allowed equally. **Layer 1, scratch space:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, then `R` (residual projection: remove the gradient part, then the curl part), `D`/`M` over candidate solvers, `E` when every public identity holds exactly, `T`. Logged measures: public cases failed, the norms ⟨h, h⟩ of wrong harmonic parts, harmonic-dimension errors.

Operands this challenge should yield:

```text
operand gradient_by_normal_equation.v1 | kind: move | when: a flow on a complex | do: solve delta0^T W1 delta0 phi = delta0^T W1 f exactly | check: delta0^T W1 (f - delta0 phi) = 0
operand curl_by_normal_equation.v1 | kind: move | when: the gradient part is removed | do: solve delta1 W1^-1 delta1^T psi = delta1 f exactly | check: delta1 h = 0
operand harmonic_dimension_is_b1.v1 | kind: guard | when: reporting harmonic_dim | do: compute |E| - rank delta0 - rank delta1 exactly | check: equals the basis size
```

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_solvers` (`solver_hodge_primal_dual_decomp.rs`, float diagnostics, for contrast only).
- `omega_engine/crates_rs/omega_linear_algebra` (`image_kernel.rs`, `exact_ldlt.rs` for the normal equations) and `omega_engine/crates_rs/omega_homology` (`exact_betti.rs` for b₁).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: none in the catalog. Checker work: the exact Hodge checker described in §6.

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose exact Hodge decompositions and harmonic bases replay on hidden weighted 2-complexes.
- **Does not support:** any physical interpretation of the parts (flows, fields or rankings); anything about L1 repair, which is [C011](c011_cycle_rank_ladder_coboundary_repair.md); decompositions on complexes of dimension above 2.
- **Narrowest defensible claim:** the frozen solver returned exact decompositions with verified orthogonality on the measured number of hidden cases.
- **Next test:** compare the L2 harmonic part with the L1 minimal repair of C011 on the same cochains, and extend to degree 2 in [C019](c019_h2_obstruction_extension.md).
