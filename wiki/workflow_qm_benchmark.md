# Compare workflows on one frozen QM problem

**The first five-plan live pilot is complete, followed by a targeted fixed-panel repair.** This benchmark compares complete answers to the same graduate quantum-mechanics problem by money, tokens, time and independently reviewed accuracy. See the [November 10 pilot results](workflow_qm_pilot_2026_11_10.md) for measured outcomes and failures.

The next implemented mechanism is [exact Hamiltonian checking before synthesis](workflow_qm_hamiltonian.md), compared with ungated decomposition, direct solving and host computation. Its eight-run comparison is graded: the check blocked incorrect representations, but none of the delivered answers completed the task.

The subsequent larger-model and output-allowance comparisons are on that same results page. The [five-section allocation control](workflow_qm_sections.md) scored 26/100, below the longer direct control's 62/100, with higher cost and incompatible formulas between sections. A later [DeepSeek direct control](workflow_qm_hamiltonian.md#exploratory-model-capability-control) scored 83/100; [self-critique](workflow_qm_controls.md#deepseek-direct-versus-self-critique) scored 88/100 at greater resource cost. Both retained mathematical errors.

The [native characteristic-polynomial workflows](workflow_qm_charpoly.md) now connect an exact Rust checker to the capped runner. Their first comparison produced a checked refusal and a truncated unchecked answer. An intermediate certificate never certifies the final solution.

The runnable implementation is published in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58), under `dag/benchmark/`; it is not yet on main. Raw run and evaluation artifacts remain in the working checkout. The source-only PR excludes private evaluator material. The earlier [WF1–WF5 results](workflow_results.md) concern integer addition and are a separate experiment.

## Choose a plan

