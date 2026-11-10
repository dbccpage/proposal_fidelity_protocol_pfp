"""Small independent finite controls; does not import or execute retained skills."""
import hashlib,html,itertools,json,pathlib,sys,xml.etree.ElementTree as ET
from fractions import Fraction as Q
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,num,obs,limit):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'OPSKILL-CHECK-{num:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':obs,'limitations':limit})
# Exhaustive finite p/q controls; p,q:D -> {0,1}, |D|=3.
count=0
for p in itertools.product(range(2),repeat=3):
 for q in itertools.product(range(2),repeat=3):
  bad=[(x,y)for x in range(3)for y in range(x+1,3)if p[x]==p[y]and q[x]!=q[y]]
  fact=any(all(q[x]==f[p[x]]for x in range(3))for f in itertools.product(range(2),repeat=2))
  breaks=[]
  for t in itertools.permutations(range(3)):
   if all(p[t[x]]==p[x]for x in range(3))and any(q[t[x]]!=q[x]for x in range(3)):breaks.append(t)
  assert bool(bad)==(not fact)==bool(breaks);count+=1
add(106,21,{'map_pairs_checked':count,'carrier_size':3,'codomain_size':2,'equivalence_holds':True},'Exact finite illustration only; general proof is factorization through fibres. Full fibre permutations need not preserve extra graph/order structure; no retained hunter run.')
omega=[1,1];d=[1,0];alpha=1;w=[0,1];res=[o-a*alpha for o,a in zip(omega,d)];dual=sum(a*b for a,b in zip(w,omega));assert sum(a*b for a,b in zip(d,w))==0 and dual==sum(map(abs,res))==1 and dual!=sum(map(abs,omega))
add(118,22,{'omega':omega,'d0_column':d,'alpha':alpha,'dual_w':w,'residual':res,'dual_value':dual,'true_optimum':1,'skill_required_rhs':2},'Exact LP counterexample: |1-alpha|+1 has minimum 1 at alpha=1, with dual witness (0,1). Skill formula incorrectly uses original norm 2.')
named={'.agents','.grok'};actual={'.agents','.claude'};assert not(named<actual)and actual-named
add(121,23,{'named':sorted(named),'actual':sorted(actual),'strict_subset_refusal':named<actual,'missing':sorted(actual-named)},'Isolated set predicate from reviewed source, not an invocation of the gate; shows incomparable declaration evades check 2.')
raw1=b'\x00\r\n\xff';raw2=b'\x00\n\xff';assert raw1!=raw2 and raw1.replace(b'\r\n',b'\n')==raw2.replace(b'\r\n',b'\n')
add(121,24,{'binary_a':raw1.hex(),'binary_b':raw2.hex(),'raw_equal':False,'gate_normalized_equal':True},'In-memory binary counterexample to unconditional CRLF replacement; no mirror files read or modified.')
K=Q(1,2);n=2;theta=Q(1);tau=Q(1,2);hill=theta**n/(K**n+theta**n);assert hill>=tau
add(126,25,{'sensor_count':1,'signal':1,'K':'1/2','n':n,'tau':'1/2','H':str(hill),'activated':True},'Allowed finite parameters show the aggregate Hill threshold alone does not require multiple distinct sensors. Sensor independence is a separate assumption.')
coarse_bad=273;coarse_total=280;restricted_bad=273;restricted_total=273;assert Q(restricted_bad,restricted_total)>Q(coarse_bad,coarse_total)
add(130,26,{'coarse_unresolved':f'{coarse_bad}/{coarse_total}','restricted_unresolved':f'{restricted_bad}/{restricted_total}','coarse_fraction_is_upper_bound':False},'Constructed subset arithmetic only, not an inspection of actual dossiers; removing the seven resolved out-of-scope refs raises the fraction.')
def sanitizer(s):
 tokens={'&amp;':'___AMP___','&lt;':'___LT___','&gt;':'___GT___','&quot;':'___QUOT___','&apos;':'___APOS___'}
 for k,v in tokens.items():s=s.replace(k,v)
 s=html.unescape(s)
 for k,v in tokens.items():s=s.replace(v,k)
 return s
before='<svg><text>&#60;g/&#62;</text></svg>';after=sanitizer(before);b=ET.fromstring(before);a=ET.fromstring(after);assert b.find('text').text=='<g/>'and a.find('text').find('g')is not None
add(124,27,{'before':before,'after':after,'both_parse':True,'text_became_element':True},'Exact copied sanitizer formula on synthetic in-memory XML; final parser does not detect changed semantics. Retained file not executed.')
before=Q(10);after=Q(1);assert after>0 and after<before
add(132,28,{'before_residual':str(before),'after_residual':str(after),'positive':True,'non_descent':False},'Positive residual alone does not establish non-descent. No actual danger-gate implementation tested.')
# A strictly decreasing nonnegative real residual need not hit zero in finite steps.
vals=[Q(1,2**i)for i in range(20)];assert all(a>b>0 for a,b in zip(vals,vals[1:]))
add(101,29,{'sequence':'r_n=2^-n','finite_prefix_length':20,'strictly_decreasing':True,'all_positive':True,'finite_zero':False},'Closed-form counterexample to inferring finite termination solely from strict real-valued descent; independent declared iteration bounds can still terminate.')
(H/(P+'_checks04.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
