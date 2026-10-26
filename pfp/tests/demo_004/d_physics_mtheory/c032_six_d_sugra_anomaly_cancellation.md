# C032: Six-Dimensional Supergravity Anomaly Cancellation

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> checker-generator that, for hidden six-dimensional (1,0) supergravity spectra, computes
> H − V + 29T, the anomaly coefficients and every factorization condition exactly, and names the
> first condition that fails, for under $1.

## 2. Why This Task

In six-dimensional (1,0) supergravity with T tensor multiplets, V vector multiplets and H hypermultiplets, cancelling the pure gravitational anomaly requires H − V + 29T = 273. The remaining anomalies cancel through the Green–Schwarz mechanism (Green and Schwarz 1984), generalized to several tensor multiplets by Sagnotti (1992), only if the anomaly polynomial factorizes. That imposes quadratic conditions relating a gravitational vector a and one vector bᵢ per simple gauge factor. Every condition is exact rational arithmetic once the group-theory trace coefficients are known.

The work is bookkeeping-heavy: dimensions of representations, half-hypermultiplets in pseudoreal representations, adjoint hypermultiplets, and trace coefficients for each representation. The task stresses OEWAS (Omega Engine Workflows, Agents, Skills) decomposition into group theory, counting and lattice checks, and OEEIS (Omega Engine Epistemic Immune System) screening of spectra that pass the counting condition but fail factorization.

## 3. Formal Problem and Bounds

Input: T with 0 ≤ T ≤ 30; a gauge group ∏ Gᵢ with at most 4 simple factors from SU(N) (N ≤ 8), SO(N) (7 ≤ N ≤ 14, N ≠ 8, because SO(8) has an extra quartic invariant, the Pfaffian, that this spec does not model), Sp(N) (N ≤ 4), G2, F4, E6, E7 and E8; hypermultiplets given as representations (by highest weight) of the gauge factors, with multiplicities that may be half-integers for pseudoreal representations; and a number of neutral hypermultiplets.

Definitions, fixed in `TASK.md`:

- V = Σᵢ dim Gᵢ. H = neutral hypers + Σ (multiplicity × dimension) over charged representations.
- Group-theory coefficients Aᴿ, Bᴿ, Cᴿ, defined by tr_R F² = Aᴿ tr F² and tr_R F⁴ = Bᴿ tr F⁴ + Cᴿ (tr F²)², with tr the trace in a fixed reference representation and a normalization λᵢ per factor. Groups without an independent quartic Casimir (SU(2), SU(3), G2, F4, E6, E7, E8) have no Bᴿ term.
- Conditions: (1) H − V + 29T = 273. (2) For each factor with a quartic Casimir, B_adj = Σ_R x_R Bᴿ. (3) a·a = 9 − T. (4) a·bᵢ, bᵢ·bᵢ and bᵢ·bⱼ (i ≠ j) equal the expressions in Aᴿ, Cᴿ and the mixed multiplicities pinned in `TASK.md`. (5) The Gram matrix of (a, b₁, …, b_k) has at most one positive and at most T negative eigenvalues, so it can be realized in signature (1, T).

The coefficients Aᴿ, Bᴿ, Cᴿ are not taken from tables or from memory. The checker derives them exactly by expanding power sums of weights, Σ_w (w·h)², and Σ_w (w·h)⁴, over each representation's weight system as polynomials in a generic Cartan element h. The operator pins the normalization constants λᵢ and the exact form of condition (4) in `TASK.md` from a reference chosen at packet-build time, and the second checker confirms them on hidden positive controls.

Arithmetic reference points: T = 9 with no gauge group and H = 12 satisfies (1) and gives a·a = 0; T = 0 with no gauge group needs H = 273.

Edge cases: SU(2) and SU(3), where no quartic condition applies; half-hypermultiplets in pseudoreal representations (such as the 56 of E7); adjoint hypermultiplets; a spectrum passing (1) but failing (2); one passing (1) to (4) but failing (5); T above 9, where a·a < 0.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Output for a checked spectrum:

```json
{"id": "sg_05", "status": "SOLVED", "H": 12, "V": 0, "T": 9,
 "gravitational": {"lhs": 273, "ok": true},
 "coefficients": {"a.a": "0", "a.b": [], "b.b": []},
 "quartic": [], "gram_inertia": {"positive": 0, "negative": 0, "zero": 1},
 "verdict": "PASSES_NECESSARY_CONDITIONS"}
{"id": "sg_06", "status": "SOLVED", "verdict": "ANOMALOUS",
 "first_failure": {"condition": 2, "factor": 0, "lhs": "16", "rhs": "15"}, "…": "…"}
{"id": "sg_07", "status": "OUT_OF_SCOPE", "witness": {"kind": "half_hyper_in_nonpseudoreal_rep", "factor": 1}}
{"id": "sg_08", "status": "UNKNOWN", "refusal_code": "GROUP_NOT_SUPPORTED"}
```

