# Check the Hamiltonian before solving

These three implementations address a concrete failure from the [first QM pilot](workflow_qm_pilot_2026_11_10.md): a solver silently changed coefficients or tensor products while constructing the Hamiltonian. They use a small typed matrix artifact before the full prose answer. The [unchanged QM seed](workflow_qm_benchmark.md) and private-evaluator separation still apply.

## What the check establishes

The host computes the coefficient of each of J, Delta and K from exact complex-rational Pauli tensor products in the specified basis. It compares all 48 rational matrix entries. Matching those three matrices establishes the affine Hamiltonian identity for every real parameter triple. This follows from linearity; it is not a finite sampling claim.

The check assumes the public Hamiltonian and basis convention. It does **not** certify eigenvalues, evolution, entanglement, thermal properties, or the final answer. A downstream solver can still misuse a correct matrix. The original private reference answer is not an input; even the expected entries in correction feedback come from public-input arithmetic.

<a id="checked"></a>

## Checked proposal with one correction

**Plan:** `hamiltonian_checked_v1`. **DAG node:** `EXECUTABLE:hamiltonian_checked_v1`.

1. The model proposes the three coefficient matrices in a closed JSON schema.
2. The host checks every entry exactly. A failed artifact gets at most one correction call with bounded public diagnostics.
3. Only an accepted representation proceeds to the full solution. Two failed matrix attempts refuse synthesis, and a matrix alone is never treated as the final answer.

There are two model calls on the ordinary path and three with correction: 1,200 output tokens per matrix attempt and 4,000 for synthesis. All calls share one USD 0.10 ledger. Unknown billing stops the run.

<a id="ungated"></a>

## Decomposition without enforcement

**Plan:** `hamiltonian_ungated_v1`. **DAG node:** `EXECUTABLE:hamiltonian_ungated_v1`.

The model proposes a matrix and then solves. Host check results are retained for analysis but never passed to the solver or used to block it. There is no correction call. This two-call control separates decomposition from enforcement. Wrong or malformed representations remain visible in the evidence.

<a id="host"></a>

## Host computation before one solver call

**Plan:** `hamiltonian_host_matrix_v1`. **DAG node:** `EXECUTABLE:hamiltonian_host_matrix_v1`.

The host computes the matrices directly from the public input, then supplies them to one synthesis call. Since checking already requires that calculation, this control tests whether paid proposal and correction calls add anything useful. It allows 4,000 output tokens and shares the same USD 0.10 run ceiling.

All three implementations use the same synthesis instruction. For an identical valid matrix, their final solver requests are byte-identical; acceptance labels and correction history do not enter that request. Every call also includes the full unchanged seed. These are fixed bounded adaptations of research idea R01-I03, not a complete native implementation of PFP, EIS, PCIV or OPERADS.

## Execution and evidence

Use `dag/benchmark/hamiltonian_campaign_run.py prepare` to freeze the four-arm pilot, including the unchanged direct baseline, and `run` to execute it with the configured OpenRouter credential. Preparation makes no paid request. The prepared design has two runs per arm, a fixed shuffled order, one concrete endpoint, USD 0.10 per run and USD 0.80 total. Existing campaign ledgers cannot be restarted automatically.

The implementation passes 166 focused tests plus 27 subtests. Checks include independent tensor-action calculations, all 48 single-entry mutants, missing factors, wrong tensor products, basis swaps, malformed artifacts, correction/refusal paths, billing stops and request equality across controls. These software checks do not establish model performance.

Raw calls, matrix checks, final answers, billing, token fields, timings, code snapshots and hashes are stored under `dag/benchmark/hamiltonian_pilot_20261110/`. The workflow implementation is available in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58); raw run evidence remains local. All final answers are graded after freezing with the existing 100-point rubric. The direct baseline retains its old instruction; the other three use a compact synthesis instruction. Total call and token allowances differ. Therefore the four-arm comparison is descriptive, while the identical-request controls offer the cleaner test of enforcement and proposal overhead.

<!-- BEGIN MEASURED RESULTS -->
## Measured eight-attempt pilot

All eight runs on `openai/gpt-4o-mini` through the `openai` OpenRouter endpoint are frozen and graded. Total recorded provider cost was **USD 0.007831**, with no unresolved charges. None delivered a complete solution.

| Plan | Scores /100 | Mean recorded cost | Mean input / output tokens | Mean wall seconds | Delivered answers |
| --- | --- | ---: | ---: | ---: | ---: |
| `direct` | 3, 4 | $0.0010370 | 422.0 / 1,622.0 | 26.0 | 2/2 |
| `hamiltonian_checked_v1` | 0, 0 | $0.0007030 | 3,065.0 / 539.5 | 8.3 | 0/2 |
| `hamiltonian_ungated_v1` | 4, 4 | $0.0012675 | 2,013.0 / 1,752.0 | 21.8 | 2/2 |
| `hamiltonian_host_matrix_v1` | 4, 4 | $0.0009080 | 778.0 / 1,317.5 | 15.9 | 2/2 |

Both checked attempts failed the exact matrix check, failed their one correction and refused synthesis. Their zero scores mean no delivered solution; they are not wrong mathematical assertions. Both ungated attempts continued from incorrect representations. The host-derived control supplied a correct representation, but the solver still produced incorrect or unfinished mathematics. All six delivered answers stopped normally, so their omissions cannot be blamed on truncation.

The checker demonstrated its narrow admission property in these runs. It did **not** establish a final-answer accuracy benefit. A correct intermediate artifact does not ensure that a model uses it correctly. Two samples on one problem, unequal total resources and the direct arm's different instruction do not support a general ranking.

