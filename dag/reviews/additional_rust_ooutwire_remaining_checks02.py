"""Bounded independent controls for price/pruning/numeric scopes; no Rust execution."""
import hashlib,itertools,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_rust_ooutwire_remaining';fs=json.loads((H/(P+'_scope.json')).read_text())['files'];out=[]
def add(n,i,obs,limit):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'ROUT-CHECK-{n:03}','status':'observed_independent_model','source':{'path':f['path'],'sha256':f['sha256']},'observation':obs,'limitations':limit})
arity=2**63;cast=arity-2**64;assert cast<0
add(7,44,{'host_model':'64-bit usize; Rust as-i64 truncating cast','positive_arity':arity,'source_mu2_second_coordinate':cast,'ordinary_unary_coordinate':1,'wrong_lexicographic_preference':cast<1,'two_i64_MAX_arities_exact_sum':2*(2**63-1),'sum_exceeds_i64':True},'Exact independent fixed-width arithmetic model. No allocation/enumeration/native run. Public arity_sum accepts these Item values without requiring costly regime materialization; debug sum can panic and release overflow policy can wrap.')
def key(item):return({'d':0,'f':1,'r':2,'i':3}[item[0]],)+item[1:]
def canon(delta):return tuple(sorted(delta,key=key))
def apply(delta):
 n=6;nf=1;inst={(0,0)};rules=set()
 for item in delta:
  tag=item[0]
  if tag=='d':n+=1
  elif tag=='f':nf+=1
  elif tag=='r':
   if item[1]>=nf:return None
   rules.add(item[1])
  else:
   if item[1]>=nf or item[2]>=n:return None
   inst.add((item[1],item[2]))
 return n,nf,inst,rules
reqs=[(0,1),(2,3),(4,5)]
def valid(delta):
 state=apply(delta)
 if state is None:return False
 n,nf,inst,rules=state
 prof=lambda d:tuple(f in rules or(f,d)in inst for f in range(nf))
 return all(prof(i)!=prof(j)for i,j in reqs)
universe=[('d',),('f',1)]+[('r',f)for f in range(2)]+[('i',f,d)for f in range(2)for d in range(7)]
full={canon(x)for x in itertools.combinations_with_replacement(universe,2)if apply(canon(x))is not None}
pruned={canon([('f',1),('i',1,d)])for d in range(6)}|{canon([('d',),('i',0,6)])}
pruned|={canon([('i',0,a),('i',0,b)])for a in range(6)for b in range(6)if a!=b and(a in[0,1]or b in[0,1])}
vf=sorted(d for d in full if valid(d));vp=sorted(d for d in pruned if valid(d));ones=[x for x in universe if(x[0]not in ['i','r']or x[1]==0)and(x[0]!='i'or x[2]<6)]
assert len(vf)==4 and not vp and not valid(())and not any(valid((x,))for x in ones)
add(8,33,{'base':{'data_count':6,'form_arities':[1],'instances':[[0,[0]]],'uniform_rules':[],'existing_requirements':[[2,3],[4,5]]},'target':[0,1],'bounds':{'max_items':2,'max_arity':1},'full_wellformed_two_item_count':len(full),'valid_full_deltas':vf,'valid_pruned_deltas':vp,'valid_below_two':False,'rule_free_base':True,'prior_requirements_unsatisfied':True},'All candidates in a complete independent unary cost<=2 population checked. This exposes missing public preconditions, not a counterexample when engine maintains all prior requirements and challenges only collapsed pairs. No native implementation executed.')
n=2**32+1;exact=n*(n-1)//2;wrapped=((n*(n-1))%(2**64))//2
assert exact<2**64 and wrapped!=exact
add(9,30,{'usize_bits':64,'n_data':n,'exact_round_bound':exact,'wrapped_multiplication_then_division':wrapped,'exact_answer_fits_usize':True},'Pure integer control for unchecked arithmetic. Debug overflow would panic instead of wrap; no runtime overflow or allocation attempted. Divide-even-factor-first with checked multiplication preserves representable results.')
(H/(P+'_checks02.json')).write_text(json.dumps({'python':sys.version,'native_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed_independent_controls':len(out)}))
