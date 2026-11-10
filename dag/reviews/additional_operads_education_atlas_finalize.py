"""Assemble completed source/visual audit from explicit readings and bounded controls."""
from pathlib import Path
import hashlib,json,zipfile,difflib
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_operads_education_atlas'
scope=json.loads(Path(str(P)+'_scope.json').read_text())
notes=json.loads(Path(str(P)+'_notes.json').read_text())
ledger=json.loads(Path(str(P)+'_read_ledger.json').read_text())
checks=json.loads(Path(str(P)+'_checks.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reviews=[]
for i,r in enumerate(scope['files']):
    assert sha(ROOT/r['path'])==r['sha256']
    if r['lines'] is not None:
        ranges=[v for x in ledger if x['path']==r['path'] and x['sha256']==r['sha256'] for v in x['reviewed_lines']]
        assert set(n for a,z in ranges for n in range(a,z+1))==set(range(1,r['lines']+1))
        reviews.append(dict(r,full_source_read=True,reviewed_lines=[[1,r['lines']]],
            review_level='full_text_source_review',reading_method='complete_body_display_and_substantive_assessment',
            assessment=notes['assessments'][str(i)],parsed_value_read=False))
    else:
        meta=next(p for p in checks['png_metadata'] if p['path']==r['path'])
        reviews.append(dict(r,full_source_read=False,reviewed_lines=[],review_level='complete_image_visual_bounded_binary_review',
            visual_review={'entire_image_inspected':True,'detail':'original','width':meta['width'],'height':meta['height']},
            reading_method='whole_image_visual_inspection_plus_PNG_header_dimensions',
            assessment=notes['visual_assessments'][str(i)],parsed_value_read=True,
            limitation='No byte-by-byte human binary read, encoder audit, hidden metadata audit, SVG rendering or pixel-equality claim.'))
s=scope['supporting_source']
assert sha(ROOT/s['path'])==s['current_sha256']
assert sha(Path(s['original_archive']))==s['archive_sha256']
with zipfile.ZipFile(s['original_archive']) as z: original=z.read(s['archive_member'])
assert hashlib.sha256(original).hexdigest()==s['original_sha256']
current=(ROOT/s['path']).read_bytes()
delta=''.join(difflib.unified_diff(original.decode().splitlines(True),current.decode().splitlines(True),fromfile='original',tofile='current'))
reviews.append(dict(path=s['path'],sha256=s['original_sha256'],bytes=s['original_bytes'],source_line_count=s['original_lines'],
    full_source_read=True,reviewed_lines=[[1,204]],review_level='full_original_archive_source_and_current_delta_review',
    assessment=notes['supporting_assessment'],supporting_source_outside_52=True,
    original_archive=s['original_archive'],archive_member=s['archive_member'],archive_sha256=s['archive_sha256'],
    current_source={'path':s['path'],'sha256':s['current_sha256'],'bytes':s['current_bytes'],'full_source_read':True,'reviewed_lines':[[1,204]]},
    complete_delta=delta,change_classification='authorized migration navigation repair; not unexplained drift'))
def E(i,a=None,z=None):
    r=scope['files'][i]
    return dict(path=r['path'],sha256=r['sha256'],lines=[] if r['lines'] is None else [[a or 1,z or r['lines']]],
        full_source_read=r['lines'] is not None,review_basis='new full text read' if r['lines'] is not None else 'new entire-image visual inspection')
claims=[];findings=[]
def C(n,statement,evidence,ceiling):
    claims.append(dict(id=f'OEA-C{n:02d}',statement=statement,source_evidence=evidence,ceiling=ceiling))
def F(n,title,statement,evidence,action,related=None,controls=None,severity='medium'):
    findings.append(dict(id=f'OEA-F{n:02d}',title=title,severity=severity,statement=statement,source_evidence=evidence,
        recommended_action=action,related_prior_findings=related or [],fresh_controls=controls or [],
        evidence_kind='new complete teaching-source/visual review; cited previous source findings remain prior evidence'))
C(1,'The ordered-profile splice and its zero-based nested/disjoint reindexing equations are a useful reusable structural mechanism. They constrain interfaces independently of arbitrary executor behavior.',
  [E(43,34,102),E(37,30,38)],'Equations are assessed mathematically at the profile/term level; no universal implementation or callback-law theorem is inferred.')
C(2,'The inventory and updated resolver chapters distinguish declaration, lexical binding, registered executor coverage, finite typed plans and actual callback execution. Ordered repeated inputs, guard preflight and explicit unavailable outcomes are useful workflow contracts.',
  [E(36,57,78),E(36,119,129),E(37,22,38),E(37,65,89),E(37,105,130)],'Documentation read with prior owner context. No new native host, model execution, performance or all-tree correctness reproduction.')
C(3,'The management-ladder guide preserves the failed initial call, unknown historical usage, continuing liability, source amendments and later settlement. It explicitly separates22 perspectives from22 independent workers and disk storage from provider tokens.',
  [E(39,86,138),E(39,140,178)],'Historical campaign observations are not fresh test evidence or a general management-benefit result. No old authorization is reused for new calls.')
C(4,'The separately changed consolidation plan has complete original and current reads. Its only delta is the authorized line48 teaching-code link; all52 other frozen hashes match.',
  [{'path':s['path'],'sha256':s['original_sha256'],'lines':[[1,204]],'full_source_read':True,'archive_member':s['archive_member']},
   {'path':s['path'],'sha256':s['current_sha256'],'lines':[[1,204]],'full_source_read':True,'version':'current authorized migration'}],
  'Custody and navigation equivalence only; no source repair completion, hidden benchmark use or migration efficacy inference.')
C(5,'The early atlas and later corpus-discovery proposal give useful explicit ceilings: byte equality, syntax, observational checks, witness bindings and external admission answer different questions. Proposed learning/repair mechanisms remain proposals.',
  [E(12,1,91),E(18,1,91),E(33,190,204),E(33,242,279),E(33,318,333)],
  'A strong audit/design vocabulary, not a new operad family or completed generic discovery workflow. External literature was not independently reverified.')

F(1,'Production labels outrun the documented execution boundary',
  'The levels overview says the engine prevents semantic drift/hallucinated handoffs and that every agent/workflow is slice-bounded and associativity-verified. The atlas itself labels symmetry, equivalence and contractivity NONCLAIM; it then asserts a Convention[kappa] slot enforces synchronization without an executor/witness protocol. A typed field does not implement a barrier or establish semantic truth. Later resolver chapters are substantially better scoped.',
  [E(40,3,8),E(40,31,40),E(40,64,95),E(14,62,89),E(37,116,126)],
  'Align curriculum status with a named implementation snapshot, explicit checker and bounded claims; mark convention synchronization as proposed until its owner and negative controls are bound.',
  ['OET-F04','OCR08','OCR10'])
F(2,'Symmetry, units and signature witnesses are different obligations',
  'Level00 calls the system symmetric but provides no symmetric action. f(sigma x)=f(x) is input-permutation invariance, not the general equivariance condition, and arbitrary permutations can be ill-typed for heterogeneous profiles. Its ensure_units code skips an existing id_* without validating its signature and only iterates registered colours. Level02 correctly computes profile splices, but matching ColourSignature cannot establish equality of differently named operations or arbitrary effects.',
  [E(41,83,95),E(41,144,167),E(41,174,195),E(43,112,189),E(14,62,75)],
  'Teach the planar profile algebra first; specify lawful identities, action/permutation conventions and the operation equality or interpretation before claiming a symmetric operad.',
  ['MOT-F01','OET-F02','OCR10'])
F(3,'The polarized formalization does not type its own iteration laws',
  'The declared g:SxCxR->SxFxOxHxE is not an endomap. pi_S o g must equal the input projection SxCxR->S, not id_S; the later pointwise equation is correctly typed. g(g(x)), commutation and finding inclusion need an extension/reinjection carrying context, registry and accumulated findings. Delta:C->C tensor C, with C already a finite colour set, does not specify a coloured cooperad, its indexed decomposition maps or coassociativity/counit laws.',
  [E(24,115,145),E(24,177,221),E(45,37,50)],
  'Define an explicit audit-state endomap or typed Kleisli/state composition and its equality; retain cooperad language as an analogy until its carrier and laws are supplied.')
F(4,'Gauge-break predicates do not preserve the task or guarantee descent',
  'A fixed cochain gauge addition omega+d alpha preserves d omega because d squared is zero. Changing the carrier can change the problem unless a comparison map and original-obligation preservation are supplied. The proposed mass-conservation test is only a positive lower bound. The OR descent rule accepts(phi,gamma)=(2,0)->(1,100), increasing the other residual and their sum. The nine-dot analogy also omits its four-stroke constraint.',
  [E(29,85,131)],
  'Separate fixed-carrier gauge, coordinate change and carrier extension; bind the original-task checker and a well-founded/vector descent rule with explicit conserved quantities.',controls=['OEA-T03'])
F(5,'Small representation steps and a finite canary bank do not establish the stated conclusion',
  'Chapter21 infers a non-exact local minimum from small consecutive representation distance plus positive defect count. A two-state graph with observed trajectory A,A, defect(A)=1 and neighboring defect(B)=0 meets that stopping condition without a local minimum. Its canary-only admission/auto-commit and hash-equality-as-atomic-replication language omit the external binding and effect gates spelled out in chapter22. A budget stop is valid policy; the convergence/admission interpretation is stronger.',
  [E(32,37,65),E(32,71,107),E(33,190,204),E(33,242,279)],
  'Emit a bounded stagnation observation with unknown optimality; distinguish finite fixture policy from semantic adequacy, external admission and transactional effects.',controls=['OEA-T04'])
F(6,'Worked workflow and diagram examples lose their typed inputs',
  'Level07 starts with manager:(State)->Contract and inserts enforcer:(Contract,Code)->Audit into its State slot, so Audit!=State. Reversing them gives(State,Code)->Audit, still not the declared(Contract,Code)->Audit. The agent PNG changes verify_proof from(Proof,Code) to(Proof,Audit) in the tree and labels the total Code->Receipt, losing Proof. The SVG separately labels gamma(f;g1) beside two children. These are teaching-example defects, not a newly observed production exploit.',
  [E(48,36,125),E(43,207,223),E(3,85,132),E(2),E(10,95,106)],
  'Use one fully specified ordered tree and enumerate every external leaf; regenerate independently checked diagrams from that example.',controls=['OEA-T01'])
F(7,'Capability slices are not automatically suboperads or sandboxes',
  'The displayed AgentSlice is a mutable allow-list with optional colour filters. Empty filters mean unrestricted; identity-like operations bypass license and colour checks before filtering. No closure under composition or required units is shown, so calling every slice a suboperad is unjustified. The no-unlicensed-operation and no-out-of-colour invariants omit the explicit identity exception. Calling this function is also an independent runtime requirement.',
  [E(44,24,96),E(44,199,215)],
  'Name the structure an allow-list unless closure is established; specify empty-set semantics and validate units before bypassing checks. Bind tool effects to the permission owner.',related=['OCR01','NATIVE03-BUG-002'])
F(8,'Residual observation and frozen fields do not give contraction or immutable evidence',
  'The lesson calls Phi decrease strict contractivity and promises automatic rollback. diag(1/2,1) decreases the sample(2,0) but has l1 operator norm1, so that sample does not establish uniform contraction. Three rows are not independent runs or a bound checker (prior OCR09). The literal frozen EvidenceReceipt has a mutable metadata dictionary, confirmed by a local snippet control; its immutable audit-trail claim therefore needs a custody mechanism beyond dataclass freezing.',
  [E(47,24,50),E(47,54,108)],
  'Use measured nonincrease/decrease labels, bind metric/checker/run identity and actual rollback owner, and separate immutable serialization from mutable in-memory records.',
  ['OCR09','MOT-F02','MOT-F03'],['OEA-T02','OEA-T05'])
F(9,'Anti-skill lifecycle lesson cites a different current owner contract',
  'Level04 attributes an affinity/half-life AntiSkillRecordV2 and automatic mutation/pruning to domain/anti_skills/anti_skill_v2.py. The hash-bound prior full owner review instead describes closed predicate/fixture/admission records and expressly no self-activation; its current opening contract confirms this. Two danger/near-miss cases are useful finite controls, not proof of detector adequacy or a completed mixed-polarity operad. The existing negative claim that anti-skills are not inverses is appropriate.',
  [E(45,37,117)],
  'Correct the owner/API and separate current closed-predicate records from proposed affinity/decay/activation mechanisms. Require positive half-life and bound evidence for any new pruning policy.',related=['additional_operads_core_remaining:operads/domain/anti_skills/anti_skill_v2.py'])
F(10,'Treg evidence labels and downgrade effects are overstated',
  'The exact2/5 strict threshold and sample floor3 are coherent policy. However, unconfirmed suppressions are not necessarily false positives, and three samples do not ensure statistical stability. The displayed code adds a name to an internal set and emits a receipt; it does not itself reconfigure a separate blocking gate or make development unblock immediately. Unknown evidence must remain distinct from independently confirmed benignness.',
  [E(46,35,57),E(46,80,128),E(46,151,169),E(39,163,171)],
  'State the empirical labels and caller responsibilities explicitly; use independently confirmed benign cases when measuring false-positive regulation. Keep EIS and teaching rate-limit mechanisms distinct.',controls=['OEA-T07'])
F(11,'Receipt example and authority/custody claims exceed their encoding',
  'Level09 uses SHA256(empty bytes) for a nonempty receipt: it matches neither the full displayed compact sorted JSON nor the payload with the hash field removed. The document gives no complete cross-library canonicalization contract beyond a Python dump recipe. A None-only enum constrains a field, not all program effects; a mutable default string is weaker still. Tail truncation is detected against a trusted retained head, not when both head and tail can be rewritten. The text does not bind a functioning GPG admission endpoint.',
  [E(50,24,66),E(50,70,129),E(50,133,173),E(42,124,139),E(37,80,89)],
  'Mark examples as illustrative or compute their real digest; name the exact serialization profile/self-field policy, preserve independent heads and bind actual authorization separately.',
  ['OET-F04','MOT-F03'],['OEA-T06'])
F(12,'Compiled checking and rollback are not compile-time or atomicity proofs',
  'Level10 says dynamic arity/slice/estate integrity is verified at compile time and that Rust slices prevent nullary evaluation; slices can be empty and runtime validation is a separate step. Prior source-pinned adapter/tape review describes finite native metadata validation, an unbound license refusal and the import-blocked legacy DDC parser, not the complete execution bridge promised here. Level08 sequential removal/copy/regeneration and final byte equality do not by themselves provide crash/concurrency atomicity.',
  [E(51,25,31),E(51,55,87),E(49,86,110),E(49,167,171)],
  'State each compiled runtime predicate and its admitted domain; cite actual rollback/crash controls and isolate unavailable legacy tape execution. Do not infer general tool isolation from Rust types.',related=['OCR05','OCR06','additional_operads_core_remaining:operads/infrastructure/operad/higher_operad_adapter.py'])
F(13,'Architecture diagrams assert missing semantic and optimization bridges',
  'The guide introduces Data and figures introduce Spec/LakeModule/Package/Claim/Refutation without mappings to the closed ten colours. They label parsed operations Executable/Verified/Admitted and no-obstruction results admitted to a catalog. The residual figure adds a presheaf colimit, univalent merge and convergence to Phi_min without its diagram, maps, universal property or optimization hypotheses. The useful architecture/status pictures cannot supply those mechanisms. PNGs differ materially from SVGs and several labels overlap or overflow.',
  [E(10,72,81),E(10,123,182),E(10,225,265),E(5,103,129),E(7,91,120),E(9,39,99),E(4),E(6),E(8)],
  'Label conceptual examples and intended future gates; bind any real executor, external admission or residual solver. Keep diagrams source-consistent and repair their text layout without treating image polish as proof.')
F(14,'Historical navigation remains broken beyond the repaired migration link',
  'A literal inline-link existence scan over the42 scoped Markdown bodies found89 missing targets among400 local link occurrences;60 occurrences resolve outside the repository. Many level code links climb one directory too far and the old test guide points under education/008_oeop/tests. Fragment validity and reference-style links were not checked. The separately reviewed chapter23 link was correctly repaired by the authorized migration and is not an unexplained change.',
  [E(27,70,103),E(40,48,60),E(41,46,46),E(33,18,18)],
  'Prepare a separately authorized navigation repair using actual current owners or explicit retired labels; preserve historical code/test claims and archive provenance.',severity='low')

prior=[]
for name in ['additional_operads_education_remaining','additional_migrated_operad_teaching','additional_operads_core_remaining','additional_native_systems_03']:
    p=ROOT/'dag/reviews'/f'{name}.json'
    prior.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'use':'context and previously completed source/controls; no new execution credit'})