The existing rubric was retained unchanged and applied to final answer text after freezing. Detailed criterion evidence and hash-bound grades are in `hamiltonian_pilot_20261110/grades.json`, `criterion_evidence.json` and `evaluation_validation.json`. This is a documented model-assisted mathematical review, not a formal or independent human certification. The private reference answer was not accessed. A separate larger-model comparison uses unchanged workflow prompts; it is exploratory and is retained separately from these eight runs.

## Exploratory larger-model comparison

Three further frozen attempts used `qwen/qwen3-235b-a22b-2507` through `deepinfra/fp8`, with unchanged workflow prompts and 4,000-token final-output ceilings. Total settled cost was **USD 0.005117**.

| Plan | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| `hamiltonian_checked_v1` | 0 | $0.000606 | 3,255 / 568 | 15.8 | Refused representation |
| `hamiltonian_host_matrix_v1` | 16 | $0.002272 | 797 / 4,000 | 273.2 | Length-truncated |
| `direct` | 10 | $0.002239 | 432 / 4,000 | 227.9 | Length-truncated |

The host-assisted answer preserved the correct Hamiltonian and eigenvalues, while the direct answer introduced an incorrect coupling. Both exhausted their output budget during the spectrum/projector section. The 16-versus-10 partial score difference is one observation, not a reproducible workflow advantage; neither completed the task.

Across both Hamiltonian experiments, three checked attempts refused synthesis after their one correction remained wrong. This confirms the observed gate behavior, not full-solution performance. The longer model responses also show that the 120-second transport setting is a socket timeout, not a total request deadline.

The harness accepts `live_campaign.py prepare --max-output-tokens N`; the USD0.10 ledger remains unchanged. Fixed adaptation-stage ceilings remain in force even when the campaign ceiling is higher. The configurable allowance passed the expanded 171-test suite plus 27 subtests. The original 4,000-token default is not a requirement of the problem.

## Output-allowance control

The direct workflow, exact public seed, Qwen235B model and DeepInfra endpoint are unchanged. The new run raises the requested output ceiling from 4,000 to 16,000 tokens. Both runs remain under the USD0.10 whole-run cap.

| Requested output ceiling | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- |
| 4,000 | 10 | $0.002239 | 432 / 4,000 | 227.9 | {'length': 1} |
| 16,000 | 62 | $0.006222 | 432 / 11,241 | 601.2 | {'stop': 1} |

The larger response earns 62/100 for substantial work on parts 1–3, compared with 10/100 in the earlier short attempt. It voluntarily requests another message before the thermal section and numerical example. It uses 11,241 tokens and stops normally, so this omission is not a provider-reported output cutoff. The final answer also retains parameter-branch defects.

This is one exploratory sample at each allowance, not a paired random-seed experiment or an established workflow advantage. The larger ceiling changes available resources; it is not evidence about PFP/EIS/PCIV/OPERADS efficacy. Grading uses the unchanged rubric after freezing, with no evaluator feedback. Criterion evidence and grade bindings are under `length_control_20261110/`. Combined summaries keep different control output allowances in separate groups. The later [five-part allocation control](workflow_qm_sections.md) scored 26/100 at greater recorded cost.

## Exploratory model capability control

The direct prompt and 16,000-token ceiling were retained while changing to DeepSeek V3.2 through AtlasCloud FP8. This tests another model/endpoint, not a new workflow. Availability and tariffs were checked against [OpenRouter's model listing](https://openrouter.ai/deepseek/deepseek-v3.2) and the frozen live endpoint metadata before dispatch.

| Model / endpoint | Score /100 | Recorded cost | Input / output tokens | Wall seconds |
| --- | ---: | ---: | ---: | ---: |
| Qwen235B / DeepInfra FP8 | 62 | $0.006222 | 432 / 11,241 | 601.2 |
| DeepSeek V3.2 / AtlasCloud FP8 | 83 | $0.004211 | 403 / 10,805 | 270.0 |

The DeepSeek answer supplies the thermal calculation and numerical example, but retains an incorrect CHSH maximum and exceptional-case gaps. Neither answer is a complete correct solution. One sample cannot establish a model ranking; the changed endpoint and model defaults are part of this exploratory comparison.

An earlier infrastructure attempt made zero model dispatches and cost zero: its preflight provider instance retained an unused prepared request, so the guard refused reuse. That failure remains in `model_control_20261110/` with zero delivered-solution points and no assessed model mathematics. The corrected attempt used a fresh provider instance in a separately frozen campaign. Full accounting totals include both attempts; the table above compares delivered model answers only.
<!-- END MEASURED RESULTS -->

Implementation: `hamiltonian_artifact.py`, `hamiltonian_workflows.py` and `reference_runner.py` under `dag/benchmark/`. Scope and protocol: `HAMILTONIAN_WORKFLOWS.md`. Return to the [benchmark overview](workflow_qm_benchmark.md).

## Native exact-arithmetic prototype

A separate local checker now reuses the production rational characteristic-polynomial methods in a small, source-bound Rust wrapper. It accepts an explicit rational matrix affine in all three parameters, dimension at most four, and a degree-bounded candidate polynomial. Exact agreement on the complete Cartesian grid of `(n+1)^3` points proves the polynomial identity for every real parameter triple: each coefficient difference has degree at most `n` in each variable, so successive univariate root bounds force it to vanish.

Fifteen public controls passed, including independent determinant expansions and mutations that defeat incomplete sampling. A parent check also passed a dense noncommuting three-by-three case and rejected an altered coefficient. This validates a bounded native arithmetic connection; the public-prose interpretation, projectors, dynamics and full PFP/EIS/PCIV/OPERADS integration remain unresolved. The checker has not been connected to a paid workflow or used to grade these model answers. Its local implementation and evidence are `dag/benchmark/native_sidecar.py` and `native_sidecar_host/`; they are not included in draft PR #58.
