# Allocate output across the five requested parts

`section_allocated_v1` is implemented and tested offline. Its first live run is frozen and independently graded below. It addresses an observed failure: a long direct response stopped after part three and promised a later message, leaving requested work undelivered.

The workflow sends the unchanged complete public QM seed to five isolated solver calls. Each call handles one numbered part and receives at most 3,200 output tokens. Calls run serially and share one USD0.10 ledger. Their combined output allowance is 16,000 tokens; repeated input, provider time and money are measured separately. This is not an equal-input, equal-cost or equal-time comparison with one direct call.

| Call | Assigned public request | Maximum output |
| --- | --- | ---: |
| 1 | Spectrum, projectors and degeneracies | 3,200 tokens |
| 2 | Dynamics, transition probability and times | 3,200 tokens |
| 3 | Pure-state entanglement and CHSH | 3,200 tokens |
| 4 | Gibbs state, partial transpose and thermal entanglement | 3,200 tokens |
| 5 | Independent consistency checks and numerical example | 3,200 tokens |

Each solver derives its own prerequisites. It receives no other section, checker feedback, grade or private reference. The host concatenates raw sections in task order without a model merge. Hashes and character spans identify every included response. A later failure preserves earlier sections and marks missing slots. No nonempty response means no delivered answer; placeholders do not become a solution.

This is an output-allocation control, not a mathematical certificate or a native PFP/EIS/PCIV/OPERADS integration. Independently written sections can conflict. Five present sections may still omit requested results. The unchanged rubric evaluates the assembled final text only after freezing; section presence earns no correctness credit.

## Run and inspect

The first finite manifest is `dag/benchmark/section_control_20261110/manifest.json`. It freezes one Qwen235B/DeepInfra attempt, the seed, compiled plan, source hashes and USD0.10 campaign ceiling. Implementation is available in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58); raw experimental evidence remains in the working checkout. Neither is yet on main.

To prepare another campaign, choose a currently available concrete model and endpoint:

```powershell
.venv\Scripts\python.exe -X utf8 dag\benchmark\live_campaign.py prepare --campaign-id UNIQUE_ID --model MODEL_ID --endpoint ENDPOINT_SLUG --plans section_allocated_v1 --repetitions 1 --cap-microusd 100000 --order-seed 20261110 --max-output-tokens 16000 --output NEW_MANIFEST.json
```

Preparation does not make provider requests. Use the [benchmark execution commands](Workflow-QM-Benchmark.md#run-and-retain-evidence) to initialize and run the exact manifest once. Never restart a live request merely because it is slow. Inspect `run.json`, request/response receipts, `host_checks.json` and both ledgers. Unknown charges retain their reservation and stop dispatch.

The expanded benchmark suite passes **190 tests plus 27 subtests**, including five end-to-end allocation controls and thirteen focused specification/assembly controls. These demonstrate orchestration behavior on synthetic outputs, not model accuracy. Live measurements are recorded below; software tests do not establish a performance advantage.

Implementation: `section_workflows.py` and `reference_runner.py` under `dag/benchmark/`. DAG node: `CONTROL:section_allocated_v1`. Compare the [direct output-allowance experiment](Workflow-QM-Hamiltonian.md#output-allowance-control), then return to the [workflow overview](Workflow-QM-Benchmark.md).

<!-- BEGIN SECTION RESULTS -->
## Measured comparison

Both attempts use the same public seed, Qwen235B model and DeepInfra endpoint. The direct run permits 16,000 output tokens in one call; allocation reserves 3,200 for each of five isolated calls. Repeated input, actual output, time and money differ.

| Plan | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Truncated calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| `direct` | 62 | $0.006222 | 432 / 11,241 | 601.2 | 0 |
| `section_allocated_v1` | 26 | $0.009065 | 2,904 / 16,000 | 445.5 | 5 |

One sample per procedure is exploratory evidence on this item. The final assembled answer receives the unchanged post-freeze rubric; headings, section presence and independent contexts certify no mathematics. Failures and truncated sections remain in the results. Detailed judgments, exact evidence and hash bindings are under `section_control_20261110/`. No evaluator or reference content was sent to any solver call.

This allocation attempt scored 26/100 versus 62/100 for the longer direct answer and cost more. All five calls reached their output ceiling. Independent sections used incompatible Hamiltonians and formulas; assigning a part did not ensure that its requested results were delivered. This observation does not support adopting the allocation control as an improvement.
<!-- END SECTION RESULTS -->
