"""Offline audit bookkeeping; never infer full reads from parsing or hashes."""
import collections
import hashlib
import json
import re
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ROOT / 'dag/reviews/additional_challenges_041_050'
RULE = r'^workflows/tasks/certified_challenges/(?:c0(?:4[1-9]|50)_[^/]+/|test_c0(?:4[1-9]|50)[^/]*\.py$)'
def file(suffix): return PREFIX.with_name(PREFIX.name + suffix)
def read(suffix): return json.loads(file(suffix).read_text(encoding='utf-8'))
def write(suffix, data): file(suffix).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
def freeze():
    inv = json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf-8'))
    coverage = json.loads((ROOT/'dag/reviews/coverage.json').read_text(encoding='utf-8'))
    records = [dict(r) for r in inv['files'] if re.match(RULE, r['path'])]
    for r in records:
        p=ROOT/r['path']; r['current_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        r['hash_matches_inventory']=r['current_sha256']==r['sha256']
    write('_scope.json', {'source_commit': inv['local_head'], 'scope_rule': RULE, 'files': records,
          'coverage_snapshot_sha256': hashlib.sha256((ROOT/'dag/reviews/coverage.json').read_bytes()).hexdigest(),
          'coverage_snapshot_top_keys': list(coverage) if isinstance(coverage,dict) else None,
          'coverage_reconciliation': 'No prior source reads are inherited; every scoped path starts pending in this audit.',
          'counts': dict(collections.Counter('source' if r['path'].endswith(('.py','.md')) else 'data' for r in records))})
    write('_read_ledger.json', [])
    write('_notes.json', {'family_assessments': [], 'primary_sources': []})
    print(len(records), 'paths;', sum(not r['hash_matches_inventory'] for r in records), 'hash mismatches')
def show(family, selectors):
    rows=read('_scope.json')['files']
    for r in rows:
        p=r['path']
        if '/'+family+'_' not in p and '/test_'+family not in p: continue
        if not p.endswith(('.py','.md')): continue
        if selectors and not any(s in p for s in selectors): continue
        print('\nFILE '+p+' SHA256 '+r['sha256'])
        for n,line in enumerate((ROOT/p).read_text(encoding='utf-8-sig').splitlines(),1): print(str(n)+':'+line)
def record(family, assessments):
    rows=read('_scope.json')['files']; ledger=read('_read_ledger.json'); existing={r['path'] for r in ledger}
    for key,assessment in assessments.items():
        matches=[r for r in rows if ('/'+family+'_' in r['path'] or '/test_'+family in r['path']) and r['path'].endswith(key)]
        assert len(matches)==1, (key,len(matches))
        r=matches[0]; assert r['path'] not in existing
        n=len((ROOT/r['path']).read_text(encoding='utf-8-sig').splitlines())
        ledger.append({'path':r['path'],'sha256':r['sha256'],'full_source_read':True,'reviewed_lines':[[1,n]] if n else [],'assessment':assessment})
    write('_read_ledger.json', ledger)
def report():
    scope=read('_scope.json'); ledger=read('_read_ledger.json'); notes=read('_notes.json')
    autos=[]
    for p in sorted(PREFIX.parent.glob(PREFIX.name+'_c???_automated.jsonl')):
        autos.extend(json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line)
    for row in autos:
        for check in row.get('checks',[]):
            if isinstance(check,dict):
                check.setdefault('status','parsed' if check.get('rule') in ('json_structure','budget_configuration','lean_case_envelope') else 'observed')
    done={r['path'] for r in ledger+autos}; assert len(done)==len(ledger)+len(autos)
    pending=[{'path':r['path'],'sha256':r['sha256'],'status':'pending_source_read' if r['path'].endswith(('.md','.py')) else 'pending_data_disposition'} for r in scope['files'] if r['path'] not in done]
    findings=[{**f,'family':a['family']} for a in notes['family_assessments'] for f in a.get('findings',[])]
    validation={'offline_only':True,'source_edits':0,'provider_calls':0,
                'scope_pin':scope['source_commit'],
                'coverage_snapshot_sha256':scope['coverage_snapshot_sha256'],
                'coverage_reconciliation':scope['coverage_reconciliation'],
                'data_assessment_counts':dict(collections.Counter(r['status'] for r in autos)),
                'retained_data_summary':notes.get('retained_data_summary',{})}
    if file('_reconciliation.json').exists(): validation['final_reconciliation']=read('_reconciliation.json')
    result={'review_id':PREFIX.name,'status':'complete' if not pending else 'in_progress','source_commit':scope['source_commit'],
            'scope_rule':RULE,'scope':{'files':len(scope['files']),'full_source_reads':len(ledger),'full_source_lines':sum(b-a+1 for r in ledger for a,b in r['reviewed_lines']),'automated_files':len(autos),'pending':len(pending)},
            'completion_basis':'Every frozen path has a full source-read receipt or a separately labelled bounded data disposition; this is not full mathematical proof replay of every data artifact.',
            'family_assessments':notes['family_assessments'],'claims':notes.get('claims',[]),'findings':findings,'file_reviews':ledger,'automated_reviews':autos,'remaining_unsupported_files':pending,
            'primary_sources':notes.get('primary_sources',[]),'validation':validation,'limitations':['Full source reads and bounded parsed data dispositions are distinct.','This slice does not complete the wider repository audit.','Owner agreement and retained historical receipts do not establish broader mathematical or provider claims.']}
    write('.json', result)
    md=['# C041–C050 mathematical audit ('+result['status']+')','',f"Pinned source `{scope['source_commit']}`; {len(ledger)} full source reads ({result['scope']['full_source_lines']:,} lines), {len(autos)} bounded data dispositions, {len(pending)} pending paths, {len(findings)} findings.",'','Original sources and historical receipts remain unchanged. No providers or sealed benchmark seeds/answers were accessed.','',result['completion_basis'],'','The wider repository audit remains incomplete.','']
    for a in notes['family_assessments']:
        math_text=a['math']
        if a['family'].upper()=='C048' and notes.get('primary_sources'):
            math_text+=' [Official PARI qfsolve documentation]('+notes['primary_sources'][0]['url']+').'
        md += ['## '+a['family'],'',math_text,'',a.get('data',''), '']
        md += ['- '+f['id']+': '+f['claim'] for f in a.get('findings',[])]
        md += ['', 'Limits: '+' '.join(a.get('limits',[])), '']
    md += ['The JSON and companion ledgers retain exact paths, SHA-256 pins, source ranges, controls, and explicit pending scope.']
    for source in notes.get('primary_sources',[]):md += ['', '['+source.get('title','Official PARI documentation')+']('+source['url']+'): '+source['scope']]
    file('.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps(result['scope']))
if __name__=='__main__':
    if sys.argv[1]=='freeze': freeze(); report()
    elif sys.argv[1]=='show': show(sys.argv[2],sys.argv[3:])
    elif sys.argv[1]=='report': report()
