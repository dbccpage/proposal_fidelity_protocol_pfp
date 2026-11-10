"""Assemble reviewed findings and exact per-file audit receipts; no source changes."""
import collections
import hashlib
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
PREFIX = ROOT / 'dag/reviews/additional_structured_evidence'


def read_jsonl(suffix):
    return [json.loads(line) for line in pathlib.Path(str(PREFIX)+suffix).read_text('utf-8').splitlines()]


def h(raw):
    return hashlib.sha256(raw).hexdigest()


automated = read_jsonl('_automated.jsonl')
references = read_jsonl('_references.jsonl')
structural = read_jsonl('_structural.jsonl')
counts = json.loads(pathlib.Path(str(PREFIX)+'_counts.json').read_text('utf-8'))
controls = json.loads(pathlib.Path(str(PREFIX)+'_controls.json').read_text('utf-8'))
hash_diagnostics = read_jsonl('_hash_diagnostics.jsonl')
hash_counts = json.loads(pathlib.Path(str(PREFIX)+'_hash_diagnostics_counts.json').read_text('utf-8'))
inv = {row['path']:row for row in json.loads((ROOT/'dag/file_inventory.json').read_text('utf-8'))['files']}

owners = {
 '.gitattributes': 'Read the full checkout policy. Governed source and evidence paths generally request LF, with explicit raw-byte workflow exceptions. Diagnosed every failing reference against raw checkout bytes, CRLF-to-LF bytes and the original inventory Git blob; raw-byte failure is not automatically a content failure.',
 'governance/tools/checker.py': 'Read all model definitions, score/mutation arithmetic, evidence binding, baseline policy and CLI paths. Invoked strict Companion and RunRecord models and check_source for eligible records without grandfathering. The checker authenticates no execution; _run_problems only rejects a source hash if that source happens to be present among inputs, and does not itself verify every run input/report or require a zero exit status. Grades still require evidential judgment.',
 'governance/policy.json': 'Read the entire acceptance policy. L4/D runtime and L2/D test floors are policy gates, not mathematical soundness conditions; baseline and exact empty-marker exceptions are explicitly separate from audited score arithmetic.',
 'pfp/infrastructure/tower_research/reach/canonical.py': 'Read strict duplicate/float/nonfinite handling, canonical ASCII/LF encoding, rational normalization and domain-separated hashing. Audit serializer checked against these actual functions. Canonical bytes and hashes bind syntax only.',
 'pfp/infrastructure/tower_research/reach/ledger.py': 'Read receipt-row construction, filename hash check, per-carrier uniqueness, coverage/depth arithmetic and canonical JSONL output. D counts contiguous admitted lifts and D_native is hard-coded zero; no reach receipt/checker context was executed by this supplemental audit.',
 'pfp/infrastructure/tower_research/reach/schema.py': 'Read closed object, exact integer versus Boolean, digest and canonical-rational admission. Invoked its validate function with transport.CERTIFICATE for every historical generated transport record.',
 'pfp/infrastructure/tower_research/reach/transport.py': 'Read producer/receiver envelope and ledger commitments, closed receiving certificate schema, exact finite injectivity checks, square equality and standing-loss obligations. Generated historical records fail the receiving shape before these semantic obligations; source records are not target-admission receipts.',
 'pfp/infrastructure/tower_evidence/level_engine/v1/outward/bundles.py': 'Read all historical v1 bundle/evidence/loss/certificate builders. Audited loss histograms, producer-specific commitments, fixture digests, and proposed/pending ceilings. External vendor and historical engine imports were not re-executed; the supplied challenge is explicitly not derived from the seed.',
 'pfp/infrastructure/tower_research/level_engine/outward/bundles.py': 'Read all current v2 builders and installed-resource provenance changes. Recomputed field-defined commitments and discriminated a vendor Git commit from installed-package bytes. Generated records still mark transport PROPOSED; no semantic preservation theorem follows from their map names.',
 'ops/operations/use_cases/level_engine/research_engine/canon.py': 'Read no-float sorted JSON encoder/decoder, SHA-256 and Git blob functions. Its exact canonicalization justifies the producer-side hash recomputations; no write function was called.',
 'ops/operations/use_cases/level_engine/research_engine/level.py': 'Read complete fixture loading/mutation, hosted decisions, census probing, expected-outcome and near-miss/kill checks. census_json serializes a dictionary of declared census classes; only derived summary arithmetic was rechecked here, not the underlying witness search or oracle behavior.',
 'ops/operations/use_cases/level_engine/bootstrap.py': 'Read deterministic generation of digest-named bundle/evidence/loss files and index links. This is the owning source for filename-as-SHA-256 checks. Build and any vendor/model work were not invoked.',
 'pfp/infrastructure/adapters/pfp_evidence.py': 'Read compact UTF-8 canonicalization, SHA-256, write-once semantics and checkout/resource discovery. Only the declared v1 byte conventions were reproduced; write_once was never invoked.',
 'pfp/infrastructure/adapters/pfp_derivation.py': 'Read entire durable adapter and both historical v1 and current v2 replay paths. Applied JSON-only receipt/token/cost/reservation equations to every retained v1 run. Database comparison, injected observer replay, prompt regeneration, source imports and actual provider dispatch remain outside this audit.',
 'pfp/infrastructure/adapters/pfp_experiment.py': 'Read per-stage decoding and max-output override, decimal price ceiling and timeout logic. Experiment reservations use ceiling(rate*hold*1e6), so applying the free-route reservation-zero rule to all v1 runs would be wrong; the final audit respects the recorded experiment profile.',
 'ops/adversary/infrastructure/providers/wire.py': 'Read bounded strict provider JSON object admission, duplicate-key rejection, nonfinite rejection, token integer constraints and optional reported cost. Arithmetic over a stored provider-shaped response cannot establish external provider authenticity.',
 'workflows/tasks/certified_challenges/c039_lattice_z2_gauge_theory_gauss_law/tests/test_dual_checkers.py': 'Read all tests, including exact raw-byte manifest size/hash rules, checker agreement and syntactic independence checks. Used only the explicit manifest rule as a representative schema. Mathematical solver/checker tests were not run here; absence of cross-imports alone is not independent evidential validation.',
 'workflows/tasks/certified_challenges/c021_q40_r/tests/test_dual_checkers.py': 'Read all inventory, manifest, gauge/relabel, dual-checker, mutation and hostile-type tests. Its current 44-case assertion supersedes stale 46-case prose; the manifest hash/size convention was reviewed without rerunning mathematical checkers.',
 'pfp/tests/normal_forms/json/receipt_tranche3_advanced_relational_nfs.json': 'Read the complete claimed 25-test PASS receipt. Line 159 has a bare string without a property/value separator, so the artifact is not JSON. Its broad named mathematical claims are not established by the record or by this syntax finding; the named test execution was not rerun.',
}

