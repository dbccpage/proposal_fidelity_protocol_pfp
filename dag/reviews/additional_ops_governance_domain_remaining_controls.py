"""Independent finite boundary models, never imports/executes original source.

These controls reproduce expressly identified predicates, not the whole application.
They establish concrete witnesses under stated admissions; source correspondence
is manual, pinned, and separate from a claim of actual production execution.
"""
from pathlib import Path
from types import MappingProxyType
import hashlib,itertools,json,posixpath,re

R=Path(__file__).resolve().parents[2]
P=R/'dag/reviews/additional_ops_governance_domain_remaining'
scope_raw=Path(str(P)+'_scope.json').read_bytes()
assert hashlib.sha256(scope_raw).hexdigest()=='c68c6e94776473c2a759da43724b5a6c74fc33dfc07927e1fc6ece096b535ea9'
scope=json.loads(scope_raw)['files']
results=[]
def evidence(index,a,z):
 row=scope[index];b=(R/row['path']).read_bytes()
 assert hashlib.sha256(b).hexdigest()==row['sha256']
 assert 1<=a<=z<=len(b.decode('utf8').splitlines())
 return {'path':row['path'],'sha256':row['sha256'],'lines':[a,z]}
def record(title,observed,refs,limits):
 results.append({'id':f'OGD-T{len(results)+1:02d}','title':title,'status':'PASS: stated control assertion holds','observed':observed,'source_evidence':[evidence(*r) for r in refs],'limits':limits,'execution_kind':'independent finite reconstruction; original functions/modules not executed'})

# 1. A byte ceiling permits arbitrarily many zero-progress finite messages.
seen=bytearray();iterations=0;limit=1
for chunk in [b'']*10000+[b'x']:
 iterations+=1;remaining=limit+1-len(seen)
 if remaining>0:seen+=chunk[:remaining]
 assert len(seen)<=limit
assert iterations==10001 and seen==b'x'
record('Byte ceiling is not an iteration ceiling',{'limit_bytes':limit,'iterations':iterations,'retained_bytes':len(seen)},[(3,239,268),(2,145,182)],'Finite example only; no infinite stream, ASGI port or original iterator executed.')

# 2. Exact byte ambiguity, not a cryptographic collision.
def preimage(fields):return b''.join(x.encode('utf8')+b'\0' for x in fields)
a=['a\0CREATE','CREATE','','b'*40,'c'*64]
b=['a','CREATE','CREATE\0','b'*40,'c'*64]
assert a!=b and preimage(a)==preimage(b)
record('Distinct mutation records have identical prehash bytes',{'first':a,'second':b,'preimage_hex':preimage(a).hex(),'sha256':hashlib.sha256(preimage(a)).hexdigest()},[(30,35,61),(31,16,29),(32,23,41)],'CREATE unused old field and NUL path admission are source-level facts; real filesystems may refuse NUL. No filesystem mutation or SHA collision claimed.')

# 3. Model the shared kernel lexical admission exactly for these strings.
def repo_path(value):
 raw=value.strip()
 if not raw:raise ValueError('empty')
 norm=posixpath.normpath(raw.replace('\\','/')).strip('/')
 if not norm or norm=='.' or norm.startswith('/') or raw.startswith('/'):raise ValueError('absolute/empty')
 if norm.startswith('..') or '/../' in norm or norm.endswith('/..') or '..' in norm.split('/'):raise ValueError('parent')
 return norm
admitted={repr(s):repo_path(s) for s in ['C:/x','\\root\\x','a\0CREATE']}
try:repo_path('../x')
except ValueError:parent_refused=True
else:parent_refused=False
assert parent_refused and admitted[repr('C:/x')]=='C:/x'
record('Repository-path constructor admits nonportable forms',{'admitted':admitted,'ordinary_parent_refused':parent_refused},[(32,23,41)],'Lexical model only; no actual path resolution, sandbox escape or filesystem read.')

# 4. Signature shape permits an odd hex width that byte decoding rejects.
odd='a'*65
assert re.fullmatch(r'[0-9a-f]{64,128}',odd)
try:bytes.fromhex(odd)
except ValueError:decode_failed=True
else:decode_failed=False
assert decode_failed
record('Admitted odd-width signature digest cannot decode to bytes',{'hex_length':65,'shape_accepts':True,'bytes_fromhex_rejects':True},[(22,29,60),(22,120,121)],'Alphabet/width model; no signature verification or crypto provider.')

# 5. IEEE NaN defeats the declared expiry comparison, unlike normal expiration.
assert not (100.0>=float('nan')) and 100.0>=99.0
record('NaN expiry evades ordinary expired comparison',{'nan_expiry_is_expired':False,'normal_past_expiry_is_expired':True},[(52,28,29),(52,89,107),(101,73,112)],'Demonstrates missing finite-number admission, not acquisition of real merge authority.')

