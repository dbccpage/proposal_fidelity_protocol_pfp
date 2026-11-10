"""Assemble review recommendations and exact source custody; never edits the import."""
from __future__ import annotations
import collections,difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).parent
inventory=json.loads((OUT/'shared_runtime_inventory.json').read_text())
reads=json.loads((OUT/'shared_runtime_reads.json').read_text())
probes=json.loads((OUT/'shared_runtime_probe_results.json').read_text())
families={n['id']:n for n in json.loads((ROOT/'dag/workflows_dag.json').read_text(encoding='utf-8'))['nodes'] if n.get('kind')=='existing_workflow_family'}
def evidence(path,lines=None,level='full_source_read_and_semantic_assessment'):
    p=ROOT/path;raw=p.read_bytes();size=len(raw.decode('utf-8').splitlines())
    return dict(path=path,sha256=hashlib.sha256(raw).hexdigest(),lines=lines or [1,size],review_level=level)
def mapping(ids,relationship):
    return [dict(family_id=i,path=families[i]['path'],relationship=relationship) for i in ids]

# Each additional self-check runner was compared in full against the fully read
# C051 owner. The only differences are identifiers/imports/checker function names
# and the explicit mutation-payload aliases; no individual full read is claimed.
base=next(s for s in inventory[0]['sources'] if '/commit_reveal_' in s['path'])
for row in inventory[1:6]:
    s=next(s for s in row['sources'] if '/commit_reveal_' in s['path'])
    reads.append(dict(path=s['path'],sha256=s['sha256'],lines=s['lines'],review_level='full_semantic_diff_review_against_fully_read_C051_runner',comparison_base=base['path']))

# The historical report changed its containing directory as well as labels.
item=next(s for s in inventory[8]['sources'] if '/woland_20261015/' in s['path'])
target='workflows/wf22_certified_cost_ladder/pilots/certified_ladder/v2/adversary_20261015/REPORT.md'
a=(ROOT/target).read_bytes();b=(ROOT/item['path']).read_bytes()
item['canonical_matches']=[m for m in item['canonical_matches'] if m['path']!=target]
item['canonical_matches'].append(dict(path=target,sha256=hashlib.sha256(a).hexdigest(),lines=[1,len(a.decode().splitlines())],byte_identical=a==b,namespace_only_difference=False,diff='\n'.join(difflib.unified_diff(a.decode().splitlines(),b.decode().splitlines(),fromfile=target,tofile=item['path'],n=1)),manual_locator_match=True))

def source_read_coverage(source, evidence_rows):
    records=[r for r in evidence_rows if r['path']==source['path']]
    body=[r for r in records if 'semantic_diff' not in r['review_level']]
    merged=[]
    for start,end in sorted(r['lines'] for r in body):
        if merged and start<=merged[-1][1]+1:merged[-1][1]=max(merged[-1][1],end)
        else:merged.append([start,end])
    full=merged==[source['lines']]
    return dict(path=source['path'],body_read_ranges=merged,full_body_read=full,
                review_kind='full_body_read' if full else 'selected_body_read' if body else 'full_diff_against_read_runner' if records else 'canonical_comparison_only',
                review_levels=sorted({r['review_level'] for r in records}))

