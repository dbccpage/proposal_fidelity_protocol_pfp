# Shared runtime and checker triage

Reviewed all **15 requested owners**: 10 directories and five root files. Recommend consolidation into existing owners for all 15, retaining their reusable mechanisms. **No new workflow family; no deletion performed.**

Scope: **1028 tracked incoming files** and **292 ignored bytecode/cache extras**. Compared 157 source-like files; 82 have an exact canonical match. Byte equality is custody evidence, not the sole basis for a verdict.

The JSON report carries per-source hashes/ranges, explicit body/diff review levels, canonical mappings, unread supporting/data paths and QM prerequisites. No protected QM seed, private storage, credentials or third-party dependency code was read. No old answer or target paper was used as a new benchmark input.

**Fresh verification:** 29 synthetic offline behavior probes; all expected observations reproduced. Some assertions intentionally reproduce defects. No archived case bank or provider run was executed.

- C052: both judges accept capacity 1.9 after int() truncation. Agreement is not adequate integer ingress.
- C059: SQLite and Python oracle disagree on TEXT COALESCE truth; null, heading, empty-suite and read-only controls pass only the tested finite inputs.
- C054/C055: first judge accepts UNKNOWN plus a valid witness; the second and paired gate reject it. This narrows the earlier first-checker-only observation.
- Ladder: H0 retains an incomplete record and H2 retains a nonmonotone curve; favorable self-test inputs do not establish experiments or declared significance.
- SQLite store: mutable replacement, vacuous empty-checker pass and truthy nonboolean acceptance require a separate custody/acceptance boundary.
- Reply kit: source hashes omit instruction; generic JSON parse admits NaN. Domain callbacks and full request binding remain necessary.
- Judge audit: normalization can accept contradictory verdict/accepted fields; leakage and independence/timing checks are bounded diagnostics, not proofs.
- Replay: preserve additional imported exact legacy source-key sets and explicit owner fallback differences before consolidation.

| Owner | Reusable mechanism | Existing family | Verdict |
|---|---|---|---|
| `c051_exact_lp_solver_with_duals` | exact_primal_dual_certificate_and_typed_refusal | WF11 | duplicate_candidate |
| `c052_maxflow_mincut_certificates` | primal_flow_dual_cut_certificate | WF11 | duplicate_candidate |
| `c053_bareiss_fraction_free_matrix_inversion` | exact_matrix_certificate_with_independent_determinant_pin | WF11 | duplicate_candidate |
| `c054_exact_linear_systems` | solution_rank_nullity_or_left_null_certificate | WF11 | duplicate_candidate |
| `c055_assignment_with_potentials` | assignment_dual_potentials_or_Hall_obstruction | WF11 | duplicate_candidate |
| `c059_sql_null_total_query_synthesis` | dual_relational_oracles_with_bag_and_NULL_boundary_checks | WF11 | duplicate_candidate |
| `challenge_suite` | source_bound_two_stage_failure_rule_transfer | WF19, WF12 | duplicate_candidate |
| `judge_packet_audit` | offline_checker_adequacy_and_custody_audit | WF23 | duplicate_candidate |
| `certified_ladder` | registered_cost_ladder_with_bounded_hypothesis_reporting | WF22 | duplicate_candidate |
| `replay_runners` | hash_bound_historical_replay_and_finite_witness_capsules | WF18, WF8 | duplicate_candidate |
| `cot_miner.py` | unadmitted_failure_pattern_mining | WF3, WF14, WF19 | duplicate_candidate |
| `pilot_reply_kit.py` | caller_supplied_reply_custody_and_domain_grade_adapter | WF1, WF13 | duplicate_candidate |
| `sqlite_pilot_store.py` | run_record_storage_and_callback_replay | WF18, WF11 | duplicate_candidate |
| `offline_evaluator.py` | historical_observation_regrade_without_efficacy_promotion | WF18, WF13 | duplicate_candidate |
| `live_evaluator.py` | retired_live_route_with_bound_offline_regrade | WF18, WF1 | duplicate_candidate |

## c051_exact_lp_solver_with_duals

Reusable exact LP certificate validation, with a separately implemented rational checker and a reference self-consistency harness.

**Mathematics:** For max c^T x with Ax<=b and x>=0: primal/dual feasibility and c^T x=b^T y certify optimality; a nonnegative Farkas vector certifies infeasibility; feasible base point plus improving recession ray certifies unboundedness. Canonical rational strings are checked separately from those equations.

The two actual judges contain substantive mathematics already owned by WF11 and its certified-challenge task package. The four-line participant TASK is much thinner than the full design, which asks for a schema, frozen synthesis, independent native validation and matched model experiments. The participant runner executes a supplied Python solve function in-process; it is not the proposed sandbox. The commit_reveal runner labels reference self-consistency and explicitly computes hashes at reveal time, not before hidden-case access.

**Execution:** Reference/participant routes are offline. No C051 model-matrix source is in this assigned tracked root. Design and findings are historical/planned evidence, not fresh provider execution.

**Canonical difference:** Judge mathematics and reference implementations match existing owners; differences in runners/generators/tests concern monorepo import prefixes, root sentinels, output custody paths and Adversary/Woland names. These path changes can break execution even when the certificate equations are identical.

**Recommendation:** Consolidate the two exact LP judges and their negative controls into the current WF11 task owner. Retain one shared self-consistency harness with task configuration. Keep the original protocol and historical findings as provenance; do not label the self-check as a sealed model experiment.

**QM prerequisite:** A QM application needs an explicit proved reduction to this rational LP, typed input bounds and an independent adequacy check. A valid LP certificate alone does not establish the QM premises.

