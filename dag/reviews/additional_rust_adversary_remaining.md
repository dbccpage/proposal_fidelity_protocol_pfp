# Rust adversary source review

Completed 99/99 frozen paths, 1,602,171 bytes and 45,350 lines: 33 direct full bodies plus 66 complete owner-prefix/exact-template/all-residual transfers. Zero partial, bounded or pending scoped files. Fourteen independent finite controls passed; no original/native/provider code ran.

This report identifies reusable execution checks and concrete boundaries. It does not establish model performance, task success, physical QM results or production qualification. Full file assessments remain below; the repair priorities focus on executable workflow behavior.

## Immediate workflow implications

- For a concrete experiment, first bind accepted checker receipts to exact task/candidate/policy and keep task acceptance separate from scheduler completion (RAD-F05/F07).
- If DDC metrics/compensation are used as decision evidence, repair complete-step binding, refusal completion and checked accumulation (RAD-F01..F04).
- Use frozen positive-weight epoch binding already present; make progress mean checked improvement/refinement, not mere change (RAD-C01/RAD-F06).
- Route paid work through one actual reservation/unknown/settled controller; copied nested budgets and agent-ID labels are insufficient global controls (RAD-C02/RAD-F08).

## Supported contributions

### RAD-C01: Exact finite predicates are real mechanisms, conditional on admitted encodings.

Primary gates check declared rational matrix dimensions and d1*d0=0, L1 primal/dual feasibility and equality, and lexicographic tie witnesses. Valuation receipts recompute bounded integer weighted residual totals and disposition. run_swarm additionally binds candidate, epoch, ordered probes and weights, and binds the packet epoch at entry. This runtime closes the standalone zero-weight/epoch mismatch concern.

Limits: No native predicate, LP solver, tie verifier or task checker ran. Supplied matrices must still represent the intended carrier/task; a supplied independently_recomputed boolean is not an independent run.

Reuse: Reuse frozen task encoding plus independently recomputed finite residual/certificate checks and explicit candidate/epoch binding. Preserve the distinction between verifying a finite certificate and establishing the encoding.

Evidence: `code/rust/core_adversary/src/primary_gates.rs:365–435`; `code/rust/core_adversary/src/primary_gates.rs:593–727`; `code/rust/core_adversary/src/stage/evaluation.rs:1–152`; `code/rust/core_adversary/src/stage/run_swarm.rs:61–90`; `code/rust/core_adversary/src/stage/run_swarm.rs:415–430`.

### RAD-C02: The active PFP gateway contains substantive reservation and recovery checks.

PfpSeatGateway reserves the full configured output allowance before send, records reservation and settlement delta, validates matching settlement terms, and blocks later sends on unresolved outcomes. It checks nonnegative receipt costs/usage and binds replay provider bytes. These mechanisms are stronger than the separate legacy gateway and than treating an idempotency-key string alone as exactly-once dispatch.

Limits: Source reasoning only. Ledger append is not a demonstrated multiprocess atomic reservation transaction; estimates need a valid upper-bound policy, and actual overruns may already have occurred before refusal. No provider/ledger run.

Reuse: Use the active reserved/unknown/settled state machine for bounded paid experiments, with one dispatcher or an independently enforced atomic lease and reconciliation policy.

Evidence: `code/rust/core_adversary/src/pfp_gateway.rs:54–200`; `code/rust/core_adversary/src/pfp_gateway.rs:227–355`; `code/rust/core_adversary/src/pfp_gateway.rs:357–404`; `code/rust/core_adversary/src/pfp_gateway.rs:449–600`.

### RAD-C03: Canonical records and exact prefix comparison provide useful local custody.

The stage codec closes record fields, normalizes semantic Unicode identity, validates selected bounds and binds record digests. complete_bout compares the entire retained DDC prefix before slicing appended steps. This is stronger than an equal-line-count mirror check.

Limits: NFC identity is a declared semantic quotient, not raw-byte identity. Receipt replay uses the same scheduler and supplied results; consistent replay does not prove model calls or truthful task outcomes. External strict-JSON/JCS dependencies were not newly fully read.

Reuse: Retain exact candidate/request/output hashes and prefix equality as custody stages, while reporting checker truth and transport evidence separately.

Evidence: `code/rust/core_adversary/src/stage/canonical.rs:1–256`; `code/rust/core_adversary/src/complete_bout.rs:114–159`; `code/rust/core_adversary/src/stage/receipt_replay.rs:1–324`.

### RAD-C04: The deterministic scheduler supplies finite choreography under explicit premises.

N=1 composition checks definition/profile/graph/catalog bindings, required operations and declared independent-seat agent disjointness. Unit-cost steps, maximum total steps, dry rounds and visit limits provide bounded choreography for validated inputs. Topology validation closes identifiers and endpoints.

Limits: Units are not dollars/tokens; distinct agent IDs are not independent control or providers. Allowed-status, completion and progress limitations are RAD-F05/F06. Finite terminal labels do not certify objective completion.

Reuse: Reuse deterministic budgeted orchestration as a controller around real task-specific checkers; keep workflow completion and accepted answer verdict separate.

Evidence: `code/rust/core_adversary/src/stage/scheduler.rs:14–161`; `code/rust/core_adversary/src/stage/scheduler.rs:177–211`; `code/rust/core_adversary/src/stage/scheduler.rs:246–364`; `code/rust/core_adversary/src/stage/topology.rs:151–267`.

### RAD-C05: The synthetic diagnostic is a constructed numerical example, with an appropriate nonauthority label.

The adapter forms a mixture of normalized real-vector outer products, applies explicit dimension/spectral policies, and labels outputs DETERMINISTIC_SYNTHETIC_DIAGNOSTIC. Positive mixtures of normalized outer products have a conditional PSD/trace-one foundation. Arithmetic failures become unavailable reports.

Limits: No RNG, eigensolver or NumPy conformance run. Full table reading and census are not a proof of upstream identity or distribution quality. These are text-seeded synthetic states, not physical QM observations, truth scores or evidence of model efficacy.

Reuse: Use only as an explicitly synthetic reproducibility/diagnostic example; do not use its quantum-labelled coordinates as a benchmark acceptance oracle.

Evidence: `code/rust/core_adversary/src/stage/synthetic_diagnostic.rs:1–144`; `code/rust/core_adversary/src/stage/diagnostics.rs:1–58`; `code/rust/core_adversary/src/stage/numpy_rng.rs:1–118`; `code/rust/core_adversary/src/stage/numpy_ziggurat.rs:1–1001`.

### RAD-C06: Research checkpoints preserve declared state consistency under a trusted-host boundary.

Mission/ledger/candidate digest, contiguous event sequence, reservation key-set and occurrence count checks are meaningful local consistency controls. The owner explicitly states that its unkeyed state digest does not authenticate a caller who recomputes it.

Limits: Resume does not replay every transition/payload or establish terminal truth. Successful host checks and evidence references remain supplied observations. Source-only review does not replace OS isolation or actual checker execution.

Reuse: Use checkpoints for crash recovery within a trusted controller; obtain task truth from separately bound checker outputs and do not promote restored terminal labels into proof.

Evidence: `code/rust/core_adversary/src/research_loop/state.rs:964–1066`; `code/rust/core_adversary/src/research_loop/budget.rs:1–384`; `code/rust/core_adversary/src/research_loop/invalidation.rs:1–143`.


## Findings

### RAD-F01: DDC step-chain hashes omit metrics and timestamps.

The step hash input contains class/carrier/witness/receipt labels but excludes phi_1, gamma_2 and timestamp. Two admitted steps with identical included fields and different metrics therefore have the same prehash input and head while producing different metric histories. State hashes also hash class labels rather than state bytes.

Limits: An omitted-field projection, not a SHA collision or a demonstrated historical tampering event. A separate immutable full receipt may supply the missing binding, but this head alone does not.

Next action: Before using the tape head to bind evaluator results, hash the complete canonical step including metrics and time/policy semantics or explicitly bind a separately checked full-step digest.

Evidence: `code/rust/core_adversary/src/stage/ddc_tape_evaluator.rs:519–595`; `code/rust/core_adversary/src/stage/ddc.rs:1–52`.

### RAD-F02: Compensation heads bind branch ID and count rather than branch contents.

record_compensation_branch checks authority and nonempty class labels, but the hash record includes only branch_id and step_count alongside chain metadata. Different branch tapes of the same length can share a head in separate histories; branch DFA validity is not checked here.

Limits: Duplicate IDs within one evaluator are refused. The finite counterexample concerns two histories and does not claim a hash collision.

Next action: Bind the complete ordered compensation steps and run the intended dialect/adjacency checks before treating a compensation head as evidence of the branch.

Evidence: `code/rust/core_adversary/src/stage/ddc_tape_evaluator.rs:717–779`.

### RAD-F03: OEARS terminal refusal conflicts with complete-tape admission.

The OEARS M rule permits no following token, while complete validation requires the final token T for every dialect. M is a valid refusal prefix, M is incomplete, and M T is rejected. Thus no completed OEARS tape can contain that terminal refusal.

Limits: Exact contradiction in the inspected rules; no Rust execution. Legacy M T semantics differ and are not covered by this counterexample.

Next action: Choose one explicit OEARS completion rule for refusal and align complete validation, terminalized state, replay and tests with it.

Evidence: `code/rust/core_adversary/src/stage/ddc_tape_evaluator.rs:133–166`; `code/rust/core_adversary/src/stage/ddc_tape_evaluator.rs:236–276`; `code/rust/core_adversary/src/stage/ddc_tape_evaluator.rs:785–813`.

### RAD-F04: Exact per-step metrics do not guarantee exact bounded window arithmetic.

Metrics are reduced to Rational64 individually, then sliding-window sum/mean uses unchecked Rational64 additions. Two individually representable i64-max integer metrics already require an unrepresentable sum. Missing metrics also enter history as zero, which conflates unavailable and measured zero for these summaries.

Limits: Exact arithmetic representability control only. Compiled dependency overflow behavior was not run; the report does not choose panic or wrap as the observed result.

Next action: Use arbitrary-precision accumulation or checked arithmetic with an explicit refusal, and retain unavailable metrics as unavailable.

Evidence: `code/rust/core_adversary/src/stage/ddc_tape_evaluator.rs:497–517`; `code/rust/core_adversary/src/stage/ddc_tape_evaluator.rs:578–645`.

### RAD-F05: Scheduler status and completion are not enforced task outcomes.

SceneSpec validates allowed_result_statuses, but scheduler.advance checks scene identity without checking membership in that set or assigned producer identity. A terminal scene becomes COMPLETED for any non-stop status: with allowed PASS and empty stop list, an incoming HOLD becomes COMPLETED. Continuation halt similarly marks any nonempty history COMPLETED. complete_bout uses a fixed PASS/changed_state=1 completion input for traversal.

Limits: These are choreography labels; they may intentionally mean run termination. They must not be consumed as accepted-task evidence. Stronger receipt bindings elsewhere do not change this transition predicate.

Next action: Enforce declared scene/producer admission and separate terminated, halted, exhausted and task-accepted states in executable experiment accounting.

Evidence: `code/rust/core_adversary/src/stage/topology.rs:82–115`; `code/rust/core_adversary/src/stage/scheduler.rs:246–270`; `code/rust/core_adversary/src/stage/scheduler.rs:309–343`; `code/rust/core_adversary/src/stage/run_swarm.rs:33–58`; `code/rust/core_adversary/src/complete_bout.rs:421–483`.

### RAD-F06: Residual worsening can reset the no-progress counter.

run_swarm sets refined_residual=1 whenever post_residual differs from pre_residual. For residual1 to2, delta is positive and status HOLD, but progressed is true and scheduler dry_rounds resets. The oscillation detector also receives that positive progress signal.

Limits: Total step/unit and visit bounds remain; this is a stagnation semantics defect rather than an infinite-loop claim.

Next action: Define progress against a task-preserving ordered residual or a separately checked refinement relation; record mere change independently.

Evidence: `code/rust/core_adversary/src/stage/run_swarm.rs:138–159`; `code/rust/core_adversary/src/stage/run_swarm.rs:183–207`; `code/rust/core_adversary/src/stage/scheduler.rs:325–331`; `code/rust/core_adversary/src/stage/run.rs:1–66`.