definitions={
'c051_exact_lp_solver_with_duals':dict(
 contribution='Reusable exact LP certificate validation, with a separately implemented rational checker and a reference self-consistency harness.',
 mathematical_basis='For max c^T x with Ax<=b and x>=0: primal/dual feasibility and c^T x=b^T y certify optimality; a nonnegative Farkas vector certifies infeasibility; feasible base point plus improving recession ray certifies unboundedness. Canonical rational strings are checked separately from those equations.',
 reusable_mechanism_name='exact_primal_dual_certificate_and_typed_refusal',families=['WF11'],
 rationale='The two actual judges contain substantive mathematics already owned by WF11 and its certified-challenge task package. The four-line participant TASK is much thinner than the full design, which asks for a schema, frozen synthesis, independent native validation and matched model experiments. The participant runner executes a supplied Python solve function in-process; it is not the proposed sandbox. The commit_reveal runner labels reference self-consistency and explicitly computes hashes at reveal time, not before hidden-case access.',
 semantic_differences='Judge mathematics and reference implementations match existing owners; differences in runners/generators/tests concern monorepo import prefixes, root sentinels, output custody paths and Adversary/Woland names. These path changes can break execution even when the certificate equations are identical.',
 next_action='Consolidate the two exact LP judges and their negative controls into the current WF11 task owner. Retain one shared self-consistency harness with task configuration. Keep the original protocol and historical findings as provenance; do not label the self-check as a sealed model experiment.',
 prerequisite='A QM application needs an explicit proved reduction to this rational LP, typed input bounds and an independent adequacy check. A valid LP certificate alone does not establish the QM premises.',
 runtime='Reference/participant routes are offline. No C051 model-matrix source is in this assigned tracked root. Design and findings are historical/planned evidence, not fresh provider execution.',
 limitations=['Full both-judge and primary-protocol reads; generated case banks and reference-solver internals were not audited for completeness.','Secondary implementation is separate Python arithmetic, not evidence of separate author, separate trust domain or native parity.']),
'c052_maxflow_mincut_certificates':dict(
 contribution='Flow feasibility plus equal-capacity cut witness; arithmetic verification independent of how the candidate flow was found.',
 mathematical_basis='Integral flow bounds and conservation, source/sink divergence, an s-t cut and equality between flow value and cut capacity; explicit saturated forward and zero reverse cut edges.',
 reusable_mechanism_name='primal_flow_dual_cut_certificate',families=['WF11'],
 rationale='This is a genuine WF11 certificate backend, not a distinct workflow because the problem is a graph. Both checkers accept the synthetic malformed input capacity 1.9 by converting it to integer 1; agreement therefore does not establish integer-domain ingress adequacy. The participant runner is a reference solver demonstration, while run_c052_matrix is a separate real provider-capable adapter that was not invoked.',
 semantic_differences='Arithmetic owner copies are exact matches. Integration differences are imports, root sentinels and output paths, with no additional max-flow verification rule. The matrix remains a shared synthesis_matrix adapter over ten inline public cases.',
 next_action='Consolidate under WF11; retain max-flow/min-cut as a backend and add strict integer input controls in a separately reviewed repair. Keep the reproduced 1.9 counterexample with both checker outcomes. Do not infer adequate independent checking from two agreeing parsers.',
 prerequisite='A QM use requires a justified finite network encoding and proof that the desired QM claim follows from the certified flow/cut property; generic QM derivations require another checker.',
 runtime='Offline reference harness plus live-capable matrix wrapper. Fresh work executed only the two checker functions on invented public inputs; no matrix or stored case bank was run.',
 limitations=['No dedicated tracked unit-test file exists in this root; mutation files were inventoried but not read or executed.','Fresh acceptance/rejection probes cover one two-node network and the nonintegral-capacity counterexample, not the full capacity/topology space.']),
'c053_bareiss_fraction_free_matrix_inversion':dict(
 contribution='Exact matrix inverse/adjugate validation with independent determinant pinning and a nonzero null-vector certificate for singularity.',
 mathematical_basis='Bareiss fraction-free determinant computation, A adj(A)=adj(A) A=dI, A inverse=I and inverse=adj/d; singularity witness Av=0 with v nonzero. The determinant must be checked separately because scaled d and adjugate satisfy the displayed product identities.',
 reusable_mechanism_name='exact_matrix_certificate_with_independent_determinant_pin',families=['WF11'],
 rationale='Existing WF11 already owns these checks. The actual code and regression test reject A=I with d=5 and adj=5I; the primary design prose that the product equations establish the determinant is too broad. Canonical answer parsing is shared by both judges and by C054, so only the arithmetic checks are separately implemented.',
 semantic_differences='Both mathematical checkers and canonical-rational parser match canonical owners. Imported participant/test/generator imports and root discovery differ. No new Bareiss mechanism is added by the import.',
 next_action='Consolidate with WF11, retaining the determinant-pin regression and the explicit distinction between parser sharing and independent arithmetic. Preserve stale protocol claims as historical text with review annotation rather than treating them as the current contract.',
 prerequisite='A QM transfer needs an explicit rational or algebraic-number matrix encoding and a checker for the intended QM identities; rational inversion does not handle arbitrary complex amplitudes or analytic claims.',
 runtime='Offline reference demonstration/self-check and a separate live-capable matrix wrapper. Both judges were freshly probed for a valid identity inverse and the scaled determinant counterexample.',
 limitations=['Full primary docs, both judges, parser and regression source read; stored cases/mutations and reference algorithm completeness not re-executed.']),
'c054_exact_linear_systems':dict(
 contribution='A solution plus independent rank/nullspace witnesses, or an exact left-null inconsistency witness.',
 mathematical_basis='Ax=b; a nonzero r-by-r minor gives rank(A)>=r; n-r independent nullspace vectors give rank(A)<=r. Inconsistency uses y^T A=0 and y^T b!=0. Exact indexed minors and rational parsing bind the witnesses.',
 reusable_mechanism_name='solution_rank_nullity_or_left_null_certificate',families=['WF11'],
 rationale='This is the existing WF11 linear-system backend. The exact checker accepts UNKNOWN with a fully valid CONSISTENT witness, but the secondary checker requires SOLVED; the actual paired harness rejects that status. The earlier numbered report examined the first checker only. Fresh paired probes narrow the issue to single-checker use rather than claiming paired false acceptance.',
 semantic_differences='Checker equations and shared parser match canonical copies. Changes are imports/sentinels and mutation-payload aliases in the common self-check harness; no new rank-nullity proof mechanism.',
 next_action='Consolidate under WF11 and require the paired gate until the first-checker status contract is repaired and tested. Retain typed-index, empty-system and canonical-rational controls. Preserve the observed first/second distinction in migration notes.',
 prerequisite='Use only after a justified finite exact-field encoding of the QM linear constraints; introduce a new algebraic/complex checker where rational encoding is insufficient. Rank/nullity alone does not prove an arbitrary QM derivation.',
 runtime='Offline participant/reference paths and live-capable shared matrix adapter. Three fresh paired probes covered valid, invalid typed-index, and UNKNOWN-with-valid-witness behavior.',
 limitations=['Both judges fully read; meaningful tests fully read but full test module was not imported because collection reads stored case banks.']),
'c055_assignment_with_potentials':dict(
 contribution='Assignment permutation with dual potentials, or a finite Hall-deficiency obstruction.',
 mathematical_basis='For minimization, u_i+v_j<=c_ij on allowed edges with matching primal value=sum(u)+sum(v); sign-adjusted maximization. A nonempty row subset S with |N(S)|<|S| proves no perfect assignment.',
 reusable_mechanism_name='assignment_dual_potentials_or_Hall_obstruction',families=['WF11'],
 rationale='Same WF11 certificate method with a combinatorial backend. Typed permutation and optimization-sense tests close prior bugs. UNKNOWN plus a valid optimal certificate is accepted by the first checker but rejected by the secondary checker and paired gate. This status defect does not invalidate the mathematical duality calculation.',
 semantic_differences='Exact/secondary checkers match canonical arithmetic; imported path/discovery differences remain. Participant code is a reference Hungarian-solver demonstration, not synthesized-solver measurement.',
 next_action='Consolidate under WF11, preserving Hall and dual certificates and strict type tests. Repair the first checker status contract only in a separate authorized change; do not retire the secondary checker based on agreement on ordinary inputs.',
 prerequisite='A QM use needs a demonstrated assignment reduction and an appropriate finite carrier; this checker certifies the optimization problem only.',
 runtime='Offline participant/reference routes; live-capable matrix wrapper was read but not run. Paired synthetic valid, Boolean-permutation and UNKNOWN probes completed.',
 limitations=['Both judges and full typed-certificate test source read; historical judge banks and solver generation not executed.']),
'c059_sql_null_total_query_synthesis':dict(
 contribution='Relational-expression verification against two separately owned expected-result evaluators, with bag multiplicity, complete headings and read-only candidate execution.',
 mathematical_basis='Finite bag algebra and three-valued predicates over declared tables; SQLite relation views versus a Python relational interpreter, comparing heading-aware Counters including NULL. Query correctness is bounded to the supplied finite test databases.',
 reusable_mechanism_name='dual_relational_oracles_with_bag_and_NULL_boundary_checks',families=['WF11'],
 rationale='Substantive existing WF11 backend. The first judge builds its expected relation in a separate SQLite connection from the candidate; the second uses a Python interpreter. Both still execute candidate SQL through SQLite, so the planned DuckDB/Rust diversity is absent. Empty database suites, wrong headings on empty results and write queries are rejected in fresh controls. A TEXT COALESCE predicate gives SQLite false and Python bool(nonempty_text)=true, causing fresh judge disagreement. The null ledger uses lexical construct checks and can be empty; it is not a completeness proof. Preflight focuses on the first applicable protected table. The separate cross-family skeleton document is explicitly planned and shares the C059 label despite a different proposed task.',
 semantic_differences='Canonical task and WF11 copies contain the same verification logic. Differences include imported obsolete project namespace and parents[6] in participant runner, generator location in the matrix import, canonical task subprocess cwd fixes, and one sqlite_temp_master comment correction. These are integration/documentation differences, not a new relational verifier.',
 next_action='Consolidate the SQL backend and ownership tests in WF11. Preserve the TEXT COALESCE counterexample and restrict or reconcile the admitted predicate semantics before acceptance use. Keep the transfer-skeleton document as an unexecuted WF11/WF19 design variant; do not count it as implemented transfer.',
 prerequisite='Needs a task-specific QM-to-finite-relations encoding and independently adequate QM predicates, if such a reduction is intended. A finite SQL bag comparison cannot certify the unchanged QM problem.',
 runtime='Offline reference/self-check routes and a live-capable shared matrix wrapper. Five public synthetic judge probes completed; no stored databases, hidden suites, provider route or private storage were read/run.',
 limitations=['Full primary SQL and transfer-design documents, both judges, relational contract, SQL/Python oracle owners and read boundary read. Selected additional ownership tests read; generators/reference compiler and all archived data were not fully audited.','Read-only SQLite authorization does not provide CPU/memory/query timeout limits; finite example equivalence is not universal query equivalence.']),
'challenge_suite':dict(
 contribution='Source-bound challenge orchestration, bounded failure-derived feedback, disjoint development/held-out transfer gating and historical source replay.',
 mathematical_basis='Composition of typed proposal checking with original task predicates; source/request hashes and paired arm comparisons; exact anchored cochain residual checks in the small repair adapter. No generic new solver theorem.',
 reusable_mechanism_name='source_bound_two_stage_failure_rule_transfer',families=['WF19','WF12'],
 rationale='Existing WF19/WF12 orchestration contains real provider-capable campaign and local-HF generation paths, unlike the spec-only numbered wrappers. No such path was run. Catalog building can write generated pilot material and read case banks; it was not invoked. The CLI-generated tests mostly check custody/shape or explicitly skip planned conditions, whereas test_challenge_learning contains actual malformed-envelope, checker-disagreement and answer-redaction controls. Typed cochain repair validates every edge equation under the original budget binding. Public local mechanism trials cover eight small cases, not the full hidden scientific protocols. protocol_collation keeps target-conditioned C008 observations quarantined and retains historical external-capture claims as such.',
 semantic_differences='Canonical WF19 shares the same mechanisms. Changes include obsolete monorepo imports/resources/CLI names, two additional historical relocation-prefix rules in catalog.py, and historical documentation/result labels. The original same-file split logic and fixed feedback repertoire remain; there is no newly learned general mathematical operator.',
 next_action='Consolidate the orchestration in WF19 and mechanism controls in WF12. Retain candidate-only transfer and same-budget repair boundaries. Preserve the added historical locator rules as explicit migration adapters if still needed; avoid generating another numbered-pilot catalog. Frozen replay requires an intentionally disposable checkout and must not be run as ordinary read-only inspection.',
 prerequisite='Register a QM task schema and independent checker before dispatch; restrict feedback to preregistered answer-free error classes. The target paper and hidden answer must never supply training guidance or expected outputs.',
 runtime='Source review only for campaign/live/HF/overlay routes. They can dispatch real models or mutate disposable output/checkouts when explicitly invoked. No model, local-HF inference, detached overlay or case-bank load occurred.',
 limitations=['All substantive imported challenge-suite modules fully read; canonical live_run transfer core and selected meaningful gate tests read. Full provider accounting and all original domain checkers are outside this row.','Claimed local trial counts and external raw captures in collation code were not reauthenticated.']),
'judge_packet_audit':dict(
 contribution='Offline audit of checker dependence, trivial and type-confused responders, bounded execution outcomes, byte custody and answer-leakage heuristics.',
 mathematical_basis='Finite adversarial testing and syntactic dependency closure, exact hash recomputation with separately reported LF/CRLF forms, and normalized categorical outcomes. These are evidence diagnostics, not a proof that participant bytes contain no derivable answer.',
 reusable_mechanism_name='offline_checker_adequacy_and_custody_audit',families=['WF23'],
 rationale='The existing WF23 owner is a substantive reusable harness. It distinguishes exceptions/timeouts/missing outcomes from rejection, restarts after failed items and inspects reference/type-confusion responses. Leakage detection is token/field/normalized-example/AST lint with one-level assignment dataflow; clean lint cannot prove non-leakage. NO_IMPORT_DEPENDENCE is not proof of conceptual checker independence. commitment_timing distinguishes added together from separately, without proving the latter was earlier. Worker network prevention monkeypatches Python sockets; it is not an OS sandbox and does not strip all inherited credentials. normalize prefers an ACCEPT verdict over accepted:false; a synthetic counterexample reproduced that precedence. The top-level audit avoids a zero-checker run, though worker all_accept by itself is vacuous for an empty list.',
 semantic_differences='Canonical WF23 differs principally in imported module paths, challenge-tree locator and CORE_INTELLIGENCE_ROOT versus OMEGA_INTELLIGENCE_ROOT. Normalization, custody and leakage algorithms match; domain-specific responders remain bounded plugins rather than new workflow families.',
 next_action='Consolidate with WF23 and keep type-confusion/responders and raw outcome records. Require checker-specific strict normalization before treating aggregate ACCEPT as authoritative. Rename or qualify timing/independence/leakage conclusions to the actually measured property in a separately reviewed change. Retain historical audited artifacts without turning them into fresh sealed cases.',
 prerequisite='The audit can inspect any future QM checker, but requires a QM-specific negative/positive/witness mutation panel and a separate adequacy argument. Source hash custody and lexical leakage lint do not establish a QM theorem.',
 runtime='No audit CLI was run, because it recursively loads judge/answer/mutation banks and writes artifacts. Three fresh pure probes exercised normalization and ID leakage only.',
 limitations=['Full worker, main audit, custody, execution and leakage sources read; descriptor/discovery and dependency-comparison core ranges read. Auxiliary special-case/reference-value/semantic responder catalogs and summary aggregation were inventoried and diff-compared, not fully semantically audited.','No actual Git chronology, receipt commitment or historical audited case bank was replayed.']),
'certified_ladder':dict(
 contribution='Registered cost/accuracy experimental design and typed hypothesis reporting over supplied observations; the imported evaluator is a wrapper around canonical domain functions.',
 mathematical_basis='Paired per-item comparisons, censoring at registered caps and declared exact certificate gates; evaluator code implements numerical threshold rules. H0 compares control statuses, H1 uses gains/cost ratios and sample size, H2 only rejects perfectly flat or strictly declining curves.',
 reusable_mechanism_name='registered_cost_ladder_with_bounded_hypothesis_reporting',families=['WF22'],
 rationale='Existing WF22 already owns this design and evaluator. The wrapper self-test uses chosen favorable metrics; it is not experiment data. H0 accepts [{}] as RETAINED, and canonical H2 retains the nonmonotone curve .9,.1,.2 in isolated AST probes. H1/H5 threshold routines do not implement the sign-test significance demanded in the design. P0 calls the same gate twice on a fixed integer-3 expected value; repeated passes are reproducibility, not independent checker implementations. Historical October 15 reports describe an ambiguous stopped send; October 16 reports claim 44 settled replies and one retained reserve. Those prose reports were read as historical claims, not revalidated from the unread ledger/raw/archive data.',
 semantic_differences='Runtime evaluator delegates only differ by pfp versus omega_engine_pfp imports. Design/report differences also include Run O versus Opus naming, native-host environment variable, custody archive locators and Adversary/Woland labels. The report at woland_20261015 matches the canonical adversary_20261015 report by full content diff, not suffix lookup. Original registration bytes must remain distinct.',
 next_action='Consolidate the design/evaluator with WF22 while preserving every historical report and archive identity. Treat H0/H1/H2/H5 evaluator outputs as provisional diagnostics until control completeness and the declared statistical tests are implemented. Never use synthetic self-test RETAINED results to support model benefit.',
 prerequisite='Needs preregistered QM items, an adequate QM checker, disjoint development/held-out encoding, fixed control obligations and analysis consistent with the claim. No existing ladder expected answer may be reused as the new sealed benchmark.',
 runtime='No campaign, ledger, archives or self-test CLI executed. Two exact AST-extracted pure checks reproduced the H0 and H2 weaknesses without constructor/import-driven storage. Historical execution numbers remain report claims.',
 limitations=['Both design documents, hypotheses, wrapper and all three historical report texts fully read; canonical H0-H5 and P0 execution core plus full evaluator tests read. H6-H13 bodies, management_ladder campaign engine and historical raw/storage artifacts were not fully reviewed.']),
'replay_runners':dict(
 contribution='Read-only historical dossier replay with source/request/response binding, exact finite witness checking, reversible representations and explicit live retirement; separate old mode-capsule builders remain artifact generators.',
 mathematical_basis='Exact rational equations, graph cycle rank and minimum forest repair, exhaustive finite F2 spin optimum, weighted L1 primal/dual equality, chain-law/rank/Betti checks with an explicit missing-cup-product refusal. Representation legends are reversible JSON token encodings; seals certify identity, not correctness.',
 reusable_mechanism_name='hash_bound_historical_replay_and_finite_witness_capsules',families=['WF18','WF8'],
 rationale='These mechanisms already exist under WF18/WF8. Dossier live() always refuses; replay recomputes current grades only if pinned source/environment/input/request/raw hashes agree. Stored output is not a fresh generation. Alternative valid certificates are accepted by the finite predicates. The mode execute.py still writes capsule seeds/specs/results and its selected predicates were already assessed in numbered_000_050; it must not be mistaken for a read-only evaluator. publish.py emits historical prose/learning artifacts and requires stored campaign data; it was not run. Dossier tests include independent SymPy/NetworkX controls and tamper mutations, but module collection would load retired plans/cases, so only source was read.',
 semantic_differences='Not a byte-interchangeable copy: imported run.py adds PREVIOUS_CHECKER_SOURCE, PREVIOUS_ACTIVE_DEPENDENCIES and a legacy_archive_set to exact allowed source-key sets. It maps old checker keys to current bytes but still checks the recorded digest. It also falls back to PILOTS when a relocated omega_engine_pfp capsule directory is absent, unlike the canonical unconditional relocated owner. Other changes are package/host/history locators, mode_11 directory label and CLI names. prepare.py pins the same historical commit with a different Git path prefix.',
 next_action='Consolidate kernels and replay under WF18/WF8 only after preserving or deliberately reconciling the extra source-key sets and absent-directory fallback. Preserve archived source snapshots and checker-drift refusals. Keep artifact-writing mode/publish routes separate from the replay API; no automatic historical-source normalization or regenerated answers.',
 prerequisite='Reuse custody and reversible encoding only after defining the QM carrier and independent predicate. The supplied finite rational/F2/graph/chain checks support only their explicit contracts; missing multiplication/continuum/physical premises remain open.',
 runtime='No historical replay, plan extraction, publication or live call performed. All 25 old mode builders had prior hash-bound code reads, reused here; new dossier checker/run/test/prepare/source/publish owners were read. No archived replies/inputs were loaded.',
 limitations=['Auxiliary import/init lines and full mode packet preamble are comparison-only where the prior ledger records selected ranges; the report does not claim every line was independently reread.','Exact-type schemas protect answer ingress for the fixed generated domains, but general malformed task handling and complexity bounds were not certified.']),
'cot_miner.py':dict(
 contribution='Deterministic heuristics extracting evidence-linked, unadmitted candidate guidance from retained reasoning traces.',
 mathematical_basis='Regex/threshold classification and set/count aggregation, with exact test/source references; no mathematical theorem or causal learning estimator.',
 reusable_mechanism_name='unadmitted_failure_pattern_mining',families=['WF3','WF14','WF19'],
 rationale='The existing pilot-estate library contains the same miner. It detects lexical corpus speculation, schema anxiety, substitution, license conflict and token thresholds; fixed rule texts remain admitted:false. These are candidate detectors and human-review leads, not certified mental-state attribution, causal efficacy, automatic immune admission or new mathematical reasoning machinery. Its exact-answer helper checks the top-level type and excludes floats, but nested Python Boolean/numeric equality can still coincide. Metadata source_file is joined to the pilot directory without a containment guard.',
 semantic_differences='Same classification/mining code; only pfp/omega_engine_pfp resource names, pilot root locator and CLI module path differ. Prior 000-050 source context establishes why trace patterns cannot become efficacy claims.',
 next_action='Keep one library miner feeding candidate-only WF3/WF14/WF19 review. Retain source hashes, quotations and false-positive controls; add held-out self-tolerance and adequacy evaluation before admission. Do not use target-paper text or hidden expected answers as mining input.',
 prerequisite='A QM deployment needs public development traces, declared error classes and independent QM checks. The miner does not supply a QM checker or prove transfer.',
 runtime='No trace corpus or source_file target opened and no mine() call made. Full miner and meaningful test source read; tests using real historical traces were not executed.',
 limitations=['Only classifier source/test semantics and canonical differences were reviewed; stored reasoning, historical answer matches and generated learning files were not assessed.']),
'pilot_reply_kit.py':dict(
 contribution='Bounded caller-supplied reply parsing, request matching and domain-pluggable decoding/grading with explicit unauthenticated evidence labels.',
 mathematical_basis='Finite request-ID matching, SHA-256 of source JSON, strict Pydantic ingress and explicit allowed status sets; all mathematical acceptance belongs to the supplied decoder/grade callback.',
 reusable_mechanism_name='caller_supplied_reply_custody_and_domain_grade_adapter',families=['WF1','WF13'],
 rationale='Byte-identical to the existing pilot-estate library. It rejects duplicate JSON keys and foreign/duplicate request IDs, caps input/replies and keeps missing replies NOT_RUN. Request.sha binds source only, not instruction; two different instructions have the same source hash. parse accepts NaN unless the domain decoder refuses it. assess uses XML outcomes, coverage and tests named mutant_* as qualification signals, not a general mutation adequacy proof. It never authenticates a provider reply.',
 semantic_differences='Exact byte match to workflows/library/pilot_estate/pilot_reply_kit.py; no code delta. Domain-specific callback behavior is outside this file and must not be inferred from byte identity.',
 next_action='Consolidate in the existing shared library. Preserve unauthenticated evidence and NOT_RUN labels; require a full instruction/schema/checker binding for future custody and strict finite numeric ingress where mathematically required. Keep adapter tests distinct from checker qualification.',
 prerequisite='Needs a QM answer schema, exact decoder and independently adequate grade callback. The source hash and passing wrapper tests cannot grade QM.',
 runtime='Four fresh pure probes covered duplicate keys, NaN acceptance, unchanged source hash across changed instruction, and missing reply behavior. No subprocess coverage/export/pytest route or caller reply files executed.',
 limitations=['Full owner read. No standalone tracked kit test was found in the targeted test search; fresh probes are a narrow replacement for behavior inspection, not a complete suite.']),
'sqlite_pilot_store.py':dict(
 contribution='Simple run-record storage and callback-based offline regrading.',
 mathematical_basis='Relational persistence of JSON fields and conjunction of checker results; no cryptographic source binding, immutable ledger or independent proof rule.',
 reusable_mechanism_name='run_record_storage_and_callback_replay',families=['WF18','WF11'],
 rationale='Same existing library helper. INSERT OR REPLACE allows a run_id record to be overwritten. An empty checker list returns all_passed=True; a truthy nonboolean checker result also passes. Both behaviors were reproduced on a mocked record with no database opened. The zero-network docstring is a convention: callback execution itself has no network blockade. Stored outcomes and cost floats are not authenticated provider receipts.',
 semantic_differences='Only Adversary/Woland prose and harness-value comments differ; persistence/replay logic is identical. The filename is a library owner, not a new pilot family.',
 next_action='Consolidate the CRUD/regrade helper into the existing library, retaining it only where mutable storage is intended. Use a separate immutable, checker-version-bound custody layer for evidence. Require nonempty exact-Boolean checkers before using replay all_passed as an acceptance decision.',
 prerequisite='Needs a separately registered QM checker and immutable provenance binding; this storage adapter cannot establish QM truth or sealed benchmark custody.',
 runtime='Full source read; two fresh method probes used __new__ plus a mocked in-memory record. No SQLite file, private storage, existing record or provider was accessed.',
 limitations=['Storage transaction/restart/power-loss properties were not tested; no append-only or authentication guarantee is present in this owner.']),
'offline_evaluator.py':dict(
 contribution='Historical raw-observation regrading separated from explicit oracle-fixture creation, with efficacy eligibility forced false.',
 mathematical_basis='Dispatch to a versioned finite task checker with the frozen legacy seed-owned expected object; immutable observation and new evaluation-receipt separation. The local 2x2 Cramer helper is a narrow deterministic example.',
 reusable_mechanism_name='historical_observation_regrade_without_efficacy_promotion',families=['WF18','WF13'],
 rationale='Existing library owner with only import/resource differences. It reads seed.expected_outcome.answer as the old oracle, re-parses saved raw replies through the live_evaluator/checker registry and emits new evaluation records; it does not regenerate observations or establish fresh model performance. The separate --create-fixtures path materializes explicit oracle fixtures. Negative-fixture summaries test supplied cases only and an empty fixture collection has vacuous all-passed counters.',
 semantic_differences='Code is unchanged apart from legacy package/resource locators and sibling evaluator import. Prior hash-bound completed reads were rechecked and the full owner reread for this report.',
 next_action='Consolidate the historical regrader with the existing library and preserve the separate fixture path and efficacy_eligible:false ceiling. Require nonempty fixture panels and an adequate new task checker for new work. Never promote old expected values into the new hidden benchmark.',
 prerequisite='Requires a fresh QM encoding/checker owned outside old expected-answer files. The unchanged QM seed was not read; no transfer claim is supported.',
 runtime='No evaluator CLI, seed, response, fixture or receipt directory opened. Full source and current registry plus prior hash-bound fail-closed gate ranges were reviewed; historical counts were not rerun.',
 limitations=['Canonical domain gate ranges were reviewed in the prior numbered report and hash-bound for reuse; end-to-end legacy import availability and all stored observations are not certified.']),
'live_evaluator.py':dict(
 contribution='Legacy live-dispatch retirement boundary plus strict historical observation binding and offline raw regrading.',
 mathematical_basis='Request/response digest identity, strict JSON parsing and checker-registry delegation; no new mathematical checker. Every fresh legacy dispatch raises a typed migration refusal.',
 reusable_mechanism_name='retired_live_route_with_bound_offline_regrade',families=['WF18','WF1'],
 rationale='Despite its filename this owner refuses new live sends before transport and marks regraded results efficacy_eligible:false. It binds persisted request and provider-response content hashes but that does not independently authenticate provider origin. sanitize_raw_reply strips optional Markdown fences for this historical route; it must not be conflated with the stricter current protocol ingress. Public prompt leak checking is a shallow regex for selected answer-bearing keys, not a non-leakage proof.',
 semantic_differences='Only pfp versus omega_engine_pfp imports differ from the canonical library copy. Retired dispatch semantics are the same; no new live model capability is imported.',
 next_action='Keep one explicit retired-route compatibility adapter and use canonical bounded dispatch for new tasks. Preserve raw bytes and historical hash bindings; do not rewrite old observations to pass a changed checker.',
 prerequisite='A new QM task needs an appropriate schema, encoding and pinned checker on the canonical execution route; this retired wrapper supplies none.',
 runtime='No live call, legacy run directory or seed read. Full owner and legacy-preflight test source read. Tests that copy seed artifacts were deliberately not run.',
 limitations=['No authentication of historical provider origins or metering was performed; no current runtime import test was attempted for old namespace paths.'])}

