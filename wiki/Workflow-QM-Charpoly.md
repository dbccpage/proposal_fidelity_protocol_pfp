# QM workflow: native characteristic-polynomial certificate

**Plans:** `qm_charpoly_checked_v1` and `qm_charpoly_ungated_v1`.
**DAG nodes:** `EXECUTABLE:qm_charpoly_checked_v1` and `EXECUTABLE:qm_charpoly_ungated_v1`.

This workflow connects a model-generated intermediate calculation to source-bound exact Rust arithmetic. Its certificate concerns the characteristic polynomial of the public Hamiltonian. It does not certify the model's final solution.

## Procedure

1. Verify the unchanged public seed and native source/build custody before any paid request. Derive the public Hamiltonian matrices from the fixed Pauli and basis conventions.
2. Ask the model for five sparse polynomial coefficients of `det(lambda I - H)`, in ascending powers of lambda. Supply the public matrices and schema, without supplying the coefficients.
3. Check the proposed identity with exact rational arithmetic. The checked plan permits one correction using a schema error or one exact counterexample. It proceeds to synthesis only after acceptance.
4. Ask the model to solve all five parts of the unchanged task using its proposed intermediate polynomial. Grade only this final answer afterward.

The ungated control uses the same proposal and synthesis instructions. It receives no checker verdict or correction and proceeds even from a malformed or false candidate. Its checker observations remain in the host record. Identical valid candidates yield identical synthesis requests in both plans.

## What the certificate proves

The registered Hamiltonian is affine in three real parameters and has dimension four. Every characteristic-polynomial coefficient has degree at most four in each parameter. The candidate parser enforces those degree bounds. Exact agreement on the full five-by-five-by-five Cartesian grid therefore establishes the polynomial identity for every real parameter triple, by repeated application of the univariate root bound.

The host binds the certificate to an exact machine-readable **intermediate assertion**. The synthesis response is separate and may contradict or misuse that assertion. Projectors, degeneracies, evolution, entanglement, thermal formulas and whole-answer accuracy remain unverified by this checker.

The implementation uses a small isolated wrapper around source-extracted `pfp_runtime` rational arithmetic. This is not execution of the full PFP host or an EIS/PCIV/OPERADS integration. Native custody failure halts both arms; there is no Python fallback labeled native.

## Resources and failures

Proposal and optional repair each permit 2,400 output tokens; synthesis permits 12,000. A smaller campaign ceiling applies to each call. Checked runs make at most three model calls; ungated runs make two. Every call shares the **USD0.10 whole-run cap**, and unknown charges block subsequent dispatch. Provider enforcement premises remain explicit in the [benchmark protocol](Workflow-QM-Benchmark.md).

Malformed proposals, refusals, unsuccessful repairs, native failures, truncated responses and paid calls without a final answer remain in the results. Only synthesis text can count as a delivered answer. Certificate acceptance does not award rubric points automatically.

## Implementation and evidence

The implementation is published in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58), commit `4cdacabfd7d5a03ab346004559724335906558e2`, under `dag/benchmark/`. It is not yet on main. An isolated committed export with a fresh native build passed 249 tests and 48 subtests. Controls exercise correct and false identities, one-repair admission, identical-context ablations, missing native custody and budget/accounting stops. See `CHARPOLY_WORKFLOWS.md` for build and run commands.

<!-- BEGIN CHARPOLY RESULTS -->
## First measured native-checker comparison

Two separately sampled attempts used the same public seed, DeepSeek V3.2 and AtlasCloud FP8. Each proposal permits 2,400 output tokens and synthesis 12,000. Only the checked arm permits one additional 2,400-token correction, under the same USD0.10 whole-run cap.

| Plan | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Intermediate certified | Outcome |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `qm_charpoly_checked_v1` | 0 | $0.001685 | 2,680 / 2,596 | 70.4 | False | certificate_refused |
| `qm_charpoly_ungated_v1` | 47 | $0.005329 | 2,956 / 12,395 | 313.4 | False | completed |

Only the frozen synthesis answer earns rubric credit. No intermediate certificate automatically earns points, and no proposal, evaluator content or earlier answer supplies grading credit. Full requests, native receipts, billing, final text and criterion evidence remain under `charpoly_pilot_20261110/`.

The checked attempt receives zero delivered-solution points: its initial proposal failed rational-format admission, and its only repair was malformed and length-truncated. The unchecked answer scores 47/100; it stops during the reduced-state calculation and omits the later entanglement and thermal results. Neither initial proposal reached native computation, so these runs demonstrate no live exact-polynomial certificate or final-answer advantage.

A separate post-run diagnostic applied a tested, value-preserving rational normalizer to both initial proposals. Both still failed the monic-leading-coefficient condition under the declared ascending-lambda interpretation. No model was called, and no original run or grade was changed. Normalization alone would not have admitted these proposals. The helper is not a registered workflow.