file_reviews = []
for path, assessment in owners.items():
    raw = (ROOT/path).read_bytes()
    assert h(raw) == inv[path]['sha256'], path
    file_reviews.append({'path':path, 'sha256':h(raw), 'full_source_read':True,
                         'assessment':assessment, 'reviewed_lines':[[1,len(raw.decode('utf-8-sig').splitlines())]],
                         'mathematical_or_runtime_correctness_certified':False})

duplicate_contexts = []
for row in structural:
    if row['status'] != 'duplicate_keys_detected':
        continue
    repeated = []
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                repeated.append({'key':key,'identical_values':result[key] == value})
            result[key] = value
        return result
    json.loads((ROOT/row['path']).read_bytes(),object_pairs_hook=pairs)
    duplicate_contexts.append({'path':row['path'],'sha256':row['sha256'],'repetitions':repeated})

empty_contexts = []
base = 'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery/g03/'
for stem in ['count_preserving_poison','duplicated_pair','fixed_target_reuse','poisoned_collapse_adapter','predicates_not_on_classes']:
    process_path = base+stem+'_process.json'
    process = json.loads((ROOT/process_path).read_bytes())
    stdout_path, stderr_path = base+stem+'_stdout.json', base+stem+'_stderr.txt'
    stdout, stderr = (ROOT/stdout_path).read_bytes(), (ROOT/stderr_path).read_bytes()
    empty_contexts.append({'path':stdout_path, 'sha256':h(stdout), 'process_record':process_path,
        'recorded_returncode':process['returncode'], 'stdout_empty':len(stdout)==0,
        'stdout_hash_matches_record':h(stdout)==process['stdout_sha256'],
        'stderr_hash_matches_record':h(stderr)==process['stderr_sha256'],
        'stderr':stderr.decode('utf-8').strip(),
        'assessment':'Empty captured stdout of a recorded refused control, not a malformed nonempty result object; historical execution not authenticated.'})

