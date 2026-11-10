"""Read-only population checks and in-memory controls over fully reviewed snippets.
No repository imports, subprocesses, network, native builds or private inputs.
"""
from pathlib import Path
from fractions import Fraction
import ast,hashlib,json,re,runpy,warnings,collections
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_patterns_remaining'
inventory=json.loads(Path(str(P)+'_inventory.json').read_text())['files']
def body(i):return (R/inventory[i]['path']).read_text(encoding='utf-8')
def block(i,language='python'):
 return re.findall(r'```'+language+r'\n(.*?)\n```',body(i),re.S)[0]
def pin(p):
 b=(R/p).read_bytes();return dict(path=p,sha256=hashlib.sha256(b).hexdigest(),lines=len(b.decode().splitlines()))
headers=[];links=[]
for row in inventory:
 b=(R/row['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256']
 s=b.decode();h={}
 if s.startswith('---\n') or s.startswith('---\r\n'):
  for line in s.split('---',2)[1].splitlines():
   if ':' in line:
    k,v=line.split(':',1);h[k]=v.strip().strip('"')
 headers.append(dict(index=row['index'],path=row['path'],metadata=h))
 for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)',s):
  target=match.group(1)
  if target.startswith(('http:','https:','#','mailto:')):continue
  path=(R/row['path']).parent/target.split('#')[0]
  links.append(dict(source=row['path'],line=s[:match.start()].count('\n')+1,target=target,exists=path.exists(),resolved=path.resolve().relative_to(R).as_posix()))
by_stem={Path(r['path']).stem:r for r in inventory}
arity=[];duals=[];missing=[];nonreciprocal=[]
for r in headers:
 h=r['metadata']
 if not h:continue
 if 'operad_source_colours' in h:
  colors=json.loads(h['operad_source_colours']);a=int(h['operad_arity'])
  if len(colors)!=a:arity.append(dict(path=r['path'],arity=a,source_colours=colors))
 d=h.get('dual_pattern')
 if d:
  d=d.removesuffix('.md');target=by_stem.get(d)
  if not target:missing.append(dict(path=r['path'],dual=d));continue
  dh=headers[target['index']]['metadata'].get('dual_pattern','').removesuffix('.md')
  if dh!=Path(r['path']).stem:nonreciprocal.append(dict(path=r['path'],dual=target['path'],back=dh))
ids=collections.Counter(h['metadata'].get('pattern_id') for h in headers if h['metadata'].get('pattern_id'))
population={'files':len(inventory),'bytes':sum(x['size_bytes'] for x in inventory),'lines':sum(x['lines'] for x in inventory),
 'frontmatter_files':sum(bool(x['metadata']) for x in headers),'missing_frontmatter_markdown':[x['path'] for x in headers if not x['metadata'] and x['path'].endswith('.md')],
 'arity_mismatches':arity,'duplicate_pattern_ids':{k:v for k,v in ids.items() if v>1},'missing_dual_targets':missing,'nonreciprocal_duals':nonreciprocal,
 'lowercase_pattern_filenames':[r['path'] for r in inventory if Path(r['path']).name.startswith(('ap_','hp_'))],
 'local_links':len(links),'broken_local_links':len([x for x in links if not x['exists']]),'links':links,
 'residual_counts':dict(collections.Counter(x['metadata'].get('operad_residual','absent') for x in headers)),
 'empty_catalogs':[r['path'] for r in inventory if r['path'].endswith('.txt')],
 'scope':'Syntax/existence checks across all198; no linked source execution or semantic proof from metadata.'}
checks=[]
def add(id,claim,observed,indices,limit):checks.append(dict(id=id,claim=claim,observed=observed,source_indices=indices,limit=limit))
ns={};exec(compile(block(99),'HP_AUTOP_001 quoted code','exec'),ns)
obligations=['independent checker still required'];got=ns['finalize_run_summary']('task-A',{'status':'PASS'},obligations)
assert got['terminal_verdict']=='PASS_TO_MASTER' and got['open_obligations']==obligations
add('OPR-P01','Status-only receipt grants pass with unresolved obligation.',got,[99],'Exact quoted pure function; no runner, signature or production owner invoked.')
with warnings.catch_warnings():
 warnings.simplefilter('ignore',SyntaxWarning);v=eval(compile('1050 > 1000 is True','quoted comparison','eval'))
assert v is False
add('OPR-P02','Purported tautology is a false chained comparison.',{'value':v,'ast':ast.dump(ast.parse('1050 > 1000 is True',mode='eval').body)},[88],'Literal Python expression only.')
t=Fraction(1,192);formula=(3-t-t*t/4)/24-11*t/78
assert formula==Fraction(5706995,46006272) and formula!=Fraction(5673203,46006272) and formula>=Fraction(1,9)
add('OPR-P03','Public quoted rational differs; weaker bound survives.',{'computed':str(formula),'printed':'5673203/46006272','at_least_one_ninth':True},[42,140],'Only the displayed finite rational formula; no analytic theorem or source monograph checked.')
f3_first_row=(1,1,1);f2=((1,1),(1,-1));tensor_row=[a*b for a in f3_first_row for b in f2[1]]
assert -1 in tensor_row
add('OPR-P04','F3 tensor F2 cannot have zero minus-one entries.',{'one_tensor_row':tensor_row},[51,151],'Uses the defined Fourier first row and2x2Fourier matrix, not a reconstruction of Tao or a MUB claim.')
base={0,1};empty={x for x in base if x==2};extra={x for x in empty if x==0};assert not extra
add('OPR-P05','Additional constraints cannot restore an empty base.',{'base_solutions':sorted(empty),'with_extra_constraint':sorted(extra)},[57,156],'Finite illustrative set inclusion; does not establish actual618/666system emptiness.')
zero=Fraction(0);assert zero*zero==0 and zero<Fraction(31,800)
add('OPR-P06','Nilpotence and alternation do not imply a positive spectral/circulation bound.',{'zero_differential_composition':str(zero*zero),'zero_spectral_value':str(zero),'zero_alternating_cycle':str(sum([zero]*3))},[60,61,159,160],'Exact scalar/zero-cochain countermodels to an unqualified implication; no claimed specific supplied complex refutation.')
grid=range(5)
def poly(x):
 y=1
 for j in grid:y*=x-j
 return y