extra={
'c051_exact_lp_solver_with_duals': [('pfp/infrastructure/synthesis_matrix.py',[75,270])],
'c052_maxflow_mincut_certificates': [('pfp/infrastructure/synthesis_matrix.py',[75,270])],
'c053_bareiss_fraction_free_matrix_inversion':[('pfp/infrastructure/synthesis_matrix.py',[75,270])],
'c054_exact_linear_systems':[('pfp/infrastructure/synthesis_matrix.py',[75,270])],
'c055_assignment_with_potentials':[('pfp/infrastructure/synthesis_matrix.py',[75,270])],
'c059_sql_null_total_query_synthesis':[('pfp/infrastructure/synthesis_matrix.py',[75,270])],
'challenge_suite':[('pfp/infrastructure/challenge_live.py',[160,251]),('pfp/tests/test_challenge_learning.py',[23,170])],
'certified_ladder':[('pfp/domain/pilots/certified_ladder.py',[380,585]),('pfp/use_cases/evaluate_certified_ladder.py',[196,309]),('pfp/tests/test_certified_ladder_evaluator.py',[1,206])],
'cot_miner.py':[('pfp/tests/test_cot_miner.py',[1,102])],
'offline_evaluator.py':[('pfp/domain/pilots/checker_registry.py',[1,93])],
'live_evaluator.py':[('pfp/domain/pilots/checker_registry.py',[1,93]),('pfp/tests/test_legacy_live_preflight.py',[1,141])]}

