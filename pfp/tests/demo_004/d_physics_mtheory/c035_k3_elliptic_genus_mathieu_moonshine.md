# C035: Mathieu Moonshine from the K3 Elliptic Genus

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that computes the coefficients A_n of the K3 elliptic genus in the N = 4
> superconformal character basis by exact series arithmetic, and decomposes them into M₂₄
> representations with non-negative integer multiplicities, for under $2.

## 2. Why This Task

Eguchi, Ooguri and Tachikawa (2010) observed that when the elliptic genus of K3 is expanded in characters of the N = 4 superconformal algebra, the coefficients of the massive characters are sums of dimensions of irreducible representations of the Mathieu group M₂₄: A₁ = 90 = 45 + 45̄, A₂ = 462 = 231 + 231̄, A₃ = 1540 = 770 + 770̄. Computing A_n is exact integer q-series arithmetic with theta functions. Decomposing a class function into irreducible characters is an exact inner product with the character table. Both are cheap to check and easy to get wrong through normalization, the massless character, or the confusion of dimension-matching with character-matching.

The task stresses OEWAS (Omega Engine Workflows, Agents, Skills) series arithmetic through host tools, and OEEIS (Omega Engine Epistemic Immune System) screening of decompositions that match dimensions but not characters.

## 3. Formal Problem and Bounds

The K3 elliptic genus is Z(τ, z) = 8 Σ_{i=2,3,4} (θᵢ(τ, z) / θᵢ(τ, 0))², a weak Jacobi form of weight 0 and index 1 with Z(τ, 0) = 24 = χ(K3). Write q = e^{2πiτ} and y = e^{2πiz}. Each q-coefficient is a Laurent polynomial in y with integer coefficients; all arithmetic stays in Z[y, y⁻¹][[q^{1/8}]].

`TASK.md` pins, from Eguchi, Ooguri and Tachikawa (2010), the decomposition Z = 24 · (massless character with h = 1/4, l = 0) + Σ_{n ≥ 0} A_n · (massive character with h = n + 1/4, l = 1/2), with the massive characters and the Appell–Lerch form of the massless character written out.

Query types:

1. **Coefficients:** return A_n for 1 ≤ n ≤ N, N ≤ 30.
2. **Decomposition:** given n and the class function g ↦ A_n(g) on the 26 conjugacy classes of M₂₄ (supplied in the case, taken from twining genera computed by the judge), return the multiplicity of each of the 26 irreducible representations.

Reference values: A₁, A₂, A₃ and their decompositions above. Values for n ≥ 4, and every class function, come from the judge's second checker at packet-build time. The M₂₄ character table is pinned by the operator from GAP's character table library, with its SHA-256 recorded.

Edge cases: n = 1, 2, 3, where the complex-conjugate pairs appear; the identity-class value A_n(1), which must equal the solver's own A_n from query 1; a supplied class function that is not a character (malformed); N = 30 at the bound.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Inputs and outputs:

```json
{"case_id": "m24_01", "query": "coefficients", "max_n": 3}
{"id": "m24_01", "status": "SOLVED", "A": {"1": 90, "2": 462, "3": 1540}}
{"case_id": "m24_05", "query": "decompose", "n": 1, "class_order": ["1A", "2A", "…"], "values": [90, "…"]}
{"id": "m24_05", "status": "SOLVED", "multiplicities": {"45": 1, "45bar": 1}, "zero_elsewhere": true}
{"id": "m24_06", "status": "OUT_OF_SCOPE", "witness": {"kind": "non_integral_multiplicity", "irrep": "231", "value": "3/2"}}
{"id": "m24_07", "status": "UNKNOWN", "refusal_code": "MAX_N_OUT_OF_BOUNDS"}
```

