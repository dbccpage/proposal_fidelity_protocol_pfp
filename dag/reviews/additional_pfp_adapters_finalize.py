"""Validate this lane's receipts and reconcile original bytes; no original writes."""
import sys, json, datetime, subprocess
sys.dont_write_bytecode=True
import additional_pfp_adapters_audit as a

s=a.read('_scope.json');r=a.read('.json');notes=a.read('_notes.json')
inv=json.loads((a.ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))
iby={x['path']:x for x in inv['files']}
expected={x['path']:x for x in s['files']}
original=s['files']+s['excluded_already_fully_reviewed']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.ROOT,text=True).strip()
assert head==s['source_commit']==inv['local_head']=='8050c66900899771766f33e8f5fdd200b7dd9120'
reconciled=[]
for x in original:
    digest=a.sha(a.ROOT/x['path'])
    assert digest==x['sha256']==x['current_sha256']==iby[x['path']]['sha256']
    reconciled.append({'path':x['path'],'sha256':digest,'status':'matches_frozen_original_inventory'})
full=r['file_reviews'];data=r['automated_reviews']
assert len(full)==155 and len(data)==138
assert {x['path'] for x in full+data}==set(expected)
assert len({x['path'] for x in full+data})==293
for x in full:
    assert x['full_source_read'] is True and x['assessment'].strip()
    assert x['sha256']==expected[x['path']]['sha256']
    end=len((a.ROOT/x['path']).read_text(encoding='utf-8-sig').splitlines())
    assert x['reviewed_lines']==([[1,end]] if end else [])
checks=0
for x in data:
    assert x['full_source_read'] is False and x['reviewed_lines']==[] and x['assessment'].strip()
    assert x['sha256']==expected[x['path']]['sha256']
    assert x['assessment_kind']=='bounded_schema_specific_data_assessment'
    for c in x['checks']:
        assert isinstance(c,str) or (isinstance(c,dict) and c.get('rule') and c.get('status'))
        checks+=1
for item in notes['findings']+notes['claims']:
    assert item['source_ranges']
    for e in item['source_ranges']:
        assert e['sha256']==expected[e['path']]['sha256']
        lo,hi=e['lines'];end=len((a.ROOT/e['path']).read_text(encoding='utf-8-sig').splitlines())
        assert 1<=lo<=hi<=end,(item['id'],e)
assert len(notes['findings'])==26 and len(notes['claims'])==2
assert r['remaining_unsupported_files']==[] and r['scope']['pending']==0
assert a.read('_data_summary.json')['retained_case_mismatches']==[]
assert a.read('_data_summary.json')['stage_cases']==1033
for x in data:
    for c in x['checks']:
        if c['rule']=='catalog_fixture_bindings':assert len(c['mismatches'])==1
        if c['rule']=='meron_wire_fixture_structure':assert c['lattice_site_count_matches'] is True
artifacts=[]
for suffix in ['_scope.json','_read_ledger.json','_automated.json','_data_summary.json','_core_probe.py','_core_probes.json','_stage_probe.py','_stage_probes.json','_stage_probe2.py','_stage_probes2.json','_ledger_probe.py','_ledger_probes.json','_bridge_probe.py','_bridge_probes.json','_data.py','_audit.py','_checkpoint13.py']:
    p=a.file(suffix)
    artifacts.append({'path':p.relative_to(a.ROOT).as_posix(),'sha256':a.sha(p)})