**Review ceiling:** Full both-judge and primary-protocol reads; generated case banks and reference-solver internals were not audited for completeness. Secondary implementation is separate Python arithmetic, not evidence of separate author, separate trust domain or native parity.

Evidence: `pilots/anomalon_woland/c051_exact_lp_solver_with_duals/docs/c051_exact_lp_solver_with_duals.md` L1–143 (2535ecdc2a1a), `pilots/anomalon_woland/c051_exact_lp_solver_with_duals/participant_packet/TASK.md` L1–4 (5bd12045d3c5), `pilots/anomalon_woland/c051_exact_lp_solver_with_duals/judge_packet/independent_checker.py` L1–176 (dc03c61acdb1), `pilots/anomalon_woland/c051_exact_lp_solver_with_duals/participant_packet/runner.py` L1–147 (8e7db9f5ba75), `pilots/anomalon_woland/c051_exact_lp_solver_with_duals/tests/test_c051_refusal_and_input_crash.py` L1–140 (8fa5ce79a12b), `pilots/anomalon_woland/c051_exact_lp_solver_with_duals/judge_packet/exact_checker.py` L1–195 (fa9cf3af7929), `pilots/anomalon_woland/c051_exact_lp_solver_with_duals/commit_reveal_c051.py` L1–373 (1917f223185f). Full source ledger and canonical comparisons are in the JSON report.

## c052_maxflow_mincut_certificates

Flow feasibility plus equal-capacity cut witness; arithmetic verification independent of how the candidate flow was found.

**Mathematics:** Integral flow bounds and conservation, source/sink divergence, an s-t cut and equality between flow value and cut capacity; explicit saturated forward and zero reverse cut edges.

This is a genuine WF11 certificate backend, not a distinct workflow because the problem is a graph. Both checkers accept the synthetic malformed input capacity 1.9 by converting it to integer 1; agreement therefore does not establish integer-domain ingress adequacy. The participant runner is a reference solver demonstration, while run_c052_matrix is a separate real provider-capable adapter that was not invoked.

**Execution:** Offline reference harness plus live-capable matrix wrapper. Fresh work executed only the two checker functions on invented public inputs; no matrix or stored case bank was run.

**Canonical difference:** Arithmetic owner copies are exact matches. Integration differences are imports, root sentinels and output paths, with no additional max-flow verification rule. The matrix remains a shared synthesis_matrix adapter over ten inline public cases.

**Recommendation:** Consolidate under WF11; retain max-flow/min-cut as a backend and add strict integer input controls in a separately reviewed repair. Keep the reproduced 1.9 counterexample with both checker outcomes. Do not infer adequate independent checking from two agreeing parsers.

**QM prerequisite:** A QM use requires a justified finite network encoding and proof that the desired QM claim follows from the certified flow/cut property; generic QM derivations require another checker.

**Review ceiling:** No dedicated tracked unit-test file exists in this root; mutation files were inventoried but not read or executed. Fresh acceptance/rejection probes cover one two-node network and the nonintegral-capacity counterexample, not the full capacity/topology space.

Evidence: `pilots/anomalon_woland/c052_maxflow_mincut_certificates/docs/c052_maxflow_mincut_certificates.md` L1–128 (c8acd6c94276), `pilots/anomalon_woland/c052_maxflow_mincut_certificates/participant_packet/TASK.md` L1–57 (e53dfef85196), `pilots/anomalon_woland/c052_maxflow_mincut_certificates/judge_packet/independent_checker.py` L1–159 (2a3bbb0ba20d), `pilots/anomalon_woland/c052_maxflow_mincut_certificates/participant_packet/runner.py` L1–71 (ac8c6aa06de1), `pilots/anomalon_woland/c052_maxflow_mincut_certificates/judge_packet/exact_checker.py` L1–176 (67e21ef21bc8), `pilots/anomalon_woland/c052_maxflow_mincut_certificates/run_c052_matrix.py` L1–191 (684e74fec95e), `pilots/anomalon_woland/c052_maxflow_mincut_certificates/commit_reveal_c052.py` L1–373 (a9739b97339d). Full source ledger and canonical comparisons are in the JSON report.

## c053_bareiss_fraction_free_matrix_inversion

Exact matrix inverse/adjugate validation with independent determinant pinning and a nonzero null-vector certificate for singularity.

**Mathematics:** Bareiss fraction-free determinant computation, A adj(A)=adj(A) A=dI, A inverse=I and inverse=adj/d; singularity witness Av=0 with v nonzero. The determinant must be checked separately because scaled d and adjugate satisfy the displayed product identities.

Existing WF11 already owns these checks. The actual code and regression test reject A=I with d=5 and adj=5I; the primary design prose that the product equations establish the determinant is too broad. Canonical answer parsing is shared by both judges and by C054, so only the arithmetic checks are separately implemented.

**Execution:** Offline reference demonstration/self-check and a separate live-capable matrix wrapper. Both judges were freshly probed for a valid identity inverse and the scaled determinant counterexample.

**Canonical difference:** Both mathematical checkers and canonical-rational parser match canonical owners. Imported participant/test/generator imports and root discovery differ. No new Bareiss mechanism is added by the import.

**Recommendation:** Consolidate with WF11, retaining the determinant-pin regression and the explicit distinction between parser sharing and independent arithmetic. Preserve stale protocol claims as historical text with review annotation rather than treating them as the current contract.

**QM prerequisite:** A QM transfer needs an explicit rational or algebraic-number matrix encoding and a checker for the intended QM identities; rational inversion does not handle arbitrary complex amplitudes or analytic claims.