| Plan ID | Procedure | Maximum model calls | Completion ceilings | Current evidence |
| --- | --- | ---: | --- | --- |
| [`direct`](workflow_qm_controls.md#direct) | Solve once | 1 | Configurable; 4,000 and 16,000 tested | Longer control stopped normally but omitted later parts |
| [`self_critique`](workflow_qm_controls.md#self-critique) | Draft, then audit and revise | 2 | Configurable; 4,000 and 16,000 tested | Later DeepSeek run scored 88/100; errors remain |
| [`rational_blind_panel_v1`](workflow_qm_rational_panels.md#blind-panel) | Solve, then generate challenges without seeing the answer | 2 | 3,000 + 1,500 | One live pilot; artifact validation failed |
| [`rational_visible_panel_v1`](workflow_qm_rational_panels.md#visible-panel) | Solve, then generate challenges while seeing the answer | 2 | 3,000 + 1,500 | One live pilot; artifact validation failed |
| [`rational_fixed_panel_v1`](workflow_qm_rational_panels.md#fixed-panel) | Solve, then use twelve fixed host probes | 1 | 3,000 | One live pilot; artifact validation failed |
| [`rational_fixed_panel_v2`](workflow_qm_rational_panels.md#fixed-panel-repair) | Same fixed panel, repaired output instructions | 1 | 3,000 | Exploratory repair also truncated; invalid JSON |
| [`hamiltonian_checked_v1`](workflow_qm_hamiltonian.md#checked) | Propose matrices, check, optionally correct once, then solve | 3 | 1,200 + optional 1,200 + 4,000 | Three live refusals across two model cohorts |
| [`hamiltonian_ungated_v1`](workflow_qm_hamiltonian.md#ungated) | Propose matrices then solve without enforcement | 2 | 1,200 + 4,000 | Two delivered answers, both incomplete |
| [`hamiltonian_host_matrix_v1`](workflow_qm_hamiltonian.md#host) | Host computes matrices then one solver call | 1 | 4,000 | Correct intermediate representation did not ensure correct final answers |
| [`section_allocated_v1`](workflow_qm_sections.md) | Solve five public parts independently, concatenate raw sections | 5 | 3,200 each; 16,000 total | 26/100; all five sections truncated and mutually inconsistent |
| [`qm_charpoly_checked_v1`](workflow_qm_charpoly.md) | Propose polynomial, check, optionally correct once, then solve | 3 | 2,400 + optional 2,400 + 12,000 | First attempt refused before synthesis |
| [`qm_charpoly_ungated_v1`](workflow_qm_charpoly.md) | Propose polynomial then solve without enforcement | 2 | 2,400 + 12,000 | First synthesis truncated; see graded comparison |

Every plan has one **USD 0.10 whole-run cap** shared by all its calls. These are maximum call counts, not a promise that later calls will fit the remaining budget. The conservative broker may refuse a request before dispatch. Monetary enforcement depends on the provider honoring its recorded tariff, token ceilings and routing restrictions; an external overcharge cannot be reversed by a local ledger.

## The frozen task and separate evaluator

The seed asks for spectrum, dynamics, pure-state entanglement and thermal properties of a two-spin system. Every model call receives the unchanged full seed from `dag/benchmark/seed_prompt.txt` as a separate message. Its SHA-256 commitment is:

```text
9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7
```

The worked answer is kept in separate private storage. Its hash is committed in `dag/benchmark/commitment.json`; its contents and storage path are never workflow inputs or Wiki content. Online checks use only public contracts and candidate artifacts. The trusted evaluator reviews frozen outputs afterward, with no feedback into the workflow.

The fixed 100-point rubric allocates 20 points to spectrum, 20 to dynamics, 25 to pure entanglement, 25 to thermal results and 10 to conventions and checks. Accurate formulas require review of derivations and exceptional parameter cases. Schema acceptance, model agreement and passing numerical probes do not supply that score.

## Run and retain evidence

Use PowerShell at the repository root with the repository virtual environment. The [control](workflow_qm_controls.md) and [panel](workflow_qm_rational_panels.md) pages give manifest preparation commands. `prepare` and `initialize` make no paid requests. Replace model and endpoint placeholders with a currently available concrete pair and freeze the aggregate campaign budget, repetition count and order before dispatch.

```powershell
.venv\Scripts\python.exe -X utf8 dag\benchmark\live_campaign.py initialize --manifest CAMPAIGN_JSON --ledger NEW_CAMPAIGN_SQLITE
.venv\Scripts\python.exe -X utf8 dag\benchmark\live_campaign.py run --ledger NEW_CAMPAIGN_SQLITE --run-id EXACT_RUN_ID_FROM_MANIFEST --output NEW_RUN_DIRECTORY
.venv\Scripts\python.exe -X utf8 dag\benchmark\live_campaign.py status --ledger NEW_CAMPAIGN_SQLITE
```

Only `run` reads `OPENROUTER_API_KEY` from the environment and can incur charges. Each output directory must be new. Execute runs serially in their frozen manifest order. There is no automatic campaign loop, retry or fallback. An uncertain charge keeps its reservation and blocks further dispatch until reconciled. Direct Anthropic billing is not implemented in this runner.

The CLI defaults to a 120-second transport timeout (`--timeout-seconds`). This is not a whole-workflow wall-time ceiling. Record actual elapsed time and the sum of provider-call durations; the panel host has a separate cooperative checking deadline.

Keep `run.json`, `run.sha256`, `ledger.sqlite3` and `calls/`; panel plans also retain `host_checks.json` and, when available, `panel_artifact.json`. The campaign ledger records aggregate admission and settlement. Receipts retain failures, raw replies, request identities, token fields and durations. Missing usage remains unavailable. Local digest checks establish consistency, not provider authentication.

## Interpret results

The first campaign ran one sample of each original plan on the same Qwen/SiliconFlow endpoint, with USD 0.50 aggregate admission and USD 0.007364 recorded spend. Its failed artifacts and truncated responses remain in the results. A separate one-run, USD 0.10-capped exploratory repair tests clearer JSON instructions and response budgeting. The [pilot page](workflow_qm_pilot_2026_11_10.md) reports costs, tokens, timing, post-freeze grades and limitations; `dag/benchmark/results_summary.json` contains the machine-readable comparison. This is an operational pilot, not evidence of a reproducible mechanism advantage.

The pinned validation receipt `dag/benchmark/rational_panel_validation.json` records 119 passing synthetic tests across the checker, runner, accounting and summarizer. An independent review records 80 passing tests in an isolated fabricated-task environment in `dag/benchmark/rational_panel_review_focused_tests_verified.json`; these overlap the larger suite and must not be added as 199 distinct tests. No test count is evidence of improved model performance.

The native-workflow suite passes 249 tests plus 48 subtests, including an isolated export of committed source after a fresh native build. The earlier 190-test section checkpoint and other counts describe historical or overlapping snapshots; do not add them together. The separate unregistered transport-normalization helper has 12 focused tests and does not change the measured v1 workflows.

Report raw outcomes and all failed attempts before averages. Compare equal-money, equal-token and equal-time experiments separately. Repeated samples of this single problem measure within-item behavior; they do not establish general performance on graduate QM problems. Full protocol: `dag/benchmark/EXPERIMENT_PROTOCOL.md`. Accounting and execution details: `dag/benchmark/LIVE_RUNNER.md` and `dag/benchmark/ACCOUNTING.md`.

## Relationship to the workflow DAG

The existing [WF1–WF49 graph](workflow_dag.md) describes workflow families. The research graph `dag/workflows_dag.json` additionally records thirty research ideas and 4,250 bounded compositions from ten research reports. That composition count is a design enumeration, not 4,250 working runners or every possible composition.

The executable QM plans above have their own `CONTROL:` and `EXECUTABLE:` node IDs. They are outside that unimplemented composition grammar. The v2 fixed-panel entry is an implementation repair, not a new research mechanism. The rational plans adapt one portion of R05-I02; they do not establish complete PFP, EIS, PCIV or OPERADS integration.

As each further workflow is implemented, its Wiki entry should be published with its exact status, procedure, source identity, resource envelope, validation, outcomes and limits. The [authoring checklist](workflow_authoring.md#completion-and-wiki-publication) defines that completion step.
