"""Independent finite models of declared source semantics; no Rust/native execution."""
import hashlib,itertools,json,pathlib,re,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_rust_ooutwire_remaining';fs=json.loads((H/(P+'_scope.json')).read_text())['files'];out=[]
def add(n,i,obs,limits):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'ROUT-CHECK-{n:03}','status':'observed_independent_model','source':{'path':f['path'],'sha256':f['sha256']},'observation':obs,'limitations':limits})
groups={}
for k in range(16):
 t=[bool((k>>i)&1)for i in range(4)];behavior=(t[0]!=t[1],t[2]!=t[3]);groups.setdefault(str(behavior),[]).append(k)
assert len(groups)==4 and all(len(v)==4 for v in groups.values())
add(1,47,{'complete_domain':'all16Boolean functions of(coverage,admission)','classes':groups,'sealed_OR_table_number':14,'sealed_OR_behavior':[True,False]},'Exhaustive independent finite truth-table calculation, not native parity. Coverage is held fixed across compared data; arbitrary multi-bit/stateful observers require different premises.')
n=2;instances={(0,(0,))};forms=[1];rules=set();pair=(0,99)
def profile(d):return {0}if 0<=d<n and(0,(d,))in instances else set()
def raw_observer(d):return 0 in rules or(0,(d,))in instances
declared_separable=all(0<=d<n for d in pair)and profile(pair[0])!=profile(pair[1]);observer=raw_observer(pair[0])!=raw_observer(pair[1]);assert observer and not declared_separable
add(2,47,{'regime':{'data_count':n,'forms':forms,'instances':[[0,[0]]],'rules':[]},'pair':pair,'unary_context':[None],'sealed_observer_separates':observer,'domain_checked_separable':declared_separable},'Independent direct predicates from read bodies; Pair(0,99) is publicly constructible and ordered but mark99 is unadmitted. No original Rust invoked.')
before={0};after={0,1};assert (0 in before)!=(1 in before)and(0 in after)==(1 in after)
add(3,51,{'data':[0,1],'form_arity':1,'admitted_instances':[[0]],'before_rule_verdicts':[True,False],'after_uniform_rule_verdicts':[True,True],'separation_lost':True},'Illustrates declared OR semantics; admission is monotone in positive facts but separation need not be monotone. Requirement checking belongs to response layer, not a claim this admission is invalid.')
def scan(source):
 out=[];rest=source
 while 'pub fn 'in rest:
  tail=rest.split('pub fn ',1)[1];positions=[tail.find(x)for x in ['{',';']if x in tail];end=min(positions)if positions else len(tail);sig=tail[:end]
  if '->'in sig:
   ret=sig.split('->',1)[1].strip()
   if re.search(r'(?<![A-Za-z0-9_])(?:Event|WorldEvent|BEvent)(?![A-Za-z0-9_])',ret):out.append(sig.split('(',1)[0])
  rest=tail[end:]
 return out
comment='// pub fn phantom() -> Event { unimplemented!() }\n';callback='pub fn check(f: fn() -> Event) -> bool { true }\n';assert scan(comment)==['phantom']and scan(callback)==['check']
add(4,27,{'comment_only':comment,'comment_findings':scan(comment),'callback_parameter':callback,'callback_findings':scan(callback)},'Independent lexical control of displayed signature scanner, not Rust parser or native replay. Complete read already admits aliases/async/traits omissions; this adds false positives from comments and parameter arrows.')
ra=['a'];rb=['b'];event='a';sa=ra if event in ra else ra+[event];sb=rb if event in rb else rb+[event];assert len(ra)==len(rb)and len(sa)!=len(sb)
add(5,1,{'initial_token_lists':[ra,rb],'same_structure_key_before':[1,[],[],[],[]],'fixed_event':'AdmitDatum(a)','post_lengths':[len(sa),len(sb)]},'Exact one-datum no-form structural counterexample: canonical token erasure is not a transition congruence under fixed external token events. Does not refute equivariance with appropriately transported event/token identities.')
add(6,31,{'n_data':2,'arity':100,'slot_tuple_count':3**100,'hole_context_count':3**100-2**100,'admit_form_accepts_positive_usize100':True,'slot_tuples_allocates_all_then_filters':True},'Exact cardinality arithmetic only; no allocation or resource exhaustion attempted. Source APIs expose no context enumeration cap, so finite mathematical domain does not mean feasible runtime resource bound.')
(H/(P+'_checks.json')).write_text(json.dumps({'python':sys.version,'native_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed_independent_controls':len(out)}))
