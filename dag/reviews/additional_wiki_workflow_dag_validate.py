"""Final own-report/hash/range checks; never mutates original sources."""
from pathlib import Path
import ast
import hashlib
import json
ROOT=Path(__file__).resolve().parents[2]
PREFIX='dag/reviews/additional_wiki_workflow_dag'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
r=read(PREFIX+'.json');s=read(PREFIX+'_scope.json');c=read(PREFIX+'_checks.json');ledger=read(PREFIX+'_read_ledger.json')
assert len(s['files'])==len(r['file_reviews'])==1
f=r['file_reviews'][0]; original=s['files'][0]
assert f['path']==original['path'] and f['sha256']==original['sha256']==digest(f['path'])
assert f['bytes']==original['bytes']==(ROOT/f['path']).stat().st_size
assert f['line_count']==len((ROOT/f['path']).read_text(encoding='utf-8').splitlines())==1669
assert f['full_source_read'] is True and f['reviewed_lines']==[[1,1669]]
covered=set()
for x in ledger:
    assert x['path']==f['path'] and x['sha256']==f['sha256'] and x['full_output']
    for a,b in x['reviewed_lines']:
        assert 1<=a<=b<=1669
        covered.update(range(a,b+1))
assert covered==set(range(1,1670))
assert len(r['claims'])==4 and len(r['findings'])==10 and len(r['family_assessments'])==49
ids=[x['id'] for x in r['claims']+r['findings']];assert len(ids)==len(set(ids))
for row in r['claims']+r['findings']+r['family_assessments']:
    for e in row['source_evidence']:
        assert e['path']==f['path'] and e['sha256']==f['sha256']
        for a,b in e['lines']: assert 1<=a<=b<=1669
for context in r['comparison_reviews']:assert context['sha256']==digest(context['path'])
assert r['validation']['sha256']==digest(PREFIX+'_checks.json')
assert r['scope_manifest_sha256']==digest(PREFIX+'_scope.json')
assert c['family_count']==49 and c['perturbation_count']==46 and c['graph']['edge_count']==75
assert c['graph']['wiki_vs_registry_edges_equal'] and c['graph']['wiki_vs_prose_edges_equal'] and c['graph']['acyclic']
assert not c['graph']['node_differences'] and not c['local_target_checks']['missing']
assert len(r['remaining_work'])==0
helpers=[]
for p in sorted((ROOT/'dag/reviews').glob('additional_wiki_workflow_dag_*.py')):
    ast.parse(p.read_text(encoding='utf-8'),filename=str(p));helpers.append(str(p.relative_to(ROOT)).replace('\\','/'))
result={'status':'PASS','original_scope_paths':1,'full_body_reads':1,'reviewed_lines':1669,'pending_paths':0,
        'families':49,'claims':4,'findings':10,'comparison_report_hashes_verified':len(r['comparison_reviews']),
        'source_sha256':f['sha256'],'report_sha256':digest(PREFIX+'.json'),'markdown_sha256':digest(PREFIX+'.md'),
        'checks_sha256':digest(PREFIX+'_checks.json'),'helper_syntax_checked':helpers,
        'validation_ceiling':'Hash/range/schema/graph consistency and documented finite controls only; not project execution or historical provider authentication.'}
(ROOT/(PREFIX+'_validation.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
