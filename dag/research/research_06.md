# Research 06: bounded adaptive compute

Status: **proposed_not_evaluated**. Baseline: `8050c66900899771766f33e8f5fdd200b7dd9120` plus the in-progress audit. The machine-readable specification is [research_06.json](research_06.json). No paid calls, seed solving, answer-key access, private-storage access, or credential access occurred.

The proposals adapt established methods. [FrugalGPT](https://arxiv.org/abs/2305.05176) motivates a fixed model cascade; its benchmark results do not establish the accuracy of these gates or models. [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html) supplies the risk–coverage framing for abstention; the proposed host rules are neither its trained selection network nor a calibration guarantee. [OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting) documents reconciliation fields, which do not themselves enforce an advance spend ceiling.

Every future model call must receive the original UTF-8 seed unchanged as its own message. Hash the seed and actual request, verify the embedded seed bytes, and keep instructions/artifacts separate. Public fixed predicates may route a run; private scores and key-derived diagnostics may not. Freeze all candidate bytes before separate trusted evaluation. No confidence, cost, model tier, or predicate agreement establishes general mathematical correctness.

| Proposal | Mechanism | Maximum calls / output tokens | Conditional full-path reservation |
| --- | --- | --- | --- |
| R06-I01 | Stop after scoped public-predicate closure; permit one repairable-residual continuation | 2 / 2,600 + 1,800 | USD 0.047 |
| R06-I02 | Cheap draft; one independent replacement from a registered escalation endpoint | 2 / 2,000 + 2,600 | USD 0.0905 |
| R06-I03 | One structured draft; publish supported claim blocks with explicit unresolved slots | 1 / 4,500 | USD 0.0415 |

These figures are conditional admission examples, not live model price quotes. They include a USD 0.01 non-dispatchable margin and assume zero additional fees; unknown fees cause refusal. JSON specifies full input envelopes, per-endpoint rate ceilings, typed inputs/outputs, instructions, dependencies, falsifiers, ablations, and risks.

**R06-I01: predicate-scoped early exit.** Freeze a finite public-check registry and repair-class allowlist. The host may stop when the registry closes, continue once for an allowed residual, or terminate unresolved. Closure is labeled only for those predicates. Compare with always taking two calls and with one direct call using the combined allowance. The hypothesis requires lower mean cost and final score within a preregistered 2/100 noninferiority margin; inconclusive evidence supports no advantage claim. An inadequate checker can stop an incorrect answer early.

**R06-I02: independent escalation.** Pre-register both endpoints and the public residual classes that trigger the second call. The escalation endpoint receives the unchanged seed, fixed slot inventory, and allowlisted residual codes, without the cheap answer. It returns a full replacement; no unverified merge or private-score selection occurs. Compare cheap-only, always-high, same-model continuation, and draft-visible escalation arms. With escalation indicator e, total cost is C_L + e C_H; this gives no correctness ordering. Require measured savings and the registered score margin. Frequent escalation may make the initial cheap call pure overhead.

**R06-I03: selective publication.** Keep every requested slot. After one call, publish passing claim blocks with their exact predicate scope; mark unsupported slots and their dependent conclusions unresolved. Preserve the raw draft and score it alongside the selective rendering only after freezing. Measure coverage, independently adjudicated error among published parts, and the full rubric score together. With g indicating publication, coverage = sum(g)/n and selective error = sum(g × loss)/sum(g); zero publications makes the latter undefined. The proposed improvement fails if coverage falls below 80% of raw attempted-slot coverage or error does not fall. Withholding difficult content never counts as full completion.

WF9 supplies bounded repair and typed residuals; WF22 supplies preregistered arms; WF33 preserves one original fuel budget; WF40 makes exhaustion terminal. The new contribution is the proposed coupling of those boundaries to explicit routing and coverage measurements. These are adaptations, not newly proved workflow theorems.

The benchmark ledger is implemented and reported locally tested, while live adapters remain unadmitted. Its reservation implication depends on an honest complete quote and provider-enforced bounds. The inspected legacy OpenRouter seat gateway uses message byte lengths as an input bound and can reserve an output allowance below the transport maximum; neither behavior is accepted as a hard benchmark cap. The duplicate raw OpenRouter sender is retired. The Anthropic wrapper delegates enforcement to Rust; this research did not audit that enforcement. No adapter was executed.

For every complete path, reserve sum(I_s × p_in_s + O_s × p_out_s + F_s) + R ≤ USD 0.10 under one run identity. Count all billable reasoning, framing, caches, fixed fees, and metered host/evaluator charges as applicable. Unknown usage retains the reservation and stops the run. No automatic retries, fallback, fresh-wallet restart, or assumed-free cancellation is allowed. A byte estimate cannot guarantee an external billing cap.

Recommend **BoundedContinuationPermitV1**: a host-owned receipt binding seed, parent, policy, predicate scope, settled accounting, next-call quote, and remaining call slots. It authorizes at most one reserved successor and refuses uncertainty, stale parents, or exhausted fuel. Implement and exercise synthetic receipt controls before considering a live pilot. It conveys execution authority only, never correctness.

Future comparisons must retain failures and abstentions, show raw scores and costs before averages, and separate equal-money, equal-token, and equal-time comparisons. Repeated samples on this one seed support only this item and settings. There are no measured outcomes in this report.

