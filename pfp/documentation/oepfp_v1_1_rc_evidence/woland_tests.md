> Source-attributed audit appendix. Source and original-extraction hashes quoted below are distinct from the wrapped release artifact hashes recorded in source_manifest.json. Historical verdicts and quoted terminology are retained as evidence; no estate test or model call was executed by this extraction. Full machine extraction: [woland_tests.json.gz](woland_tests.json.gz).

# Woland test-estate forensic extraction for OEPFP v1.1RC

Repository HEAD: `58a6a1ef92e155b1fa3783081becb41de3e07734`. AuthorityEffect: None. Integrity mode: benchmark.

This is a source audit. No test imports, pytest collection, pytest execution, Cargo invocation, provider call, or Lean build was performed. Test bodies and assertions express intended checks; they are not current PASS receipts. Only `/workspace/scratch/oepfp-audit/` artifacts were written.

## Census and exact scope

The literal recursive scope contains **308 test_*.py files**, all tracked, and all 308 parse with Python AST. The prompt’s 158-module count is stale. There are 133 root files, 16 retained evidence/source-snapshot files and one retired runner file. The remaining 291 are source-test candidates; their collection remains unverified.

There are **2771 statically named test functions**, 10131 assert statements across tests and helpers, 49 unittest-style assertion calls, 1080 expected-exception contexts, 101 local/conftest fixture definitions, and 613 parametrized test functions. These are AST counts, not expanded test-case counts. Nested helpers and delegated fixture controls are explicitly retained. One retained `test_fixtures.py` file defines no tests.

Root `pytest.ini` testpaths statically select 85 of the 308 modules. Explicit path invocation, nested configuration, plugins, import errors and skip conditions can change collection. The root configuration excludes evidence snapshots and retired runner recursion; it also excludes generic `research` recursion while explicitly listing selected research files. Do not infer “all 308 ran” from a root pytest command.

Sorted `(path, source_sha256)` manifest digest: `3f467ad906d65119f17de58052f369843159665487ce5f263bf569c04d84014a`.

| Subtree | Files |
|---|---:|
| `(root)` | 133 |
| `domain` | 1 |
| `geometry` | 9 |
| `intelligence_mining` | 1 |
| `intergates` | 3 |
| `pilots` | 74 |
| `probes` | 1 |
| `providers` | 17 |
| `research` | 50 |
| `research_swarm` | 1 |
| `researcher` | 2 |
| `residual_algebra` | 3 |
| `spine` | 13 |

The accompanying `woland_tests.json` retains every module path, full byte SHA-256, imports with direct repository source hashes, every function/test name and location, every assert expression, assertion calls, expected-exception checks, fixture definitions/dependencies, parametrization source, module fixture values, mock/stub operations, contract literals, skip/environment controls, and requirement leads with citations. Parsing never executes test code. Requirement keyword leads are labeled as leads; contextual conclusions below are manually scoped.

## Formal requirement crosswalk

| Requirement | Existing source evidence | What the evidence does not establish |
|---|---|---|
| R1 forensic coverage | All 308 files inventoried with byte hashes, source lines, assertions, fixtures and provenance; gate, bout, binding and replay families extracted. | Current execution results, complete collection, or a one-to-one AB-001–019 semantic mapping. |
| R2 coloured symmetric operad | Residual sort/package examples; planar free multicategory substitution; finite lens composition; explicit native gate/operator and admitted anti-skill checks. | Full symmetric-group actions/equivariance, a sound ideal quotient with NullTree laws, 100% pipeline typing, or elimination of procedural/text heuristics. |
| R3 quantum epistemic bundle / RG | Geometry observer/capture metadata, explicit proposer-side token/activation interventions, finite quantum pilot fixtures. | A Hilbert-bundle model of beliefs, density-operator dynamics, CPTP partial-trace RG, Lindblad semigroup, entropy/relative-entropy engine, beta functions, or Tsirelson theorem. |
| R4 end-to-end algebraic typing | Strict bound raw replies; exact finite cochains and independent witness checks; registered finite DPO rules and protected interfaces; pinned replay; proof-source/axiom custody. | DPO confluence in general, general discrete termination from telemetry, high-degree cohomology closure, or a Lean reflection theorem for the entire operad/DPO interpreter. |
| R5 architecture and v1.2 | Versioned typed envelopes, Rust/native process boundaries, immutable schema tests, reusable DDC procedures, finite forward/backward lenses, explicit Nomos scanner. | Publication-grade implemented architecture, equilibrium semantics for open games, autonomous safe skill self-repair, or full trusted compiler reflection. |

## Gate contracts, binding schemas, and procedures

The source establishes a useful distinction between model proposals, host mathematical checks, protocol disposition and authority. A field named `AUTHORIZED` is a local protocol label; tests repeatedly require `authority_effect == "None"`. “Coverage complete” and “all gates pass” are separate flags. A retained procedure or replayed provider envelope is not a solved mathematical task.