One attempt per procedure on one problem cannot establish a reliable benefit. Proposal and synthesis sampling can differ independently. If both initial proposals pass, the checked arm uses no repair and both arms apply the same procedure to their respective candidates; a score difference then does not isolate a checker effect. Native acceptance remains an intermediate polynomial guarantee only.
<!-- END CHARPOLY RESULTS -->

<!-- BEGIN HOST CHARPOLY WORKFLOWS -->
## Coverage-first workflows and unexecuted campaign preparation

**Plans:** `coverage_first_direct_v1`, `coverage_first_matrix_v1`, `coverage_first_charpoly_v1`, and `coverage_first_operad_composition_v1`.
**DAG nodes:** `EXECUTABLE:coverage_first_direct_v1`, `EXECUTABLE:coverage_first_matrix_v1`, `EXECUTABLE:coverage_first_charpoly_v1`, and `EXECUTABLE:coverage_first_operad_composition_v1`.

Four matched-resource comparison arms are implemented and verified offline:
1. `coverage_first_direct_v1`: seed-only baseline under coverage-first instruction.
2. `coverage_first_matrix_v1`: public matrix context derived by host from Pauli products.
3. `coverage_first_charpoly_v1`: public matrix plus host-derived, native-replayed characteristic polynomial context with explicitly limited intermediate scope.
4. `coverage_first_operad_composition_v1`: typed bounded composition integrating host characteristic polynomial with Epistemic Immune System (EIS) allosteric Hill consensus gate, Prompt Civilization (PCIV) non-empty task set Pareto selection, and planar Operad sequential associativity verification.

### Offline semantic composition (PFP / EIS / PCIV / OPERADS)
- **PFP Host Carrier**: Derives intermediate characteristic polynomial `det(lambda I - H)` in `Q[lambda, J, Delta, K]` under explicit degree bounds and executes native Rust sidecar verification before emitting full or compact certificates (`final_answer_certified: False`), binding `receipt_sha256` and re-executing native verification on validation (`validate_certified_context(..., reexecute_native=True)`).
- **EIS Allosteric Consensus Gate**: Recomputes three independent evidence-grounded sensors (`sensor_native_receipt` native sidecar re-execution, `sensor_symbolic_identity` independent Laplace determinant from admitted Pauli matrices, and `sensor_structural_constraints` symmetric traceless matrices + monic degree-4 zero-cubic bounds) bound to a common `artifact_polynomial_sha256` under Hill parameters (n=2, K=2, t=1/2), never trusting declared metadata fields.
- **PCIV Task Set Evaluator**: Enforces non-empty 5-part QM task portfolio (`part1_spectrum_degeneracies`, `part2_dynamics_transition_prob`, `part3_reduced_state_entanglement`, `part4_thermal_state_threshold`, `part5_algebraic_consistency_checks`), rejects empty candidate measurements (`MISSING_MEASUREMENTS`), and computes non-dominated Pareto fronts without heuristic scalarization.
- **OPERADS Typed Port Pipeline**: Models composition as morphisms `f: (State) -> Contract` (Host Charpoly), `g: (Contract) -> Audit` (EIS Allosteric Gate), and `h: (Audit) -> Receipt` (PCIV Pareto Selection), formally certifying sequential associativity `(h o_0 g) o_0 f = h o_0 (g o_0 f)` via `TreeCompositionWitness`.

### Offline validation status
- All four workflows execute offline under synthetic provider tapes with strict source-pin enforcement covering both `dag/benchmark/` and the 72-file runtime import closure in `source_custody.py`.
- Exact polynomial equivalence on the 125-point rational grid is verified offline via `qm_host_charpoly.py` using dual Leibniz/Laplace determinant engines and 3D tensor product Lagrange interpolation (`interpolate_trivariate_charpoly` and `interpolate_charpoly_from_grid`), cross-checked against receipt-grounded native sidecar replay.
- Compact serialized context schema `pfp.qm-host-charpoly.compact-certificate.v1` (`COMPACT_CHAR_BUDGET = 1,300` characters) eliminates internal `failure_states` diagnostics and redundant wire metadata while binding `receipt_sha256`, reducing prompt context by over 72% (1,252 characters vs 4,507 original) while delivering standard descending-degree formulas and public matrices.
- The intermediate certificate covers only `det(lambda I - H)`; downstream derivations, projectors, and final answers are explicitly uncertified.

### Campaign preparation status
No paid campaign allowance is currently authorized. These workflows have not been executed with live paid provider dispatch. Finite campaign manifests are prepared via `live_campaign.py prepare` awaiting explicit user authorization. Historical measured benchmark totals remain strictly at 24 runs (settled spend USD 0.055614, 0 held liability).
<!-- END HOST CHARPOLY WORKFLOWS -->

Return to [workflow results](Workflow-Results.md) or [choose a workflow](Workflows.md).