dependencies=[]
core=json.loads((ROOT/'dag/reviews/additional_operads_core_remaining.json').read_text())
for path in ['operads/domain/anti_skills/anti_skill_v2.py','operads/infrastructure/ddc_execution/ddc_tape.py','operads/infrastructure/operad/higher_operad_adapter.py','operads/skill_operad/skill_compiler/budget_gate.py']:
    old=next(r for r in core['file_reviews'] if r['path']==path)
    assert sha(ROOT/path)==old['sha256']
    dependencies.append({'path':path,'sha256':old['sha256'],'prior_full_source_report':'dag/reviews/additional_operads_core_remaining.json',
        'prior_reviewed_lines':old['reviewed_lines'],'prior_assessment':old['assessment'],
        'new_reviewed_lines':[[1,65]] if path.endswith(('anti_skill_v2.py','budget_gate.py')) else [],'new_full_read_credit':False})
for finding_id,paths in {
    'OEA-F09':['operads/domain/anti_skills/anti_skill_v2.py'],
    'OEA-F12':['operads/infrastructure/ddc_execution/ddc_tape.py','operads/infrastructure/operad/higher_operad_adapter.py'],
}.items():
    f=next(x for x in findings if x['id']==finding_id)
    for path in paths:
        d=next(x for x in dependencies if x['path']==path)
        f['source_evidence'].append({'path':path,'sha256':d['sha256'],'lines':d['prior_reviewed_lines'],
            'full_source_read':True,'review_basis':'prior hash-identical complete source read; no additional full-read credit',
            'prior_report':d['prior_full_source_report']})