### RAD-F07: PASS_TO_MASTER publication checks verdict without binding the current task/candidate.

skill_run parses a checker receipt and requires Accepted for PASS_TO_MASTER, but does not compare its candidate content digest/optional candidate ID with the current task, objective or selected candidate. The checker parser itself supplies those identity fields; publication retains them without establishing the relationship.

Limits: No forged receipt or filesystem publication was executed. This is the standalone writer boundary; a correctly binding caller can supply the missing assurance.

Next action: Require an exact task/candidate/checker-policy binding and successful task-specific receipt validation before publishing an accepted answer.

Evidence: `code/rust/core_adversary/src/skill_run.rs:187–215`; `code/rust/core_adversary/src/skill_run.rs:267–317`; `code/rust/core_adversary/src/skill_run.rs:375–394`; `code/rust/core_adversary/src/evidence_parse.rs:90–163`.

### RAD-F08: Nested dialectic budgets are local copies, not a conserved experiment budget.

AdversaryMachine.nest opens a child with the unchanged parent remaining budget. Two children of a100 budget can each spend60 under their local checks. This is valid local accounting but exceeds a shared100 experiment cap.

Limits: The separate active PFP gateway has reservation/recovery mechanisms (RAD-C02); this finding must not be generalized to that ledger. No provider spend occurred.

Next action: Document local budget scope or reserve each child allocation from one shared controller before any live dispatch.

Evidence: `code/rust/core_adversary/src/dialectic.rs:166–194`; `code/rust/core_adversary/src/dialectic.rs:282–309`.

### RAD-F09: Generic boundary trailers do not establish production qualification.

Sixty-nine complete matching trailers instantiate the same bounded-count mechanism after nominal origin/claim/identifier substitutions. Their tests exercise count admission rather than the enclosing carrier, scheduler or provider algorithm. Other trailers construct Ok/Err directly. Mutation-accounting comments therefore cannot establish the claimed production mutation campaign from these bodies.

Limits: All distinct owner prefixes and every template residual were reviewed. This does not imply all meaningful tests elsewhere are absent; separately referenced test targets were not run or granted reading credit.

Next action: Keep finite count tests as count tests. Qualify actual workflow predicates using bound negative controls and real task failures; do not use trailer counts as experiment success evidence.

Evidence: `code/rust/core_adversary/src/act_capture.rs:71–187`; `code/rust/core_adversary/src/dialectic.rs:952–1074`; `code/rust/core_adversary/src/stage/synthetic_diagnostic.rs:146–162`; `code/rust/core_adversary/src/stage/mod.rs:122–137`.

### RAD-F10: Response-schema numeric semantics need an explicit dialect contract.

The local integer type admits values representable through as_i64/as_u64, and number equality compares rendered strings. Mathematical1 and1.0 can therefore differ, and larger exact integers are outside that integer predicate. Regex and local-ref handling are also a deliberately restricted implementation.

Limits: No external schema validator or serde runtime was invoked. This is a concrete language-boundary review, not a claim of whole-standard conformance failure.

Next action: Freeze the supported numeric/ref/regex dialect for provider outputs and test equivalent numeric encodings against it; avoid presenting the subset as interchangeable with every schema evaluator.

Evidence: `code/rust/core_adversary/src/research_loop/response_schema.rs:338–361`; `code/rust/core_adversary/src/research_loop/response_schema.rs:472–512`.

### RAD-F11: Carrier and matrix admission do not establish the intended topology automatically.

Public Network::new checks edge endpoints but accepts faces without their boundary. The JSON parser is stronger. Separately, primary gates verify declared matrix algebra without reconstructing incidence matrices from the supplied carrier. Thus algebraic witness acceptance needs an explicit encoding relation to the intended complex/task.

Limits: The direct constructor witness does not bypass the stronger JSON parser. Valid declared matrices can support a correct finite theorem even when their application interpretation remains unproved.

Next action: Centralize validated complex construction and bind/recompute oriented incidence matrices from that carrier before using cohomology or LP certificates as task evidence.

Evidence: `code/rust/core_adversary/src/carrier.rs:124–149`; `code/rust/core_adversary/src/carrier.rs:721–762`; `code/rust/core_adversary/src/primary_gates.rs:365–435`; `code/rust/core_adversary/src/primary_gates.rs:688–727`.

## Prior evidence reconciliation

OAR-F06: PFP gateway now reviewed here has explicit reservation/unknown/settled accounting; the prior finding concerns the separate Python researcher dispatch path. Do not equate those owners or claim the Python crash window is repaired.

OAR-F14: Rust complete_bout compares an exact DDC prefix. This is a different owner/buffer from the Python event mirror that only counts lines; stronger Rust behavior does not retroactively repair the mirror.

OAR-F21: Rust local valuation receipt alone leaves epoch semantics external, but run_swarm compares candidate/epoch/probes/weights. This preserves the earlier distinction between a local DTO and its stronger orchestration boundary.

OAR-F23: Fixed completion inputs persist in native complete_bout; the deterministic scheduler is real bounded choreography, while task acceptance remains a separate checker result.

## Coverage and limits

- All 99 frozen source bodies are covered: 33 directly and 66 by complete owner prefix plus exact pinned template and all residuals. No partial/bounded/pending scoped file remains. Full source reading does not constitute a proof of every table value or external dependency.
- Fresh execution is limited to 14 standalone standard-library finite controls. No original modules/functions, native/Cargo/tests, retained provider runners, credentials, network or private benchmark were accessed/executed.
- Cargo explicit external test targets, included YAML/JCS/strict-JSON/runtime helpers, linear-algebra/eigensolver owners and OS/native implementations were not newly fully read in this slice. Prior source reviews remain separate evidence; includes/imports confer no credit.
- No live performance, scientific utility, paid-spend bound under arbitrary concurrency or deployment isolation claim is made. Historical comments and stored outcomes are not fresh tests.
- Only this audit prefix was written. No production repair or source change was made. This scope is frozen; no new scope was started.

## Per-file assessments

### code/rust/core_adversary/Cargo.toml

SHA256 `f2485a31f19f5679db62d8f7f95a2d70be0e4555889ef4b81e5ab58a26855f1a`; complete lines 1–280; full_raw_source_body_review.

Complete Cargo manifest read, including every explicit test target. autotests=false is paired with named shared integration targets; dependency declarations expose exact rational/big-integer arithmetic, JSON raw/arbitrary precision, canonical hashing and blocking HTTP capability. These are dependency/target declarations, not executed test evidence or dependency-body review. The named parity/falsification/provider tests were not read or run in this scope; no Cargo command was executed.

### code/rust/core_adversary/src/act_capture.rs

SHA256 `168256c36ade76b540701f027d1a8f002fd88bdaf099d4fcabdbc42ba5378f13`; complete lines 1–187; full_raw_source_body_review.

Reply provenance preserves missing model/provider as NOT_REPORTED and records supplied parameters/usage/request digest. Candidate-list witness representation is a quoted list of admitted lowercase SHA IDs, with checked usize arithmetic independently compared to rendered length. That consistency check does allocate the rendered list, so it is not a preallocation resource ceiling. Full generated trailer and five input-case test read: it establishes only 1<=count<=capacity and saturating remaining count, not enclosing L4 production adequacy or the commented six killed mutants.

### code/rust/core_adversary/src/algorithm_metadata.rs

SHA256 `6c3ef12ea7972b2fe19fab1bbda00a93d62accdcaf9b6526892df43ea03b149b`; complete lines 1–216; full_raw_source_body_review.

Exact metadata validator admits canonical nonnegative rational strings or paired nulls; measured statuses require degree one, both phi/gamma measurements, and exact equivalence between both-zero values and ZERO_ON_DECLARED_CARRIER. Trace hash is syntax-only optional provenance. This checks cross-field declarations, not that supplied cochain values were computed from a carrier, nor a global-cover theorem. Full generated boundary-count trailer read; its template test does not independently validate the cochain metadata owner.

### code/rust/core_adversary/src/authorization.rs

SHA256 `dfaca7ee3d5706d867c606e87aa20fe096c4a98b431b2dbc728b1d666a09b419`; complete lines 1–754; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Full authorization algorithm read plus exact generated-trailer transfer. The gate binds selected candidate/check content refs, requires a NON_BLOCKING critique label, distinguishes declared/unmeasured/open carriers, protects contexts, keeps ablated/fixture outcomes non-authorized, and authorizes only the AUTHORIZED branch. It explicitly delegates authenticity/reproduction of checker facts to the preceding use case. It chooses the first unblocked candidate, not the first fully checked one; critique-verdict strings and measurement context remain supplied premises. Ablation flags use Python truthiness, including nonempty false-like strings. Candidate selection remains authority None. Several emitted DDC carrier hashes are the constant hash of carrier rather than the actual carrier; event_kind may say TERMINAL while terminal flag is false, which requires downstream interpretation. Generated count-template does not strengthen these operational claims; no gate/emitter was executed.

### code/rust/core_adversary/src/bin/adversary_dialectic.rs

SHA256 `de696fc40be6a954d0f6377e99cbeceb5d7868a83145dfce0f71dcdb7ef3deea`; complete lines 1–226; full_raw_source_body_review.

Complete binary source and inline tests read. Stdin budget uses checked addition/subtraction and a fixed 65536-byte retained-input bound, with distinct status exit0/1/2 and output/transport exit3; reading may consume an entire extra8192-byte chunk before refusal. All read failures collapse to unit error and main reports INPUT_TOO_LARGE even for ordinary I/O error, so refusal cause is not preserved. Inline test verifies fixed exit-map/budget shape; the additional Ok/Err mutant test is a tautological status example, not mutation-campaign evidence. No binary/stdin/native execution.

### code/rust/core_adversary/src/bout_auxiliary.rs

SHA256 `fb5ed5f13074db28d738f22dbed2e10f54cb741c40cd74e483a63ed8dcafecce`; complete lines 1–323; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Epistemic sieve chooses the first matching candidate content and computes an injected synthetic diagnostic, with explicit narrative that diagnostics are not verification. Sandbox sends a seat prompt and records disposition/excerpt while explicitly denying independent safety verification; candidate bytes/context are supplied and no host checker is invoked here. Crystallization maps terminal declarations to nonauthoritative capture/reentry states and optionally records generic genealogy guidance. Concrete hooks exist, but completion/learning efficacy is not measured. Prefix fully read with exact generated-count-trailer transfer; no seat/provider/sink execution.

### code/rust/core_adversary/src/bout_boundary.rs

SHA256 `5d748931fd528160ebfb825db153dbbe13f98020e159270ea17556e48bcaf5ee`; complete lines 1–368; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Bout boundary wraps injected acts with start journaling, capture, panic/interruption classification, optional refusal-bundle persistence and explicit final journal residuals. Start append failure prevents acts, while missing optional journal permits an unjournaled run. Completion append failure is retained separately even if result is Ok, so consumers must not discard journal_residuals. Interruption returns captured turns but does not enter refusal-bundle persistence; repeated residual detail keys can overwrite one detail while the vector preserves all. Useful custody orchestration, not the seven-act algorithm or proof of external exactly-once execution. Prefix plus complete generated-template transfer read; no acts or ports invoked.

### code/rust/core_adversary/src/candidate_checks.rs

SHA256 `91ab030c782504fa0ebb336faf46d02466c5638cf6b8fbc7bef8de540d704199`; complete lines 1–255; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Candidate checking requires exact candidate payload bytes, verifies their SHA is a committed artifact, calls an injected checker, and rechecks candidate ID/artifact/content digest afterward. Missing checker becomes a typed NOT_MEASURED result, not acceptance. Audit emission requires a supplied measured-carrier digest and uses an R audit step rather than promoting ACCEPTED to an E repair. The input map/digest labels do not authenticate a checker implementation or bind objective/run intrinsically; repeated candidate IDs overwrite result-map entries after repeated checks unless excluded upstream. Prefix plus complete generated trailer reviewed; no host checker/emitter called.

### code/rust/core_adversary/src/candidate_proposals.rs

