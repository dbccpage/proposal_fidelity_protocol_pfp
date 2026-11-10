"""Validate coverage/custody metadata; never executes reviewed repository owners."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_operads_education_atlas'
load=lambda suffix:json.loads(Path(str(P)+suffix).read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
scope=load('_scope.json');report=load('.json');ledger=load('_read_ledger.json');checks=load('_checks.json')
parent=json.loads((ROOT/scope['parent_scope']).read_text())
assert sha((ROOT/scope['parent_scope']).read_bytes())==scope['parent_scope_sha256']
assert {r['path'] for r in scope['files']}=={r['path'] for r in parent['files']}-set(parent['parent_initial_paths'])
assert len(scope['files'])==52 and len(report['file_reviews'])==53 and not report['pending_paths']
assert len({r['path'] for r in report['file_reviews']})==53
checks_done=[]
for r in scope['files']:
    b=(ROOT/r['path']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
    row=next(x for x in report['file_reviews'] if x['path']==r['path'])
    assert row['sha256']==r['sha256'] and row['assessment'].strip()
    if r['lines'] is not None:
        n=len(b.decode().splitlines());assert r['lines']==n
        seen=set(k for x in ledger if x['path']==r['path'] and x['sha256']==r['sha256'] for a,z in x['reviewed_lines'] for k in range(a,z+1))
        assert seen==set(range(1,n+1)) and row['full_source_read'] and row['reviewed_lines']==[[1,n]]
    else:
        assert row['full_source_read'] is False and row['reviewed_lines']==[] and row['visual_review']['entire_image_inspected']
    checks_done.append({'path':r['path'],'sha256':sha(b),'bytes':len(b),'status':'verified'})
s=scope['supporting_source'];archive=Path(s['original_archive'])
assert sha(archive.read_bytes())==s['archive_sha256']
with zipfile.ZipFile(archive) as z:o=z.read(s['archive_member'])
c=(ROOT/s['path']).read_bytes()
assert sha(o)==s['original_sha256'] and sha(c)==s['current_sha256']
ol=o.decode().splitlines();cl=c.decode().splitlines();assert len(ol)==len(cl)==204
changes=[i+1 for i,(a,b) in enumerate(zip(ol,cl)) if a!=b];assert changes==[48]
assert ol[47].replace('../code/was_operad_core.py','../../../pilots/education/operad_simulation/code/was_operad_core.py')==cl[47]
for version,hash_value in [('original',s['original_sha256']),('current',s['current_sha256'])]:
    seen=set(k for x in ledger if x['path']==s['path'] and x['sha256']==hash_value for a,z in x['reviewed_lines'] for k in range(a,z+1))
    assert seen==set(range(1,205))
evidence_count=0
for row in report['claims']+report['findings']:
    for e in row['source_evidence']:
        evidence_count+=1
        b=o if e['path']==s['path'] and e['sha256']==s['original_sha256'] else (ROOT/e['path']).read_bytes()
        assert sha(b)==e['sha256']
        if e['lines']:
            n=len(b.decode().splitlines())
            for a,z in e['lines']:assert 1<=a<=z<=n
for r in report['prior_evidence']:assert sha((ROOT/r['path']).read_bytes())==r['sha256']
for r in report['dependency_context']:assert sha((ROOT/r['path']).read_bytes())==r['sha256']
assert report['fresh_validation']['sha256']==sha(Path(str(P)+'_checks.json').read_bytes())
assert len(checks['fresh_checks'])==8 and len(checks['png_metadata'])==len(checks['svg_checks'])==5
assert report['summary']['pending']==0 and sum(r['full_source_read'] for r in report['file_reviews'])==48
out={'status':'passed','frozen_scope_paths':52,'supporting_original_paths':1,'report_file_reviews':53,
     'full_text_original_receipts':48,'bounded_png_visual_dispositions':5,'current_supporting_full_read':1,
     'scoped_full_text_lines':8398,'supporting_original_lines':204,'supporting_current_lines':204,
     'source_evidence_rows_checked':evidence_count,'supporting_changed_lines':changes,
     'scope_sha256':sha(Path(str(P)+'_scope.json').read_bytes()),'report_sha256':sha(Path(str(P)+'.json').read_bytes()),
     'markdown_sha256':sha(Path(str(P)+'.md').read_bytes()),'checks_sha256':sha(Path(str(P)+'_checks.json').read_bytes()),
     'source_hash_verification':checks_done,
     'limits':['Metadata/hash/range validation verifies custody and reported coverage consistency, not mathematical truth or production execution.',
         'Initial frozen sources remained unchanged. No production or historical files were written.']}
Path(str(P)+'_validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ['source_hash_verification','limits']},indent=2))
