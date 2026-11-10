"""Independent bounded controls of inspected predicates and exact interval algebra."""
import hashlib,json,pathlib,itertools,math
from fractions import Fraction as Q
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_rust_quantum_probability_remaining';fs=json.loads((H/(P+'_scope.json')).read_text())['files'];out=[]
def record(i,title,result,indices,limitations):
 pins=[]
 for k in indices:
  f=fs[k];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];pins.append({'path':f['path'],'sha256':f['sha256']})
 out.append({'id':f'RQPR-CHECK{i:03d}','title':title,'observed':result,'source_pins':pins,'limitations':limitations})
raw={'numerator':1,'denominator':0};display_accept=raw['denominator']!=0;variant='ExactRational';governance_accept=variant in ('ExactRational','Integer','BooleanRegime');assert governance_accept and not display_accept
record(1,'Exact variant gate is weaker than display denominator validation',{'public_packet':raw,'variant':variant,'display_accept':display_accept,'governance_accept':governance_accept},[50],'Direct independent model of inspected match arms; no original BigRational or Rust code executed. new_raw(1,0) is explicitly constructed in affine/clock tests.')
scaled=42.0*1e18;mantissa=min(2**63-1,max(-2**63,int(scaled)));display=mantissa/1e18;assert display<10 and display!=42
record(2,'Placeholder decimal conversion loses ordinary large magnitudes',{'input':42,'scale':18,'saturating_i64_mantissa':mantissa,'display':display,'NaN_saturating_cast_expected':0},[50],'Rust float-to-i64 saturation modeled independently; function is explicitly named unchecked and documented as placeholder. Not a governance bypass.')
x,r=Q(-3,2),Q(2,3);a,b,alpha,beta,eta=Q(-2),Q(1,3),Q(1,4),Q(1,5),Q(1,7);center=a*x+b;radius=(abs(a)+alpha)*r+alpha*abs(x)+beta+eta;realized=[]
for se,sa,sb,ss in itertools.product((-1,1),repeat=4):
 truth=(a+sa*alpha)*(x+se*r)+b+sb*beta+ss*eta;assert abs(truth-center)<=radius;realized.append(truth)
record(3,'Affine conditional enclosure contains all16 endpoint realizations',{'center':str(center),'radius':str(radius),'min':str(min(realized)),'max':str(max(realized)),'corners':16},[43],'Exact independent Fraction arithmetic. The triangle-inequality derivation covers all admissible values; finite corner control alone does not authenticate supplied errors or instruments.')
eps=Q(1,2);readings=[(Q(1),Q(1,10)),(Q(0),Q(1,20)),(Q(1),Q(1,5))];nominal=(readings[0][0]-2*readings[1][0]+readings[2][0])/eps**2;radius=(readings[0][1]+2*readings[1][1]+readings[2][1])/eps**2
for signs in itertools.product((-1,1),repeat=3):
 vals=[c+s*r for(c,r),s in zip(readings,signs)];v=(vals[0]-2*vals[1]+vals[2])/eps**2;assert nominal-radius<=v<=nominal+radius
record(4,'Central difference propagates eight independent endpoint combinations',{'finite_response':[str(nominal-radius),str(nominal+radius)],'declared_M':3,'extra_regularization_radius':str(3*eps/3)},[46],'No function regularity or common-target premise is established by this calculation; Taylor remainder bound remains conditional.')
dur=list(map(Q,[1,2,3]));read=[Q(0),Q(3,2),Q(3),Q(25,4)];bud=[Q(1,2),Q(1,2),Q(1,4)];intervals=[]
for i in range(4):
 for j in range(i,4):
  total=sum(dur[i:j],Q());measured=read[j]-read[i];bound=sum(bud[i:j],Q());assert abs(measured-total)<=bound;intervals.append([i,j,str(abs(measured-total)),str(bound)])
coarse={'durations':[sum(dur[:2]),dur[2]],'readings':[read[0],read[2],read[3]],'budgets':[sum(bud[:2]),bud[2]]};assert coarse['readings'][1]-coarse['readings'][0]-coarse['durations'][0]==0
record(5,'Clock telescoping and endpoint coarsening preserve exact bounds',{'all10intervals':intervals,'coarse':{k:list(map(str,v))for k,v in coarse.items()}},[45],'Exact independent finite arithmetic; no chronology, physical calibration or empirical adequacy follows.')
result={'execution_kind':'independent_bounded_controls','controls':out,'all_assertions_passed':True,'helper_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()};(H/(P+'_checks.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'controls':len(out),'all_assertions_passed':True}))