SHA256 `6feb30c6292aea0aee2c062dfe4111fd1ab9c9db93072092ceb2a4913986a61a`; complete lines 1–448; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Proposal generation preserves exact payload bytes inside one optional candidate fence, refuses multiple/malformed/nested candidate fences, and otherwise uses the complete reply verbatim. Candidate artifact SHA and request-ID/NUL/raw-response receipt binding keep proposal content separate from generation metadata. Cheap gates only reject empty response or non-None authority and retain failure headstones; they do not prove candidate correctness. Budget is an i64 loop bound with no local positive/cap admission: negative yields zero calls, large positive delegates resource safety to the caller/provider layer. Carrier audit field is a constant placeholder hash. Full prefix plus exact generated count-template transfer; no seat/provider/cemetery execution.

### code/rust/core_adversary/src/carrier.rs

SHA256 `5cb056534268193631a8a777a2124c442f370172b5bb3346b11049dad1e2ff96`; complete lines 1–1096; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete979-line carrier algorithm prefix read and exact117-line generated trailer transferred. JSON admission checks finite node/edge distinctness, unoriented duplicate edges/faces/cells, boundary closure through tetrahedra/4-simplices, and exact rational cochains with orientation sign reversal and explicit zero-fill counts. It preserves Python-like literal aliases including bool/finite-float cochain keys using numeric equivalence, while admitted node JSON is int/nonempty-string. The public Network::new only checks edge endpoint membership and bypasses parser face/cell/duplicate invariants; those invariants are entry-point specific. Iterable coercion accepts string characters/object keys; permissive cochain-key fallback and duplicate-map handling require canonical input/caller policy. No topology or scoring theorem follows from admission, and the Numerical profile comment does not describe the exact cochain computation. External Integer/rational/Unicode owners remain dependencies. No parser/scorer executed.

### code/rust/core_adversary/src/carrier_digits.rs

SHA256 `4c4d4d7861b79dc62f36e7d254d29250b06bb64f7ffe1d8c50765269bca67ad5`; complete lines 1–179; full_raw_source_body_review.

Full Unicode decimal table, binary-search digit lookup, separated-base/ASCII tests and generated count trailer read. The finite ordered nonoverlapping zero-base table maps each listed ten-codepoint block to0..9 with checked indexes/subtraction. Its frozen Python15.0 Nd provenance is a source claim, not freshly verified Unicode completeness. The main carrier currently uses a separate linear lookup over the same table, so this binary function test does not establish runtime parser coverage. Generic count test/mutation comment remains independent of digit semantics.

### code/rust/core_adversary/src/carrier_framing.rs

SHA256 `e8c66137ad42b9a7c53fd4b2a5bcce6cce02287f4bf872effa371a1de4ce5091`; complete lines 1–262; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Carrier framing parses the carrier before optional history and synthetic diagnostics, preserves declared/undeclared status and explicitly reports zero-filled edge count. History load failures are intentionally suppressed to empty history, so no-antibodies and failed-history are observationally conflated. The emitted DDC carrier hash is a constant hash of carrier, not a binding to parsed topology/cochain. Synthetic SBE is delegated and not a mathematical correctness claim. Outcome exposes status directly and in narrative while top-level to_dict omits its dedicated field. Prefix and exact generated trailer fully covered; no history or diagnostic calls.

### code/rust/core_adversary/src/checker_ports.rs

SHA256 `8e740fb67789fdaa51d09e9595b6f23495999aca99921fae6c37fbad83da76ac`; complete lines 1–155; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

CandidateCheckerPort is an injected checker interface over run/objective/candidate bytes/context. NullCandidateChecker faithfully returns NOT_MEASURED with the actual supplied byte digest and no receipt, preserving absence rather than manufacturing a pass. Concrete correctness/authentication belongs to bound host implementations. Full prefix plus exact generated count-template transfer; the trailer does not implement or qualify a checker and no checker call was executed.

### code/rust/core_adversary/src/complete_bout.rs

SHA256 `7de8f0b8f7c51376284b9c693593623665da4c00c73d3febaf2aa164cb537769`; complete lines 1–1572; full_raw_source_body_review.

All1572 lines read, including substantive DDC custody and scheduler-order tests. Seven-act controller binds candidate bytes/checker observations, requires configured DDC sinks to expose the tape, snapshots exact prefix and rejects any changed prefix/presence before persistence. This is stronger than length-only mirror checks. Higher-carrier remeasurement refuses decreases in either exact obstruction statistic under the declared lift assumptions. However ground_truth_admissible=false skips post-lift measurement while later audit hashes use the lifted carrier, leaving old measurement versus new carrier binding dependent on that caller policy. Scheduler finalization synthesizes fixed PASS/changed_state1 and a hard-coded work-packet ID, precharges seven steps with saturating subtraction, and trusts an optional initial_state without local packet identity validation. Scheduler/scene owners still need assessment before end-to-end conclusions. Publication failure is explicitly retained separately without changing task outcome and strips receipt pins; no retained ports run. Inline test/mutation comments are source evidence only.

### code/rust/core_adversary/src/council.rs

SHA256 `8a4570c8c8a1ed4a6473b45f6f13ae5b7d743a9490d20c5b4b7bbb8c2d81d56a`; complete lines 1–604; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Council assembly reads YAML string-keyed maps, rejects normalized seat-name collisions, builds finite seat/scene/transition/plan records and hashes both original YAML bodies with domain and length framing. Input scenes are checked only for ten unique normalized IDs; their contents are otherwise discarded in favor of compiled layout. Core-seat insert uses or_insert, so an existing same-ID declaration with a different inferred trust domain is retained: one-seat-per-trust-domain wording is not locally enforced. Roles are inferred by substrings/iterable acts, independence lists are empty, and the generated license hash is a proposal identity, not an authenticated capability. Core mode transparently maps seatless acts to the evaluator; full wrapper intentionally retains legacy full mode. Prefix plus exact count-template transfer; no YAML loader/scheduler execution.

### code/rust/core_adversary/src/council_layout_v1.json

SHA256 `7c10b1f5caafcfd8929860031f55481801388bb564e32dc7c2aef4b922299db7`; complete lines 1–314; full_raw_source_body_review.

Full314-line raw JSON body read. Eight core-required seat descriptors, seven act-scene descriptors, eight transition records, and one source_sha256 field define a finite narrative workflow. Roles/cognitive-operator names are declared labels rather than independent agents or mathematical checkers. Scene visit maxima/status lists and explicit terminal act7 are concrete scheduling inputs, conditional on the scheduler consuming them. The source hash is an unverified external provenance label; no source reconstruction or historical efficacy is inferred. Compiled layout use means the separate ten-scene YAML admission is not itself this graph.

### code/rust/core_adversary/src/custody.rs

SHA256 `f1f7b3d89d1494c12dd03ea910cedc3546c4a0be3d10ff26bc1239f0746104b2`; complete lines 1–395; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

RecordingSeatPort adds reviewed plan/guidance and explicitly untrusted historical scene observations before computing request digest; scene context has64-record/64KiB caps. A configured journal must append SeatTurnStarted before the inner call, but checkpoint failures merely accumulate residuals and missing journal is an admitted mode. Returned replies with a supplied mismatching request digest are rejected; absent reply digest is accepted, so response binding is conditional on the concrete port. Reply/raw bytes and failure paths are preserved in turn records, interruption resumes unwinding with pending state for recovery, and completed-journal failure is reported separately. Prefix fully read plus exact count-template trailer; no seat/journal/provider invocation.

### code/rust/core_adversary/src/dialectic.rs

SHA256 `4424c17439ebce061c1fac7ae8abf5178614e2fc8c29593657064faa1d8b5415`; complete lines 1–1074; full_raw_source_body_review.

All1074 lines directly read, including the full generated trailer. Dialectic kernel is explicitly separate from the live runner: seven ordered acts, unique lexical seat labels, depth<=5, exact Ratio<i64> budget debit, closed wire records and complete replay of stored budget/turn/evidence identities. Arithmetic checks refuse intermediate overflow even if a reduced mathematical result might fit; this is a conservative representation domain. Nest clones the full remaining budget without debiting the parent, so depth-bounded local accounting does not bound aggregate sibling spend. Seven valid declarations can finish PASS with zero spend and arbitrary well-formed subject hashes; sealing checks self-consistency, not underlying evidence or independent seats. Public state/receipt records can be manually constructed but restoration enforces the replay constraints. No original kernel/native run; JCS/literature dependencies remain separately pending.

### code/rust/core_adversary/src/evidence.rs

SHA256 `f8d5de62902602c0540f7b71241b8879c801ae83046e03649b1c2182a845dd5b`; complete lines 1–535; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete evidence owner prefix plus exact generated template read. BigRational parsing rejects floats/bools and nonpositive denominators, while normalized string spellings may differ from raw input. Measurement records require nonnegative phi/gamma and declared verified-certificate flag for MEASURED, align defect count with listed obstructions, and keep NOT_MEASURED value/certificate absence explicit. They do not verify a dual witness or bind a carrier, as the module correctly states. CandidateCheck requires nonempty receipt bytes and their exact hash for accepted/rejected verdicts and binds candidate/content refs, but does not parse receipt semantics, authenticate checker identity or bind run/objective; concrete ports own those obligations. Exact-zero status can coexist with declared active-obstruction labels absent additional semantics. No original check executed.

### code/rust/core_adversary/src/evidence_parse.rs

SHA256 `e8680eb8d38ed7a2b7d32ae1bee60b9c43ddb3fb01ec3c0f72ea9bd29ad704ad`; complete lines 1–427; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Full parser prefix plus exact generated trailer read. Checker-receipt parsing admits closed verdict vocabulary, content-digest shape, nonempty checker ID and optional candidate ID, while leaving authentication/reproduction explicitly external and allowing extra fields. Structured critique requires exactly one matched fenced JSON block, exact bool, closed kind and nonempty counterexample for blocking; malformed input is blocking. Direct StructuredCritique::new does not enforce the parser counterexample requirement for Structured+blocking, an entry-point distinction. Plain Value JSON loading does not implement an explicit duplicate-key refusal at this owner; outer screening must be assessed before any end-to-end claim. A nonempty counterexample string is not its mathematical validation. No parser/provider run.

### code/rust/core_adversary/src/exact.rs

SHA256 `ab7dc2998dd3a17b9a2f38347e937db6a9e9cf035f53b836bcc0bd84a11717f6`; complete lines 1–146; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete29-line exact-integer owner and exact generated count-template trailer covered. Integer serializes BigInt as a JSON Number and deserializes only values representable as integer number text, rejecting bool/string/float shape through its helper. Arbitrary-precision dependency semantics and any special Value-deserialization representation remain external premises; source labels do not themselves prove a closed raw-wire integer grammar. No native/serde execution or claim of algorithm efficacy.

### code/rust/core_adversary/src/gateway.rs

SHA256 `f6a0923ef220a5caffecd1de464a3464b51d17973af95ab0b36c9b5b988b0286`; complete lines 1–807; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete684-line gateway owner prefix plus exact generated template. Ordered fallback attempts retain byte-bound machine rejections, reject every observed non-None authority declaration before duplicate fields collapse, and reject explicit truncation. Machine syntax validates required keys and residual colour but does not itself validate all disposition/DDC labels or factual statements. Legacy spend admission reserves min(max_output_tokens,reserve) while send still uses max_output_tokens, so the reserve is not a hard worst-case cap. Usage token integers are not constrained nonnegative; malformed transport/JSON replies become zero-cost TRANSPORT_ERROR and their raw bytes are not retained here. There is no durable hold before send in this owner. PFP gateway is a separate pending owner and must not inherit these conclusions without comparison. Exact decimal receipt cost rounds upward to microusd; external pricing/provider truth remains an assumption. No original call executed.

### code/rust/core_adversary/src/gauge_break.rs

SHA256 `72a59b9daf0a4c667efdd2fd48fc3207f6bd8d3d2ac614fde3c115525d0b0566`; complete lines 1–422; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete299-line gauge-break prefix plus exact template. Finite lift chooses a fresh integer node >=9, adds edges to endpoints of the first two original edges and corresponding triangles, retains old cochain values and sets new edge values to zero. This is a concrete combinatorial extension, not a gauge equivalence or semantic prompt-preservation theorem: a nonzero old edge can acquire nonzero coboundary on its new triangle. Trigger uses measured obstruction and either fewer than two candidates or L1 diagnostic delta<1/20 for only the first two candidates. Optional model response contributes only a raw-byte hash, not the actual lift. DDC carrier tags are hashes of fixed words rather than the constructed network. Existing complete_bout post-lift remeasurement is relevant; its caller-controlled skipped remeasurement remains a separate boundary. No diagnostic/model/native call executed.