def failures(prefix):
    return [r['path'] for r in automated if any(c['rule'].startswith(prefix) and c['status']=='fail' for c in r['checks'])]

def selected_refs(kind, status):
    return [r for r in references if r['kind']==kind and r['status']==status]

bundle_example = 'pfp/infrastructure/tower_evidence/level_engine/v2/bundles/011cfa5b0582b3524031dcb68456e40666a667cd0e0ce3d1be625d4626e6d3ba.json'
findings = [
 {'id':'ASE-F01','severity':'high','finding':'Historical v2 tower content addresses and transport envelopes do not bind the retained bytes.',
  'evidence':{'v2_bundle_filename_mismatches':len(failures('TOWER-2: filename')), 'v2_transport_payload_digest_mismatches':len(failures('TOWER-11')),
              'v1_v2_transport_record_digest_mismatches':len(failures('TOWER-12')), 'example':bundle_example,
              'example_filename_sha256':pathlib.PurePosixPath(bundle_example).name[:64],'example_actual_sha256':h((ROOT/bundle_example).read_bytes()),
              'line_ending_diagnostic':'All 108 filename mismatches persist against LF-normalized bytes and the pinned Git blobs; payload/record computations already use producer canonical serialization.',
              'producer_rules':['pfp/infrastructure/tower_evidence/level_engine/v1/outward/bundles.py:489-493','pfp/infrastructure/tower_research/level_engine/outward/bundles.py:552-556','ops/operations/use_cases/level_engine/bootstrap.py:75-83']},
  'impact':'The digest-named v2 witness bundle and certificate custody chain cannot be used as intact byte evidence at this snapshot.',
  'limitations':['No cause or author is inferred. This is a retained-byte mismatch at the pinned inventory, not a claim that the historical run never occurred.','Loss-ledger commitments and all canonical serialization checks pass; no blanket claim that all tower evidence is corrupted.'],
  'recommendation':'Preserve the historical files; recover and identify the actual original bytes or issue a separately versioned reconstruction receipt before relying on these links.'},
 {'id':'ASE-F02','severity':'medium','finding':'All 216 generated transport certificates fail the current receiving transport schema despite sharing its schema identifier.',
  'evidence':{'count':len(failures('TOWER-17')), 'receiver':'pfp/infrastructure/tower_research/reach/transport.py:77-137',
              'producer':'pfp/infrastructure/tower_research/level_engine/outward/bundles.py:492-556'},
  'impact':'They remain drafts awaiting an adapter and independently grounded target replay. The explicit PROPOSED/PENDING fields are consistent with that limit.',
  'limitations':['Shape rejection is not a counterexample to the underlying mathematical statement.','No target expectation or semantic transport checker was fabricated to obtain admission.']},
 {'id':'ASE-F03','severity':'high','finding':'Seven score companions fail the owning current-byte/evidence checker; ten more cite evidence outside the original inventory.',
  'evidence':{'owning_checker_failures':failures('SCORE-4'), 'artifact_binding_mismatch_paths':sorted({r['target'] for r in selected_refs('contract_source','mismatch')}),
              'outside_inventory_evidence_paths':sorted({r['target'] for r in selected_refs('score_evidence','unresolved_outside_original_inventory')}),
              'all_95_model_and_arithmetic_checks_pass':not failures('SCORE-1') and not failures('SCORE-5')},
  'impact':'A displayed score token can remain arithmetically valid while its source or evidence binding is stale. Current-byte acceptance must check both.',
  'limitations':['No grade deservedness review was substituted for reading the cited evidence.','Outside the original inventory means unresolved in this audit; it is not asserted absent from all historical storage.','All three source-pin and eight distinct score-evidence-pin mismatches persist against LF normalization and pinned Git blobs.']},
 {'id':'ASE-F04','severity':'medium','finding':'Challenge manifests contain stale target hashes/sizes and inconsistent self-summary fields.',
  'evidence':{'manifests_checked':28,'target_references_pass':len(selected_refs('challenge_manifest','pass')),
              'target_references_mismatch':len(selected_refs('challenge_manifest','mismatch')),
              'target_references_outside_inventory':len(selected_refs('challenge_manifest','unresolved_outside_original_inventory')),
              'manifests_with_target_failure':len(failures('MAN-4')), 'count_mismatch_paths':failures('MAN-3'),
              'ordered_lines_manifest_digest_failure':failures('MAN-5'),
              'count_details':['C038 declared_file_count=100 versus 101 entries','C039 declared_file_count=102 versus 103 entries']},
  'impact':'The listed custody cannot be treated as a currently validated judge packet. Several manifests explicitly disclaim being pre-run commitments.',
  'limitations':['CRLF_TO_LF normalization was applied only when explicitly declared; additional diagnostics show all 171 remaining mismatches persist in raw/LF/pinned-Git comparisons.','Unlisted-directory completeness and C011-C060 mathematical outputs were not certified.']},
 {'id':'ASE-F05','severity':'high','finding':'Seven JSON evidence records have duplicate keys with conflicting values.',
  'evidence':{'files':duplicate_contexts,'conflicting_repetitions':sum(not item['identical_values'] for row in duplicate_contexts for item in row['repetitions'])},
  'impact':'Ordinary JSON object loading silently chooses the last value, so these source inventories cannot represent a unique original path-to-digest map under a strict decoder.',
  'limitations':['No historical bytes were repaired.','A source relocation may explain conflicting names, but this audit does not establish the cause.']},
 {'id':'ASE-F06','severity':'medium','finding':'The normal-forms 25-test PASS receipt is not valid JSON; other parse failures include documented hostile or refused controls.',
  'evidence':{'malformed_receipt':'pfp/tests/normal_forms/json/receipt_tranche3_advanced_relational_nfs.json:159',
              'empty_refusal_stdout':empty_contexts,
              'intentional_nonfinite_mutations':['workflows/tasks/certified_challenges/c057_sorting_network_synthesis/judge_packet/hostile_mutations/mut_41_network_contains_nan.json','workflows/tasks/certified_challenges/c057_sorting_network_synthesis/judge_packet/hostile_mutations/mut_42_network_contains_inf.json']},
  'impact':'The normal-forms receipt requires preservation and a distinct corrected/replayed artifact before machine consumption. Intentional negative inputs must not be counted as damaged positive evidence.',
  'limitations':['The C057 checkers were not run on the hostile inputs here.','The claimed 25-test execution was not authenticated or rerun.']},
 {'id':'ASE-F07','severity':'medium','finding':'Most raw governed-run input mismatches are checkout line-ending effects; a smaller set remains different in the pinned Git content.',
  'evidence':{'run_records':len(failures('RUN-3')),'unique_current_mismatch_input_paths':len({r['target'] for r in selected_refs('recorded_run_input','mismatch')}),
              'distinct_line_ending_only_input_paths':2626,'line_ending_cases_also_matching_pinned_Git_blob':2626,
              'persistent_input_digest_mismatches':162,'persistent_input_mismatch_distinct_paths':144,
              'unique_unresolved_input_paths':len({r['target'] for r in selected_refs('recorded_run_input','unresolved_outside_original_inventory')}),
              'report_hashes_matching':len(selected_refs('recorded_run_report','pass'))},
  'impact':'Do not interpret the large raw mismatch count as thousands of content changes. These remain historical receipts; content drift is limited here to the separately enumerated persistent mismatches.',
  'limitations':['A changed input hash is expected after source evolution and does not prove the earlier execution was false.','Referenced paths excluded from the original inventory were not opened.','Raw rule outcomes were preserved and qualified by per-file diagnostic indices; LF diagnostics do not silently change the declared hash convention.']},
]