report={'source_commit':scope['source_commit'],'status':'complete','scope_manifest':P.relative_to(ROOT).as_posix()+'_scope.json',
    'summary':{'frozen_scope':52,'supporting_original_sources':1,'full_scope_text_bodies':47,'whole_image_visual_bounded_binary':5,
        'full_supporting_original_bodies':1,'full_supporting_current_bodies':1,'full_text_scoped_lines':sum(r['lines'] or 0 for r in scope['files']),
        'frozen_scope_bytes':sum(r['bytes'] for r in scope['files']),'pending':0,'claims':len(claims),'findings':len(findings),'fresh_bounded_checks':8},
    'file_reviews':reviews,'pending_paths':[],'claims':claims,'findings':findings,'prior_evidence':prior,'dependency_context':dependencies,
    'fresh_validation':{'path':P.relative_to(ROOT).as_posix()+'_checks.json','sha256':sha(Path(str(P)+'_checks.json')),
        'controls':checks['fresh_checks'],'navigation_summary':{k:v for k,v in checks['navigation'].items() if k!='links'},
        'svg_checks':checks['svg_checks'],'png_metadata':checks['png_metadata'],
        'probe_history':['Initial helper regex failed to find a CRLF-fenced block before any check completed; normalized only in-memory decoded text and reran successfully.','A further pure integer-defect graph was added to clarify the stagnation counterexample; final eight checks passed.']},
    'validation_receipt':P.relative_to(ROOT).as_posix()+'_validation.json',
    'workflow_disposition':[
        'Retain ordered-profile substitution, declared-port refinement, guard-slot checks and explicit callback accounting as bounded reusable mechanisms; do not mint new families for narrative domains.',
        'Retain audit/custody/admission separation, negative controls, historical failure retention and continuing budget liability as useful design and teaching contracts.',
        'Correct the worked manifests, symmetry/equivariance definitions, status labels and image examples before using these lessons as executable specifications.',
        'A transfer to any new task needs an admitted input encoding, original-task checker, task-preserving transforms, metric/fixture bindings and external-effect authorization. No target answer or hidden benchmark artifact was read or supplied.'
    ],
    'limits':['All47 scoped text/XML bodies were read completely, including231 historical ledger rows; this gives no reading credit for their referenced bodies.',
        'Five PNGs received whole-image visual inspection and bounded header checks, not full human binary-byte coverage. SVG source was read; no renderer or pixel-equivalence test ran.',
        '53 original paths have dispositions:52 frozen unchanged plus one recovery-archive supporting original; the current supporting version is a separately identified read, not another original inventory path.',
        'No literature lookup, foreign-repository body read, provider/model call, native build, private benchmark/seed/key access, or original source mutation.',
        'Historical suite counts, live-campaign results and previous reviews remain historical evidence. Eight controls cover exact displayed examples and arithmetic only, not a fresh production suite.',
        'All recommendations are review findings; no deletion, source repair, admission or cutover was performed.']}
