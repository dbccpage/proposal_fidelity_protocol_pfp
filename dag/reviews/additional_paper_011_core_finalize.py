import sys,json,datetime,hashlib,subprocess
sys.dont_write_bytecode=True
import additional_paper_011_core_audit as a
scope=a.read('_scope.json');initial=a.read('_initial_reconciliation.json')
inventory=json.loads((a.ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))
iby={r['path']:r for r in inventory['files']}
ledger=a.read('_read_ledger.json');autos=a.read('_automated.json');notes=a.read('_notes.json')
assert len(scope['files'])==51 and len(ledger)==50 and len(autos)==1
assert a.sha(a.file('_scope.json'))==initial['scope_sha256']
assert a.sha(a.ROOT/'dag/file_inventory.json')==initial['inventory_sha256']
reviewed={r['path']:r for r in ledger+autos};assert len(reviewed)==51
rows=[]
for r in scope['files']:
    p=a.ROOT/r['path'];digest=a.sha(p);raw=p.read_bytes();end=len(raw.decode('utf-8-sig').splitlines());v=reviewed[r['path']]
    assert digest==r['sha256']==iby[r['path']]['sha256']==v['sha256']
    if r['path'].endswith('.py'):
        assert v['full_source_read'] is True and v['reviewed_lines']==[[1,end]] and v['assessment']
    else:
        assert v['full_source_read'] is False
        assert all(isinstance(c,str) or c.get('rule') and c.get('status') for c in v['checks'])
    rows.append({'path':r['path'],'sha256':digest,'bytes':len(raw),'lines':end,'disposition':'full_source_read' if v['full_source_read'] else 'bounded_data_assessment'})
for c in notes['controls']:assert a.sha(a.ROOT/c['path'])==c['sha256']
for collection in ('claims','findings'):
    ids=[r['id'] for r in notes[collection]];assert len(ids)==len(set(ids))
    for item in notes[collection]:
        assert item['statement'] and item['evidence']
        for e in item['evidence']:
            assert a.sha(a.ROOT/e['path'])==e['sha256']
            last=len((a.ROOT/e['path']).read_text(encoding='utf-8-sig').splitlines())
            assert 1<=e['lines'][0]<=e['lines'][1]<=last
