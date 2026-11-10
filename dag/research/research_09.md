# Research 09 — Allocation, stopping, and time budgets

Status: proposed, not evaluated. No paid model calls were made. The seed and private answer-key material were not read.

These three executable workflow specifications combine PFP public checking, EIS fixture-bound detectors, PCIV protected wrapper lineage, and OPERADS typed composition. They repeat one frozen graduate-QM input; they support no cross-problem claim. New orchestration adapters are required.

## Evidence and boundaries

- [Howard, Ramdas, McAuliffe and Sekhon, Time-uniform, nonparametric, nonasymptotic confidence sequences (Annals of Statistics, 2021)](https://arxiv.org/abs/1810.08240): Develops time-uniform inference under stated assumptions. Motivates distinguishing a preregistered fixed sample size from optional stopping; this proposal uses fixed campaign sizes and no score-dependent continuation. An ordinary fixed-sample confidence interval is not made anytime-valid by calling a workflow sequential.
- [El-Yaniv and Wiener, On the Foundations of Noise-free Selective Classification (JMLR, 2010)](https://jmlr.csail.mit.edu/papers/v11/el-yaniv10a.html): Formalizes selective classification and the risk-coverage tradeoff. Motivates reporting coverage alongside conditional error. Its noise-free classification guarantees do not transfer automatically to mathematical derivation, proxy detectors, or this single seed.
- [OpenRouter official provider routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection): Documents endpoint pinning, fallback controls, parameter requirements, and max_price filtering. Price ceilings filter providers; latency preferences are not deadline guarantees and neither mechanism substitutes for the aggregate run ledger.
- [OpenRouter official usage accounting documentation](https://openrouter.ai/docs/cookbook/administration/usage-accounting): Documents returned native-token counts, charged cost, and available reasoning/cache detail. Use returned accounting fields as observations and retain unavailable values explicitly. Admission quotes and output limits remain separate from actual usage.

- `dag/FOUNDATIONS.md:5-33,39-41`: Separates native finite mechanisms from semantic adequacy and identifies no complete verified checker for the frozen graduate-QM seed.
- `dag/benchmark/EXPERIMENT_PROTOCOL.md:5-19`: Requires unchanged seed bytes, isolated after-freeze grading, randomized repeated samples, failures in the denominator, distinct money/token/time comparisons, and an aggregate campaign budget.
- `dag/benchmark/ACCOUNTING.md:3-13`: USD 0.10 applies across a whole workflow; honest input/tariff bounds and provider-enforced ceilings are prerequisites; actual usage and both time metrics are mandatory.
- `dag/benchmark/budget_ledger.py:22-34,68-117`: Quotes are rounded upward in integer microusd, run/call identities prevent reset or redispatch, outstanding calls hold reservations, and uncertainty or observed overruns block the run.
- `pfp/use_cases/pfp_proposal.py:35-42,118-135`: Host-bounded feedback is distinct from raw judge diagnostics; missing or failing checkers and disagreement have explicit outcomes. Typed acceptance depends on the injected checker.
- `eis/domain/thymus.py:1-16`: Runs the actual bound detector against known-clean fixtures and explicitly limits a passing result to that finite panel.
- `eis/domain/danger_gate.py:3-20,110-117`: Immune suppression needs two named signals, while a host refusal remains independently enforceable. Provenance assertions do not establish population statistical independence.
- `pciv/use_cases/genealogy.py:1-6,21-35`: Lineage distinguishes direct mutation, repair, retry, and precedent; requires witnessed edges and an acyclic inheritance graph.
- `pciv/use_cases/fitness.py:45-82,181-187,280-296`: Preserves explicit failure/infrastructure outcomes and assigned-unit completion denominators; comparative claims require a holdout indicator and multiplicity declaration, not merely a good-looking fitness number.
- `operads/domain/operad/planar.py:34-60,83-94`: Ordered colour-compatible substitution rejects ill-typed insertion. Its associativity receipt is signature-level and does not certify operation bodies, scheduler behavior, or mathematical answers.

## Shared execution and comparison contract

**formula.** For every run reserve Cmax = sum_j(Ij*p_in_j + Oj*p_out_j + Fj) + R <= USD 0.10, with prices in USD/token, before the corresponding dispatch. At most two model calls, no retries, model judges, paid search, tools, or implicit fallback. Ij includes exact seed, all wrappers and any prior artifacts. Oj bounds all billable completion/reasoning tokens under the endpoint's documented semantics; do not double-count a reported reasoning subset. Reserve every potentially concurrent call before either is launched. Unknown billing or unenforceable bounds cause preflight refusal.

**conditional example.** Illustrative admission ceilings only: p_in <= USD 0.000001/token, p_out <= USD 0.000005/token, Fj=0 and R=USD 0.010 for explicitly priced remaining charges. These are not current tariff claims or a model choice. Envelopes are R09-I01: I<=16000/O<=4400/C<=0.048; R09-I02: I<=15000/O<=4200/C<=0.046; R09-I03: I<=12000/O<=4400/C<=0.044. If the actual bounded seed/request cannot fit, refuse; never truncate or replace the seed. Margin alone does not cover unknown fees.

**routing.** Pin model revision, provider endpoint, tariff snapshot, billable-token semantics and supported limits. Disable fallback and SDK retries. A timeout or cancellation is not evidence of nonbilling; retain the full reservation and block dispatch until trusted reconciliation. Do not infer an input-token upper bound from bytes/token averages.

**receipts.** Record all assigned run IDs and statuses; exact seed, wrapper, request, output and policy hashes; randomization stratum/assignment; observed input/output/reasoning/cache fields; quoted and actual monetary amounts separately. Missing token/cost/grade/time data remain unavailable. Record wall latency from run admission to frozen output, each dispatch-to-terminal elapsed duration, their sum called serialtime_proxy, and provider-reported compute duration separately if available. Sum of client durations is not measured accelerator compute time. Record late settlements without replacing frozen output. No paid calls were made.

**host compute.** Local host checks have fixed caps: at most 64 claims, 256 dependency edges, 10000 AST nodes, 4096-bit exact integers, 1 MiB candidate bytes, 2 seconds per candidate and 256 MiB additional memory. Exceeding a cap yields OPEN or HOST_LIMIT, not an incorrect-mathematics label. Already provisioned local compute has assumed zero incremental monetary charge; otherwise reserve metered host cost or refuse. Private evaluation is a separately budgeted trusted activity after freeze, with cost and reviewer time reported separately; it is not a hidden free workflow call.

**experiment contract.** Before paid execution, explicitly authorize and freeze campaign aggregate budget, N per arm, all arm manifests, fixed random order in complete blocks, endpoint/settings, primary endpoints, thresholds, and stopping. Conduct three separate panels: equal monetary allowance, equal total token allowance, and equal wall-time allowance. Equality concerns assigned allowance, not realized spend; retain savings as an outcome. Every panel still obeys USD 0.10 per run and two-call maximum. Do not force simultaneous equality or silently discard calls to match realized cost.

**statistics contract.** Fixed N; no hidden-score-dependent early stopping, adaptive allocation, or future-wrapper selection. Infrastructure/budget safety may halt a campaign, preserving every assigned unit and labeling incomplete inference. Use a direct same-model baseline. For fixed primary paired normalized-score differences D in [-1,1], a conservative simultaneous bound is mean(D) +/- sqrt(2*log(2*K/alpha)/N), clipped to [-1,1], for K preregistered contrasts under independent blocks and stable mean; this is the elementary Hoeffding/union-bound construction, not the confidence-sequence theorem. Set alpha=0.05 and freeze K before launch. Drift/dependence invalidates that sampling guarantee and requires a descriptive result. Keep raw scores, status tables and uncertainty even when intervals are wide. Additional thresholds, rubric categories, budget panels, ablations and Pareto-front selections enlarge the family or remain exploratory. Any wrapper tuning needs a subsequent independently sampled, untouched confirmation block on this same item.

**failure contract.** All assigned executions remain in intention-to-treat denominators, including preflight refusal, timeout, truncation, parsing failure, abstention and incomplete accounting. Raw mathematical score is separately scored where a frozen answer exists; the operational utility score is 0 for no delivered answer. For missing trusted grades, retain missingness and report worst/best bounds using 0 and 100 instead of inventing a measured score or dropping the row. Accepted-only accuracy and zero-cost ratios cannot replace unconditional score, coverage, cost and time deltas.

## R09-I01: Randomized second-slot repair versus independent re-derivation

**Hypothesis.** At equal second-slot allowance, repair improves unconditional mean rubric score by at least 3 points over fresh re-derivation in the actionable-public-failure stratum; the overall contrast and other stratum are separately preregistered secondary outcomes.

**known method.** Randomized treatment allocation conditional on a pretreatment stratum, followed by intention-to-treat estimation.

**proposed adaptation.** Generate one complete compact derivation, freeze it, and classify its public-check residuals. Within each fixed stratum, allocate the only remaining model slot to either repair of that artifact or a fresh complete derivation that cannot see it. The output cap, model/provider and monetary allowance are identical for the two actions. Thus the experiment identifies the value of allocating the second slot to an informed repair rather than another sample, instead of confounding an elaborate workflow with more model calls.

**allocation.** H=h(C1) belongs to {actionable_public_failure, unsupported_or_no_failure}; h and fixtures are fixed before any seed execution. Z~Bernoulli(1/2) is revealed after C1 and H are frozen. Z=1 supplies C1 plus only approved public failure codes; Z=0 supplies the seed and a frozen PCIV wrapper variant, but not C1. Both slot-two roles return a complete answer. A pre-generated blocked allocation table prevents outcome-responsive scheduling.

**estimand.** For final normalized rubric outcome Y(z) in [0,1], tau=E[Y(1)-Y(0)] over repeated calls on this fixed seed. With randomized positivity, no interference and consistent execution, tau_hat=N^-1 sum_i[Z_i*Y_i/0.5-(1-Z_i)*Y_i/0.5] is unbiased for that assigned-population contrast. Stratified mean differences may improve precision. The allocation estimator's summand has range [-2,2], so it needs its own valid randomization interval or Hoeffding radius sqrt(8*log(2*K/alpha)/N); do not reuse the paired-difference radius without adjustment.

**selection.** Use the same host selector in both arms: among complete schema-valid candidates, prefer fewer demonstrated public-predicate violations, then fewer unresolved required fields, then the lower fixed slot ID. Emit the chosen original answer unchanged with a receipt. No model self-score or private rubric appears in selection. If no complete candidate is usable, freeze an explicit partial/abstention with preserved artifacts.

**Assumptions.**

- Random assignment is generated independently of provider outcomes and private evaluation; service conditions are blocked by nearby execution time and the endpoint is pinned.
- Public checks identify only their declared predicates. A detector stratum can be uninformative about mathematical error and is never a correctness label.
- Second-slot repair and fresh-generation bodies obey their typed information boundary. A fresh answer cannot retrieve the first response through shared conversation history.
- The local selection rule and all wrapper variants are frozen on answer-independent fixtures; fresh draws are not assumed statistically independent merely because prompts differ.

**Typed inputs.**

- `SeedBytes{utf8_bytes,sha256}`
- `FrozenPolicy{wrapper_A,wrapper_B,public_detector_version,selector_version,allocation_table_hash}`
- `RunEnvelope{input_total_max:16000,output_total_max:4400,calls_max:2,run_cap_usd:0.10}`

**Typed outputs.**

- `AllocationReceipt{first_candidate_hash,stratum,assignment_probability,assigned_role,actual_role,status}`
- `SelectedAnswer{candidate_hash,answer_bytes,public_check_receipt,residuals}`
- `FrozenRun{all_candidate_hashes,cost_receipt,wall_latency,serialtime_proxy}`

**Stage DAG.**

- `bind` (host; dependencies: none; output-token cap: 0): `(SeedBytes, FrozenPolicy, RunEnvelope) -> BoundRun`. Verify exact seed inclusion, type-check the OPERADS composition, reserve aggregate maxima and freeze the PCIV wrapper lineage. Prepare concealed randomized second-role assignment. Preflight refusal is a recorded assigned-run outcome.
- `draft` (model; dependencies: bind; output-token cap: 2200): `BoundRun -> CandidateV1`. Receive unchanged seed in its own message. Produce a complete compact derivation with explicit claim IDs, assumptions, requested-part coverage and public-check artifacts; identify open obligations. Return at most 2200 billable output/reasoning tokens under the admitted endpoint semantics.
- `allocate` (host; dependencies: draft; output-token cap: 0): `CandidateV1 -> AllocationPacket<RepairInput|FreshInput>`. Freeze C1, run PFP public checks and calibrated EIS screening, determine the fixed stratum, then reveal the randomized role. Bind h, Z, propensity and all input hashes. RepairInput contains C1 and bounded non-secret failure codes; FreshInput contains no C1. Never pass a raw private/evaluator diagnostic.
- `second_slot` (model; dependencies: allocate; output-token cap: 2200): `AllocationPacket<RepairInput|FreshInput> -> CandidateV2`. One mutually exclusive paid operation, not two branches dispatched: repair C1 if assigned RepairInput; independently derive a complete answer if assigned FreshInput. Both receive the exact seed and the same 2200-token ceiling. If the first call has uncertain billing or the remaining reservation fails, issue SKIPPED without a provider call.
- `freeze` (host; dependencies: second_slot; output-token cap: 0): `(CandidateV1,CandidateV2|Skipped) -> FrozenRun`. Recheck candidate artifacts, apply the fixed public selector, retain failures and both original outputs, freeze final bytes and ledger. The private evaluator later sees frozen candidates/final output only after the full campaign closes; its results cannot reopen this DAG.

**Baseline.** Direct same-model single call with the same assigned money or token allowance in its respective panel; also a two-call draft plus generic self-critique control isolates extra-call effects.

**Ablations.**

- Replace detector-stratified allocation with unstratified randomized allocation
- Repair with generic feedback instead of public failure codes
- Select slot two unconditionally instead of the fixed public selector

**Evaluation.** Freeze N, strata, primary contrast and K first. Report arm/stratum assignment counts, delivered-answer score, all-run score, slot-two improvement over frozen C1, actual cost, token fields, wall latency, serialtime_proxy and missingness. First-draft scores are computed only in delayed private evaluation. Randomize run order within complete blocks; common timestamps or provider seed labels do not create paired counterfactuals.

**Falsification.** The 3-point actionable-stratum advantage is contradicted when its multiplicity-adjusted upper confidence bound is below 3; a nonpositive upper bound rejects even a positive gain. Wide bounds mean inconclusive. Any second-role dispatch seeing a hidden score or a supposedly fresh branch seeing C1 falsifies the isolation contract.

**Risks.**

- Thin strata and a tiny paid campaign may make the randomized contrast extremely imprecise.
- Provider changes, cache carryover or rate-limit interference can invalidate stable-mean assumptions; record and block rather than pool silently.
- A public selector can reject a correct but unfamiliar derivation or favor formally neat nonsense; rubric score remains the endpoint.
- Testing many strata, allocation probabilities or selector tie-breaks after seeing grades creates multiplicity and same-item tuning.

**Conditional budget.** At most two calls. Cmax<=16000*p_in+4400*p_out+F1+F2+R. At the stated conditional price ceilings and R=0.010, Cmax<=USD 0.048. Slot-two alternative roles share one reservation; they are never both executed. Actual cost is measured separately.

## R09-I02: Public-evidence continuation gate with explicit abstention accounting

**Hypothesis.** Relative to always-repair two-call execution, the gate reduces mean realized provider spend by at least 15% while losing no more than 3 points in unconditional mean rubric score; both conditions must hold with the preregistered uncertainty treatment.

**known method.** Selective prediction with a reject option and a bounded two-stage cascade.

**proposed adaptation.** Run one complete derivation and a public obligation audit. Spend the second call only when a fixed predicate finds a repairable public defect and a safe reservation remains. Stop with the first answer when no such defect is found; stop with explicit unresolved claims or abstention when infrastructure failure or unsupported obligations cannot be repaired by the admitted second-stage operation. No high self-confidence threshold or private expected-answer signal is used.

**policy.** g(C1,receipt) in {STOP_WITH_UNCHECKED_ANSWER,REPAIR_ONCE,PARTIAL_OR_ABSTAIN}. REPAIR_ONCE requires at least one declared repairable schema/identity/coverage defect, healthy bound checker, known billing and sufficient reservation. Unsupported analytic obligations remain OPEN rather than being treated as false. A direct host integrity refusal is enforced even without both EIS danger signals; immune suppression must not manufacture a second independent signal from the same model statement.

**metrics.** Let A=1 only for a delivered output labeled full_answer; partial answers and full abstentions have A=0 for this selective metric. For normalized trusted score Y, coverage=E[A], selective risk=E[A*(1-Y)]/E[A] when E[A]>0, and full-answer delivered utility=E[A*Y]. This strict utility gives partial answers zero while their independently graded raw rubric score is still reported; the label full_answer asserts intended coverage, not correctness. Preserve the original unfiltered final rubric score too, including partial answers. Score-based risk is rubric loss, not the probability that every formula is correct; report the separately defined complete-correctness indicator if the evaluator supports it. C=C1+1{REPAIR_ONCE}*C2 and E[C]=E[C1]+E[1{REPAIR_ONCE}*C2]; factorization is not assumed.

**stopping.** All stopping happens from frozen public rules before private grading. Campaign N is fixed. A later confidence interval is descriptive or fixed-N inference under its stated assumptions, not permission to stop early when a convenient significance level appears.

**Assumptions.**

- A fixed public registry distinguishes demonstrated errors from absent evidence and unsupported theories.
- EIS negative-selection fixtures and false-rejection controls are answer-independent, versioned and disjoint from any fixtures used to choose detector thresholds.
- The public repair packet cannot expose expected corrections from private evaluation; PCIV only mutates the allowed wrapper/repair instructions while preserving seed bytes.
- An early accepted result is merely an unchecked answer with bounded public evidence. Neither coverage nor zero public defects certifies the complete derivation.

**Typed inputs.**

- `SeedBytes{utf8_bytes,sha256}`
- `ContinuationPolicy{repairable_failure_codes,unsupported_codes,public_fixture_commitment,version}`
- `RunEnvelope{input_total_max:15000,output_total_max:4200,calls_max:2,run_cap_usd:0.10}`

**Typed outputs.**

- `GateDecision{action,predicate_ids,public_evidence_hashes,no_private_feedback:true}`
- `SelectiveAnswer{answer_bytes,delivered_status,unresolved_claims,coverage_indicator}`
- `FrozenRun{branch_taken,first_artifact_hash,final_artifact_hash,reservations,actual_usage}`

**Stage DAG.**

- `bind` (host; dependencies: none; output-token cap: 0): `(SeedBytes,ContinuationPolicy,RunEnvelope) -> BoundCascade`. Pin seed bytes, wrappers, detector controls, typed branch operations and both potential call ceilings. Validate finite host limits and fail closed on uncertain pricing. Do not run the seed to tune thresholds.
- `derive` (model; dependencies: bind; output-token cap: 2600): `BoundCascade -> CandidateV1`. Produce a complete answer to every seed request with a compact claim/assumption map and explicit unresolved obligations. Seed remains a separate exact-byte message. The admitted completion cap is 2600 tokens including billable reasoning where applicable.
- `gate` (host; dependencies: derive; output-token cap: 0): `CandidateV1 -> GateDecision<Stop|Repair|Partial>`. Freeze C1, invoke PFP public checks and EIS fixture-bound rules, then apply the preregistered decision table. STOP means no flagged repairable defect, not proven correctness. A budget or infrastructure issue yields an explicit partial/abstention outcome; missing mathematical support stays OPEN. Record the counterfactual rule conditions without private labels.
- `repair_once` (model; dependencies: gate; output-token cap: 1600): `GateDecision<Repair> -> CandidatePatch; Stop|Partial -> Skipped`. Dispatch only on Repair and known settled prior billing, with unchanged seed plus the public artifact and bounded defect codes. Return a 1600-token bounded patch or explicit inability. No automatic retry. Patches cannot alter seed assumptions or erase unsupported obligations. Non-Repair branches produce a host Skipped token and incur no call.
- `freeze` (host; dependencies: repair_once; output-token cap: 0): `(CandidateV1,CandidatePatch|Skipped,GateDecision) -> FrozenRun`. Apply only well-formed patches linked to declared claims, replay affected public checks, and preserve the original response. If patch verification fails, keep the original with unresolved status rather than inventing a successful repair. Freeze final bytes, coverage, statuses and cost receipt. Close every branch before separate private grading.

**Baseline.** Direct same-model call at matched assigned money/token allowance, and always-repair using exactly the same draft/patch prompts and ceilings; the latter is the primary cost-saving comparator.

**Ablations.**

- Randomly skip the second slot at a preregistered fixed probability, separating detector value from generic economizing
- Always deliver the first artifact without selective status
- Use single-signal detector matches for continuation only, preserving direct host integrity refusals

**Evaluation.** Report unconditional raw rubric score, operational delivered utility, abstention and partial rates, score-loss coverage curve at the one preregistered gate, actual spend and both time metrics. Selected-answer accuracy is secondary. Validate the gate using synthetic valid/invalid receipts including missing usage, checker exception, exact contradiction and unsupported expression. Retain all assigned failures; grade missingness gets bounds. Any extra gate thresholds are exploratory or increase K.

**Falsification.** Reject the declared savings/noninferiority conjunction if either the upper confidence bound on savings is below 15% or the upper confidence bound on the score difference is below -3 points; intervals crossing the thresholds are inconclusive. Any path labeling unsupported mathematics as certified or hiding abstentions from the denominator falsifies the mechanism contract.

**Risks.**

- Reducing coverage alone can improve accepted-only accuracy, so that metric cannot establish benefit.
- The gate might spend more often on intrinsically difficult outputs; naive repaired-versus-unrepaired comparisons are confounded and are not causal evidence.
- Public fixed thresholds can be overfit to the same seed after viewing grades; no within-campaign changes are permitted.
- A short patch can leave stale downstream dependencies; replay is required and residuals remain visible.

**Conditional budget.** Cmax<=15000*p_in+4200*p_out+F1+F2+R<=USD 0.046 at the conditional ceilings. Actual cost equals the first-call bill plus a second-call bill only when dispatched, plus priced fees. Reserve for the worst branch before admission; unused capacity is a measured saving, never an automatic extra retry.

## R09-I03: Deadline-frozen two-candidate portfolio with serial and parallel schedules

**Hypothesis.** At equal monetary and output-token allowance, parallel scheduling increases the fraction of assigned runs delivering a candidate by the fixed deadline, with at most a 3-point reduction in unconditional mean rubric score; any latency advantage must be reported alongside unchanged or higher actual aggregate spend and serialtime_proxy.

**known method.** Bounded algorithm portfolios, fork/join scheduling and performance profiles under a fixed deadline.

**proposed adaptation.** Create two complete candidate attempts with fixed PCIV wrapper variants, neither seeing the other, and compare parallel dispatch with serial dispatch using the same two-call allowance and public selector. At a preregistered deadline, freeze a usable completed candidate or abstain. This directly measures whether concurrency buys delivery latency on the fixed seed without pretending it reduces total provider work or cost.

**time model.** Let dj be each observed dispatch-to-terminal duration and h total host overhead. Without queue contention, parallel wall latency is approximately h+max(d1,d2), serial wall latency approximately h+d1+d2; serialtime_proxy=d1+d2 in both schedules. Actual timestamps, concurrency contention and transport time override this approximation. Provider-reported compute time, if absent, is unavailable rather than inferred.

**deadline rule.** D is fixed before dispatch and measured from run admission. At D choose only schema-usable candidates whose full bytes arrived and public checks completed by D using the same fixed selector; deterministic slot ID breaks ties. No usable candidate yields abstention. Late results are retained for accounting and a clearly separate offline sensitivity analysis, never substituted into the frozen primary result. Client cancellation does not release an uncertain billing reservation.

**resource rule.** Use two predeclared full-answer variants with 2200-token ceilings; no extra synthesis/judge call. The serial comparator starts slot 2 only if policy permits before D, with an undisbursed reservation otherwise unused. Keep assigned two-slot allowance fixed and compare actual dispatch/cost separately. A second no-deadline paired panel isolates scheduling overhead from deadline censoring.

**Assumptions.**

- The provider permits the declared concurrency and documents charge/token caps. Concurrency itself may induce queueing or rate limits, which are measured rather than assumed absent.
- Both PCIV wrapper variants preserve the full immutable seed and are fixed before execution; no specialized seed subproblem or derived formula is substituted.
- The final selector uses only PFP/EIS public receipts and slot IDs. It does not select by a private score, model self-confidence, or answer agreement.
- A strict wall deadline includes bounded host validation time; the adapter must reserve time to freeze a result and label any missed deadline explicitly.

**Typed inputs.**

- `SeedBytes{utf8_bytes,sha256}`
- `PortfolioPolicy{variant_A_hash,variant_B_hash,schedule:parallel|serial,deadline_ms,selector_version,randomized_slot_order}`
- `RunEnvelope{input_total_max:12000,output_total_max:4400,calls_max:2,run_cap_usd:0.10}`

**Typed outputs.**

- `SlotResult{slot_id,Completed|Late|Timeout|NotDispatched|InfrastructureError,received_at,public_receipt}`
- `DeadlineAnswer{frozen_at,deadline_met,chosen_slot|abstain,answer_hash}`
- `SchedulingReceipt{dispatch_intervals,wall_latency,serialtime_proxy,provider_compute_time|unavailable,all_reservations}`

**Stage DAG.**

- `bind` (host; dependencies: none; output-token cap: 0): `(SeedBytes,PortfolioPolicy,RunEnvelope) -> TwoSlotPlan`. Create two typed operations from protected PCIV wrapper variants. Randomize schedule/run order within preregistered blocks. Reserve both worst-case calls transactionally before parallel dispatch; set an absolute deadline and a fixed host-check margin. No private feedback is available.
- `candidate_A` (model; dependencies: bind; output-token cap: 2200): `TwoSlotPlan -> SlotResultA`. Receive the entire unchanged seed and variant A. Return a complete compact derivation with claim IDs and explicit open obligations, at most 2200 billable output/reasoning tokens. No access to B, filesystem, retrieval or evaluator. Execute when the scheduler assigns slot A; scheduler order is an explicit resource constraint rather than a data dependency.
- `candidate_B` (model; dependencies: bind; output-token cap: 2200): `TwoSlotPlan -> SlotResultB`. Receive the entire unchanged seed and variant B, never A's output. Use the same 2200-token ceiling. Parallel mode starts both ready operations; serial mode permits only one active call and randomizes which slot goes first. If the deadline or uncertain billing forbids dispatch, return NotDispatched with no provider request.
- `public_join` (host; dependencies: candidate_A, candidate_B; output-token cap: 0): `(SlotResultA,SlotResultB,DeadlineEvent) -> DeadlineSelection`. Treat every dependency as a total terminal result including PendingAtDeadline, not an instruction to wait forever for both providers. Apply bounded PFP/EIS checks to arrived candidates, choose via the fixed selector, and retain detector/control receipts. OPERADS type compatibility alone does not validate this deadline semantics; the scheduler adapter needs synthetic event-trace tests.
- `freeze` (host; dependencies: public_join; output-token cap: 0): `DeadlineSelection -> FrozenRun`. Freeze chosen bytes or abstention no later than the admitted deadline, recording a miss if overhead exceeds it. Late provider settlement is append-only accounting outside the answer-producing DAG; never change selected bytes. All charged or uncertain work remains in the aggregate ledger and denominator. Private grading begins only after campaign output freeze.

**Baseline.** Direct same-model one-call answer with matching assigned total monetary/token allowance, plus serial execution of the identical two candidate operations as the primary scheduling comparator.

**Ablations.**

- Parallel candidates with identical wrappers, isolating diversity from scheduling
- Choose the fixed first usable slot instead of ranking public receipts
- No-deadline execution of both schedules, keeping both calls and reporting complete-run latency separately

**Evaluation.** Use a fixed deadline chosen from infrastructure-only timing pilots or a user latency requirement, never from private seed scores. Report deadline-delivery fraction over all assigned runs, unconditional rubric score, abstention, per-slot error/rate-limit counts, actual tokens/costs, critical-path wall latency and sum of observed call durations. Completed-by-deadline results are the primary endpoint; survivor-only latency summaries and late-result scoring are secondary and explicitly labeled. Shared endpoint contention means paired blocks need workload isolation or a descriptive caveat.

**Falsification.** A simultaneous upper confidence bound at or below zero for the deadline-delivery improvement rejects a positive scheduling benefit. A score-difference upper bound below -3 points rejects the noninferiority requirement. A late candidate replacing the frozen answer, a third model call, or a cancellation treated as zero cost falsifies the implementation contract.

**Risks.**

- Parallel calls can worsen queueing, throttle each other or multiply timeouts; shorter theoretical critical path is not observed benefit.
- Selecting among completed candidates creates completion-time selection bias; keep late, failed and undispatched slots visible.
- Polling/stream parsing overhead can miss the wall deadline even if the provider completed earlier.
- Changing wrapper diversity, schedule and selector simultaneously confounds mechanisms; retain the serial identical-body control and fixed ablations.

**Conditional budget.** Two calls maximum. Cmax<=12000*p_in+4400*p_out+F1+F2+R<=USD 0.044 at the conditional ceilings. Parallel dispatch holds both reservations before any request. Deadline expiry never refunds an uncertain call. Serial and parallel have equal assigned limits; actual realized costs may differ because the serial second slot can remain undispatched.

## Reusable primitive

**FrozenPolicyRunReceiptV1.** Implement a typed run/policy receipt and deterministic host-only scheduler simulator before any paid experiment. It connects randomized allocation, selective continuation and deadline portfolios without introducing a semantic correctness bit.

The generation/selection DAG has no edge from delayed evaluation. All stage result types include bounded failure/skip outcomes, every paid stage consumes a unique reservation, and no model path can make more than two calls or exceed the conditional USD 0.10 run quote. Receipt fields distinguish actual observations from estimates and preserve residuals; typed composition does not establish semantic truth.

- binding: `seed_sha256`, `compiled_request_sha256`, `policy_sha256`, `wrapper_parent_child_hashes`, `detector_fixture_commitment`, `endpoint_revision`, `tariff_snapshot_hash`
- assignment: `campaign_id`, `assigned_run_id`, `block_id`, `arm_id`, `stratum`, `allocation_probability`, `randomization_commitment`, `assigned_allowance`
- execution: `stage_id`, `typed_input_refs`, `typed_output_ref`, `dispatch_time`, `terminal_time`, `deadline`, `failure_status`, `candidate_frozen_at`, `selected_candidate_hash`
- accounting: `quote_microusd`, `held_microusd`, `actual_charge_or_unavailable`, `input_tokens_or_unavailable`, `output_tokens_or_unavailable`, `reasoning_tokens_or_unavailable`, `cache_fields_or_unavailable`, `wall_latency`, `serialtime_proxy`, `provider_compute_duration_or_unavailable`
- delayed_evaluation: `campaign_freeze_hash`, `trusted_grade_or_missing`, `all_assigned_denominator`, `coverage`, `raw_rubric_score`, `operational_utility`, `multiplicity_family`, `confirmation_block_id`

Implement only the policy compiler and synthetic scheduler/receipt fixtures first. Do not read or solve the seed, inspect private key storage, or make paid provider calls. Include positive/negative fixtures for duplicate dispatch, concurrent reservations, delayed billing, deadline censoring, hidden-feedback rejection, deterministic assignment, protected seed mutation and missing accounting.

After host-only validation and separately authorized campaign admission, preregister a small fixed-N R09-I01 comparison with a direct same-model baseline. Keep all outputs and the entire campaign frozen before grading. Report it as a pilot on one item if precision is inadequate; do not turn a wide or selected positive estimate into a general workflow-improvement claim.

