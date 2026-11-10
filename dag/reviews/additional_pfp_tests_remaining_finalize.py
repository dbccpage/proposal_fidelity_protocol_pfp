"""Finalize only this explicitly frozen audit slice; never execute original sources."""
import sys,json,collections
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a

def pin(p):
 return {'path':str(p.relative_to(a.ROOT)).replace('\\','/'),'sha256':a.sha(p),'size_bytes':p.stat().st_size}

def main():
 r=a.read('.json');assert r['scope']['full_source_reads']==415 and r['scope']['bounded_data_dispositions']==25
 assert not r['remaining_unsupported_files'] and r['scope']['partial_source_reads']==0
 artifacts={}
 for c in r['controls']:
  assert 'rule' in c and 'status' in c
  for kind in ('receipt','helper'):
   p=c.get(kind)
   if isinstance(p,dict) and p.get('path') and p.get('sha256'):
    f=a.ROOT/p['path'];assert a.sha(f)==p['sha256'];artifacts[p['path']]=pin(f)
 for f in a.file('_notes.json').parent.glob(a.PREFIX.name+'_probe*'):
  if f.is_file() and f.suffix in ('.py','.json'):artifacts[str(f.relative_to(a.ROOT)).replace('\\','/')]=pin(f)
 manifest={'review_id':a.PREFIX.name,'rule':'control_artifact_custody_only','status':'all_named_control_artifact_hashes_reconciled','control_count':len(r['controls']),'control_ids':[c['id'] for c in r['controls']],'artifacts':sorted(artifacts.values(),key=lambda x:x['path']),'limits':['This manifest binds persisted helpers/receipts; it does not rerun controls, original tests, native binaries or providers.','Controls include source/predicate observations and bounded independent or AST-extracted experiments; 81 controls does not mean 81 production tests passed.']}
 a.write('_control_artifact_manifest.json',manifest)
 n=a.read('_notes.json');n['analysis_complete']=True
 n['audit_methods']={
  'full_source_read':'Every one of the 415 non-JSON original bodies was displayed and substantively reviewed. Each receipt pins original SHA256, complete line coverage and body-specific assessment; empty files have explicit empty-body receipts.',
  'bounded_data_disposition':'25 JSON artifacts were parsed under explicit schema-specific checks. Those checks and retained status declarations are not full human source reads, native replay or mathematical certification.',
  'controls':'Read-vetted AST extraction, standard-library exact finite calculations, synthetic files confined to this audit prefix, source metadata/delta checks and retained receipt reconciliation. No broad original test suite was run.',
  'runtime':'Available workspace .venv Python 3.14.2. Runtime-dependent results are bounded to that interpreter; no claim to reproduce a pinned historical Python environment.',
  'source_custody':'438 of 440 current paths match original inventory hashes; two authorized migration consumers have separately pinned original and current bodies. Original coverage remains attributed to the original hashes.',
  'historical_context':'Historical comments, receipts, sealed/archive labels and instructions are evidence to assess, not authorization or governance. Foreign/private benchmark material was not accessed.'}
 n['synthesis']={
  'overall':'This slice contains substantial reusable finite verification and workflow-custody mechanisms, alongside numerous test-local stand-ins, label checks and mathematical overclaims. Reading every test body does not establish that the suite collects or passes, that its native owners execute correctly, or that the broader research claims follow.',
  'substantive_mechanisms':[
   'Exact finite ground-step/join registration; exhaustive small CHSH/parity/GF2 examples; independently checkable finite linear-algebra witnesses and negative controls.',
   'Explicit representation sufficiency and observation-fiber impossibility examples, conditional on their admitted carriers, observers and reconstruction maps.',
   'Primal residual, dual annihilation, infinity-norm and zero-gap obligations can form a finite L1 certificate when all are actually checked; lexical labels and authority fields supply no semantic extraction theorem.',
   'Raw-byte custody before decoding, source/obligation/attempt bindings, unknown dispatch accounting without automatic retry, and separate process-crash versus power-loss claims.',
   'Current/historical custody, declared/unverified/judged results, closed fixtures and missing-owner refusals are distinct states in several meaningful regression suites.'
  ],
  'main_gaps':[
   'Several test-local mathematical helpers accept counterexamples or compute the wrong invariant; the findings explicitly avoid transferring those failures to an unexecuted production owner.',
   'Some negatives fail multiple obligations at once, some tests only inspect labels or comments, and some compare an implementation to itself. Such assertions cannot isolate the named rule.',
   'Finite graph cycle ranks, selected scalar identities and constants are repeatedly presented with broader topology, physics or universal theorem labels without the required structures or assumptions.',
   'Receipt emitters can write PASS without consulting test outcomes; hashes bind bytes but do not authenticate who ran a checker or establish the truth of its payload.',
   'Legacy path, collection/import, serialization-profile and fixture-contract defects limit the evidence available from a broad pass claim. No such aggregate pass is claimed here.'
  ],
  'workflow_contribution':'PFP/EIS/PCIV-style workflows gain useful conditional mechanisms for explicit obligations, residual/refusal states, repair witnesses, binding and retained uncertainty. These tests do not derive their carriers, authorize observers, authenticate external source truth, or prove primitive/genesis/physical claims from labels.',
  'scope_completion':'All 440 frozen paths have explicit dispositions; no pending body remains in this slice. Repository-wide audit remains incomplete.'}
 n['final_artifact_bindings']=[pin(a.SCOPE),pin(a.file('_read_ledger.json')),pin(a.file('_data_reviews.json')),pin(a.file('_index.json')),pin(a.file('_authorized_revisions.json')),pin(a.file('_control_artifact_manifest.json')),pin(a.file('_audit.py')),pin(a.file('_finalize.py'))]
 n['limits']+= [x for x in [
  'Full source reading establishes review coverage, not test execution, collection success, mutation completeness or production correctness.',
  'Named findings distinguish observed test-local counterexamples, logical adequacy gaps, historical/source wording and separately attributed owner evidence.',
  'Fixture-only encryption, declared LIVE labels, mock liability and loopback examples are not production cryptography, real vendor responses or vendor-enforced billing caps.',
  'No claims of broad PFP, EIS, PCIV, operadic, physical, philosophical or primitive/genesis completeness follow from this slice.'
 ] if x not in n['limits']]
 a.write('_notes.json',n);a.report();r=a.read('.json')
 assert r['status']=='complete' and len(r['findings'])==126 and len(r['claims'])==61 and len(r['controls'])==81
 lines=['# PFP remaining tests and support audit','',
  '**This 440-path slice is complete: 415 full source reads (99,337 original lines), 25 bounded JSON dispositions, and no pending paths. The repository-wide audit remains incomplete.**','',
  'The frozen slice contains 4,248,364 original bytes and 102,095 original logical lines. Every full read has an exact original path, SHA256, complete line ranges and substantive assessment in the JSON report and durable read ledger. The remaining 2,758 lines belong to parsed JSON artifacts and receive no full-body reading credit.','',
  f'Canonical report SHA256: `{a.sha(a.file(".json"))}`. Scope SHA256: `{a.sha(a.SCOPE)}`. Control-artifact manifest SHA256: `{a.sha(a.file("_control_artifact_manifest.json"))}`.','',
  'The report records 126 findings (87 medium, 39 low), 61 bounded claims and 81 controls. These counts are an audit inventory, not an aggregate test-pass count. No broad suite, native/Cargo build, retained executable, provider call or private benchmark access was performed. Bounded helpers used the workspace Python 3.14.2 runtime.','',
  '## What the bodies support','',
  'There is substantive finite mathematics here: exact ground-step and join registration, small exhaustive CHSH/parity and GF2 controls, conditional finite L1 certificates, independent graph traversal, and representation-sufficiency examples. Their assumptions matter. For an L1 certificate, primal residual, dual annihilation, infinity-norm and equality of primal/dual objectives are separate obligations; source hashes and authority labels do not supply the semantic extraction from prose to that finite problem.','',
  'The strongest workflow tests keep uncertainty visible: raw bytes precede decoding; preflight refusal differs from a possibly billed dispatch; unknown outcomes prohibit automatic retry; missing artifacts cannot become complete; and historical/current or declared/judged evidence stays distinct. Execution-trace tests explicitly show that a wholly rewritten chain can verify against its own digest. External anchoring, actual provider provenance, production encryption and power-loss durability remain separate obligations.','',
  'These are useful components for PFP, EIS and PCIV workflows. They do not derive the input carrier, prove that an observer is authoritative, validate arbitrary repair scores or dual witnesses, or establish broad physical, operadic or primitive/genesis conclusions.','',
  '## Findings that change the interpretation of a green result','',
  '| Finding | Concrete boundary |','|---|---|',
  '| F031–F032 | Some receipt writers emit unconditional PASS; the PJNF receipt also replaces a valid common-key premise with the insufficient claim that each projection contains some key. |',
  '| F050–F051 | Read-vetted local sketch controls expose a Count-Min seed-reset merge and a Cuckoo insertion that loses an earlier admitted key. These are test-local implementations. |',
  '| F055, F066 | An all-negative triangle already meets the stated stoquastic target; a local Bareiss helper loses swap sign and fails on a zero singular matrix. |',
  '| F095 | Supplied dual-norm negatives also violate other obligations. An independent exact example isolates why the norm bound is necessary. |',
  '| F104 | Graph cycle counts 10, 15 and 7 are not first Betti numbers of the stated filled K6/K7/octahedral complexes; the latter are zero. |',
  '| F106 | The SAT negative demands rejection of mask 2 even though it satisfies all displayed clauses. |',
  '| F109, F111 | Tests miss an already-reviewed false-inequality owner defect; the retired checker can throw on valid JSON term-reference strings despite its total-refusal claim. |',
  '| F120, F123–F126 | Broad coverage claims exceed finite assertions; nine mutation checks accept comment-only synthetic Rust, and documentation guards admit basename/clause/path-tail counterexamples. |','',
  'The full finding ledger below and JSON distinguish direct counterexamples, source wording, missing discriminating controls and production-owner findings inherited from a separately pinned report. A defect in a local substitute is not automatically a defect in the native owner.','',
  '## Custody and validation','',
  'All original source bodies and historical artifacts remain untouched by this lane. Current hashes match the original inventory for 438 paths. The two authorized migration consumers—`test_consistency_teaching.py` and `types/test_taxonomy_task_families_yaml.py`—retain recovered original bytes plus separately reviewed current bodies/deltas. Coverage uses their original hashes. The parent-owned taxonomy run was 2 pass / 1 fail with the same baseline ordering failure; it is attributed evidence, not a run performed here.','',
  'The absent `education/documentation/014_normal_forms` paths were absent from the original inventory and are outside the authorized 84-file move. They are pre-existing stale cross-repository references, not migration regressions. The retraction benchmark legacy path is likewise distinguished by exact path metadata. No moved pilot body was imported or repaired.','',
  'Final checks reconcile all 440 current bindings, recovered original blobs, complete read ranges, unique IDs, source evidence ranges, rule/status fields and named helper/receipt hashes. Immutable checkpoint snapshots use `.json.snapshot` so they are not re-imported as separate DAG reports. Full reads, bounded parsed data and narrow external dependency consultations remain separate.','',
  '## Complete finding ledger','',
  '| ID | Severity | Finding |','|---|---|---|']
 for f in r['findings']:lines.append('| '+f['id']+' | '+f['severity']+' | '+f['statement'].replace('|','\\|').replace('\n',' ')+' |')
 lines+=['','## Claim ledger','','Each claim is conditional on the exact evidence and limits in the JSON report.','', '| ID | Statement |','|---|---|']
 for c in r['claims']:lines.append('| '+c['id']+' | '+c['statement'].replace('|','\\|').replace('\n',' ')+' |')
 lines+=['','## Bounded JSON dispositions','','These 25 parsed artifacts receive no full-source-reading credit. Their exact hashes, checks, observations and limits are in `automated_reviews`.','', '| Path | Assessment |','|---|---|']
 for d in r['automated_reviews']:lines.append('| `'+d['path']+'` | '+d['assessment'].replace('|','\\|').replace('\n',' ')+' |')
 lines+=['','## Source read index','','Every entry below is a complete original body read. Full source hashes and individual chunk assessments are in `file_reviews`; no parse-only transfer is used.','', '| Original path | Lines | Original SHA256 |','|---|---:|---|']
 for f in r['file_reviews']:lines.append('| `'+f['path']+'` | '+str(f['line_count'])+' | `'+f['sha256']+'` |')
 lines+=['','## Limits','','No aggregate suite pass, native equivalence, authenticated historical run or general theorem is inferred. The controls are bounded to their recorded synthetic inputs and available interpreter. This report closes only the frozen 440-path slice.','']
 a.file('.md').write_text('\n'.join(lines),encoding='utf8')
 print(json.dumps({'report':pin(a.file('.json')),'markdown':pin(a.file('.md')),'control_manifest':pin(a.file('_control_artifact_manifest.json')),'source_reads':415,'bounded_json':25,'findings':126,'claims':61,'controls':81}))

if __name__=='__main__':main()
