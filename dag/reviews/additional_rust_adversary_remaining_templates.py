"""Exact source-template transfers for completely read generated trailers.

Only origin/claim lines and a repeated identifier token may differ. Every
replacement is retained and displayed; all other complete trailer text must
equal one of the two manually read pinned bases. This is not production proof.
"""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_rust_adversary_remaining'
raw=Path(str(P)+'_scope.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='d0547aab64c96d5e8cb280c02ad499283cff257d6931ca886f113cb4235ccd27'
s=json.loads(raw)['files'];ledger=json.loads(Path(str(P)+'_read_ledger.json').read_bytes())
def h(b):return hashlib.sha256(b).hexdigest()
def source(i):
 row=s[i];b=(R/row['path']).read_bytes();assert h(b)==row['sha256'];return b.decode('utf8').splitlines()
def suffix(lines):
 starts=[i for i,x in enumerate(lines) if x.startswith('// Origin: ')]
 if not starts:return None
 k=starts[-1];t='\n'.join(lines[k:]);ids=set(re.findall(r'(?:BoundaryRecord|BoundaryError|l4_boundary_tests_)([a-f0-9]{8})',t))
 if len(ids)!=1:return None
 ident=next(iter(ids));normalized=t.replace(lines[k],'// Origin: {ORIGIN}',1).replace(lines[k+1],'// Claim: {CLAIM}',1)
 # Replacing this exact identifier everywhere is safe only if every occurrence
 # is one of the three complete Rust generated names; reject unexpected uses.
 assert len(re.findall(ident,t))==len(re.findall(r'(?:BoundaryRecord|BoundaryError|l4_boundary_tests_)'+ident,t))
 normalized=normalized.replace(ident,'{ID}')
 return k+1,t,ident,normalized
bases={}
for i,start in [(1,71),(17,952)]:
 lines=source(i);z=len(lines);v=suffix(lines);assert v[0]==start
 seen=set()
 for r in ledger:
  if r['index']==i:
   a,b=r['displayed_lines'];seen.update(range(a,b+1))
 assert set(range(start,z+1))<=seen
 bases[v[3]]={'path':s[i]['path'],'sha256':s[i]['sha256'],'index':i,'lines':[start,z],'body_sha256_utf8_lf':h(v[1].encode()),'identifier':v[2]}
rows=[]
for i,row in enumerate(s):
 lines=source(i);v=suffix(lines)
 if v is None or v[3] not in bases:continue
 start,text,ident,normalized=v;base=bases[normalized]
 residual={'origin':lines[start-1],'claim':lines[start],'identifier':ident,'identifier_occurrences':len(re.findall(ident,text))}
 rows.append({'index':i,'path':row['path'],'sha256':row['sha256'],'reviewed_lines':[start,len(lines)],'trailer_sha256_utf8_lf':h(text.encode()),'base':base,'complete_residual':residual,'normalized_complete_text_sha256':h(normalized.encode()),'all_other_text_exactly_equal':True,'semantic_assessment':'Generated bounded-count record proves only 1 <= admitted_items <= capacity_bound for values created through try_admit; saturating subtraction supplies remaining count. Inline five-case test and mutation-accounting comment concern this isolated counter template, not the enclosing production algorithm. Identifier/origin/claim substitutions change nominal packaging, not that predicate. Full owner context requires its independently read prefix.'})
 print(f"{i}: {start}..{len(lines)} BASE {base['index']} ID {ident} ({residual['identifier_occurrences']} occurrences) | {residual['origin']} | {residual['claim']}")
out={'scope_sha256':h(raw),'method':'Both complete bases manually read. Exact complete suffix equality after displayed origin/claim lines and generated identifier substitutions; all residual text listed. Source prefixes reviewed separately before any whole-file credit.','base_source_reads':list(bases.values()),'transfers':rows}
Path(str(P)+'_template_transfers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('TRANSFER_ROWS',len(rows))