| Area | Declared contract and falsifiers | Source anchors |
|---|---|---|
| Exact request boundary | `omega.symbol-game.request.v1`, `symbol_game.c011.exact.v1`; no float tokens or elevated authority; candidate bytes and receipt hashes bind independent evidence. | [omega_engine_woland/tests/test_spec_001_exact_admission.py:40](../../../omega_engine_woland/tests/test_spec_001_exact_admission.py#L40); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:436](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L436) |
| Honest terminal gate | Missing measurement, inconsistent host residual, unverified certificate, unbound checker, nonzero exact obstruction and ablation cannot substitute for evidence. Structured critique binds candidate selection. | [omega_engine_woland/tests/test_honest_gate_falsifiers.py:237](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L237); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:303](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L303); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:473](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L473) |
| Carrier-dependent gate scope | An undeclared carrier permits the explicit checker-only evidence path; a declared carrier additionally needs valid exact-zero measurement. This is not one universal joint-zero predicate for every task. | [omega_engine_woland/tests/test_honest_gate_falsifiers.py:720](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L720); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:754](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L754); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:775](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L775) |
| Seven-act lifecycle | Start → carrier framing → proposal/critique/lift/check → typed terminal disposition → persisted bundle. Write-ahead seat markers precede potentially paid execution; crash reconciliation emits CRASHED_UNKNOWN. | [omega_engine_woland/tests/test_bout_execution.py:82](../../../omega_engine_woland/tests/test_bout_execution.py#L82); [omega_engine_woland/tests/test_bout_journal.py:191](../../../omega_engine_woland/tests/test_bout_journal.py#L191); [omega_engine_woland/tests/test_bout_journal.py:269](../../../omega_engine_woland/tests/test_bout_journal.py#L269) |
| Refusal surface | AST extraction must find a nonempty declared surface; every declared code has an injection and every injection still targets a declared code; 31 codes are pinned in the fixture. | [omega_engine_woland/tests/test_bout_refusal_coverage.py:488](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L488); [omega_engine_woland/tests/test_bout_refusal_coverage.py:496](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L496); [omega_engine_woland/tests/test_bout_refusal_coverage.py:515](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L515) |
| Retained DDC program | Six-file `omega.woland.reported-run-bundle.v1` with versioned content-addressed receipt IDs; C/R/I/T trace; fresh checker required; current prompt and premises must match and raw trace/summary/binding tampering rejects. | [omega_engine_woland/tests/test_ddc_program_reuse.py:30](../../../omega_engine_woland/tests/test_ddc_program_reuse.py#L30); [omega_engine_woland/tests/test_ddc_program_reuse.py:55](../../../omega_engine_woland/tests/test_ddc_program_reuse.py#L55) |
| Checked reuse | Registered recipe pins task seed, premises, contract, candidate, checker ID/source and output; fresh source and target checks run; missing premises produce QUERY_USER_MORE_INFO/NOT_SOLVED with zero provider calls. | [omega_engine_woland/tests/test_checked_ddc_reuse.py:130](../../../omega_engine_woland/tests/test_checked_ddc_reuse.py#L130); [omega_engine_woland/tests/test_checked_ddc_reuse.py:167](../../../omega_engine_woland/tests/test_checked_ddc_reuse.py#L167) |
| Actual native gates | Exact stdout bytes bind 35 native results and 10 transition checks; five governed checkpoints; strict policy stops before models while retaining finish/readback obligations. | [omega_engine_woland/tests/test_teamwork_native_gates.py:50](../../../omega_engine_woland/tests/test_teamwork_native_gates.py#L50); [omega_engine_woland/tests/test_teamwork_native_gates.py:71](../../../omega_engine_woland/tests/test_teamwork_native_gates.py#L71) |
| Graph replay | Native certificate replay, persisted-file custody, regular entries, source-event identity, mid-replay recheck and adversarial substitution; model agreement has no certificate weight. | [omega_engine_woland/tests/test_graph_replay.py:35](../../../omega_engine_woland/tests/test_graph_replay.py#L35); [omega_engine_woland/tests/test_graph_replay.py:85](../../../omega_engine_woland/tests/test_graph_replay.py#L85); [omega_engine_woland/tests/test_graph_boundaries.py:261](../../../omega_engine_woland/tests/test_graph_boundaries.py#L261) |
| Finite ACSets/DPO | Monic interface, rule/source/match digests, protected task/constraints, strict exact attributes, fuel and independent gradient judge; structural rewrite can still fail mathematical acceptance. | [omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py:185](../../../omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py#L185); [omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py:148](../../../omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py#L148) |

The exact line references above are source anchors, not PASS evidence. Full assertion line records and fixture bodies are in JSON; source hashes make a changed revision detectable.

## Contextual review of the principal gate/replay modules

### `omega_engine_woland/tests/test_spec_001_exact_admission.py`

SHA-256: `a5bc98753f049bf5a08ee43f0ec216f42fe499bc1857501427413441d74c5b58`. Requirements: R1, R2, R4. Static source review; NOT_RUN.

Versioned no-authority request/outcome types; float-token refusal; exact positive obstruction and independent-witness ablation block admission. Scope is explicit finite fixtures.

Anchors: [omega_engine_woland/tests/test_spec_001_exact_admission.py:40](../../../omega_engine_woland/tests/test_spec_001_exact_admission.py#L40); [omega_engine_woland/tests/test_spec_001_exact_admission.py:79](../../../omega_engine_woland/tests/test_spec_001_exact_admission.py#L79); [omega_engine_woland/tests/test_spec_001_exact_admission.py:115](../../../omega_engine_woland/tests/test_spec_001_exact_admission.py#L115); [omega_engine_woland/tests/test_spec_001_exact_admission.py:152](../../../omega_engine_woland/tests/test_spec_001_exact_admission.py#L152).

### `omega_engine_woland/tests/test_honest_gate_falsifiers.py`

SHA-256: `7693ed5537ed892c35a86bb7471262a2d6ea26fcdf2af50a93cfed2fac569705`. Requirements: R1, R2, R4. Static source review; NOT_RUN.

Falsifiers cover cochain laundering, missing/unverified/inconsistent measurement, missing or byte-unbound checkers, structured critique, receipt custody and exact-zero boundaries. Later tests explicitly permit checker-only admission when no carrier is declared; do not state every admitted task necessarily has a cochain measurement.

Anchors: [omega_engine_woland/tests/test_honest_gate_falsifiers.py:121](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L121); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:135](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L135); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:147](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L147); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:170](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L170); [omega_engine_woland/tests/test_honest_gate_falsifiers.py:190](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L190).

### `omega_engine_woland/tests/test_bout_refusal_coverage.py`

SHA-256: `20b6567bfd9ce61aca093049aaef7755ca597e383d2bb51d9b325dfe1c3593ce`. Requirements: R1, R4, R5. Static source review; NOT_RUN.

AST discovers a nonempty 31-code declared circuit refusal surface, compares injection inventory both directions and executes each injection when run. This is scoped finite negative coverage, not a theorem for arbitrary new branches.

Anchors: [omega_engine_woland/tests/test_bout_refusal_coverage.py:488](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L488); [omega_engine_woland/tests/test_bout_refusal_coverage.py:496](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L496); [omega_engine_woland/tests/test_bout_refusal_coverage.py:505](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L505); [omega_engine_woland/tests/test_bout_refusal_coverage.py:515](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L515); [omega_engine_woland/tests/test_bout_refusal_coverage.py:528](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L528).

### `omega_engine_woland/tests/test_bout_journal.py`

SHA-256: `59e844a7767ec431f9f8fd61b49530346025fa6e37a685ee6f1fd28f66c2ab6c`. Requirements: R1, R4. Static source review; NOT_RUN.

Write-ahead start/turn/terminal records; typed corrupt and unwritable journals; idempotent reconciliation; interruption propagation; actual child termination fixture. Reconciliation labels unknown crashes rather than inventing completion.

Anchors: [omega_engine_woland/tests/test_bout_journal.py:86](../../../omega_engine_woland/tests/test_bout_journal.py#L86); [omega_engine_woland/tests/test_bout_journal.py:97](../../../omega_engine_woland/tests/test_bout_journal.py#L97); [omega_engine_woland/tests/test_bout_journal.py:101](../../../omega_engine_woland/tests/test_bout_journal.py#L101); [omega_engine_woland/tests/test_bout_journal.py:118](../../../omega_engine_woland/tests/test_bout_journal.py#L118); [omega_engine_woland/tests/test_bout_journal.py:125](../../../omega_engine_woland/tests/test_bout_journal.py#L125).

### `omega_engine_woland/tests/test_bout_execution.py`

SHA-256: `d2f345a496019a55ed9b73a60cb17c14ea61616f4bd5f684f29dbd8b5221aab9`. Requirements: R1, R4. Static source review; NOT_RUN.

Seven-act execution uses injected measurement and spy fixtures, keeps exact lifted cochain values, rejects malformed carriers and declared Regge measurement failure; null scorer remains NOT_MEASURED.

Anchors: [omega_engine_woland/tests/test_bout_execution.py:53](../../../omega_engine_woland/tests/test_bout_execution.py#L53); [omega_engine_woland/tests/test_bout_execution.py:82](../../../omega_engine_woland/tests/test_bout_execution.py#L82); [omega_engine_woland/tests/test_bout_execution.py:155](../../../omega_engine_woland/tests/test_bout_execution.py#L155); [omega_engine_woland/tests/test_bout_execution.py:222](../../../omega_engine_woland/tests/test_bout_execution.py#L222); [omega_engine_woland/tests/test_bout_execution.py:243](../../../omega_engine_woland/tests/test_bout_execution.py#L243).

### `omega_engine_woland/tests/test_turn_and_terminal_truth.py`

SHA-256: `19bfb7271ce55b64f7a24c1704a6a01c7120588b20f3b9c92829af2bc451ec6a`. Requirements: R1, R4. Static source review; NOT_RUN.

Executor output is byte-preserved; absent executor cannot fabricate success; external-admission request and actual selection control terminal status independently from authority.

Anchors: [omega_engine_woland/tests/test_turn_and_terminal_truth.py:28](../../../omega_engine_woland/tests/test_turn_and_terminal_truth.py#L28); [omega_engine_woland/tests/test_turn_and_terminal_truth.py:34](../../../omega_engine_woland/tests/test_turn_and_terminal_truth.py#L34); [omega_engine_woland/tests/test_turn_and_terminal_truth.py:53](../../../omega_engine_woland/tests/test_turn_and_terminal_truth.py#L53); [omega_engine_woland/tests/test_turn_and_terminal_truth.py:62](../../../omega_engine_woland/tests/test_turn_and_terminal_truth.py#L62); [omega_engine_woland/tests/test_turn_and_terminal_truth.py:70](../../../omega_engine_woland/tests/test_turn_and_terminal_truth.py#L70).

### `omega_engine_woland/tests/test_checked_ddc_reuse.py`

SHA-256: `6fcc34809a9e02b0a11b3e1aa0822f98c9696d4fbf9d1e9cf0985694dbf62dbb`. Requirements: R1, R2, R4, R5. Static source review; NOT_RUN.

Registered source/target task-premise-contract and checker bindings are rechecked; source bytes remain unchanged; a query transfers QUERY_USER_MORE_INFO/NOT_SOLVED rather than fabricated missing premises. Includes finite DPO transport fixtures, not general semantic equivalence.

Anchors: [omega_engine_woland/tests/test_checked_ddc_reuse.py:130](../../../omega_engine_woland/tests/test_checked_ddc_reuse.py#L130); [omega_engine_woland/tests/test_checked_ddc_reuse.py:145](../../../omega_engine_woland/tests/test_checked_ddc_reuse.py#L145); [omega_engine_woland/tests/test_checked_ddc_reuse.py:159](../../../omega_engine_woland/tests/test_checked_ddc_reuse.py#L159); [omega_engine_woland/tests/test_checked_ddc_reuse.py:167](../../../omega_engine_woland/tests/test_checked_ddc_reuse.py#L167); [omega_engine_woland/tests/test_checked_ddc_reuse.py:178](../../../omega_engine_woland/tests/test_checked_ddc_reuse.py#L178).

### `omega_engine_woland/tests/test_ddc_program_reuse.py`

SHA-256: `b3927237bc530c999c7ad3a9235b0c660ea3c8fb7535ac03fc134961b4702fd4`. Requirements: R1, R4, R5. Static source review; NOT_RUN.

Retained C/R/I/T procedure with content-bound six-file bundle, explicit fresh-check obligation, current prompt/premise checks, byte tampering, metadata mutation and versioned receipt-ID format. Reusing a procedure does not reuse an acceptance verdict.

Anchors: [omega_engine_woland/tests/test_ddc_program_reuse.py:30](../../../omega_engine_woland/tests/test_ddc_program_reuse.py#L30); [omega_engine_woland/tests/test_ddc_program_reuse.py:55](../../../omega_engine_woland/tests/test_ddc_program_reuse.py#L55); [omega_engine_woland/tests/test_ddc_program_reuse.py:74](../../../omega_engine_woland/tests/test_ddc_program_reuse.py#L74); [omega_engine_woland/tests/test_ddc_program_reuse.py:88](../../../omega_engine_woland/tests/test_ddc_program_reuse.py#L88); [omega_engine_woland/tests/test_ddc_program_reuse.py:97](../../../omega_engine_woland/tests/test_ddc_program_reuse.py#L97).

### `omega_engine_woland/tests/test_ddc_operad_bout_ingress.py`

SHA-256: `6da33dc1915d8a42ba2f516c10a8972042cf9e4f2d338cd8687a1b71b2517a05`. Requirements: R1, R2, R4. Static source review; NOT_RUN.

Alternative DDC entrypoint cannot skip live instruction binding; offline fixture with undecided structure cannot print SUCCESS.

Anchors: [omega_engine_woland/tests/test_ddc_operad_bout_ingress.py:8](../../../omega_engine_woland/tests/test_ddc_operad_bout_ingress.py#L8); [omega_engine_woland/tests/test_ddc_operad_bout_ingress.py:24](../../../omega_engine_woland/tests/test_ddc_operad_bout_ingress.py#L24).

### `omega_engine_woland/tests/test_teamwork_ddc_host.py`

SHA-256: `be105b07888da669cc3457f253efd6372f6ed220109ddffa566eedabe800eb7b`. Requirements: R1, R4, R5. Static source review; NOT_RUN.

Offline PFP role fixtures coexist with actual native persistence, real local checker subprocess and durable SQLite admission. DDC stores UNVERIFIED procedure and final checked readback; current source/checker/premise changes reject reuse.

Anchors: [omega_engine_woland/tests/test_teamwork_ddc_host.py:29](../../../omega_engine_woland/tests/test_teamwork_ddc_host.py#L29); [omega_engine_woland/tests/test_teamwork_ddc_host.py:73](../../../omega_engine_woland/tests/test_teamwork_ddc_host.py#L73); [omega_engine_woland/tests/test_teamwork_ddc_host.py:100](../../../omega_engine_woland/tests/test_teamwork_ddc_host.py#L100); [omega_engine_woland/tests/test_teamwork_ddc_host.py:117](../../../omega_engine_woland/tests/test_teamwork_ddc_host.py#L117); [omega_engine_woland/tests/test_teamwork_ddc_host.py:128](../../../omega_engine_woland/tests/test_teamwork_ddc_host.py#L128).

### `omega_engine_woland/tests/test_teamwork_checked_query.py`

SHA-256: `8fe28a3a6bc258741c39889c7dd29ab034e7f911a02bd5f3af488fc3ebecdecc`. Requirements: R1, R4. Static source review; NOT_RUN.

Original checker and checked-query disposition; synthetic role proposals cannot convert missing premises into acceptance. Requires current execution and durable task binding.

Anchors: [omega_engine_woland/tests/test_teamwork_checked_query.py:81](../../../omega_engine_woland/tests/test_teamwork_checked_query.py#L81); [omega_engine_woland/tests/test_teamwork_checked_query.py:122](../../../omega_engine_woland/tests/test_teamwork_checked_query.py#L122); [omega_engine_woland/tests/test_teamwork_checked_query.py:174](../../../omega_engine_woland/tests/test_teamwork_checked_query.py#L174); [omega_engine_woland/tests/test_teamwork_checked_query.py:182](../../../omega_engine_woland/tests/test_teamwork_checked_query.py#L182); [omega_engine_woland/tests/test_teamwork_checked_query.py:202](../../../omega_engine_woland/tests/test_teamwork_checked_query.py#L202).

### `omega_engine_woland/tests/test_teamwork_native_gates.py`

SHA-256: `b7c285b1b004a528e41a49dee671b1dfddde14168b818cd1d48958db3ae1472f`. Requirements: R1, R2, R4, R5. Static source review; NOT_RUN.

Captures 35 native gate responses and 10 transition checks, verifies exact process output bytes, tracks five checkpoints, distinguishes coverage_complete from all_pass, preserves legacy read-only replay and stopped-finish residuals.

Anchors: [omega_engine_woland/tests/test_teamwork_native_gates.py:50](../../../omega_engine_woland/tests/test_teamwork_native_gates.py#L50); [omega_engine_woland/tests/test_teamwork_native_gates.py:71](../../../omega_engine_woland/tests/test_teamwork_native_gates.py#L71); [omega_engine_woland/tests/test_teamwork_native_gates.py:81](../../../omega_engine_woland/tests/test_teamwork_native_gates.py#L81); [omega_engine_woland/tests/test_teamwork_native_gates.py:119](../../../omega_engine_woland/tests/test_teamwork_native_gates.py#L119); [omega_engine_woland/tests/test_teamwork_native_gates.py:141](../../../omega_engine_woland/tests/test_teamwork_native_gates.py#L141).

### `omega_engine_woland/tests/test_teamwork_process_observation.py`

SHA-256: `b52504aeba8b8bfcea4e4070c20276c7025c6eef5ab37d7a494195d9bfa786a6`. Requirements: R1, R4. Static source review; NOT_RUN.

Signed actual child-byte observations depend on authenticated capability and matching policy/candidate scope; timeout/nonzero child and forged/transplanted evidence cannot mint a successful check.

Anchors: [omega_engine_woland/tests/test_teamwork_process_observation.py:42](../../../omega_engine_woland/tests/test_teamwork_process_observation.py#L42); [omega_engine_woland/tests/test_teamwork_process_observation.py:96](../../../omega_engine_woland/tests/test_teamwork_process_observation.py#L96); [omega_engine_woland/tests/test_teamwork_process_observation.py:117](../../../omega_engine_woland/tests/test_teamwork_process_observation.py#L117); [omega_engine_woland/tests/test_teamwork_process_observation.py:128](../../../omega_engine_woland/tests/test_teamwork_process_observation.py#L128); [omega_engine_woland/tests/test_teamwork_process_observation.py:143](../../../omega_engine_woland/tests/test_teamwork_process_observation.py#L143).

### `omega_engine_woland/tests/test_teamwork_kernel_observation.py`

SHA-256: `c549edecb64ffe1ccb8ba4c6abe39948eeacf70fe5aa1f34bbf3c3ba9b3cc8b9`. Requirements: R1, R4, R5. Static source review; NOT_RUN.

Actual tiny kernel proof capture with explicit operator trust and public obligations; current source/checker/artifact binding; wrong theorem, sorry and unavailable kernel cannot create signed success. Scope is declared proof artifacts and axioms, not arbitrary AST/operad/DPO reflection.

Anchors: [omega_engine_woland/tests/test_teamwork_kernel_observation.py:62](../../../omega_engine_woland/tests/test_teamwork_kernel_observation.py#L62); [omega_engine_woland/tests/test_teamwork_kernel_observation.py:70](../../../omega_engine_woland/tests/test_teamwork_kernel_observation.py#L70); [omega_engine_woland/tests/test_teamwork_kernel_observation.py:91](../../../omega_engine_woland/tests/test_teamwork_kernel_observation.py#L91); [omega_engine_woland/tests/test_teamwork_kernel_observation.py:98](../../../omega_engine_woland/tests/test_teamwork_kernel_observation.py#L98); [omega_engine_woland/tests/test_teamwork_kernel_observation.py:111](../../../omega_engine_woland/tests/test_teamwork_kernel_observation.py#L111).

### `omega_engine_woland/tests/test_graph_replay.py`

SHA-256: `21bd9c9ca510eddd10920070c520c6ee5ebfe318f7a4008c236dd3867188b4e9`. Requirements: R1, R4. Static source review; NOT_RUN.

Pinned replay checks native math and harvesting, all persisted-file byte custody, regular entries, mid-replay mutation, substitution with recomputed self-digests, certificate corruption and deduplicated recurring observations.

Anchors: [omega_engine_woland/tests/test_graph_replay.py:35](../../../omega_engine_woland/tests/test_graph_replay.py#L35); [omega_engine_woland/tests/test_graph_replay.py:56](../../../omega_engine_woland/tests/test_graph_replay.py#L56); [omega_engine_woland/tests/test_graph_replay.py:70](../../../omega_engine_woland/tests/test_graph_replay.py#L70); [omega_engine_woland/tests/test_graph_replay.py:85](../../../omega_engine_woland/tests/test_graph_replay.py#L85); [omega_engine_woland/tests/test_graph_replay.py:106](../../../omega_engine_woland/tests/test_graph_replay.py#L106).

### `omega_engine_woland/tests/test_graph_boundaries.py`

SHA-256: `b3282929913b4cc76888320373dd11592670903032630e4a71aab689df26dab5`. Requirements: R1, R2, R4. Static source review; NOT_RUN.

Actual candidate/output bytes and native validation outrank model agreement, fixture enforcement is explicit, live gateway unbound refusal happens before output, invalid finite-language candidates are rejected.

Anchors: [omega_engine_woland/tests/test_graph_boundaries.py:25](../../../omega_engine_woland/tests/test_graph_boundaries.py#L25); [omega_engine_woland/tests/test_graph_boundaries.py:56](../../../omega_engine_woland/tests/test_graph_boundaries.py#L56); [omega_engine_woland/tests/test_graph_boundaries.py:66](../../../omega_engine_woland/tests/test_graph_boundaries.py#L66); [omega_engine_woland/tests/test_graph_boundaries.py:78](../../../omega_engine_woland/tests/test_graph_boundaries.py#L78); [omega_engine_woland/tests/test_graph_boundaries.py:103](../../../omega_engine_woland/tests/test_graph_boundaries.py#L103).

### `omega_engine_woland/tests/test_governing_councils_input_binding.py`

SHA-256: `82406e188c7a1983f429bfc25cd2b52dfb5af9c9fd689e2c0ef1f8b5e2d8525b`. Requirements: R1, R4. Static source review; NOT_RUN.

Full motion/evidence/dissent retention and detached context snapshots; input limits include exact UTF-8 bytes and nesting; caller-supplied status cannot promote harvested obligations.

Anchors: [omega_engine_woland/tests/test_governing_councils_input_binding.py:98](../../../omega_engine_woland/tests/test_governing_councils_input_binding.py#L98); [omega_engine_woland/tests/test_governing_councils_input_binding.py:118](../../../omega_engine_woland/tests/test_governing_councils_input_binding.py#L118); [omega_engine_woland/tests/test_governing_councils_input_binding.py:150](../../../omega_engine_woland/tests/test_governing_councils_input_binding.py#L150); [omega_engine_woland/tests/test_governing_councils_input_binding.py:198](../../../omega_engine_woland/tests/test_governing_councils_input_binding.py#L198); [omega_engine_woland/tests/test_governing_councils_input_binding.py:217](../../../omega_engine_woland/tests/test_governing_councils_input_binding.py#L217).

### `omega_engine_woland/tests/test_lake_candidate_binding.py`

SHA-256: `e503ce7f89746e96da56301b07ba62e8990f8024aab75742930009f5531f76f5`. Requirements: R1, R4, R5. Static source review; NOT_RUN.

Tiny real Lean candidate bytes, fence extraction, source manifests, toolchain/process capture and explicit axiom policy; tests skip when the explicit toolchain is absent. Candidate checking must never substitute a canonical proof for supplied bytes.

Anchors: [omega_engine_woland/tests/test_lake_candidate_binding.py:44](../../../omega_engine_woland/tests/test_lake_candidate_binding.py#L44); [omega_engine_woland/tests/test_lake_candidate_binding.py:55](../../../omega_engine_woland/tests/test_lake_candidate_binding.py#L55); [omega_engine_woland/tests/test_lake_candidate_binding.py:86](../../../omega_engine_woland/tests/test_lake_candidate_binding.py#L86); [omega_engine_woland/tests/test_lake_candidate_binding.py:111](../../../omega_engine_woland/tests/test_lake_candidate_binding.py#L111); [omega_engine_woland/tests/test_lake_candidate_binding.py:121](../../../omega_engine_woland/tests/test_lake_candidate_binding.py#L121).

### `omega_engine_woland/tests/test_lean4_dual_witness_cross_verification.py`

SHA-256: `9c9bca3fd87b3c57210829f283d7a8be38b519606217e5c5b30ab628546cbba3`. Requirements: R1, R4, R5. Static source review; NOT_RUN.

Triangle Python result and canonical serialization/hash are compared with a Lean program. The referenced Lean program hardcodes three booleans, and its kernel proves conjunction of boolean flags; this does not mechanically verify the rational dual vector equations in Lean.

Anchors: [omega_engine_woland/tests/test_lean4_dual_witness_cross_verification.py:24](../../../omega_engine_woland/tests/test_lean4_dual_witness_cross_verification.py#L24); [omega_engine_woland/tests/test_lean4_dual_witness_cross_verification.py:114](../../../omega_engine_woland/tests/test_lean4_dual_witness_cross_verification.py#L114).

### `omega_engine_woland/tests/test_compositional_open_games.py`

SHA-256: `5435115a842b66e9ca754b39e8cda4976ad248dc478613c6e5357034aeed964e`. Requirements: R2, R5. Static source review; NOT_RUN.

Finite forward/backward cochain lens identity/associativity and selected retinue composition, plus local terminal labels. Uses float masses 0.5,0.25,1.5 and dictionary flags; does not prove symmetric operad equivariance, open-game equilibria or exact rational totality.

Anchors: [omega_engine_woland/tests/test_compositional_open_games.py:33](../../../omega_engine_woland/tests/test_compositional_open_games.py#L33); [omega_engine_woland/tests/test_compositional_open_games.py:53](../../../omega_engine_woland/tests/test_compositional_open_games.py#L53); [omega_engine_woland/tests/test_compositional_open_games.py:78](../../../omega_engine_woland/tests/test_compositional_open_games.py#L78); [omega_engine_woland/tests/test_compositional_open_games.py:112](../../../omega_engine_woland/tests/test_compositional_open_games.py#L112).

### `omega_engine_woland/tests/test_bqnf_runtime_interventions.py`

SHA-256: `7c7a516efd1bf729ad3380ca4b5a9c6dda7b4d8296e005b19ca854e21f6745be`. Requirements: R1, R3, R5. Static source review; NOT_RUN.

Optional live/local model logits processors and activation patches test token masks, captured activations and retained digests. These are proposer-side interventions; no Wilsonian RG map, density-operator semantics or universal-normal-form fixed-point proof follows.

Anchors: [omega_engine_woland/tests/test_bqnf_runtime_interventions.py:191](../../../omega_engine_woland/tests/test_bqnf_runtime_interventions.py#L191); [omega_engine_woland/tests/test_bqnf_runtime_interventions.py:265](../../../omega_engine_woland/tests/test_bqnf_runtime_interventions.py#L265); [omega_engine_woland/tests/test_bqnf_runtime_interventions.py:383](../../../omega_engine_woland/tests/test_bqnf_runtime_interventions.py#L383).

### `omega_engine_woland/tests/test_grobner_variety_contraction_bout.py`

SHA-256: `50bfadec74765a2fefb8370a1ae84adbae697bf21a83d708beccd8975dbdb844`. Requirements: R1, R2, R4. Static source review; NOT_RUN.

Finite exact polynomial ideal-membership versus naive division, deterministic repair bout and optional OpenRouter trial. Keyword presence in a live critique is separate from the exact polynomial checker verdict.

Anchors: [omega_engine_woland/tests/test_grobner_variety_contraction_bout.py:360](../../../omega_engine_woland/tests/test_grobner_variety_contraction_bout.py#L360); [omega_engine_woland/tests/test_grobner_variety_contraction_bout.py:384](../../../omega_engine_woland/tests/test_grobner_variety_contraction_bout.py#L384); [omega_engine_woland/tests/test_grobner_variety_contraction_bout.py:484](../../../omega_engine_woland/tests/test_grobner_variety_contraction_bout.py#L484).

### `omega_engine_woland/tests/test_nomos_contract_compliance.py`

SHA-256: `c5054195a6bc397c362cba75b1d09ef3d03db0b43f0b47ae7fd7988bacc4ac6b`. Requirements: R1, R2, R5. Static source review; NOT_RUN.

Contract scanner counts, supplied defect logging, immutability, textual claim hygiene and encoding. This is a scanner/logging boundary, not self-modifying skill correctness or a meta-law proof.

Anchors: [omega_engine_woland/tests/test_nomos_contract_compliance.py:49](../../../omega_engine_woland/tests/test_nomos_contract_compliance.py#L49); [omega_engine_woland/tests/test_nomos_contract_compliance.py:67](../../../omega_engine_woland/tests/test_nomos_contract_compliance.py#L67); [omega_engine_woland/tests/test_nomos_contract_compliance.py:108](../../../omega_engine_woland/tests/test_nomos_contract_compliance.py#L108); [omega_engine_woland/tests/test_nomos_contract_compliance.py:134](../../../omega_engine_woland/tests/test_nomos_contract_compliance.py#L134).

### `omega_engine_woland/tests/test_architecture_fitness.py`

SHA-256: `5cc24ce6ffec1abad5065ef704757b7d4c87f2ac4e0c1f0feb20600d50bbf703`. Requirements: R1, R5. Static source review; NOT_RUN.

AST-resolved inward dependency checks with nonempty-corpus control, frozen dataclass models and Result-return discipline. AST inspection is compatible with architecture audit but is not a replacement for the requested formal engine semantics.

Anchors: [omega_engine_woland/tests/test_architecture_fitness.py:76](../../../omega_engine_woland/tests/test_architecture_fitness.py#L76); [omega_engine_woland/tests/test_architecture_fitness.py:86](../../../omega_engine_woland/tests/test_architecture_fitness.py#L86); [omega_engine_woland/tests/test_architecture_fitness.py:91](../../../omega_engine_woland/tests/test_architecture_fitness.py#L91); [omega_engine_woland/tests/test_architecture_fitness.py:96](../../../omega_engine_woland/tests/test_architecture_fitness.py#L96); [omega_engine_woland/tests/test_architecture_fitness.py:104](../../../omega_engine_woland/tests/test_architecture_fitness.py#L104).

### `omega_engine_woland/tests/test_woland_phi_qualification.py`

SHA-256: `5576b60b217f02cdead1a435bfad0a96103183c9a8b19701ce4baee8cfa4c3f5`. Requirements: R1, R4. Static source review; NOT_RUN.

Epoch-bound nonincreasing Phi, hard admissibility gates and lexicographic productivity ordering; rejects counterexample hiding. Such finite protocol checks do not establish a general Lyapunov/curvature termination theorem.

Anchors: [omega_engine_woland/tests/test_woland_phi_qualification.py:150](../../../omega_engine_woland/tests/test_woland_phi_qualification.py#L150); [omega_engine_woland/tests/test_woland_phi_qualification.py:196](../../../omega_engine_woland/tests/test_woland_phi_qualification.py#L196); [omega_engine_woland/tests/test_woland_phi_qualification.py:232](../../../omega_engine_woland/tests/test_woland_phi_qualification.py#L232); [omega_engine_woland/tests/test_woland_phi_qualification.py:261](../../../omega_engine_woland/tests/test_woland_phi_qualification.py#L261); [omega_engine_woland/tests/test_woland_phi_qualification.py:292](../../../omega_engine_woland/tests/test_woland_phi_qualification.py#L292).

### `omega_engine_woland/tests/intergates/test_intergate_input_contract.py`

SHA-256: `2ae4c09a42a5975168550646ccb0982b31ee4d5db0bad002b121529c18c4a570`. Requirements: R1, R4. Static source review; NOT_RUN.

Missing evidence, coercions/nonfinite values, duplicate YAML/spec identity, reused seeds, unknown specs and unbound terminal labels reject. Transition descent requires actual observations.

Anchors: [omega_engine_woland/tests/intergates/test_intergate_input_contract.py:12](../../../omega_engine_woland/tests/intergates/test_intergate_input_contract.py#L12); [omega_engine_woland/tests/intergates/test_intergate_input_contract.py:19](../../../omega_engine_woland/tests/intergates/test_intergate_input_contract.py#L19); [omega_engine_woland/tests/intergates/test_intergate_input_contract.py:28](../../../omega_engine_woland/tests/intergates/test_intergate_input_contract.py#L28); [omega_engine_woland/tests/intergates/test_intergate_input_contract.py:37](../../../omega_engine_woland/tests/intergates/test_intergate_input_contract.py#L37); [omega_engine_woland/tests/intergates/test_intergate_input_contract.py:42](../../../omega_engine_woland/tests/intergates/test_intergate_input_contract.py#L42).

### `omega_engine_woland/tests/intergates/test_source_contract_profile.py`

SHA-256: `c9b2d174ec4dd1811258c8d3fa0970f8dd7fc46163202c84dc52093a8c7138c7`. Requirements: R1, R4. Static source review; NOT_RUN.

Source-contract profile selection is explicit; unknown/current failure cannot retry weakened legacy math; native result inputs and endpoint/source binding are retained and checked.

Anchors: [omega_engine_woland/tests/intergates/test_source_contract_profile.py:26](../../../omega_engine_woland/tests/intergates/test_source_contract_profile.py#L26); [omega_engine_woland/tests/intergates/test_source_contract_profile.py:36](../../../omega_engine_woland/tests/intergates/test_source_contract_profile.py#L36); [omega_engine_woland/tests/intergates/test_source_contract_profile.py:42](../../../omega_engine_woland/tests/intergates/test_source_contract_profile.py#L42); [omega_engine_woland/tests/intergates/test_source_contract_profile.py:63](../../../omega_engine_woland/tests/intergates/test_source_contract_profile.py#L63); [omega_engine_woland/tests/intergates/test_source_contract_profile.py:86](../../../omega_engine_woland/tests/intergates/test_source_contract_profile.py#L86).

### `omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py`

SHA-256: `bbe1409f29050f1facaf1f1f0b1bd8ac79a2e87a6525defa39ebd176dee25538`. Requirements: R1, R2, R5. Static source review; NOT_RUN.

Replay required before inert review candidate persistence; unavailable replay remains residual; critic labels cannot mint antibodies; duplicate source observations do not satisfy recurrence.

Anchors: [omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py:127](../../../omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py#L127); [omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py:143](../../../omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py#L143); [omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py:149](../../../omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py#L149); [omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py:160](../../../omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py#L160); [omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py:170](../../../omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py#L170).

### `omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py`

SHA-256: `2586f66c45db993d4673e562b08efac147bdb4dd2fc22070000f669b224f1d94`. Requirements: R2, R4. Static source review; NOT_RUN.

Planar free multicategory substitution, declared residual sorts, gauge isolation/naturality and bounded licensing. Float residual telemetry and named invariants are present; full symmetric actions, ideals as sound congruences and NullTree laws remain separate requirements.

Anchors: [omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py:64](../../../omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py#L64); [omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py:85](../../../omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py#L85); [omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py:115](../../../omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py#L115); [omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py:165](../../../omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py#L165); [omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py:205](../../../omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py#L205).

### `omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py`

SHA-256: `2048059ae3fab308542915bd8b4c76158685652f193fee2ac5eaa2bc22ab4d90`. Requirements: R1, R2, R4. Static source review; NOT_RUN.

Twenty-five finite host controls: oriented gradients, exact rational residuals, protected topology/potentials, registered rule+source+match binding, deterministic fuel and independent mathematical judge. Structural DPO acceptance alone cannot pass wrong edge weights.

Anchors: [omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py:39](../../../omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py#L39); [omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py:45](../../../omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py#L45); [omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py:50](../../../omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py#L50); [omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py:56](../../../omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py#L56); [omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py:61](../../../omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py#L61).

### `omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py`

SHA-256: `e63a5aec50fdb02df3286af4a8cc5cc05add5fd4dec40042b21e4d8abaaa9ea4`. Requirements: R1, R2, R4. Static source review; NOT_RUN.

Twenty-five offline controls: protected task/constraint/output spans, Unicode preservation, finite rule registry, monic inclusion, dangling and ID/fuel/custody refusals. A typed reply remains UNVERIFIED until an independent task judge.

Anchors: [omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py:50](../../../omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py#L50); [omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py:62](../../../omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py#L62); [omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py:75](../../../omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py#L75); [omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py:122](../../../omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py#L122); [omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py:132](../../../omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py#L132).

### `omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py`

SHA-256: `30a452eac8655a904240bd280b9e6b9bea29663a44df30c434489dff66343795`. Requirements: R1, R2, R4. Static source review; NOT_RUN.

Explicit branching example disproves global confluence of original presentation. Extended examples have a unique explored normal form but global_confluence remains NOT_CHECKED. Exhaustive words through length five and budget refusal cannot establish unrestricted confluence.

Anchors: [omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py:20](../../../omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py#L20); [omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py:41](../../../omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py#L41); [omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py:68](../../../omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py#L68); [omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py:73](../../../omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py#L73); [omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py:80](../../../omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py#L80).

## Genuine coverage gaps and mathematical corrections

1. **DPO does not imply confluence.** The original rewrite example has the irreducible descendants `ae` and `dc` and explicitly records `global_confluence == "DISPROVED"`; a completed finite example records `"NOT_CHECKED"` globally. Preserve this falsifier in the specification. Require explicit termination and joinability hypotheses, and critical-pair or orthogonality evidence, before claiming confluence. See [omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py:20](../../../omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py#L20).
2. **Lean flag parity is narrower than witness reflection.** `CrossVerification.lean` constructs `divergenceFree := true`, `linfBounded := true`, `pairingSaturated := true`; `Kernel.valid_certificate_holds` unfolds their Boolean conjunction. The cross-language test checks canonical string/hash parity. It does not feed the rational incidence matrix/vector to a kernel decision procedure. The later proof-source-bound candidate tests provide stronger custody for declared theorems, but do not fill the general interpreter-reflection theorem.
3. **A planar multicategory is not a fully specified symmetric operad.** Existing tests sample substitution, finite lens identity/associativity and named residual sorts. Missing from this scope are explicit symmetric actions and their equivariance with every partial composition, soundness of ideal generators, and annihilator/NullTree coherence. Propose these as implementation obligations rather than declaring all current Python orchestration already mathematical morphisms.
4. **Float telemetry remains in legacy residual/lens fixtures.** `mass=0.5`, `mass=0.25`, `mass=1.5` and float risk scores are intentionally present in these test fixtures. They cannot be cited as a uniform exact-rational acceptance core. Keep display/heuristic telemetry separate from exact witness arithmetic.
5. **R3 is an architectural proposal in this scope.** No matching Woland test source was found for Wilsonian RG, Lindblad evolution, von Neumann/relative entropy, transition cocycles or Tsirelson bounds. Token masking and activation interventions are actual distinct capabilities, not proofs of those mathematical identifications. Other estates may supply evidence; this audit does not claim their absence globally.
6. **Antibody-ID linkage is not yet mechanically total.** Explicit AB-004/005/013/017/019 identifiers were absent from this test-file corpus in the bounded source search. Rejection tests can support a semantic crosswalk only after matching the canonical antibody’s hypotheses. Do not label a generic exactness test as complete inoculation against all nineteen antibodies.
7. **Collection and execution remain separate obligations.** The physical census includes evidence snapshots and one no-test fixture module, and default root paths select a subset. Import errors, missing native executables/toolchains, credentials, optional Torch/TransformerLens/DSPy dependencies and live markers must be resolved before any estate-wide PASS statement.

## Small targeted validation candidates (not run)

These are existing source tests worth scheduling after dependency checks. Commands are suggestions only; no test was executed in this audit.

| Scope | Suggested selector | Intended evidence |
|---|---|---|
| Exact gate falsifier | `omega_engine_woland/tests/test_spec_001_exact_admission.py::test_act7_refuses_float_epsilon_open_obstruction` | Tiny positive exact obstruction cannot be rounded to zero. |
| Bound checked reuse | `omega_engine_woland/tests/test_checked_ddc_reuse.py::test_wrong_fresh_checker_binding_refuses` | Each candidate/seed/premise/contract/checker binding mutation rejects. Native storage prerequisite must be available. |
| DPO independent judge | `omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py::test_structurally_valid_wrong_weight_still_fails_independent_judge` | Structural rewrite is insufficient for mathematical acceptance. |
| Confluence counterexample | `omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py::test_four_exercise_obligations` | Original nonconfluence and honest NOT_CHECKED status remain intact. |
| No-evidence gate | `omega_engine_woland/tests/intergates/test_intergate_input_contract.py::test_terminal_verdict_string_is_insufficient` | A terminal label alone cannot pass an evidence gate. |
| Proof-source custody | `omega_engine_woland/tests/test_lake_candidate_binding.py::test_unrelated_prose_is_not_replaced_by_canonical_proof` | Submitted bytes reach the checker; requires explicit local Lean toolchain and can skip. |

New tests should follow concrete implementations: symmetric permutation/composition laws on exhaustive small typed trees; nonjoinable versus commuting DPO critical pairs; actual rational dual-vector checks in Lean with independently corrupted entries; CPTP/partial-trace preservation of trace and positivity plus non-CP refusals; exact Lyapunov descent with frozen grid quantum and epoch-bound measures. These are requirements and test designs, not existing coverage claims.

## Exhaustive module index

Every physical file appears once below. `T/A/F` are named test functions / assert statements (including helpers) / local fixture definitions. `R* leads` are static lexical associations, not proof of the requirements. The JSON carries all test and assertion lines, helper calls, support-source hashes and fixture bodies. `candidate` means possible test source, not verified collection or execution.

| Module and first test anchor | T/A/F | Provenance; root testpaths | R* leads | Source SHA-256 |
|---|---:|---|---|---|
| [domain/test_oew_qa_evidence_falsification.py](../../../omega_engine_woland/tests/domain/test_oew_qa_evidence_falsification.py#L80) | 13/19/0 | candidate; not selected | R1,R4 | `3c73edee1aee5aeb814d431adc9c98811bc063e0c281158d513ed3b9c20bca14` |
| [geometry/test_checkpoint_hooks.py](../../../omega_engine_woland/tests/geometry/test_checkpoint_hooks.py#L8) | 4/12/0 | candidate; not selected | R1,R4 | `162fa6edb8a5d428526c5c24754d904fc0e48b4d6c611ab13c0d0a933a38c65c` |
| [geometry/test_forge_pfp.py](../../../omega_engine_woland/tests/geometry/test_forge_pfp.py#L71) | 12/38/1 | candidate; not selected | R1,R3,R4,R5 | `870196220cab2bd5d2229ec712dc1c6baec142646bdfb7ea84f9a1c9f174e302` |
| [geometry/test_graph_captures.py](../../../omega_engine_woland/tests/geometry/test_graph_captures.py#L44) | 4/28/1 | candidate; not selected | R1,R3,R4 | `aeff1d615b764cc9f9d67e73e8c3040e3c9b2bba4f916d682adae07956a3902d` |
| [geometry/test_graph_reporting.py](../../../omega_engine_woland/tests/geometry/test_graph_reporting.py#L21) | 4/23/0 | candidate; not selected | R1 | `9527a261935a86b194bd32bce99bc7d51515a5729e6692331c731efa7c260cb8` |
| [geometry/test_native_reporting_outcome.py](../../../omega_engine_woland/tests/geometry/test_native_reporting_outcome.py#L8) | 2/7/0 | candidate; not selected | R1,R3,R4 | `e021e2a785fb40e8890f5901ef883102143cbb3d33d5d28769a3d845a59a9471` |
| [geometry/test_observer_configuration.py](../../../omega_engine_woland/tests/geometry/test_observer_configuration.py#L8) | 3/7/0 | candidate; not selected | R1,R3,R4 | `0272ac4394320faa2e9e2991023de4cff80d016f632cecfd6aa93481e3c3696b` |
| [geometry/test_openrouter_captures.py](../../../omega_engine_woland/tests/geometry/test_openrouter_captures.py#L30) | 3/14/0 | candidate; not selected | R1,R3,R4 | `1847ed560f0a0c13adf75126827c6c3807761a22e335cedfdc052c7ef5768e3b` |
| [geometry/test_pilot035_continuation_replay.py](../../../omega_engine_woland/tests/geometry/test_pilot035_continuation_replay.py#L62) | 3/8/1 | candidate; not selected | R1,R4 | `2c72b41f59b46f6e9fd10c4d726a42009d639f36ebde22332a24df88c00ff2c5` |
| [geometry/test_pilot035_retained_json.py](../../../omega_engine_woland/tests/geometry/test_pilot035_retained_json.py#L11) | 4/2/0 | candidate; not selected | R1 | `3e72ca3bd2cc75f8134996e873d1e421a97e1772e889527a10d8f4480d8f3e53` |
| [intelligence_mining/test_intelligence_miner.py](../../../omega_engine_woland/tests/intelligence_mining/test_intelligence_miner.py#L127) | 14/39/0 | candidate; not selected | R1,R2,R4,R5 | `bbe1409f29050f1facaf1f1f0b1bd8ac79a2e87a6525defa39ebd176dee25538` |
| [intergates/test_intergate_input_contract.py](../../../omega_engine_woland/tests/intergates/test_intergate_input_contract.py#L12) | 13/18/0 | candidate; not selected | R1,R2,R4,R5 | `2ae4c09a42a5975168550646ccb0982b31ee4d5db0bad002b121529c18c4a570` |
| [intergates/test_intergates_evaluator.py](../../../omega_engine_woland/tests/intergates/test_intergates_evaluator.py#L26) | 12/46/1 | candidate; not selected | R1,R4 | `4f663f2271279cfa7ff09a2fc0d8e8764b4537c830e436c62af7a75e1d871421` |
| [intergates/test_source_contract_profile.py](../../../omega_engine_woland/tests/intergates/test_source_contract_profile.py#L26) | 10/20/0 | candidate; not selected | R1,R4,R5 | `c9b2d174ec4dd1811258c8d3fa0970f8dd7fc46163202c84dc52093a8c7138c7` |
| [pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py](../../../omega_engine_woland/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py#L39) | 25/27/0 | candidate; not selected | R1,R4,R5 | `2048059ae3fab308542915bd8b4c76158685652f193fee2ac5eaa2bc22ab4d90` |
| [pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py](../../../omega_engine_woland/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py#L50) | 25/24/0 | candidate; not selected | R1,R3,R4,R5 | `e63a5aec50fdb02df3286af4a8cc5cc05add5fd4dec40042b21e4d8abaaa9ea4` |
| [pilots/c051_exact_lp_solver_with_duals/tests/test_c051_refusal_and_input_crash.py](../../../omega_engine_woland/tests/pilots/c051_exact_lp_solver_with_duals/tests/test_c051_refusal_and_input_crash.py#L54) | 7/15/0 | candidate; not selected | R1 | `8fa5ce79a12b75dde32bffc5229447ded14b873f5a105033ee3454937eac8f88` |
| [pilots/c053_bareiss_fraction_free_matrix_inversion/tests/test_c053_canonical_rationals_and_det_pin.py](../../../omega_engine_woland/tests/pilots/c053_bareiss_fraction_free_matrix_inversion/tests/test_c053_canonical_rationals_and_det_pin.py#L55) | 9/18/0 | candidate; not selected | R1 | `729f8733ab41cdefec3def7106338e77e09de846c4c026b0f1917a4f0635cfe8` |
| [pilots/c054_exact_linear_systems/tests/test_c054_typed_rejections.py](../../../omega_engine_woland/tests/pilots/c054_exact_linear_systems/tests/test_c054_typed_rejections.py#L47) | 7/11/0 | candidate; not selected | R1,R2 | `b2911034f5a13440cfd70396c6a07a2781a8254edb589d0e2a2a9d29e4df767e` |
| [pilots/c055_assignment_with_potentials/tests/test_c055_typed_certificates.py](../../../omega_engine_woland/tests/pilots/c055_assignment_with_potentials/tests/test_c055_typed_certificates.py#L44) | 8/11/0 | candidate; not selected | R1,R2,R4 | `64be8cbb2da7999acc54d9123fff6f31489d268de05615fff0574688d5c329eb` |
| [pilots/evidence/demo004_pfp_learning/live/c005_dev_typed_witness_v3/source_snapshot/omega_engine_education/pilots/demo_004/a_mechanism/c005_hosted_decode_controls/test_c005_bakeoff.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c005_dev_typed_witness_v3/source_snapshot/omega_engine_education/pilots/demo_004/a_mechanism/c005_hosted_decode_controls/test_c005_bakeoff.py#L46) | 17/81/0 | snapshot; not selected | R1,R3,R4,R5 | `7577e217ff9aeebfd1eea2d8bf2527f567e78993a05f390dd2e8f5e51017d5f5` |
| [pilots/evidence/demo004_pfp_learning/live/c005_dev_typed_witness_v4/source_snapshot/omega_engine_education/pilots/demo_004/a_mechanism/c005_hosted_decode_controls/test_c005_bakeoff.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c005_dev_typed_witness_v4/source_snapshot/omega_engine_education/pilots/demo_004/a_mechanism/c005_hosted_decode_controls/test_c005_bakeoff.py#L46) | 17/81/0 | snapshot; not selected | R1,R3,R4,R5 | `7577e217ff9aeebfd1eea2d8bf2527f567e78993a05f390dd2e8f5e51017d5f5` |
| [pilots/evidence/demo004_pfp_learning/live/c005_dev_typed_witness_v5/source_snapshot/omega_engine_education/pilots/demo_004/a_mechanism/c005_hosted_decode_controls/test_c005_bakeoff.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c005_dev_typed_witness_v5/source_snapshot/omega_engine_education/pilots/demo_004/a_mechanism/c005_hosted_decode_controls/test_c005_bakeoff.py#L46) | 17/81/0 | snapshot; not selected | R1,R3,R4,R5 | `7577e217ff9aeebfd1eea2d8bf2527f567e78993a05f390dd2e8f5e51017d5f5` |
| [pilots/evidence/demo004_pfp_learning/live/c011_dev_baseline_v2/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c011_dev_baseline_v2/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py#L34) | 2/4/0 | snapshot; not selected | R1,R4 | `f7dc11c34adbbefd1627b4e1c37b8f418ec899318d2743e3d8211b2bea84bcb1` |
| [pilots/evidence/demo004_pfp_learning/live/c011_dev_typed_witness_v2/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c011_dev_typed_witness_v2/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py#L34) | 2/4/0 | snapshot; not selected | R1,R4 | `f7dc11c34adbbefd1627b4e1c37b8f418ec899318d2743e3d8211b2bea84bcb1` |
| [pilots/evidence/demo004_pfp_learning/live/c011_development_baseline_deepseek/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c011_development_baseline_deepseek/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py#L34) | 2/4/0 | snapshot; not selected | R1,R4 | `f7dc11c34adbbefd1627b4e1c37b8f418ec899318d2743e3d8211b2bea84bcb1` |
| [pilots/evidence/demo004_pfp_learning/live/c011_development_typed_v2/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c011_development_typed_v2/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py#L34) | 2/4/0 | snapshot; not selected | R1,R4 | `f7dc11c34adbbefd1627b4e1c37b8f418ec899318d2743e3d8211b2bea84bcb1` |
| [pilots/evidence/demo004_pfp_learning/live/c011_held_out_transfer_v2/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c011_held_out_transfer_v2/source_snapshot/omega_engine_education/pilots/demo_004/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py#L34) | 2/4/0 | snapshot; not selected | R1,R4 | `f7dc11c34adbbefd1627b4e1c37b8f418ec899318d2743e3d8211b2bea84bcb1` |
| [pilots/evidence/demo004_pfp_learning/live/c021_dev_baseline_v2/source_snapshot/omega_engine_education/pilots/demo_004/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c021_dev_baseline_v2/source_snapshot/omega_engine_education/pilots/demo_004/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py#L34) | 2/7/0 | snapshot; not selected | R1,R4 | `064823deac61b7b7473be7d34d4e6d3c06496d8a075f6c5cd7fd28372acb39cc` |
| [pilots/evidence/demo004_pfp_learning/live/c021_dev_baseline_v3/source_snapshot/omega_engine_education/pilots/demo_004/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c021_dev_baseline_v3/source_snapshot/omega_engine_education/pilots/demo_004/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py#L34) | 2/7/0 | snapshot; not selected | R1,R4 | `064823deac61b7b7473be7d34d4e6d3c06496d8a075f6c5cd7fd28372acb39cc` |
| [pilots/evidence/demo004_pfp_learning/live/c021_dev_typed_witness_v2/source_snapshot/omega_engine_education/pilots/demo_004/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c021_dev_typed_witness_v2/source_snapshot/omega_engine_education/pilots/demo_004/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py#L34) | 2/7/0 | snapshot; not selected | R1,R4 | `064823deac61b7b7473be7d34d4e6d3c06496d8a075f6c5cd7fd28372acb39cc` |
| [pilots/evidence/demo004_pfp_learning/live/c039_dev_baseline_v2/source_snapshot/omega_engine_education/pilots/demo_004/d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c039_dev_baseline_v2/source_snapshot/omega_engine_education/pilots/demo_004/d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law/judge_packet/mutation_suite/test_checker_mutations.py#L33) | 4/0/0 | snapshot; not selected | R1,R4 | `41f631a53b627f87ddc0c1c119ee2bc1f153f950811f6d31d35b46485e1ba069` |
| [pilots/evidence/demo004_pfp_learning/live/c039_dev_typed_witness_v2/source_snapshot/omega_engine_education/pilots/demo_004/d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c039_dev_typed_witness_v2/source_snapshot/omega_engine_education/pilots/demo_004/d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law/judge_packet/mutation_suite/test_checker_mutations.py#L33) | 4/0/0 | snapshot; not selected | R1,R4 | `41f631a53b627f87ddc0c1c119ee2bc1f153f950811f6d31d35b46485e1ba069` |
| [pilots/evidence/demo004_pfp_learning/live/c039_dev_typed_witness_v3/source_snapshot/omega_engine_education/pilots/demo_004/d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law/judge_packet/mutation_suite/test_checker_mutations.py](../../../omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c039_dev_typed_witness_v3/source_snapshot/omega_engine_education/pilots/demo_004/d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law/judge_packet/mutation_suite/test_checker_mutations.py#L33) | 4/0/0 | snapshot; not selected | R1,R4 | `41f631a53b627f87ddc0c1c119ee2bc1f153f950811f6d31d35b46485e1ba069` |
| [pilots/evidence/pfp_ownership_migration_20261012/frozen_sources/omega_engine_education/pfp/infrastructure/po035/test_fixtures.py](../../../omega_engine_woland/tests/pilots/evidence/pfp_ownership_migration_20261012/frozen_sources/omega_engine_education/pfp/infrastructure/po035/test_fixtures.py#L1) | 0/2/0 | snapshot; not selected | R1 | `1e240b5985b10d48df37771318770aaabb3c26c8d1641988177264583a1b9597` |
| [pilots/evidence/pfp_ownership_migration_20261012/frozen_sources/omega_engine_education/pfp/tests/test_pilot_runner.py](../../../omega_engine_woland/tests/pilots/evidence/pfp_ownership_migration_20261012/frozen_sources/omega_engine_education/pfp/tests/test_pilot_runner.py#L83) | 9/48/0 | snapshot; not selected | R1,R2,R4,R5 | `9dc4ab7f2c5debbee732eb658237c8d2513b2ed2be4ef042f45f7f6bf80ddeec` |
| [pilots/optional_rewrite_backends/dspy/test_demo.py](../../../omega_engine_woland/tests/pilots/optional_rewrite_backends/dspy/test_demo.py#L36) | 11/23/0 | candidate; not selected | R1,R2,R3,R4,R5 | `ecb659801e8a2604aacc15fe28a888ecb883d17798f7e5fd4361fa762c717543` |
| [pilots/pilot_0000026/tests/test_cycle.py](../../../omega_engine_woland/tests/pilots/pilot_0000026/tests/test_cycle.py#L26) | 18/68/0 | candidate; not selected | R1,R2,R4,R5 | `699642104e181f22430a5de38f3e0f224c4d3d44b1fdfba8639e3030c58158a4` |
| [pilots/pilot_0000027/tests/test_lp_certificates.py](../../../omega_engine_woland/tests/pilots/pilot_0000027/tests/test_lp_certificates.py#L21) | 25/96/0 | candidate; not selected | R1,R4,R5 | `8846f27969606a7c2dc9a871dce723bbf25b4e02b2320cd533fd9b2e6147947e` |
| [pilots/pilot_0000028/tests/test_packet_profiles.py](../../../omega_engine_woland/tests/pilots/pilot_0000028/tests/test_packet_profiles.py#L38) | 13/71/0 | candidate; not selected | R1,R4,R5 | `24c9df2a67b48973f611237c88e843cd290267560295fac39802737c6c818043` |
| [pilots/pilot_0000029/tests/test_integer_obstructions.py](../../../omega_engine_woland/tests/pilots/pilot_0000029/tests/test_integer_obstructions.py#L20) | 18/72/0 | candidate; not selected | R1,R4,R5 | `e202035366c8e0b679ca8629595d7db23dbdd5d885507da5f871183a9a57da5b` |
| [pilots/pilot_0000030/tests/test_rewrite_information.py](../../../omega_engine_woland/tests/pilots/pilot_0000030/tests/test_rewrite_information.py#L20) | 19/66/0 | candidate; not selected | R1,R4,R5 | `30a452eac8655a904240bd280b9e6b9bea29663a44df30c434489dff66343795` |
| [pilots/pilot_0000031/tests/test_exact_interference.py](../../../omega_engine_woland/tests/pilots/pilot_0000031/tests/test_exact_interference.py#L28) | 16/69/0 | candidate; not selected | R1,R3,R4,R5 | `5b9d630f841086f803dd31798a2e98d2fdd250706f176d58057151ff3881f7bb` |
| [pilots/pilot_0000032/tests/test_three_sector_normalization.py](../../../omega_engine_woland/tests/pilots/pilot_0000032/tests/test_three_sector_normalization.py#L28) | 17/60/0 | candidate; not selected | R1,R4,R5 | `0d4b338dc554c0a4304ab27604c90edac86468158b43310491615db2bab64ae4` |
| [pilots/pilot_0000033/tests/test_sn09_budget_dependency.py](../../../omega_engine_woland/tests/pilots/pilot_0000033/tests/test_sn09_budget_dependency.py#L27) | 7/16/0 | candidate; not selected | R1,R4,R5 | `4c3d82140a16fcec7202c76b44c4b37b50e1767d36b163d5545c33860f73e6a1` |
| [pilots/pilot_0000033/tests/test_sn09_packets_and_loop.py](../../../omega_engine_woland/tests/pilots/pilot_0000033/tests/test_sn09_packets_and_loop.py#L43) | 23/70/0 | candidate; not selected | R1,R4,R5 | `28eed8581fde383f772a712b0c3752ff583dd034c4ed6e3d762d8fccf309b880` |
| [pilots/pilot_0000034/tests/test_trace_replay.py](../../../omega_engine_woland/tests/pilots/pilot_0000034/tests/test_trace_replay.py#L42) | 33/85/0 | candidate; not selected | R1,R2,R4,R5 | `10eea66681d85fef19bbbec86dc8eaa5b1338df232a519bdf5cc722c7c0f6a4d` |
| [pilots/pilot_0000035/tests/test_role_comparison.py](../../../omega_engine_woland/tests/pilots/pilot_0000035/tests/test_role_comparison.py#L33) | 29/90/0 | candidate; not selected | R1,R4 | `87d87970b5aa3b8bebd4b540672222043fbb8b66d61ffc7f4f354b04c382dfdb` |
| [pilots/pilot_0000036/tests/provenance/test_quiz01_provenance.py](../../../omega_engine_woland/tests/pilots/pilot_0000036/tests/provenance/test_quiz01_provenance.py#L21) | 27/83/0 | candidate; not selected | R1,R4 | `3d637577396c71562ac6d11a9f0db957b560ed926839e516e042dca440c2eb23` |
| [pilots/pilot_0000037/tests/quotients/test_quiz02_quotients.py](../../../omega_engine_woland/tests/pilots/pilot_0000037/tests/quotients/test_quiz02_quotients.py#L34) | 27/113/0 | candidate; not selected | R1,R2,R4 | `226ccd35554a3b89f678db9f54ef801e8144cc891becbd31603572135b3a1e4a` |
| [pilots/pilot_0000038/tests/singular_integrals/test_quiz04_integrals.py](../../../omega_engine_woland/tests/pilots/pilot_0000038/tests/singular_integrals/test_quiz04_integrals.py#L53) | 27/127/0 | candidate; not selected | R1,R2,R4,R5 | `50463c61e7ec274993491c2979425bc7018e1e4ece224dce507ab63ddb6d08fc` |
| [pilots/pilot_0000039/tests/intrinsic_geometry/test_quiz05_geometry.py](../../../omega_engine_woland/tests/pilots/pilot_0000039/tests/intrinsic_geometry/test_quiz05_geometry.py#L53) | 27/117/0 | candidate; not selected | R1,R4 | `1326716c7a95e50aed824ec89f3335b04cc36fa0c47a3538fbd3e4f2b9ea6ef8` |
| [pilots/pilot_0000040/tests/cochains/test_quiz06_cochains.py](../../../omega_engine_woland/tests/pilots/pilot_0000040/tests/cochains/test_quiz06_cochains.py#L119) | 25/128/0 | candidate; not selected | R1,R3,R4 | `0af7542d9687d74e3e43f4f621414683e34b2e0e82a369f14ee3a1b43af03c17` |
| [pilots/pilot_0000041/tests/face_activation/test_quiz08_face_activation.py](../../../omega_engine_woland/tests/pilots/pilot_0000041/tests/face_activation/test_quiz08_face_activation.py#L73) | 21/97/0 | candidate; not selected | R1,R4,R5 | `533969802c9d736914e060d846a8556b4c6c947b07d99d5f86ad4d424f494815` |
| [pilots/pilot_0000042/tests/hodge/test_quiz11_hodge.py](../../../omega_engine_woland/tests/pilots/pilot_0000042/tests/hodge/test_quiz11_hodge.py#L148) | 32/110/0 | candidate; not selected | R1,R2,R4 | `ce3b65b88c342102fb36d5ba231e3ed30f43b7905a2abcfca757e407de9d7170` |
| [pilots/pilot_0000043/tests/checkerboard/test_quiz12_checkerboard.py](../../../omega_engine_woland/tests/pilots/pilot_0000043/tests/checkerboard/test_quiz12_checkerboard.py#L48) | 26/85/0 | candidate; not selected | R1,R2,R4 | `a90a31b49f36421dc9f5da109ff58620f4672598cde8061aadae1067a51b93c1` |
| [pilots/pilot_0000044/tests/clique/test_quiz13_clique.py](../../../omega_engine_woland/tests/pilots/pilot_0000044/tests/clique/test_quiz13_clique.py#L111) | 21/89/0 | candidate; not selected | R1,R4,R5 | `9c2f74d11399704394ee18bc2e51e9e4fa81c8a6053fa4c1ef21295ca3b8d7cc` |
| [pilots/pilot_0000045/tests/fan_pairing/test_quiz14_fan_pairing.py](../../../omega_engine_woland/tests/pilots/pilot_0000045/tests/fan_pairing/test_quiz14_fan_pairing.py#L24) | 21/79/0 | candidate; not selected | R1,R4 | `9a1871f8d050e3a589ccbc5e9e1df5640f36d4b2be04c81cc0c1abb38dfa324d` |
| [pilots/pilot_0000046/tests/hodge_companion/test_pilot_0000046_hodge_companion.py](../../../omega_engine_woland/tests/pilots/pilot_0000046/tests/hodge_companion/test_pilot_0000046_hodge_companion.py#L41) | 19/69/0 | candidate; not selected | R1,R4,R5 | `ac9df25aff87281358f90c4b2eb8bdb467e3e7378693ba87d35273bc7c7a60d1` |
| [pilots/pilot_0000047/tests/typed_engine/test_new001_typed_engine.py](../../../omega_engine_woland/tests/pilots/pilot_0000047/tests/typed_engine/test_new001_typed_engine.py#L40) | 22/61/0 | candidate; not selected | R1,R2,R4,R5 | `5d4ec56e4b0f9a4ce3fbea1ca05de7a00c0a27a2ef2d0eba2f6d349421f16388` |
| [pilots/pilot_0000048/tests/glyph_packet/test_new002_glyph_packet.py](../../../omega_engine_woland/tests/pilots/pilot_0000048/tests/glyph_packet/test_new002_glyph_packet.py#L83) | 18/58/0 | candidate; not selected | R1,R4,R5 | `4e8f3b7efcefdb7b149e8dace73c3fe632b0336c2ececdb8e3ec41660ee37175` |
| [pilots/pilot_0000048/tests/glyph_packet/test_pilot23_check.py](../../../omega_engine_woland/tests/pilots/pilot_0000048/tests/glyph_packet/test_pilot23_check.py#L68) | 4/9/1 | candidate; not selected | R1,R4 | `4a6927c01cba94b826a98c5af6686a72ae00f5ad3654ade14db92858e15df4c8` |
| [pilots/pilot_0000049/tests/repair/test_pilot24_bounded_repair.py](../../../omega_engine_woland/tests/pilots/pilot_0000049/tests/repair/test_pilot24_bounded_repair.py#L41) | 13/30/0 | candidate; not selected | R1,R4 | `1ffcde4f497d90479f1c354b716f6fc3d9e08f484cc10fad31e3cdba5e811d46` |
| [pilots/pilot_0000049/tests/repair/test_pilot24_check.py](../../../omega_engine_woland/tests/pilots/pilot_0000049/tests/repair/test_pilot24_check.py#L79) | 5/12/1 | candidate; not selected | R1,R4 | `2ea1afb956aaec4b8088c0a68021c8b15b249b1b5bbdfe118ba025723d0a2617` |
| [pilots/pilot_0000050/tests/templates/test_pilot25_check.py](../../../omega_engine_woland/tests/pilots/pilot_0000050/tests/templates/test_pilot25_check.py#L79) | 5/12/1 | candidate; not selected | R1,R4 | `3cf1f494370816c06361ea7f157edef8ff1cc0c188902b2968b794e9658433c0` |
| [pilots/pilot_0000050/tests/templates/test_pilot25_templates.py](../../../omega_engine_woland/tests/pilots/pilot_0000050/tests/templates/test_pilot25_templates.py#L32) | 7/16/0 | candidate; not selected | R1,R4 | `f8230c2b812b4447d34a0d0d54bcf6a2b5b3aff3fa0cda80a1319d27f40ee21c` |
| [pilots/pilot_0000188/misc/retired_dossier_trials_runner_v1/test_campaign.py](../../../omega_engine_woland/tests/pilots/pilot_0000188/misc/retired_dossier_trials_runner_v1/test_campaign.py#L78) | 11/27/0 | retired; not selected | R1,R2,R4,R5 | `93d2479d4f67793d2e4c7b0b7dced39a92b3f6ea8269677930fd36f45b87268f` |
| [pilots/pilot_0000192/tests/test_c005_predicates.py](../../../omega_engine_woland/tests/pilots/pilot_0000192/tests/test_c005_predicates.py#L24) | 5/5/0 | candidate; not selected | R1,R4 | `f1970c5d250f2c459b36a2fe2867e8fc5735f1854a660dfb117169f1adc7566b` |
| [pilots/pilot_0000192/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000192/tests/test_pilot.py#L17) | 2/2/0 | candidate; not selected | R1,R4 | `d49d6bf0153c3ce4bd15a4555000a3e228ae40d488bf8c39e57e7dd7ef236873` |
| [pilots/pilot_0000193/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000193/tests/test_pilot.py#L17) | 2/2/0 | candidate; not selected | R1,R4 | `d49d6bf0153c3ce4bd15a4555000a3e228ae40d488bf8c39e57e7dd7ef236873` |
| [pilots/pilot_0000194/tests/test_native_q40.py](../../../omega_engine_woland/tests/pilots/pilot_0000194/tests/test_native_q40.py#L52) | 2/4/1 | candidate; not selected | R1,R3,R5 | `8b41dbd620d13bab49f62320a62447db582c1e7fc4f29240782c56d657885282` |
| [pilots/pilot_0000194/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000194/tests/test_pilot.py#L17) | 2/2/0 | candidate; not selected | R1,R4 | `d49d6bf0153c3ce4bd15a4555000a3e228ae40d488bf8c39e57e7dd7ef236873` |
| [pilots/pilot_0000195/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000195/tests/test_pilot.py#L17) | 2/2/0 | candidate; not selected | R1,R4 | `d49d6bf0153c3ce4bd15a4555000a3e228ae40d488bf8c39e57e7dd7ef236873` |
| [pilots/pilot_0000196/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000196/tests/test_pilot.py#L17) | 2/2/0 | candidate; not selected | R1,R4 | `d49d6bf0153c3ce4bd15a4555000a3e228ae40d488bf8c39e57e7dd7ef236873` |
| [pilots/pilot_0000197/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000197/tests/test_pilot.py#L17) | 2/2/0 | candidate; not selected | R1,R4 | `d49d6bf0153c3ce4bd15a4555000a3e228ae40d488bf8c39e57e7dd7ef236873` |
| [pilots/pilot_0000198/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000198/tests/test_pilot.py#L12) | 1/0/0 | candidate; not selected | R1 | `2099e674908de88160eb641e42365abed6c1127b42a2141511ceaa40e24d198b` |
| [pilots/pilot_0000199/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000199/tests/test_pilot.py#L9) | 1/0/0 | candidate; not selected | R1 | `45adb258a9bd647e1a5c703cb1fd1322a466ea4c7b27712db2380c7644e4c2cd` |
| [pilots/pilot_0000200/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000200/tests/test_pilot.py#L9) | 1/0/0 | candidate; not selected | R1 | `f82f920c13a6e6fbb5623a0dafa2c33daa2e56625cd8f9ffdeb2bc3f7618f512` |
| [pilots/pilot_0000201/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000201/tests/test_pilot.py#L9) | 1/0/0 | candidate; not selected | R1 | `66818b0d953d09b9d3f308214d08f96e3851b515dd5399d3a5b660280cf7b20b` |
| [pilots/pilot_0000202/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000202/tests/test_pilot.py#L9) | 1/0/0 | candidate; not selected | R1 | `0901d30bf57bb662c140b5fb8d10637f5b737226f663ba1afbba84ec963fe343` |
| [pilots/pilot_0000203/tests/test_pilot.py](../../../omega_engine_woland/tests/pilots/pilot_0000203/tests/test_pilot.py#L9) | 1/0/0 | candidate; not selected | R1 | `9fca3025bea76170b57eb93ef09308e5578d9c5f16adb9c51338469bef12801b` |
| [pilots/replay_runners/dossier_capsules/test_campaign.py](../../../omega_engine_woland/tests/pilots/replay_runners/dossier_capsules/test_campaign.py#L80) | 17/51/0 | candidate; not selected | R1,R2,R4,R5 | `4675450eb5d79d255555a56f2beec92ae79c6e1be93e4712ea5c219d45854892` |
| [pilots/test_c051_dual_woland_pfp.py](../../../omega_engine_woland/tests/pilots/test_c051_dual_woland_pfp.py#L44) | 3/28/0 | candidate; not selected | R1,R4,R5 | `fb943e02189c07b2ba2ffb5376211494f3f781e817b54daad1957d57f508d36e` |
| [pilots/test_c052_dual_woland_pfp.py](../../../omega_engine_woland/tests/pilots/test_c052_dual_woland_pfp.py#L46) | 3/27/0 | candidate; not selected | R1,R4,R5 | `ce9ba2cf8a277e94f78f87434aa12c4eeeaa1985fb8fff3430975e475ab9e88b` |
| [pilots/test_c053_dual_woland_pfp.py](../../../omega_engine_woland/tests/pilots/test_c053_dual_woland_pfp.py#L46) | 3/27/0 | candidate; not selected | R1,R4,R5 | `e67c7e53ba7531ea0ba786cba2952db95fb5f139665f8a8bbc6f6254c58c5861` |
| [pilots/test_c054_dual_woland_pfp.py](../../../omega_engine_woland/tests/pilots/test_c054_dual_woland_pfp.py#L46) | 3/27/0 | candidate; not selected | R1,R4,R5 | `d3778e7c5421a1c5ffda02c59555e5236c513632e5f6849f663121ce43499020` |
| [pilots/test_c055_dual_woland_pfp.py](../../../omega_engine_woland/tests/pilots/test_c055_dual_woland_pfp.py#L46) | 3/27/0 | candidate; not selected | R1,R4,R5 | `0a615d5816e0438a108a6fac833f11fdaf44807ead41bbdf00e0d592a28b17ac` |
| [pilots/test_c059_dual_woland_pfp.py](../../../omega_engine_woland/tests/pilots/test_c059_dual_woland_pfp.py#L45) | 3/28/0 | candidate; not selected | R1,R4,R5 | `6fbe225334021abe98fd0bd894835177eda292ceee05edb80ad9a1e16e4ae94f` |
| [probes/test_multi_agent_bout_crash_recovery.py](../../../omega_engine_woland/tests/probes/test_multi_agent_bout_crash_recovery.py#L56) | 7/39/0 | candidate; not selected | R1,R2,R4 | `adc1702e51ed475b7a3686507f9f679c853c76710e93d8c977f1031da047d26c` |
| [providers/test_backend_pfp_boundary.py](../../../omega_engine_woland/tests/providers/test_backend_pfp_boundary.py#L20) | 10/35/0 | candidate; selected | R1,R4,R5 | `07c36f39c8afd2de7fcc93f676c56a4285bb896e7e5e683ffeca7c7efc02777e` |
| [providers/test_budget.py](../../../omega_engine_woland/tests/providers/test_budget.py#L25) | 9/19/0 | candidate; selected | R1,R5 | `95223be2b4a81e5773b73088b3ef556d77e56482b71cd2748a43d01d83378a86` |
| [providers/test_completion_contracts.py](../../../omega_engine_woland/tests/providers/test_completion_contracts.py#L109) | 33/59/1 | candidate; selected | R1,R4,R5 | `3c0c6dceb74908a4ba3aa5ff85caa1b2388589349deabeab6fefa35f85dcf16f` |
| [providers/test_completion_failure_bytes.py](../../../omega_engine_woland/tests/providers/test_completion_failure_bytes.py#L22) | 4/16/0 | candidate; selected | R1,R4 | `5a6b21b8ac7552984394cb4cabe842a152979d045e75b94e97d0f1e78e6a805b` |
| [providers/test_contract_test_selection.py](../../../omega_engine_woland/tests/providers/test_contract_test_selection.py#L16) | 3/3/0 | candidate; selected | R1,R4 | `e9aa5f3ee29385f1b3adcb3948974f6658993365536345f3ff9500778a180a16` |
| [providers/test_credential_source.py](../../../omega_engine_woland/tests/providers/test_credential_source.py#L42) | 22/45/1 | candidate; selected | R1,R2,R5 | `bc46f0565db661671c3113b2107346f998277eac809039d78e4b134a328f7721` |
| [providers/test_http_error_custody.py](../../../omega_engine_woland/tests/providers/test_http_error_custody.py#L27) | 4/19/0 | candidate; selected | R1,R4 | `a7e5c54f4d8a7f49c2c17f4401b9c5e01fd0ee5231042f1aa354653cbc619d3f` |
| [providers/test_llm_gateway_pfp.py](../../../omega_engine_woland/tests/providers/test_llm_gateway_pfp.py#L15) | 8/26/0 | candidate; selected | R1,R4 | `8cd7e74d1b1c2a32b372e29bb2825b2c3777c0243e8ed17a0fb9a04e693249f8` |
| [providers/test_llm_proposer.py](../../../omega_engine_woland/tests/providers/test_llm_proposer.py#L29) | 8/13/0 | candidate; selected | R1,R2,R4,R5 | `c0bd2f3365e5d901fe9ab6f4e643267d3a760761c5402877fceb8553c987fc6f` |
| [providers/test_model_backends.py](../../../omega_engine_woland/tests/providers/test_model_backends.py#L62) | 12/29/2 | candidate; selected | R1,R4,R5 | `ea58cdebb2ebb4f98bf62050baaaa601be676949bc8dac14270cc7d6207793d3` |
| [providers/test_model_registry.py](../../../omega_engine_woland/tests/providers/test_model_registry.py#L37) | 10/13/0 | candidate; selected | R1,R5 | `4503fbc9df59eeb49a824136ca9112573da9aad94d062117f681c554d5d0be34` |
| [providers/test_native_functional.py](../../../omega_engine_woland/tests/providers/test_native_functional.py#L49) | 7/13/1 | candidate; selected | R1,R5 | `a0f9c930f78619c8d130b50323dc222c27048a342e15435ef3400d0ecbf15b55` |
| [providers/test_openai_compat_body.py](../../../omega_engine_woland/tests/providers/test_openai_compat_body.py#L27) | 9/40/0 | candidate; selected | R1,R4,R5 | `de5c7819bde76a6dc38b8c30b64284e855851e25b7ddb4796af99d81b578f9e1` |
| [providers/test_openrouter_experiment_deadline.py](../../../omega_engine_woland/tests/providers/test_openrouter_experiment_deadline.py#L57) | 9/15/0 | candidate; selected | R1 | `ee37957750d449b5c2edb5de88895571200b8affbcda2eccae2046d6b2c715fd` |
| [providers/test_openrouter_transport.py](../../../omega_engine_woland/tests/providers/test_openrouter_transport.py#L15) | 6/12/0 | candidate; selected | R1,R2,R4,R5 | `067b59694228f9ed0065f8e061fa7ccd08ed5c22b66481991681abcd8bf85896` |
| [providers/test_pricing_observations.py](../../../omega_engine_woland/tests/providers/test_pricing_observations.py#L34) | 4/10/0 | candidate; selected | R1,R4 | `de6d7facec98ead2096919d8c6545a45f451481c27925ddc24ba4a54929c6366` |
| [providers/test_sakana_adapter.py](../../../omega_engine_woland/tests/providers/test_sakana_adapter.py#L23) | 10/23/0 | candidate; selected | R1,R5 | `dc1b8abbd05b9b66be886e0d45976bcd553de40398fe12b5fbc8aca8b8cba482` |
| [research/test_code_panel_gateway_boundary.py](../../../omega_engine_woland/tests/research/test_code_panel_gateway_boundary.py#L65) | 7/43/1 | candidate; selected | R1,R4,R5 | `ae9770e97c4accb5530cb5ffe26fb314ab8075683b958c602493c81707384270` |
| [research/test_domain_research_ddd_modules.py](../../../omega_engine_woland/tests/research/test_domain_research_ddd_modules.py#L32) | 7/0/0 | candidate; not selected | R1 | `50c9e36dce838f5bf49ec91912c27858082541c04ac6155e23c26a4b1745a685` |
| [research/test_domain_research_disk_io_ast.py](../../../omega_engine_woland/tests/research/test_domain_research_disk_io_ast.py#L44) | 4/0/0 | candidate; not selected | R1,R4 | `a9e405cd52499bc223fbd4ea9892a550d15d4e80d8975a1aaae14e82bae41079` |
| [research/test_http_ingress_limits.py](../../../omega_engine_woland/tests/research/test_http_ingress_limits.py#L53) | 7/24/1 | candidate; selected | R1,R2,R4,R5 | `087888866ad11d4b1f78b06a56d1c63ce33b52e6ecc23657e8f3f6030d7717e9` |
| [research/test_http_pfp_boundary.py](../../../omega_engine_woland/tests/research/test_http_pfp_boundary.py#L37) | 8/47/0 | candidate; not selected | R1,R4,R5 | `ab56977c3c128a8197f4fe4b47653e021981e386672c2b939824330af44dd277` |
| [research/test_increment_pad.py](../../../omega_engine_woland/tests/research/test_increment_pad.py#L38) | 6/18/1 | candidate; selected | R1,R2,R4 | `e6625055b606b72fca719538e41d58fc34cb459b520886b760f32827a6e342f3` |
| [research/test_live_residual_input_boundary.py](../../../omega_engine_woland/tests/research/test_live_residual_input_boundary.py#L90) | 20/54/2 | candidate; selected | R1,R4 | `47ba13bb5692718c63ee4efeeb52049e420395b7087a996118531d886c8ac4db` |
| [research/test_module_identity.py](../../../omega_engine_woland/tests/research/test_module_identity.py#L48) | 6/9/0 | candidate; selected | R1,R5 | `ed244486a7cd5604f4066111723c5828aa515dc33344c01f3e26875da4075cf1` |
| [research/test_oears_host_s1.py](../../../omega_engine_woland/tests/research/test_oears_host_s1.py#L42) | 8/17/1 | candidate; selected | R1,R4 | `efe5ac56562944271e3cd79a2578da538ad196c026bfab57cb5b6ac71fbc95a1` |
| [research/test_oears_host_s2_providers.py](../../../omega_engine_woland/tests/research/test_oears_host_s2_providers.py#L50) | 17/43/0 | candidate; selected | R1,R4,R5 | `ee157f63b5ec53235b420182043ee1ba67c8ac3b10db0d31d1c79cd36d394bf7` |
| [research/test_oears_host_s3_api.py](../../../omega_engine_woland/tests/research/test_oears_host_s3_api.py#L31) | 7/27/1 | candidate; selected | R1,R5 | `eb12ec44cead67337f13411aae74009003e767d8c558f6ddf6218cea86c20e4f` |
| [research/test_oears_host_s4_skeleton.py](../../../omega_engine_woland/tests/research/test_oears_host_s4_skeleton.py#L50) | 8/37/1 | candidate; selected | R1,R4,R5 | `880b462a2165039adf00cd4e2f13a3741848af96f348d372afe41c4abf241f14` |
| [research/test_oears_host_s5_digest_literature.py](../../../omega_engine_woland/tests/research/test_oears_host_s5_digest_literature.py#L60) | 17/75/3 | candidate; selected | R1,R4,R5 | `5436b990f2c65f78ab7eec9b2b742fd2e36d502c40be5275cacebee5773a5d64` |
| [research/test_oears_host_s6_stage_zip.py](../../../omega_engine_woland/tests/research/test_oears_host_s6_stage_zip.py#L63) | 8/87/2 | candidate; selected | R1,R4,R5 | `c895d9b6f115e21a0e0689f51c0be2a8c214b7c932b4250aef2930e310308e84` |
| [research/test_oears_host_s7_dashboard.py](../../../omega_engine_woland/tests/research/test_oears_host_s7_dashboard.py#L36) | 6/63/2 | candidate; selected | R1,R4,R5 | `34dfa61d10c2f913e9f3f3172490729c9e4893e1be607ff1da35cb5238278ee8` |
| [research/test_oears_host_s8_soviet_estate.py](../../../omega_engine_woland/tests/research/test_oears_host_s8_soviet_estate.py#L85) | 12/48/2 | candidate; selected | R1,R4,R5 | `8dfa859b9adde63b4b69cfd1cbb061416e3ae2566c46924d70e4de0503835095` |
| [research/test_oears_host_scale_001_s1_openrouter.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_001_s1_openrouter.py#L42) | 11/21/0 | candidate; selected | R1,R5 | `b62554e3dc852d81905b2b69afc8862e75696eba03eab44a1d7c3bf0679ab129` |
| [research/test_oears_host_scale_001_s2_stage_routes.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_001_s2_stage_routes.py#L30) | 8/30/0 | candidate; selected | R1,R2,R5 | `01bd850ee5a8c3816b7ae72dacde2f0eeec6bdc54bf75445694059e0c736b556` |
| [research/test_oears_host_scale_001_s3_ollama_local.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_001_s3_ollama_local.py#L55) | 16/33/0 | candidate; selected | R1,R5 | `b8a85910910c2715e707fc86bd9bb2f7fdb69b2d5759a555a9d99d8757bf7474` |
| [research/test_oears_host_scale_001_s4_soviet_estate.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_001_s4_soviet_estate.py#L63) | 14/22/0 | candidate; selected | R1,R4,R5 | `00d0edc6474d536b801e9d0f8deea0525611c08d68b496713d5d39310c5c3c41` |
| [research/test_oears_host_scale_002_s1_skill_panel.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_002_s1_skill_panel.py#L39) | 7/19/1 | candidate; selected | R1,R4,R5 | `ecaf270cadf480d9760ac8f9e78fd5fd3ec51804c0fcc75509ac782333ee3b5d` |
| [research/test_oears_host_scale_002_s2_claim_queue.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_002_s2_claim_queue.py#L86) | 9/28/2 | candidate; selected | R1,R4 | `3303a4b8d191207700c5dfe12c73832866040e17cf7e35ec21bb7eff7a9841a2` |
| [research/test_oears_host_scale_002_s3_live_residual.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_002_s3_live_residual.py#L64) | 8/25/1 | candidate; selected | R1,R4 | `11d904a4d3a3b680580a41456e50f7ef1e229c3bccf8c10d68aff1ece94eb6ea` |
| [research/test_oears_host_scale_002_s4_stage5_on_demand.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_002_s4_stage5_on_demand.py#L57) | 11/22/2 | candidate; selected | R1,R4 | `99327ef8cdc57e24867aa742f9a0a3020f7f52be57c8d2f1a8713252962fdc2e` |
| [research/test_oears_host_scale_002_s5_soviet_estate.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_002_s5_soviet_estate.py#L55) | 14/16/2 | candidate; selected | R1,R4 | `d8589f74d805c60f3cbb1adccc5976b4a3d917dbc0686f29c1aa77cc1aaecdee` |
| [research/test_oears_host_scale_003_s3_gemini_provider.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_003_s3_gemini_provider.py#L37) | 9/25/0 | candidate; selected | R1,R5 | `f0dd48679f092b621ab071fdb316ef091bb3fd9c113750959450aad646f53643` |
| [research/test_oears_host_scale_005_s1_warm_cache.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_005_s1_warm_cache.py#L18) | 4/12/0 | candidate; selected | R1,R4 | `79ec48ad921ecb66dc071cad040794512ae092aa8e6714646a78a207d5b418e4` |
| [research/test_oears_host_scale_005_s2_cloud_kill_dispatch.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_005_s2_cloud_kill_dispatch.py#L16) | 7/11/0 | candidate; selected | R1,R4 | `d3e3d20700d15919ae2c5cdcf9907028854cc815b00ba5bfa68476fa2fb5f53a` |
| [research/test_oears_host_scale_005_s3_multi_job_isolation.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_005_s3_multi_job_isolation.py#L15) | 5/7/0 | candidate; selected | R1 | `f3f3a783dce9fee22416c7f24d7acaa340b9da77a2ae599af3156954df08c2e6` |
| [research/test_oears_host_scale_005_s4_soviet_estate.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_005_s4_soviet_estate.py#L32) | 7/9/0 | candidate; selected | R1,R4 | `b7a5a08523bf6cfa89ef14c7a4cebfbad558a986b96f7f1f77c3c1301e84aae0` |
| [research/test_oears_host_scale_006_s1_code_pipeline.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_006_s1_code_pipeline.py#L32) | 10/37/0 | candidate; selected | R1,R2,R4,R5 | `fe0ac34d3f7c12705761123ed33371735e0a0824b6c09886e574e75cdbe6b320` |
| [research/test_oears_host_scale_006_s2_code_panel.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_006_s2_code_panel.py#L26) | 3/12/1 | candidate; selected | R1,R4,R5 | `ee0ce2722d92d8f687bf9a1305093570da211a4f720a3a09ab4fca8cc8bc825d` |
| [research/test_oears_host_scale_006_s3_code_routes.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_006_s3_code_routes.py#L15) | 5/14/0 | candidate; selected | R1,R2,R5 | `09d6f99b2af1c877607157bd9525fd9acd147d8d8440316e7da4aa840157f2dd` |
| [research/test_oears_host_scale_006_s4_soviet_estate.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_006_s4_soviet_estate.py#L24) | 4/7/0 | candidate; selected | R1,R2 | `9197ade3256e65dcb0dd1bb71eddd3b7c8a7c39d6c9b5c54a6b0763806bb24c5` |
| [research/test_oears_host_scale_007_s1_soviet_cheap_routes.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_007_s1_soviet_cheap_routes.py#L25) | 4/9/0 | candidate; selected | R1,R5 | `33c95a8de8f72176b31ed98d66f17e4fdd63f6b9e36bacfa59800400048afad6` |
| [research/test_oears_host_scale_007_s2_multi_host_parity.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_007_s2_multi_host_parity.py#L14) | 3/6/0 | candidate; selected | R1,R2,R4 | `5d64a0caccb016484fafaba4701a775d9f0d29fbac66a474d76a1477590c56ee` |
| [research/test_oears_host_scale_007_s3_cloud_kill_soviet.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_007_s3_cloud_kill_soviet.py#L18) | 3/1/0 | candidate; selected | R1 | `cf7fc9ed4f0fe800798cbb11d6076bf4051325735a7d9ecfea56b88bc3253a84` |
| [research/test_oears_host_scale_007_s4_true_i3_ceremony.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_007_s4_true_i3_ceremony.py#L18) | 6/10/0 | candidate; selected | R1,R4 | `c7f2a3de7326f4a0b0cb82640d3ab6a975260ab4a1dce18ee47488647059f516` |
| [research/test_oears_host_scale_007_s5_saga_honesty.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_007_s5_saga_honesty.py#L13) | 2/5/0 | candidate; selected | R1,R4 | `3be6e423ce1e172c74696cddc5cfbce22f8ac475565ab7bb94cadec8e8a1c603` |
| [research/test_oears_host_scale_nvidia_provider.py](../../../omega_engine_woland/tests/research/test_oears_host_scale_nvidia_provider.py#L30) | 4/9/0 | candidate; selected | R1,R5 | `0a5d28bd52d1eeee564605949d68a81f2d5167bef0eb7412cb7ad5b70968b344` |
| [research/test_oears_host_true_i3_board.py](../../../omega_engine_woland/tests/research/test_oears_host_true_i3_board.py#L18) | 4/12/0 | candidate; selected | R1,R4 | `5a144b9d82313c3fc5eb000eafec2d81072f0f62193a0711c95957d660de374f` |
| [research/test_paper_run_graph_s0.py](../../../omega_engine_woland/tests/research/test_paper_run_graph_s0.py#L49) | 10/34/1 | candidate; selected | R1,R2,R4 | `da4d49d0895901be4ccbd3a4de1e67acb903f0d6559356b2272b760926ac187c` |
| [research/test_pfp_model_routes.py](../../../omega_engine_woland/tests/research/test_pfp_model_routes.py#L36) | 17/100/0 | candidate; not selected | R1,R4,R5 | `9648488266c38ca8a725c6d243f28b39e63dfc79662372fe37aae6f01b62bc1e` |
| [research/test_program_and_merge_apply.py](../../../omega_engine_woland/tests/research/test_program_and_merge_apply.py#L81) | 7/15/3 | candidate; selected | R1,R2,R4 | `dfb9f416a0c1f51358d8ebc1b192d89455312079408efe71149efe66d3697dd9` |
| [research/test_program_map_and_estate_gate.py](../../../omega_engine_woland/tests/research/test_program_map_and_estate_gate.py#L23) | 6/19/0 | candidate; selected | R1,R3 | `dbfc9bd34f1fbaa31fd9205b6b09c3eef0be25ffc8c5024c83ed50d406b14809` |
| [research/test_provider_ingress.py](../../../omega_engine_woland/tests/research/test_provider_ingress.py#L63) | 17/18/0 | candidate; selected | R1,R2,R4 | `dbb34445ee53b1a79d10bb026e43032e5a2761b5630896a1d28f2912c281e3f7` |
| [research/test_provider_json_ingress.py](../../../omega_engine_woland/tests/research/test_provider_json_ingress.py#L104) | 7/28/0 | candidate; selected | R1 | `28d959722a9764c2b6b767fde29c49845ef7f88d36e22e2deb4d2a2b1325b187` |
| [research/test_stage_receipt_custody.py](../../../omega_engine_woland/tests/research/test_stage_receipt_custody.py#L43) | 7/21/0 | candidate; selected | R1,R4 | `0b1e8e9676c0088d67fec16cf89acc42b75670be77194f9b96bdd05b7ec4caaf` |
| [research/test_stage_route_binding.py](../../../omega_engine_woland/tests/research/test_stage_route_binding.py#L53) | 12/56/1 | candidate; selected | R1,R2,R4,R5 | `3c195b2c0bc59ecacd7c310383d1a083cb3511188118cc43419f50972a6a5fcf` |
| [research/test_stage_transition_gates.py](../../../omega_engine_woland/tests/research/test_stage_transition_gates.py#L16) | 4/3/0 | candidate; selected | R1 | `f97340ea54cda7a462808978391f2b772a8b0778b85bdca7e220351ba3e396a0` |
| [research_swarm/test_research_swarm.py](../../../omega_engine_woland/tests/research_swarm/test_research_swarm.py#L26) | 7/45/0 | candidate; not selected | R1,R3,R4,R5 | `615e95f2dc81018bc3f7c70a84b44f1ea8743aef1771249cef04860e71b0052b` |
| [researcher/test_executor_policy.py](../../../omega_engine_woland/tests/researcher/test_executor_policy.py#L8) | 1/3/0 | candidate; not selected | R1,R5 | `a71ba46b84c7d4f4be03f29e8c7e46c7a329e2d25a0decd6334fc0a4f28350f7` |
| [researcher/test_researcher_loop.py](../../../omega_engine_woland/tests/researcher/test_researcher_loop.py#L145) | 12/36/1 | candidate; not selected | R1,R3,R4,R5 | `fdda587c30978b73817f9e759040f9472b688f301ac737f4bc566c89bf19c5b9` |
| [residual_algebra/test_residual_algebra_core.py](../../../omega_engine_woland/tests/residual_algebra/test_residual_algebra_core.py#L64) | 10/64/0 | candidate; not selected | R1,R2,R4,R5 | `2586f66c45db993d4673e562b08efac147bdb4dd2fc22070000f669b224f1d94` |
| [residual_algebra/test_scene_engine_refactor.py](../../../omega_engine_woland/tests/residual_algebra/test_scene_engine_refactor.py#L16) | 11/45/0 | candidate; not selected | R1,R4,R5 | `97f537eeced78127d09c1d9780bab53f2c6d6c6d3ed7f285e20c862990a114b4` |
| [residual_algebra/test_woland_bout_runtime.py](../../../omega_engine_woland/tests/residual_algebra/test_woland_bout_runtime.py#L25) | 5/20/0 | candidate; not selected | R1,R2,R4,R5 | `f0a8cd02b8347842c22eb4010a41d1ce36dec114dcf186cf863b9e6f6fd98827` |
| [spine/test_connection_matrix.py](../../../omega_engine_woland/tests/spine/test_connection_matrix.py#L49) | 19/65/0 | candidate; not selected | R1,R2,R4,R5 | `657f9eb09b22c4e1cf9665e84e85908455374e4a4cfb6480711a84e78271faae` |
| [spine/test_cross_engine_disconnected_contract.py](../../../omega_engine_woland/tests/spine/test_cross_engine_disconnected_contract.py#L28) | 10/37/1 | candidate; not selected | R1,R2,R4,R5 | `fb7208de5d6f1fb27544fdf2e989cb3fb6f19f75ba8fb708c0d272ff1cd0117b` |
| [spine/test_cross_engine_task_binding.py](../../../omega_engine_woland/tests/spine/test_cross_engine_task_binding.py#L27) | 8/24/0 | candidate; not selected | R1,R2,R4,R5 | `c30f6c91b1f24d2bfe7e75a184a57fcf0673ede878cd6b7e5790e33e22c8cf1c` |
| [spine/test_llm_mediation.py](../../../omega_engine_woland/tests/spine/test_llm_mediation.py#L90) | 10/14/0 | candidate; not selected | R1,R5 | `086f674030be163b7bb92ec0dfea927c03f1938a750080491ac50ce37c58ebae` |
| [spine/test_native_anti_skill_ingress.py](../../../omega_engine_woland/tests/spine/test_native_anti_skill_ingress.py#L47) | 9/22/0 | candidate; not selected | R1,R4,R5 | `67bce23210ef6641d4992b88a0a786b6e0117fd74d3da816130b471ca33d8a70` |
| [spine/test_native_cross_engine_pipeline.py](../../../omega_engine_woland/tests/spine/test_native_cross_engine_pipeline.py#L50) | 3/31/0 | candidate; not selected | R1,R2,R4,R5 | `689b5a513ba2e5dacafb939a8e23212e1d0aa122a60a63aded55962fa0464d79` |
| [spine/test_native_immune_screen.py](../../../omega_engine_woland/tests/spine/test_native_immune_screen.py#L20) | 2/4/0 | candidate; not selected | R1,R2,R5 | `2cd15f9d97bc49c4d5a0b6ab94cf24adc3d6aa2014dc5dfc0823399f50e18e70` |
| [spine/test_no_retired_module_paths.py](../../../omega_engine_woland/tests/spine/test_no_retired_module_paths.py#L90) | 2/2/0 | candidate; not selected | R1,R5 | `34f3391456d125ecaee2644a74577ada1d31a57f9b54e1bac26075e0816f8df1` |
| [spine/test_oeeis_candidate_custody.py](../../../omega_engine_woland/tests/spine/test_oeeis_candidate_custody.py#L23) | 12/58/0 | candidate; not selected | R1,R2,R4 | `d8c2026d4a0b9071a0975cb2870e11c164379194f38b2c77f38aa57c3979f12c` |
| [spine/test_op_term_binding.py](../../../omega_engine_woland/tests/spine/test_op_term_binding.py#L38) | 10/13/1 | candidate; not selected | R1,R2,R4,R5 | `652d1bd0c2f5519ff6ac201a1881e3d2d81209a5c7da12e3617d46663cd2ec30` |
| [spine/test_skill_reference_resolution.py](../../../omega_engine_woland/tests/spine/test_skill_reference_resolution.py#L12) | 2/5/0 | candidate; not selected | R1,R4,R5 | `908fa4842f9c8de5c416473a78c950ae3b08cef94c1eacda776971c0648f9b09` |
| [spine/test_specialization_contract.py](../../../omega_engine_woland/tests/spine/test_specialization_contract.py#L39) | 10/30/0 | candidate; not selected | R1,R2,R4,R5 | `c7b2e5e086cb55128d30edf7d2a117a85675c43b53458b8a8fe46b4f917b35c4` |
| [spine/test_swarm_specialization_gate.py](../../../omega_engine_woland/tests/spine/test_swarm_specialization_gate.py#L162) | 7/9/0 | candidate; not selected | R1,R4 | `765c152277c0bea8c9ffca8ed38b684580faf188d66156b995bb8d0196d3e570` |
| [test_add_two_integers_acceptance_demo.py](../../../omega_engine_woland/tests/test_add_two_integers_acceptance_demo.py#L17) | 1/6/0 | candidate; selected | R1,R2,R5 | `3759e8eaf85f2294b8d085e0fb6d5e19a574fc92e09b0abf91526dad2509cbe2` |
| [test_adversarial_m1_1_challenger.py](../../../omega_engine_woland/tests/test_adversarial_m1_1_challenger.py#L71) | 9/31/0 | candidate; selected | R1,R4 | `8bb305244317c4be26c1accae78ac85b8151203a4fd25e250bdfbd022b7ca9b4` |
| [test_adversarial_m1_challenger.py](../../../omega_engine_woland/tests/test_adversarial_m1_challenger.py#L100) | 15/72/1 | candidate; selected | R1,R4,R5 | `7d060bdc0b57c226da716fa53438c39894c021b87467d949aba3dc6e20173068` |
| [test_adversarial_m1_it2_1_challenger.py](../../../omega_engine_woland/tests/test_adversarial_m1_it2_1_challenger.py#L114) | 16/59/0 | candidate; selected | R1,R2,R4 | `4e38a0f0bf59e4670ca9c120a5f8270afe5fe95eb077099d7364834f5d88b29b` |
| [test_adversarial_m1_it2_challenger2.py](../../../omega_engine_woland/tests/test_adversarial_m1_it2_challenger2.py#L40) | 5/42/0 | candidate; not selected | R1,R4,R5 | `346eda2ecfc5ba9543dd6c0f2b6c7358cc7aca9f87ce598be4ad1e747e90ea29` |
| [test_algorithm_receipt_custody.py](../../../omega_engine_woland/tests/test_algorithm_receipt_custody.py#L78) | 7/12/0 | candidate; not selected | R1,R4 | `bc7f6d060c2c53bc73c01dfc1abbe0be71ad6f714ca300102d26c2ba9d80dcf8` |
| [test_architecture_fitness.py](../../../omega_engine_woland/tests/test_architecture_fitness.py#L76) | 8/21/0 | candidate; selected | R1,R2,R4 | `5cc24ce6ffec1abad5065ef704757b7d4c87f2ac4e0c1f0feb20600d50bbf703` |
| [test_ast_lint.py](../../../omega_engine_woland/tests/test_ast_lint.py#L8) | 4/7/0 | candidate; not selected | R1 | `499406987da324eb41dfd4c9cf85dbf54c3bacbd9270fea9be6ff6b78d526418` |
| [test_blocking_challenge_selection.py](../../../omega_engine_woland/tests/test_blocking_challenge_selection.py#L57) | 6/37/0 | candidate; selected | R1,R4 | `ce025729b0416c35f61ef5e720af0b4d4f39d5a3b27e3220724dbeafd3e96c64` |
| [test_bout_execution.py](../../../omega_engine_woland/tests/test_bout_execution.py#L53) | 8/69/0 | candidate; selected | R1,R4 | `d2f345a496019a55ed9b73a60cb17c14ea61616f4bd5f684f29dbd8b5221aab9` |
| [test_bout_journal.py](../../../omega_engine_woland/tests/test_bout_journal.py#L86) | 18/56/0 | candidate; not selected | R1,R2,R3,R4 | `59e844a7767ec431f9f8fd61b49530346025fa6e37a685ee6f1fd28f66c2ab6c` |
| [test_bout_refusal_coverage.py](../../../omega_engine_woland/tests/test_bout_refusal_coverage.py#L488) | 14/34/0 | candidate; selected | R1,R2,R4 | `20b6567bfd9ce61aca093049aaef7755ca597e383d2bb51d9b325dfe1c3593ce` |
| [test_bout_service_units.py](../../../omega_engine_woland/tests/test_bout_service_units.py#L38) | 18/75/0 | candidate; selected | R1,R2,R4 | `1dc83218fc6ba0575b6d75b202b4d8038d933aee4047baac90bb187fb69610e6` |
| [test_bqnf_runtime_interventions.py](../../../omega_engine_woland/tests/test_bqnf_runtime_interventions.py#L191) | 3/10/2 | candidate; not selected | R1,R4,R5 | `7c7a516efd1bf729ad3380ca4b5a9c6dda7b4d8296e005b19ca854e21f6745be` |
| [test_challenge_campaign_cli.py](../../../omega_engine_woland/tests/test_challenge_campaign_cli.py#L11) | 3/14/0 | candidate; not selected | R1 | `174a57cdb983eb5dd47d8024fcffcdd1e2be8c0d6cec47adad876c5f3ac70a41` |
| [test_checked_ddc_reuse.py](../../../omega_engine_woland/tests/test_checked_ddc_reuse.py#L130) | 17/54/1 | candidate; not selected | R1,R3,R4,R5 | `6fcc34809a9e02b0a11b3e1aa0822f98c9696d4fbf9d1e9cf0985694dbf62dbb` |
| [test_circuit_algorithm_evidence.py](../../../omega_engine_woland/tests/test_circuit_algorithm_evidence.py#L65) | 7/31/0 | candidate; not selected | R1,R2,R4 | `b6206bc97d6088c59de372bd8318a3a78a6bfdeff8fcb36d97f7c833b1735fd8` |
| [test_cli.py](../../../omega_engine_woland/tests/test_cli.py#L32) | 38/98/1 | candidate; selected | R1,R2,R3,R4,R5 | `e8c1097284ad1777de2f4af23938a40944ca7aa4f5544abba35f8be6d57cbe9e` |
| [test_coda_hypothesis_fuzzing.py](../../../omega_engine_woland/tests/test_coda_hypothesis_fuzzing.py#L81) | 4/20/0 | candidate; not selected | R1,R3,R4,R5 | `8ee4a9106920d1f1ca19b87f405f111d525a4a2850108e0d184cfb519b06c683` |
| [test_coda_native_subprocess.py](../../../omega_engine_woland/tests/test_coda_native_subprocess.py#L31) | 15/50/1 | candidate; not selected | R1,R3,R4,R5 | `dbef163f9fc59dd79cfb4df546aa5013312e74e628af3347b6de4dbfee5afe5a` |
| [test_compositional_open_games.py](../../../omega_engine_woland/tests/test_compositional_open_games.py#L33) | 4/22/0 | candidate; not selected | R1,R2,R4,R5 | `5435115a842b66e9ca754b39e8cda4976ad248dc478613c6e5357034aeed964e` |
| [test_critique_loop_replay.py](../../../omega_engine_woland/tests/test_critique_loop_replay.py#L66) | 1/40/0 | candidate; not selected | R1,R4 | `d652aa7bdaf1cc0f444cad2d38ab744cf9614d7f95b31a71183bab750adce9ee` |
| [test_critique_pfp_boundary.py](../../../omega_engine_woland/tests/test_critique_pfp_boundary.py#L13) | 7/38/0 | candidate; not selected | R1,R4,R5 | `6519ebcec615d5d4cd07d132d77ab2eec8a4874fdcc7b6ac69672d9d3a2d79bb` |
| [test_ddc_operad_bout_ingress.py](../../../omega_engine_woland/tests/test_ddc_operad_bout_ingress.py#L8) | 2/6/0 | candidate; not selected | R1,R3,R4 | `6da33dc1915d8a42ba2f516c10a8972042cf9e4f2d338cd8687a1b71b2517a05` |
| [test_ddc_program_reuse.py](../../../omega_engine_woland/tests/test_ddc_program_reuse.py#L30) | 7/17/1 | candidate; not selected | R1,R3,R4,R5 | `b3927237bc530c999c7ad3a9235b0c660ea3c8fb7535ac03fc134961b4702fd4` |
| [test_diff_oracle.py](../../../omega_engine_woland/tests/test_diff_oracle.py#L24) | 3/20/0 | candidate; not selected | R1,R4 | `2878205076e897b72ef74c595d0801e2d9cb05bfb7933b8f14d798ce7dfdcf17` |
| [test_digestion_extraction.py](../../../omega_engine_woland/tests/test_digestion_extraction.py#L34) | 26/61/0 | candidate; not selected | R1,R3,R4,R5 | `8d87538aba5d8a4130c8a9a2a1ecd66da347496982953da452bbf2568aebeb2b` |
| [test_end_to_end_multiturn_bout_derivation_target.py](../../../omega_engine_woland/tests/test_end_to_end_multiturn_bout_derivation_target.py#L234) | 8/62/5 | candidate; not selected | R1,R2,R4,R5 | `fea68a99c253b0b65611c2bfdc2fdf8bdf15f8532d29f300896e94ebf14d04db` |
| [test_evidence_gate_review_findings.py](../../../omega_engine_woland/tests/test_evidence_gate_review_findings.py#L118) | 24/58/0 | candidate; selected | R1,R3,R4 | `97c97f2a948bf4c48da00b786c2c8711b9852ec49f44f37ce979a3f35ca1dd2a` |
| [test_fable_long_horizon_critique.py](../../../omega_engine_woland/tests/test_fable_long_horizon_critique.py#L22) | 5/24/0 | candidate; not selected | R1,R4 | `b9dbfdd8807617b7336c65b08a931b74fc57ba467a29ee8e4dc08a564ed904e6` |
| [test_fugu_autophagous_cemetery.py](../../../omega_engine_woland/tests/test_fugu_autophagous_cemetery.py#L49) | 3/19/0 | candidate; not selected | R1,R2,R4 | `1954ea1c3e25aa1d19dfbc77353b00bf8de53b51e93015e44448b65c95d6c921` |
| [test_governance_dispatch.py](../../../omega_engine_woland/tests/test_governance_dispatch.py#L31) | 11/50/0 | candidate; not selected | R1,R2,R3,R4,R5 | `94a7d78437389d495f99615c0182ff3148b342e0603a2721a2dcb3862764d53d` |
| [test_governing_councils_bout_use_case.py](../../../omega_engine_woland/tests/test_governing_councils_bout_use_case.py#L57) | 7/59/1 | candidate; not selected | R1,R4,R5 | `1a23b76df141ee8dad374a4bd26e9aac0689f08fac1b0d2020e08e1f51d38892` |
| [test_governing_councils_input_binding.py](../../../omega_engine_woland/tests/test_governing_councils_input_binding.py#L98) | 5/28/1 | candidate; not selected | R1,R4 | `82406e188c7a1983f429bfc25cd2b52dfb5af9c9fd689e2c0ef1f8b5e2d8525b` |
| [test_graph_boundaries.py](../../../omega_engine_woland/tests/test_graph_boundaries.py#L25) | 11/35/0 | candidate; not selected | R1,R4,R5 | `b3282929913b4cc76888320373dd11592670903032630e4a71aab689df26dab5` |
| [test_graph_ingress_cli.py](../../../omega_engine_woland/tests/test_graph_ingress_cli.py#L19) | 2/15/0 | candidate; not selected | R1,R4,R5 | `86d3189c8cb7b915916ce170419827176c05e430e5eef6aca5d2e13c5cfb5dd0` |
| [test_graph_instruction_ingress.py](../../../omega_engine_woland/tests/test_graph_instruction_ingress.py#L44) | 11/38/0 | candidate; not selected | R1,R4 | `ea1ede276582d3360e177ba4d97ee09337328716a3bd840bf0287d2b9c3f9be0` |
| [test_graph_pfp_boundary.py](../../../omega_engine_woland/tests/test_graph_pfp_boundary.py#L61) | 11/47/0 | candidate; not selected | R1,R4 | `0fa75ddf573aaa1d57d3f7f97b193ab0b64ff1e43c18f4152f56d1865c7f50d1` |
| [test_graph_replay.py](../../../omega_engine_woland/tests/test_graph_replay.py#L35) | 11/27/0 | candidate; not selected | R1,R4,R5 | `21bd9c9ca510eddd10920070c520c6ee5ebfe318f7a4008c236dd3867188b4e9` |
| [test_graph_tasks.py](../../../omega_engine_woland/tests/test_graph_tasks.py#L33) | 13/44/0 | candidate; not selected | R1,R2,R4,R5 | `3ed9cfdf8bd1795ce93bd587901089b01974ed4794f30deab43cc6d163b19245` |
| [test_grobner_variety_contraction_bout.py](../../../omega_engine_woland/tests/test_grobner_variety_contraction_bout.py#L360) | 3/43/0 | candidate; not selected | R1,R2,R4,R5 | `50bfadec74765a2fefb8370a1ae84adbae697bf21a83d708beccd8975dbdb844` |
| [test_honest_gate_falsifiers.py](../../../omega_engine_woland/tests/test_honest_gate_falsifiers.py#L121) | 43/115/0 | candidate; selected | R1,R2,R3,R4,R5 | `7693ed5537ed892c35a86bb7471262a2d6ea26fcdf2af50a93cfed2fac569705` |
| [test_human_projection_adapter.py](../../../omega_engine_woland/tests/test_human_projection_adapter.py#L79) | 17/56/0 | candidate; not selected | R1,R3,R4,R5 | `376f6604c2a54b1cd3fd1c41385e28e61e8c5fb45422e5085837c0f085edab75` |
| [test_ingress_ordering.py](../../../omega_engine_woland/tests/test_ingress_ordering.py#L610) | 25/59/0 | candidate; selected | R1,R2,R4,R5 | `4b08ea683756b366c6660bc0fcb3d7d683b4ca10004b5df8b0b4728d0dd7c70e` |
| [test_koroviev_live_flaw_critique_cemetery.py](../../../omega_engine_woland/tests/test_koroviev_live_flaw_critique_cemetery.py#L236) | 5/48/0 | candidate; not selected | R1,R2,R4,R5 | `2eae17c23daa2dcccf8fa6f65a3aa93cbbc812b80bba00efc75f43a0ca489beb` |
| [test_lake_candidate_binding.py](../../../omega_engine_woland/tests/test_lake_candidate_binding.py#L44) | 7/43/1 | candidate; not selected | R1,R4,R5 | `e503ce7f89746e96da56301b07ba62e8990f8024aab75742930009f5531f76f5` |
| [test_lean4_dual_witness_cross_verification.py](../../../omega_engine_woland/tests/test_lean4_dual_witness_cross_verification.py#L24) | 2/19/0 | candidate; not selected | R1,R2,R3,R4 | `9c9bca3fd87b3c57210829f283d7a8be38b519606217e5c5b30ab628546cbba3` |
| [test_learning_completion.py](../../../omega_engine_woland/tests/test_learning_completion.py#L34) | 4/18/0 | candidate; not selected | R1,R4 | `7813407def624ccfc7bc3f27093fdcd91969060ca39f7faeae23b25a5694e9ce` |
| [test_legacy_rip_manifest_absence_gate.py](../../../omega_engine_woland/tests/test_legacy_rip_manifest_absence_gate.py#L108) | 6/16/0 | candidate; not selected | R1,R4,R5 | `73803e04012992c8a2c6a389a6ff63c347222e7015e8a814050ff7c597206478` |
| [test_level_engine_checker.py](../../../omega_engine_woland/tests/test_level_engine_checker.py#L52) | 11/43/1 | candidate; not selected | R1,R2,R4,R5 | `c82966cbbab51744729a4fa7475ef1958f6ac9c31ec7874df527fb02f4231832` |
| [test_live_configuration_cli.py](../../../omega_engine_woland/tests/test_live_configuration_cli.py#L155) | 13/77/1 | candidate; not selected | R1,R2,R4,R5 | `7c9e4ef35618de1d135ce21017a223fe4997bb92e6d9f50a52cb196b5405a439` |
| [test_matrix_transport_adapter.py](../../../omega_engine_woland/tests/test_matrix_transport_adapter.py#L66) | 11/90/1 | candidate; not selected | R1,R4,R5 | `3f59d8e10f72ec5560d63e159274befe16cc5b78599e2719cdff32b427545dbd` |
| [test_mechanism_cli.py](../../../omega_engine_woland/tests/test_mechanism_cli.py#L19) | 12/50/1 | candidate; not selected | R1,R4,R5 | `c92a2e89bb97d455b2cddd12a56fa5b83a16ed358271856e1ce8f11ae7c7b607` |
| [test_model_backend_budget_reservation.py](../../../omega_engine_woland/tests/test_model_backend_budget_reservation.py#L9) | 3/6/0 | candidate; not selected | R1 | `f70f725fa0aee3ea8967769020c1ff738a5abad2eacf1e784833b0c53b88c6f3` |
| [test_mub6_review_refusals.py](../../../omega_engine_woland/tests/test_mub6_review_refusals.py#L10) | 4/7/0 | candidate; not selected | R1,R4 | `96fab03990c6a99c11cba33295828ad66d93bd6c3b6d3d864f7d04ce14753073` |
| [test_multi_round_repair_bout.py](../../../omega_engine_woland/tests/test_multi_round_repair_bout.py#L53) | 2/29/0 | candidate; not selected | R1,R3,R4 | `fc56fad67d7aaf5a0326e301936fe47ea8e85d5874a58a504768b25587717f46` |
| [test_multivariate_singular_boundary_bout.py](../../../omega_engine_woland/tests/test_multivariate_singular_boundary_bout.py#L283) | 3/46/0 | candidate; not selected | R1,R2,R4,R5 | `3d63d371ad74c83fa8390007f72f3c01faaa03a13030e7f7841b3df11a4631b0` |
| [test_native_c011_composition.py](../../../omega_engine_woland/tests/test_native_c011_composition.py#L7) | 3/16/0 | candidate; not selected | R1,R2,R4,R5 | `077917537e8dd9dea30975fdee806c2d65893977fd88de1baf98f606387c55ee` |
| [test_native_live_retirement.py](../../../omega_engine_woland/tests/test_native_live_retirement.py#L12) | 5/20/0 | candidate; not selected | R1,R4,R5 | `7b85ebeed1573372d31630fc98d3657fbb07db87846b58e34a4bbc5b3399598d` |
| [test_native_runtime.py](../../../omega_engine_woland/tests/test_native_runtime.py#L22) | 5/28/0 | candidate; not selected | R1,R4,R5 | `274e901e8bdf6d67c534debae95297e7b45c8b3a2edd0ef6479c2a94464fefe4` |
| [test_nomos_contract_compliance.py](../../../omega_engine_woland/tests/test_nomos_contract_compliance.py#L49) | 4/22/1 | candidate; not selected | R1,R2,R4,R5 | `c5054195a6bc397c362cba75b1d09ef3d03db0b43f0b47ae7fd7988bacc4ac6b` |
| [test_oewas_signed_ingress.py](../../../omega_engine_woland/tests/test_oewas_signed_ingress.py#L142) | 9/46/0 | candidate; not selected | R1,R2,R4,R5 | `1655d182bcea83005eac008cd730ccaa00db45f29a878604fb7f48dd56259f01` |
| [test_omc_dag_intake.py](../../../omega_engine_woland/tests/test_omc_dag_intake.py#L122) | 7/42/1 | candidate; not selected | R1,R4,R5 | `2a96bd16c042ca6db1c91d2a30b21ab79acc4084648567251ed349e83aa9a7d0` |
| [test_operad_pre_miner_harness.py](../../../omega_engine_woland/tests/test_operad_pre_miner_harness.py#L20) | 2/18/0 | candidate; not selected | R1,R2 | `f83b482f6b29d347856c8f1c5f90f10decc9afbafdd6065f4fd1988915dc07b0` |
| [test_package_imports.py](../../../omega_engine_woland/tests/test_package_imports.py#L22) | 2/1/0 | candidate; not selected | R1 | `0fe69e9ca7b2df538065ad0b11026fc54bc3091640b90cce8f58e817f45c25bb` |
| [test_pfp_teamwork_integration.py](../../../omega_engine_woland/tests/test_pfp_teamwork_integration.py#L108) | 9/40/1 | candidate; not selected | R1,R2,R4,R5 | `07a7d74ab4622d1936ae9f51ae51e88a3d9b8744696a9464ce4c2b14cd5cbc4b` |
| [test_pilot035_play.py](../../../omega_engine_woland/tests/test_pilot035_play.py#L15) | 7/16/0 | candidate; not selected | R1,R2,R4,R5 | `1fbaaae87d7d2e43167c38bf6af457962045ad2cbe4a0130c01c5ff7c8e83deb` |
| [test_pilot_owner_migration.py](../../../omega_engine_woland/tests/test_pilot_owner_migration.py#L15) | 1/28/0 | candidate; not selected | R1,R4,R5 | `34c317dde8260ca864e872582ba517f89260374f1a56a0981c85b7e15c7e2bf9` |
| [test_prime_descent_adapter.py](../../../omega_engine_woland/tests/test_prime_descent_adapter.py#L39) | 9/36/0 | candidate; not selected | R1,R4,R5 | `e171de061b6d199e7789567ded53ee24a36c27a018f5cd3753272c1e43161eab` |
| [test_prior_art_native_transition_composition.py](../../../omega_engine_woland/tests/test_prior_art_native_transition_composition.py#L20) | 12/79/1 | candidate; not selected | R1,R3,R4,R5 | `9ad1ffc2491d35ebd2efa738925e62ef447fc087050ededa87d622490c6cb714` |
| [test_product_mgmt_bout_use_case.py](../../../omega_engine_woland/tests/test_product_mgmt_bout_use_case.py#L57) | 7/58/1 | candidate; not selected | R1,R4,R5 | `859f8608fc2f91da9e7a22f8a29a36a3b0fbff6f4a47c4cfa3580e0d8e0f543a` |
| [test_prompt_family.py](../../../omega_engine_woland/tests/test_prompt_family.py#L60) | 13/41/0 | candidate; not selected | R1,R2,R4,R5 | `495c4c56f881b44b4a037b1bae6bc2a490f9147d6fd4b191d4805fd47328efb8` |
| [test_prompt_family_binder.py](../../../omega_engine_woland/tests/test_prompt_family_binder.py#L37) | 10/10/0 | candidate; not selected | R1,R2,R4,R5 | `811562176df02c9ccf5d9f703d4751c8cb8a9cadf0cba5b1fea28355a89e9226` |
| [test_rebased_swarm_spoe_aliases.py](../../../omega_engine_woland/tests/test_rebased_swarm_spoe_aliases.py#L77) | 4/26/1 | candidate; not selected | R1,R3,R4,R5 | `80490f4c4e9d2a4b2ff60c6c875d2e08658eba363bde7d6e1e3e2c8838903e4a` |
| [test_report_learning.py](../../../omega_engine_woland/tests/test_report_learning.py#L29) | 9/28/0 | candidate; not selected | R1,R2,R4 | `273ad3c75766d728d8b7addb1edccc4dc85ca75b682330d7ee35b64243309d9f` |
| [test_report_operation.py](../../../omega_engine_woland/tests/test_report_operation.py#L53) | 9/38/1 | candidate; not selected | R1,R3,R4,R5 | `46176db22ab1a4478d35237662a42a7cc896efa05b350e9d4d206ab0fa70eb3f` |
| [test_retinue_22_cast_totality.py](../../../omega_engine_woland/tests/test_retinue_22_cast_totality.py#L48) | 4/17/0 | candidate; not selected | R1,R2,R4 | `50bc9406d0d131cd289c2aadf7923767b59718b248de5c1eeb9047ab8e63d7a6` |
| [test_retired_facade_removed.py](../../../omega_engine_woland/tests/test_retired_facade_removed.py#L20) | 3/6/0 | candidate; selected | R1,R5 | `f633247c166670231c186a0cea0624f24020d93357c26ebd91ba769130367346` |
| [test_rust_cochain_adapter_parity.py](../../../omega_engine_woland/tests/test_rust_cochain_adapter_parity.py#L66) | 17/127/0 | candidate; not selected | R1,R2,R4,R5 | `c05b5cdec54d76ace02772b43ee994c76395e2cd22f9b40c297f1a68512d8034` |
| [test_seat_routing.py](../../../omega_engine_woland/tests/test_seat_routing.py#L48) | 14/35/0 | candidate; not selected | R1,R4,R5 | `6cc05ca66b86550ecbec97fe16c5c2959ae80df651298df671a62c89511ad9ce` |
| [test_skill_learning_notice.py](../../../omega_engine_woland/tests/test_skill_learning_notice.py#L55) | 2/15/0 | candidate; not selected | R1 | `4709f210f25433554163aa221c8fa56c49a66a25a4c5350e67d12b6eee0fd8f7` |
| [test_skill_run_ic_routing.py](../../../omega_engine_woland/tests/test_skill_run_ic_routing.py#L17) | 2/4/0 | candidate; not selected | R1,R4 | `dd552f7cce5cae44542008a3d9908b1c15ec72c16aeb11acd5a64744609e9cf8` |
| [test_skill_work_status.py](../../../omega_engine_woland/tests/test_skill_work_status.py#L51) | 8/31/1 | candidate; not selected | R1,R4 | `0295e9a9c021c52a4fcfb0a2df2ff71bbd1f9a44e56fb709d09554e29b3e5da8` |
| [test_software_dev_bout_use_case.py](../../../omega_engine_woland/tests/test_software_dev_bout_use_case.py#L58) | 7/50/1 | candidate; not selected | R1,R4 | `5d30e10c917fbe84141a0a83a5a53629a25dd41994ccfeb69c3121d13a953ed5` |
| [test_soviet_gate_cli.py](../../../omega_engine_woland/tests/test_soviet_gate_cli.py#L11) | 2/7/0 | candidate; not selected | R1 | `dd1dc41655299d0fe5fa96a102b77668a651ec4b46e9937207523333423875d9` |
| [test_spec_001_exact_admission.py](../../../omega_engine_woland/tests/test_spec_001_exact_admission.py#L40) | 4/22/0 | candidate; not selected | R1,R4,R5 | `a5bc98753f049bf5a08ee43f0ec216f42fe499bc1857501427413441d74c5b58` |
| [test_sprint2_7act_bout.py](../../../omega_engine_woland/tests/test_sprint2_7act_bout.py#L26) | 2/22/0 | candidate; selected | R1,R4 | `38ab6c7e061396aa47e97893f62099741442b5323026c74e18735a5fe82133e8` |
| [test_structurebench_quad_persistence.py](../../../omega_engine_woland/tests/test_structurebench_quad_persistence.py#L41) | 3/19/0 | candidate; selected | R1,R4 | `c648c8efa8fd76e36b26cd698bab67413b0e0385e2a7c2072fb8d89e10014615` |
| [test_teamwork.py](../../../omega_engine_woland/tests/test_teamwork.py#L61) | 13/58/1 | candidate; not selected | R1,R4,R5 | `4a795d12cc4188eac2f23af5ad77191ba59446e5fffbd9bbc589424f47e407df` |
| [test_teamwork_checked_query.py](../../../omega_engine_woland/tests/test_teamwork_checked_query.py#L81) | 5/25/1 | candidate; not selected | R1,R4 | `8fe28a3a6bc258741c39889c7dd29ab034e7f911a02bd5f3af488fc3ebecdecc` |
| [test_teamwork_checked_reuse.py](../../../omega_engine_woland/tests/test_teamwork_checked_reuse.py#L30) | 3/8/0 | candidate; not selected | R1 | `2062858ddd74d142427ace6f507227e6eee69ba158f70bc0a2d235fe7bb37025` |
| [test_teamwork_checked_reuse_cli.py](../../../omega_engine_woland/tests/test_teamwork_checked_reuse_cli.py#L63) | 6/20/1 | candidate; not selected | R1,R4 | `5570dc8bbdc331e0021a17e28806190c59735bab0c271e0f1dd594994287804c` |
| [test_teamwork_cleanup.py](../../../omega_engine_woland/tests/test_teamwork_cleanup.py#L120) | 16/47/4 | candidate; not selected | R1,R4,R5 | `b023ea80fcf34f6529412c235462acb35161df1ff31ebe538b5109c45ad5a85c` |
| [test_teamwork_cli.py](../../../omega_engine_woland/tests/test_teamwork_cli.py#L51) | 11/59/1 | candidate; not selected | R1,R4,R5 | `2b8662012a9a70c3c5fd146132ad3951c5ea59593dfdc3b4ebae507369d27b85` |
| [test_teamwork_compact_profile.py](../../../omega_engine_woland/tests/test_teamwork_compact_profile.py#L31) | 8/21/0 | candidate; not selected | R1,R4,R5 | `b7d6653e9376bc4b6a5ce4b9a1d88c2bc56360fd84afffa95dc63152a73b54d8` |
| [test_teamwork_compact_v2.py](../../../omega_engine_woland/tests/test_teamwork_compact_v2.py#L68) | 6/84/1 | candidate; not selected | R1,R2,R4,R5 | `b35d1ad1d23c0aad318754537cd9b9120d42189cb0a77b9371ed858279aa3ace` |
| [test_teamwork_continuation.py](../../../omega_engine_woland/tests/test_teamwork_continuation.py#L85) | 13/57/1 | candidate; not selected | R1,R4,R5 | `bd94d4a98c0d4149621c1b60a771d19160e18d82781cf96d2411a859a0e53c3e` |
| [test_teamwork_ddc_host.py](../../../omega_engine_woland/tests/test_teamwork_ddc_host.py#L29) | 12/38/1 | candidate; not selected | R1,R2,R3,R4,R5 | `be105b07888da669cc3457f253efd6372f6ed220109ddffa566eedabe800eb7b` |
| [test_teamwork_digestion.py](../../../omega_engine_woland/tests/test_teamwork_digestion.py#L127) | 21/94/1 | candidate; not selected | R1,R4,R5 | `21f2249b66bbf3d702e9752d3e832b764102d8d08807569d8e84b3b5acb6022d` |
| [test_teamwork_factory.py](../../../omega_engine_woland/tests/test_teamwork_factory.py#L17) | 8/16/0 | candidate; not selected | R1,R4,R5 | `f6dbb22490fc73b1e4c9795933388d423f10ad61c08acea17fb47876d671da57` |
| [test_teamwork_ide_gate.py](../../../omega_engine_woland/tests/test_teamwork_ide_gate.py#L64) | 7/41/1 | candidate; not selected | R1,R4,R5 | `2c37de6c1a6b08655149d93c0529d5cdeb59abf9b0b23e4320cfdbcba96e1b99` |
| [test_teamwork_installed.py](../../../omega_engine_woland/tests/test_teamwork_installed.py#L91) | 1/7/0 | candidate; not selected | R1,R4 | `a2084595e2b3df99ce01dfbfff3f44c43a54d1b93e4b9a9e83176d9bdbe9cd36` |
| [test_teamwork_kernel_learning_privacy.py](../../../omega_engine_woland/tests/test_teamwork_kernel_learning_privacy.py#L11) | 1/6/0 | candidate; not selected | R1,R4,R5 | `422133e5690fa83dd3ccdacb7b079a79b9c5bd05048f4f87cd001c31f88df101` |
| [test_teamwork_kernel_observation.py](../../../omega_engine_woland/tests/test_teamwork_kernel_observation.py#L62) | 11/40/0 | candidate; not selected | R1,R4,R5 | `c549edecb64ffe1ccb8ba4c6abe39948eeacf70fe5aa1f34bbf3c3ba9b3cc8b9` |
| [test_teamwork_learning_context.py](../../../omega_engine_woland/tests/test_teamwork_learning_context.py#L17) | 2/13/0 | candidate; not selected | R1,R4 | `a7a3e13076e037a7de9ac42dc820f97695841272d43b3c95198d229715152be7` |
| [test_teamwork_learning_readback.py](../../../omega_engine_woland/tests/test_teamwork_learning_readback.py#L23) | 1/5/0 | candidate; not selected | R1,R4,R5 | `3e3b182a58005078214f2e3ec799a6fc58437c3413e664f6c75e182cd859eb40` |
| [test_teamwork_native_gates.py](../../../omega_engine_woland/tests/test_teamwork_native_gates.py#L50) | 9/53/1 | candidate; not selected | R1,R4,R5 | `b7c285b1b004a528e41a49dee671b1dfddde14168b818cd1d48958db3ae1472f` |
| [test_teamwork_native_host_facts.py](../../../omega_engine_woland/tests/test_teamwork_native_host_facts.py#L49) | 6/25/1 | candidate; not selected | R1,R4,R5 | `1fee819e890e4e367e91ac058efbc7e5cb15966b36f5e4db86999db80ef06680` |
| [test_teamwork_openrouter.py](../../../omega_engine_woland/tests/test_teamwork_openrouter.py#L78) | 18/62/1 | candidate; not selected | R1,R4,R5 | `d64f0c874b562bcd2edc220804176cf39cdf5f36f294ba7f06bc8c76c523921b` |
| [test_teamwork_pfp.py](../../../omega_engine_woland/tests/test_teamwork_pfp.py#L31) | 6/40/1 | candidate; not selected | R1,R4,R5 | `1f9e7f63762520879e747f373a91d74a7d09c1699420f0c576ef61f08b7b4c89` |
| [test_teamwork_plain_digestion.py](../../../omega_engine_woland/tests/test_teamwork_plain_digestion.py#L28) | 5/32/0 | candidate; not selected | R1,R4,R5 | `a30479336ece4d723057c03d496112a18a21bb57777f8db4da658902a387afe2` |
| [test_teamwork_process_observation.py](../../../omega_engine_woland/tests/test_teamwork_process_observation.py#L42) | 11/39/0 | candidate; not selected | R1,R2,R4,R5 | `b52504aeba8b8bfcea4e4070c20276c7025c6eef5ab37d7a494195d9bfa786a6` |
| [test_teamwork_reporting.py](../../../omega_engine_woland/tests/test_teamwork_reporting.py#L28) | 5/29/0 | candidate; not selected | R1,R3,R4,R5 | `af5d10a4e94482969905bca50928ea6ac05b9f0596f3818ebea122458620ce4b` |
| [test_teamwork_reports.py](../../../omega_engine_woland/tests/test_teamwork_reports.py#L31) | 5/23/0 | candidate; not selected | R1,R4 | `99c826469faebdfaec870c0a22f57b25fb0b446198b4613c756e572162fe9dbb` |
| [test_teamwork_resource_observation.py](../../../omega_engine_woland/tests/test_teamwork_resource_observation.py#L34) | 6/22/0 | candidate; not selected | R1,R4,R5 | `8a551142c6c4f6a23e0f54f8f31036f310ca3346387a15a40b8b04ab0aaa2aab` |
| [test_teamwork_retinue_adversarial.py](../../../omega_engine_woland/tests/test_teamwork_retinue_adversarial.py#L51) | 21/42/2 | candidate; not selected | R1,R4,R5 | `3127698430b46caa809e11e7f4342357bcd1c3245f495e68e7e289dfa3c26508` |
| [test_teamwork_routing.py](../../../omega_engine_woland/tests/test_teamwork_routing.py#L50) | 11/42/0 | candidate; not selected | R1,R2,R4,R5 | `31546a569412dd2c8c2541f6012ddf8fa7587228bfa0655fee08db42b325001a` |
| [test_teamwork_semantic_review.py](../../../omega_engine_woland/tests/test_teamwork_semantic_review.py#L34) | 2/27/0 | candidate; not selected | R1,R4,R5 | `5a65afc76dac53fb253ca39f5dfb73719d1e2630b16f6877c65e31c45e593586` |
| [test_teamwork_source_profile.py](../../../omega_engine_woland/tests/test_teamwork_source_profile.py#L24) | 4/9/0 | candidate; not selected | R1,R4,R5 | `16d3cc514875592ec6a66e760e4271dcdedc6b8532ddb78f2c8810766092cc5f` |
| [test_teamwork_v3.py](../../../omega_engine_woland/tests/test_teamwork_v3.py#L48) | 10/59/0 | candidate; not selected | R1,R4,R5 | `9eaaf26dabca5a088b6705a8ee46c32eb4001b28abde37a1335050ebf78dd983` |
| [test_thanatos_bout_use_case.py](../../../omega_engine_woland/tests/test_thanatos_bout_use_case.py#L57) | 7/57/1 | candidate; not selected | R1,R4,R5 | `51682accd0d4710aa3af236b96e9a202fe9029db4f94d1d88ce3df35629777b3` |
| [test_the_master_live_routed_bout.py](../../../omega_engine_woland/tests/test_the_master_live_routed_bout.py#L50) | 4/37/0 | candidate; not selected | R1,R4,R5 | `5e47d10e1ea1e8efed3fe0b539a02f372e6a13d526d1e6b99ab0f6a66fc9d52e` |
| [test_the_master_seed_prover_bout.py](../../../omega_engine_woland/tests/test_the_master_seed_prover_bout.py#L58) | 7/51/0 | candidate; not selected | R1,R4 | `3b566e3febceeb868ce1552e12992f0505c9b47355b9f9efe880c49b2499a5ac` |
| [test_truthful_turn_content.py](../../../omega_engine_woland/tests/test_truthful_turn_content.py#L64) | 9/67/0 | candidate; selected | R1,R4,R5 | `9ca5921d864753c338477c85d38cb0b348d547b96d69c0bd299f3f687343c1e5` |
| [test_turn_and_terminal_truth.py](../../../omega_engine_woland/tests/test_turn_and_terminal_truth.py#L28) | 7/24/0 | candidate; selected | R1,R2,R4 | `19bfb7271ce55b64f7a24c1704a6a01c7120588b20f3b9c92829af2bc451ec6a` |
| [test_versioned_symbol_game_connector.py](../../../omega_engine_woland/tests/test_versioned_symbol_game_connector.py#L39) | 6/18/0 | candidate; not selected | R1,R2,R4,R5 | `7c03b302cfb06a5c0f0cb4d56c7025f7295757efe589f40e1bd1c7429e5c13b2` |
| [test_woland_council_loader.py](../../../omega_engine_woland/tests/test_woland_council_loader.py#L9) | 2/14/0 | candidate; selected | R1 | `e035d15cceac25972459b5b0724ec6806f24875ff0563679fb080d4ba23824ad` |
| [test_woland_hella_koroviev_debate.py](../../../omega_engine_woland/tests/test_woland_hella_koroviev_debate.py#L37) | 9/32/2 | candidate; not selected | R1,R4 | `c83a427f19660101e0c6fe3f1ab5a8a268e8492311fb9785a178d3e44538fa0a` |
| [test_woland_phi_qualification.py](../../../omega_engine_woland/tests/test_woland_phi_qualification.py#L150) | 6/21/0 | candidate; selected | R1,R4 | `5576b60b217f02cdead1a435bfad0a96103183c9a8b19701ce4baee8cfa4c3f5` |
| [test_woland_profile.py](../../../omega_engine_woland/tests/test_woland_profile.py#L93) | 6/22/0 | candidate; selected | R1,R2,R4 | `10f1a691d5a1f6a2c9184676952dec3142f152604b49ab3ba013b8db9f8f5acb` |
| [test_woland_scene_locations.py](../../../omega_engine_woland/tests/test_woland_scene_locations.py#L98) | 12/23/1 | candidate; not selected | R1,R4,R5 | `1d5f6afd294677de90ac7febdd635b9490b416aa33220dbf7c275ad4a19ad7eb` |
| [test_woland_swarm.py](../../../omega_engine_woland/tests/test_woland_swarm.py#L26) | 9/53/0 | candidate; selected | R1,R2,R4 | `e8f9c94e946333a14fd356e5b564135774b16a8e40c67ef442e014f01a73a89a` |
| [test_woland_thymus_gate_integration.py](../../../omega_engine_woland/tests/test_woland_thymus_gate_integration.py#L103) | 14/39/2 | candidate; not selected | R1,R2,R4,R5 | `1bcf45550a9ab3f8e654a7dc7af787ff6db3525b81e0ff8a896825c3f75641d5` |

## Reproduction and artifact integrity

Extraction: `python3 /workspace/scratch/oepfp-audit/extract_woland_tests.py`, followed by `python3 /workspace/scratch/oepfp-audit/enrich_woland_audit.py` and `python3 /workspace/scratch/oepfp-audit/write_woland_synthesis.py`. These scripts parse source and write scratch artifacts; they do not import or execute tests.

The inventory is pinned to source-byte hashes and HEAD. A changed file requires a fresh audit. The source-manifest digest covers the sorted full 308-file test list; supporting-source hashes include root pytest configuration and the two Lean files discussed above.
