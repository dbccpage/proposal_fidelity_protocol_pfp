"""Assemble reviewed teaching findings; validates custody, never changes sources."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / 'dag/reviews/additional_eis_pciv_teaching_scripts'
scope = json.loads(Path(str(P)+'_scope.json').read_text())
rows = scope['files']
ledger = json.loads(Path(str(P)+'_read_ledger.json').read_text())
checks = json.loads(Path(str(P)+'_checks.json').read_text())

def pinned(path, ranges, kind='fresh_full_teaching_body'):
    b = (ROOT/path).read_bytes()
    n = len(b.decode('utf-8').splitlines())
    assert all(1 <= a <= z <= n for a,z in ranges)
    return {'path':path, 'sha256':hashlib.sha256(b).hexdigest(), 'lines':ranges,
            'evidence_kind':kind}

def ev(i, a, z):
    return pinned(rows[i]['path'], [[a,z]])

def dep(p, a, z):
    return pinned(p, [[a,z]], 'targeted_dependency_body_reread_not_new_full_file_credit')

assessments = [
('Admission and execution routing',
 'Separates a clean pharmacy report from admission, and distinguishes admitted active snapshots, pre-dispatch/pre-seal gates, compilation, defect witnesses and scaffold writes. The four unjoined registers are a useful warning against a single assumed lifecycle.',
 'A route description is not an end-to-end run or authentication proof. HOLD/unavailable states must be checked at each consuming adapter; common scene labels do not supply that execution evidence.'),
('Candidate anti-skills and mutation gaps',
 'Names four separate registries and distinguishes proposed anti-skills from inverses or antimorphisms. Explains resolver search then attached guards and an unbuilt certificate-field detector, retaining proposal status.',
 'A lexical guard firing establishes its predicate on that input, not a computed certificate field or general adequacy. This script is more cautious than Level 10 algebraic-dual language.'),
('Finite pharmacy diagnostics',
 'Lists the 12 failure classes and the three Refuse/two Hold/seven Finding partition; the finding has no repair and a zero-hit report grants no admission.',
 'These are named mechanical/lexical checks, not semantic completeness. The script corrects the Level 00 blanket halt claim; actual run evidence remains prior native review, not fresh execution.'),
('Seven role separation',
 'Correctly locates AntiSkillSpecV2 and its fixture/receipt/decision/registry/profile/hit roles in operads, with PROPOSED/runtime-false and same-spec PASS/APPROVE bindings. Distinguishes candidate-only farm from direct admitted-string records with None authority.',
 'Record consistency and immutable fields do not authenticate a human issuer or supply execution of the declared predicate. This directly corrects the level page constructor/owner assertions.'),
('Behavioral fixture polarity',
 'Explicit producer/schema mapping avoids positive/negative naming ambiguity. The script distinguishes the two supplied Boolean match results, failed-binding suspension, and a separate retirement proposal that does not itself change custody.',
 'Booleans and fixture receipt equality are not a fresh detector evaluation. The level page conflates proposal-only handling with validate_binding, which actually writes Suspended.'),
('Finite self-panel screening',
 'Separates native Proposed->Candidate/Retired screening from human admission. Explains Python evaluate_candidate always false admission versus evaluate_rule.is_admitted as a finite-panel result, and requires matcher identity for non-regex rules.',
 'No-match is conditional on the supplied panel and matcher. Newline panel hashing and placeholder-panel behavior have prior source findings; this script does not authenticate the panel or prove future nonreactivity.'),
('Guard conjunction and collapse checks',
 'Specifies admitted, matched, host-danger, nonsuspended conjunction and identifies concrete subject/evidence/observer checks. Separates Python independent evaluation from the weaker basic native gate.',
 'Metadata inequality and a HOST label do not prove statistical or causal independence. This script has better API distinctions than Level 04; a real trusted observation adapter remains necessary.'),
('Bounded correlation graph support',
 'Describes occurrence and key-tuple deduplication, edges for shared nonempty model/scaffold/precedent/root keys, and exact maximum independent set on at most 32 retained nodes. The A-B-C path has support 2, freshly checked over all eight subsets.',
 'Missing keys create no edges and graph independence is relative to supplied labels. Integer support passed to promotion is not a carried proof of the graph or authenticity of observations.'),
('Provisional custody and queue boundary',
 'Explains support_count>=3 produces Provisional and review_queued metadata, without authenticated admission or an actual queue append. Distinguishes the native witness-count path and diagnostic-only provisional activation.',
 'A review flag is not delivery to a human queue. Caller support counts and scopes remain premises; the script explicitly identifies missing diagnostic graph storage rather than claiming it is implemented.'),
('Idle decay versus selection',
 'Accurately explains stimulation, additive affinity, linear idle cutoff, and mutation copying matcher/tally without custody. Distinguishes finite nonnegative Python floats/ints from exact-boost refusals and no-op compatibility paths.',
 'The name half-life is an idle limit here, not exponential decay; no affinity ranking or evolutionary improvement follows. The script corrects stronger exact-selection terminology in related teaching material.'),
('Three distinct regulatory operations',
 'Separates the five-hit unsuspended anergy proposal, Python signal-one-only Fraction toxicity with threshold 1/5, and Rust FP/(TP+FP) strict threshold 1/10 after ten samples. Notes no automatic queue call from the proposal.',
 'These denominators and effects differ. Supplied trigger/TP/FP data require provenance; neither measure is the population false-positive probability FP/(FP+TN). Level 08 describes a different count-based API.'),
('External admission metadata',
 'Explains candidate-only requests, distinct observation digests, equal-fixture refusal, rule-byte binding and separate external admission of native Candidate status. Eligibility is kept distinct from admission.',
 'Nonblank issuer/scope and a receipt prefix are consistency checks, not authenticated human signatures. The default Python applier performs its own check and raises on digest mismatch, so the narrated human_admit/refusal contract is not universal across adapters.'),
('Diagnostic homology ceiling',
 'Distinguishes caller-supplied telemetry counts, operational-binding refusal, finite F2 computation, and the separate GLOBAL_H1_OBSTRUCTION token. Explicitly states the native anti-skill spec has no polarity enum and the farm probes are not a gate.',
 'The telemetry record computes no barcode and supplies no formal duality or model-safety metric. This is a useful correction of the Level 10 invented Rust seam and unsupported algebraic language.'),
('Level 00 pharmacy contract',
 'The finite detector taxonomy, zero-repair intention and clean-report non-admission distinction are useful. The page also describes all hits as immediate halts and claims zero-allocation semantic/AST filtering, unlike the actual diagnostic routing and owned String/Vec records.',
 'Frontmatter computed/gated flags are not a receipt. Several type fields differ from the owner; declared fixture success would only establish those fixtures, not elimination of all self-certification or counterfeit receipts.'),
('Level 01 role contract',
 'Separation of specification, fixtures, evaluation, decision, registry, scope and hit is a reusable design discipline. The page mislocates the actual roles and claims direct admitted Antibody construction raises, contrary to both source and companion script.',
 'Frozen dataclasses and supplied decision records do not provide complete structural defense against arbitrary self-modification, authenticated signatures or actual evaluator execution.'),
('Level 02 polarity contract',
 'The finite conjunction of all must-match hits and all near-miss nonhits is mathematically sound for a declared detector and supplied finite fixtures. Producer/schema polarity mapping is useful.',
 'The referenced fallback validates supplied booleans, mutates binding custody to Suspended, and returns a separate proposal without queue delivery. The page instead promises unchanged custody and a queued proposal; unseen false-positive elimination is not proved.'),
('Level 03 self-panel contract',
 'Universal quantification over an explicitly finite self-panel correctly defines negative-selection success. The non-admission intention is sound, but SelfPanelV1/screen_candidate/NegativeSelectionReceiptV1 code is illustrative rather than the linked Python API.',
 'The actual constructor can use two placeholder fixtures for an arbitrary panel id; no hash-chained authenticated panel or permanent elimination follows. evaluate_rule uses is_admitted=True for fixture success, so that field name cannot be treated as a uniform operational law.'),
('Level 04 activation contract',
 'The four-condition Boolean law is a useful normative gate, and signal 2 alone must not be confused with a learned guard hit. The embedded evaluate_activation/AdmittedGuardV1 API is not the linked owner API.',
 'A source_locus inequality and supplied is_independent_witness Boolean cannot establish an independent host observation. Explicit adapter trust, witness binding and the selected gate variant are needed before the broad elimination/guarantee wording is warranted.'),
('Level 08 count-based anergy proposal',
 'The written count threshold is a coherent proposed policy distinct from rational toxicity and false-discovery proportion. Its code simply uses len(fp_receipts), and a fresh literal-snippet control generated a target-detector proposal from five duplicate other-detector receipts with empty evidence.',
 'This is not the current pfp/eis Treg API, authenticated receipt audit or implemented checkpoint-reversal protocol. The fresh counterexample applies to the teaching snippet, not the different production supervisor.'),
('Level 10 antimorphism/telemetry contract',
 'Diagnostic-only telemetry and non-equivalence to the symbol-game H1 token are useful boundaries. Merely specifying a map B->Omega does not define a contravariant functor, composition reversal or a duality; the stated enum/spec fields are absent from the native spec.',
 'Opposite-polarity/formal-dual wording is aspirational. Caller-supplied component/cycle counts are not computed persistence diagrams, and telemetry quarantine does not establish a mathematical relationship with a constructive skill.'),
('Genome versus execution occurrence',
 'Distinguishes immutable identity material from current custody/retrieval/maturity and from repeated stochastic occurrences. Explicitly includes protected spans in the identity tuple and warns equal digests do not make provider behavior deterministic.',
 'Canonical encoding and collision resistance remain assumptions. No new hash-identity, idempotency or provider repeatability test ran here; parent identity-level findings remain distinct.'),
('Causal lineage versus reference',
 'Separates inheritance/realization from citations, and excludes reference edges from generation and antibody propagation. Requires a host receipt for the intended causal edge rather than treating similarity as ancestry.',
 'A DAG label and receipt string alone do not verify causality, acyclicity or issuer authenticity. Parent notebook cycle counterexample is prior evidence about the toy implementation, not this script or a new native test.'),
('Canalized mutation scope',
 'Limits the forge proposal to plastic scaffold and excludes evaluation, review, activation and admission by the operator. This supplies a concrete task-preservation obligation for mutation.',
 'Actual range checks and host write confinement must enforce it, including zero-width insertion. Parent notebook insertion counterexample is referenced as prior toy evidence; no production forge ran.'),
('Lamarckian integration route',
 'Names the measured artifact, defect witness, scaffold insertion and hop weight (1/2)^d for d<=10; importantly labels unexercised arrows as design and retains efficacy=NOT_MEASURED.',
 'Line 28 nonetheless says thymic screening admits or drops, contradicting the explicit separate admission step in EIS 520.03. Geometric attenuation is a policy, not evidence of semantic improvement or operationally completed end-to-end learning.'),
('Two-axis Pareto selection',
 'Gives correct mixed-direction dominance: maximize task-success credit, minimize failures, weakly improve both and strictly one. Separates deterministic within-front tie order, exact ratio denominators, selected-attempt reduction and retrieval exploration.',
 'Counters depend on independently adequate task outcomes and exposure; raw credit is not an unbiased success-rate estimate. Front membership is not admission, and no model-performance comparison follows.'),
('Exact inverse-lineage PageRank',
 'States the child-to-parent row construction, q pass fraction/default half, damping 17/20 and rational fixed-point equation. The two-node 57/97,40/97 solution was freshly checked by exact substitution.',
 'Require nonempty finite node set, valid normalized rows and the intended edge semantics; the solver does not determine causal ancestry. Native invalid-singleton/duplicate-edge caveats remain in prior reviews; one exact example is not general implementation certification.'),
('Retrieval eligibility and per-use decay',
 'Separates Active plus ADMITTED_LOCAL read-scope filtering from unmeasured/front/id ordering. Explains floor-based independently aged citation contributions and correctly computes 1+25/256=281/256.',
 'The decay sum is not the retrieval sort, rank or admission. H must be meaningful and histories accurate; the parent continuous-versus-floor notebook mismatch is reused, not rediscovered as a new issue.'),
('Integer reserve allocation',
 'States the explicit n<4 table and 60/30/10 floors with earlier-bucket ties. Fresh independent integer arithmetic checked nonnegative seats summing to n for n=0..10000, including (6,3,1) at 10 and (12,6,2) at 20.',
 'This is a policy allocation, not Pareto optimization or a theorem of exploration quality. Python unbounded arithmetic does not test native integer overflow; parent different-ratio notebook and older documentation findings remain separate.'),
('Revocation versus forward taint',
 'Separates digest-wide rule disarming from graph reachability and states OR inheritance/realization propagation without reference-edge spread or decay.',
 'A taint closure is conditional on authenticated initial taint and accurately typed causal edges; it is not a proof that all descendants are semantically defective. Parent toy closure enumeration is prior evidence only.'),
('Durable log ownership',
 'Identifies the OEOS event log plus packet CAS as intended durable source and lineage/immunity JSONL as rebuildable projections. Distinguishes reconstruction from admission and PFP measurement.',
 'This is an ownership description, not a crash-consistency, atomicity, exactly-once or durable replay demonstration. No event-log owner executed; parent toy payload-hash-only finding remains relevant.'),
('Crossover and bounded island migration',
 'Names protected/homologous block constraints, conflicting immunity versions, Wild child custody, and one-hop snapshot ring migration with objective/period/quota/capacity constraints. Explicitly says two nonempty witnesses are not issuer authentication and finite freezing is not a convergence theorem.',
 'These are finite transitions under supplied inputs, not demonstrated open-ended improvement or a token budget. No native ecology/crossover run occurred; notebook list-transfer shortcomings are prior evidence.'),
]
assert len(assessments) == 31
file_reviews = []
for i,(row,(purpose,assessment,limit)) in enumerate(zip(rows,assessments)):
    b=(ROOT/row['path']).read_bytes(); n=len(b.decode().splitlines())
    assert hashlib.sha256(b).hexdigest()==row['sha256'] and n==row['lines']
    assert any(r['path']==row['path'] and r['sha256']==row['sha256'] and r['reviewed_lines']==[[1,n]] for r in ledger)
    file_reviews.append({'path':row['path'],'sha256':row['sha256'],'bytes':len(b),
                         'full_source_read':True,'reviewed_lines':[[1,n]],'source_line_count':n,
                         'review_level':'full_text_source_review','reading_method':'complete_numbered_body_read',
                         'parsed_value_read':False,'purpose':purpose,'assessment':assessment,
                         'limitations':limit})

claims = [
 {'id':'EPTS-C01','statement':'The scripts contain reusable bounded mechanisms: explicit fixture polarity, finite self-panel screening, metadata correlation graphs, proposed/admitted separation, protected scaffold mutation, mixed-direction Pareto order, exact damped rank, integer reserve allocation, and typed forward taint. Their usefulness is conditional on declared inputs, evaluator adequacy and trusted custody; names do not establish biological or model efficacy.',
  'evidence':[ev(4,26,28),ev(5,26,28),ev(7,26,28),ev(22,26,31),ev(24,26,30),ev(28,26,30)]},
 {'id':'EPTS-C02','statement':'Fresh independent arithmetic confirms the narrated two-node PageRank fixed point (57/97,40/97), the A-B-C support graph maximum of2, the sum281/256, and nonnegative exact 60/30/10 reserve counts summing to capacity for0..10000. These checks validate the stated finite arithmetic, not native code, input authenticity or learning improvement.',
  'evidence':[ev(25,26,26),ev(7,26,28),ev(26,26,26),ev(27,26,26)],'validation':str(P.relative_to(ROOT)).replace('\\','/')+'_checks.json'},
 {'id':'EPTS-C03','statement':'The EIS scripts explicitly separate finite negative selection from admission, graph support from promotion input, provisional metadata from queue delivery, idle counts from affinity selection, three distinct regulatory operations, and telemetry counts from computed homology. These caveats should be retained when reconciling the stronger level pages.',
  'evidence':[ev(5,26,28),ev(7,26,28),ev(8,26,30),ev(9,26,28),ev(10,26,30),ev(12,26,30)]},
 {'id':'EPTS-C04','statement':'The PCIV scripts distinguish genome from occurrence, ancestry from reference, ranking from custody, and migration from admission; the crossover script explicitly limits witnesses to presence checks and treats freezing as a stopping policy. The Lamarckian script also preserves efficacy=NOT_MEASURED and unexecuted diagram status, despite its separate erroneous thymus-admission sentence.',
  'evidence':[ev(20,26,30),ev(21,26,31),ev(23,24,32),ev(25,26,30),ev(30,26,32)]},
]

findings = [
 {'id':'EPTS-F01','severity':'medium','statement':'Level00 says any innate detector hit halts execution and advertises zero-allocation filtering/elimination of unauthorized claims. The current owner routes seven classes to diagnostic Finding, two to Hold and three to Refuse, and constructs owned String findings; its own header limits evidence to named fixtures. The script gives the more accurate routing partition.',
  'evidence':[ev(13,72,74),ev(13,103,111),ev(13,156,166),ev(2,26,30),dep('code/rust/core_prompt_civilization/src/pharmacy.rs',1,18),dep('code/rust/core_prompt_civilization/src/pharmacy.rs',83,141)],
  'prior_context':['additional_native_systems_03: NATIVE03-PCIV-009'],
  'recommended_action':'Document routing by disposition, remove zero-allocation and universal elimination claims, and bind fixture results to actual retained tests rather than evidence-grade flags.'},
 {'id':'EPTS-F02','severity':'medium','statement':'Level01 attributes the seven roles to eis.value_objects and says direct Antibody(..., pharmacy_status="admitted") raises. The companion script locates the roles in operads and correctly permits a direct known status with authority_effect None; the current Antibody constructor enforces known-status and None-authority checks, while farm fixes candidate. Signed-human/complete-defense language also exceeds record consistency.',
  'evidence':[ev(14,25,26),ev(14,64,80),ev(14,113,126),ev(3,26,28),dep('eis/domain/pharmacy_models.py',47,86),dep('eis/domain/pharmacy_models.py',88,135)],
  'prior_context':['additional_operads_core_remaining: operads/domain/anti_skills/anti_skill_v2.py full-body assessment'],
  'recommended_action':'Use the canonical role owner and distinguish farm guarantees, observational status records, trusted admission and actual runtime authority. Replace illustrative types with labeled examples or pinned real constructors.'},
 {'id':'EPTS-F03','severity':'medium','statement':'Level02 promises fixture failure queues a retirement proposal while custody stays unchanged. The linked default validate_binding consumes supplied booleans and sets custody="Suspended" on failure; handle_validation_failure only returns a proposal. The script distinguishes these operations, so the level conflates different effects and overstates executed detector/queue evidence.',
  'evidence':[ev(15,74,86),ev(15,114,130),ev(4,26,28),dep('eis/domain/external_admission.py',383,451)],
  'recommended_action':'Specify which operation changes effectiveness/custody and which merely returns a proposal. Add an actual detector/queue adapter if those broader workflow claims are intended; keep finite fixture agreement separate from unseen accuracy.'},
 {'id':'EPTS-F04','severity':'medium','statement':'Level03 presents a cryptographically sealed/hash-chained self-panel and screen_candidate receipt API as the Python seam, plus permanent elimination and a uniform never-is_admitted rule. The linked owner accepts literal fixture tuples or two placeholders for an arbitrary panel id, exposes evaluate_candidate/evaluate_rule, and the latter sets is_admitted=True for no hits while explicitly limiting it to fixtures. The script explains this overloaded field; the level does not.',
  'evidence':[ev(16,54,77),ev(16,83,117),ev(5,26,28),dep('eis/domain/thymus.py',94,129),dep('eis/domain/thymus.py',145,216)],
  'prior_context':['systems_audit: SYS-EIS-001','additional_native_systems: NATIVE-EIS-001 and NATIVE-BUG-006'],
  'recommended_action':'Label the code as a proposal or bind to actual APIs. Name the exact finite panel and matcher, separate panel result from operational admission, and require independently verified panel custody before describing cryptographic sealing.'},
 {'id':'EPTS-F05','severity':'medium','statement':'Level04 describes evaluate_activation with a supplied is_independent_witness flag and claims elimination of self-referential danger. The current linked owner has distinct evaluate_independent, evaluate_conjunction and custody evaluation APIs, while the script distinguishes additional native/guard paths. Boolean conjunction or unequal origin labels alone does not prove an independent host observation.',
  'evidence':[ev(17,69,81),ev(17,85,117),ev(17,130,136),ev(6,26,30),dep('eis/domain/danger_gate.py',184,257)],
  'prior_context':['systems_audit: SYS-EIS-003','additional_eis_pciv_education_remaining: EPE-F006'],
  'recommended_action':'Name the concrete adapter and trust boundary for the witness; keep the four-condition law normative and state the exact collapse cases tested. Do not transfer toy Boolean or label checks into a general independence guarantee.'},
 {'id':'EPTS-F06','severity':'medium','statement':'Level08 teaches a five-receipt count Treg with authenticated audit and checkpoint reversal, but pfp.domain.immune.treg re-exports the Fraction signal-one-toxicity supervisor. Its literal snippet also accepts five duplicate receipts for another detector with empty subject/auditor fields and produces a proposal for the requested detector. The companion script correctly separates the count-only anergy proposal, Python toxicity and Rust false-discovery suspension.',
  'evidence':[ev(18,63,86),ev(18,92,138),ev(10,26,30),dep('pfp/domain/immune/treg.py',1,24),dep('eis/domain/treg.py',191,264),dep('code/rust/core_epistemic_immune_system/src/regulation.rs',1,87)],
  'validation':str(P.relative_to(ROOT)).replace('\\','/')+'_checks.json#level08_receipt_binding_counterexample',
  'recommended_action':'Separate the three policies and their denominators/effects. Label the illustrative count supervisor as proposed; if retained as executable teaching, validate detector binding, receipt uniqueness and evidence before counting. Do not claim implemented checkpoint reversal without an owner.'},
 {'id':'EPTS-F07','severity':'medium','statement':'Level10 calls anti-skills formal algebraic duals while only defining a map B->Omega, with no reverse-composition, functorial or duality law. Its AntiMorphismPolarity/AntiSkillSpecV1 Rust snippet is not the linked native spec, which has no polarity field. The companion script explicitly says the telemetry stores caller counts and the farm is a refusal demo, not a polarity algebra.',
  'evidence':[ev(19,53,75),ev(19,81,104),ev(19,118,124),ev(12,26,30),dep('code/rust/core_epistemic_immune_system/src/anti_skill.rs',13,71),dep('code/rust/core_prompt_civilization/src/pharmacy.rs',1,6)],
  'recommended_action':'Retain the diagnostic boundary but describe anti-skills as predicates/review operations unless an explicit algebra and laws are supplied. Mark invented seams as proposed and avoid equating caller counts with persistence computation.'},
 {'id':'EPTS-F08','severity':'medium','statement':'PCIV script400.03 says OEEIS thymic screening admits or drops an antibody. EIS script520.03 and the native state machine separate finite screening to Candidate from subsequent external admission. The same PCIV script labels the integration as design and efficacy unmeasured, but that does not correct the admission sentence.',
  'evidence':[ev(23,24,32),ev(5,26,28),dep('code/rust/core_epistemic_immune_system/src/anti_skill.rs',110,131),dep('eis/domain/thymus.py',112,129)],
  'recommended_action':'Replace the screening/admission conflation with explicit screening, external decision and activation steps, and preserve the unmeasured integration ceiling.'},
 {'id':'EPTS-F09','severity':'medium','statement':'All24 scripts reuse generic Executed/Tested/Pinned scene labels and direct learners to companion notebooks. Parent notebook review found constant self-comparisons/manual exceptions and several different toy algorithms; those notebooks do not reproduce every narrated runtime mechanism. These are recording instructions, not evidence that a video or runtime falsifier has executed.',
  'evidence':[ev(0,13,18),ev(9,15,18),ev(25,15,18),ev(29,15,18)],
  'prior_context':['additional_eis_pciv_education_remaining: EPE-C04/EPE-C05 and EPE-F009/EPE-F010/EPE-F011/EPE-F012','additional_eis_pciv_education_eis_notebook_checks.json','additional_eis_pciv_education_pciv_notebook_checks.json'],
  'recommended_action':'Give each scene an exact runnable example, observed expected result and specific countercontrol, or label it planned/illustrative. Keep the notebook toy result and the separately reviewed runtime result in different evidence tracks.'},
 {'id':'EPTS-F10','severity':'low','statement':'Of271 local-link occurrences in these31 bodies,156 do not resolve and84 resolve outside the repository. Script production links commonly ascend six directories from a five-directory location, level links ascend four from three, and old engine/crates_rs paths also need reconciliation with code/rust. Missing cross-curriculum/arena references add separate gaps.',
  'evidence':[ev(3,26,32),ev(13,25,25),ev(25,26,30),ev(29,26,30)],
  'validation':str(P.relative_to(ROOT)).replace('\\','/')+'_checks.json#links',
  'prior_context':['additional_eis_pciv_education_remaining: EPE-F008 covers a disjoint31 curriculum/concept pages'],
  'recommended_action':'Repair links relative to each actual source location, then map moved local owners through custody metadata; mark intentionally foreign/unavailable references. Preserve the absent-target inventory rather than guessing replacement content.'},
]

dependency_ranges = {
 'code/rust/core_prompt_civilization/src/pharmacy.rs':[[1,155]],
 'eis/domain/thymus.py':[[94,216]],
 'eis/domain/treg.py':[[191,272]],
 'eis/domain/external_admission.py':[[307,347],[383,451]],
 'eis/domain/pharmacy_models.py':[[1,138]],
 'code/rust/core_epistemic_immune_system/src/anti_skill.rs':[[1,145]],
 'code/rust/core_epistemic_immune_system/src/regulation.rs':[[1,153]],
 'eis/domain/danger_gate.py':[[184,257]],
 'pfp/domain/immune/treg.py':[[1,24]],
}
dependencies = [pinned(p,r,'targeted_dependency_body_reread_not_new_scope_credit') for p,r in dependency_ranges.items()]
prior = []
for name in ['systems_audit','additional_native_systems','additional_native_systems_02','additional_native_systems_03',
             'additional_operads_core_remaining','additional_eis_pciv_remaining',
             'additional_eis_pciv_education_remaining','additional_eis_pciv_education_lesson_checks',
             'additional_eis_pciv_education_eis_notebook_checks','additional_eis_pciv_education_pciv_notebook_checks']:
    p=ROOT/'dag/reviews'/f'{name}.json'
    prior.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                  'use':'Selected relevant findings/claims or owner assessment; no new full-report/source reading credit and no fresh execution credited.'})

report = {'schema_version':'teaching-source-audit/v1','source_commit':scope['source_commit'],
 'status':'complete_declared_31_file_scope','scope_manifest':P.relative_to(ROOT).as_posix()+'_scope.json',
 'parent_scope':scope['parent_scope'],'summary':{'files':31,'bytes':sum(r['bytes'] for r in rows),
     'lines':sum(r['lines'] for r in rows),'narration_scripts':24,'eis_level_pages':7,
     'full_body_reads':31,'partial_body_reads':0,'bounded_artifacts':0,'pending':0,
     'claims':len(claims),'findings':len(findings),'fresh_bounded_controls':len(checks['controls']),
     'local_link_occurrences':271,'unresolved_local_links':156},
 'method':['Exact parent-scope subset frozen before reading; four .gitkeep markers explicitly excluded, as are all PCIV levels and both level README files owned by parent.',
           'Every selected Markdown body was displayed untruncated with numbered lines and SHA verified; no template substitution or semantic scan credited as a full read.',
           'Compared claims with companion scripts, targeted already-reviewed owner spans and selected prior audit evidence; dependencies are separate from the31-path reading ledger.',
           'Fresh execution was limited to independent Fraction/integer arithmetic and the complete reviewed Level08 literal Python snippet with standard-library names supplied.',
           'No original source, notebook, shared report, DAG or coverage changed.'],
 'claims':claims,'findings':findings,'file_reviews':file_reviews,'dependency_readings':dependencies,
 'prior_evidence':prior,'fresh_validation':P.relative_to(ROOT).as_posix()+'_checks.json',
 'pending_paths':[],
 'limits':['Full prose reading establishes what the teaching sources say, not correctness of every referenced implementation.',
           'No new notebook/kernel/native/provider run, renderer/media generation, foreign-repository read/write, or private benchmark access.',
           'No empirical learning, safety, model-performance or biological claim was established. Biological analogies were not independently adjudicated.',
           'The pure arithmetic checks have explicit finite scope; runtime integer limits, authentication and real task outcomes remain separate obligations.',
           'Parent probes and historical source results are prior evidence. This report does not add their counts to fresh test totals.',
           'Link checks cover Markdown local path occurrences only, not anchors, prose-only references or remote availability.']}
Path(str(P)+'.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

md = ['# EIS/PCIV teaching scripts and remaining EIS levels','',
      'Complete: **31/31 full bodies**, 164,104 bytes, '+str(report['summary']['lines'])+' lines; 24 narration scripts and 7 EIS level pages. No pending files. All frozen source hashes matched. No originals were changed.','',
      'The scripts generally give more accurate implementation boundaries than the EIS level pages. The useful mechanisms are finite tests and state policies; several level pages instead present illustrative APIs, proposed custody flows or algebraic labels as computed/gated behavior. The PCIV Lamarckian script also incorrectly gives thymic screening admission authority.','',
      '## Findings','']
for r in findings:
    md += ['### '+r['id']+' ('+r['severity']+')','',r['statement'],'',
           '**Action:** '+r['recommended_action'],'',
           '**Evidence:** '+ '; '.join('`'+e['path']+':'+','.join(str(a)+'-'+str(z) for a,z in e['lines'])+'`' for e in r['evidence'])+'.','']
    if r.get('prior_context'):md += ['**Prior context:** '+'; '.join(r['prior_context'])+'.','']
md += ['## Supported claims','']
for c in claims:md += ['- **'+c['id']+':** '+c['statement']]
md += ['', '## Fresh checks and evidence limits','',
       '- Exact substitution verifies the two-node rank (57/97,40/97); eight subset checks verify the A-B-C support maximum of 2; 1+25/256=281/256.',
       '- An independent integer transcription preserves nonnegative reserve counts summing to n for n=0..10000. This does not test native overflow or prove the policy optimal.',
       '- The full Level08 Python snippet, with only stdlib names supplied, emits a target-detector proposal from five duplicate other-detector receipts with empty evidence. This is a teaching-snippet counterexample.',
       '- Local paths: 271 occurrences, 115 resolving, 156 missing; 84 point outside the repository. Full inventory is in `_checks.json`.',
       '- Parent notebook/normal-form controls are prior evidence, never counted as fresh tests here. No notebook kernel, production runtime, native build, provider, renderer, external repository or private benchmark was accessed.',
       '', '## Complete file assessments','',
       'All rows below are full, direct body reads, lines 1 through the stated total. Exact hashes and ranges are in the JSON; no bounded artifact substitutes were needed.','']
for r in file_reviews:
    md += ['### '+r['path'],'',
           '`SHA256 '+r['sha256']+'`; lines 1-'+str(r['source_line_count'])+'.','',
           '**'+r['purpose']+'.** '+r['assessment'],'',
           '**Limit:** '+r['limitations'],'']
md += ['## Integration boundary','',
       'Only these31 file_reviews add reading coverage. The dependency spans and selected prior report records supply context, without duplicate full-file credit. Four script-directory .gitkeep markers, all PCIV level pages and both level README files remain outside this sub-scope. Parent owns integration and any eventual corrections.','']
Path(str(P)+'.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps(report['summary'],indent=2))