### code/rust/core_adversary/src/independent_witness.rs

SHA256 `8265d779cec3dad12478b01b9dbe9567b7ddc62bcf55b5d790bfa99a100bb0ac`; complete lines 1–542; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete419-line independent-witness prefix plus exact template. Candidate payload hash must match artifact refs before critique, raw replies and NOT_RUN verification status are retained, and malformed critique is blocking. One selected lexical critic identity does not establish evaluator independence. A blocking critique plus machine DISPOSITION=KILL removes one candidate and records its exact content hash; non-killing rounds stop early. KILL is absent from the gateway prompt suggested disposition set but the gateway parser does not enforce that set, so the path exists though instructions differ. Verdict map overwrites by candidate ID and final critique; rounds below zero produce none. Nonempty counterexamples are declarations, explicitly not validated here. No provider/source execution.

### code/rust/core_adversary/src/instruction_plan.rs

SHA256 `1eec43b6e097cc38dbb5087cfe6e39007ce836f01c55291bdfbc96a7620de361`; complete lines 1–290; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete173-line instruction transport prefix plus exact template. Validates bounded nonempty ordered bodies, byte census <=65536, source tuple ordering/uniqueness, lexical source allowlist, no-authority label, exact body hash with domain and length framing, and exact source-list snapshot digest. Manifest/selection/plan digest fields are only shape checked: signed admission and actual source/body correspondence belong to the host as the documentation says. Operation IDs need not be unique and are positional labels. Public fields/deserialization permit unvalidated construction; prompt_block does not itself call validate, so callers must perform admission. Reusable mechanism is bounded ordered instruction custody, not authority or task-equivalence proof. No host or plan executed.

### code/rust/core_adversary/src/intergates.rs

SHA256 `6477b98cc5a4554110233fa55269f043419d85afe7dafc2cd67114ca4e33cc8c`; complete lines 1–900; full_raw_source_body_review.

All900 raw lines read, including generated count trailer. Ten legacy diagnostic predicates implement exact rational thresholds, lexical phrase/section checks, declared isolation/descent booleans and unique reviewer IDs/seeds. A terminal receipt is duplicate-key screened and bound to candidate bytes, but checker authentication remains explicitly external. Repeated-edge history plus false descent produces DIVERTED with literal holonomy_norm=1; this is a finite loop heuristic, not a computed connection/holonomy invariant. Legacy optional profile delegates to stronger source contracts. Payload depth/node/text/byte limits are real post-parsing checks; raw outer duplicate-key custody belongs to caller. Computational-Profile floating-point wording does not match the exact decimal predicate implementation. No inline test or original evaluator executed; no source YAML reread credit.

### code/rust/core_adversary/src/intergates_source_contract.rs

SHA256 `b1d89fc14253ce9d7aa037fc29274dbce6f7b3b934599fd95195b3b55c201595`; complete lines 1–1347; full_raw_source_body_review.

All1347 raw lines read, including measured-profile tests and distinct trailer. Source-contract gates add actual finite bijection inverse checks, exact supplied before/after/rollback byte equality, ordered prior-round requirements, dissent retention, two distinct configured signing keys and candidate/task/spec-bound signatures via EIS dependency. Equal finite sizes plus inverse[forward[i]]=i is a sound finite bijection condition; it proves no semantic isomorphism of prompts. TrustPolicy, expected binding, source digest and observations are payload inputs, so host selection/authentication and detector truth remain premises explicitly scoped by the module. V2 separates absent top-level observations as HOLD from wrong types/hex as BLOCKED and preserves complete early repeat/bypass negatives; nested trust/witness dependencies are still resolved by V1 and may BLOCK when absent. Lexical urgency deletion can remove caller-specified arbitrary text and is not task-preserving by itself. Scar/context distinctness and signed repair statements do not prove efficacy or probabilistic independence. Generated count tests do not certify these gates; substantive inline tests are read but unexecuted. No EIS signature verifier execution or new dependency full-read credit.

### code/rust/core_adversary/src/jcs.rs

SHA256 `bf1c72621e9c6d1a0aaa1cec3649a16d48e3677f3cbf37fb7c5b5094d73d88b9`; complete lines 1–179; full_raw_source_body_review.

All179 raw lines read. Local JCS wrapper includes external ../../jcs_subset.rs and declares 65536-byte, depth32, node4096 limits. DialecticLimitEnvelope checks positive bounds and checked twice-depth <= byte budget, but stores only max_bytes and is not itself the parser or a proof that all permitted combinations fit simultaneously. Two local tests cover fixed envelope acceptance and a depth-byte rejection; repeated L4 counter tests add no parser coverage. Included shared source is a dependency, not newly full-read by this receipt; RFC8785-subset behavior is conditional on that implementation. No Rust parser execution.

### code/rust/core_adversary/src/journal.rs

SHA256 `4b8cc01ab673bc778b767043c6b21bfadbc621ec6c231ca7afac79c92a7f9891`; complete lines 1–273; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Full156-line journal prefix plus exact template. Defines write-ahead event/status vocabulary, optional no-op checkpoint hooks and ordered unterminated-bout inventory. It groups solely by bout ID, subtracts aggregate completed turns from starts with saturation, and considers any terminal anywhere in history sufficient: it does not validate sequence, task consistency, request pairing or start/terminal temporal order. Reusing a bout ID after a terminal can therefore hide the later start in this inventory. This is useful conservative bookkeeping only under unique bout IDs, single writer and valid event-order premises. Public entry fields and detail-map collapse are not authenticated log semantics. No journal run.

### code/rust/core_adversary/src/journal_store.rs

SHA256 `b75d1152ac726196f4ba64fcf7b2bc6e89ddc054634922281efc0c97c0051b0a`; complete lines 1–248; full_raw_source_body_review.

All248 raw lines read. JSONL adapter appends newline-separated records, flushes and syncs the file, and preserves malformed UTF8/JSON/unknown-kind lines as hash-labelled unreadable entries. Parser deliberately coerces legacy nonstring metadata and defaults sequence, ignores malformed detail pairs and source authority_effect, and does not reject duplicate object keys or enforce sequence monotonicity. read_all loads the entire file; no hard data bound or concurrent-writer lock is present. File fsync is not a directory-creation durability proof. The appended mutation test merely checks constructed Ok/Err values and never exercises this store. No file adapter invoked.

### code/rust/core_adversary/src/kernel_observation.rs

SHA256 `2d23ceee9a9e538303365dbc332b88581bfb46bccef9b39c326d3771b59b2808`; complete lines 1–965; full_raw_source_body_review.

All965 raw lines read, including substantive fixture-process tests. This owner authenticates an EIS observer statement over exact source/context/record bytes, checks fixed extraction/harness/package manifests, exact three process commands or a valid failed prefix, ordered timestamps, captured stream hashes, observed toolchain text, and replays source/axiom audit through pfp_runtime. It does not launch Lake here or independently prove the captured execution; authenticated host truth, selected trust policy, audit parser and runtime/binary environment remain premises. Exact empty axiom policy is enforced separately from the older auditor default. Failures explicitly mean submitted-certificate failure rather than theorem falsity, and output says sandbox_verified/general_theorem_verified=false. Receipt objective digest is only shape checked; task meaning is represented by host-selected declarations/context, not inferred from that digest. Required statement strings are host inputs, not a closed Lean syntax admission. Native audit/signature dependencies and inline fixtures were not executed or newly granted full dependency reads.

### code/rust/core_adversary/src/ledger.rs

SHA256 `0ab748fc751a11b2419a3d4ac799fcd49920ad012cc30f07d992c129c5db8b91`; complete lines 1–197; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete80-line ledger prefix plus exact template. Appends JSONL with sync_data and exposes strict-json records for the stronger PFP budget owner. Legacy spent_on independently uses permissive Value parsing, counts only integer costs with matching day, accepts negative integers and silently skips missing/noninteger costs; it is not an authenticated accounting total. Partial trailing lines are not separated on append, unlike journal_store, so a torn line can contaminate the next record and fail later reads. No concurrent locking/transactional reservation is present in this owner. No actual ledger read/write invoked.

### code/rust/core_adversary/src/lib.rs

SHA256 `46cf5ba91b9c076424bd87908d88da1ae1e19061f75fdbe7947d8991316448e4`; complete lines 1–121; full_raw_source_body_review.

All121 raw lines read. Module exports define composition surface. BoutGateWitness admits a nonempty <=u32 count of supplied booleans iff every flag is true, with checked counting. This is a precise finite conjunction witness, but has no gate identities, task binding or evidence verification and does not establish every required gate was represented. Inline positive/one-false tests are meaningful for this tiny predicate; mutation count comment is not new campaign evidence. No original code executed.

### code/rust/core_adversary/src/literature_receipt.rs

SHA256 `e870509530a2dc795e3e4093c5a3df0be1a03b74b14103ca5cc1831ef9e7158a`; complete lines 1–473; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete356-line literature owner prefix plus exact template. Constructor enforces bounded trimmed NFC text, lexical arXiv/DOI formats, no-authority/no-global-green labels and closed manual/fixture/lookup_stub provenance. It computes both legacy pipe-joined content fingerprint and structured canonical bibliographic digest. Since pipe is admitted in fields, the legacy fingerprint has prehash tuple ambiguity (package a|b,cite c versus package a,cite b|c); the separately structured canonical digest distinguishes them. This is metadata custody, not existence or reading of a cited paper. Public receipt fields can mutate after construction; canonical_bytes serializes stored digest fields without rechecking. JCS include/dependencies are separately scoped and unexecuted; no literature/network lookup performed.

### code/rust/core_adversary/src/mam.rs

SHA256 `7b9e8f1f0f5fa091c7573619a7284c00b6061eaf90979f3f71b694145b06278e`; complete lines 1–815; full_raw_source_body_review.

All815 raw lines read, including PDF byte writer and substantive retained tests. Deterministic MAM rendering prefers summary history then tape fallback; it retains blocked-turn mentions, truncates quotes with explicit ellipsis, escapes LaTeX/PDF delimiters and emits fixed-template MD/TEX/PDF without a renderer subprocess. PDF uses WinAnsi with unsupported characters replaced by ?, so it cannot preserve arbitrary mathematical/Unicode text; full narrative/source bytes remain the reference. Long unbroken words are not split to fit width. Captured summary presence skips tape parsing; this is retelling, not cross-artifact validation. Missing text is narrated as blocked even absent an explicit refusal. Tests check ordering, blocked status, determinism, xref offsets and pagination but not complete PDF semantics; not executed. Explicit not-evidence footer is appropriate.

### code/rust/core_adversary/src/mam_voices_v1.json

SHA256 `4970ee89cb9f9083926e0c0e2cb4919fd1a5dffb56a464d053709ce90a735217`; complete lines 1–71; full_raw_source_body_review.

Full71-line voice JSON body read. Twenty-two role descriptions, nine aliases, speech openings and outcome/reflection templates supply fictional narrative framing; no algorithms, model independence or mathematical evidence arise from the character names. Footer clearly distinguishes retelling from receipt/trace/action tape/full narrative. Template absent_roles describes unrecorded roles as not speaking, a stronger observation than sparse captured history can support; template blocked_turn also conflates missing words with an observed block in the renderer. The note asserting original wording was read as a corpus declaration, not independently verified literary provenance.

### code/rust/core_adversary/src/novella.rs

SHA256 `6cb5258d5c2af0bc802aeb2f67fffd5b1f22c859ea216c6c5d11b321398efdf3`; complete lines 1–626; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete503-line novella prefix plus exact template. Evidence-led renderer admits a closed top-level argument vocabulary and type-checks required text/list fields. It chooses a backtick fence longer than any captured run, preserving embedded fenced content visibly as data; supplied metrics, compilation checks, safety claims, guidance and proof are explicitly marked unverified/NOT_RUN. Missing diagnostics invoke an injected SBE port, so the no-IO claim depends on the supplied implementation; supplied diagnostic values are rendered rather than independently validated. Stage narrative is labelled authored framing, not observed agent dialogue. Reusable contribution is honest source-order narrative/captured-byte presentation, not verification or an operad law. No port or renderer executed.

