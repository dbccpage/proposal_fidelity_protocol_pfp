# C025: Exact Mutually Unbiased Bases in Prime-Power Dimensions

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that builds complete sets of mutually unbiased bases in exact cyclotomic arithmetic for
> d in {2, 3, 4, 5, 7, 8, 9}, and says UNKNOWN for d = 6, for under $0.50.

## 2. Why This Task

Complete sets of d + 1 mutually unbiased bases (MUBs) exist in every prime-power dimension (Wootters and Fields 1989). Whether four MUBs exist in d = 6 is open. The task therefore tests two things at once: exact construction where the answer is known, and refusal where it is not. A solver that "completes" d = 6 by analogy is wrong, however well formatted its output.

Generation is hard in d = 4, 8 and 9, where arithmetic modulo d fails and the construction must use the finite field GF(d). Verification is cheap: orthonormality and unbiasedness are finitely many exact inner products in a cyclotomic field. The task stresses OEWAS (Engine Workflows, Agents, Skills) retrieval of the finite-field construction and OEEIS (Engine Epistemic Immune System) screening of overclaims on an open problem.

## 3. Formal Problem and Bounds

Input: a dimension d with 2 ≤ d ≤ 10 and a requested number of bases k with 2 ≤ k ≤ d + 1. Optionally, a fixed first basis B₀ that the set must contain.

Bases B₁, …, B_k of C^d are mutually unbiased when each is orthonormal and |⟨e, f⟩|² = 1/d for every e ∈ Bᵢ, f ∈ Bⱼ, i ≠ j. To keep everything exact without square roots, the solver returns unnormalized vectors with entries in Q(ζ_m) and a declared rational squared norm N_v per vector. The conditions become: ⟨v, v⟩ = N_v; ⟨v, w⟩ = 0 within a basis; and d · |⟨v, w⟩|² = N_v N_w across bases.

Known facts used by the judge:

- At most d + 1 MUBs exist in dimension d, and d + 1 exist when d is a prime power (Wootters and Fields 1989).
- For d = 6 and d = 10, three MUBs exist (tensor products of complete sets in the prime factors). For d = 6, whether even four exist is open. The judge poses no d = 10 request with k ≥ 4, because this spec does not rely on the status of that case.

Expected status by request: d ∈ {2, 3, 4, 5, 7, 8, 9} with any k ≤ d + 1: `SOLVED`. d ∈ {6, 10} with k ≤ 3: `SOLVED`. d = 6 with k ≥ 4: `UNKNOWN` with refusal code `OPEN_PROBLEM`. Any k > d + 1: `OUT_OF_SCOPE`.

Edge cases: d = 2 (Pauli eigenbases); d = 4 and 8, where Z₄ or Z₈ arithmetic gives bases that are not unbiased; d = 9, where GF(9) is required; k = 2 (any Fourier pair); a fixed B₀ that is a monomial rotation of the standard basis.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Field elements are lists of m rational strings, the coefficients of ζ_m^0 … ζ_m^{m−1}; the checker reduces them modulo the cyclotomic polynomial Φ_m. Input and outputs:

```json
{"case_id": "mub_05", "dimension": 3, "num_bases": 4, "fixed_first_basis": null}
{"id": "mub_05", "status": "SOLVED", "cyclotomic_order": 3,
 "bases": [[{"norm2": "1", "entries": [["1","0","0"], ["0","0","0"], ["0","0","0"]]}, "…"], "…"]}
{"id": "mub_06", "status": "UNKNOWN", "refusal_code": "OPEN_PROBLEM"}
{"id": "mub_07", "status": "OUT_OF_SCOPE", "witness": {"requested": 8, "max_possible": 7}}
```

A `SOLVED` answer is complete when the checker verifies every orthogonality and unbiasedness identity exactly, confirms k bases of d vectors each, and, if B₀ was given, confirms that one returned basis equals B₀ up to per-vector phases in the field and reordering.

## 5. Participant Packet

