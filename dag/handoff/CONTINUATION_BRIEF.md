# Research and engineering continuation brief

## Mission and stopping boundary

Find useful, defensible mathematical mechanisms in PFP, EIS, PCIV and OPERADS, then determine experimentally whether workflows using them improve full-answer accuracy at acceptable money, token and time costs. The user wants ambitious adversarial attacks, mutations and discovery, but objected to many hours of document cleanup without measured workflow improvement. Prioritize implemented mechanisms and informative comparisons. Keep the exhaustive source audit honest and separate. Do not consume an unbounded agent or API budget to inflate coverage or enumerate cosmetic permutations.

This checkpoint stops all experimentation at the user's request. Resume only in the new session where the user invokes the continuation. Neither this brief nor a design catalog grants an unlimited paid campaign. The existing hard constraint is USD 0.10 **per whole run**, including all paid stages, repair attempts and retries. Freeze a finite campaign and aggregate ceiling before dispatch. No new run was launched during this handoff.

The user originally requested: clean the checkout; seal a graduate QM seed and correct answer; review every original file outside dot-prefixed directories; assess the mathematical foundations and usefulness of papers; build derivation and workflow DAGs; use ten researchers to propose meaningful typed compositions; relocate Anomalon pilots/demo material with source deletions in PRs; turn useful pilots into workflows; publish completed workflows in the Wiki; and compare every implemented workflow on the same exact seed. The mathematical audit, pilot consolidation and complete benchmark program remain unfinished.

## Where to start

