# C037: Fusion Rules from the Verlinde Formula

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that returns the central charge, conformal weights and complete fusion rules of hidden
> Virasoro minimal models and SU(2)_k WZW models, computed from the Verlinde formula in exact
> cyclotomic arithmetic, for under $1.

## 2. Why This Task

The Verlinde formula (Verlinde 1988), N_{ij}^k = Σ_m S_{im} S_{jm} S̄_{km} / S_{0m}, turns the modular S-matrix of a rational conformal field theory into non-negative integer fusion coefficients. The entries of S are sines of rational multiples of π, so the sum lives in a cyclotomic field. Evaluating it in floating point and rounding is the usual shortcut, and it is forbidden here. Checking an answer is cheap: fusion must be an associative, commutative ring with the right unit, and the coefficients must match an independent combinatorial rule.

The task stresses OEWAS (Omega Engine Workflows, Agents, Skills) exact algebraic-number arithmetic through host tools, and OEEIS (Omega Engine Epistemic Immune System) screening of rounding-based answers and of Kac-table double counting.

## 3. Formal Problem and Bounds

Models:

- **SU(2)_k**, 1 ≤ k ≤ 20. Primaries a = 0, …, k (a is twice the spin). S_{ab} = √(2/(k+2)) · sin(π(a+1)(b+1)/(k+2)). Conformal weight h_a = a(a+2) / (4(k+2)); central charge c = 3k/(k+2).
- **Virasoro minimal model M(p, p′)**, coprime p > p′ ≥ 2, p ≤ 13. Central charge c = 1 − 6(p − p′)²/(pp′). Primaries are Kac labels (r, s), 1 ≤ r ≤ p′ − 1, 1 ≤ s ≤ p − 1, identified under (r, s) ∼ (p′ − r, p − s), with weights h_{r,s} = ((pr − p′s)² − (p − p′)²)/(4pp′). The labelling convention is pinned in `TASK.md`.

In the Verlinde sum the normalization appears squared, so each term lies in Q(ζ_N) with N = 4(k+2) for SU(2)_k. Minimal-model S-matrices are products of two SU(2)-type factors, and `TASK.md` writes their field out.

Reference values (standard):

- Ising, M(4, 3): c = 1/2, h ∈ {0, 1/16, 1/2}; σ × σ = 1 + ε, σ × ε = σ, ε × ε = 1.
- Lee–Yang, M(5, 2): c = −22/5, a single nontrivial primary φ with h = −1/5 and φ × φ = 1 + φ.
- SU(2)_k: N_{ab}^c = 1 exactly when |a − b| ≤ c ≤ min(a + b, 2k − a − b) and a + b + c is even, and 0 otherwise.

Edge cases: k = 1 (two primaries, a simple current); odd k; non-unitary models (p − p′ > 1), where some S_{0m} are negative; Kac-label identification (each field listed once); p and p′ not coprime (malformed).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Input and outputs:

```json
{"case_id": "vf_02", "model": "minimal", "p": 4, "p_prime": 3}
{"id": "vf_02", "status": "SOLVED", "central_charge": "1/2",
 "primaries": [{"label": [1, 1], "h": "0"}, {"label": [1, 2], "h": "1/16"}, {"label": [2, 1], "h": "1/2"}],
 "fusion": [[[1, 2], [1, 2], [1, 1], 1], [[1, 2], [1, 2], [2, 1], 1], "…"]}
{"id": "vf_03", "status": "OUT_OF_SCOPE", "witness": {"kind": "not_coprime", "gcd": 2}}
{"id": "vf_04", "status": "UNKNOWN", "refusal_code": "LEVEL_OUT_OF_BOUNDS"}
```

