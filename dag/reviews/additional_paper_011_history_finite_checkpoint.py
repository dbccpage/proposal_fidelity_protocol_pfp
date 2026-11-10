"""Persist completed finite-history reads; unreviewed populations remain pending."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; REV=ROOT/'dag/reviews'
PREFIX='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery/'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
scope=read(REV/'additional_paper_011_history_finite_receipts_scope.json'); frozen={x['path']:x for x in scope['files']}
target=REV/'additional_paper_011_history_finite_receipts.json'
report=read(target) if target.exists() else {'source_commit':scope['source_commit'],'scope_manifest':'dag/reviews/additional_paper_011_history_finite_receipts_scope.json','file_reviews':[],'claims':[],'findings':[]}
rows={x['path']:x for x in report['file_reviews']}
assessments={
 'g03/README.md':'Complete G03 account read. Explicitly distinguishes operator-declared prefix/anchor adapter, historical model experiment, finite sealed/native catalog and preserved failed replay attempts. Cost-one repairs using already-present unary forms explain why the fresh two-item predicate is false; the result is adapter-relative, not G4 generally. Counts/timings and source/binary custody are historical claims awaiting bound-data reconciliation, not freshly rerun catalogs.',
 'g03/adapter_design.md':'Complete adapter declaration read. Endpoint singleton forms, binary-coded anchor requirements and untouched genesis prefix distinguish canonical interiors while their observation profiles collapse. Existing forms change minimum response costs, so the supplied construction cannot stand for a bare carrier. Weak/some and strong/all class predicates are precisely stated over a fresh-form response. Complete pairs, relabeling, reversal and count-preserving correspondence poison are useful finite obligations; no general theorem or original model run established.',
 'g04/README.md':'Complete G04 entry point read. Supplied rectangle, original endpoint collision and new universal-stake poison are separated from missing historical length-five samples/operator stakes/model arms. Fixed seven-stake invariance is not universal stake invariance. Closed second attempt and failed first attempt are distinct receipts, to be checked separately.',
 'g04/claim_ledger.md':'Complete finite claim ledger read.18798 histories,131586 row/stake checks,16331 trace classes and81610 common mappings are claimed scoped census counts. Nontrivial renaming supplement and fresh fixed-stake counterexample do not replace missing original held-outs. Common-prefix bijections are mathematically stronger than unrelated pointwise isomorphisms. No model score, optional Lean proof or fresh upstream binary reproduction inferred.',
 'g04/full_rectangle_v1/diagnostic_scope.md':'Complete first-attempt failure account read. Relative/absolute receipt-path failure occurs after mathematical comparisons; the record explicitly refuses closed-run status. A later successful run cannot retroactively make this physical process successful.',
 'g04/scope.md':'Complete G04 finite boundary/source-custody account read. Exact full history partitions, one common mapping across all prefixes and transported stakes are meaningful invariance obligations. Original fixed alphabet makes nontrivial token-renaming claim vacuous; supplemental renaming is separately labeled. Seven-stake X3c success is explained by initial demands and permutation-invariant stakes; the fresh {0,2} stake supplies absent/3 counterexample with absent/absent after proper transport. Held-out/operator and model/estate obligations remain open. AST/body and raw-source assertions require current hash checks.',
 'g07/README.md':'Complete G07 account read. Declares finite P1 depth15/pre-expansion3000 guard and deterministic P2 depth60, complete held-out/renaming populations and separate quiet-state checks. Expanded tie counts, offered-target widths and undefined quiet widths must not be conflated. Maximum observed width11 only motivates an OPEN fitted conjecture. Source82-file715794-byte census and native timing/build claims are historical receipts, not a new provider run or current source/binary attestation.',
 'g03/pinned_sources/research/g1_local_class/STATUS.md':'Complete historical local-class status read. Claimed exclusion requires fixed radius, locality factorization and a chain-independent finite alphabet; pigeonhole threshold is class-relative and does not discharge OB1. Valued identity-grade and recurring fresh marks are outside that class. Original455-pair check is explicitly withdrawn because it failed to pass the chain target to the engine. This copied status cites external theorems, not a newly verified proof.',
 'g03/pinned_sources/code/derivation/generator.py':'Complete deterministic15-round chain generator read. Views expose tags/incidence, depth2 neighbors or declared mark values; demands are equal-view pairs. Per-pair repair mints observables until current pairs separate, while valued marks make all elements distinct immediately. Five-branch classification is finite and follows implemented predicates; no object-language endogenous generator follows. Fresh small controls reproduce all15 bare-pair identities, valued separation, five classifications and four named checks. No Lean compilation inferred from the lean_agreement function name.',
 'g07/pinned_python/research/alpha_engine/evaluate.py':'Complete evaluation adapter read. Enumerates bounded minima, imposes the fixed target, computes ephemeral canonical child keys and retains every generated class/member, without persisting events to the declared base. fresh_retained_keys reruns enumeration rather than trusts a stored result. Immutability is conditional on trusted imported Regime/evaluator behavior; result schema alone is not a minimum/partition certificate. History comparison includes replay consistency, not generic mutable-object detection.',
 'g07/pinned_python/research/alpha_engine/harness.py':'Complete proposal/evaluation/license payload and refusal helper source read. Separates offers, evaluations and external authorization; rejects index selectors, grade-as-license, automatic unique response, leftover-as-demand and seventh constructors. RetainedClass only checks inhabitance/duplicate members; EvalResult checks some shape/order conditions but not exact raw/retained partition, nonnegative cost or semantic minimum. Node and License do not certify their advertised history/subset relation. Constructor countercontrols demonstrate these gaps without asserting a later authorization bypass.',
 'g07/pinned_python/research/unboundedness/unboundedness.py':'Complete deterministic driver and finite checks read. Controlled fresh supply and least quotient representative define an external policy; finite visited-key distinctness is not unboundedness. Nondecreasing data/requirement counts alone do not exclude cycles. Closed-system helper uses the same termination_depth field for quietness, missing response and100-step exhaustion, with no completion discriminator. A selected-AST missing-response control returns termination_depth0 despite one remaining collapsed pair. Whole module path mutation/main were not executed.',
}
assessments.update({
 'g03_package_v1/genesis_g03_pack.py':'Complete archived first packer read and complete diff against current packer inspected. It hashes every declared tar member and verifies decompression identity but excludes representation files by basename at every depth, with platform sorting and no packer/order commitment. Current code fixes these three historical gaps and adds explicit tests. Archived module-relative paths are historical placement assumptions; this copied file was not run as a CLI. Unpack verifies before a second archive read and refuses different preexisting bytes; no concurrent-mutation guarantee follows from a precheck alone.',
 'g03_package_v1/test_paper011_genesis_g03.py':'Complete archived G03 test suite read and complete current-source diff inspected. Tests audit exact cases/arguments, full key witnesses, selected full row comparisons, source/native member inventories, typed mutation reasons, restoration and explicit experiment ceilings. They consume retained sources/receipts and absolute dependency paths rather than freshly execute all native oracles. Current edition adds package-order/exclusion tests absent here. No historical pytest output is promoted to a fresh current pass; relocated archived test cannot use its original module-relative root unchanged.',
 'g03/frozen_failed_replays/key_bridge_1.py':'Complete frozen failed receiver read, plus full diff against current receiver. It reconstructs states from serialized keys, checks explicit data/form bijections and transports complete candidate rows, avoiding unsupported equality of distinct canonical-label conventions. Fresh witnesses are searched/written here; this version reruns replay.controls and binds fewer input files than the later retained-control closure. It records exceptions as FAILED/UNKNOWN. It is preserved failed-run evidence, not a completed receipt or a portable executable at this archived path. No close/native function invoked.',
})
for name,assessment in assessments.items():
    p=PREFIX+name;assert sha(ROOT/p)==frozen[p]['sha256']
    rows[p]={'path':p,'sha256':sha(ROOT/p),'full_source_read':True,'reviewed_lines':[[1,len((ROOT/p).read_text(encoding='utf-8-sig').splitlines())]],'assessment':assessment}
handoff=read(REV/'additional_paper_011_native_history_transfer_candidates.json')
transferred=0
for x in handoff:
    if not x['full_read_matches']:continue
    p=x['target_path'];source=x['full_read_matches'][0]
    assert p in frozen and sha(ROOT/p)==sha(ROOT/source['path'])==frozen[p]['sha256']==x['sha256']
    assert source['reviewed_lines']==[[1,len((ROOT/p).read_text(encoding='utf-8-sig').splitlines())]]
    report_source=read(ROOT/source['report']); source_row=next(r for r in report_source['file_reviews'] if r['path']==source['path'])
    assert source_row['full_source_read'] is True and source_row['sha256']==x['sha256']
    rows[p]={'path':p,'sha256':x['sha256'],'full_source_read':True,'reviewed_lines':source['reviewed_lines'],
             'assessment':source['assessment']+' Explicit hash-equal team full-body transfer with G07 caller-context review: the copied evaluator/driver use Bounds(2,2), canonical grouping and controlled g/w token generation. Historical source-manifest/build claims remain separate and unvalidated by this transfer; arbitrary state/renaming inputs still require the original assumptions.',
             'reading_transfer':{'report':source['report'].replace('\\','/'),'path':source['path'],'sha256':x['sha256'],'same_bytes_verified':True,'context_sources':[PREFIX+'g07/README.md',PREFIX+'g07/pinned_python/research/alpha_engine/evaluate.py',PREFIX+'g07/pinned_python/research/unboundedness/unboundedness.py']}}
    transferred+=1
def finding(i,statement,names,action):return {'id':i,'statement':statement,'evidence':[PREFIX+n for n in names],'source_evidence':[{'path':PREFIX+n,'sha256':sha(ROOT/(PREFIX+n))} for n in names],'recommended_action':action}
report['findings']=[
 finding('PAPER011-FINITE-EVAL-PAYLOAD-NOT-CERTIFICATE','EvalResult accepts a found result with cost(-1,0), empty raw minima and an inhabited retained class, as well as an unfound result carrying cost/raw minima. Its constructor does not bind the retained partition to actual valid minima.','g07/pinned_python/research/alpha_engine/harness.py'.split(),'Treat these values as untrusted payloads at workflow boundaries and recompute or verify exact problem-bound minima. No later consumer bypass is claimed.'),
 finding('PAPER011-FINITE-TERMINATION-DISPOSITION','verify_closed_system_termination conflates no offered target, missing minimum response and100-step budget exhaustion under termination_depth. With a synthetic unsatisfied target and min_responses=None it returns depth0 while a collapsed pair remains.',['g07/pinned_python/research/unboundedness/unboundedness.py'],'Record separate closed, no_response and budget_exhausted outcomes; do not call an interrupted search a closure certificate. The retained actual baseline is not refuted by this synthetic boundary control.'),
]
data_path=REV/'additional_paper_011_history_finite_data.json'
if data_path.exists():
    data=read(data_path)
    report['automated_reviews']=[{'path':p,'sha256':r['sha256'],'status':'bounded_custody_checked',
        'checks':[{'rule':'frozen_current_sha256','status':'pass'},{'rule':'outer_ZIP_member_comparison','status':z['comparison']}],
        'ledger':'dag/reviews/additional_paper_011_history_finite_data.json','evidence_ceiling':'Current/original byte comparison only; not source semantics or historical execution.'}
        for p,r in frozen.items() for z in data['outer_zip_bindings'] if z['path']==p]
    for p,r in frozen.items():
        if Path(p).suffix!='.txt':continue
        raw=(ROOT/p).read_bytes();assert sha(ROOT/p)==r['sha256']
        assessment='Complete retained text stream read. '
        if not raw:assessment+='Empty bytes convey no mathematical proposition or successful-execution status by themselves.'
        elif p.endswith('first_focused_tests_stdout.txt'):assessment+='First suite preserves one failure: direct equality of sealed/native canonical labels, later handled by explicit isomorphism witnesses. It is not a passing run.'
        elif p.endswith('_stderr.txt'):assessment+='Exact typed refusal text retained; its process/request binding is separate from this body read and no new native refusal was executed.'
        else:assessment+='Historical test/lint/package output declaration; counts, digests and old rewritten paths are not a fresh execution or portable-environment certificate.'
        rows[p]={'path':p,'sha256':r['sha256'],'full_source_read':bool(raw),'reviewed_lines':[[1,len(raw.decode('utf-8-sig').splitlines())]] if raw else [],
                 'review_level':'complete_text_stream' if raw else 'complete_empty_stream_identity','assessment':assessment}
    bounded={
      'g03/evidence.tar.gz':'All69 safe unique regular members streamed and matched against declared size/SHA;1,682,042,010 uncompressed bytes. Nine large current raw files are absent but preserved in this archive. Embedded semantic review remains separate.',
      'g03/archive_manifest.json':'All69 path/size/SHA records checked against streamed archive, summed uncompressed size and current file existence. Current archive order is UTF8 ordinal. This is complete manifest custody, not full member mathematical review.',
      'g03_package_v1/evidence.tar.gz':'All69 safe unique regular members streamed and matched against declared size/SHA; same1,682,042,010 raw payload bytes as current representation. Historical member ordering is not UTF8 ordinal; declared v1 has no order field. No extraction or execution.',
      'g03_package_v1/archive_manifest.json':'All69 path/size/SHA bindings and compressed/raw totals checked. Historical schema lacks later packer-source/order commitments. No current/source authenticity inferred from digest consistency.',
      'g04/full_rectangle_v2/comparison.json':'All three base counts reconciled:18798 rows,131586 row/stake entries,16331 exact trace groups and81610 common mappings. Provided first-count agreements and relation multiplicities match; no exhaustive generation or fresh demand computation inferred.',
    }
    if 'g04_provided_census_checks' in data:
        for version in ['v1','v2']:
            for name in ['source_census.json','native_census_stdout.json']:
                bounded['g04/full_rectangle_'+version+'/'+name]='Complete retained populations parsed. All shared source/native fields agree except irrelevant token-group ordering; exact group-record multisets agree. Every supplied common datum/form bijection was replayed over401689 corresponding prefix states, with partition membership and multiplicity checks. V1/V2 payloads are raw-identical despite different run dispositions. No fresh enumeration or first-count oracle rerun.'
    if 'g07_provided_population_checks' in data:
        for name in ['result.json','native_request.json','native_stdout.json']:
            bounded['g07/run_v1/'+name]='All3617 provided case IDs, request/source histories and result/native cost/state/width/class-size fields reconciled;3530 P1 and87 P2. Recomputed histograms/expanded ties,44 unique held-out rows, all61 trajectory depths and35 undefined quiet widths. Observed maximum11 remains OPEN globally. Native delta/key strings were not treated as freshly checked proofs and no full tree rebuilt.'
    for name,assessment in bounded.items():
        p=PREFIX+name;rows[p]={'path':p,'sha256':frozen[p]['sha256'],'full_source_read':False,'reviewed_lines':[],
            'review_level':'bounded_all_record_or_member_checks','assessment':assessment,'detail_receipt':'dag/reviews/additional_paper_011_history_finite_data.json'}
    report['findings'].append(finding('PAPER011-FINITE-G03-COMPRESSED-ONLY-CURRENT-INPUTS',
        'G03 current checkout lacks nine raw inputs/results consumed by its retained test/receiver paths, including full_native_request/stdout, key_correspondences and reference_rows. Both69-member archives retain all nine with valid hashes. Thus the current raw_run_files_deleted=False statement does not describe this checkout; compressed custody survives, but direct local replay needs an explicit verified restoration or streaming adapter.',
        ['g03/README.md','g03/archive_manifest.json','g03_package_v1/test_paper011_genesis_g03.py'],
        'Retain archives and declare compressed-only inputs in the workflow; avoid treating file existence or old test output as current replay success. No files were restored or deleted by this audit.'))
extra_full={
 'g03/focused_tests_junit.xml':'Complete XML body read:19 historical testcases,0 errors/failures/skips,79.900s suite time. Cases correspond to the reviewed finite custody/candidate/poison suite; this is retained test output, not a fresh current run.',
 'g03_package_v1/package_scoped_tests_junit.xml':'Complete XML body read:two later package-order/exclusion controls,0 failures,0.672s historical suite. These controls are in the current test owner rather than the archived earlier v1 test source; editions remain distinct.',
 'g03_package_v1/first_pack_terminal_tool_records.jsonl':'Complete two-record terminal excerpt read. Matching call identifier and historical exit0 output retain archive946395.../32547669bytes/69members/1682042010raw bytes. It records completion of that pack session, not the mathematical experiment or current execution.',
 'g03_package_v1/first_pack_tool_records.jsonl':'Complete two-record tool excerpt read. Historical solve-contract construction and pack launch retain19-test summary and an asynchronous session identifier. A launch/session is not completion; terminal excerpt supplies the separate final pack result. Embedded command/approval text is inert archival data.',
 'g03_package_v1/first_run_tool_records.jsonl':'Complete two-record launch excerpt read. Old Python3.12/native G03 command returns a running session; no terminal success appears here. Historical permission justifications and paths are not executed or reused as current authority.',
 'g03_package_v1/preregistration_tool_records.jsonl':'Complete two-record registration excerpt read. Logged successful preregistration precedes the shown run launch and freezes explicit adapter/target/predicate/source declarations. Chronology of this retained excerpt is not proof no unlogged oracle calls existed. The later finite reconstruction remains separate from model arms.',
 'g03/fixed_target_reuse_process.json':'Complete process record read: historical exit2,0.428s and request/stdout/stderr digests, old argv/cwd. Exact bound streams were checked separately against original archive; no current executable run.',
 'g03/focused_tests_process.json':'Complete process record read: historical pytest19-test invocation with explicit cache/temp/output paths, exit0 and88.127s wall time. Streams/JUnit retain distinct79.900s suite measurement. Current receipts do not certify rewritten source/runtime.',
 'g04/full_rectangle_v2/M01_stake_untransported_process.json':'Complete process record read: explicit request and physical stdout/stderr/executable hashes, exit2 and STAKE_TRANSPORT_MISMATCH expectation. Original bytes reconcile separately. Label/exit metadata do not independently prove the native algorithm ran.',
 'g07/run_v1/receipt.json':'Complete historical base-run receipt read.3617cases/44heldouts; source/build/interpreter/binary and raw stream hashes;21.559s native and49.835s total, with empirical differentiation false. Runtime excludes OS/stdlib closure; no new execution or provider-billed result inferred.',
 'g07/provider_free_completion.json':'Complete completion record read. Binds base/quiet receipts and3617/35/44 counts; conjecture OPEN, empirical differentiation false, no model arms or historical raw model reply replay. It is finite baseline completion only.',
 'g07/quiet_v1/receipt.json':'Complete quiet receipt read, including all library hashes and four control records. Declares35quiet cases and2.103s inclusive native phase; four exact typed reasons/exit2 and positive exit0 are separately stream-bound. Fresh pure-Python replay independently verifies the35 retained histories/states have pairwise distinct profiles; historical native binary execution remains unverified here.',
}
for name,assessment in extra_full.items():
    p=PREFIX+name;assert sha(ROOT/p)==frozen[p]['sha256']
    rows[p]={'path':p,'sha256':frozen[p]['sha256'],'full_source_read':True,'reviewed_lines':[[1,len((ROOT/p).read_text(encoding='utf-8-sig').splitlines())]],'assessment':assessment}
rc_path=REV/'additional_paper_011_history_finite_receipt_checks.json'
if rc_path.exists():
    rc=read(rc_path)
    def bounded_row(p,assessment):
        if p in rows and rows[p]['full_source_read']:return
        assert p in frozen
        rows[p]={'path':p,'sha256':frozen[p]['sha256'],'full_source_read':False,'reviewed_lines':[],
            'review_level':'explicit_record_binding_or_bounded_replay_checks','assessment':assessment,'detail_receipt':rc_path.relative_to(ROOT).as_posix()}
    paper_prefix='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/'
    for r in rc['source_manifests']:
        bounded_row(paper_prefix+r['path'],f"Every one of{r['rows']} declared local path/SHA/byte/Git-blob rows checked against current/LF and original archive representations, with explicit core.rs/omega.rs filename mapping. External commit/tree membership not checked. Raw mismatches remain visible; no new mathematical proof or binary correspondence follows.")
    for r in rc['process_streams']:
        bounded_row(paper_prefix+r['path'],'All explicit request/stdout/stderr bindings reconciled to current and original archive or nested G03 stream identities. Across26 process records,72 original bindings pass and26 current raw bindings pass. Exit codes, durations and typed expectations remain historical metadata; no native process was rerun.')
    for r in rc['before_after_maps']:
        p=paper_prefix+r['path']
        bounded_row(p,'Complete named before/after digest-map comparison and all confined local bindings checked; external runtime/compiler/library paths were explicitly not accessed. Declared maps agree within their run. Historical G04 helper833583... is unresolved at its named current and original ZIP path; no fresh hermetic build or source/executable equivalence established.')
    for r in rc['binary_dispositions']:
        bounded_row(r['path'],'Complete zero-byte process-stream identity checked; emptiness is not proof of success.' if r['format'].startswith('empty') else 'Full-file digest and bounded PE header inspected (AMD64 executable); archive bytes agree. Retained executable remained inert; machine code was not audited or independently rebuilt.')
    for p in rc['json_schema']['empty_json_named_streams']:
        bounded_row(p,'Complete empty output stream inspected; despite .json suffix it contains no JSON document. This is expected for its retained nonzero-exit negative control, not a successful empty mathematical result.')
    for name in ['request.json','stdout.json','duplicate_case_request.json','malformed_history_request.json','nonquiet_state_request.json','unknown_event_request.json']:
        bounded_row(PREFIX+'g07/quiet_v1/'+name,'All35 positive histories replayed through review-vetted pure Python admission/observation source and compared with retained state/id/depth records; profiles are pairwise distinct and requirements satisfied. Four controls reproduce duplicate IDs, a nonquiet pair, unknown constructor and malformed form999. This is a fresh bounded Python3.14 check, not historical native execution or an unbounded theorem.')
    report['findings'].append(finding('PAPER011-FINITE-G04-HISTORICAL-HELPER-GAP',
        'Four G04 build/execution receipts bind code/genesis_g04_replay.py SHA83358310e833cb7aa7d04851f6a8c437c13259bdac78a6cb963f8b4e3eaaa99b. Current raw/LF bytes differ; the original ZIP same-path body hashes e02d7a24f927f54f3c06ab5ffad913e418b51c1fe6831754f511a97772346c6b. No outer archive member has the recorded833583... digest. This unresolved exact helper version is distinct from reversible line-ending/name migration.',
        ['g04/full_rectangle_v2/receipt.json','g04/native_build_v1/receipt.json','g04/universal_poison_build_v1/receipt.json','g04/universal_poison_v1/receipt.json'],
        'Recover the exact historical helper from a separately bound snapshot or state this runtime/source gap. Provided finite mapping/data checks remain valid at their stated scope; do not infer their falsity or repair old receipts by repinning.'))
report.update(status='in_progress',file_reviews=sorted(rows.values(),key=lambda x:x['path']),pending_paths=sorted(set(frozen)-set(rows)),
              validation=[{'rule':'selected_source_small_controls','receipt':'dag/reviews/additional_paper_011_history_finite_probes.json','status':'completed'}],
              limits=['No native binaries/providers/external repositories/private QM answers accessed.','Full source transfer requires exact bytes and explicit G07 caller-context review; it is not binary runtime certification.','Large receipt populations and archives remain pending.'])
write(target,report)
swarm_path=ROOT/'dag/swarm_manifest.json';swarm=read(swarm_path)
swarm['parent_active_slice']={'scope':'191 Paper011 g03/g04/g07 finite-history source and receipt paths','status':'in_progress','scope_manifest':'dag/reviews/additional_paper_011_history_finite_receipts_scope.json','report':str(target.relative_to(ROOT)).replace('\\','/')}
write(swarm_path,swarm)
print(json.dumps({'full_bodies':sum(x['full_source_read'] for x in rows.values()),'exact_transfer_bodies':transferred,'pending':len(report['pending_paths'])}))
