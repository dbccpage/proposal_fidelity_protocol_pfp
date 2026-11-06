# C028: Fermion-to-Qubit Mappings with Exact CAR Checks

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that maps hidden fermionic Hamiltonians to exact qubit Hamiltonians under a declared
> linear encoding (Jordan–Wigner, parity, Bravyi–Kitaev or another invertible one), with
> Majorana images that satisfy the canonical anticommutation relations exactly, for under $0.50.

## 2. Why This Task

Fermion-to-qubit mappings are pure sign bookkeeping. The Jordan–Wigner string, the reordering signs of creation and annihilation operators, and the factors of i in Majorana operators are exactly where a plausible derivation goes wrong. Every step is cheap to verify: the 2N Majorana images must be Hermitian Pauli strings that pairwise anticommute, they must act correctly on encoded basis states, and the Hamiltonian must equal its expansion in those images.

Bravyi and Kitaev (2002) showed that encodings other than Jordan–Wigner give shorter operator strings. The task stresses OEWAS (Engine Workflows, Agents, Skills) phase tracking through host checks, and OEEIS (Engine Epistemic Immune System) screening of answers correct up to a sign.

## 3. Formal Problem and Bounds

Input: N fermionic modes, 1 ≤ N ≤ 12; an invertible N × N matrix M over F2 (the encoding: occupation vector n is stored as qubit basis state |M n mod 2⟩); and a Hamiltonian H = Σ c_t · (product of at most 4 operators a_j or a_j†) with Gaussian-rational coefficients c_t. H must be Hermitian as given.

Conventions, fixed in `TASK.md`:

- Majorana operators γ_{2j} = a_j + a_j† and γ_{2j+1} = −i(a_j − a_j†), so {γ_k, γ_l} = 2δ_{kl}.
- Fock basis ordering: a_j† |n⟩ = (−1)^{Σ_{k < j} n_k} |n + e_j⟩ when n_j = 0, and 0 otherwise.
- Qubit |1⟩ means the stored bit is 1. With M = I this is Jordan–Wigner: a_j = (∏_{k < j} Z_k)(X_j + iY_j)/2.

Required output: the 2N Majorana images, each a Pauli string with a sign ±1, and the qubit Hamiltonian as a sum of distinct Pauli strings with real rational coefficients, all zero terms removed.

Edge cases: number operators (a_j† a_j maps to (I − Z_j)/2 under Jordan–Wigner); hopping between distant modes; terms written out of normal order (a_2 a_1† = −a_1† a_2); a term a_j a_j (zero); quartic terms with a repeated index; terms that cancel completely; N = 12 at the bound; a singular M and a non-Hermitian H (both malformed).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Input and outputs:

```json
{"case_id": "fq_06", "num_modes": 2, "encoding": [[1, 0], [0, 1]],
 "terms": [{"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
           {"coeff": ["1", "0"], "ops": [["dag", 1], ["ann", 0]]}]}
{"id": "fq_06", "status": "SOLVED",
 "majoranas": ["+XI", "+YI", "+ZX", "+ZY"],
 "hamiltonian": [["XX", "1/2"], ["YY", "1/2"]]}
{"id": "fq_07", "status": "OUT_OF_SCOPE", "witness": {"kind": "singular_encoding", "kernel_vector": [1, 1]}}
{"id": "fq_08", "status": "UNKNOWN", "refusal_code": "TOO_MANY_MODES"}
```

Qubit strings are written with qubit 0 on the left. A `SOLVED` answer is complete when: (a) the Majorana images are pairwise anticommuting and each squares to I; (b) for every occupation vector n (all 2^N when N ≤ 10, 1,024 sampled vectors otherwise), each image maps |M n⟩ to the encoded image of γ_k |n⟩ with the correct sign and phase; (c) expanding H in the verified images, with phase-tracked Pauli products, gives exactly the stated Pauli sum. `OUT_OF_SCOPE` covers a singular M (a kernel vector as witness) and a non-Hermitian H (a term whose conjugate is missing or has the wrong coefficient).

## 5. Participant Packet