- `TASK.md` with §3 and §4 and the field-element encoding.
- `examples/`: 8 cases with exact outputs: d = 2 (k = 3), d = 3 (k = 4), d = 5 (k = 2), d = 4 (k = 2), d = 6 (k = 3, tensor product), d = 6 (k = 4, `UNKNOWN`), d = 4 (k = 6, `OUT_OF_SCOPE`), and one fixed-B₀ case in d = 3.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** complete sets for each d ∈ {2, 3, 4, 5, 7, 8, 9}, partial sets for three of them, three MUBs for d = 6 and d = 10, and three open requests for d = 6 (k = 4, 5, 7): 15 cases.
- **Relabel and gauge controls:** 8 controls, each giving a fixed first basis B₀ = U·(standard basis), where U is a Clifford or monomial unitary with entries in the field. The existence answer is invariant; the returned set must contain B₀.
- **Poisoned-but-schema-valid cases:** 5 cases: d = 4, 8 and 9 (where modular arithmetic tempts), d = 6 with k = 4 and a fixed B₀ drawn from the three-basis tensor set, and d = 10 with k = 3, where the tensor product with d = 5 tempts a solver to claim six bases.
- **Exact checker (Rust):** direct inner products over Q(ζ_m).
- **Independent second checker:** the projector-algebra route, checking tr(PᵢPⱼ) = 1/d for rank-one projectors, through `verify_mub_projector_algebra`.
- **Mutation suite:** one entry off by a root of unity, a Z₄-arithmetic set in d = 4, a wrong `norm2`, a d = 6 "complete set" of 7 bases, two identical bases, a fixed B₀ that is missing from the output.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the estate's existing constructions for d = 2, 3, 4, 5 and the d = 6 tensor product, extended with the odd-prime-power and characteristic-two Weyl constructions in `core_mub`. If E already covers every `SOLVED` case, a pass in A shows automation, not a model advantage. Arm F does not apply.

## 8. Budget, Models and Provenance

$0.50 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, Qwen3 32B, `deepseek/deepseek-r1-distill-qwen-32b`. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** every `SOLVED` case certified by both checkers, every open request answered `UNKNOWN`, every impossible request `OUT_OF_SCOPE`, and 8/8 controls.
- **Primary metric (pre-registered):** per-case correctness on the 15 base cases, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Hard fail:** any claim of four or more MUBs in d = 6 is scored as a critical error and reported separately, whatever the rest of the run.

## 10. Interpretation

- Passing prime d but failing d = 4, 8, 9 means the solver used modular rather than finite-field arithmetic.
- An arm that answers d = 6 with k ≥ 4 as `SOLVED` has overclaimed on an open problem. That is the most important failure this challenge detects.
- A passing run shows exact construction of known objects, not progress on the d = 6 problem.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a `SOLVED` claim for d = 6 with k ≥ 4; signal 2 is any unbiasedness identity failing. Signal 1 alone triggers review; both together quarantine the candidate.
- **Thymus:** the self-panel includes the d = 6 open-problem statement, so no operand that asserts completion in d = 6 is admitted.
- **Treg** (`TregSupervisor`): damps repeated retries on d = 6 after a correct refusal.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the GF(d) multiplication table and trace map, so the model does not rebuild them in text.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose d and field), `Λ` (lift from Z_p to GF(p^r) when d is not prime), `I` (integrate the Weyl or quadratic-chirp construction), `R` (residual: the count of failing unbiasedness identities), `D`, `E`, `T`; for open requests `C M T`. Logged measure: the number of failing identities, split into orthogonality and unbiasedness.

Operands expected: (1) for odd prime p, the quadratic-chirp bases ω^{a x² + b x}; (2) for d = 2^r, use GF(2^r) and the trace form, never Z_d; (3) tensor products give min over factors of (pᵢ^{rᵢ} + 1) bases; (4) refuse d = 6 with k ≥ 4 as an open problem.

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_quantum_physics/src/mub/` (`odd_prime.rs` d = 3, 5; `char_two.rs` d = 2, 4; `composite.rs` d = 6 tensor product; `algebra.rs` `verify_mub_projector_algebra`).
- `engine/crates_rs/core_number_theory/src/finite_field.rs` (GF(p^k)), `cyclotomic.rs` (`Cyc5`, `Cyc8`, `Cyc12`, `Cyc24`) and `cyclotomic28.rs` (contains ζ₇).
- `engine/crates_rs/core_mub` (`odd_prime_power_weyl.rs`, `char_two_weyl_board.rs`, `composite_controls.rs`). The d = 6 research modules there are about the open problem and must not be used to claim a solution.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize exact MUB constructions in prime-power dimensions and refuse the open d = 6 case.
- **Does not support:** anything about the existence of four MUBs in d = 6, or about composite dimensions beyond the tensor bound.
- **Narrowest defensible claim:** "Arm X returned exactly verified complete MUB sets for d in {2, 3, 4, 5, 7, 8, 9} and refused every open request."
- **Next test:** C027 (Kochen–Specker sets), which reuses exact projector arithmetic.
