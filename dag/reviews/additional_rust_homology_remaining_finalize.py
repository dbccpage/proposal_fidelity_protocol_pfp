"""Finalize this declared source-review slice; no original code execution."""
import sys,json,re,hashlib,datetime
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a

assert a.sha(a.file('_scope.json'))=='6bcbbbca1fd29535e26badb949d0f4655439b42d5634e1be09c978bfdb3ca729'
before=a.read('.json');assert before['scope']['full_source_reads']==126 and before['scope']['pending_files']==0
ledger=a.read('_read_ledger.json')
for x in ledger:
    if x['path'].endswith('/restriction_dga.rs'):
        x['assessment']=x['assessment'].replace('through the pending FinitePoset owner','through the FinitePoset owner, subsequently fully reviewed in checkpoint10').replace('Backend and poset validity remain dependencies','The exact backend remains an unexecuted dependency; the private FinitePoset constructor and complete source are reviewed in this slice')
a.write('_read_ledger.json',ledger)
n=a.read('_notes.json')
next(x for x in n['claims'] if x['id']=='RUSTHOMOLOGY-CL006')['limits']='No actual local replay, cover construction, extraction of the comparison map, proof of faithful comparison or quantitative Phi1 value is computed.'
next(x for x in n['claims'] if x['id']=='RUSTHOMOLOGY-CL007')['limits']='The exact dot-product certificate is credited within its limited predicate; the approximate dual witness expressly lacks theorem-grade status. No quantitative optimizer or external norm backend is replayed here.'
f=next(x for x in n['findings'] if x['id']=='RUSTHOMOLOGY-F056')
f['reason']+=' Relabel the control facet vertices 1..6 as 0..5 when passing them to the indexed FiniteDirectedGraph/graph_carrier constructors; this does not change either incidence matrix rank.'
for x in n['findings']:
    x['runtime_scope']='inactive_source_only' if 60<=int(x['id'][-3:])<=65 else 'active_api_or_claim_with_stated_limits'
    if x['id'] in ('RUSTHOMOLOGY-F055','RUSTHOMOLOGY-F056'):x['severity']='low'

# Cosmetic prose spacing only; never edit identifiers, paths, hashes or source.
def readable(s):
    s=re.sub(r'\b(all|every|through|under|Independent|independent|on|with)(?=\d)',r'\1 ',s)
    s=re.sub(r'(\d)(?=(?:lines|labels|vertices|vertex|edges|faces|cells|tables|maps|cycles|fillings|small|matrix|parameter|nonzero|source|degree|dimensions|integers|cases|bytes|pairs|terms|choices|triangles|cores|columns|rows)\b)',r'\1 ',s)
    return s
for x in ledger:x['assessment']=readable(x['assessment'])
a.write('_read_ledger.json',ledger)
for group in ('claims','findings','controls'):
    for x in n[group]:
        for k in ('statement','reason','limits'):
            if isinstance(x.get(k),str):x[k]=readable(x[k])