**Review ceiling:** Full primary docs, both judges, parser and regression source read; stored cases/mutations and reference algorithm completeness not re-executed.

Evidence: `pilots/anomalon_woland/c053_bareiss_fraction_free_matrix_inversion/docs/c053_bareiss_fraction_free_matrix_inversion.md` L1–66 (b6c1e8b37d95), `pilots/anomalon_woland/c053_bareiss_fraction_free_matrix_inversion/participant_packet/TASK.md` L1–54 (6baabaf7a8a8), `pilots/anomalon_woland/c053_bareiss_fraction_free_matrix_inversion/judge_packet/independent_checker.py` L1–163 (a6ac5218e341), `pilots/anomalon_woland/c053_bareiss_fraction_free_matrix_inversion/participant_packet/runner.py` L1–71 (70c7c264ec90), `pilots/anomalon_woland/c053_bareiss_fraction_free_matrix_inversion/judge_packet/exact_checker.py` L1–240 (f5a3c69555aa), `pilots/anomalon_woland/c053_bareiss_fraction_free_matrix_inversion/judge_packet/canonical_rational.py` L1–54 (8d86d131e6c5), `pilots/anomalon_woland/c053_bareiss_fraction_free_matrix_inversion/tests/test_c053_canonical_rationals_and_det_pin.py` L1–195 (729f8733ab41), `pilots/anomalon_woland/c053_bareiss_fraction_free_matrix_inversion/run_c053_matrix.py` L1–155 (f2c05b5e119c). Full source ledger and canonical comparisons are in the JSON report.

## c054_exact_linear_systems

A solution plus independent rank/nullspace witnesses, or an exact left-null inconsistency witness.

**Mathematics:** Ax=b; a nonzero r-by-r minor gives rank(A)>=r; n-r independent nullspace vectors give rank(A)<=r. Inconsistency uses y^T A=0 and y^T b!=0. Exact indexed minors and rational parsing bind the witnesses.

This is the existing WF11 linear-system backend. The exact checker accepts UNKNOWN with a fully valid CONSISTENT witness, but the secondary checker requires SOLVED; the actual paired harness rejects that status. The earlier numbered report examined the first checker only. Fresh paired probes narrow the issue to single-checker use rather than claiming paired false acceptance.

**Execution:** Offline participant/reference paths and live-capable shared matrix adapter. Three fresh paired probes covered valid, invalid typed-index, and UNKNOWN-with-valid-witness behavior.

**Canonical difference:** Checker equations and shared parser match canonical copies. Changes are imports/sentinels and mutation-payload aliases in the common self-check harness; no new rank-nullity proof mechanism.

**Recommendation:** Consolidate under WF11 and require the paired gate until the first-checker status contract is repaired and tested. Retain typed-index, empty-system and canonical-rational controls. Preserve the observed first/second distinction in migration notes.

**QM prerequisite:** Use only after a justified finite exact-field encoding of the QM linear constraints; introduce a new algebraic/complex checker where rational encoding is insufficient. Rank/nullity alone does not prove an arbitrary QM derivation.

**Review ceiling:** Both judges fully read; meaningful tests fully read but full test module was not imported because collection reads stored case banks.

Evidence: `pilots/anomalon_woland/c054_exact_linear_systems/docs/c054_bareiss_nullspace_solver.md` L1–127 (22e4ae82ad72), `pilots/anomalon_woland/c054_exact_linear_systems/participant_packet/TASK.md` L1–60 (6a8f4dec0fbe), `pilots/anomalon_woland/c054_exact_linear_systems/judge_packet/independent_checker.py` L1–241 (5f2401041853), `pilots/anomalon_woland/c054_exact_linear_systems/tests/test_c054_typed_rejections.py` L1–157 (b2911034f5a1), `pilots/anomalon_woland/c054_exact_linear_systems/participant_packet/runner.py` L1–62 (f4cd740a48ba), `pilots/anomalon_woland/c054_exact_linear_systems/judge_packet/exact_checker.py` L1–247 (0b362b472791), `pilots/anomalon_woland/c054_exact_linear_systems/judge_packet/canonical_rational.py` L1–54 (8d86d131e6c5), `pilots/anomalon_woland/c054_exact_linear_systems/run_c054_matrix.py` L1–180 (dbdbbc79af96). Full source ledger and canonical comparisons are in the JSON report.

## c055_assignment_with_potentials

Assignment permutation with dual potentials, or a finite Hall-deficiency obstruction.

**Mathematics:** For minimization, u_i+v_j<=c_ij on allowed edges with matching primal value=sum(u)+sum(v); sign-adjusted maximization. A nonempty row subset S with |N(S)|<|S| proves no perfect assignment.

Same WF11 certificate method with a combinatorial backend. Typed permutation and optimization-sense tests close prior bugs. UNKNOWN plus a valid optimal certificate is accepted by the first checker but rejected by the secondary checker and paired gate. This status defect does not invalidate the mathematical duality calculation.

**Execution:** Offline participant/reference routes; live-capable matrix wrapper was read but not run. Paired synthetic valid, Boolean-permutation and UNKNOWN probes completed.

**Canonical difference:** Exact/secondary checkers match canonical arithmetic; imported path/discovery differences remain. Participant code is a reference Hungarian-solver demonstration, not synthesized-solver measurement.

**Recommendation:** Consolidate under WF11, preserving Hall and dual certificates and strict type tests. Repair the first checker status contract only in a separate authorized change; do not retire the secondary checker based on agreement on ordinary inputs.

**QM prerequisite:** A QM use needs a demonstrated assignment reduction and an appropriate finite carrier; this checker certifies the optimization problem only.