A `SOLVED` answer is complete when every reported number equals the checker's exact value, the verdict follows from those values, and, for `ANOMALOUS`, `first_failure` names the lowest-numbered failing condition with its exact left and right sides. `OUT_OF_SCOPE` covers half-hypermultiplets in representations that are not pseudoreal, and representations that are not valid highest weights.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the pinned normalizations, the weight-system convention for each group family, and the condition order.
- `examples/`: 10 cases with exact outputs: the two arithmetic reference points, an SU(2) spectrum, an SU(3) spectrum, an SU(4) spectrum where the quartic condition binds, an E7 spectrum with half-hypermultiplets, a spectrum failing only (5), and three malformed or unsupported cases.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 28 spectra, half passing every necessary condition (built by the judge by solving for multiplicities) and half failing exactly one condition, spread across all five.
- **Relabel and gauge controls:** 8 controls: reordering gauge factors; reordering hypermultiplets; replacing a representation by its conjugate (even-power traces are unchanged); an integral change of basis of the tensor lattice, which leaves the Gram matrix invariant.
- **Poisoned-but-schema-valid cases:** 6 cases: a half-hypermultiplet counted as full; an adjoint hypermultiplet omitted from H; an SU(3) case baiting a quartic condition that does not exist; a spectrum that satisfies (1) exactly but fails (3).
- **Exact checker (Rust):** weight systems, power sums over Q, conditions (1) to (4), and inertia through exact LDLᵀ.
- **Independent second checker:** derives Aᴿ, Bᴿ, Cᴿ by a second route, taking exact traces of explicit representation matrices for the fundamental, adjoint and antisymmetric representations of classical groups, and computing the inertia by Sylvester's criterion on leading minors with pivoting. It must agree with the weight route on every coefficient used.
- **Mutation suite:** H off by one neutral hyper, V off by a rank, a Bᴿ with the wrong sign, a verdict inconsistent with the reported numbers, a first failure that is not the lowest-numbered one, a wrong inertia count.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the judge's weight-system implementation packaged as a solver. E passes by construction on supported groups; the challenge measures whether an arm synthesizes the group theory and bookkeeping correctly. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `qwen/qwen3-30b-a3b`. The reference used to pin normalizations is recorded in the judge packet with its bibliographic details.

## 9. Pass Gates and Statistics

- **Capability gate:** 28/28 base and 8/8 controls.
- **Primary metric (pre-registered):** per-case exact-match rate on base cases, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** error rates by condition number, and the half-hypermultiplet error rate.

## 10. Interpretation

- Passing (1) everywhere and failing (2) to (5) means the arm counts well but cannot derive trace coefficients.
- `PASSES_NECESSARY_CONDITIONS` means only that the stated anomaly conditions hold. It does not certify that a consistent quantum theory of gravity with that spectrum exists, nor that it arises from string theory.
- Reproducing known consistent spectra certifies the computation, not any physical claim about string theory.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a `PASSES_NECESSARY_CONDITIONS` verdict; signal 2 is any reported coefficient that differs from its recomputation. Together they catch verdicts asserted without the arithmetic.
- **Kinetic proofreading:** counting, then trace coefficients, then quadratic conditions, then inertia.
- **Thymus:** reject operands that apply a quartic condition to SU(2) or SU(3).

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the weight systems and power sums for each representation.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose spectrum), `I` (integrate weight systems), `R` (residual: the vector of condition left-minus-right values), `D` as each is computed and checked, `M` when a condition fails and the verdict turns `ANOMALOUS`, `T`. Logged measure: the number of conditions evaluated and the first nonzero residual.

Operands expected: (1) trace coefficients from power sums over weights; (2) half-hypermultiplets only in pseudoreal representations; (3) no quartic condition for groups without a quartic Casimir; (4) the signature (1, T) inertia test by exact LDLᵀ.

## 13. Estate Reuse and Prerequisites

- `omega_engine_projects/mssn_sn_symgam/demos/demo_11/` and `research/mssn_sn_tower/demos/demo_11/dossier_2_green_schwarz_anomaly_cancellation/`: the dossier pattern (`input.yaml`, `witness_valid.json`, `witness_near_miss.json`, claim ledger) and the Rust `verify_phi4` route. That dossier is a discrete cochain analogue of the Green–Schwarz mechanism on a triangulated S⁴; it does not compute six-dimensional anomaly polynomials.
- `omega_engine/crates_rs/omega_linear_algebra` (`exact_ldlt.rs`) for inertia.
- No Lie-algebra weight-system module exists in the estate. The weight-system code is shared with C033 and is new Rust work.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize an exact anomaly-condition checker for six-dimensional (1,0) spectra under pinned conventions.
- **Does not support:** the existence of any supergravity theory, any F-theory or heterotic realization, or any swampland claim.
- **Narrowest defensible claim:** "Arm X reproduced the judge's exact anomaly coefficients and verdicts for k of 28 hidden spectra."
- **Next test:** C033, which checks the weight systems this challenge depends on.