### code/rust/core_adversary/src/obstruction_identification.rs

SHA256 `4d7c5225d6cb10c79a5721d87c1d9ccb41c4b8a8052ceaf97d5ac1c585560784`; complete lines 1–262; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete145-line obstruction identification prefix plus exact template. Empty network is explicitly NOT_MEASURED and absent scorer delegates to NullCochainScorer; nonempty carriers pass their exact network/cochain to a configured scoring port. Narrative certificate-verified wording is derived from returned Measurement records, whose booleans do not themselves check a certificate. Emitted DDC measurement fields use exact strings, but carrier_hash is SHA of the constant word carrier rather than actual carrier bytes. This is orchestration/custody of a scorer result, not a new cochain solver. Scoring owner remains separately pending; no scoring or emission executed.

### code/rust/core_adversary/src/oewas_oeeis_bridge.rs

SHA256 `49a11242777bab949c6f6707ac674a4feb639ef75c3b2e29ca92eda3caaec16f`; complete lines 1–636; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete519-line bridge prefix plus exact template. Concrete adapter maps typed detector evidence into EIS two-signal gates, rejects casefold/trim duplicate sensor IDs and delegates exact Hill quorum. Default n=2,K=2,threshold=1/2,per-sensor-cap=1 is a finite response rule, not a probabilistic independence guarantee. Literal escaped trigger phrases are screened against ten baseline strings; empty self-panel refuses, but empty phrase list vacuously admits and no recall/positive-fixture test occurs here. Stage methods verify a declared specialization port before invoking operad guards, formulary or regulator; this is a static per-stage membership license, not an observed seven-act progression. Registration precedes admission, so failed admission can leave the candidate registered. Actual EIS/operad laws and human-receipt authentication depend on external owners; no new dependency source-read or execution credit.

### code/rust/core_adversary/src/pfp_gateway.rs

SHA256 `a09267a8c228a61ab6912d6a9f56b7791bc4b17b916fc8105c778f96c9985209`; complete lines 1–911; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete788-line active PFP gateway prefix plus exact template. Unlike frozen legacy gateway, it reads/reconciles reservations, writes a full-output estimate hold before send, retains unknown outcomes and raw received bytes, blocks unresolved holds across the account, accepts actual nonnegative receipt cost only, validates nonnegative u64 token usage and charges settlement delta=actual-hold. Known costly malformed replies retain at least their hold/known overrun and stop fallback; missing usage stops later model roles in that bout. Actual budget overrun is fully charged and refused after the call, not prevented by an estimate. Replay binds current request/config/bout/route, provider container bytes/cost, PFP content and checked envelope; mathematical candidate checkers remain downstream and evidence_grade is UNVERIFIED. Correctness assumes a trusted single-writer ledger: recover/read/admit/append is not an atomic cross-process reservation, and records are not signed here. PreparedTaskTurn and concrete transport/strict-json implementations are external dependencies, separately reviewed where available; no provider/replay executed.

### code/rust/core_adversary/src/primary_gates.rs

SHA256 `dd7eba65f2ee104e7db15953f13d2bce4c18bfd2298a3b4154cdd4af5d5422c9`; complete lines 1–1800; full_raw_source_body_review.

All1800 raw lines read, including typed-dispatch tests. Actual reusable mathematics includes exact rational chain nilpotency d1*d0=0, L1 residual primal/dual certificates (||y||inf<=1,d0^T y=0,y.w=||w-d0 alpha||1), and sequential LP lower bounds selecting lexicographic residual coordinates over the optimum face. Carrier arrays supply only counts: incidence/unique-cell topology is not reconstructed, so these certify a declared finite rational chain complex rather than arbitrary listed simplicial geometry. Signed edge permutation checks preserve declared matrices/omega and Gamma2; no random campaign or universal task semantics follows. Other predicates provide exact byte transport, obligation dependency order/receipt binding, retained-tip hash chain and finite rate arithmetic; labels/host observations are explicit premises. Missing proof/process authority correctly HOLDs unless authenticated profile is selected. Empirical amortization top-level K/marginal/totals are not reconciled with the separate increasing-batch history, and containment counts have no per-trial records. Resource profile is explicitly unsigned and checks native_result_sha256 only by64-character length, not actual result bytes. describe.required lists are informational, not blanket field enforcement; conditional unused fields can be absent. Typed selectors merely dispatch the existing predicate. No evaluator/native tests executed; source YAML inclusion is not new source read.

### code/rust/core_adversary/src/process_observation.rs

SHA256 `756e0f9a37e850a5b81ce4f40d51007e1e59730ee08d0bfb11c1afa43c7e45b8`; complete lines 1–395; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete272-line process-observation prefix plus exact template. Closed wire record binds current host-selected run/task/action/source/candidate/checker, requested and resolved argv, ordered artifact/source pin lists, exact stdout/stderr bytes and observed completion times. EIS signature verifies an observer statement whose subject is the exact record hash; zero exit then passes. No process is launched and no executable/artifact is reread here, so actual OS observations and policy/key selection are trusted inputs. Requested executable name may resolve to a different exact executable path, with arguments required unchanged. Direct-child completion is expressly distinct from process-tree termination or sandbox/general safety. Structured deserialization closes known record fields, while outer payload custody and authenticated dependency remain external. No process/signature/native code executed.

### code/rust/core_adversary/src/providers/anthropic/mod.rs

SHA256 `a5fbce372b5e11d656ceb5cec071327bfa5750a78b192fd913b46b2d69500c74`; complete lines 1–83; full_raw_source_body_review.

All83 raw lines read. Provider exports and immutable MicrosBudget enforce spent<=ceiling and checked-add charges. Zero ceiling is valid here; paid transport separately refuses it. Cloning/forking budget values does not reserve aggregate funds. Inline100/40+50 and overrun assertions concern this local arithmetic, not provider integration or a fresh mutation campaign. Raw persistence and quote guarantees depend on the transport/sink.

### code/rust/core_adversary/src/providers/anthropic/raw_store.rs

SHA256 `7bf610647a17d69550ab64b31911911cba81b71837d9fdc2b2e400dd3764a83b`; complete lines 1–237; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete120-line prefix plus exact template. Portable name grammar, exclusive temp creation, file sync and hard-link publication support immutable raw-response custody; existing identical bytes are idempotent and different bytes conflict. Temp name uses name+PID, so same-process concurrent attempts can collide; failed create removes that temp even when it belonged to another attempt. Hard-link fallback creates the final target directly and can leave partial bytes on a later write failure, contrary to unconditional complete-publication wording. Directory fsync is absent. Shared writable directories/symlinks and concurrent use need an explicit filesystem premise. No filesystem owner execution.

### code/rust/core_adversary/src/providers/anthropic/request.rs

SHA256 `0035ab26f9497c24c576df4fbae30dbb99a02257a7407aa054022ed4d8fe4ccd`; complete lines 1–443; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete326-line prefix plus exact template. Closed request construction checks positive token counts, legal/unique custom tool names, alternated user/assistant roles, advisor allowlist membership, selected code-execution versions and declared fees. Allowlist is caller-provided, tool schemas are only object-shaped, and hardcoded dated model identifiers are historical declarations, not verified current provider capabilities. Recursive content screening blocks URL/file/upload references but permits base64 images without establishing a tokenizer/image-cost upper bound. Code-execution fee is explicitly caller-declared and provider unenforced. Cache/output/container checks constrain selected syntax, not tool safety or model efficacy. No provider call.

### code/rust/core_adversary/src/providers/anthropic/response.rs

SHA256 `33a887544566f1a793f1eb29a76694732eee7858728a235ec9f7723031b9bed2`; complete lines 1–444; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete321-line prefix plus exact template. Parses typed stop reasons, content and u64 usage while retaining unknown blocks and parsed raw_content values. Parsed preservation is not original JSON byte preservation; transport owns raw bytes. text() selects Text only. Readability singles out advisor redacted results, while redacted_thinking is typed as Thinking and can still receive Readable; unknown blocks may also be opaque. Duplicate-key/byte caps and request-response model identity are not enforced in this parser. Tool IDs are not globally uniqueness-checked here. Typed error messages remain untrusted provider content. No parser/provider execution.

### code/rust/core_adversary/src/providers/anthropic/tool_round.rs

SHA256 `6c2421d358f11a89a4ad6eb9a9daab3199de9fecb6d89f93da350220c0f1f478`; complete lines 1–227; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete110-line prefix plus exact template. Extracts client tool uses with nonempty distinct IDs and nonempty names, ignoring server tools. Builds exactly one ordered result per request, refuses foreign outcome IDs and marks missing outcomes as explicit not-run errors. Public ToolUse can bypass extractor grammar: a singleton empty ID/name is not rejected by the message builder, which rechecks uniqueness but not nonemptiness. No tool execution, concurrency or authorization proof is implemented.

### code/rust/core_adversary/src/providers/anthropic/transport.rs

SHA256 `eed5b65341f7916cf296caf5f6ff21c99fbf9fb93b38f3b377fd7b3314800e70`; complete lines 1–437; full_raw_source_body_review.

All437 raw lines read. Paid send requires positive ceiling and a quoted request before HTTP; response bytes are persisted before typed parsing, with conflicting names retried under a16-hex digest suffix. Quote uses body bytes+4096, advisor allowances, cache multiplier and declared code fee, not a proved tokenizer/provider/image/server-execution upper bound. Sibling name can exceed the raw store200-character cap after a valid long original name, and persistence failure after a call yields OutcomeUnknown. Unknown billing fields decline metering, leaving quote settlement to callers; model prices follow the request model without response identity enforcement. Non-2xx and truncated/partial captures are preserved where available. Bottom fabricated Ok/Err tests do not exercise transport. No HTTP or credentials accessed.

### code/rust/core_adversary/src/providers/budget.rs

SHA256 `85500dd71b10de43078e1b6660e491e05fe49c5e1bb98358179b7d5fdb445495`; complete lines 1–535; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete418-line prefix plus exact template. BigInt prices/tokens and rational decimal parsing implement nonnegative exact micro-dollar arithmetic, input/output legs individually ceiling-rounded. Pricing windows require effective<=observed<stale and latest eligible observation; evidence digest validates shape only. Budget debit locally enforces cap, while supplied actual charge is not recomputed from token usage or expiry. Settlement is an immutable local calculation rather than durable reservation/accounting. Decimal parser permits custom forms such as .1 and1.; it is not JSON syntax validation. ceil(bytes/3)+8 remains an estimate, not a universal token bound. No prices/network/original code executed.

### code/rust/core_adversary/src/providers/credentials.rs

SHA256 `c75a303eb6e7994b313e751745e319d09953a43970709f2e5c8197fbe5130b45`; complete lines 1–261; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete138-line source prefix plus exact template; no actual credentials/environment/key file read. OpenRouter resolver takes explicit file bytes first with BOM/export/simple quoting handling and last duplicate key winning, then an explicitly supplied map; inherited environment access exists only in uncalled functions. Missing/non-file explicit path can fall back to environment rather than fail closed. Anthropic uses only the supplied/inherited named environment variable. Key type omits Debug/Serialize but stores ordinary String without zeroization. These are lookup rules, not access performed by this audit.

### code/rust/core_adversary/src/providers/mod.rs

SHA256 `e7459c5ac3708e36529173c7341a9c2836f5f73d3213d6c29420ddf3fa1112f1`; complete lines 1–188; full_raw_source_body_review.

All188 raw lines read. Provider exports include open-string refusals and checked u64 quote arithmetic priced per token, distinct from per-million-token owner elsewhere. Both token counts zero refuse; zero-price nonempty requests may quote zero. Arithmetic fixture3*5+2*7=29 is meaningful locally, while generated count tests do not qualify integration. This function checks a declared ceiling but does not reserve or charge money. No owner execution.

### code/rust/core_adversary/src/providers/request.rs

SHA256 `418f948818669eeca33f0a95a7411df0d5008a6c41fdd80b4529ca5de7eccdf8`; complete lines 1–257; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete140-line prefix plus exact template. Chat request uses explicit messages in preference to system/user fallback, positive max tokens and trimmed nonempty model. Message roles are only nonempty, permitting unknown/whitespace role values; content can be empty. Decoding fields have numeric types but no temperature/top_p/logit-bias range checks; schema/grammar are arbitrary supplied values. Provider fallback/parameter requirements are emitted only when decoding is Some, so omitted decoding cannot inherit these configured defaults by proof. Request building provides no task preservation/effectiveness guarantee. No provider invocation.

