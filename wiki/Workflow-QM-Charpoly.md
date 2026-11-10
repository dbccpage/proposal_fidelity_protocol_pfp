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

Return to [workflow results](Workflow-Results.md) or [choose a workflow](Workflows.md).
