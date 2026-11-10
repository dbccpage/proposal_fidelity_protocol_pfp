"""Read only the1164 corresponding public outer-ZIP members; no extraction."""
import collections,hashlib,json,pathlib,zipfile
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_paper_011_recreated_receipts';B='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/';AR=B+'021_recreated_demos_and_proposal_fidelity_evidence_2026-10-02.zip';PREFIX='021_recreated_demos_and_proposal_fidelity_evidence/'
scope=json.loads((H/(P+'_scope.json')).read_text());files={x['path']:x for x in scope['files']};checks=json.loads((H/(P+'_population_checks.json')).read_text());data={};rows=[]
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
with(R/AR).open('rb')as stream:archive_sha=hashlib.file_digest(stream,'sha256').hexdigest()
assert archive_sha=='8bf43405313439d05383552f1281eaec96442dac7eb733134bcae1394863d6b3'
with zipfile.ZipFile(R/AR)as z:
 names=set(z.namelist());used=set()
 for path,x in files.items():
  member=PREFIX+path[len(B):].replace('/demo_adversary_tribunal/','/demo_woland_tribunal/')
  assert member in names and member not in used;used.add(member);raw=z.read(member);data[path]=raw;current=(R/path).read_bytes();assert sha(current)==x['sha256']
  rows.append({'path':path,'sha256':x['sha256'],'archive_member':member,'archive_member_sha256':sha(raw),'archive_bytes':len(raw),'raw_equal':raw==current,'LF_equal':raw.replace(b'\r\n',b'\n')==current.replace(b'\r\n',b'\n')})
 assert len(used)==len([n for n in names if'/docs/recreated_run/'in n])==1164
def obj(path):return json.loads(data[path])
def map_recorded(path):
 s=path.replace('\\','/');marker='021_recreated_demos_and_proposal_fidelity_evidence/'
 if marker in s:s=B+s.split(marker,1)[1]
 else:
  marker='011_recreated_demos_and_proposal_fidelity_evidence/'
  if marker in s:s=B+s.split(marker,1)[1]
 return s.replace('/demo_woland_tribunal/','/demo_adversary_tribunal/')
leaves=[];batches=[];matrices=[]
for path in files:
 name=pathlib.PurePosixPath(path).name
 if name not in {'recreation_receipt.json','batch_receipt.json'}and not name.startswith('coverage_matrix_'):continue
 d=obj(path);entry={'path':path,'recorded_self_digest':d['receipt_sha256'],'computed_self_digest':sha(canon({k:v for k,v in d.items()if k!='receipt_sha256'}))};entry['self_digest_matches']=entry['computed_self_digest']==entry['recorded_self_digest']
 parent=str(pathlib.PurePosixPath(path).parent)
 if name=='recreation_receipt.json':
  artifacts=[]
  for rel,pin in d['artifacts_sha256'].items():
   target=parent+'/'+rel;artifacts.append({'path':target,'expected':pin,'archive_sha256':sha(data[target])if target in data else None,'matches':target in data and sha(data[target])==pin})
  job=obj(parent+'/job.json');worker=parent+'/worker_result.json';entry.update(artifact_bindings=artifacts,job_capability_digest_matches=sha(canon(job['capability']))==d['capability_sha256'],job_row_digest_matches=sha(canon(job['row']))==d['catalog_row_sha256'],worker_result_matches=obj(worker)==d['result']if worker in data else None);leaves.append(entry)
 elif name=='batch_receipt.json':batches.append(entry)
 else:
  rb=[];cb=[]
  for row in d['rows']:
   target=map_recorded(row['receipt_path']);rb.append({'id':row['id'],'target':target,'matches':target in data and sha(data[target])==row['receipt_bytes_sha256']})
  for row in d['batch_closures']:
   target=map_recorded(row['path']);cb.append({'target':target,'matches':target in data and sha(data[target])==row['sha256']})
  entry.update(row_bindings=rb,batch_bindings=cb);matrices.append(entry)
summary={'mapped_members':len(rows),'raw_equal':sum(x['raw_equal']for x in rows),'LF_equal':sum(x['LF_equal']for x in rows),'leaf_self_digests':dict(collections.Counter(str(x['self_digest_matches'])for x in leaves)),'leaf_artifact_bindings':dict(collections.Counter(str(y['matches'])for x in leaves for y in x['artifact_bindings'])),'job_capability_digests':dict(collections.Counter(str(x['job_capability_digest_matches'])for x in leaves)),'worker_equality':dict(collections.Counter(str(x['worker_result_matches'])for x in leaves)),'batch_self_digests':dict(collections.Counter(str(x['self_digest_matches'])for x in batches)),'matrix_self_digests':dict(collections.Counter(str(x['self_digest_matches'])for x in matrices)),'matrix_row_bindings':dict(collections.Counter(str(y['matches'])for x in matrices for y in x['row_bindings'])),'matrix_batch_bindings':dict(collections.Counter(str(y['matches'])for x in matrices for y in x['batch_bindings']))}
out={'archive':AR,'archive_sha256':archive_sha,'files':rows,'original_leaf_checks':leaves,'original_batch_checks':batches,'original_matrix_checks':matrices,'summary':summary,'limits':'Corresponding public scope members only. Archive hash matches prior support review. Original archive representations are not new execution/authenticity evidence. Current mismatch remains a current-edition replay limitation; original matching bytes remain recoverable without repinning or overwriting originals. No extraction, private file access or binary/command execution.'}
(H/(P+'_archive_comparison.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(summary,indent=2))