### code/rust/core_adversary/src/providers/transport.rs

SHA256 `5c9ba3df99b75bb4ca34adbf8214c4512080f4e1c26efbcfeb8975c9284e11d0`; complete lines 1–336; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete219-line prefix plus exact template. Concrete reqwest client applies timeout, no redirects and bounded streaming, retaining partial bytes on read failure and at most the declared limit on overflow. One extra byte may be observed for the overflow decision then omitted from returned raw prefix. Simple post discards non-2xx/partial bodies whereas post_with_status preserves status/prefix. Default trait implementations can synthesize status200 for older post-only clients, so authentic HTTP status depends on concrete implementation. OpenRouter transport itself has no budget policy. External raw sink owns durable custody. No network call.

### code/rust/core_adversary/src/receipt.rs

SHA256 `fa372b6798aaab9929ea4154ef5699f75caf7e7a014bd0b06a59c4254aac1dbd`; complete lines 1–152; full_raw_source_body_review.

All152 raw lines read. Generic public Receipt constructors permit empty codes or malformed detail/status combinations; optional admit_closed checks code nonempty, Pass without detail and Fail/Refusal with nonempty detail. ClosedReceiptWitness retains only status tag/detail length, not the original subject/code/evidence. This is a local shape check, not default constructor safety or truth certification. Inline mutated-pass/empty-fail examples were read, not run; mutation-count comments are historical declarations.

### code/rust/core_adversary/src/recovery.rs

SHA256 `701d9a66c6b8e3554be91b05a3f2e2662f5d3936b8c314bbbb5fdda6b1206210`; complete lines 1–157; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete40-line prefix plus exact template. Recovery refuses closure on any unreadable journal line, then appends CRASHED_UNKNOWN for each start lacking a terminal. A later append failure reports partial progress, not transaction rollback. Cause/cost are not inferred. Correctness inherits globally unique bout IDs and valid journal ordering; reused IDs can be misclassified by the journal owner. No recovery or journal mutation executed.

### code/rust/core_adversary/src/render_record.rs

SHA256 `a3fe26049ba2ca789054bbfc0cc737ab9494d37ecde0cf685be5cf1962911fe7`; complete lines 1–371; full_raw_source_body_review.

All371 raw lines read. RawValue-based traversal protects against serde arbitrary-number marker collapse and preserves insertion order, but duplicate keys collapse to their last value in IndexMap, so this is not lossless wire custody. BigInt integers remain exact; decimal values become rounded f64, potentially infinity. Python-like float rendering can emit NaN/Infinity and is explicitly presentation-only, not strict JSON/money/certificates. Styles select ordering/ASCII and fixed-vs-exponent conventions; source does not establish all-float Python equivalence. Generic count tests do not test rendering or substantiate convergence wording. No original renderer executed.

### code/rust/core_adversary/src/research_loop/budget.rs

SHA256 `76b1cfa7188c06aa0bb976dc4d9167669e01013dea23fa27196e0cc887575147`; complete lines 1–507; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete384-line prefix plus exact template. Reservation ledger derives spend from retained entries; pre-dispatch hold charges call/tokens/cost, settled actual replaces hold including overruns, unknown retains hold, release returns tokens/cost but keeps call counted. One pending entry per round/stage prevents overlapping retry; closed reconciled entries permit another attempt. Checked u64 sums bound arithmetic. Direct existing-occurrence comparison checks key/executor/amounts but not packet/round/stage; controller-derived keys bind these externally. Resume checks structural charge/state consistency and aggregate limits, with any settled overrun permitting aggregate excess; it is not historical transition replay. Ledger is cloned/serialized local state, not durable or authenticated global accounting. No dispatch executed.

### code/rust/core_adversary/src/research_loop/canonical.rs

SHA256 `f6f7745f498829e9dcfb9bfeb983e9f85a741db472f602a31c9878c0b950372a`; complete lines 1–247; full_raw_source_body_review.

All247 raw lines read including concrete canonicalization tests. Canonical encoder sorts Unicode scalar keys, emits compact non-ASCII strings, arrays/booleans/null and lexical decimal integers only, with sha256-prefixed digest shape checks. Noninteger spellings and negative zero refuse to avoid cross-language float disagreement. Scope is parsed admitted JSON values, not original byte preservation or duplicate-key detection. Python-like integer/string examples and noninteger refusals are source tests, not newly executed cross-language conformance. Generic trailer adds only count invariant.

### code/rust/core_adversary/src/research_loop/invalidation.rs

SHA256 `46769fee0acc9c2280f4f0c8dbfd4bbf80d67261bed764f6af81b111fa6d9499`; complete lines 1–266; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete149-line prefix plus exact template. Kahn cycle detection on closed declared graph and fixed-point reverse reachability compute changed nodes plus all transitive dependents. Unknown changed IDs or undeclared dependencies return all known nodes, preserving conservative reuse semantics under incomplete declarations. Empty-change plan returns preserve immediately, and nonclosed graph returns full recompute before cycle checking; therefore blanket cyclic-graph-refusal wording exceeds these branches. Completeness of declared semantic dependencies is an external premise, explicitly not BQNF/additive-repair proof.

### code/rust/core_adversary/src/research_loop/mission.rs

SHA256 `277422f834e1d5ad3107252510c4551276cd039a32e037f21082f777f487f3d7`; complete lines 1–430; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete313-line prefix plus exact template. Mission admission closes fields, validates required/optional disjoint claim IDs, nonempty done predicates, route coverage, run-ID filename grammar and selected positive limits, then hashes the fully defaulted mission. Several limits are explicitly adapter-owned; capability/retention/source-inventory strings are declarations, not enforced capabilities. Owned/forbidden overlap is ASCII case-folded lexical comparison; no filesystem resolution or Windows alias/trailing-dot/symlink admission is provided, so it is not containment. Required claims and done predicates have no enforced semantic mapping. Public serializable mission requires verify at resume. No referenced seed content read.

### code/rust/core_adversary/src/research_loop/mod.rs

SHA256 `852ae03c06d887f62251c6e5e97e43b30a992b7b640a8e7da890c0fd97e4e046`; complete lines 1–209; full_raw_source_body_review.

All209 raw lines read. Module wires eight-stage research controller and documents host/payload separation; concrete local fixture reserves50 tokens then settles20, preserving one counted call and30 returned tokens. Source test exercises that finite accounting fact, not the entire18-check oracle or provider workflow. Generated mutation count remains declaration; no replay or original module executed.

### code/rust/core_adversary/src/research_loop/occurrence.rs

SHA256 `8e4cd7d7b5cf7c201c46a8414744df56fe1e22d458bf84886eeb6b9670f0ae0c`; complete lines 1–178; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete61-line prefix plus exact template. Occurrence naming and canonical digest of run/round/stage/occurrence/packet provide deterministic context binding under collision resistance. validate_id checks portable character/length syntax only, not allocated run/round/stage grammar; allocate itself is unconstrained. Idempotency effects require state/transport enforcement and are not caused by a hash alone. No dispatch/replay executed.

### code/rust/core_adversary/src/research_loop/pack.rs

SHA256 `288514a1e7dc214bf75a0bb9c382f4ba711108ddf717cbaf3f7d59e3b4f50f2a`; complete lines 1–418; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete301-line prefix plus exact template. Pack checker compares defaults, mandatory field order, routing names/order, eight stage executors/dependencies, nine prompt lineage records, raw_text digests, common budget values and compilability of response schemas. It does not compare route condition semantics, prompt task preservation, expected schema contents or concrete budget validity: all-null common budgets and empty raw_text with its digest can satisfy these local equalities. mission_required filter_map ignores nonstring extra entries. Stage file paths are joined from trusted pack data without containment enforcement and reads are unbounded. Pack is a local declaration consistency check, not full workflow equivalence. No files loaded through this owner.

### code/rust/core_adversary/src/research_loop/phase.rs

SHA256 `7bd3a749f10165bf2bff1a2e1a04d6698f1138024205905c48dd6a3a2e33a92a`; complete lines 1–178; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete61-line prefix plus exact template. Closed nine-phase/eight-stage mapping and stage5 host-only executor policy are precise finite dispatch predicates. Mapping alone does not enforce temporal progression; ResearchLoop owns expected-stage state. Phase Census/Plan/Produce all reference stage2, so choosing last matching phase in the controller yields Produce rather than executing three distinct visits. No machine execution.

### code/rust/core_adversary/src/research_loop/response_schema.rs

SHA256 `abce1d0262c1a2b25c41ad11d8b01221f6acdb1864d42711666994e3b1f901f2`; complete lines 1–635; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete512-line prefix plus exact template. Explicit supported-keyword compiler and sorted violations implement a bounded local schema dialect: depth64, root-local definitions, object required/additional rules, array prefix/items, Unicode scalar length, Rust regex and exact stored-number spelling equality. It is not full JSON Schema2020-12 semantics even for accepted type/const keywords: integer accepts only i64/u64 representations (rejecting integral decimal spellings or larger arbitrary integers), while const/enum distinguish1 from1.0. Reference names are literal after #/$defs/ rather than JSON-pointer unescaping; regex semantics are Rust rather than ECMAScript. Cyclic references compile then fail by runtime depth limit. Parsing/custody and semantic truth remain outside. No original validator executed.

### code/rust/core_adversary/src/research_loop/routing.rs

SHA256 `1ee4dc91f27a12c456cce09fa89209cc4f3ea8bba537fffcee0cf2b979cf98d7`; complete lines 1–430; full_raw_source_body_review.

All430 raw lines read including projection-table test. Ordered host-fact routing preserves11 dispositions alongside a many-to-one7-terminal projection and labels information loss. Policy/infrastructure/missing-input/verifier-unavailable blockers precede success; fully reviewed success precedes budget exhaustion, while witnessed unrepairable failure or repeated residual precedes budget fallback. Stall key hashes sets of required claims, residual identities and passed-required evidence identities, not prose confidence. Explicit oracle departures mean18 reported compatible scenarios are not exhaustive equivalence. Inputs remain trusted facts; route itself does not validate evidence, reviewer independence or logical consistency of supplied flags. No tests executed.

### code/rust/core_adversary/src/research_loop/state.rs

SHA256 `0be9e8bff3c1c63602421304ecb90a4339c7f1b44076e6f58c2f9d2c25120ae2`; complete lines 1–1192; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete1069-line prefix plus exact template. State machine sequences eight stages, reserves before recording, freezes stage4 canonical candidate, binds stage6/7 candidate digests, records host-only checks, and derives required status from done-predicate IDs. Repeat reservation uses a context-derived key, strengthening the direct ledger owner. Response-schema checking is not called here; host checks require only nonblank evidence-reference strings, and absent current-source/candidate/policy digests mean unchanged. Thus trusted adapter/checker observations remain explicit premises, not model-independent truth established by this machine. Resume verifies unkeyed state digest, mission, ledger, event sequence, reservation key set, occurrence count/key matching and candidate digest only when both fields are Some. It does not replay event payloads/transitions, verify terminal derivation, enforce candidate/frozen co-presence or authenticate evidence. The source candidly excludes a caller recomputing the digest; these checks are structural custody, not full historical execution proof. No model or host commands executed.

### code/rust/core_adversary/src/residual_ledger.rs

SHA256 `7403aac01fb91131c487bcc1832e45ee0521f76fd96d10e70428b685d3bf9714`; complete lines 1–286; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete163-line prefix plus exact template. ActVI records each dead-candidate cause through an injected failure-history sink and emits a residual declaration: exact joint-zero measurement maps CLEARED, other measured maps BOUNDED_RESIDUAL, missing measurement maps NOT_MEASURED. Blocking critiques remain separately listed, so CLEARED is only measurement status, not an overall acceptance decision. Recording occurs before ledger/event construction and even when residual-ledger ablation returns empty, allowing partial side effects on later failure. Narrative antibody updates are recorded failure history, explicitly not reproduced/admitted detectors. DDC emission uses constant carrier hash and exact ledger serialization witness; no sink or event executed.

### code/rust/core_adversary/src/routing.rs

