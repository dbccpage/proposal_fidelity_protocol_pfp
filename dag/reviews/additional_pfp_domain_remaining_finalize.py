"""Validate/finalize only this audit lane; no source mutation or reviewed-code execution."""
import sys,json,hashlib,datetime,collections
from pathlib import Path
sys.dont_write_bytecode=True
import additional_pfp_domain_remaining_audit as a
ROOT=a.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(d):
 frozen={x['path']:x for x in a.scope()['files']};inventory={x['path']:x for x in json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))['files']}
 assert len(frozen)==427
 for path,row in frozen.items():assert sha(ROOT/path)==row['sha256']==inventory[path]['sha256'] and (ROOT/path).stat().st_size==row['bytes']
 full={x['path']:x for x in d['file_reviews']};bounded={x['path']:x for x in d['automated_reviews']}
 assert len(full)==426 and len(bounded)==1 and not set(full)&set(bounded) and set(full)|set(bounded)==set(frozen)
 for p,r in full.items():
  assert r['full_source_read'] and r['sha256']==frozen[p]['sha256'] and r['assessment']
  lines=[n for start,end in r['reviewed_lines'] for n in range(start,end+1)]
  assert len(lines)==len(set(lines)) and set(lines)==set(range(1,r['line_count']+1))
  assert len((ROOT/p).read_text(encoding='utf-8-sig').splitlines())==r['line_count']
 for p,r in bounded.items():assert not r['full_source_read'] and r['sha256']==frozen[p]['sha256'] and all(isinstance(c,str) or ('rule'in c and 'status'in c) for c in r['checks'])
 ids={}
 for kind in ['claims','findings','controls']:
  seq=[x['id'] for x in d[kind]];assert len(seq)==len(set(seq));ids[kind]=set(seq)
 assert len(ids['claims'])==27 and len(ids['findings'])==120 and len(ids['controls'])==143
 for c in d['controls']:assert c['rule'] and c['status']
 for kind in ['claims','findings']:
  for c in d[kind]:
   assert c['statement'] and c['source_evidence'];assert set(c.get('control_ids',[]))<=ids['controls']
   for e in c['source_evidence']:
    assert e['sha256']==sha(ROOT/e['path'])
    n=len((ROOT/e['path']).read_text(encoding='utf-8-sig').splitlines())
    if 'lines' not in e:assert e['path'] in bounded and e.get('assessment_mode') and e.get('checks')
    for lo,hi in e.get('lines',[]):assert 1<=lo<=hi<=n
 assert not d['remaining_unsupported_files'] and all(x['status']!='pending_source_review' for x in d['pending_followups'])
 return frozen
d=a.read('.json');frozen=validate(d);probe_ids=[];probe_artifacts=[];source_bindings=[]
for p in sorted((ROOT/'dag/reviews').glob('additional_pfp_domain_remaining*probes.json')):
 out=json.loads(p.read_text(encoding='utf8'));probe_ids.extend(c['id'] for c in out['controls'])
 for binding in out['source_bindings']:
  assert sha(ROOT/binding['path'])==binding['sha256'];source_bindings.append((binding['path'],binding['sha256']))
 probe_artifacts.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'control_count':len(out['controls']),'source_binding_count':len(out['source_bindings'])})