n['analysis_complete']=True
n['completed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
n['completion_scope']='All 126 paths in the frozen Rust core_homology remaining scope only. The original repository-wide audit remains incomplete.'
n['methodology']={
 'reading':'Every source/manifests/test body was displayed and substantively reviewed. Complete ranges and chunk assessments are in file_reviews and the durable read ledger; no parse-only or template-only full credit.',
 'custody':'Scope was reconciled with original inventory and then-current coverage before reading. All126 current bodies match frozen original SHA256 at final validation. No originals or shared coverage/DAG/manifests were edited by this lane.',
 'controls':'23 audit-owned standard-library Python controls, executed with the explicit workspace Python3.14.2 runtime. They independently evaluate source predicates, mathematical countermodels or bounded exact identities; they do not run Rust or its backends.',
 'test_review':'Inline and integration test source was assessed for real assertions, omitted premises, literal Result assertions, historical mutation labels and disabled modules. Cargo collection/build/test success is not claimed.',
 'template_accounting':'Repeated capacity wrappers and tests were read in every displayed body. No base/delta transfer was used in this slice.',
 'authority':'AuthorityEffect and contract URNs are interpreted as source labels, not new authorization or a proof of workflow acceptance.'}
n['synthesis']={
 'substantive_foundations':[
  {'claims':['RUSTHOMOLOGY-CL005','RUSTHOMOLOGY-CL020','RUSTHOMOLOGY-CL024','RUSTHOMOLOGY-CL025'],'assessment':'Private exact carriers, immutable rational quotient/map snapshots, coordinate-lattice Smith receipts and complete integral equivalence/perturbation checks are reusable foundations. Their backend arithmetic and metadata authentication ceilings remain explicit.'},
  {'claims':['RUSTHOMOLOGY-CL009','RUSTHOMOLOGY-CL014','RUSTHOMOLOGY-CL016','RUSTHOMOLOGY-CL023','RUSTHOMOLOGY-CL027'],'assessment':'Finite posets, restriction matrix algebra, F2 cup/cohomology, question-preserving comparison cells and explicit permutohedral contractions contain actual equations and algorithms. Exact finite controls support their declared small carriers.'},
  {'claims':['RUSTHOMOLOGY-CL011','RUSTHOMOLOGY-CL012','RUSTHOMOLOGY-CL022','RUSTHOMOLOGY-CL029'],'assessment':'Validated clique and persistence pipelines, cyclic coboundary replay, odd-cycle/parity certificates, signed matrix symmetries and exact ordinary Lie-table admission are substantive mechanisms beyond module names.'}],
 'principal_boundaries':[
  {'findings':['RUSTHOMOLOGY-F002','RUSTHOMOLOGY-F004','RUSTHOMOLOGY-F005','RUSTHOMOLOGY-F010','RUSTHOMOLOGY-F011','RUSTHOMOLOGY-F014','RUSTHOMOLOGY-F036','RUSTHOMOLOGY-F041','RUSTHOMOLOGY-F044'],'assessment':'Construction-time equations must be distinguished from retained immutable invariants, deserialization admission, basis/carrier identity, projection obligations and complete receipt binding.'},
  {'findings':['RUSTHOMOLOGY-F016','RUSTHOMOLOGY-F018','RUSTHOMOLOGY-F020','RUSTHOMOLOGY-F043','RUSTHOMOLOGY-F048','RUSTHOMOLOGY-F050','RUSTHOMOLOGY-F052','RUSTHOMOLOGY-F066'],'assessment':'Dot equality, source coordinate predicates, support partitions, claimed diagnostics, supplied trees and incomplete numerical bases do not establish the stronger optimality, exactness, additivity or completeness interpretations.'},
  {'findings':['RUSTHOMOLOGY-F019','RUSTHOMOLOGY-F035','RUSTHOMOLOGY-F037','RUSTHOMOLOGY-F038','RUSTHOMOLOGY-F049','RUSTHOMOLOGY-F051','RUSTHOMOLOGY-F054','RUSTHOMOLOGY-F057','RUSTHOMOLOGY-F058'],'assessment':'Fixed-width overflow, hidden intermediate float overflow, allocation preflight and combinatorial expansion need owner-specific limits; separate capacity wrappers do not supply them.'}],
 'inactive_history':{'findings':['RUSTHOMOLOGY-F060','RUSTHOMOLOGY-F061','RUSTHOMOLOGY-F062','RUSTHOMOLOGY-F063','RUSTHOMOLOGY-F064','RUSTHOMOLOGY-F065'],'assessment':'DGLA, L-infinity, Lefschetz and transition-scorer files have cfg(any()). Their full bodies are reviewed historical source, not active features. Exact gauge-sign, parity, nondegeneracy and transfer-vacuity findings must not be attributed to the stronger active owners.'},
 'pfp_eis_pciv_operads_contribution':'The reviewed mechanisms can support declared finite carrier admission, question-relative comparison, candidate replay and reconstruction. They do not alone certify semantic realization, physical interpretation, unrestricted observers, repair existence, global optimum or operational authority. Operad/A-infinity/L-infinity titles and scalar witnesses must be assessed at their implemented predicates.'}
n['limits'] += [
 'The source scope is complete; repository-wide scope is not. No providers, private benchmark answers/keys, external sources, native/Cargo builds or original retained programs were accessed or executed in this slice.',
 'Rust compiler, dependency versions, integer overflow build profiles, external exact-field/SNF/GF2/numerical/ReportQuotient implementations and end-to-end callers were not reproduced by these Python controls.',
 'Public historical comments and mutation-accounting labels are evidence of what the source says, not independent proof that mutations were executed or killed.',
 'The one HoTT owner-report consultation is separately pinned and grants no new body-reading coverage. Its validated equivalence admission is stronger than the direct Vec adapter predicate.',
 'No universal theorem, physical Genesis/Hilbert/fermion-sign conclusion, general semantic repair or repository-wide completion follows from this finite source-review slice.' ]
a.write('_notes.json',n);a.report()
r=a.read('.json');assert r['status']=='complete' and r['scope']['reviewed_original_lines']==37443
inventory={x['path']:x for x in json.loads((a.ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))['files']}
for row in r['file_reviews']:assert inventory[row['path']]['sha256']==row['sha256']==a.sha(a.ROOT/row['path'])
ids={x['id'] for group in ('claims','findings','controls') for x in r[group]}
for group in ('claims','findings'):
    for x in r[group]:
        assert x.get('evidence')
        if x.get('control'):assert x['control'] in ids
controls=[]
for x in r['controls']:
    receipt=json.loads((a.ROOT/x['receipt']['path']).read_text(encoding='utf8'))
    assert receipt['status']==x['status']
    controls.append({'id':x['id'],'rule':x['rule'],'status':x['status'],'receipt_rule':receipt.get('rule'),'helper':x['helper'],'receipt':x['receipt'],'evidence':x['evidence'],'limits':x['limits']})
a.write('_control_manifest.json',{'status':'23_bounded_controls_custody_validated','runtime':sys.version,'native_execution':False,'controls':controls,'limits':'Differing early report/receipt rule aliases are retained explicitly; IDs, statuses and pins bind the exact artifacts.'})

def cite(e):return '`'+e['path']+'`:'+str(e['lines'][0])+'–'+str(e['lines'][1])+' (SHA256 `'+e['sha256']+'`)'
md=['# Rust core_homology source and certificate audit','',
 'Complete for the **126 frozen paths**, **1,313,676 bytes**, and **37,443 lines** in this slice: **126 full body reads**, **0 partial**, **0 bounded data dispositions**, **0 pending**. The broader repository audit remains incomplete.','',
 'The report contains **67 findings**, **29 qualified claims**, and **23 independent bounded controls**. Every current source hash matches its original inventory pin. Original sources and historical artifacts remain unchanged. No Rust/Cargo/native build, provider call, private answer access or original program execution was performed.','',
 'Original commit: `'+r['source_commit']+'`. Scope SHA256: `'+a.sha(a.file('_scope.json'))+'`. Report SHA256: `'+a.sha(a.file('.json'))+'`.','',
 '## Mathematical and workflow assessment','',
 'The strongest reusable components bind explicit finite carriers and replay real equations: private rational complexes and induced homology maps; integral equivalence certificates with filling/obstruction transport; normalized perturbation contractions; finite poset and restriction algebras; question-preserving comparison cells; exact graph, parity and ordinary Lie-table checks; and two constructive permutohedral contractions. Their output remains conditional on the declared representation and external arithmetic backend.','',
 'The main failures arise when a local check is promoted into a stronger certificate: mutable public state outlives constructor guarantees, omitted maps stand in for zero boundaries, receipts omit source or basis obligations, a dot equality stands in for optimality, and caller-supplied counts or trees stand in for actual geometry. Numeric and fixed-width routines have separate overflow, rank, completeness and resource limits.','',
 'Four legacy bodies are explicitly disabled by `cfg(any())`: DGLA, L-infinity, Lefschetz and the transition scorer. Their mathematical defects are historical-source findings. The active exact perturbation and Lie-table owners are assessed separately. Generic capacity wrappers and literal `Ok`/`Err` assertions do not validate the named mathematical modules.','',
 'For PFP/EIS/PCIV and operad workflows, the substantive contribution is finite admission, question-relative comparison, candidate replay and reconstruction. Semantic realization, physical interpretation, general repair existence, optimality and operational authority require additional premises and checks.','',
 '## Control results and limits','',
 'Controls used the explicit workspace Python 3.14.2 interpreter and only audit-owned standard-library scripts. They are independent mathematical reconstructions or countermodels, not a Rust test run or reproduction of an external backend. Notable exhaustive bounds include 1,100 simple graphs through five vertices; 243 posets through four vertices; 22,084 integer matrices against determinantal divisors; 2,094 admissible ordered-partition/poset pairs for both contractions; 4,927 cyclic-phase assignments; 1,099 loop-allowed graph colorings; and 343 exact Lie tables. Each receipt retains its exact carrier and ceiling.','']
for x in controls:md += ['- **'+x['id']+'** — `'+x['rule']+'`: '+x['status']+'. Receipt `'+x['receipt']['path']+'`, SHA256 `'+x['receipt']['sha256']+'`. '+x['limits']]
md += ['','## Findings','']
for x in r['findings']:
    md += ['### '+x['id']+' — '+x['statement'],'', '**'+x['severity']+'; '+x['runtime_scope']+'.** '+x['reason'],'','Evidence: '+'; '.join(cite(e) for e in x['evidence'])+'.','', 'Limit: '+x['limits']+' Control: '+str(x.get('control') or 'source inspection only')+'.','']
md += ['## Qualified claims and reusable mechanisms','']
for x in r['claims']:
    md += ['### '+x['id'],'',x['statement'],'','Evidence: '+'; '.join(cite(e) for e in x['evidence'])+'.','', 'Limit: '+x['limits'],'']
md += ['## Complete file receipts','', 'Every range below is a full substantive source/body review. Repeated wrappers were read, not granted automated template-transfer credit.','']
for x in r['file_reviews']:
    ranges=', '.join(str(lo)+'–'+str(hi) for lo,hi in x['reviewed_lines']) or 'empty body'
    md += ['### '+x['path'],'','SHA256 `'+x['sha256']+'`; '+str(x['line_count'])+' lines; read '+ranges+'.','',x['assessment'],'']
md += ['## Dependencies and remaining limits','']
for x in r['external_dependencies_consulted']:md += ['- `'+x['path']+'`, SHA256 `'+x['sha256']+'`: '+x['consulted']+' '+x['assessment']+' No source-body coverage credit.']
md += ['']+['- '+s for s in r['limits']]+['','Pending files in this declared slice: **none**.','']
a.file('.md').write_text('\n'.join(md),encoding='utf8')
a.validate('final')
validation=a.read('_final_validation.json')
validation.update({'file_inventory_sha256':a.sha(a.ROOT/'dag/file_inventory.json'),'all126_original_inventory_hashes_match':True,'finding_count':67,'claim_count':29,'control_count':23,'control_references_and_statuses_valid':True,'read_ledger_sha256':a.sha(a.file('_read_ledger.json')),'notes_sha256':a.sha(a.file('_notes.json')),'markdown_sha256':a.sha(a.file('.md')),'control_manifest_sha256':a.sha(a.file('_control_manifest.json')),'finalizer_sha256':a.sha(a.file('_finalize.py')),'native_execution':False,'pending_paths':[]})
a.write('_final_validation.json',validation)
print(json.dumps({'report_sha256':a.sha(a.file('.json')),'markdown_sha256':a.sha(a.file('.md')),'control_manifest_sha256':a.sha(a.file('_control_manifest.json')),'validation_sha256':a.sha(a.file('_final_validation.json')),'scope':r['scope'],'findings':67,'claims':29,'controls':23},indent=2))
