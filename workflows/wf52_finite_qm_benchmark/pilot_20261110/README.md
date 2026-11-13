# First live QM pilot

This is a five-run operational pilot, one sample of each existing executable
plan, on the unchanged committed seed. It is not a statistically powered
comparison or an equal-token experiment. The existing control plans allow
4,000 output tokens per call; rational plans allow 3,000 for the solver and
1,500 for the challenger. These recipe differences remain visible in results.

The frozen manifest is `manifest.json` (SHA-256
`9744a0f0b135894ecba5d90eaeb1125f35fc7b901d3921a5f7eb5720eec2f4a4`).
It specifies Qwen3 30B A3B Instruct 2507 through SiliconFlow on OpenRouter,
five runs in a fixed shuffled order, USD 0.10 per run and USD 0.50 total.
Model sampling settings use endpoint defaults, as recorded in the wire request.
No paid retries, endpoint fallback, tools, retrieval or evaluator feedback are
permitted. An ambiguous charge stops the campaign. Each response and the final
answer are frozen before mathematical grading.

The inherited 100-point rubric is spectrum 20, dynamics 20, pure entanglement
25, thermal entanglement 25, and checks/conventions 10. Mathematical review
must distinguish wrong claims, missing derivations and omitted boundary cases.
The private reference answer is not read by this runner or supplied to models.

Success for this pilot means obtaining honest measurements and identifying
which mechanism to change next. Schema errors, truncations, checker refusals
and unsuccessful runs remain in the report. Passing a rational check is not
an accuracy score. The three panel recipes preserve the solver answer; their
checks can detect defects but cannot repair the answer in this version.

Artifacts: `preflight.json`, `campaign.sqlite3`, `runs/*/run.json` with adjacent
hashes and call evidence, `ungraded_results.json`, and `campaign_status.json`.
Post-freeze grades and the graded comparison are added separately.