SHA256 `0d03a4a0200c5889a91541e7bf42b939ec43294f5364448bd87fb2a29a70ca13`; complete lines 1–686; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete569-line prefix plus exact template. Exact BigRational weighted token prices and ceiling arithmetic, positive bout/day/tier caps, canonical seat-name collision checks, three distinct lexical model/vendor labels and cheap-seat fraction provide finite configuration constraints. Vendor strings are not independent model provenance; cheap share counts declared seats, not calls/cost. Missing id_verified defaults true, without provider verification. Direct admit_spend and RouteLeg cost permit negative supplied spending/token values; active gateway must enforce nonnegativity externally. Public structs can bypass parse validation. JSON/YAML loading hashes raw source but parsed duplicate fields may collapse, and unknown fields are ignored. No pricing/provider checks executed.

### code/rust/core_adversary/src/run_folder_store.rs

SHA256 `963f492fc49e25130640dafac20aef22c8697354b4701c9ccc6b177fe4ec4c0b`; complete lines 1–734; full_raw_source_body_review.

All734 raw lines read including substantive v2/v3/MAM tamper tests. Artifact adapter stages a named run in a temporary directory, allowlists files and renames at commit. Readback checks exact versioned filenames, rejects final-file and directory redirections, verifies raw file hashes, legacy tape equality, UTS references, content identity and optional MAM exact re-render. This is strong internal bundle custody under trusted stable filesystem; no file/directory fsync, cross-process no-replace transaction or ancestor/TOCTOU guarantee is proved. Readback does not independently execute model/checker work or validate every tape payload. MAM remains optional for historical v3, so removal plus removal of MAM receipt fields intentionally preserves identity, as source tests demonstrate. Tests were read, not run.

### code/rust/core_adversary/src/run_persistence.rs

SHA256 `da84e47c2adcd69c63180ec4dfb89778fa80defa9b2d9bdeff37eb61b1b732b7`; complete lines 1–956; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete833-line prefix plus exact template. Constructs hash-chained tape records and version-domain-separated bundle identities from narrative, tape, summary excluding receipt_id, and optional UTS; immutable artifact port controls publication. Metadata agreement is conditional on both fields existing; measured-certificate verification is a supplied boolean, not replay. UTS validates schema/sequence/unique IDs, minimum two newline-terminated rows and optional projected references, but does not require actual run_source/run_checkpoint kinds or nonempty IDs despite wording. Recursive reference checks visit only *_reference fields; generic retained wrappers/nested payload references are outside that check. sync_shared_key overwrites conflicting summary task/selection with nonempty receipt values rather than refusing. Custody is not source authenticity or semantic correctness. No persistence executed.

### code/rust/core_adversary/src/run_reporting.rs

SHA256 `44670a394b5482cf9777c04cf027e442858bc5b4555048e8e4e2763d96f352eb`; complete lines 1–983; full_raw_source_body_review.

All983 raw lines read including schedule-skip test. Deterministic UNS/UTS projection retains malformed/raw captures and caller narrative, labels pending turns NOT_ESTABLISHED, distinguishes missing roles from declared skips, and explicitly disclaims verification, independent workers and inference of external dispatch counts. Source pointers and content digests support later custody; large arrays become references and text is literal-fenced. Observations take precedence over seat_turns and graph results, so mixed-history secondary collections can be omitted by this view. blocked:false overrides refusal-derived blocked status. Context-only check data may be rendered with history-root compact pointers although no captured event is emitted. Output status and evidence verdict are caller facts, not newly established claims. No renderer/tests run.

### code/rust/core_adversary/src/scene_orchestration.rs

SHA256 `a5e9a7decc37328c09ede5a6a0e9cab8a7843917f9d9d709cb85c2390174422e`; complete lines 1–698; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete575-line prefix plus exact template. Finite scene graph admission bounds steps64, visits8, stages10, edges64, seats22 and attachment count16, checks reachability/deterministic status edges, and binds attached skill operands/digests to the consumed instruction plan. Runtime precharges declared seat count against total_budget-7 before executing injected seat calls, retains results and evaluates configured primary-gate payload; seat failures force ERROR. Gate predicates need not derive their mathematical witness from returned prose, which is added only under _adversary_scene. Fallback loops are bounded, but reachability is possible-path reachability, not guaranteed execution; transition callback occurs before later spend refusal and histories/side effects are not rolled back. Caller supplies actual seat implementations and monetary controls. No calls made.

### code/rust/core_adversary/src/scoring_ports.rs

SHA256 `afba16089ce5c3bd8ee36d61664d3219c0a1ddd2c60363416f17d94ee3b7aba4`; complete lines 1–114; full_raw_source_body_review.

All114 raw lines read. Null scorer correctly returns NOT_MEASURED without numeric/certificate fabrication. Euler witness computes checked V-E+F and one triangle fixture yields1. This is Euler characteristic only for an admitted valid finite2-complex; public Network constructor does not establish complete face closure/uniqueness, so raw count arithmetic alone cannot certify topology or cohomology. Counts may conservatively overflow i64 before cancellation. Mutation comment is not independent evidence and test was not executed.

### code/rust/core_adversary/src/skill_run.rs

SHA256 `0bb292ee13cb4454a15030b1eb8203a155c1683e791842d8097dcdde623ed245`; complete lines 1–561; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete438-line prefix plus exact template. Skill-run writer distinguishes caller-authored narrative from captured contributions and persists raw checker receipt bytes/digest plus verdict-shaped metadata. PASS_TO_MASTER requires a parsed Accepted receipt, REFUSE with receipt requires Rejected; other statuses may omit receipts. No matching objective/task/candidate/checker invocation is established by this owner, so an unrelated self-authored Accepted receipt can satisfy its local gate unless caller/checker bindings are supplied elsewhere. parse_actions accepts object rows and checks letter only when present; persistence accepts dda_steps separately without calling that parser. Current reporting adds custody, not replay or authority. No writing/checker execution.

### code/rust/core_adversary/src/soundness.rs

SHA256 `23e1c5b930e0e2b0da7201f3fbc08f7209aba2ee2a6f7933cff3ce00d65bd1ed`; complete lines 1–155; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete38-line prefix plus exact template. Thin exact-rational adapter calls core_epk::lggr_v::check_soundness on supplied D,Q and records the function name/report, explicitly distinguishing joint-kernel decision from finite path-kernel multiplication. Mathematical validity, matrix admission and quotient assumptions live in the dependency, not reproduced by wrapper or generic count tests. Dependency not newly fully read here; no native execution.

### code/rust/core_adversary/src/specialization.rs

SHA256 `98022556c96d25c31c46cb44cbc80e5d61136519e5db46140b4d994519e96570`; complete lines 1–443; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete326-line prefix plus exact template. Structural specialization validates closed port enum, identifiers, /adversary skill, nonempty ordered act bindings, licensed ports/terminals and bounded rounds/compute. validate_within checks only subset ports/terminals and componentwise budgets: it does not verify ceiling validity, child ancestry prefix, inheritance of parent skills or per-stage restrictions. Ordered nonempty stages need not cover all seven acts; a single actVII stage can pass. These are declarative capabilities until callers enforce them. Bout-status projection correctly separates fixture/ablated status from CheckPassed. No swarm/native execution.

### code/rust/core_adversary/src/stage/canonical.rs

SHA256 `c9904287929fcaa2bc21fa6de3b574b07ed01c0b0c39600835b4ce6b6cb3bb1a`; complete lines 1–379; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete256-line prefix plus exact template. Validated-record macro closes wire fields and calls each owner validation; fields remain crate-visible, not universal construction-proof. Canonical identity uses domain-separated JSON, NFC strings/keys and rejects normalized-key collisions and floats. This is a declared semantic quotient: canonically equivalent Unicode spellings share identity rather than byte identity. Text/item limits are applied by selected record validators, not recursively by arbitrary semantic_id payloads. Digest syntax does not authenticate content. No serialization execution.

### code/rust/core_adversary/src/stage/ddc.rs

SHA256 `440e92ba890570109f761a0c372c826ac7ac25ef85f536ca85e61cda5f5067cf`; complete lines 1–175; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete52-line prefix plus exact template. DDC record reuses external operation enum with aliases and validates class identifiers, nonempty trimmed carrier/witness/receipt text and authority None. Fields named hashes are not checked as SHA digests; timestamp and optional signed rational metrics receive no semantic/chronology/nonnegative check here. It is a data contract, not evidence of state transition correctness. Native calculus dependency not newly fully read.

### code/rust/core_adversary/src/stage/ddc_tape_evaluator.rs

SHA256 `7936943fe821f8bcdc51971597f00d627d1467e1a7c9ac48c69beebe542fa98c`; complete lines 1–1200; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete1077-line prefix plus exact template. Actual finite mechanisms: alphabet/prefix syntax, sequence/parent continuity, step/rollback bookkeeping and bounded-i64 rational metric admission. Important limits: step record hash omits phi/gamma/timestamp, compensation record binds only branch ID/count rather than step bodies, and class hashes hash labels rather than actual states. Adjacent before/after class equality is not enforced. Missing metrics become zero histories; window sums use unchecked Rational64 addition, so individually representable metrics do not ensure a representable sum. OEARS M is terminal in transition rule but complete validation globally requires final T, making a completed M refusal impossible. Compensation steps are not DFA-checked; rollback accepts any in-range index, not only saved checkpoints. JSONL record hashes and expected head are optional, blank lines affect physical sequence indices, and evaluator deserialization has no custom invariant revalidation. No cryptographic collision is asserted: omitted fields simply do not enter hash material. No native execution.

### code/rust/core_adversary/src/stage/diagnostics.rs

SHA256 `9e461a6891af46fd60ffb019186ea982eba044d49e30d15dce61dc4ade29b539`; complete lines 1–181; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete58-line prefix plus exact template. SBE diagnostic wrapper retains arbitrary object fields and exposes coordinates only under explicit DETERMINISTIC_SYNTHETIC_DIAGNOSTIC label. Quoted rationals remain exact; legacy numeric decimals are converted through f64 and booleans to0/1. No entropy/purity range or density-operator validity is inferred. Label and coordinates are supplied diagnostics, never verified residuals. Numerical port is external and unexecuted.

### code/rust/core_adversary/src/stage/emission.rs

SHA256 `50dae9e7c87e9af290290568b6206b924ee4d7b8d4012817ebfbda94eebfa305`; complete lines 1–441; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete318-line prefix plus exact template. Event builder binds actual payload bytes to a SHA and injected timestamp; emitter orders UTS, DDC, SGT, UNS callbacks. Any later failure leaves earlier sink effects, so this is ordered emission rather than an atomic transaction. emit_event does not recheck supplied payload against an already deserialized event hash; raw event contract checks text only. DDA-without-step refuses only when a DDC sink exists. Whitespace-prefixed JSON is treated as raw text by SGT turn parser. Optional sinks and default PUBLIC label do not establish persistence/privacy authorization. No emission executed.

### code/rust/core_adversary/src/stage/evaluation.rs

SHA256 `ba392279fc2056c6d879f976edbd8af111cfffe14ff523831d5e9395de69c68b`; complete lines 1–275; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete152-line prefix plus exact template. Evaluator epoch pins positive integer weights/probes, rule identifiers and implementation digests. Valuation receipt recomputes exact weighted pre/post/delta and sign disposition under a safe bound256*10^12<i64max. Receipt permits zero weights whereas epochs require positive weights, and does not resolve epoch digest to compare probes/weights/baseline. independently_recomputed is a supplied true boolean, not a separate checker execution. Thus local arithmetic is verified on supplied vectors; frozen-epoch/independence claims need an external binding check. No original arithmetic/tests executed. Later full runtime review resolves the local binding concern for run_swarm: verify_valuation_bindings compares candidate/epoch/ordered probes/weights, and entry compares packet epoch. Zero weights cannot pass that runtime against a valid positive-weight epoch. The independently_recomputed boolean remains supplied.

### code/rust/core_adversary/src/stage/exact.rs

SHA256 `98fbafae08b0561d3ef9b803c464a2fb9973ba41daf4f9e24ea9289a668cb5b6`; complete lines 1–178; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete55-line prefix plus exact template. Exact quoted rational parser normalizes BigInt numerator/denominator, refuses zero denominator and supports finite decimal/exponent notation with scale magnitude<=10000. This bounds powers of ten but input integer/ratio digit length is unbounded here and parsed before that check. Whitespace and alternate decimal spellings normalize intentionally. It is exact arithmetic syntax, not nonnegativity/domain validation or universal resource bound. No parser execution.