recon={'status':'complete_for_frozen_adapter_slice','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_head':head,'original_files_checked':len(reconciled),'all_frozen_hashes_match':True,'files':reconciled,'receipt_checks':[{'rule':'exact_scope_partition','status':'verified','full_source_reads':155,'bounded_data_assessments':138,'pending':0},{'rule':'full_source_ranges_and_hashes','status':'verified','lines':28647},{'rule':'automated_rule_status_schema','status':'verified','checks':checks},{'rule':'finding_claim_evidence_ranges','status':'verified','findings':26,'claims':2},{'rule':'retained_fixture_replay','status':'observed','cases':1033,'mismatches':0,'limits':'Supplied expected labels, regression consistency only.'}], 'evidence_artifacts':artifacts,'limits':['Only this frozen adapter prefix reconciled; no repository-wide pristine-state claim.','Data parsing is not full source reading.','No original-source modifications or live/provider/native execution performed by this lane.','The original every-file audit remains incomplete.']}
a.write('_reconciliation.json',recon)
notes['reconciliation']={'path':'dag/reviews/additional_pfp_adapters_reconciliation.json','sha256':a.sha(a.file('_reconciliation.json')),'original_hashes_checked':296,'all_match':True}
notes['controls']=[{**c,'sha256':a.sha(a.ROOT/c['path'])} for c in notes['controls']]
a.write('_notes.json',notes);a.report()
r=a.read('.json')
md=['# PFP adapters: frozen remaining-path audit','',
    'Completed the declared adapter slice at original HEAD `'+head+'`. The repository-wide every-file audit remains incomplete.','',
    '| Scope disposition | Files |','|---|---:|','| Original candidates | 296 |','| Previously full, excluded without duplicate credit | 3 |','| Newly read full source bodies | 155 |','| Separately parsed JSON artifacts | 138 |','| Pending in this slice | 0 |','',
    'The full reads cover 28,647 lines: 154 Python files and the complete 8,354-line crosswalk. Every receipt has the original path, SHA-256, exact read range and substantive assessment in [the report](additional_pfp_adapters.json). Data records carry `full_source_read: false`; schema parsing, reference checks and supplied-case replay are not promoted to source reading.','',
    'All 296 current original hashes still match the frozen inventory. The [reconciliation](additional_pfp_adapters_reconciliation.json) validates the scope partition, read ranges, finding evidence and every automated `rule`/`status` field. The frozen exclusions and coverage snapshot are in [the scope](additional_pfp_adapters_scope.json).','',
    '## Evidence and limits','',
    'Independent small controls include finite sign-graph enumeration, exact characteristic-polynomial comparisons, malformed injected native envelopes, representation round trips, ledger boundary cases, stage countermodels and a synthetic retained-profile bridge. The five control artifacts are named and hashed in the report. The bridge and two unavailable adapter imports required explicitly documented unchanged-source AST extraction with narrow dependency stubs; these controls do not establish production dependency or canonicalization correctness.','',
    'Separately, all 1,033 retained stage cases replayed with their supplied expected labels. That is regression consistency, not independent ground truth. Schema-specific data checks found one stale catalog digest. The data parser was corrected during review to recognize the four-dimensional lattice key names before finalizing those bounded dimension checks.','',
    'Native kernels, live models, providers, private benchmarks, credentials and linked sealed seed/answer material were not used. No original source or historical receipt was changed. Source-body observations about sandboxing, runtime availability and accounting are scoped to the code read; broad execution claims are not made.','',
    '## Conditional mathematical claims','']
for c in r['claims']:md.append('- **'+c['id']+'**: '+c['claim']+' '+c['limits'])
md+=['','The crosswalk repeatedly declares draft status, no authority, and candidate syntax. Its listed preservation laws are conditional obligations requiring declared models and independent checkers; reading it does not establish any external derivation or transfer.','', '## Findings','', 'Findings distinguish unsound boundary behavior, insufficient assumptions, deliberately incomplete certificate policies and malformed-input failures. Each has exact source evidence and control references in the JSON.','', '| ID | Finding |','|---|---|']
for f in r['findings']:md.append('| '+f['id']+' | '+f['claim'].replace('|','\\|')+' |')
md+=['','The adapter slice is disposition-complete. The 138 data artifacts remain bounded assessments, and larger repository coverage is still pending.','']
a.file('.md').write_text('\n'.join(md),encoding='utf8')
print(json.dumps({'status':r['status'],'scope':r['scope'],'findings':len(r['findings']),'claims':len(r['claims']),'automated_checks':checks,'original_hashes_match':len(reconciled)}))
