"""Independent finite controls for paper hash/source predicates, without importing owners."""
import hashlib,io,json,pathlib,re,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,k,o,l):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'OPSKILL-CHECK-{k:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':o,'limitations':l})
raw=b'A\r\n$x$\r\n';text=io.TextIOWrapper(io.BytesIO(raw),encoding='utf-8',newline=None).read();reported=len(text.splitlines(keepends=True)[0].encode());actual=raw.index(b'$');assert (reported,actual)==(2,3)
add(448,80,{'raw_hex':raw.hex(),'normalized_text':text,'reported_second_line_byte_start':reported,'actual_start':actual},'Reproduces universal-newline reading and offset formula only. Source bytes never changed.')
line='Here $$x$$';display=re.findall(r'(?:\\\[(.*?)\\\]|\$\$(.+?)\$\$)',line);inline=re.findall(r'(?:(?<!\\)\$(?!\$)(.+?)(?<!\\)\$|\\\((.+?)\\\))',line);assert len(display)==len(inline)==1
add(448,81,{'line':line,'display_matches':display,'inline_matches':inline,'numeric_inline_1_excluded':'1'.isdigit()},'Exact parser regexes demonstrate duplicate display/inline classification and numeric exclusion; not exhaustive grammar testing.')
def buffered_claim(formula):
 lines=['Statement:', '$$',formula,'$$',''];buf=[];display=False
 for line in lines:
  if display:
   if line=='$$':display=False
   continue
  if line=='$$':display=True;continue
  buf.append(line)
 return '\n'.join(buf).strip()
a=buffered_claim('x=1');b=buffered_claim('x=2');assert a==b
add(448,82,{'different_display_equations':['x=1','x=2'],'both_claim_statement':a,'same_claim_statement_sha256':hashlib.sha256(a.encode()).hexdigest()},'Reduced source control flow shows display formulas bypass claim buffer. Formula entries themselves still differ; this is a claim-statement binding gap, not a SHA collision.')
entry='00000000  code/check.py';claimed,path=entry.split(None,1);names=['unrelated/code/check.py'];member=any(n==path or n.endswith('/'+path) for n in names);assert member and len(claimed)!=64
add(448,83,{'checksum_line':entry,'archive_names':names,'membership_predicate_passes':member,'digest_length_valid':False,'bytes_compared':False},'Exact name/suffix predicate and ignored checksum column; no ZIP or retained verifier invocation. Whole ZIP digest is still recorded by implementation.')
bindings=[];required=['docs/descriptions.md'];missing=[];status='FAIL'if not required or missing else'PASS';assert status=='PASS'
add(448,84,{'bound_modules':bindings,'required_from_document_only':required,'status':status},'Reproduces required-list condition: an ancillary document or checksum list can defeat advertised no-bindings refusal.')
md_author=zenodo_author=md_version=zenodo_version=None;pdf='';mismatches=[];consistent=len(mismatches)==0;assert consistent
add(448,85,{'all_identity_fields_missing':True,'identity_consistent':consistent},'Missing identity values create no mismatches; no claim that metadata exists or author matches. Source also does not compare arbitrary full author identities.')
manifest_exists=False;events=[]
if manifest_exists:events.append('verified')
add(444,86,{'manifest_exists':False,'verification_events':events,'exception_raised':False},'Reduced snippet preserves missing-manifest branch. No historical commitment files read; assert-based comparisons additionally disappear under optimized Python.')
(H/(P+'_checks11.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