**Review ceiling:** Both judges and full typed-certificate test source read; historical judge banks and solver generation not executed.

Evidence: `pilots/anomalon_woland/c055_assignment_with_potentials/docs/c055_assignment_with_potentials.md` L1–71 (cf54ad195487), `pilots/anomalon_woland/c055_assignment_with_potentials/participant_packet/TASK.md` L1–56 (36905dc83e57), `pilots/anomalon_woland/c055_assignment_with_potentials/judge_packet/independent_checker.py` L1–159 (e24c702fe1cd), `pilots/anomalon_woland/c055_assignment_with_potentials/tests/test_c055_typed_certificates.py` L1–159 (64be8cbb2da7), `pilots/anomalon_woland/c055_assignment_with_potentials/participant_packet/runner.py` L1–62 (e0a44a005c95), `pilots/anomalon_woland/c055_assignment_with_potentials/judge_packet/exact_checker.py` L1–199 (9a39fafb5b7a), `pilots/anomalon_woland/c055_assignment_with_potentials/run_c055_matrix.py` L1–168 (c6cb583ec9ca), `pilots/anomalon_woland/c055_assignment_with_potentials/commit_reveal_c055.py` L1–373 (dceb780d7cbe). Full source ledger and canonical comparisons are in the JSON report.

## c059_sql_null_total_query_synthesis

Relational-expression verification against two separately owned expected-result evaluators, with bag multiplicity, complete headings and read-only candidate execution.

**Mathematics:** Finite bag algebra and three-valued predicates over declared tables; SQLite relation views versus a Python relational interpreter, comparing heading-aware Counters including NULL. Query correctness is bounded to the supplied finite test databases.

Substantive existing WF11 backend. The first judge builds its expected relation in a separate SQLite connection from the candidate; the second uses a Python interpreter. Both still execute candidate SQL through SQLite, so the planned DuckDB/Rust diversity is absent. Empty database suites, wrong headings on empty results and write queries are rejected in fresh controls. A TEXT COALESCE predicate gives SQLite false and Python bool(nonempty_text)=true, causing fresh judge disagreement. The null ledger uses lexical construct checks and can be empty; it is not a completeness proof. Preflight focuses on the first applicable protected table. The separate cross-family skeleton document is explicitly planned and shares the C059 label despite a different proposed task.

**Execution:** Offline reference/self-check routes and a live-capable shared matrix wrapper. Five public synthetic judge probes completed; no stored databases, hidden suites, provider route or private storage were read/run.

**Canonical difference:** Canonical task and WF11 copies contain the same verification logic. Differences include imported obsolete project namespace and parents[6] in participant runner, generator location in the matrix import, canonical task subprocess cwd fixes, and one sqlite_temp_master comment correction. These are integration/documentation differences, not a new relational verifier.

**Recommendation:** Consolidate the SQL backend and ownership tests in WF11. Preserve the TEXT COALESCE counterexample and restrict or reconcile the admitted predicate semantics before acceptance use. Keep the transfer-skeleton document as an unexecuted WF11/WF19 design variant; do not count it as implemented transfer.

**QM prerequisite:** Needs a task-specific QM-to-finite-relations encoding and independently adequate QM predicates, if such a reduction is intended. A finite SQL bag comparison cannot certify the unchanged QM problem.

**Review ceiling:** Full primary SQL and transfer-design documents, both judges, relational contract, SQL/Python oracle owners and read boundary read. Selected additional ownership tests read; generators/reference compiler and all archived data were not fully audited. Read-only SQLite authorization does not provide CPU/memory/query timeout limits; finite example equivalence is not universal query equivalence.

Evidence: `pilots/anomalon_woland/c059_sql_null_total_query_synthesis/docs/c059_sql_null_total_query_synthesis.md` L1–135 (09335ad72315), `pilots/anomalon_woland/c059_sql_null_total_query_synthesis/participant_packet/TASK.md` L1–64 (7672a889b79b), `pilots/anomalon_woland/c059_sql_null_total_query_synthesis/sqlite_read_boundary.py` L1–32 (d6967b32f171), `pilots/anomalon_woland/c059_sql_null_total_query_synthesis/judge_packet/exact_checker.py` L1–168 (c5a2ca3e86e5), `pilots/anomalon_woland/c059_sql_null_total_query_synthesis/judge_packet/independent_checker.py` L1–158 (38dfd64e83f3), `pilots/anomalon_woland/c059_sql_null_total_query_synthesis/relational_contract.py` L1–319 (5b85c5fe579e), `pilots/anomalon_woland/c059_sql_null_total_query_synthesis/judge_packet/sqlite_relational_oracle.py` L1–218 (afe339d90104), `pilots/anomalon_woland/c059_sql_null_total_query_synthesis/judge_packet/relational_interpreter.py` L1–397 (769b84fd82be). Full source ledger and canonical comparisons are in the JSON report.

## challenge_suite

Source-bound challenge orchestration, bounded failure-derived feedback, disjoint development/held-out transfer gating and historical source replay.

**Mathematics:** Composition of typed proposal checking with original task predicates; source/request hashes and paired arm comparisons; exact anchored cochain residual checks in the small repair adapter. No generic new solver theorem.

Existing WF19/WF12 orchestration contains real provider-capable campaign and local-HF generation paths, unlike the spec-only numbered wrappers. No such path was run. Catalog building can write generated pilot material and read case banks; it was not invoked. The CLI-generated tests mostly check custody/shape or explicitly skip planned conditions, whereas test_challenge_learning contains actual malformed-envelope, checker-disagreement and answer-redaction controls. Typed cochain repair validates every edge equation under the original budget binding. Public local mechanism trials cover eight small cases, not the full hidden scientific protocols. protocol_collation keeps target-conditioned C008 observations quarantined and retains historical external-capture claims as such.