Path(str(P)+'.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
md=['# OPERADS education atlas and levels audit','',
    'Completed 52 frozen paths: 47 full Markdown/SVG bodies and five whole-image visual inspections with bounded binary accounting. The 53rd supporting original and its current authorized migration revision were both read completely. No pending paths.','',
    'The useful contribution is ordered typed composition, explicit guard/callback boundaries, evidence custody and scoped experimental accounting. The lessons and diagrams overstate symmetric-operad semantics, contraction, immutability and automatic admission; several worked examples fail their own displayed contracts.','',
    'There are five bounded claims, fourteen findings and eight fresh offline controls. Prior owner tests and historical campaign counts are not fresh execution.','',
    '## Findings','']
for f in findings:
    md += ['### '+f['id']+' — '+f['title'],'',f['statement'],'','Recommended action: '+f['recommended_action'],'']
    for e in f['source_evidence']:
        desc='full image' if not e['lines'] else ', '.join(f'{a}–{z}' for a,z in e['lines'])
        md.append(f"- `{e['path']}` ({desc}); SHA256 `{e['sha256']}`.")
    if f['related_prior_findings']: md += ['','Prior evidence, not re-executed: '+', '.join(f['related_prior_findings'])+'.']
    if f['fresh_controls']:md += ['','Fresh bounded controls: '+', '.join(f['fresh_controls'])+'.']
    md.append('')
md += ['## Supported contributions','']
for c in claims:md += ['- **'+c['id']+'** '+c['statement']+' Limit: '+c['ceiling']]
md += ['','## Fresh checks and coverage','',
    'Eight controls verified the published profile mismatch, a noncontractive operator with a decreasing sample, OR-descent/mass-floor counterexamples, stagnation counterexamples, mutable metadata in the literal frozen snippet, the empty-input receipt digest, exact Treg threshold arithmetic and 231 numbered ledger rows. Five SVGs parse without scripts/external hrefs. All five PNGs were visually inspected at original resolution.','',
    'The inline navigation scan found 89 missing targets/400 local occurrences, including 60 occurrences resolving outside the repository. It checks neither anchors nor reference-style links; the full occurrence list is in the checks JSON.','',
    'The initial helper failed before controls on CRLF fence parsing; only its in-memory normalization changed. No source bytes changed.','',
    '## Complete per-file dispositions','']
for r in reviews:
    coverage='full text '+str(r['reviewed_lines']) if r['full_source_read'] else 'whole-image visual; bounded binary'
    md += ['### '+r['path'],'',coverage+'; SHA256 `'+r['sha256']+'`.','',r['assessment'],'']
md += ['## Limits','']+['- '+x for x in report['limits']]
Path(str(P)+'.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps(report['summary']))