claims = [
 {'id':'ASE-C01','claim':'Byte custody, numerical consistency, schema acceptance and mathematical validity are separate obligations.',
  'evidence':['governance/tools/checker.py','pfp/infrastructure/tower_research/reach/transport.py','validation:ASE-V01'],
  'dependencies':['Exact original inventory','Declared canonicalization and source-owner conventions'],
  'limitations':['Automated results never mark a data file as a full source review.','Hashes establish byte correspondence under their declared input convention, not a source event, theorem or model capability.']},
 {'id':'ASE-C02','claim':'All 95 retained score records satisfy their strict model and weakest-gate/token/floor/mutation-ratio arithmetic, while custody checks can still fail.',
  'evidence':['governance/tools/checker.py:306-365','ASE-F03','dag/reviews/additional_structured_evidence_automated.jsonl'],
  'dependencies':['Order E<D<C<B<A<A+','Mutation denominator killed+survived+inconclusive+unrun, excluding demonstrably equivalent and invalid mutants','Policy category floors'],
  'limitations':['The arithmetically weakest declared gate may itself be unjustified.','Historical scores and exemptions were not promoted into fresh source evidence.']},
 {'id':'ASE-C03','claim':'The 25 retained v1 derivation/experiment runs and their 80 provider receipts pass the audited JSON arithmetic and internal binding checks.',
  'evidence':['pfp/infrastructure/adapters/pfp_derivation.py','pfp/infrastructure/adapters/pfp_experiment.py','validation:ASE-V04'],
  'dependencies':['total_tokens=prompt_tokens+completion_tokens','cost_microusd=ceil(10^6*recorded_cost_usd)','spent=sum(settled actuals)+sum(unresolved reservations)','Per-stage output cap and recorded price ceiling'],
  'limitations':['No database/private storage access, provider call or independent billing confirmation.','No prompt-lineage regeneration or observer/proposal mathematical check.','All terminal analytical_status values remain UNVERIFIED.']},
 {'id':'ASE-C04','claim':'Tower loss histograms, producer commitments, declared census summaries and embedded fixture hashes can be checked without granting target authority.',
  'evidence':['pfp/infrastructure/tower_evidence/level_engine/v1/outward/bundles.py','pfp/infrastructure/tower_research/level_engine/outward/bundles.py','validation:ASE-V03'],
  'dependencies':['The producer classifies each loss field and each clause','Canonical ASCII/LF JSON','Explicit PROPOSED and PENDING ceilings'],
  'limitations':['A histogram does not validate the correctness of its semantic classifications.','Target injectivity, compatibility, goal/move correspondence and native proof claims were not established.','Broken envelope/content-address links are separately reported in ASE-F01.']},
 {'id':'ASE-C05','claim':'All 17,503 original JSON/JSONL/YAML files were structurally parsed, but only 1,527 structured files received the selected schema-specific checks.',
  'evidence':['dag/reviews/additional_structured_evidence_structural.jsonl','dag/reviews/additional_structured_evidence_unsupported.jsonl'],
  'dependencies':['Pinned 32,261-file inventory at 8050c66900899771766f33e8f5fdd200b7dd9120'],
  'limitations':['The 15,976 remaining structured files still require schema/semantic review.','Many additionally hashed sources have only referenced-byte evidence.','This supplement does not complete the every-file substantive audit.']},
]

