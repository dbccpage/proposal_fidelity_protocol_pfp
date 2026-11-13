# QM controls: direct answer and self-critique

**Status: implemented and measured in the initial Qwen pilot and a later DeepSeek comparison.** The initial Qwen calls hit their output limits; the later DeepSeek calls stopped normally. See the comparison below and the [initial results](workflow_qm_pilot_2026_11_10.md).

Both use `workflows/wf52_finite_qm_benchmark/reference_runner.py` and retain the exact seed in every call. They have no tools, retrieval, private-answer input or automatic correctness judge. Implementation identity and campaign bindings are retained in the run evidence. The implementation is available in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58), not yet on main; raw run evidence remains in the working checkout.

<a id="direct"></a>

## Direct answer

**Plan:** `direct`. **DAG node:** `CONTROL:direct`.

Use this as the same-model baseline. One solver receives the unchanged task and instructions to solve every part, state assumptions and exceptional cases, and provide a complete derivation. The broker freezes that reply as the final answer for later trusted grading.

There is at most one model call, with a default 4,000-token completion ceiling and a USD 0.10 run cap. The campaign preparation flag `--max-output-tokens N` can set a different allowance without increasing the monetary cap. Current endpoint metadata and conservative cost admission still apply. A completed transport receipt means a response was retained with accounting; it does not mean the mathematics passed.

<a id="self-critique"></a>

## Draft, then self-critique

**Plan:** `self_critique`. **DAG node:** `CONTROL:self_critique`.

1. A solver drafts a complete solution to the unchanged task.
2. A second call receives the same task and the untrusted draft. It audits unsupported steps and missing cases, then returns a complete revised solution.
3. The broker freezes the final available answer and records whether both stages completed. Trusted grading happens afterward.

The normal path has two serial calls, each with a 4,000-token completion ceiling, sharing USD 0.10. The second stage may be blocked by budget or accounting failure; retain that outcome. The draft and critique may share errors. Critique is not an independent mathematical certificate, and no host checker requires the revision to improve the draft.

## Prepare the two-arm comparison

From the repository root in PowerShell:

```powershell
.venv\Scripts\python.exe -X utf8 workflows\wf52_finite_qm_benchmark\live_campaign.py prepare --campaign-id qm-controls-001 --model AUTHOR/MODEL --endpoint PROVIDER/ENDPOINT --plans direct self_critique --repetitions 1 --cap-microusd 200000 --order-seed 70719 --output workflows\wf52_finite_qm_benchmark\qm_controls_campaign.json
```

This prepares two runs in reproducibly shuffled order with a USD 0.20 aggregate ceiling. It makes no provider request and is an example configuration, not an executed campaign. Use a fresh output path; replace the model and endpoint placeholders before initialization. Follow the [shared execution steps](workflow_qm_benchmark.md#run-and-retain-evidence).

These defaults compare one versus two calls and different total token allowances. They do not isolate the value of self-critique at equal tokens. Freeze a separate matched-resource comparison before making that claim.

## Evidence and failure handling

The 119-test checkpoint in `workflows/wf52_finite_qm_benchmark/rational_panel_validation.json` includes `test_reference_runner.py`, `test_live_admission.py`, `test_budget_ledger.py` and `test_summarize_runs.py`. It covers synthetic dispatch, preservation, accounting and result handling. It is not a live provider test.

Keep both draft and final response records for self-critique. Treat a refused request as a refusal, an incomplete account as unknown cost, and a truncated answer as an attempted outcome. Do not restart with a fresh ledger to erase an earlier charge. Review accuracy only after freezing the answer. The first direct run used 4,432 total tokens, USD 0.001239 and 83.5 seconds; self-critique used 12,882 total tokens, USD 0.002840 and 176.6 seconds. The direct answer and both self-critique responses were truncated. These single observations do not establish a general accuracy advantage.

**Next:** [Compare rational counterexample panels](workflow_qm_rational_panels.md).

The [later direct comparisons](workflow_qm_hamiltonian.md#output-allowance-control) include a 16,000-token Qwen control scoring 62/100 and a DeepSeek/AtlasCloud control scoring 83/100. Both stopped normally and retained mathematical omissions or errors. The unchanged self-critique plan has now completed one DeepSeek attempt, with 16,000 tokens per call and a shared USD0.10 cap; its graded comparison follows. Two calls permit more total output than the one-call baseline, so actual resource costs must be compared explicitly.

<!-- BEGIN CRITIQUE RESULTS -->
## DeepSeek direct versus self-critique

Both runs use the identical public seed, DeepSeek V3.2 and AtlasCloud FP8, with a 16,000-token ceiling per call and a USD0.10 whole-run cap. Self-critique generates its own new draft and revises that draft; it does not revise the separately scored direct answer. The private answer, grades and evaluator derivations are absent from both requests.

| Plan | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Finish reasons |
| --- | ---: | ---: | ---: | ---: | --- |
| `direct` | 83 | $0.004211 | 403 / 10,805 | 270.0 | {'stop': 1} |
| `self_critique` | 88 | $0.007756 | 9,594 / 13,844 | 370.3 | {'stop': 2} |

Only the frozen final revised answer earns rubric credit. The unchanged 25-criterion rubric and exact supporting evidence are retained under `deepseek_critique_20261110/`. Grading is model-assisted mathematical review, not human or formal certification. Draft quality has not been independently scored in this comparison.

The revised answer scores 88/100 versus 83/100 for the separate direct run. It states a correct general CHSH maximum but contradicts it in its correlation-matrix derivation; an equality-case entanglement time is also wrong. Other special cases remain incomplete. Neither answer is fully correct. Self-critique costs about 84% more money, uses 109% more total tokens and takes 37% longer in these two observations.

One attempt per procedure cannot establish a reproducible advantage. Self-critique permits two calls and more total output; this is not a matched-resource ablation. It tests a generic revision procedure, not implemented PFP/EIS/PCIV/OPERADS integration. Compare correctness and actual money, tokens and time together.
<!-- END CRITIQUE RESULTS -->