A coefficient answer is complete when every A_n equals the checker's exact series value. A decomposition is complete when every multiplicity is a non-negative integer and Σᵢ mᵢ χᵢ(g) = A_n(g) holds for all 26 classes; since the character table is invertible, this determines the multiplicities uniquely. `OUT_OF_SCOPE` covers supplied class functions whose inner product with some irreducible character is not a non-negative integer, with that irreducible as witness.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the theta-function conventions and q-expansions, the pinned character formulas, the M₂₄ character table with class names, and the inner-product formula weighted by class sizes.
- `examples/`: 8 cases with exact outputs: coefficients up to n = 3, the three decompositions above (class functions built from the pinned table), Z(τ, 0) = 24, a class function with one perturbed value (malformed), and an out-of-bounds request.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 6 coefficient queries (max_n from 5 to 30) and 16 decompositions for n from 4 to 20.
- **Relabel and gauge controls:** 8 controls: the class order permuted, with the permutation supplied; complex-conjugate pairs exchanged (45 ↔ 45̄), where multiplicities must swap; the substitution y ↔ y⁻¹ (the SU(2) Weyl reflection), under which every A_n is invariant.
- **Poisoned-but-schema-valid cases:** 6 cases: a class function with the correct identity value A_n(1) but one non-identity value changed, so dimension-only matching succeeds while the character check fails; a class function giving a negative multiplicity; decompositions at orders the judge selects, using the second checker, because A_n / 2 there is not the dimension of a single irreducible.
- **Exact checker (Rust):** integer q-series with Laurent-polynomial coefficients for the theta quotients, the character-basis extraction, and exact inner products over Q with the pinned table.
- **Independent second checker:** computes Z(τ, z) by a second route, as a weak Jacobi form built from the standard weight-0 index-1 generator, cross-checked against the theta-function route to order q³⁰. It computes the twining genera, from formulas the operator pins with references in the judge packet, to produce the class functions.
- **Mutation suite:** A_n off by 2, a massless-character term omitted, a decomposition that matches dimension but not one class, a negative multiplicity, conjugate irreducibles swapped without a control asking for it.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the checker's series code and inner products packaged as a solver. E passes by construction; the challenge measures synthesis of correct q-series and character arithmetic. Arm F does not apply.

## 8. Budget, Models and Provenance

$2.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `deepseek/deepseek-r1-distill-qwen-32b`. The GAP character table and the twining-genus references are pinned in the judge packet.

## 9. Pass Gates and Statistics

- **Capability gate:** 22/22 base and 8/8 controls, both checkers agreeing.
- **Primary metric (pre-registered):** per-case exact-match rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** the rate of dimension-only decompositions, correct in total dimension and wrong in characters.

## 10. Interpretation

- Correct A_n with dimension-only decompositions means the solver guessed irreducibles from dimensions. That is not a decomposition, and it is scored wrong.
- A pass certifies q-series arithmetic and character inner products. It gives no new evidence for or against any explanation of Mathieu moonshine, and no physical claim about K3 string compactifications.
- Reproducing the known decompositions certifies the computation, not any physical claim about string theory.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a decomposition whose dimensions sum to A_n; signal 2 is a mismatch at any non-identity class. Together they flag the dimension-matching antimorphism.
- **Kinetic proofreading:** series coefficients, then the identity-class match, then all 26 class matches, then non-negativity.
- **Thymus:** reject operands asserting that A_n / 2 is always an irreducible dimension.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds truncated q-series as coefficient arrays of Laurent polynomials, so the model never expands theta functions in text.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose the definitions), `I` (integrate the theta expansions), `R` (residual: Z minus the character sum truncated at order n), `D` as each A_n is fixed, `E` when the residual vanishes to the requested order, then `C I R E` for decompositions with the class-function residual, and `T`. Logged measures: the lowest order at which the residual is nonzero, and the number of mismatched classes.

Operands expected: (1) exact q-series with Laurent-polynomial coefficients; (2) peel characters order by order, massless term first; (3) decompose by inner product with the character table, never by dimension; (4) invariance under y ↔ y⁻¹ as a free check.

## 13. Estate Reuse and Prerequisites

- No modular-form, Jacobi-form or finite-group character module exists in the estate. The q-series engine and the character-table routines are new Rust work.
- `omega_engine/crates_rs/omega_kernel` for exact rationals and digests; `omega_engine/crates_rs/omega_linear_algebra` for inverting the character table.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize exact elliptic-genus series arithmetic and M₂₄ character decompositions.
- **Does not support:** any claim about the origin of Mathieu moonshine, about K3 sigma models, or about string theory.
- **Narrowest defensible claim:** "Arm X reproduced the judge's exact A_n up to n = N and M₂₄ decompositions for k of 16 hidden class functions."
- **Next test:** C036, which uses the same exact series machinery for mirror-symmetry invariants.