### code/rust/core_adversary/src/stage/file_adapters.rs

SHA256 `869c7df632639a96cbbba025f468ee3eff841174f61eb45874100073f523f3dc`; complete lines 1–419; full_raw_source_body_review.

All419 raw lines read. Single-process file adapters fsync appended bytes; cemetery publishes no-clobber immutable records, failure history increments counts without activating pending detectors, and genealogy uses one OS-locked handle for read/append plus hash-chain verification. Already-ACTIVE labels are trusted retained admissions and context_key is ignored on load. Genealogy duplicate-idempotent return stops at matching earlier row without checking later tail; a valid final row lacking newline can concatenate with next append. History load is unbounded; path redirection/concurrent writers outside genealogy are not prevented. Fabricated Ok/Err mutation test never invokes these owners. No filesystem writes through original code.

### code/rust/core_adversary/src/stage/genealogy.rs

SHA256 `0998131ea97ac139c8cde869ae495c77dbed5527dfaa89a1be7286ce50504fcf`; complete lines 1–464; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete341-line prefix plus exact template. Closed wire records constrain cemetery, failure counts and lineage metadata while explicitly disclaiming detector/defect verification. Headstone ID hashes only run/scene/candidate/cause, omitting payload hash, killer, evidence and round; lineage ID hashes only parent/child/reason, omitting deficiencies/fixes/guidance. These are selected-key identities rather than full-content custody hashes; file adapter equality can detect conflicting writes separately. Headstone new allows an empty evidence string while from_json wire_strings forbids it, so an admitted constructor value need not round-trip. Genealogy permits self-parent/cycles; no DAG law. Antibody input defaults ACTIVE in generic deserialization but explicit from_json requires status; neither authenticates admission.

### code/rust/core_adversary/src/stage/mod.rs

SHA256 `c2e95825f665d301babd8093096b0b2ce0a7a48204eb887389460d0cde07d2f8`; complete lines 1–137; full_raw_source_body_review.

All137 raw lines read. Stage exports strict JSON from external runtime and contains a concrete finite vocabulary check: sorted distinct nonempty challenge labels, membership and positive exact rational stake with round-trip. This does not establish truth of a challenge or enforce every packet stake through this helper. Bottom test fabricates Result values rather than exercising closure, so claimed six killed mutations are not demonstrated here. No original code executed.

### code/rust/core_adversary/src/stage/numpy_rng.rs

SHA256 `732c50df15837630fea5f52960588728a0504c5737c949c349460f961860757b`; complete lines 1–241; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete118-line prefix plus exact template. Narrow deterministic SeedSequence(u32)/PCG64/ziggurat adapter uses deliberate wrapping integer arithmetic and bounded normal rejection loops. Uniform uses53 high bits; tails use floating ln_1p/exp and fixed tables. Bounded rejection may refuse, so even intended NumPy stream compatibility has an explicit termination departure; platform libm rounding may matter. Included stream test path is not a newly read test body. No full NumPy compatibility or statistical quality claim follows from source labels or generic trailer; no RNG/native execution.

### code/rust/core_adversary/src/stage/numpy_ziggurat.rs

SHA256 `d08a410d7cf2724215ef7d4e5264ed32412722a6947319ef8cd2aad2523ca430`; complete lines 1–1001; full_raw_source_body_review.

All1001 raw lines read, including all768 constants, census helpers and tests. KI256 integer thresholds plus WI/FI exact IEEE bit patterns make a finite reproducible table; FI starts1 and decreases to positive tail, WI retains the exceptional first entry and increasing remaining scale. KI census checks256 distinct entries and exactly one zero, which is much weaker than equality to the named upstream header or correctness of the normal distribution. Historical upstream version/header digest is a declaration, not independently retrieved/verified here. Full source reading does not mean hand-proving every table value; any later parsed census is separate bounded arithmetic. Numerical convergence comment and generic count tests add no approximation-error proof.

### code/rust/core_adversary/src/stage/oscillation.rs

SHA256 `231e83e1646318c2f83103b2554ab575a7917f290a80311ef0d67e24c33b74b7`; complete lines 1–270; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete147-line prefix plus exact template. Exact Jaccard distance uses token sets from nonclaims and artifact-reference strings only, not candidate payload/task semantics; empty sets have distance0. Per-scene consecutive low-distance pairs without caller-reported progress increment a bounded i64 counter; threshold0 never trips because comparison is strict. Historical tripped fields remain true but later record returns can be false, so caller must act on each signal; no persistent enforced circuit-open refusal. Useful lexical stagnation heuristic under bounded proposal inputs, not semantic equivalence or convergence theorem. No detector execution. The empty-set branch describes the raw distance helper only: valid CandidateProposal records require nonempty artifacts and nonclaims, so it is not asserted to be reachable through valid proposal inputs.

### code/rust/core_adversary/src/stage/packets.rs

SHA256 `0fae010f257171c7d34da7f5c5f2ec932016a238fcbcc5a8f0518416c193fcc2`; complete lines 1–392; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete269-line prefix plus exact template. Validated packet records close fields and bind semantic identities. Candidate proposals require artifact digests and explicit nonclaims, but neither artifact/prediction existence nor task preservation is checked. Workflow plans remain PROPOSED; operation/license/catalog IDs are declarations until external resolution. AgentResult PASS permits empty candidate/artifact lists; parser admissibility is not successful work. Work packets bound unit budgets and require objectives/acceptance criteria but do not evaluate them. Challenge independence is an agent/domain label, not external evidence. No packet or provider execution.

### code/rust/core_adversary/src/stage/ports.rs

SHA256 `b377304b4872e93b50ae1da4e56ae1fc91f8ae8df5d5fe6a666ad253e98e3c0e`; complete lines 1–278; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete155-line prefix plus exact template. Request digest binds canonical context and prompt/role/scene/seat/round/operator fields, but public construction does not impose semantic policy. Reply validation checks optional identifiers and exact nonnegative usage lexemes; it does not check authority/residual values or bind raw response bytes/digest to content. Derived deserialization does not automatically call validate. Injected continuation, model, evaluator and scheduler ports make responsibilities explicit; their presence supplies no independence or successful execution. No transport calls.

### code/rust/core_adversary/src/stage/receipt_replay.rs

SHA256 `e24783f2b241c257d96da28febe12f1010b43998bb8e99936738b70da5353075`; complete lines 1–447; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete324-line prefix plus exact template. Strict receipt parsing demands explicit nonnull IDs and exact canonical serialization; replay checks definition/profile/graph/work-packet bindings, result packet IDs and reconstructed final state. Reconstruction uses the same DeterministicScheduler over supplied result/progress records, so it checks internal transition consistency rather than independent truth of results or evidence that calls occurred. Terminal halt/stall overrides are reconstructed from declarations: stall sets HOLD without rerunning oscillation detection. Selection shape is validated, not actual frontier evaluation. External strict-JSON dependency is not newly read or executed.

### code/rust/core_adversary/src/stage/run.rs

SHA256 `f4eb4b98912e6af09713b284d36a3ded977c5eb5576cbe5b5ffd1a2ecaa88e8c`; complete lines 1–465; full_raw_source_body_review.

All465 raw lines read. Progress is derived from supplied bounded positive counters, not measured work. State validates sorted visits, result/progress arity and bounded counts but relies on scheduler/replay for historical consistency. with_terminal_status accepts any closed terminal label and rebinds identity; retained test explicitly stamps COMPLETED onto a zero-result state. Selection requires nonempty evidence/nonclaims and SELECT membership in the supplied frontier but does not independently construct it. Receipt binds causal result IDs and final result IDs; additional progress/state consistency belongs replay. Tests and declaration trailers are source, not new runs.

### code/rust/core_adversary/src/stage/run_swarm.rs

SHA256 `a16eb22387097a4f11fabc4fc6be3dec14a0512f571c52c7a4af0961c01636c1`; complete lines 1–606; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete483-line prefix plus exact template. run_swarm binds packet epoch at entry and evaluator candidate/epoch/probes/weights before accepting arithmetic, closing the standalone receipt gap. It consumes injected proposal/evaluation, bounded scheduler and optional sinks; there is no provider work in this review. Residual-refined counter increments whenever any residual changes, including increases, so a worsening valuation can reset dry-round accounting. Continuation halt ignores supplied reason/remaining budget and marks any nonempty result history COMPLETED. Model proposal precedes missing evaluator/epoch checks, and events/rollback may occur before local state/result commit; sink errors are not atomic rollback. Runtime receipt labels definition/profile supplied separately from scheduler without a direct identity crosscheck here; deterministic replay can detect inconsistent bindings later. Trust domain uses first assignment for scene, not the producing agent lookup. No global task-correctness guarantee.

### code/rust/core_adversary/src/stage/scheduler.rs

SHA256 `d5c64230cd965bf16b52f1505eb79d697c2dab0f2455b659cc75349f7ccbf197`; complete lines 1–507; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete384-line prefix plus exact template. Concrete N=1 scheduler validates definition/profile/graph/catalog identity, required operation coverage and declared independent-seat agent-ID disjointness. It does not resolve license digests or match required colours, and agent-ID distinction is weaker than independent provider/control. Step cost is exactly one unit; bounded steps/dry rounds/visits ensure a finite run for validated records. advance checks current scene but omits membership of result.status in SceneSpec.allowed_result_statuses and does not bind result agent to assigned seats. A terminal scene becomes COMPLETED for any non-stop result, including HOLD if stop statuses omit it. Transitions use first sorted matching priority; residual filters are any-match. Replay reuses the same scheduler, not an independent implementation. Direct call state/profile validity remains caller premise.

### code/rust/core_adversary/src/stage/synthetic_diagnostic.rs

SHA256 `64872be49940b0a4c0feb857ac21f0c28700524b5f39f80add44886dcafc2c8c`; complete lines 1–162; full_raw_source_body_review.

All162 raw lines read. Deterministic synthetic diagnostic hashes text to a32-bit RNG seed, perturbs real Gaussian vectors, forms a normalized mixture of outer products and delegates density/spectrum validity to linear-algebra owners. Dimension guard1..128 and iteration policy100000 bound the declared numerical problem, while tolerances define entropy/nonzero thresholds. It measures this constructed synthetic state, not textual truth, physical quantum state or task fitness. Normalization and positive mixture have a clear conditional PSD/trace-one basis; actual numerical success depends on unexecuted linear-algebra dependencies. Failures become UNAVAILABLE/ArithmeticError; stream compatibility label lacks a fresh cross-language check. Bottom Ok/Err test does not exercise the diagnostic or prove six killed mutations.

### code/rust/core_adversary/src/stage/topology.rs

SHA256 `ccfca985ad3bb75c18da7578e73f33b1e4f31737a4e78a3fb53782149e5f9c10`; complete lines 1–428; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete305-line prefix plus exact template. Topology records enforce unique/sorted seats/scenes/transitions, closed labels, endpoint membership, explicit terminal-scene existence and exact semantic IDs. They do not establish terminal reachability, acyclicity or executable operation/license availability. Independent-seat references are closed but only assignment agent identity is compared by scheduler. Scene allowed-result vocabulary is validated locally but scheduler does not enforce membership for incoming results. Profile skill IDs and anti-skill digest are declarative; required colours have no scheduler composition check. Finite well-formed topology is useful independently of these operational gaps.

### code/rust/core_adversary/src/wire_json.rs

SHA256 `ded92bf0a57434bca41cedd09615fc4ad968c727eb44049be80e50b9b5a2bcca`; complete lines 1–174; full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review.

Complete51-line prefix plus exact template. Recursive sorted-key, spaced ASCII JSON emits UTF-16 escape pairs for non-ASCII scalars, preserving a deterministic declared wire format for parsed JSON values. It is not RFC canonical JSON or original byte identity. Scalar number formatting is delegated to serde_json, so complete Python numeric formatting equivalence is not established. Recursion/size is not bounded in this helper and duplicate raw keys have already been resolved by the upstream parser. Generic count trailer does not test Unicode/numeric wire compatibility. No serializer execution.