# Prior gate source context is accepted only if the exact current hash agrees.
prior=json.loads((OUT/'numbered_000_050_reads.json').read_text())
gate=[]
for r in prior:
    if r['path']=='pfp/domain/pilots/fail_closed_gate.py':
        assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']
        gate.append(dict(r,review_level='prior_hash_bound_selected_gate_read',prior_read_ledger='dag/pilot_triage/numbered_000_050_reads.json'))

pilots=[]
for inv in inventory:
    root=inv['id']; d=definitions[root]; prefix='pilots/anomalon_woland/'+root
    evidence_rows=[r for r in reads if r['path']==prefix or r['path'].startswith(prefix+'/')]
    for p,bounds in extra.get(root,[]):
        match=next(r for r in reads if r['path']==p and r['lines']==bounds);evidence_rows.append(match)
    if root in ('offline_evaluator.py','live_evaluator.py'):evidence_rows.extend(gate)
    # Canonical full diffs were compared, while body reads are bounded by the
    # imported ledger. Do not describe unseen generator/supporting bodies as read.
    own_paths={r['path'] for r in evidence_rows};canonical=[]
    for s in inv['sources']:
        if s['path'] not in own_paths:continue
        for m in s['canonical_matches']:
            canonical.append(dict(path=m['path'],sha256=m['sha256'],lines=m['lines'],review_level='canonical_full_file_hash_and_diff_review_body_coverage_follows_imported_read_ledger',compared_imported_path=s['path'],byte_identical=m['byte_identical']))
    evidence_rows.extend(canonical)
    evidence_rows=list({(r['path'],tuple(r['lines']),r['review_level']):r for r in evidence_rows}.values())
    counts=collections.Counter('exact_bytes' if any(m['byte_identical'] for m in s['canonical_matches']) else 'content_diff_reviewed' if s['canonical_matches'] else 'no_canonical_match' for s in inv['sources'])
    coverage=[source_read_coverage(s,evidence_rows) for s in inv['sources']]
    row={k:d[k] for k in ('contribution','mathematical_basis','reusable_mechanism_name','rationale','next_action')}
    row.update(id=root,path=prefix,owner_kind='root_file' if root.endswith('.py') else 'shared_directory',verdict='duplicate_candidate',workflow_mapping=mapping(d['families'],'Existing process/library owner; retain the reusable mechanism there, with the reported limitations and semantic deltas.'),source_evidence=evidence_rows,
      duplicate_evidence=dict(canonical_comparison_counts=dict(counts),semantic_differences=d['semantic_differences'],per_file_comparisons=[dict(path=s['path'],sha256=s['sha256'],lines=s['lines'],canonical_matches=[{k:v for k,v in m.items() if k!='diff'} for m in s['canonical_matches']]) for s in inv['sources']],full_diff_inventory='dag/pilot_triage/shared_runtime_inventory.json',judgment='Semantic recommendation follows owner/checker behavior, not byte similarity alone.'),
      qm_seed_transfer=dict(protected_qm_seed_read=False,mathematical_support_for_unchanged_qm_seed='NOT_ESTABLISHED',requires_seed_appropriate_checker_or_encoding=True,prerequisite=d['prerequisite']),
      actual_execution_status=dict(model_calls=0,full_suite_run=False,description=d['runtime'],fresh_probe_names=[p['probe'] for p in probes['checks'] if p['owner']==root],probe_results='dag/pilot_triage/shared_runtime_probe_results.json',historical_claims_reauthenticated=False),
      consolidation_recommendation=dict(retain_mechanism=True,create_new_family=False,delete_now=False,condition='Review the mapped owner, preserve source/record provenance and reconcile the stated deltas before any archive-backed retirement; this report performs no deletion.'),
      review_coverage=dict(tracked_incoming_files=inv['tracked_count'],ignored_extras=inv['extras_count'],ignored_extra_categories=inv['extras_categories'],source_like_tracked_files=len(inv['sources']),source_files_with_body_or_prior_read_evidence=sum(bool(c['body_read_ranges']) for c in coverage),source_read_coverage=coverage,supporting_sources_not_fully_read=[c['path'] for c in coverage if not c['full_body_read']],unread_tracked_data_paths=inv['unread_tracked_data'],limitations=d['limitations']))
    pilots.append(row)