# 6. Complete modeled field checks in verify_active_fence (no authentication).
active={'id':'L','owner':'O','epoch':1,'fence':2,'expiry':10,'scope':['a']}
altered=dict(active,fence=3,expiry=100,scope=['a','b'])
def fence_accepts(presented,now):
 return presented['id']=='L' and presented['owner']==active['owner'] and active['epoch']==1 and presented['epoch']==1 and not presented['fence']<active['fence'] and presented['expiry']>now
assert not fence_accepts(active,20) and fence_accepts(altered,20)
record('Presented lease can outlive and exceed stored grant',{'stored':active,'presented':altered,'now':20,'stored_accepts':False,'altered_accepts':True},[(106,96,119),(105,44,79)],'Unrevoked same-ID/owner/epoch preconditions are fixed. No original registry or concurrency exercised.')

# 7. N ceiling counts map keys, while repeated identities grow admitted list.
def admission(active,paths,n):return len(active)<n and not any(set(paths)&set(old) for old in active.values())
live={};accepted=[]
for i in range(20):
 paths=[f'p{i}']
 if admission(live,paths,2):live['same']=paths;accepted.append(('same',paths))
assert len(live)==1 and len(accepted)==20
record('Repeated candidate IDs exceed list admission ceiling',{'ceiling':2,'active_dictionary_keys':len(live),'admitted_records':len(accepted)},[(58,71,130),(136,65,78)],'Admission fragment only; retained N10 harness/land/mutex programs not executed. Unique IDs would block this witness.')

# 8. Exact set overlap and hierarchical overlap are different relations.
assert admission({'old':['dir']},['dir/file'],10)
assert not admission({'old':['dir/file']},['dir/file'],10)
record('Conflict graph compares exact strings, not ancestor paths',{'parent_child_admitted':True,'identical_path_refused':True},[(58,95,120),(32,59,79)],'Only a gap if declared write sets may denote directories; canonical file-only sets are a narrower admissible use.')

# 9. On the string-valued domain the two-way map comparison is exact;
# admitting None supplies a concrete counterexample outside its annotation.
def witness_accepts(expected,observed):return all(observed.get(k)==v for k,v in expected.items()) and all(k in expected for k in observed)
maps=[]
for choices in itertools.product([None,'0','1'],repeat=2):
 maps.append({k:v for k,v in zip(['a','b'],choices) if v is not None})
assert all(witness_accepts(x,y)==(x==y) for x in maps for y in maps)
assert witness_accepts({'a':None},{}) and {'a':None}!={}
record('Postmerge equality is exact on strings but collapses missing/null',{'valid_domain_pairs_checked':81,'invalid_domain_expected':{'a':None},'invalid_domain_observed':{},'invalid_pair_accepted':True},[(121,50,78)],'No Git reads; direct calls can violate annotations, so runtime type admission is required at this boundary.')

# 10. Outer mapping immutability is not deep immutability.
v=['before'];original={'a':v};proxy=MappingProxyType(dict(original));v.append('after')
assert proxy['a']==['before','after']
record('Shallow copied mapping retains mutable nested values',{'nested_value_after_mutation':proxy['a']},[(51,26,33),(51,124,148)],'List-valued blobs violate the intended string annotation, but the constructor has no value-type validation; no original CandidateBinding was executed.')

# 11. Independent slot validation admits a state forbidden by builder order.
states=list(itertools.product([False,True],repeat=2)) # execution/evidence created
constructor_states=states
ordered_states=[s for s in states if not s[1] or s[0]]
assert (False,True) in constructor_states and (False,True) not in ordered_states
record('Independent identity slots omit evidence-after-execution invariant',{'constructor_states':constructor_states,'builder_order_states':ordered_states,'counterexample':[False,True]},[(88,74,123),(88,259,309)],'Abstract created/uncreated states with correctly typed domain/slot references. No hashes or original constructor executed.')

# 12. The same packet ID can replace rather than extend a protected scope.
leases={'p':['a']}
assert not set(['b'])&set(leases['p'])
leases['p']=['b']
assert not any('a' in paths for paths in leases.values())
stacked_skipped=[key for key in {'parent':['a']} if key=='parent']
record('Lease overwrite loses old scope and stacking bypass is caller-selected',{'after_regrant':leases,'old_path_unprotected':True,'stacked_parent_skipped':stacked_skipped},[(115,32,69)],'Equal/ancestor checks elsewhere remain useful; this finite model assumes distinct canonical paths and does not resolve actual paths.')

# 13. The explicit delimiter does not make a broad pathspec narrow.
rest=['--','.'];idx=rest.index('--');opts=rest[:idx];paths=rest[idx+1:]
allow=not any(o in {'-A','--all','-u','.'} for o in opts) and bool(paths)
assert allow
record('git add -- . is admitted by broad-staging predicate',{'argv':['git','add','--','.'],'predicate_allows':allow},[(83,105,119)],'No Git command run. Attached -C handling is an additional source-level parser gap, not tested here.')