**Execution:** Source review only for campaign/live/HF/overlay routes. They can dispatch real models or mutate disposable output/checkouts when explicitly invoked. No model, local-HF inference, detached overlay or case-bank load occurred.

**Canonical difference:** Canonical WF19 shares the same mechanisms. Changes include obsolete monorepo imports/resources/CLI names, two additional historical relocation-prefix rules in catalog.py, and historical documentation/result labels. The original same-file split logic and fixed feedback repertoire remain; there is no newly learned general mathematical operator.

**Recommendation:** Consolidate the orchestration in WF19 and mechanism controls in WF12. Retain candidate-only transfer and same-budget repair boundaries. Preserve the added historical locator rules as explicit migration adapters if still needed; avoid generating another numbered-pilot catalog. Frozen replay requires an intentionally disposable checkout and must not be run as ordinary read-only inspection.

**QM prerequisite:** Register a QM task schema and independent checker before dispatch; restrict feedback to preregistered answer-free error classes. The target paper and hidden answer must never supply training guidance or expected outputs.

**Review ceiling:** All substantive imported challenge-suite modules fully read; canonical live_run transfer core and selected meaningful gate tests read. Full provider accounting and all original domain checkers are outside this row. Claimed local trial counts and external raw captures in collation code were not reauthenticated.

Evidence: `pilots/anomalon_woland/challenge_suite/campaign.py` L1–304 (0dc71517804b), `pilots/anomalon_woland/challenge_suite/typed_certificate_repair.py` L1–138 (683c8a778e80), `pilots/anomalon_woland/challenge_suite/local_mechanism_trials.py` L1–242 (b91448579ccd), `pilots/anomalon_woland/challenge_suite/typed_certificate_repair.py` L34–98 (683c8a778e80), `pilots/anomalon_woland/challenge_suite/catalog.py` L1–308 (49fe08fd7df9), `pilots/anomalon_woland/challenge_suite/__main__.py` L1–306 (bd29c1955e5f), `pilots/anomalon_woland/challenge_suite/c001.py` L1–130 (205676f3b783), `pilots/anomalon_woland/challenge_suite/mechanism_panels.py` L1–229 (539a65dfd8a9). Full source ledger and canonical comparisons are in the JSON report.

## judge_packet_audit

Offline audit of checker dependence, trivial and type-confused responders, bounded execution outcomes, byte custody and answer-leakage heuristics.

**Mathematics:** Finite adversarial testing and syntactic dependency closure, exact hash recomputation with separately reported LF/CRLF forms, and normalized categorical outcomes. These are evidence diagnostics, not a proof that participant bytes contain no derivable answer.

The existing WF23 owner is a substantive reusable harness. It distinguishes exceptions/timeouts/missing outcomes from rejection, restarts after failed items and inspects reference/type-confusion responses. Leakage detection is token/field/normalized-example/AST lint with one-level assignment dataflow; clean lint cannot prove non-leakage. NO_IMPORT_DEPENDENCE is not proof of conceptual checker independence. commitment_timing distinguishes added together from separately, without proving the latter was earlier. Worker network prevention monkeypatches Python sockets; it is not an OS sandbox and does not strip all inherited credentials. normalize prefers an ACCEPT verdict over accepted:false; a synthetic counterexample reproduced that precedence. The top-level audit avoids a zero-checker run, though worker all_accept by itself is vacuous for an empty list.

**Execution:** No audit CLI was run, because it recursively loads judge/answer/mutation banks and writes artifacts. Three fresh pure probes exercised normalization and ID leakage only.

**Canonical difference:** Canonical WF23 differs principally in imported module paths, challenge-tree locator and CORE_INTELLIGENCE_ROOT versus OMEGA_INTELLIGENCE_ROOT. Normalization, custody and leakage algorithms match; domain-specific responders remain bounded plugins rather than new workflow families.

**Recommendation:** Consolidate with WF23 and keep type-confusion/responders and raw outcome records. Require checker-specific strict normalization before treating aggregate ACCEPT as authoritative. Rename or qualify timing/independence/leakage conclusions to the actually measured property in a separately reviewed change. Retain historical audited artifacts without turning them into fresh sealed cases.

**QM prerequisite:** The audit can inspect any future QM checker, but requires a QM-specific negative/positive/witness mutation panel and a separate adequacy argument. Source hash custody and lexical leakage lint do not establish a QM theorem.

**Review ceiling:** Full worker, main audit, custody, execution and leakage sources read; descriptor/discovery and dependency-comparison core ranges read. Auxiliary special-case/reference-value/semantic responder catalogs and summary aggregation were inventoried and diff-compared, not fully semantically audited. No actual Git chronology, receipt commitment or historical audited case bank was replayed.

Evidence: `pilots/anomalon_woland/judge_packet_audit/worker.py` L1–512 (f5b9221e53d1), `pilots/anomalon_woland/judge_packet_audit/audit.py` L1–429 (7c1e4fe5265a), `pilots/anomalon_woland/judge_packet_audit/audit.py` L432–748 (7c1e4fe5265a), `pilots/anomalon_woland/judge_packet_audit/custody.py` L1–274 (88bc553141e4), `pilots/anomalon_woland/judge_packet_audit/execution.py` L1–131 (038139558729), `pilots/anomalon_woland/judge_packet_audit/leakage.py` L1–332 (33415afe6ea4), `pilots/anomalon_woland/judge_packet_audit/static_analysis.py` L188–295 (8482caf8b4be), `pilots/anomalon_woland/judge_packet_audit/layout.py` L1–262 (fc30e156927e). Full source ledger and canonical comparisons are in the JSON report.