summary=dict(owner_count=len(pilots),shared_directory_count=10,root_file_owner_count=5,verdict_counts=dict(collections.Counter(p['verdict'] for p in pilots)),new_workflow_families_recommended=0,tracked_incoming_files=sum(x['tracked_count'] for x in inventory),ignored_extras=sum(x['extras_count'] for x in inventory),ignored_extra_classification='All 292 manifest entries in these roots marked source_git_tracked=false are bytecode/cache files, not extra mechanisms.',source_like_files_compared=sum(len(x['sources']) for x in inventory),source_like_files_with_an_exact_canonical_match=sum(any(m['byte_identical'] for m in s['canonical_matches']) for x in inventory for s in x['sources']),fresh_public_probe_count=len(probes['checks']),fresh_probe_assertions_passed=probes['all_assertions_passed'])
report=dict(schema_version='1.0',schema='pfp.imported-pilot-triage.v1',status='complete_first_substantive_review_of_15_shared_owners_not_full_corpus_certification',scope='Manifest-tracked incoming files in the ten requested directories and five exact root-file owners.',authority_effect='None; recommendations only; no imported/canonical source edits or deletion.',summary=summary,
 review_method=['Full primary specifications/TASK documents for six certificate packages; both mathematical checker owners read in full, with previous reads reused only on exact hashes.','All substantive challenge-suite modules and ladder wrapper/designs read; main audit/worker/custody/execution/leakage owners and selected auxiliary cores read; full-read versus selected/diff-only evidence stays explicit.','Canonical comparisons use dag/file_inventory.json only to find candidates, then current file hashes and complete unified diffs. The manually relocated ladder report is mapped explicitly. Semantic behavior and integration differences determine consolidation recommendations.','The common reference self-check runners were reviewed through one complete C051 body plus complete cross-runner diffs. Task generators, reference solver internals and auxiliary catalogs were compared for duplication but not claimed as full substantive reads.','29 synthetic offline probes use invented public data and explicit network refusal. AST-extracted ladder checks use recorder stand-ins rather than constructing receipt writers. No full legacy test module was imported where collection loads case banks or seeds.','Data/artifact review is limited to tracked manifest paths/counts plus the three ladder report texts. Inline public examples embedded in runner/test source were read as code. Historical JSON/SQLite/raw captures/archives, stored judge cases and hostile-mutation banks were not opened.','The canonical family registry and numbered_000_050/051_101 recommendations informed mapping. No generated composition-node census or literature novelty claim was made.'],
 evidence_limits=['No protected QM seed, private storage, credentials or bundled third-party dependency source was read. No model calls, local model inference, corpus edits, runtime overlay, publication or deletion occurred.','Historical report numbers and model/pricing names are provenance claims, not current API facts or freshly authenticated experiment outcomes.','Two checker acceptances, hash custody, source similarity, leakage lint, mutation counts and model efficacy are separate claims.','No old expected answer, target paper or historical raw output was designated as a new workflow input or sealed benchmark.','Current import/resource-path failures were not repaired; direct checker probes deliberately bypass package entrypoints and cannot establish full CLI portability.','This first substantive pass covers all 15 owners but intentionally does not fully audit generated data, reference algorithms, every auxiliary audit plugin, full budget engines or historical stores.'],
 substantive_findings=[
  'C052: both judges accept capacity 1.9 after int() truncation. Agreement is not adequate integer ingress.',
  'C059: SQLite and Python oracle disagree on TEXT COALESCE truth; null, heading, empty-suite and read-only controls pass only the tested finite inputs.',
  'C054/C055: first judge accepts UNKNOWN plus a valid witness; the second and paired gate reject it. This narrows the earlier first-checker-only observation.',
  'Ladder: H0 retains an incomplete record and H2 retains a nonmonotone curve; favorable self-test inputs do not establish experiments or declared significance.',
  'SQLite store: mutable replacement, vacuous empty-checker pass and truthy nonboolean acceptance require a separate custody/acceptance boundary.',
  'Reply kit: source hashes omit instruction; generic JSON parse admits NaN. Domain callbacks and full request binding remain necessary.',
  'Judge audit: normalization can accept contradictory verdict/accepted fields; leakage and independence/timing checks are bounded diagnostics, not proofs.',
  'Replay: preserve additional imported exact legacy source-key sets and explicit owner fallback differences before consolidation.'],
 context_evidence=[evidence('dag/workflows_dag.json',level='selected_existing_workflow_family_nodes_only'),evidence('dag/migrations/anomalon_pilots_move.json',level='manifest_metadata_paths_tracked_flags_and_hashes_only'),evidence('dag/pilot_triage/numbered_000_050.json',level='prior_report_context_and_hash_bound_source_ledger'),evidence('dag/pilot_triage/numbered_051_101.json',level='prior_report_context_and_hash_bound_source_ledger')],pilots=pilots)
