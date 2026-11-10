"""Bounded all-record data review; no provider, build, production writes."""
import collections
import difflib
import hashlib
import json
import re
import tarfile
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
P='additional_paper_004'
PKG=ROOT/'papers/pfp/004_pfp_native_verification_and_evidence_custody'
OUT=HERE/(P+'_inspection')
def sha(b): return hashlib.sha256(b).hexdigest()
def write(n,x): (HERE/(P+n)).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def pairs(b): return [tuple(s.split('  ',1)) for s in b.decode().splitlines() if s and not s.startswith('#')]

def custody():
    with zipfile.ZipFile(next(PKG.glob('*.zip'))) as z:
        old=z.read(PKG.name+'/audited_source/SOURCE_MEMBERS.sha256')
    current=(PKG/'audited_source/SOURCE_MEMBERS.sha256').read_bytes()
    a,b=pairs(old),pairs(current)
    oldmap={p:h for h,p in a}
    diffs=collections.Counter()
    for (h,p),(j,q) in zip(a,b):
        for op,i,k,v,w in difflib.SequenceMatcher(None,p,q,autojunk=False).get_opcodes():
            if op!='equal': diffs[(p[i:k],q[v:w])]+=1
    checked=[]
    with tarfile.open(PKG/'audited_source/pfp-iv-native-source-52cb5457.tar.gz') as t:
        for m in t.getmembers():
            rel=m.name.split('/',1)[1]
            checked.append((rel,sha(t.extractfile(m).read())==oldmap.get(rel)))
    r={'historical_manifest_sha256':sha(old),'current_manifest_sha256':sha(current),'rows':len(a),'same_digest_sequence':len(a)==len(b) and all(x[0]==y[0] for x,y in zip(a,b)),'renamed_rows':sum(x[1]!=y[1] for x,y in zip(a,b)),'historical_manifest_matches_tar':all(x[1] for x in checked),'historical_tar_members_checked':len(checked),'rename_fragments':[{'old':x,'new':y,'occurrences':n} for (x,y),n in diffs.most_common()],'examples':[{'old':x[1],'new':y[1],'same_digest':x[0]==y[0]} for x,y in list(zip(a,b))[:8]]}
    write('_manifest_translation.json',r);print(json.dumps(r,ensure_ascii=False))

def data():
    names=['code/chordal_fuzz_repair_benchmark_receipt.json','code/l1_sparsity_benchmark_receipt.json','code/topology50_benchmark_receipt.json','docs/historical_native_run/004_republication_gate_receipt.json']
    rows=[]
    for name in names:
        raw=(PKG/name).read_bytes();obj=json.loads(raw)
        summary={k:v for k,v in obj.items() if not isinstance(v,list) or len(v)<6}
        arrays={k:v for k,v in obj.items() if isinstance(v,list) and len(v)>=6}
        row={'path':str((PKG/name).relative_to(ROOT)).replace('\\','/'),'sha256':sha(raw),'lines':len(raw.decode().splitlines()),'top_level_summary':summary,'arrays':{}}
        for k,v in arrays.items():
            schemas=collections.Counter(tuple(sorted(x)) if isinstance(x,dict) else type(x).__name__ for x in v)
            sub={'count':len(v),'schema_counts':[(x,n) for x,n in schemas.items()]}
            if all(isinstance(x,dict) for x in v):
                keys=sorted(set().union(*(x.keys() for x in v)))
                sub['field_profiles']={}
                for f in keys:
                    vals=[x.get(f) for x in v];encoded=[json.dumps(x,sort_keys=True,ensure_ascii=False) for x in vals]
                    distinct=list(dict.fromkeys(encoded))
                    if len(distinct)<=12:sub['field_profiles'][f]={'all_distinct_values':[json.loads(x) for x in distinct]}
                    elif all(isinstance(x,(int,float)) for x in vals):sub['field_profiles'][f]={'min':min(vals),'max':max(vals),'sum':sum(vals),'count':len(vals)}
                    else:sub['field_profiles'][f]={'distinct':len(distinct),'first':vals[0],'last':vals[-1]}
            row['arrays'][k]=sub
        rows.append(row)
        print(json.dumps(row,ensure_ascii=False))
    write('_parsed_data.json',rows)

def pdf_equality():
    from PIL import Image
    inv=json.loads((OUT/'pdf_inventory.json').read_text(encoding='utf-8'))
    combined=[ROOT/p for p in inv[1]['page_images']]
    r=[]
    for idx,offset in [(2,0),(5,1),(3,6),(4,11)]:
        matches=[]
        for j,p in enumerate(inv[idx]['page_images']):
            with Image.open(ROOT/p) as a,Image.open(combined[offset+j]) as b:
                matches.append(a.size==b.size and a.tobytes()==b.tobytes())
        r.append({'path':inv[idx]['path'],'sha256':inv[idx]['sha256'],'base_path':inv[1]['path'],'base_sha256':inv[1]['sha256'],'base_pages':[offset+1,offset+len(matches)],'rendered_pixel_equal_by_page':matches})
    write('_pdf_equality.json',r);print(json.dumps(r))

if __name__=='__main__':
    import sys
    {'custody':custody,'data':data,'pdf_equality':pdf_equality}[sys.argv[1]]()