## certified_ladder

Registered cost/accuracy experimental design and typed hypothesis reporting over supplied observations; the imported evaluator is a wrapper around canonical domain functions.

**Mathematics:** Paired per-item comparisons, censoring at registered caps and declared exact certificate gates; evaluator code implements numerical threshold rules. H0 compares control statuses, H1 uses gains/cost ratios and sample size, H2 only rejects perfectly flat or strictly declining curves.

Existing WF22 already owns this design and evaluator. The wrapper self-test uses chosen favorable metrics; it is not experiment data. H0 accepts [{}] as RETAINED, and canonical H2 retains the nonmonotone curve .9,.1,.2 in isolated AST probes. H1/H5 threshold routines do not implement the sign-test significance demanded in the design. P0 calls the same gate twice on a fixed integer-3 expected value; repeated passes are reproducibility, not independent checker implementations. Historical October 15 reports describe an ambiguous stopped send; October 16 reports claim 44 settled replies and one retained reserve. Those prose reports were read as historical claims, not revalidated from the unread ledger/raw/archive data.

**Execution:** No campaign, ledger, archives or self-test CLI executed. Two exact AST-extracted pure checks reproduced the H0 and H2 weaknesses without constructor/import-driven storage. Historical execution numbers remain report claims.

**Canonical difference:** Runtime evaluator delegates only differ by pfp versus omega_engine_pfp imports. Design/report differences also include Run O versus Opus naming, native-host environment variable, custody archive locators and Adversary/Woland labels. The report at woland_20261015 matches the canonical adversary_20261015 report by full content diff, not suffix lookup. Original registration bytes must remain distinct.

**Recommendation:** Consolidate the design/evaluator with WF22 while preserving every historical report and archive identity. Treat H0/H1/H2/H5 evaluator outputs as provisional diagnostics until control completeness and the declared statistical tests are implemented. Never use synthetic self-test RETAINED results to support model benefit.

**QM prerequisite:** Needs preregistered QM items, an adequate QM checker, disjoint development/held-out encoding, fixed control obligations and analysis consistent with the claim. No existing ladder expected answer may be reused as the new sealed benchmark.

**Review ceiling:** Both design documents, hypotheses, wrapper and all three historical report texts fully read; canonical H0-H5 and P0 execution core plus full evaluator tests read. H6-H13 bodies, management_ladder campaign engine and historical raw/storage artifacts were not fully reviewed.

Evidence: `pilots/anomalon_woland/certified_ladder/design.md` L1–185 (0dac3b627aea), `pilots/anomalon_woland/certified_ladder/design_v2.md` L1–88 (f307f6810f0b), `pilots/anomalon_woland/certified_ladder/hypotheses.yaml` L1–73 (0482fb5f2831), `pilots/anomalon_woland/certified_ladder/hypothesis_evaluator.py` L1–298 (da752b00bb9f), `pilots/anomalon_woland/certified_ladder/hypotheses.yaml` L1–16 (0482fb5f2831), `pilots/anomalon_woland/certified_ladder/v2/campaign_20261015/REPORT.md` L1–112 (842d0c3ba248), `pilots/anomalon_woland/certified_ladder/v2/campaign_20261016/REPORT.md` L1–137 (d819a3563c4f), `pilots/anomalon_woland/certified_ladder/v2/woland_20261015/REPORT.md` L1–87 (3394e9ec267d). Full source ledger and canonical comparisons are in the JSON report.

## replay_runners

Read-only historical dossier replay with source/request/response binding, exact finite witness checking, reversible representations and explicit live retirement; separate old mode-capsule builders remain artifact generators.

**Mathematics:** Exact rational equations, graph cycle rank and minimum forest repair, exhaustive finite F2 spin optimum, weighted L1 primal/dual equality, chain-law/rank/Betti checks with an explicit missing-cup-product refusal. Representation legends are reversible JSON token encodings; seals certify identity, not correctness.

These mechanisms already exist under WF18/WF8. Dossier live() always refuses; replay recomputes current grades only if pinned source/environment/input/request/raw hashes agree. Stored output is not a fresh generation. Alternative valid certificates are accepted by the finite predicates. The mode execute.py still writes capsule seeds/specs/results and its selected predicates were already assessed in numbered_000_050; it must not be mistaken for a read-only evaluator. publish.py emits historical prose/learning artifacts and requires stored campaign data; it was not run. Dossier tests include independent SymPy/NetworkX controls and tamper mutations, but module collection would load retired plans/cases, so only source was read.

**Execution:** No historical replay, plan extraction, publication or live call performed. All 25 old mode builders had prior hash-bound code reads, reused here; new dossier checker/run/test/prepare/source/publish owners were read. No archived replies/inputs were loaded.

**Canonical difference:** Not a byte-interchangeable copy: imported run.py adds PREVIOUS_CHECKER_SOURCE, PREVIOUS_ACTIVE_DEPENDENCIES and a legacy_archive_set to exact allowed source-key sets. It maps old checker keys to current bytes but still checks the recorded digest. It also falls back to PILOTS when a relocated omega_engine_pfp capsule directory is absent, unlike the canonical unconditional relocated owner. Other changes are package/host/history locators, mode_11 directory label and CLI names. prepare.py pins the same historical commit with a different Git path prefix.

