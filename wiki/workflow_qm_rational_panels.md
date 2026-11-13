# QM rational counterexample panels

**Status: all three v1 plans were sampled live and failed their artifact contracts; a targeted v2 repair is implemented.** These plans attempt to add exact rational checks to a complete QM answer. See the [pilot results](workflow_qm_pilot_2026_11_10.md). They adapt the rational-substitution part of research idea R05-I02 and share the [frozen benchmark and accounting rules](workflow_qm_benchmark.md).

## Shared procedure and mathematical scope

1. A solver receives the complete unchanged seed and public contract. It returns strict JSON containing a complete prose solution and optional typed rational equalities, with explicit unsupported records for mathematics outside the grammar.
2. A model challenger or fixed host panel supplies rational assignments, without expected answers or executable code.
3. The host evaluates candidate equalities with exact rational arithmetic and records witnesses, undefined points and unresolved obligations.
4. The original solver answer is retained for post-freeze grading. The panel never replaces or repairs it.

The public variables are `J`, `Delta`, `K`, `t` and `beta`; probes are restricted to `t >= 0` and `beta >= 0`. This is the checker domain, not a restriction on the complete task. Expressions support rational constants, arithmetic and integer powers zero through eight. Trigonometric, complex, matrix, exponential and limit expressions are outside this checker.

An in-domain point where the declared guards hold and the two defined sides differ refutes that encoded universal equality. A false guard makes a probe inapplicable. Undefined guards remain unknown; undefined conclusions are recorded separately. A finite set of passing points never proves a universal equality. The host cannot establish that an encoded equation accurately represents the prose or the QM question: semantic alignment and all five task obligations remain uncertified.

<a id="blind-panel"></a>

## Blind panel

**Plan:** `rational_blind_panel_v1`. **DAG node:** `EXECUTABLE:rational_blind_panel_v1`.

After the solver reply is frozen, the challenger receives only the exact seed and public contract. Its request does not depend on the solver artifact. It proposes up to twelve rational assignments aimed at the public task obligations. The host applies them to the candidate's declared claims.

Use this to study challenges generated without access to the candidate. There are at most two serial model calls: 3,000 completion tokens for the solver and 1,500 for the challenger. Request separation does not imply independent model errors or provider-side isolation.

<a id="visible-panel"></a>

## Candidate-visible panel

**Plan:** `rational_visible_panel_v1`. **DAG node:** `EXECUTABLE:rational_visible_panel_v1`.

The procedure and ceilings match the blind panel, except the challenger also sees the complete frozen solver artifact. This can help it target the proposed equalities but can also expose it to the solver's mistakes. The comparison changes candidate visibility, not the host acceptance semantics. The challenger still supplies tests, not a replacement answer or correctness verdict.

<a id="fixed-panel"></a>

## Fixed panel

**Plan:** `rational_fixed_panel_v1`. **DAG node:** `EXECUTABLE:rational_fixed_panel_v1`.

One solver call has a 3,000-token completion ceiling. The host then uses twelve predetermined rational probes, with no model challenger. This is a cheaper mechanism ablation. It is not an equal-token comparison with the two-call plans, and the fixed probes need not expose every false claim.

<a id="fixed-panel-repair"></a>

## Fixed-panel contract repair

**Plan:** `rational_fixed_panel_v2`. **DAG node:** `EXECUTABLE:rational_fixed_panel_v2`.

The first live v1 outputs exposed a prompt ambiguity: models nested artifacts under `candidate_grammar` or `panel_grammar`, while the checker requires the fields directly at the root. Long answers also exhausted their token ceilings before closing JSON. V2 gives the five exact top-level candidate fields, prohibits wrapper objects, requests compact plain-text mathematics with about 2,000 tokens allocated to the answer, and limits optional claim records to five. It preserves the original seed, 3,000-token call ceiling, exact checker, twelve fixed probes and USD 0.10 run cap.

This is one repair of the existing fixed-panel recipe, not another mathematical idea. Its first live response still exhausted 3,000 tokens and failed JSON validation; the repair did not solve the operational problem. The run is exploratory: it changes both wording and response allocation after observing v1 failures. No answer-key content or grading corrections enter the instruction. Contract acceptance still does not establish correctness, and this recipe still cannot repair the solver's answer.

## Prepare the three-arm comparison

From the repository root in PowerShell:

```powershell
.venv\Scripts\python.exe -X utf8 dag\benchmark\live_campaign.py prepare --campaign-id qm-rational-panel-001 --model AUTHOR/MODEL --endpoint PROVIDER/ENDPOINT --plans rational_blind_panel_v1 rational_visible_panel_v1 rational_fixed_panel_v1 --repetitions 1 --cap-microusd 300000 --order-seed 70719 --output dag\benchmark\qm_panel_campaign.json
```

This prepares three runs with a USD 0.30 aggregate ceiling and USD 0.10 per run. It does not initialize or execute a campaign. The model and endpoint are placeholders. Follow the [shared execution steps](workflow_qm_benchmark.md#run-and-retain-evidence) only after freezing the actual campaign settings. Implementation is available in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58); raw receipts remain in the working checkout.

## Artifacts, limits and failures

Keep the solver and challenger request/response records, `run.json`, its digest, the run ledger, and `host_checks.json`. Retain `panel_artifact.json` when available, including the fixed panel. Host evidence binds the seed, contract, candidate, panel and implementation hashes, along with resource use and unresolved obligations. Invalid candidate JSON is preserved raw with an artifact error; it is not silently repaired.

The host limits artifacts to 24 claims, 12 challenges and eight guards per claim. Expression bounds include 128 nodes, depth 16, 128-bit rational inputs, 4,096-bit retained intermediates and 200,000 host operations. Its ten-second cooperative deadline is not OS-level isolation. Resource exhaustion produces unknown evidence. If a call is blocked or a charge is uncertain, retain missing evidence as missing and stop; there are no retries or repair calls in these plans.

The historical shared validation receipt records 119 passing tests, including blind-request invariance, visible-artifact inclusion, exact false-equality witnesses, undefined expressions, malformed artifacts, preservation and accounting. The independent review's 80 passing tests use a fabricated task and overlap that suite. The repaired runner passes 121 tests, including the v2 execution contract and explicit truncation reporting. These checks do not establish checker completeness, native PFP/EIS/PCIV/OPERADS integration, or better QM answers. Consult the live pilot page for measured outcomes rather than inferring performance from tests.

Implementation: `dag/benchmark/rational_workflows.py`, `rational_panel.py` and `reference_runner.py`. Detailed contract and limits: `dag/benchmark/RATIONAL_PANEL.md`. Validation and independent review: `dag/benchmark/rational_panel_validation.json` and `rational_panel_review.json`.

**Next:** compare frozen outputs using the [benchmark protocol](workflow_qm_benchmark.md#interpret-results).