assert len(probe_ids)==len(set(probe_ids))==143 and set(probe_ids)=={c['id'] for c in d['controls']}
now=datetime.datetime.now(datetime.timezone.utc).isoformat();n=a.read('_notes.json')
n['analysis_complete']=True
n['audit_completion']={'completed_at_utc':now,'scope_sha256':sha(a.SCOPE),'inventory_sha256':sha(ROOT/'dag/file_inventory.json'),'initial_reconciliation':'dag/reviews/additional_pfp_domain_remaining_initial_reconciliation.json','final_validation':'dag/reviews/additional_pfp_domain_remaining_final_validation.json','runtime':sys.version,'reviewed_body_lines':70549,'bounded_data_lines_not_full_read':6007,'pending_scope_paths':[],'repository_goal_complete':False,'evidence_ceiling':'Complete declared-slice accounting: 426 full bodies plus one bounded generated-panel disposition. Not universal correctness, native reproduction, empirical model performance or a whole-repository completion claim.'}
n['evidence_artifacts']=probe_artifacts+[{'path':a.file('_read_ledger.json').relative_to(ROOT).as_posix(),'sha256':sha(a.file('_read_ledger.json'))},{'path':a.file('_data_reviews.json').relative_to(ROOT).as_posix(),'sha256':sha(a.file('_data_reviews.json'))}]
n['limits'].extend(['All 143 controls belong to26 recorded bounded probe runs, with source hashes rechecked at finalization. Positive controls and counterexamples are distinguished by status.','Historical/domain instructions and embargo prose were treated as audit data. No retained sealed/private research state was loaded; finite regimes and examples were synthetic.','The 1000-entry self-panel has40 repeated base strings and6007 JSON lines. Parsed schema/custody checks and inspected base texts remain a bounded disposition, never full-source reading credit.','Python3.14.2 and installed Pydantic2.13.5 were available; this is not reproduction of a Python3.12 or native toolchain profile. No package installation, broad tests, native build or live provider execution.','Positive finite checks establish only their encoded assumptions and supplied source/certificate contracts; physical interpretation, scientific adequacy, independent host authority and universal semantic fidelity remain external obligations.'])
a.write('_notes.json',n);a.report();d=a.read('.json');validate(d);assert d['status']=='complete' and d['analysis_complete']
def link(path,label=None,line=None):return '['+(label or path)+']('+str(ROOT/path).replace('\\','/')+(f':{line}' if line else '')+')'
md=['# Remaining PFP domain: completed scoped audit','',f"Original inventory commit: `{d['source_commit']}`. Scope: **427 files, 2,913,844 bytes**. Final accounting: **426 full body reviews (70,549 lines), one bounded generated-data assessment (6,007 lines), zero pending paths**. This completes only the declared slice; the repository-wide audit remains incomplete.",'',f"The {link('dag/reviews/additional_pfp_domain_remaining.json','JSON report')} is the authoritative per-file/hash/range/claim/control record. {link('dag/reviews/additional_pfp_domain_remaining_read_ledger.json','The durable read ledger')} records incremental body reads; automated parsing is not credited as full reading. {link('dag/reviews/additional_pfp_domain_remaining_final_validation.json','Final reconciliation')} pins this report and confirms all427 original hashes still match frozen scope and inventory.",'','## Mathematical and operational assessment','',
'PFP has reusable finite mechanisms here: exact rational normalization and matrix arithmetic, conditional weighted-L1 primal/dual certificates, source-bound finite lift replay, explicit typed refusals, frozen claim/witness separation, deterministic finite enumeration, and tree-based coboundary repair. Each needs its own premises. The finite lift checker admits its carrier and predicates; bare assertion still has a singleton self-relation. Irreflexivity, distinct vertices, cost grammar, observation map and authority are additional structure, not consequences of the inscription `<>`.',
'',
'The strongest weaknesses occur at certificate boundaries. Several records accept declared success, source hashes or host labels without replaying the claimed computation; some lose operative data during canonicalization. Concrete counterexamples include stale verified receipts, scalar zero-gap checks without feasibility, false exactness after float conversion, unsound sort pruning, phantom stage residuals, missing native-result type checks and unbound summary hashes. Findings are local to the pinned owner and tested input; downstream callers may impose additional restrictions.',
'',
'EIS/PCIV and operadic/normal-form components supply useful schema, provenance, composition and finite relation machinery, but their semantic claims are not licensed by naming alone. Protected-query preservation requires actual source and observation binding. Operadic composition requires carrier/slot laws and cannot inherit them from a generic AST. Role declarations do not authenticate independent observers. Budget, refusal and evidence levels must survive the full call chain.',
'',
'The higher-stage physical vocabulary is particularly conditional. Regge checks accept a supplied closure boolean without holonomy matrices; Hodge checks use Euclidean transpose while ignoring supplied metric matrices; zeta checks trust an exactness flag and a constant coefficient. The cochain solver does perform an exact graph construction, but its positive fundamental-cycle sum is basis-dependent, not the weighted-L1 optimum Phi1 or the first homology of a filled complex. The synthetic hook installs the solver answer directly; it is not a live-model experiment.',
'','## Findings to prioritize','']
for i in [6,10,25,27,28,33,39,42,44,47,49,51,53,65,71,72,80,96,100,102,103,109,114,115,116,117]:
 f=next(x for x in d['findings'] if x['id']==f'PFPDOMAIN-F{i:03}');md.append(f"- **{f['id']}: {f['title']}.** {f['statement']}")