**Recommendation:** Consolidate kernels and replay under WF18/WF8 only after preserving or deliberately reconciling the extra source-key sets and absent-directory fallback. Preserve archived source snapshots and checker-drift refusals. Keep artifact-writing mode/publish routes separate from the replay API; no automatic historical-source normalization or regenerated answers.

**QM prerequisite:** Reuse custody and reversible encoding only after defining the QM carrier and independent predicate. The supplied finite rational/F2/graph/chain checks support only their explicit contracts; missing multiplication/continuum/physical premises remain open.

**Review ceiling:** Auxiliary import/init lines and full mode packet preamble are comparison-only where the prior ledger records selected ranges; the report does not claim every line was independently reread. Exact-type schemas protect answer ingress for the fixed generated domains, but general malformed task handling and complexity bounds were not certified.

Evidence: `pilots/anomalon_woland/replay_runners/dossier_capsules/checking.py` L1–169 (2735adc008e7), `pilots/anomalon_woland/replay_runners/dossier_capsules/run.py` L1–264 (2ba793d67881), `pilots/anomalon_woland/replay_runners/mode_capsules/execute.py` L1–296 (42496edbd262), `pilots/anomalon_woland/replay_runners/mode_capsules/kernels.py` L1–101 (31a621b4e486), `pilots/anomalon_woland/replay_runners/dossier_capsules/test_campaign.py` L1–367 (4675450eb5d7), `pilots/anomalon_woland/replay_runners/dossier_capsules/prepare.py` L1–59 (f646b55228dd), `pilots/anomalon_woland/replay_runners/dossier_capsules/learn.py` L1–74 (60aabdb98921), `pilots/anomalon_woland/replay_runners/dossier_capsules/cases.py` L1–144 (0575e430b8b1). Full source ledger and canonical comparisons are in the JSON report.

## cot_miner.py

Deterministic heuristics extracting evidence-linked, unadmitted candidate guidance from retained reasoning traces.

**Mathematics:** Regex/threshold classification and set/count aggregation, with exact test/source references; no mathematical theorem or causal learning estimator.

The existing pilot-estate library contains the same miner. It detects lexical corpus speculation, schema anxiety, substitution, license conflict and token thresholds; fixed rule texts remain admitted:false. These are candidate detectors and human-review leads, not certified mental-state attribution, causal efficacy, automatic immune admission or new mathematical reasoning machinery. Its exact-answer helper checks the top-level type and excludes floats, but nested Python Boolean/numeric equality can still coincide. Metadata source_file is joined to the pilot directory without a containment guard.

**Execution:** No trace corpus or source_file target opened and no mine() call made. Full miner and meaningful test source read; tests using real historical traces were not executed.

**Canonical difference:** Same classification/mining code; only pfp/omega_engine_pfp resource names, pilot root locator and CLI module path differ. Prior 000-050 source context establishes why trace patterns cannot become efficacy claims.

**Recommendation:** Keep one library miner feeding candidate-only WF3/WF14/WF19 review. Retain source hashes, quotations and false-positive controls; add held-out self-tolerance and adequacy evaluation before admission. Do not use target-paper text or hidden expected answers as mining input.

**QM prerequisite:** A QM deployment needs public development traces, declared error classes and independent QM checks. The miner does not supply a QM checker or prove transfer.

**Review ceiling:** Only classifier source/test semantics and canonical differences were reviewed; stored reasoning, historical answer matches and generated learning files were not assessed.

Evidence: `pilots/anomalon_woland/cot_miner.py` L1–403 (91fd831f64a7). Full source ledger and canonical comparisons are in the JSON report.

## pilot_reply_kit.py

Bounded caller-supplied reply parsing, request matching and domain-pluggable decoding/grading with explicit unauthenticated evidence labels.

**Mathematics:** Finite request-ID matching, SHA-256 of source JSON, strict Pydantic ingress and explicit allowed status sets; all mathematical acceptance belongs to the supplied decoder/grade callback.

Byte-identical to the existing pilot-estate library. It rejects duplicate JSON keys and foreign/duplicate request IDs, caps input/replies and keeps missing replies NOT_RUN. Request.sha binds source only, not instruction; two different instructions have the same source hash. parse accepts NaN unless the domain decoder refuses it. assess uses XML outcomes, coverage and tests named mutant_* as qualification signals, not a general mutation adequacy proof. It never authenticates a provider reply.

**Execution:** Four fresh pure probes covered duplicate keys, NaN acceptance, unchanged source hash across changed instruction, and missing reply behavior. No subprocess coverage/export/pytest route or caller reply files executed.

**Canonical difference:** Exact byte match to workflows/library/pilot_estate/pilot_reply_kit.py; no code delta. Domain-specific callback behavior is outside this file and must not be inferred from byte identity.

**Recommendation:** Consolidate in the existing shared library. Preserve unauthenticated evidence and NOT_RUN labels; require a full instruction/schema/checker binding for future custody and strict finite numeric ingress where mathematically required. Keep adapter tests distinct from checker qualification.

**QM prerequisite:** Needs a QM answer schema, exact decoder and independently adequate grade callback. The source hash and passing wrapper tests cannot grade QM.

**Review ceiling:** Full owner read. No standalone tracked kit test was found in the targeted test search; fresh probes are a narrow replacement for behavior inspection, not a complete suite.

Evidence: `pilots/anomalon_woland/pilot_reply_kit.py` L1–274 (838b5022e8dd). Full source ledger and canonical comparisons are in the JSON report.

## sqlite_pilot_store.py

Simple run-record storage and callback-based offline regrading.

**Mathematics:** Relational persistence of JSON fields and conjunction of checker results; no cryptographic source binding, immutable ledger or independent proof rule.