rules = {
 'STRUCT':'Parse every selected file and record duplicate keys; syntax only. YAML merges are allowed and explicit duplicate keys reported. JSON nonfinite/overflow numbers rejected. No data schema or semantic assertions follow.',
 'REF':'Compare declared SHA-256 and optional size with current original-inventory bytes; declared CRLF_TO_LF is honored. No outside-inventory path is opened. Every reference and actual digest is in the references ledger.',
 'MAN':'For 28 original judge manifests, normalize list/dict entries, resolve the manifest-wide declared base, count entries, compare bytes/sizes and recompute the explicitly defined C021 ordered-lines digest. No mathematical case-checker evaluation or full-directory completeness.',
 'SCORE':'Invoke actual strict Pydantic models and owning score arithmetic, mutation ratio and current-byte checker without baseline grandfathering. Out-of-inventory evidence blocks only the corresponding custody check, not independent arithmetic.',
 'RUN':'Invoke strict RunRecord model, compare recorded timestamps and every listed in-inventory input/report digest. Exit status is recorded, not silently required to be success. Executions are historical assertions.',
 'TOWER':'Apply producer-defined no-float canonical bytes, content filenames, loss commitments/counts, declared census/status arithmetic, bundle-index links, fixture hashes, payload/record envelopes and provenance separation. Separately invoke the receiving closed schema; no receiving semantic replay.',
 'DERIV':'Reconcile all retained v1 JSON terminal/snapshot/receipt records, exact token sums, decimal cost ceiling, prompt/request/raw hashes, configured model, settled attempts and sequence uniqueness. Read the experiment adapter before handling its reservation rules. No database/observer/runtime/provider execution.',
}

