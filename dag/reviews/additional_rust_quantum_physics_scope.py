"""Freeze pending original-inventory quantum owners; hash/parse is not semantic review."""
import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics'
ip=R/'dag/file_inventory.json';cp=H/'coverage.json'
i=json.loads(ip.read_text());c=json.loads(cp.read_text());coverage={x['path']:x for x in c['files']}
rows=[];excluded=[]
for x in i['files']:
 if not x['path'].startswith('code/rust/core_quantum_physics/'):continue
 if coverage[x['path']]['substantive_status']=='full_text_source_review_recorded':excluded.append(x['path']);continue
 p=R/x['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==x['sha256'],x['path']
 rows.append({'path':x['path'],'sha256':x['sha256'],'bytes':len(raw),'lines':len(raw.decode('utf-8').splitlines()),'previous_coverage':coverage[x['path']]['substantive_status'],'original_git_blob':x['head_git_oid']})
d={'source_commit':i['local_head'],'inventory_sha256':hashlib.sha256(ip.read_bytes()).hexdigest(),'coverage_sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'scope':'Original inventoried pending files under core_quantum_physics only; no private benchmark or new pilot corpus. Configuration/source/test bodies require explicit semantic assessment.','excluded_prior_full_reads':excluded,'files':rows}
out=H/(P+'_scope.json');assert not out.exists();out.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'files':len(rows),'lines':sum(x['lines']for x in rows),'bytes':sum(x['bytes']for x in rows),'excluded':excluded,'largest':sorted(rows,key=lambda x:x['lines'],reverse=True)[:12]},indent=2))