Same existing library helper. INSERT OR REPLACE allows a run_id record to be overwritten. An empty checker list returns all_passed=True; a truthy nonboolean checker result also passes. Both behaviors were reproduced on a mocked record with no database opened. The zero-network docstring is a convention: callback execution itself has no network blockade. Stored outcomes and cost floats are not authenticated provider receipts.

**Execution:** Full source read; two fresh method probes used __new__ plus a mocked in-memory record. No SQLite file, private storage, existing record or provider was accessed.

**Canonical difference:** Only Adversary/Woland prose and harness-value comments differ; persistence/replay logic is identical. The filename is a library owner, not a new pilot family.

**Recommendation:** Consolidate the CRUD/regrade helper into the existing library, retaining it only where mutable storage is intended. Use a separate immutable, checker-version-bound custody layer for evidence. Require nonempty exact-Boolean checkers before using replay all_passed as an acceptance decision.

**QM prerequisite:** Needs a separately registered QM checker and immutable provenance binding; this storage adapter cannot establish QM truth or sealed benchmark custody.

**Review ceiling:** Storage transaction/restart/power-loss properties were not tested; no append-only or authentication guarantee is present in this owner.

Evidence: `pilots/anomalon_woland/sqlite_pilot_store.py` L1–187 (fc3b85257175). Full source ledger and canonical comparisons are in the JSON report.

## offline_evaluator.py

Historical raw-observation regrading separated from explicit oracle-fixture creation, with efficacy eligibility forced false.

**Mathematics:** Dispatch to a versioned finite task checker with the frozen legacy seed-owned expected object; immutable observation and new evaluation-receipt separation. The local 2x2 Cramer helper is a narrow deterministic example.

Existing library owner with only import/resource differences. It reads seed.expected_outcome.answer as the old oracle, re-parses saved raw replies through the live_evaluator/checker registry and emits new evaluation records; it does not regenerate observations or establish fresh model performance. The separate --create-fixtures path materializes explicit oracle fixtures. Negative-fixture summaries test supplied cases only and an empty fixture collection has vacuous all-passed counters.

**Execution:** No evaluator CLI, seed, response, fixture or receipt directory opened. Full source and current registry plus prior hash-bound fail-closed gate ranges were reviewed; historical counts were not rerun.

**Canonical difference:** Code is unchanged apart from legacy package/resource locators and sibling evaluator import. Prior hash-bound completed reads were rechecked and the full owner reread for this report.

**Recommendation:** Consolidate the historical regrader with the existing library and preserve the separate fixture path and efficacy_eligible:false ceiling. Require nonempty fixture panels and an adequate new task checker for new work. Never promote old expected values into the new hidden benchmark.

**QM prerequisite:** Requires a fresh QM encoding/checker owned outside old expected-answer files. The unchanged QM seed was not read; no transfer claim is supported.

**Review ceiling:** Canonical domain gate ranges were reviewed in the prior numbered report and hash-bound for reuse; end-to-end legacy import availability and all stored observations are not certified.

Evidence: `pilots/anomalon_woland/offline_evaluator.py` L1–294 (c0e8f7b618d3). Full source ledger and canonical comparisons are in the JSON report.

## live_evaluator.py

Legacy live-dispatch retirement boundary plus strict historical observation binding and offline raw regrading.

**Mathematics:** Request/response digest identity, strict JSON parsing and checker-registry delegation; no new mathematical checker. Every fresh legacy dispatch raises a typed migration refusal.

Despite its filename this owner refuses new live sends before transport and marks regraded results efficacy_eligible:false. It binds persisted request and provider-response content hashes but that does not independently authenticate provider origin. sanitize_raw_reply strips optional Markdown fences for this historical route; it must not be conflated with the stricter current protocol ingress. Public prompt leak checking is a shallow regex for selected answer-bearing keys, not a non-leakage proof.

**Execution:** No live call, legacy run directory or seed read. Full owner and legacy-preflight test source read. Tests that copy seed artifacts were deliberately not run.

**Canonical difference:** Only pfp versus omega_engine_pfp imports differ from the canonical library copy. Retired dispatch semantics are the same; no new live model capability is imported.

**Recommendation:** Keep one explicit retired-route compatibility adapter and use canonical bounded dispatch for new tasks. Preserve raw bytes and historical hash bindings; do not rewrite old observations to pass a changed checker.

**QM prerequisite:** A new QM task needs an appropriate schema, encoding and pinned checker on the canonical execution route; this retired wrapper supplies none.

**Review ceiling:** No authentication of historical provider origins or metering was performed; no current runtime import test was attempted for old namespace paths.

Evidence: `pilots/anomalon_woland/live_evaluator.py` L1–215 (a31319a1bd3d). Full source ledger and canonical comparisons are in the JSON report.

## Review boundaries

- No protected QM seed, private storage, credentials or bundled third-party dependency source was read. No model calls, local model inference, corpus edits, runtime overlay, publication or deletion occurred.
- Historical report numbers and model/pricing names are provenance claims, not current API facts or freshly authenticated experiment outcomes.
- Two checker acceptances, hash custody, source similarity, leakage lint, mutation counts and model efficacy are separate claims.
- No old expected answer, target paper or historical raw output was designated as a new workflow input or sealed benchmark.
- Current import/resource-path failures were not repaired; direct checker probes deliberately bypass package entrypoints and cannot establish full CLI portability.
- This first substantive pass covers all 15 owners but intentionally does not fully audit generated data, reference algorithms, every auxiliary audit plugin, full budget engines or historical stores.