validation = [
 {'id':'ASE-V01','command':'.venv/Scripts/python.exe -B -X utf8 dag/reviews/additional_structured_evidence_audit.py','exit_status':0,
  'counts':counts,'inventory_hash_drift_in_structured_files':sum(not r['inventory_sha256_matches'] for r in structural),
  'limit':'A zero script exit means the audit completed and recorded failures, not that all evidence passed.'},
 {'id':'ASE-V02','command':'.venv/Scripts/python.exe -B -X utf8 dag/reviews/additional_structured_evidence_controls.py','exit_status':0,
  'controls_passed':controls['passed'],'controls_total':controls['total'],'artifact':'dag/reviews/additional_structured_evidence_controls.json',
  'limit':'Fifteen positive/negative controls exercise selected parsers, owner score functions and digest functions; not exhaustive verification of this helper.'},
 {'id':'ASE-V03','families':{'loss_ledgers':204,'challenge_evidence':216,'witness_bundles':216,'transport_certificates':216,'checker_input_bundles':216,'bundle_indexes':2},
  'all_schema_specific_rule_failures':dict(collections.Counter(c['rule'] for r in automated for c in r['checks'] if c['status']=='fail' and not c['rule'].startswith('REF-')))},
 {'id':'ASE-V04','v1_runs':25,'provider_receipts':80,'failed_derivation_rules':len(failures('DERIV-')),
  'limit':'JSON-only readback. Original v1 provenance and injected proposal semantics were not replayed.'},
 {'id':'ASE-V05','command':'.venv/Scripts/python.exe -B -X utf8 dag/reviews/additional_structured_evidence_hash_diagnostics.py','exit_status':0,
  'diagnostics':hash_counts,'ledger':'dag/reviews/additional_structured_evidence_hash_diagnostics.jsonl'},
]