head=subprocess.run(['git','rev-parse','HEAD'],cwd=a.ROOT,check=True,capture_output=True,text=True).stdout.strip();assert head==scope['source_commit']
rec={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':head,'scope_sha256':a.sha(a.file('_scope.json')),'inventory_sha256':a.sha(a.ROOT/'dag/file_inventory.json'),'initial_coverage_sha256':initial['coverage_sha256'],'files':rows,'file_count':len(rows),'bytes':sum(r['bytes'] for r in rows),'all_original_hashes_match':True,'all_full_read_ranges_complete':True,'all_automated_rules_have_status':True,'all_control_artifacts_match':True,'claim_finding_source_hashes_and_ranges_valid':True,'repository_wide_audit_complete':False}
a.write('_final_reconciliation.json',rec)
a.report();report=a.read('.json')
report['repository_wide_audit_complete']=False
report['completion_scope']='Only the frozen51-file Paper011core partition; zero pending within this partition.'
report['final_reconciliation']={'path':'dag/reviews/additional_paper_011_core_final_reconciliation.json','sha256':a.sha(a.file('_final_reconciliation.json'))}
report['test_summary']={'pytest_cases':163,'passed':162,'failed':1,'failure_finding':'P011CORE-F08','runtime':'Python3.14.2, available-runtime focused checks; not pinnedPython3.12 reproduction','independent_synthetic_boundary_controls':10,'data_arithmetic_controls':2}
report['dependency_boundaries']=[
 {'dependency':'Original engine/Git object archives, historical provider traces and findings inventories','status':'not_consulted_or_executed','limit':'Core source references and test expectations are not authentication of those bytes or runs.'},
 {'dependency':'Rust/Lean/native mathematics and compiled binary source linkage','status':'not_executed','limit':'Read wrappers and synthetic transport controls only; native partition separately owned.'},
 {'dependency':'Paper011release support helpers','status':'parent_owned','limit':'Release tests fully read here; parent owns support-source review and probes.'},
 {'dependency':'Sealed QM key/seed/answer, provider credentials and private benchmarks','status':'not_accessed','limit':'No sealed data or private benchmark payload read/solved, no provider/network access.'}
]
report['claims'][0]['dependencies']=['Trusted fixed external manifest digest','Stable regular-file snapshot','Truthful inventory assumptions; Git content bridge weaknessF01 retained']
report['claims'][1]['dependencies']=['Uniform choice among labeled k-subsets','Exactly s successes among n outcomes','Strict integer bounds1<=k<=n']
report['claims'][2]['dependencies']=['Natural-number interpretation','Stated thresholds40/70and50/2600','Original-case source binding and Lean replay remain external obligations']
assert not report['remaining_unsupported_files'];a.write('.json',report)
md=['# Paper011 core audit','',f'Completed only the frozen **51-file partition** at `{head}`: **50 full source reads /16,957lines**, **1 separately parsed data fixture**, **0 pending in this slice**. The repository-wide audit remains incomplete. All51current SHA256values match the original inventory;816,406source bytes were preserved.','',
 'All source bodies were read in numbered ranges before full-read credit. Per-file hashes, complete read ranges and substantive assessments are in `additional_paper_011_core.json`; automated parsing remains in `automated_reviews` with `full_source_read:false`. Scope and final reconciliation are separate immutable-input records.','',
 'The runners often preserve useful boundaries: finite demonstrations versus empirical claims, accepted refusal/negative labels versus positive capability, same-input native certificate replay versus topology labels, and historical hash integrity versus provider authenticity. The remaining defects below limit current execution or the advertised custody contracts.','',
 '## Findings','']
for f in report['findings']:
    md += ['### '+f['id'],'',f['statement'],'','Evidence: '+ '; '.join('`'+e['path']+'` L'+str(e['lines'][0])+'–'+str(e['lines'][1])+' SHA256 `'+e['sha256']+'`' for e in f['evidence'])+'.','', 'Limit: '+f['limits'],'']
md += ['## Validation and mathematical limits','',
 '**163focused pytest cases:162passed,1failed.** The failure is the existing positive catalog-discovery regression and independently confirmsF08. No source repair was made. The three batches are31/31,17/17and114/115. Ten independent synthetic boundary controls cover content/Git binding, census duplication, AST semantics, stale-variable failure, exact subset probability, catalog ordering, dialogue parsing and undeclared process forwarding. All actual native calls in the selected tests were stubbed.','',
 'The C041JSONfixture remains a bounded data disposition. Its false universal target has counterexample39+39=78; its true target follows from k<=49and k²<=2401<2600. The50admissible natural kvalues were checked exactly. Candidate Lean syntax was inspected but no kernel was run and original case hash references were not independently reauthenticated.','',
 'All checks used the available workspace Python3.14.2, not the declared Python3.12reproduction profile. No providers, paid models, credentials, private benchmark payloads, sealed QM key/seed/answer, broad native builds or unreviewed binary execution were used. Historical runner source was read; referenced historical data was not opened or executed. Parent-owned support/native/history partitions retain separate evidence.','',
 'Control artifacts:']
md += ['','| Artifact | SHA256 |','|---|---|']
md += ['| `'+c['path']+'` | `'+c['sha256']+'` |' for c in report['controls']]
md += ['','## Per-file dispositions','','| Path | Disposition | Lines | SHA256 |','|---|---|---:|---|']
md += ['| `'+r['path']+'` | '+r['disposition']+' | '+str(r['lines'])+' | `'+r['sha256']+'` |' for r in rows]
a.file('.md').write_text('\n'.join(md)+'\n',encoding='utf8')
artifacts=[a.file(s) for s in ['.json','.md','_scope.json','_read_ledger.json','_automated.json','_notes.json','_initial_reconciliation.json','_final_reconciliation.json','_custody_pytest.txt','_boundary_pytest.txt','_final_pytest.txt']]
artifacts += [a.ROOT/c['path'] for c in notes['controls']]
a.write('_completion_receipt.json',{'review_id':a.PREFIX.name,'source_commit':head,'scope':report['scope'],'findings':len(report['findings']),'claims':len(report['claims']),'test_summary':report['test_summary'],'artifact_sha256':{p.relative_to(a.ROOT).as_posix():a.sha(p) for p in artifacts},'repository_wide_audit_complete':False,'source_edits':False,'authority':'Bounded audit evidence, not mathematical or historical authentication outside stated dependencies.'})
print(json.dumps({'scope':report['scope'],'findings':len(report['findings']),'claims':len(report['claims']),'bytes':rec['bytes'],'hashes_match':True,'test_summary':report['test_summary'],'report_sha256':a.sha(a.file('.json'))}))