# 14. Ownership-first selection differs from ordinary three-way preservation.
def reconcile(owner,actor,base,main,branch):
 if branch==main:return 'OWNED' if owner==actor else 'SHARED'
 if owner==actor:return 'OWNED'
 if owner is not None and owner!=actor:return 'TAKE_MAIN'
 if branch==base and main!=base:return 'TAKE_MAIN'
 if main==base and branch!=base:return 'TAKE_BRANCH'
 return 'UNRESOLVED'
cases={'owned_branch_unchanged':reconcile('actor','actor','a','b','a'),'unowned_branch_unchanged':reconcile(None,'actor','a','b','a'),'foreign_branch_only_edit':reconcile('other','actor','a','a','b'),'unowned_concurrent':reconcile(None,'actor','a','b','c')}
assert cases=={'owned_branch_unchanged':'OWNED','unowned_branch_unchanged':'TAKE_MAIN','foreign_branch_only_edit':'TAKE_MAIN','unowned_concurrent':'UNRESOLVED'}
record('Ownership changes the three-way reconciliation policy',cases,[(129,88,177)],'Conditional policy difference, not an incorrect theorem if exclusive ownership is the intended authoritative premise.')

# 15. Empty allow substrings suppress every possible scanned line.
lines=['C:\\Users\\alice\\x','/home/alice/x','plain']
assert all(any(pattern in line for pattern in ['']) for line in lines)
record('Empty portable-reference allow pattern suppresses all lines',{'lines':lines,'suppressed':3},[(118,75,118)],'Does not assert universal coverage of the four regex profiles or execute the scanner.')

# 16. Relative path normalization erases leading parent syntax; POSIX root prefix.
def relcanon(raw):
 stack=[]
 for part in raw.replace('\\','/').lstrip('/').split('/'):
  if part in ('','.'):continue
  if part=='..':
   if stack:stack.pop()
   continue
  stack.append(part)
 return '/'.join(stack)
assert relcanon('../a')=='a' and relcanon('/a')=='a'
assert not ('/a'=='/' or '/a'.startswith('/'+'/'))
record('Path spelling information is lost before prefix reasoning',{'parent_escape_normalized':relcanon('../a'),'absolute_normalized':relcanon('/a'),'posix_root_prefix_contains_child':False},[(114,34,62)],'Pure lexical fragment only; actual canonicalize_path uses ambient filesystem and platform state and was not executed.')

# 17. A non-None empty digest is a present measurement label to the classifier.
def transported(source,destination):
 if source is None or destination is None:return 'REFUSED'
 return 'VERIFIED_PATH_ONLY' if source==destination else 'VERIFIED_CONTENT_CHANGED'
assert transported(None,None)=='REFUSED' and transported('','')=='VERIFIED_PATH_ONLY'
record('Transport refuses absent digests but accepts empty present labels',{'none_pair':transported(None,None),'empty_pair':transported('',''),'unequal_label_pair':transported('a','b')},[(146,109,149)],'Different-path branch only. Actual byte measurement, digest shape and mutation semantics remain external.')

# 18. Declared count/provenance is not consistency with the listed population.
source='DIRECT';count=0;numbers=[17];residual=None
assert source=='DIRECT' and count==0 and residual in (None,'ZERO_OPEN') and len(numbers)>0
record('DIRECT zero count can disagree with its open-number list',{'source':source,'count':count,'open_numbers':numbers,'zero_open_predicate':True},[(53,10,28)],'Caller-constructed record witness only; no claim that an actual direct API adapter emitted this inconsistency.')

# 19. The declared work-packet parser permits contradictory path declarations.
write_paths=[''];forbidden_paths=[''];schema='unexpected'
assert isinstance(write_paths,(list,tuple)) and len(write_paths)>0 and all(isinstance(x,str) for x in write_paths)
assert set(write_paths)&set(forbidden_paths)
record('Work-packet sequence shape does not establish valid write scope',{'write_paths':write_paths,'forbidden_paths':forbidden_paths,'ignored_input_schema':schema},[(162,36,46),(162,64,114)],'Primary required labels assumed valid; no actual parser/module call. Unknown schema is ignored by the mapping function, while direct construction is weaker still.')

# 20. String-enum equality can prevent intended canonical assignment.
from enum import Enum
class NoneEffect(str,Enum):NONE='None'
input_effect='None';canonical=NoneEffect.NONE
stored=canonical if canonical!=input_effect else input_effect
assert type(stored) is str and canonical==stored
record('Equality-based enum normalization preserves raw string',{'stored_type':type(stored).__name__,'equal_to_enum':True},[(134,24,31),(161,29,34),(162,64,69)],'Representation inconsistency only: NONE remains the only admitted effect. WorkPacket uses identity comparison and normalizes correctly.')

out={'review_id':'additional_ops_governance_domain_remaining','scope_sha256':hashlib.sha256(scope_raw).hexdigest(),'summary':{'independent_controls':len(results),'passed':len(results),'failed':0,'original_modules_executed':0,'original_functions_executed':0},'method':'Manual source-correspondent, finite stdlib reconstructions; assertions test the named witnesses, not production runtime correctness. No retained runners or native/provider calls.','controls':results}
Path(str(P)+'_controls.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(out['summary'],indent=2))