md+=['','## Scope and evidence limits','',
'The panel assessment parses all1000 objects and recomputes content hashes:40 base texts appear25 times each, and25 stored content hashes disagree with current bytes. Fixture labels such as clean proof are not checked Lean proofs or reliable empirical ground truth. No panel text was compiled, and no private grading material was accessed.',
'',
'All143 controls are bounded offline checks on read-vetted owners or explicitly isolated unchanged functions.26 receipt files record runtime and source bindings. A missing NumPy dependency limited the AST/numerical lane; nothing was installed. No broad native builds, retained executable replay, model calls, credentials or private benchmark/answer/seed access occurred. Original sources and historical evidence remain unchanged. Exact details and transformations are in the probe receipts.',
'','## Claims and reusable mechanisms','']
for c in d['claims']:
 md += [f"### {c['id']} — {c['title']}",'',c['statement'],'','Evidence: '+', '.join(link(e['path'],e['path'],e.get('lines',[[None]])[0][0]) for e in c['source_evidence'])+'.','']
md+=['## Complete finding register','']
for f in d['findings']:
 md += [f"### {f['id']} — {f['title']}",'',f['statement'],'','Evidence: '+', '.join(link(e['path'],e['path'],e.get('lines',[[None]])[0][0]) for e in f['source_evidence'])+'.', 'Controls: '+', '.join(f.get('control_ids',[]))+'.', 'Limit: '+f.get('limits','Owner/source assessment only.'),'']
md+=['## Per-file coverage','', '| Original path | SHA256 | Disposition and read ranges |','|---|---|---|']
for r in d['file_reviews']:
 ranges=', '.join(f'{lo}–{hi}' for lo,hi in r['reviewed_lines']) or 'empty body'
 md.append(f"| {link(r['path'])} | `{r['sha256']}` | Full body: {ranges} |")
for r in d['automated_reviews']:md.append(f"| {link(r['path'])} | `{r['sha256']}` | Bounded schema/custody/base-text assessment; not full body |")
md+=['','Every full-file substantive assessment and chunk-level range is retained in JSON. No pending path remains in this declared slice. Broader semantic, physical and repository audit obligations remain open.','']
a.file('.md').write_text('\n'.join(md),encoding='utf8')
validation={'schema':'pfp-domain-audit-final-validation-v1','at_utc':now,'status':'complete_declared_slice','source_commit':d['source_commit'],'scope_sha256':sha(a.SCOPE),'report_sha256':sha(a.file('.json')),'markdown_sha256':sha(a.file('.md')),'read_ledger_sha256':sha(a.file('_read_ledger.json')),'counts':d['scope'],'claims':27,'findings':120,'controls':143,'probe_receipts':len(probe_artifacts),'unique_probe_source_bindings':len(set(source_bindings)),'checks':[{'rule':'original_current_scope_inventory_sha256','status':'all427_match'},{'rule':'full_body_ranges_exact_nonoverlapping','status':'all426_match'},{'rule':'bounded_generated_data_separate','status':'one_explicit_disposition'},{'rule':'claim_finding_source_ranges_and_hashes','status':'validated'},{'rule':'control_ids_unique_and_probes_complete','status':'validated_143'},{'rule':'every_bounded_check_rule_and_status','status':'validated'},{'rule':'pending_scope_paths','status':'none'}],'remaining_unsupported_files':[],'repository_wide_audit_complete':False,'limits':['Final hash/range reconciliation, not a proof of correctness for all sources.','No original source mutation; current bytes compared to pinned original inventory.']}
a.write('_final_validation.json',validation)
print(json.dumps({k:validation[k] for k in ['status','report_sha256','markdown_sha256','claims','findings','controls','unique_probe_source_bindings']}))
