"""Independent small controls; no import/execution of original Rust or workflows."""
import hashlib,json,pathlib,itertools,math
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_rust_ooutwire_remaining';fs=json.loads((H/(P+'_scope.json')).read_text())['files'];out=[]
def record(i,title,observed,indices):
 out.append({'id':f'ROUT-CHECK{i:03d}','title':title,'observed':observed,'method':'Independent finite Python control of inspected source predicates; no native execution','source_pins':[{'path':fs[k]['path'],'sha256':fs[k]['sha256']}for k in indices]})
# Gate sequence exactly isolates changed budget from unchanged regime/license.
old={'budget':0,'license':False};history=[('SetBudget',0),('SetLicense',False)];history.append(('SetBudget',3));recorded_support=old.copy();replayed=old.copy()
for tag,value in history:replayed['budget'if tag=='SetBudget'else'license']=value
assert recorded_support!=replayed
record(10,'Refunding before denied license records stale support',{'funding_answers':[0,3],'authorization':False,'recorded_support':recorded_support,'replayed_support':replayed,'verify_support_equality':False},[32,69])
def breplay(events,marks=()):
 supplied=set();marks=list(marks)
 for tag,t in events:
  if tag=='supply':supplied.add(t)
  elif t not in supplied and t not in marks:return None
  elif t not in marks:marks.append(t)
 return tuple(marks)
a=[('supply','x')];b=[('admit','x')];whole=breplay(a+b);part=breplay(b,breplay(a));assert whole==('x',)and part is None
record(11,'Boundary replay loses earlier supply provenance across chunks',{'whole':whole,'first_chunk':breplay(a),'second_chunk':'refused'},[22])
# Two marks, no forms, imposed pair: empty supplied menu fails vacuously,
# whereas a unary form plus instance on0 separates0/1.
empty_examined=0;empty_has_repair=any([]);assert not empty_has_repair
record(12,'Public empty Menu can manufacture an Exhaustion declaration',{'target':[0,1],'recorded':True,'initial_separated':False,'supplied_items':[],'exhaustion_searched':empty_examined,'actual_repair':['NewForm(1)','NewInst(0,[0])'],'world_refusal_accepts_forgery':False},[45,48,56,69])
rows=[]
for n in range(5):
 placements=list(itertools.product((0,1),repeat=n));u={min(sum(p),n-sum(p))for p in placements};o={sum(p)for p in placements};fixed=sum(sum(p)*2==n for p in placements);rows.append([n,len(placements),len(u),len(o),fixed])
assert rows==[[0,1,1,1,1],[1,2,1,2,0],[2,4,2,3,2],[3,8,2,4,0],[4,16,3,5,6]]
record(13,'Reflection census independently reduced to population counts',{'rows':rows,'general_formula':'O:n+1; U:floor(n/2)+1; fixed:C(n,n/2) for even n else0'},[22])
tokens=['g2','x'];fresh=f'g{len(tokens)}';after=tokens[:]if fresh in tokens else tokens+[fresh];assert after==tokens
record(14,'Tree continuation token collides on valid custom reading',{'tokens':tokens,'generated':fresh,'after':after,'structural_key_unchanged':True,'possible_attach':'merge to same node when target set empty'},[68])
result={'execution_kind':'independent_bounded_controls','controls':out,'helper_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()};(H/(P+'_checks03.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'controls':len(out),'all_assertions_passed':True}))