(OUT/'shared_runtime.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'shared_runtime_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'shared_runtime_reads.json').write_text(json.dumps(list({(r['path'],tuple(r['lines']),r['review_level']):r for r in reads}.values()),indent=2)+'\n',encoding='utf-8')
md=['# Shared runtime and checker triage','',f"Reviewed all **{summary['owner_count']} requested owners**: 10 directories and five root files. Recommend consolidation into existing owners for all 15, retaining their reusable mechanisms. **No new workflow family; no deletion performed.**",'',f"Scope: **{summary['tracked_incoming_files']} tracked incoming files** and **{summary['ignored_extras']} ignored bytecode/cache extras**. Compared {summary['source_like_files_compared']} source-like files; {summary['source_like_files_with_an_exact_canonical_match']} have an exact canonical match. Byte equality is custody evidence, not the sole basis for a verdict.",'','The JSON report carries per-source hashes/ranges, explicit body/diff review levels, canonical mappings, unread supporting/data paths and QM prerequisites. No protected QM seed, private storage, credentials or third-party dependency code was read. No old answer or target paper was used as a new benchmark input.','',f"**Fresh verification:** {len(probes['checks'])} synthetic offline behavior probes; all expected observations reproduced. Some assertions intentionally reproduce defects. No archived case bank or provider run was executed.",'']
md += ['- '+x for x in report['substantive_findings']]
md += ['','| Owner | Reusable mechanism | Existing family | Verdict |','|---|---|---|---|']
for p in pilots:md.append(f"| `{p['id']}` | {p['reusable_mechanism_name']} | {', '.join(x['family_id'] for x in p['workflow_mapping'])} | duplicate_candidate |")
for p in pilots:
    md += ['',f"## {p['id']}",'',p['contribution'],'',f"**Mathematics:** {p['mathematical_basis']}",'',p['rationale'],'',f"**Execution:** {p['actual_execution_status']['description']}",'',f"**Canonical difference:** {p['duplicate_evidence']['semantic_differences']}",'',f"**Recommendation:** {p['next_action']}",'',f"**QM prerequisite:** {p['qm_seed_transfer']['prerequisite']}",'', '**Review ceiling:** '+' '.join(p['review_coverage']['limitations'])]
    owned=[e for e in p['source_evidence'] if e['path']==p['path'] or e['path'].startswith(p['path']+'/')]
    md += ['','Evidence: '+', '.join(f"`{e['path']}` L{e['lines'][0]}–{e['lines'][1]} ({e['sha256'][:12]})" for e in owned[:8])+'. Full source ledger and canonical comparisons are in the JSON report.']
md += ['','## Review boundaries','']+['- '+x for x in report['evidence_limits']]
(OUT/'shared_runtime.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