ledger_paths = ['_automated.jsonl','_references.jsonl','_structural.jsonl','_unsupported.jsonl','_counts.json','_controls.json','_hash_diagnostics.jsonl','_hash_diagnostics_counts.json']
ledgers = []
for suffix in ledger_paths:
    p = pathlib.Path(str(PREFIX)+suffix); raw = p.read_bytes()
    ledgers.append({'path':p.relative_to(ROOT).as_posix(),'sha256':h(raw),'size_bytes':len(raw)})
report = {'schema':'pfp.additional-structured-evidence-review.v1','source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120',
          'generated_at_utc':datetime.now(timezone.utc).isoformat(),
          'status':'bounded_structured_evidence_audit_complete_substantive_corpus_audit_incomplete',
          'scope_coverage':{**counts,'full_source_reads':len(file_reviews),'all_files_substantively_reviewed':False},
          'prohibitions_observed':['No source or historical evidence edits','No paid/provider calls','No benchmark seed read','No private key/database/storage access','No imported top-level pilots read','All outputs have additional_structured_evidence prefix'],
          'claims':claims,'findings':findings,'validation':validation,'rules':rules,'file_reviews':file_reviews,
          'automated_reviews':[r for r in automated if 'schema_evidence' in r['evidence_ceiling']],
          'remaining_unsupported_files':{'count':counts['unsupported_structured_files'],'ledger':'dag/reviews/additional_structured_evidence_unsupported.jsonl',
              'interpretation':'No schema-specific arithmetic/validation rule was executed; all semantic claims remain pending even where syntax or referenced hashes passed.'},
          'ledgers':ledgers,
          'limits':['Automated ledger entries do not count as full_source_read or complete semantic review.','Referenced source hashes were checked without reading their bodies as source.','No native theorem prover, scientific checker, source blind experiment or external authenticity service was invoked.','Current versus historical drift is reported without editing or silently repinning history.']}