- `TASK.md` with §3 and §4, the Majorana and ordering conventions, the parity and Bravyi–Kitaev matrices for N ≤ 8 written out, and the rule for multiplying Pauli strings with phases.
- `examples/`: 10 cases with exact outputs: a single number operator, the two-mode hopping above under Jordan–Wigner and under the parity encoding, a 4-mode quartic term, a cancelling pair, an out-of-order term, the same Hamiltonian under two encodings, a singular M and a non-Hermitian H.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 24 cases, N from 2 to 12: Hubbard-type chains and rings, random quadratic Hamiltonians, random quartic terms, under Jordan–Wigner, parity, Bravyi–Kitaev and random invertible encodings.
- **Relabel and gauge controls:** 8 controls: the same fermionic H under a different encoding, where for N ≤ 6 the exact characteristic polynomial of the qubit Hamiltonian must be unchanged; terms rewritten with anticommutation (a_i† a_j as −a_j a_i† for i ≠ j), where the output must be identical; term reordering.
- **Poisoned-but-schema-valid cases:** 6 cases: a hopping term across 10 modes, where a truncated Z string is wrong; a Hermitian pair entered with coefficients ±i; a term a_1 a_1† (equal to 1 − n_1, which leaves an identity term).
- **Exact checker (Rust):** checks (a), (b) and (c) of §4 using a phase-tracked Pauli product and F2 encoding arithmetic.
- **Independent second checker:** for N ≤ 6, builds H directly on the 2^N-dimensional Fock space from the ordering convention, conjugates by the encoding permutation, and compares the resulting matrix with the solver's Pauli sum entry by entry over Q(i). For larger N it applies H, built sparsely from the Fock-space definition, to 256 random encoded basis states and compares each result exactly with the action of the Pauli sum. This is labelled a spot check; the first checker's expansion (c) remains the complete check.
- **Mutation suite:** one Majorana image with a flipped sign, a Z string one qubit short, a Y written as X, a Hamiltonian with a stray imaginary coefficient, a merged pair of terms with a wrong sum, an identity term dropped.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: a direct implementation of the general linear-encoding construction (update, parity and flip sets derived from M). E should pass; the challenge measures reliable synthesis of sign-exact code. Arm F does not apply.

## 8. Budget, Models and Provenance

$0.50 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, Qwen3 14B, Mistral Small 24B. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 24/24 base and 8/8 controls, both checkers accepting.
- **Primary metric (pre-registered):** per-case certified-correct rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** the rate of answers correct up to one global or per-term sign, reported separately.

## 10. Interpretation

- Passing Jordan–Wigner and failing random encodings means the solver memorized a textbook mapping rather than deriving it from M.
- A high sign-only error rate in every arm points to phase bookkeeping as the shared weakness; host scratch space is the natural fix.
- A pass certifies algebraic identities of the stated encoding. It says nothing about simulation cost or hardware.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a Pauli sum whose strings are all right; signal 2 is a coefficient sign or phase that differs from the expansion. This is the sign-flip antimorphism (AM-5 family) at term level.
- **Kinetic proofreading:** CAR check, then basis-state action, then Hamiltonian expansion.
- **Thymus:** reject repair operands that "fix" a sign by dropping the Z string.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the running phase exponent (a power of i) for each product being expanded.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose conventions and M), `I` (integrate the Majorana images), `R` (residual: failed anticommutation pairs and wrong basis-state actions), `D` as they are fixed, `E` on exact images, then a second `I R D E` cycle for the Hamiltonian expansion, and `T`. Logged measures: failed CAR pairs, wrong basis-state actions, and mismatched Pauli coefficients.

Operands expected: (1) the Pauli product table with an explicit power-of-i counter; (2) normal ordering with a sign per transposition; (3) Majorana images for a general encoding M from its update, parity and flip sets; (4) Hermiticity check before mapping.

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_majorana` (GF(2) parity diagnostics and cell complexes; its receipts are diagnostic only).
- `engine/crates_rs/core_quantum_physics/src/pauli.rs` (commutation) and `binary_field.rs` (F2 arithmetic).
- `engine/crates_rs/core_symbol_game` exact characteristic polynomial and rank actions for the second checker.
- Rust has no phase-tracked Pauli string product. The checker needs one; [U14](../../upgrades/u14_rust_quantum_stabilizer_port.md) will provide a shared one and should be reused if it lands first.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize a sign-exact fermion-to-qubit mapper for arbitrary invertible linear encodings.
- **Does not support:** claims about Majorana hardware, topological qubits, or chemistry accuracy.
- **Narrowest defensible claim:** "Arm X produced exactly verified qubit Hamiltonians and Majorana images for k of 24 hidden fermionic Hamiltonians (N ≤ 12)."
- **Next test:** C021-style synthesis of a solver for the commuting subset of the mapped Hamiltonians.