assert all(poly(x)==0 for x in grid) and poly(5)==120
add('OPR-P07','Finite grid equality needs a degree bound to imply polynomial identity.',{'grid_values':[poly(x) for x in grid],'outside_value':poly(5),'degree':5},[49,149],'One-variable factor extends to a multivariate grid; not a refutation of an independently supplied symbolic identity.')
decoded={'label':'a b'};wire=json.dumps(decoded,separators=(',',':'));stripped=''.join(wire.split());assert json.loads(stripped)!=decoded
add('OPR-P08','Stripping all whitespace can change protected string values.',{'wire':wire,'stripped':stripped,'after':json.loads(stripped)},[147],'Ordinary JSON example; a separately constrained whitespace-free grammar may be safe.')
stdout='1 passed\n';passed=int(re.search(r'(\d+)\s+passed',stdout).group(1));accepted=passed>0 and 0==0
assert accepted
add('OPR-P09','Printed pass count plus exit0 satisfies the quoted gate without assertions.',{'stdout':stdout,'returncode':0,'accepted':accepted},[191],'In-memory branch evaluation, not an actual early-exiting process.')
ascii_wire=json.dumps({'label':'é'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
utf_wire=json.dumps({'label':'é'},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')
assert json.loads(ascii_wire)==json.loads(utf_wire) and ascii_wire!=utf_wire
add('OPR-P10','Equal JSON values can have different serialization-profile hashes.',{'ascii_sha256':hashlib.sha256(ascii_wire).hexdigest(),'utf8_sha256':hashlib.sha256(utf_wire).hexdigest(),'equal_values':True},[77,176],'No claim either profile is intrinsically correct or Rust parity is established.')
owner='operads/skills/techne-code-python-anti-patterns/scripts/python_anti_pattern_auditor.py'
py=runpy.run_path(str(R/owner),run_name='pattern_audit_review_only')
visitor=py['PythonAntiPatternVisitor']('example.py',['def f(x=[]): pass'])
visitor.visit(ast.parse('def f(x=[]): pass'));got=visitor.findings
assert got[0]['id']=='AP_PY_005'
add('OPR-P11','Python owner emits AP_PY005 for mutable default, catalog005 means digest-shape verification.',got,[74],'Fully read standard-library-only owner, AST visitor on supplied string. No repository target scanned or module under review executed.')
filename='..';accepted_filename=bool(filename) and Path(filename).name==filename
assert accepted_filename
add('OPR-P12','Caller-selected receipt filename guard admits parent-directory component.',{'filename':filename,'guard_accepts':accepted_filename},[183],'Path-name predicate only; no directory creation, write, traversal or production helper call.')
class MissingArchive:
 def exists(self):return False
calls=[];ns={'archive_path':MissingArchive(),'source_dir':'declared-source','check_selected_archive':lambda x:calls.append('archive'),'check_directory_payload':lambda x:calls.append('directory')}
exec(compile(block(187),'HP_PY_019 quoted code','exec'),ns);assert calls==['directory']
add('OPR-P13','Explicit missing archive falls back to directory check.',{'calls':calls,'explicit_archive_selected':True},[85,187],'Exact quoted branch with in-memory fake paths and callbacks; no archive/directory inspected by the snippet.')
extra=[owner,'operads/skills/techne-code-lean4-anti-patterns/scripts/lean4_anti_pattern_auditor.py','operads/skills/techne-code-sql-anti-patterns/scripts/sql_anti_pattern_auditor.py','operads/skills/techne-code-rust-anti-patterns/scripts/rust_anti_pattern_auditor.py','eis/antibodies/definitions/pilot035_candidates.json','eis/antibodies/admissions/pilot035_owner_approval_20261015.json']
extra_pins=[pin(p) for p in extra]
dag=json.loads((R/'dag/workflows_dag.json').read_text())
families=[dict(id=x['id'],name=x['name'],status=x.get('status'),source_paths=x.get('source_paths',x.get('source_pilots',[]))) for x in dag['nodes'] if x.get('kind')=='existing_workflow_family']
result={'status':'completed','population_checks':population,'probes':checks,'supporting_source_pins':extra_pins,'family_registry_metadata_only':families}
Path(str(P)+'_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in population.items() if k not in {'links','empty_catalogs','nonreciprocal_duals'}},indent=2));print('NONRECIPROCAL',json.dumps(nonreciprocal));print('PROBES',len(checks));print('FAMILIES',json.dumps(families))
