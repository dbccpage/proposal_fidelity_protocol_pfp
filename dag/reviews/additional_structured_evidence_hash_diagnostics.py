"""Separate retained content drift from CRLF checkout conversion using pinned Git blobs."""
import collections
import hashlib
import json
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
PREFIX = ROOT / 'dag/reviews/additional_structured_evidence'
inv = {r['path']:r for r in json.loads((ROOT/'dag/file_inventory.json').read_text('utf-8'))['files']}
refs = [json.loads(line) for line in pathlib.Path(str(PREFIX)+'_references.jsonl').read_text('utf-8').splitlines()]
selected = {}
for r in refs:
    if r['status'] == 'mismatch':
        key = (r['target'],r['declared_sha256'].removeprefix('sha256:').lower(),r['normalization'],r.get('declared_size_bytes'))
        selected.setdefault(key, set()).add(r['kind'])
for p in inv:
    if p.startswith('pfp/infrastructure/tower_evidence/level_engine/v2/bundles/') and len(pathlib.PurePosixPath(p).stem)==64:
        selected.setdefault((p,pathlib.PurePosixPath(p).stem,'RAW',None),set()).add('tower_content_filename')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


git = subprocess.Popen([shutil.which('git'),'cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
blobs = {}


def pinned_blob(oid):
    if oid in blobs:
        return blobs[oid]
    git.stdin.write((oid+'\n').encode('ascii'));git.stdin.flush()
    header = git.stdout.readline().decode('ascii').strip().split()
    if len(header)!=3 or header[1]!='blob':
        result = {'available':False,'response':header}
    else:
        size = int(header[2]); data = git.stdout.read(size)
        assert len(data)==size and git.stdout.read(1)==b'\n'
        assert header[0]==oid
        result = {'available':True,'sha256':sha(data),'lf_sha256':sha(data.replace(b'\r\n',b'\n')),
                  'size_bytes':size,'lf_size_bytes':len(data.replace(b'\r\n',b'\n')),'crlf_count':data.count(b'\r\n')}
    blobs[oid] = result
    return result


results=[]
try:
    for (path, expected, normalization, declared_size), kinds in sorted(selected.items(),key=lambda item: str(item[0])):
        raw = (ROOT/path).read_bytes(); lf=raw.replace(b'\r\n',b'\n')
        oid=inv[path]['head_git_oid']; blob=pinned_blob(oid)
        row={'path':path,'sha256':sha(raw),'expected_sha256':expected,'declared_normalization':normalization,
             'declared_size_bytes':declared_size,'kinds':sorted(kinds),'checkout_crlf_count':raw.count(b'\r\n'),
             'checkout_lf_sha256':sha(lf),'raw_matches_declared_hash':sha(raw)==expected,
             'lf_normalized_matches_declared_hash':sha(lf)==expected,'pinned_git_blob_oid':oid,'pinned_git_blob':blob}
        if blob['available']:
            row.update(pinned_git_blob_matches_declared_hash=blob['sha256']==expected,
                       pinned_git_blob_lf_matches_declared_hash=blob['lf_sha256']==expected,
                       checkout_raw_matches_pinned_blob=sha(raw)==blob['sha256'])
        if sha(raw)==expected:
            classification='hash_matches_only_size_or_other_check_failed'
        elif sha(lf)==expected:
            classification='checkout_crlf_to_lf_explains_hash_mismatch'
        elif blob['available'] and blob['sha256']==expected:
            classification='pinned_git_blob_matches_but_checkout_does_not'
        elif blob['available'] and blob['lf_sha256']==expected:
            classification='pinned_git_blob_lf_normalization_explains_hash_mismatch'
        elif blob['available']:
            classification='content_mismatch_persists_in_raw_LF_and_pinned_git_blob'
        else:
            classification='content_mismatch_raw_and_LF_git_blob_unresolved'
        row['classification']=classification
        if declared_size is not None:
            row['checkout_raw_size_matches']=len(raw)==declared_size
            row['checkout_lf_size_matches']=len(lf)==declared_size
            if blob['available']:
                row['pinned_git_size_matches']=blob['size_bytes']==declared_size
                row['pinned_git_lf_size_matches']=blob['lf_size_bytes']==declared_size
        results.append(row)
finally:
    git.stdin.close()
    git.wait(timeout=30)
    assert git.returncode==0

counts=dict(collections.Counter(r['classification'] for r in results))
by_kind={}
for row in results:
    for kind in row['kinds']:
        by_kind.setdefault(kind,collections.Counter())[row['classification']]+=1
summary={'scope':'Every mismatching in-inventory declared-hash/size reference plus all 108 v2 digest-named witness bundles. Outside-inventory references remain unresolved and were not opened.',
         'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120','distinct_target_digest_normalization_size_checks':len(results),
         'distinct_target_paths':len({r['path'] for r in results}),'classifications':counts,
         'by_reference_kind':{k:dict(v) for k,v in sorted(by_kind.items())},
         'pinned_git_blobs_read':len(blobs),'checkout_vs_pinned_blob_differences':sum(not r.get('checkout_raw_matches_pinned_blob',False) for r in results),
         'limit':'These diagnostics do not silently normalize accepted evidence or rewrite stored hashes. Original rule results retain their declared convention. Canonical payload/record digest failures are independent of checkout line endings.'}
pathlib.Path(str(PREFIX)+'_hash_diagnostics.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in results),encoding='utf-8',newline='\n')
pathlib.Path(str(PREFIX)+'_hash_diagnostics_counts.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
by_path={}
for index,row in enumerate(results):
    by_path.setdefault(row['path'],[]).append((index,row['classification']))
automated_path=pathlib.Path(str(PREFIX)+'_automated.jsonl')
automated=[json.loads(line) for line in automated_path.read_text('utf-8').splitlines()]
for row in automated:
    if row['path'] in by_path:
        diagnoses=by_path[row['path']]
        row['hash_diagnostic_indices']=[index for index,_ in diagnoses]
        row['hash_mismatch_classifications']=sorted({classification for _,classification in diagnoses})
        row['hash_diagnostic_ledger']='dag/reviews/additional_structured_evidence_hash_diagnostics.jsonl'
        row['interpretation']='Original raw-byte rule outcomes are retained; consult line-ending and pinned-Git diagnostics before inferring a content mismatch.'
automated_path.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in automated),encoding='utf-8',newline='\n')
print(json.dumps(summary,indent=2))