Repository: <https://github.com/dbccpage/proposal_fidelity_protocol_pfp>.
Local checkout: `C:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp`.
Original census baseline: `8050c66900899771766f33e8f5fdd200b7dd9120`.
Benchmark branch: `codex/pfp-workflow-benchmark-20261110`, published head `4cdacabfd7d5a03ab346004559724335906558e2`, draft [PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58).
Companion checkpoint branch: `codex/pfp-research-handoff-20261110`, [draft PR #59](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/59), based on that benchmark head. Consult `publication.json` for the final companion PR and current commits; recheck mutable GitHub state before acting.

Read these small entry points before broad searching:

1. `dag/README.md`, `dag/WORK_PRIORITY.md`, this brief and `dag/FOUNDATIONS.md`.
2. `wiki/Workflow-QM-Benchmark.md`, `dag/benchmark/results_summary.json`, `LIVE_RUNNER.md`, `CHARPOLY_WORKFLOWS.md`, `HAMILTONIAN_WORKFLOWS.md`, `RATIONAL_PANEL.md`.
3. `dag/benchmark/reference_runner.py`, `live_campaign.py`, `budget_ledger.py`, `campaign_ledger.py`, `openrouter_provider.py`, `summarize_runs.py` when changing execution or accounting.
4. `dag/derivations_dag.json`, `workflows_dag.json`, `composition_catalog.json`, `validation.json`; query them programmatically rather than loading megabytes into a model context.
5. `dag/reviews/coverage.json`, `pending_reuse_candidates.json`, `papers_audit.json`, and the specific `additional_*.json` reports implicated by the next mechanism.
6. `dag/pilot_triage/README.md`, `dag/migrations/demo_support_publication.json`, `demo_support_verification.json`, `anomalon_followup.json` before changing relocated material.

Use the repository Python environment, PowerShell, and explicit UTF-8. Do not overwrite `dag/PROGRESS.md` through a lossy decode: it has a historical non-UTF-8 byte; append bytes or preserve the original exactly. Keep secrets out of logs, prompts, command lines and commits. No provider key should be printed. There are no project AGENTS.md instructions in the checkpoint inventory.

## Current state and what it does not establish

The original census has 32,261 files, with 9,576 full-source-reading receipts, 33 partial and 22,652 pending. The DAGs have 3,126 derivation nodes / 3,060 edges and 4,562 workflow nodes / 9,472 edges, checked acyclic at this checkpoint. Ten research reports propose 30 ideas. The composition catalog contains 4,250 bounded designs: 3,776 pairs and 474 triples drawn from 49 existing families and new ideas under explicit call/node/type bounds. They are not 4,250 implementations and do not enumerate all possible programs.

There are 12 runnable benchmark plans and 17 Wiki entries including the historical WF1–WF5 workflows. Inspect `reference_runner.PLANS` for current identifiers. Their native integration is narrow: an isolated Rust exact characteristic-polynomial computation and Python host checks. Full PFP host execution, EIS regulation, PCIV selection and OPERADS execution have **not** been integrated into a single validated QM pipeline. Naming a plan after a system does not supply that integration.

The latest published Wiki revision is `78810678064fb6b4439210899da3102b69849d1d`; see `dag/wiki/workflow_publication_charpoly_20261110.json`. Public entry: <https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-QM-Benchmark>. Every completed future workflow needs its implementation status, exact predicate, inputs, failure behavior, metrics and limitations documented in the Wiki and `dag/wiki/workflow_documentation.json`. Keep proposed ideas distinct from implemented and evaluated plans.

The current benchmark's fresh committed export passed 249 tests plus 48 subtests and rebuilt the isolated wrapper offline using Windows/MSVC. Evidence: `dag/benchmark/committed_native_validation.xml`, `native_code_publication_20261110.json`, `committed_native_validation_evidence.zip`. This is not a full monorepo test or proof of model accuracy. `charpoly_wire.py` and its tests subsequently passed 12 tests plus 20 subtests; the normalizer is unregistered and unused in paid workflows.

## Mathematical foundations to preserve and challenge

**PFP:** typed proposals, contracts, witnesses, exact finite predicates, bindings and custody. Useful guarantees are conditional on the admitted carrier, encoding, source, verifier, and connection between the checked object and the task. A passed schema, sealed transcript or valid intermediate witness does not establish arbitrary mathematical prose, provenance authenticity, or physical assumptions.

**OPERADS:** typed, ordered substitution and composition, with explicit input/output compatibility and declared operations. Test the identity, associativity, ordering and substitution laws for the actual executor and its side effects. A diagram or type-correct plan does not prove those laws. Existing native inline execution is limited; guarded compositions need host execution glue and real budget/error propagation.

**EIS:** evidence signals and regulatory dispositions. Signal 2 alone can be diagnostic; the exact source's decision table determines what combinations permit suppression or escalation. Two fields containing the same observation do not constitute independent evidence. Exact checker refusal is a separate predicate and should not be disguised as two independent observers. Study false acceptance, false refusal, sensitivity to stale bindings, and failure of supposedly independent channels.

**PCIV:** candidates, policy fitness, required outcomes/receipts and Pareto selection under trusted metadata. Make required task sets nonempty, bind scores to independently assessed frozen outputs, and include failed attempts and all resource costs. A candidate's self-declared success is not validation. The benchmark's Python Pareto summary is not native PCIV integration.

**Exact polynomial identity slice:** the host admits an affine matrix of dimension n <= 4 in three real parameters with rational coefficients. Degree bounds plus all (n+1)^3 rational grid points and exact native arithmetic can certify the admitted characteristic polynomial globally. Without degree bounds a finite grid is only testing; an adversarial polynomial can vanish at every sampled point and differ elsewhere. Axis/diagonal samples are not the full tensor grid. Certification covers that polynomial for the admitted matrix, not eigenvectors, projectors, dynamics, entanglement, thermal statements or the final answer.

Read reports before turning old helpers into oracles. Existing findings include unchecked Rational64 arithmetic; Hermitian imaginary-diagonal admission; a public So4 bypass; sparse mutation on failure; an old Laplacian orientation error; degenerate modular data admitted through a structure-only path; an incorrect binary-field polynomial admission; ragged marginal and zero-denominator panic routes; zero-step Markov dimension bypass; a selected-minimum Majorana residual misdescribed as a lower bound; raw GF2 carrier bypass; and a packet wall trusting a separately supplied residual weight. These are source-specific bounded findings, not blanket refutations of their underlying theories.

Useful pilot mechanisms include primal/dual LP certificates, max-flow/min-cut, exact linear algebra, finite gluing, Smith form, chain/cochain checks, persistence and covariance tests. Known adversarial examples include capacity `1.9` truncated to `1`, disagreement between SQLite and Python TEXT/number comparisons, feasible dual bounds accepted as exact optima without primal equality, incomplete cohomology bases accepted, and duplicate incidences overwritten. Check the precise owning report and whether the paired gate really accepts the attack.

All 38 primary manuscripts have a usefulness assessment. Evaluate definitions, theorem assumptions, actual proofs, code correspondence, reproducibility and incremental contribution. Do not infer LLM authorship from style. Publication discrepancies are evidence to narrow a claim: examples include broad claims from narrow Paper001 receipts, Paper003 prose calling a case diagnostic when its rule locks down, Paper004 retained PDF claims diverging from amended Markdown/TeX, and Paper007's 21 queried axioms not being the full 64-item census. Preserve historical evidence; do not silently rewrite papers or call every defect a theorem refutation.

## Seed, evaluator and leakage boundary

The only benchmark seed is `dag/benchmark/seed_prompt.txt`, exact UTF-8 LF bytes, SHA-256 `9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7`. It asks a five-part two-spin QM problem with H = J(XX + YY) + Delta(ZI - IZ) + KZZ, initial |01>, real parameters and hbar = kB = 1: spectrum/projectors/degeneracies; dynamics; entanglement/CHSH; Gibbs/partial transpose; consistency checks. Read the public seed, not an answer file, when implementing a task adapter.

The separately stored original answer commitment is `60557cd9c141245544bf866e6ad463d0aacfa3e36431ec71b14a895698b6e77e`. Do not locate, read or disclose the private answer to workflow designers or solvers. Hashes are commitments, not encryption. Initial independent numerical checks covered 261 cases with maximum error 5.329e-15; that does not prove universal correctness.

The fixed evaluator rubric is `dag/benchmark/pilot_20261110/evaluator_rubric.json`, SHA-256 `eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc`: spectrum 20, dynamics 20, pure entanglement 25, thermal entanglement 25, checks 10, over 25 criteria. Grades assess the final `answer_text` only. A refusal has zero delivered-answer points but is different from an asserted false statement. Grades are model-assisted assessments with quoted evidence and independent public derivation, not formal or human certification.

Keep three roles separate: controller/designer, solver, evaluator. Evaluation reports now contain correct mathematical information and observed model errors. Never give this brief, reports, grades, answer references, review notes, hidden files, retrieval indexes or unrestricted repository access to a benchmark solver. Freeze requests and outputs before grading; do not edit or replace historical results. Audit the actual serialized messages for leakage. Controllers who have seen errors must label same-seed optimization exploratory; future sealed holdouts are needed to assess transfer.

## Measured results and lessons

There are 24 frozen, graded attempts: 23 with paid dispatch and one infrastructure refusal before dispatch. Total settled charges are 55,614 microUSD = USD 0.055614, with zero held liability. No fully correct solution has been established. This is provider API spending, not Codex subscription usage.

| Observation | Score | USD | Input / output tokens | Wall seconds |
|---|---:|---:|---:|---:|
| DeepSeek direct | 83 | 0.004211 | 403 / 10805 | 270.038 |
| DeepSeek self-critique | 88 | 0.007756 | 9594 / 13844 | 370.259 |
| Qwen235 direct, 16k output allowance | 62 | 0.006222 | 432 / 11241 | 601.157 |
| Qwen235 five sections | 26 | 0.009065 | 2904 / 16000 | 445.486 |
| Native-charpoly checked | 0 delivered | 0.001685 | 2680 / 2596 | 70.413 |
| Native-charpoly ungated | 47 | 0.005329 | 2956 / 12395 | 313.399 |

DeepSeek self-critique gained 5 points in one sample at roughly 84% more money, 109% more tokens and 37% more time; it is not a matched-resource comparison or proof of a system-specific effect. Its final answer still has derivation/exceptional-case errors. Qwen's longer allowance did not ensure coverage: direct stopped voluntarily after part 3; sectioned responses were truncated and contradictory. Cheap small-model rational/Hamiltonian attempts generally scored poorly. More stages have not automatically improved results.

The checked charpoly proposal first failed rational canonicalization; its single repair was malformed and length-truncated. Neither proposal reached native computation. The ungated answer scored 20+17+4+0+6 = 47, stopped during reduced-state work, and omitted the later entanglement/thermal solution. Post-run lossless normalization of both initial proposals still refused `NONMONIC_LEADING_COEFFICIENT`. Formatting alone is not the next useful experiment.

Keep all attempt folders: `pilot_20261110`, `hamiltonian_pilot_20261110`, `hamiltonian_large_model_20261110`, `length_control_20261110`, `section_control_20261110`, `model_control_20261110`, `model_control_repaired_20261110`, `deepseek_critique_20261110`, `charpoly_pilot_20261110`. Rebuild the all-campaign comparison with `build_comparison_report.py`. Do not use old `build_pilot_report.py` to overwrite it with the first six attempts, or the older five-plan evaluator that drops v2.

## Execution and accounting constraints

Use existing ledgers rather than a parallel ungoverned HTTP script. Every run has a maximum 100,000 microUSD liability across its stages. Preflight reserves the full advertised input context plus the output ceiling at current endpoint tariffs. Known charges settle even when later validation or artifact writing fails. Unknown charge or in-flight liability remains held and blocks further dispatch. No resets, retries after ambiguous delivery, fallback routing or optimistic token heuristics to make a run fit the cap.

Manifests define finite exact membership, order, plan hashes, model/endpoint, output ceilings and aggregate budget. Review current official provider documentation and endpoint metadata before new calls; old prices/model availability may drift. An OpenRouter provider instance is single-use after its upper quote prepares a request: do not reuse a preflight instance for actual execution. That mistake already caused the zero-dispatch refusal. The 120-second transport timeout is socket inactivity, not a total wall-clock deadline. If adding cancellation, retain liability for requests that may have reached the provider.

Direct Anthropic billing is not implemented. If adding it, port the same admission/accounting/failure contracts and test them offline first. A paid Anthropic subscription is not automatically an API entitlement. Never substitute OpenAI subscription usage for the recorded API budget. Obtain only required credentials through the user's supported secure mechanism, without printing them.

For analysis, maximize independent full-answer accuracy and minimize money, total input+output tokens and wall time. `summarize_runs.py` uses those four axes. Reasoning tokens are not added a second time when already included in output. Missing tokens exclude a point from Pareto eligibility, not raw results. Include setup, verification and failed-attempt costs; distinguish amortized costs from one-off costs and sequential wall time from summed provider durations.

## Recommended next executable increment — not implemented

The planned next idea is to derive the characteristic polynomial in the host from the public admitted matrix instead of asking a model to serialize it. Proposed implementation: evaluate the 125 exact grid points, perform exact tensor Lagrange interpolation with explicit degree assumptions, then replay through the independent exact identity checker. Emit a compact certificate with its narrow scope and source/build bindings. Do not bake a manually solved answer or evaluator constants into the host.

Compare three one-call arms with the same coverage-first instruction and output allowance: (1) exact seed only; (2) seed plus admitted public matrix; (3) seed plus that matrix and host-derived polynomial certificate. The shared instruction should require all five parts before lengthy derivation, without naming known answer errors. This separates prompt coverage, public representation and computed certificate effects. Only after offline review should a finite pilot manifest and aggregate cap be admitted. A suggested three-run envelope is USD 0.30 total, still <= USD 0.10 per run; **no such campaign is currently admitted**.

There is no `qm_host_charpoly.py`, `coverage_workflows.py` or host implementation/test in this checkpoint. `host_charpoly_pilot_20261110/reference_provenance.json` and `reference_design_amendment.json` are preparation-only evaluator records. `charpoly_wire.py` is a separate finished pure normalizer, not that implementation. Do not present plans as completed features.

## Adversarial attacks and mutations

Build an explicit threat model and an attack registry with owning boundary, mutation, expected behavior, actual outcome, evidence and unresolved scope. Run deterministic local attacks before paying for model calls. Every discovered failure should become a minimized fixture tied to a real predicate, not a test that merely mirrors implementation.

* Ingress: missing/unknown/duplicate keys, duplicate monomials before zero removal, booleans masquerading as integers, floats/NaN/infinity, signed or zero denominators, huge numerator/denominator bits, Unicode lookalikes, oversized JSON, ragged matrices, invalid dimensions and non-Hermitian input.
* Algebra: nonmonic leading coefficients, wrong sign/basis/parameter order, omitted terms, low-degree boundary violations, polynomials vanishing only on the test grid, corrupted interpolation, overflow, singular and zero parameters, degeneracies and discontinuous case splits. Mutation tests must distinguish exact proof conditions from sampled evidence.
* Custody: stale seed/plan/source hashes, changed Rust source after preflight, swapped binary/build receipts, altered answer after grading, forged grades, equivalent bytes with ambiguous serialization, tampered task IDs and current-core replay masquerading as historical authenticity.
* Semantics: correct intermediate polynomial paired with false final prose; correct spectrum with wrong projectors/dynamics; valid witness for a different task; omitted question parts; contradictory concatenated sections; verifier feedback falsely promoted to full-answer certification.
* EIS/PCIV: cloned observations presented as independent, correlated blind reviewers, stale suppressions transferred across tasks, empty mandatory task list, missing receipts, self-reported fitness, duplicate candidate IDs, survivor-only selection and trusted metadata spoofing.
* Composition: invalid substitution, swapped noncommuting operators, repeated stages disguised as new workflows, discarded failures, side-effectful associativity, context loss, cycle bounds, inconsistent branch joins, shared mutable state, irreversible mutation before error and broken witness transport.
* Provider/accounting: timeout before/after delivery, malformed usage, missing cost, overcharge, metadata drift, fallback routing, crash between admission and receipt, duplicate dispatch, failed write after charge, concurrent ledger claims, cancellation with unknown liability and campaign exhaustion.
* Prompt/context: instructions embedded in candidate artifacts or retrieved text, requests to reveal evaluator material, hostile "verified" labels, adversarial review instructions and misleading tool output. Treat attack text as data. Do not grant these workflows shell/network/repository access solely to test a prompt injection.

Measure mutation kill rate only over a declared relevant mutation set. Also report false acceptance, false refusal, crashes, unresolved outcomes and survivors. Minimize and explain survivors; neither 100% kills nor a large test count proves arbitrary semantic correctness. Preserve useful metamorphic relations only after proving their assumptions: basis permutation with transported state/observables, parameter relabeling, exact rational scaling and typed identity insertion are candidates, not automatic invariances.

## Experiment design and workflow search

Begin from the strongest direct baseline, not a deliberately weak model. Pre-register the hypothesis and expected distinguishing observation. Use matched model, endpoint, output allowances, context information and resource budgets where possible; explicitly label unavoidable differences. Include ungated, no-feedback, public-context-only and generic-revision controls. A gain from more tokens or a stronger model is not system-specific evidence.

Search a finite typed grammar. Deduplicate by operational behavior and message/checker traces where justified, not workflow names. Retain noncommuting orderings and genuinely different feedback/selection policies. Start with inexpensive offline screening, then a small finite pilot, then repetitions and randomized order for promising mechanisms. Distinguish exploration from confirmatory evaluation; freeze choices before new sealed holdouts. Report uncertainty, distributions, worst cases, refusals and cost per correct completed answer, not just one best score.

Useful hypotheses include host-derived exact certificates; proof-carrying intermediate decompositions with semantic bridges; independently sourced counterexamples; uncertainty-triggered verification; checker-guided repair with bounded feedback; candidate diversity measured by failure modes; EIS evidence policies that regulate rather than merely restate a checker; and PCIV selection over independently evaluated portfolios. Test the minimum mechanism first. Explain the mathematical contribution and how its effect could be falsified before expanding combinations.

Each completed increment must deliver code, a precise claim, a meaningful offline check, finite frozen execution if justified, independent grading, four-axis comparison, DAG status, Wiki documentation and a concise commit/PR. Negative results are completed experiments. Do not keep tuning until a positive result appears.

## Migration and remaining audit obligations

Anomalon pilot deletion PR #1572 and follow-up #1573 were merged earlier. The later support migration [PR #1575](https://github.com/dbccpage/anomalon/pull/1575) is recorded merged at `9fadd347e8b7203dcab3f95a4a8d1336bac062c1e`. The destination checkpoint preserves imported pilots, 216 moved Anomalon support files and 84 moved PFP education files, source-path deletions and consumer fixes. 138 stub/trivial pilot folders were retired with recoverable originals; 204 numbered pilots and 17 shared owners received initial triage. Do not re-delete source trees or restore retired stubs accidentally.

The retained pilot corpus is historical source material, not a claim that every pilot runs independently. Some owners need the separate Anomalon runtime. Migration receipts record focused validation and known pre-existing catalog failures; there was no full monorepo replay. Preserve source/destination bytes and follow-up revisions. Do not rewrite old receipts to imply later work happened earlier.

The final `pending_reuse_candidates.json` checked census agreement for all 32,261 rows and byte equality for 487 nonempty duplicates plus 713 empty files. One RuntimeLimits.lean target remains metadata-only at its read boundary. **Zero new semantic coverage credit was granted.** Reuse a full-read anchor only after checking path-specific semantics, consumers, packaging, provenance and modifications. Largest pending groups include certified challenges (5,292), tower evidence (2,905) and Paper011 (1,793). Batch full-population structured checks with explicit limits; avoid opening thousands of identical JSON files one at a time.

Rebuild coverage and DAGs only after a substantive relevant change using `dag/reviews/build_coverage.py` and `dag/build_dags.py`. `additional_*.json` reports with file reviews integrate automatically; automated schema/custody checks must not be called full semantic reading. Do not use generated handoff/test files to inflate the original census. Claim resolution requires evidence, not a renamed status.

## Working cadence and final deliverables

Use at most three worker agents plus a coordinating parent unless the user changes that limit. Reuse the completed ten research reports; do not launch ten new brainstormers merely to repeat them. Give each worker a bounded ownership area and explicit deliverable, stop condition and spend boundary. Keep one writer per shared registry. Use periodic short updates that state measured progress and remaining uncertainty.

Work in bounded increments. Stop a campaign on budget exhaustion, unknown liability, reproducibility failure or unavailable infrastructure; preserve a clear checkpoint instead of retrying indefinitely. Do not spend hours on punctuation, hash churn or repeated unchanged test runs. At each session boundary, commit and open/update a PR, report exact status and unfinished obligations, and leave a continuation artifact. The successful outcome is a defensible comparison of useful workflows, including where they do not help, not the largest DAG or most impressive vocabulary.