The example's labels follow one common convention; `TASK.md` pins the one in force. `fusion` lists every nonzero N_{ij}^k once, with i ≤ j in the canonical order. A `SOLVED` answer is complete when c, every h (as reduced rationals, each field once after identification) and every fusion coefficient equal the checker's exact values, and no nonzero coefficient is missing. `OUT_OF_SCOPE` covers non-coprime (p, p′) and p′ < 2.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the S-matrix formulas in both families, the Kac-table convention, the identification rule and the canonical field order.
- `examples/`: 8 cases with exact outputs: Ising, Lee–Yang, tricritical Ising M(5, 4), SU(2)₁, SU(2)₂, SU(2)₃, a non-coprime pair and an oversized level.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 20 models: SU(2)_k for 8 levels up to 20, and 12 minimal models up to p = 13, including at least 5 non-unitary ones.
- **Relabel and gauge controls:** 8 controls: primaries renamed by a permutation (supplied); Kac labels given in the alternate representative (p′ − r, p − s); the SU(2)_k simple current relabelling a → k − a applied to one index, with N_{Ja,b}^{Jc} = N_{ab}^c checked. The fusion ring is invariant up to the stated map.
- **Poisoned-but-schema-valid cases:** 6 cases: SU(2)_k at odd k, where truncating at min(a + b, k) is wrong; non-unitary minimal models, where the sign of S_{0m} matters; a minimal model whose Kac table has many identified pairs, so double counting inflates the fusion list.
- **Exact checker (Rust):** the Verlinde sum in exact cyclotomic arithmetic, with the result checked to be a non-negative rational integer.
- **Independent second checker:** the truncated Clebsch–Gordan rule for SU(2)_k, and for minimal models the product of two SU(2) rules at levels p′ − 2 and p − 2 with Kac identification. Both also verify ring axioms: commutativity, associativity Σ_m N_{ab}^m N_{mc}^d = Σ_m N_{bc}^m N_{am}^d, and the unit.
- **Mutation suite:** one coefficient changed from 1 to 2, a missing nonzero entry, a field listed twice under two Kac labels, h with the wrong sign for a non-unitary model, weights h computed with p and p′ swapped, which permutes the Kac table, a fusion table that is commutative but not associative.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the combinatorial rules of the second checker packaged as a solver, which needs no Verlinde sum at all. E passes. If A only matches E, the result is automation; the Verlinde-exactness requirement is scored separately (§9). Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, Qwen3 32B, Gemma 3 27B. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 20/20 base and 8/8 controls, both checkers agreeing.
- **Primary metric (pre-registered):** per-case exact-match rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** whether the frozen solver computes fusion by an exact Verlinde sum. The sandbox records any floating-point use, which is labelled and reported, not hidden.

## 10. Interpretation

- Failing only non-unitary models means sign handling of S_{0m}, not the fusion concept, is the weakness.
- A solver that uses the combinatorial rule rather than the Verlinde formula passes the capability gate but not the secondary measure. Both are reported.
- A pass certifies exact fusion arithmetic for these rational conformal field theories. It makes no claim about critical phenomena or string backgrounds beyond these models.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a fusion table that is integral everywhere; signal 2 is a floating-point intermediate detected in the sandbox trace, or an associativity failure. Together they flag rounding-based answers.
- **Kinetic proofreading:** c and h, then fusion integrality, then ring axioms, then agreement with the combinatorial rule.
- **Thymus:** reject operands that truncate SU(2)_k fusion at min(a + b, k).

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds S-matrix entries as exact cyclotomic elements.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose model), `I` (integrate the S-matrix in the cyclotomic field), `R` (residual: fusion entries that are not non-negative integers, and ring-axiom failures), `D` as they are fixed, `E`, `T`. For minimal models, a `Λ` step lifts from two SU(2) factors to the product with identification. Logged measures: non-integral entries, associativity violations and duplicate fields.

Operands expected: (1) the Verlinde sum with the normalization squared into a rational; (2) the SU(2)_k truncation min(a + b, 2k − a − b); (3) minimal-model fusion as a product of two SU(2) rules with Kac identification; (4) the simple-current symmetry as a free check.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_number_theory/src/cyclotomic.rs` and the fixed-order modules (`cyclotomic28.rs`, `cyclotomic44.rs`, `cyclotomic52.rs`, `cyclotomic120.rs`) cover some but not all orders 4(k + 2); a general Q(ζ_N) type is new Rust work.
- `omega_engine/crates_rs/omega_quantum_physics/src/s_matrix.rs` and `modular_tensor_category.rs` are best-effort scaffolds and are not used for checking.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize exact Verlinde fusion for SU(2)_k and Virasoro minimal models.
- **Does not support:** claims about other chiral algebras, about classification of conformal field theories, or about physical systems.
- **Narrowest defensible claim:** "Arm X returned exact central charges, weights and fusion rules for m of 20 hidden models, matching both checkers."
- **Next test:** a T4 variant for SU(3)_k, which needs the rank-2 weight machinery of C033.
