# C026: Frustration-Free Projector Hamiltonians

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that decides whether a hidden sum of local rational projectors has a zero-energy state,
> returning the full zero-energy space or a certificate that it is trivial, for under $1.

## 2. Why This Task

For H = Σᵢ Pᵢ with each Pᵢ a projector (Pᵢ² = Pᵢ = Pᵢ†), every term is positive semidefinite, so H has a zero-energy state exactly when the kernels of all Pᵢ (each extended by the identity off its support) have a nonzero common intersection. Such an H is called frustration-free. The check reduces to exact kernel intersection, which is cheap for the bounds below. Finding the answer by reasoning about "which local states satisfy every term" is not: entangled kernels, and local satisfiability that fails globally, trip heuristic search.

The task stresses exact linear algebra through host calls in OEWAS (Omega Engine Workflows, Agents, Skills) and OEEIS (Omega Engine Epistemic Immune System) screening of product-state guesses presented as the whole ground space.

## 3. Formal Problem and Bounds

Input: sites with local dimension 2 or 3 and total dimension D = ∏ dₛ ≤ 64; up to 20 terms. Each term has a support (a list of sites, at most 3) and a matrix over Q(i) on the support's space. Weights wᵢ > 0 in Q may multiply terms; they do not change the answer.

Decide whether K = ⋂ᵢ ker(Pᵢ ⊗ I) is nonzero. If it is, return a basis of K; dim K is the ground-space degeneracy at energy 0. If K = {0}, return a certificate of that.

Reference facts the hidden set uses (all follow directly from the definitions):

- Hard-core terms |11⟩⟨11| on the edges of a graph: K is spanned by the basis states whose 1-positions form an independent set, so dim K equals the number of independent sets, including the empty set. For a triangle, dim K = 4.
- The singlet projector on each pair of a triangle of qubits: K is the symmetric subspace, dim K = 4.
- The triplet projector on each pair of a triangle of qubits: K = {0}, because no three-qubit state is a singlet on every pair. Each pair alone is satisfiable; the whole is frustrated.

Edge cases: a single term; terms with overlapping supports; a kernel containing only entangled states; a case at D = 64; a matrix that is Hermitian but not idempotent (malformed); a support naming a missing site (malformed).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Matrices are row-major lists of Gaussian rationals `["a", "b"]` meaning a + b·i. Input and outputs:

```json
{"case_id": "ff_03", "local_dims": [2, 2, 2],
 "terms": [{"support": [0, 1], "weight": "1", "matrix": "…4x4…"}, "…"]}
{"id": "ff_03", "status": "SOLVED", "frustration_free": true, "kernel_dim": 4, "kernel_basis": ["…"]}
{"id": "ff_04", "status": "SOLVED", "frustration_free": false,
 "certificate": {"kind": "left_inverse", "matrix": "…"}}
{"id": "ff_05", "status": "OUT_OF_SCOPE", "witness": {"term": 2, "reason": "not_idempotent", "entry": [1, 3]}}
{"id": "ff_06", "status": "UNKNOWN", "refusal_code": "DIMENSION_OUT_OF_BOUNDS"}
```

A frustration-free certificate is complete when every basis vector is annihilated by every extended term, the vectors are linearly independent, and `kernel_dim` equals D minus the rank of the stacked matrix [P₁ ⊗ I; …; P_m ⊗ I], which the checker computes itself. A frustrated certificate is complete when the checker verifies L · [P₁ ⊗ I; …; P_m ⊗ I] = I_D exactly for the supplied L. `OUT_OF_SCOPE` requires a term that is not a projector, with the offending entry of P² − P or P − P†.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the Kronecker ordering convention for extending a term, and the three reference facts above.
- `examples/`: 9 cases with exact outputs: the three reference facts, a 1D chain of hard-core terms, a rational rotation of one of them, a single rank-one term, one malformed matrix, one missing site and one out-of-bounds case.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 24 cases on 3 to 6 qubits or up to 3 qutrits: hard-core terms on random graphs, random rational rank-one and rank-two projectors, singlet and triplet mixtures, and entangled-kernel cases.
- **Relabel and gauge controls:** 8 controls: site permutation; a local change of basis by a rational orthogonal matrix such as [[3/5, −4/5], [4/5, 3/5]] on one site; positive rescaling of weights. dim K is invariant under all three.
- **Poisoned-but-schema-valid cases:** 6 cases: a kernel with no product state in it; a frustrated case in which every pair of terms is jointly satisfiable; a Hermitian term equal to a projector except for one perturbed off-diagonal pair of entries, so that P² ≠ P while every other check looks normal.
- **Exact checker (Rust):** annihilation, independence and the stacked rank over Q(i), or the left-inverse identity.
- **Independent second checker:** forms H = Σ wᵢ Pᵢ ⊗ I and computes its nullity by exact LDLᴴ, sharing no code with the stacked-rank route. Positive semidefiniteness makes the two nullities equal.
- **Mutation suite:** a basis vector violating one term, a dependent basis, a `kernel_dim` one too small (the product-state-only answer), a left inverse off in one entry, a frustrated answer for a frustration-free case.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: direct kernel intersection with `omega_linear_algebra`. E should pass everything, so C026 measures whether an arm reaches exact linear algebra reliably rather than whether it beats E. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, Mistral Small 24B. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 24/24 base and 8/8 controls, both checkers accepting.
- **Primary metric (pre-registered):** per-case certified-correct rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** rate of product-state-only answers (correct frustration-free flag, wrong `kernel_dim`).

## 10. Interpretation

- A right `frustration_free` flag with a wrong `kernel_dim` is scored wrong; the full ground space is the point, as in Q40.
- If A and E both pass and B does not, the engine's host calls are what closes the gap; compare A with C to see whether the representation matters.
- Passing says nothing about quantum k-SAT complexity beyond these bounds.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a frustration-free claim; signal 2 is a basis made only of product states when the stacked rank implies a larger kernel.
- **Kinetic proofreading:** annihilation, then independence, then the rank identity.
- **Allostery** (`AllostericConsensusGate`): a frustrated verdict is accepted only when the left-inverse check and the LDLᴴ nullity agree.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the running kernel basis after each term is intersected.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose terms), `I` (kernel of the first term), then one `D` per term as the running kernel shrinks, `R` when a candidate vector leaves a residual ⟨ψ|H|ψ⟩ > 0, `E` on an exact basis, and `T`; for frustrated cases the final `D` reaches dimension 0 and `T` carries the left inverse. Logged measure: the running kernel dimension after each term.

Operands expected: (1) frustration-free means a nonzero common kernel, found term by term; (2) hard-core edge terms count independent sets; (3) the triplet triangle is locally satisfiable but globally frustrated; (4) a trivial common kernel is certified by a left inverse of the stacked matrix.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_linear_algebra` (`image_kernel.rs`, `exact_ldlt.rs`, `determinant.rs`).
- `omega_engine/crates_rs/omega_quantum_physics` (exact finite quantum mechanics), including `src/rational.rs` and `cyclotomic.rs` (`GaussianRat`).
- A Kronecker-extension helper and the left-inverse check are new work in Rust.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize an exact frustration-freeness decider that returns the whole zero-energy space.
- **Does not support:** claims about spectral gaps, thermodynamic limits, or the complexity of quantum k-SAT in general.
- **Narrowest defensible claim:** "Arm X decided frustration-freeness, with full kernels or left-inverse certificates, for k of 24 hidden cases (D ≤ 64)."
- **Next test:** C039, where the toric-code ground space is a frustration-free kernel with topological degeneracy.