PREFIX.with_suffix('.json').write_text(json.dumps(report,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')

md = '''# Additional structured evidence audit

Snapshot: `8050c66900899771766f33e8f5fdd200b7dd9120`. Original scope: 32,261 files. This is a bounded evidence audit, not a completed mathematical or every-file review.

All 17,503 JSON/JSONL/YAML files received strict parsing and duplicate-key checks. The schema-grounded pass covered **1,527 files**: 28 judge manifests, 95 score companions, 19 governed run records, 1,070 tower records, and the JSON files supporting 25 derivation/experiment runs. A further 9,973 files were checked only as referenced bytes. The 15,976 structured files without a schema-specific check remain explicitly pending. Nineteen named source/evidence owners were read completely; only these have full-source reading receipts.

## Results that change the evidence assessment

* **Broken tower custody:** all 108 v2 witness-bundle filenames disagree with their actual SHA-256, including LF-normalized bytes and pinned Git blobs. All 108 v2 transport payload digests and all 216 v1/v2 transport record digests fail the producer-defined canonical recomputation, independently of checkout line endings. Loss commitments, canonical byte profiles, declared census arithmetic and fixture-input digests pass. The failures do not justify discarding or rewriting historical evidence.
* **Transport remains unadmitted:** all 216 generated transport records fail the current receiving closed schema despite using the same schema identifier. Their explicit `PROPOSED`, `PENDING` and `TARGET_REPLAY_REQUIRED` fields are consistent with this remaining work. No finite map name or digest establishes target preservation.
* **Scores need fresh bindings:** all 95 scores pass strict model and arithmetic checks, but seven companions fail the owning source/evidence checker, and ten cite two log paths outside the original inventory. Three current Rust source digests differ from their score bindings. A valid score token is not a current validation receipt.
* **Judge manifests have stale entries:** 2,840 listed targets pass their declared byte convention, 171 fail a hash/size comparison, and 40 lie outside the original inventory. C038 and C039 each have an outdated `declared_file_count`; the C021 ordered-lines manifest digest does not recompute. Explicit `CRLF_TO_LF` declarations were honored. Regenerated inventories were not treated as pre-run commitments.
* **Conflicting duplicate keys:** seven evidence JSON files contain 27 repeated keys with different values. They are concentrated in OPERADS source inventories and Paper 011 capture records. A last-value-wins parser hides the ambiguity.
* **One positive receipt is malformed:** the normal-forms 25-test PASS receipt has a bare string at line 159 where a property/value pair is required. Five other parse failures are empty stdout from recorded refused controls, and two are deliberate NaN/Infinity hostile fixtures; these were kept distinct.
* **Checkout conversion explains most run-input differences:** 2,626 input paths fail the raw checkout hash but match both LF-normalized bytes and their pinned Git blobs. A separate 162 target/digest comparisons over 144 input paths still disagree in raw, LF and pinned Git bytes. All outside-inventory paths remain unresolved. The receipts' historical execution claims were neither rerun nor declared false.

Every mismatching reference received a supplementary line-ending/Git diagnostic: 3,192 distinct target/digest/convention/size comparisons in total, with 2,626 explained by checkout conversion and 566 persistent content mismatches. The manifest, score source/evidence and tower findings above all survive that distinction. Raw-byte rule failures remain in the original ledgers, with per-file diagnostic links; they must not be counted as content failures without those qualifications.

## Positive bounded result

All 25 retained v1 derivation/experiment runs and 80 provider receipts pass the audited JSON arithmetic and internal bindings: nonnegative exact token sums, decimal ceiling to microusd, per-stage output caps, recorded price reservations, settled-attempt reconciliation, terminal totals and unique generation IDs. Every terminal still says `analytical_status: UNVERIFIED`. Database custody, provider authenticity, prompt regeneration, observer execution and mathematical proposal correctness remain untested.

The 204 loss ledgers are histograms of *declared* classifications. A correct histogram does not establish that a semantic property was preserved. Similarly, a score's minimum gate and mutation ratio concern the declared grades and selected mutants. These checks cannot bridge task encoding, checker adequacy, or physical interpretation.

## Reproduction and records

Run `additional_structured_evidence_audit.py` with the repository virtual environment and `-B -X utf8`; its zero exit means the audit completed, while failures remain in the ledger. Then run `additional_structured_evidence_hash_diagnostics.py` to compare all mismatches with LF-normalized bytes and original pinned Git blobs. Run `additional_structured_evidence_controls.py` for 15 positive/negative controls (15 passed). `additional_structured_evidence_report.py` assembles this report from the completed ledgers.

* `additional_structured_evidence.json`: claims, findings, source reading receipts, schema-specific per-file checks and precise limits.
* `additional_structured_evidence_automated.jsonl`: all 11,500 bounded per-file records, including referenced-byte-only checks.
* `additional_structured_evidence_references.jsonl`: every attempted reference resolution, expected/actual hash and declared normalization.
* `additional_structured_evidence_structural.jsonl`: all 17,503 parse results, never promoted to semantic review.
* `additional_structured_evidence_unsupported.jsonl`: every structured file still lacking a schema-specific review.
* `additional_structured_evidence_hash_diagnostics.jsonl`: all failing bindings compared with raw/LF/pinned-Git bytes, linked by index from each affected automated record.

No historical file, source implementation or imported top-level pilot was modified. No model calls, benchmark seed reads, private storage or database reads occurred. Counts and hashes of these ledger artifacts appear in the JSON report.
'''
PREFIX.with_suffix('.md').write_text(md,encoding='utf-8',newline='\n')
print(json.dumps({'source_reads':len(file_reviews),'automated_schema_reviews':len(report['automated_reviews']),'findings':len(findings),'claims':len(claims)}))
