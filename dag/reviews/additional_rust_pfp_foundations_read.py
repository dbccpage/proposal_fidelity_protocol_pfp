"""Frozen original-inventory scope and bounded full-text read aid."""
import hashlib
import json
import sys
import re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PREFIX='additional_rust_pfp_foundations'
SCOPE_PATH=Path(__file__).with_name(PREFIX+'_scope.json')
PREFIXES=('code/rust/pfp/','code/rust/pfp_runtime/','code/rust/core_types/','code/rust/core_contracts/','code/rust/core_solvers/')
def freeze():
    if SCOPE_PATH.exists(): return json.loads(SCOPE_PATH.read_text(encoding='utf-8'))
    inv=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf-8'))
    cov=json.loads((ROOT/'dag/reviews/coverage.json').read_text(encoding='utf-8'))
    index={r['path']:r for r in inv['files']}
    selected=[]
    for row in cov['files']:
        path=row['path']
        if path.startswith(PREFIXES) and row['substantive_status']!='full_text_source_review_recorded':
            raw=(ROOT/path).read_bytes(); sha=hashlib.sha256(raw).hexdigest()
            assert sha==index[path]['sha256'],path
            selected.append({'path':path,'sha256':sha,'bytes':len(raw),'lines':raw.count(b'\n')+int(bool(raw) and not raw.endswith(b'\n')),'coverage_at_freeze':row['substantive_status']})
    result={'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120','coverage_sha256':hashlib.sha256((ROOT/'dag/reviews/coverage.json').read_bytes()).hexdigest(),'files':selected}
    SCOPE_PATH.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
def read(path,start=1,end=None):
    index={r['path']:r for r in freeze()['files']}; row=index[path]
    raw=(ROOT/path).read_bytes(); assert hashlib.sha256(raw).hexdigest()==row['sha256']
    lines=raw.decode('utf-8-sig').split('\n')
    if lines and lines[-1]=='': lines.pop()
    end=len(lines) if end is None else min(end,len(lines))
    print('FILE',path,'SHA256',row['sha256'],'TOTAL_LINES',len(lines),'READ',start,end)
    for i in range(start,end+1): print(f'{i}: {lines[i-1].rstrip(chr(13))}')
    ledger=Path(__file__).with_name(PREFIX+'_emissions.json')
    entries=json.loads(ledger.read_text(encoding='utf-8')) if ledger.exists() else []
    entries.append({'path':path,'sha256':row['sha256'],'emitted_lines':[start,end],'note':'Emission alone is not a semantic review receipt; only final report assessments establish full read.'})
    ledger.write_text(json.dumps(entries,indent=2)+'\n',encoding='utf-8')
def dedup(paths):
    index={r['path']:r for r in freeze()['files']}
    template_path='code/rust/core_types/src/primitive_difference.rs'
    template_raw=(ROOT/template_path).read_bytes()
    assert hashlib.sha256(template_raw).hexdigest()==index[template_path]['sha256']
    template_lines=template_raw.decode('utf-8').splitlines(keepends=True)
    templates=[(83,167),(169,194)]
    template_texts=[''.join(template_lines[a-1:b]) for a,b in templates]
    receipt_path=Path(__file__).with_name(PREFIX+'_template_receipts.json')
    receipts=json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else {}
    for path in paths:
        raw=(ROOT/path).read_bytes(); row=index[path]
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        content=raw.decode('utf-8'); lines=content.splitlines(keepends=True)
        matches=[]
        for ident in set(re.findall(r'BoundaryRecord([0-9a-f]{8})',content)):
            for (a,b),template in zip(templates,template_texts):
                instance=template.replace('00a1b2a9',ident)
                newline_mode='original'
                start=content.find(instance)
                if start<0:
                    instance=instance.replace('\r\n','\n')
                    newline_mode='LF'
                    start=content.find(instance)
                if start<0: continue
                first=content[:start].count('\n')+1
                last=first+instance.count('\n')-1
                assert ''.join(lines[first-1:last])==instance
                matches.append({'first':first,'last':last,'template_lines':[a,b],'identifier':ident,'newline_mode':newline_mode,'instance_sha256':hashlib.sha256(instance.encode()).hexdigest()})
        print('FILE',path,'SHA256',row['sha256'],'TOTAL_LINES',len(lines))
        starts={m['first']:m for m in matches}; covered=set()
        rebuilt=[]
        for m in matches: covered.update(range(m['first'],m['last']+1))
        for i,line in enumerate(lines,1):
            if i in starts:
                m=starts[i]; a,b=m['template_lines']; value=''.join(template_lines[a-1:b]).replace('00a1b2a9',m['identifier'])
                if m['newline_mode']=='LF': value=value.replace('\r\n','\n')
                print('EXACT_SHARED_CAPACITY_TEMPLATE',json.dumps(m),'BASE',template_path)
                rebuilt.append(value)
            elif i not in covered:
                print(f'{i}: {line.rstrip(chr(10)).rstrip(chr(13))}'); rebuilt.append(line)
        assert ''.join(rebuilt).encode()==raw
        receipts[path]={'path':path,'sha256':row['sha256'],'template_path':template_path,'template_sha256':index[template_path]['sha256'],'substitutions':matches,'byte_reconstruction_verified':True,'note':'Shared blocks enforce only positive count <= supplied capacity. All distinctive non-template source must be semantically read before recording completion.'}
    receipt_path.write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
    if len(sys.argv)==1:
        rows=freeze()['files']
        print(json.dumps({'files':len(rows),'by_crate':dict(Counter(r['path'].split('/')[2] for r in rows)),'bytes':sum(r['bytes'] for r in rows),'lines':sum(r['lines'] for r in rows),'largest':sorted(rows,key=lambda r:r['bytes'],reverse=True)[:12]},indent=2))
    elif sys.argv[1]=='--dedup': dedup(sys.argv[2:])
    else: read(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 1,int(sys.argv[3]) if len(sys.argv)>3 else None)
