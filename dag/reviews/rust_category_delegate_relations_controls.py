"""Independent finite mathematics/source controls; no Rust or repository modules executed."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import product
import hashlib,json,math,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/rust_category_delegate_relations'
S=json.loads(Path(str(P)+'_scope.json').read_text());rows=S['files'];out=[]
def ev(i,lo,hi):
 r=rows[i];assert hashlib.sha256((R/r['path']).read_bytes()).hexdigest()==r['sha256'];assert 1<=lo<=hi<=r['lines']
 return {'path':r['path'],'sha256':r['sha256'],'lines':[lo,hi]}
def add(id,title,result,refs):out.append({'id':id,'title':title,'status':'confirmed','method':'independent finite Python model/static source control; no Rust execution','result':result,'source_evidence':[ev(*x) for x in refs]})
def norm(vals):
 d={};return tuple(d.setdefault(v,len(d)) for v in vals)
def refine(reports,succ):
 p=norm(reports);history=[p]
 while True:
  q=norm((p[x],tuple(sorted({p[y] for y in succ[x]}))) for x in range(len(p)))
  if q==p:return p,history
  p=q;history.append(p)
def greatest_relation(reports,succ):
 r={(x,y) for x in range(len(reports)) for y in range(len(reports)) if reports[x]==reports[y]}
 while True:
  new={(x,y) for x,y in r if all(any((a,b) in r for b in succ[y]) for a in succ[x]) and all(any((a,b) in r for a in succ[x]) for b in succ[y])}
  if r==new:return r
  r=new
checked=0
for reports in product(range(2),repeat=3):
 for mask in range(512):
  succ=[{y for y in range(3) if mask&(1<<(3*x+y))} for x in range(3)]
  p,h=refine(reports,succ);g=greatest_relation(reports,succ)
  assert all((p[x]==p[y])==((x,y) in g) for x in range(3) for y in range(3));assert len(h)<=3
  checked+=1
add('RDR-T01','Partition refinement matches independent greatest-relation elimination',{'systems':checked,'states':3,'labels':1,'report_colors':2,'all_relations':512,'max_recorded_partitions':3},[(2,239,327),(2,579,610)])

src=[set(),{1}];mapping=[0,0];target=[{0}]
assert all({mapping[t] for t in src[x]}<=target[mapping[x]] for x in range(2))
assert any({mapping[t] for t in src[x]}!=target[mapping[x]] for x in range(2))
add('RDR-T02','Back condition refuses a forward-only deadlock collapse',{'forward_preserving':True,'bounded_morphism':False,'missing_successor_state':0},[(2,364,403)])

d={(i,j):Q(0 if i==j or {i,j}=={0,1} else 1) for i in range(3) for j in range(3)}
assert all(d[i,k]<=d[i,j]+d[j,k] for i,j,k in product(range(3),repeat=3))
classes=[{0,2},{1}];related=lambda i,j:any(i in c and j in c for c in classes)
assert related(0,2) and d[0,2]!=0
verifier=d[0,1]==0 and not related(0,1);assert verifier
add('RDR-T03','Collision replay accepts a witness when the decision must refuse ill-defined quotient',{'metric':[[str(d[i,j]) for j in range(3)] for i in range(3)],'equivalence_classes':[[0,2],[1]],'decision':'IdentificationNotZero(0,2,1)','supplied_collision':[0,1],'collision_branch_accepts':True},[(3,674,691),(3,739,768),(3,787,805),(3,871,896)])

parts=[(0,0,0),(0,0,1),(0,1,0),(0,1,1),(0,1,2)];admitted=decisions=0
for a,b,c in product(range(3),repeat=3):
 mat=[[Q(0),Q(a),Q(b)],[Q(a),Q(0),Q(c)],[Q(b),Q(c),Q(0)]]
 if not all(mat[i][k]<=mat[i][j]+mat[j][k] for i,j,k in product(range(3),repeat=3)):continue
 admitted+=1
 for p in parts:
  e_zero=all(p[i]!=p[j] or mat[i][j]==0 for i,j in product(range(3),repeat=2))
  well_defined=all(mat[i][j]==mat[k][l] for i,j,k,l in product(range(3),repeat=4) if p[i]==p[k] and p[j]==p[l])
  assert e_zero==well_defined
  if e_zero:
   collision=any(i<j and mat[i][j]==0 and p[i]!=p[j] for i,j in product(range(3),repeat=2))
   if not collision and len(set(p))>1:assert min(mat[i][j] for i,j in product(range(3),repeat=2) if p[i]!=p[j])>0
  decisions+=1
add('RDR-T04','Finite quotient-distance criterion agrees with representative independence',{'admitted_three_point_integer_pseudometrics':admitted,'partition_checks':decisions,'distance_range':[0,1,2]},[(3,291,341),(3,674,768)])

threshold_cases=qualifying=0
for query in product(range(3),repeat=2):
 for report in product(range(2),repeat=2):
  image=sorted(set(report))
  for dec_values in product(range(3),repeat=len(image)):
   decoder=dict(zip(image,dec_values))
   for epsilon in [Q(0),Q(1,2),Q(1)]:
    threshold_cases+=1
    if not all(abs(query[x]-decoder[report[x]])<=epsilon for x in range(2)):continue
    diameter=max([abs(query[x]-query[y]) for x,y in product(range(2),repeat=2) if report[x]==report[y]],default=0)
    assert diameter<=2*epsilon
    outputs=set(query)
    if len(outputs)<2:continue
    gap=min(abs(a-b) for a,b in product(outputs,repeat=2) if a!=b)
    if 2*epsilon<gap:
     assert all(report[x]!=report[y] or query[x]==query[y] for x,y in product(range(2),repeat=2));qualifying+=1
assert Q(2)*Q(1)==2
add('RDR-T05','Exact decoder threshold enforces report-fiber constancy under its assumptions',{'enumerated_cases':threshold_cases,'strict_gap_qualified_cases':qualifying,'boundary_example':'q=(0,2), one report, decoder=1, epsilon=1 has 2epsilon=gap and must be refused'},[(3,922,972),(3,1002,1102)])

maxf=sys.float_info.max;assert math.isfinite(maxf) and math.isinf(maxf+maxf)
middle=['B','B'];pairs=[('p','q',b) for b in middle]
assert len(pairs)==2
add('RDR-T06','Finite weighted summands can overflow and repeated middle objects overcount',{'finite_summand':str(maxf),'sum':'inf','single_middle_true_pair_count':1,'repeated_middle_implementation_count':len(pairs)},[(1,104,132),(1,139,197)])

# Rust nested block-comment depth, sufficient for this inspected file: delimiters occur only as comments.
text=(R/rows[4]['path']).read_text();depth=0;closed=[];i=0;line=1
while i<len(text):
 if text.startswith('/*',i):depth+=1;i+=2;continue
 if text.startswith('*/',i):depth-=1;assert depth>=0;closed.append((line,depth));i+=2;continue
 if text[i]=='\n':line+=1
 i+=1
assert depth==0 and closed[-1]==(411,0)
fiber={'Red','Blue'};image={'Red':'Green','Blue':'Green'}
assert image['Red']==image['Blue'] and ('Blue'=='Red') is False
add('RDR-T07','Grothendieck draft is inactive and arbitrary preimage is not a cartesian lift',{'outer_comment_ends_line':411,'active_category_of_elements_implementation':False,'countermodel':'walking arrow A->B with F(A)={Red,Blue}, F(B)={Green}; chosen Red lift cannot factor Blue over id_A'},[(4,1,160),(4,180,220),(4,319,345),(4,411,530)])

body=(R/rows[3]['path']).read_text();start=body.index('pub fn weighted_coordinate_pseudometric');end=body.index('/// An admitted equivalence',start);part=body[start:end]
assert part.index('Vec::with_capacity')<part.index('FinitePseudometric::new') and 'MAX_PSEUDOMETRIC_POINTS' not in part
add('RDR-T08','Weighted wrapper performs quadratic work before the point ceiling',{'n':513,'rows_built_before_refusal':513*513,'guard_points':512,'no_large_allocation_performed':True},[(3,208,225),(3,472,492)])

result={'status':'complete','controls':out,'summary':{'controls':len(out),'native_or_provider_runs':0},'limits':['Independent Python finite reconstructions and static checks, not execution of the Rust implementation or its tests.','No private benchmark data, production writes, builds or external calls.']}
Path(str(P)+'_controls.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(result['summary'])
