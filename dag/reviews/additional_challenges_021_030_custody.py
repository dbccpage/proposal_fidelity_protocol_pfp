"""Recheck manifest byte bindings using their declared LF convention, without expanding scope."""
import hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'dag/reviews/additional_challenges_021_030'
inventory={r['path']:r for r in json.loads((ROOT/'dag/file_inventory.json').read_text())['files']}
prior={}
for text in (ROOT/'dag/reviews/additional_structured_evidence_automated.jsonl').open():
    r=json.loads(text)
    if r['path'].endswith('/judge_packet/manifest.json') and any('/c%03d_'%n in r['path'] for n in range(21,31)):prior[r['path']]=r
records=[]
for n in range(21,31):
    path=next(p for p in inventory if p.startswith('workflows/tasks/certified_challenges/c%03d_'%n) and p.endswith('/judge_packet/manifest.json'))
    p=ROOT/path;raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();d=json.loads(raw);table=d['files']
    entries=table if isinstance(table,list) else [{'path':k,**v} for k,v in table.items()]
    base=p.parent if n==21 else p.parent.parent;results=[]
    for entry in entries:
        target=(base/entry['path']).resolve();tp=target.relative_to(ROOT).as_posix()
        r={'declared_path':entry['path'],'resolved_path':tp,'declared_sha256':entry['sha256'],'declared_size_bytes':entry['size_bytes']}
        if tp not in inventory:r['status']='unresolved_outside_original_inventory'
        else:
            b=target.read_bytes();lf=b.replace(b'\r\n',b'\n');actual=hashlib.sha256(b).hexdigest();normalized=hashlib.sha256(lf).hexdigest()
            r.update(actual_sha256=actual,lf_sha256=normalized,actual_size=len(b),lf_size=len(lf),inventory_raw_hash_match=actual==inventory[tp]['sha256'],raw_match=actual==entry['sha256'] and len(b)==entry['size_bytes'],declared_lf_match=normalized==entry['sha256'] and len(lf)==entry['size_bytes'])
            r['status']='declared_lf_match' if r['declared_lf_match'] else 'declared_lf_mismatch'
        results.append(r)
    rec=dict(path=path,sha256=sha,inventory_sha256=inventory[path]['sha256'],inventory_raw_hash_match=sha==inventory[path]['sha256'],full_source_read=False,checks=['json_parse','declared_CRLF_TO_LF_hash_and_size','unique_declared_paths','in_original_inventory_target_binding'],status='manifest_bounded_custody_recheck',declared_normalization=d.get('digest_normalization'),manifest_status=d.get('manifest_status'),entry_count=len(entries),unique_paths=len({r['path'] for r in entries})==len(entries),target_status_counts=dict(Counter(r['status'] for r in results)),target_reviews=results,prior_manifest_record_reused_only_for_provenance=prior.get(path,{}).get('sha256')==sha,evidence_ceiling='Regenerated historical custody table; no pre-run commitment, provider authenticity, complete-file coverage or mathematical validity. Outside-inventory paths remain unresolved, not false; CRLF-only effects are separated.')
    if 'manifest_sha256' in d:
        actual=hashlib.sha256(''.join(f"{e['sha256']}  {e['path']}\n" for e in entries).encode()).hexdigest()
        rec['declared_ordered_lines_digest']={'claimed':d['manifest_sha256'],'computed':actual,'matches':actual==d['manifest_sha256'],'definition':d['manifest_sha256_definition']}
    if 'counts' in d:rec['custodied_files_count_matches']=d['counts']['custodied_files']==len(entries)
    records.append(rec)
with Path(str(P)+'_custody_automated.jsonl').open('w',encoding='utf8',newline='\n') as f:
    for r in records:f.write(json.dumps(r)+'\n')
print(json.dumps([{'family':n,'counts':r['target_status_counts'],'prior_pin_matches':r['prior_manifest_record_reused_only_for_provenance'],'digest':r.get('declared_ordered_lines_digest')} for n,r in zip(range(21,31),records)],indent=2))
