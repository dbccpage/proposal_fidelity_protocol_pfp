"""Small G04 source-only controls; original imports are hash-bound full reads."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_native'
report=json.loads((H/(P+'.json')).read_text(encoding='utf-8'));base=R/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g04/original'
names=['code/derivation/'+x+'.py' for x in ['__init__','model','observe','candidates','iso','engine']]
names+=['research/identification_dual/dual.py','research/two_sided_commitment/two_sided.py','research/second_nofirst/nofirst.py','research/second_index/index.py']
for name in names:
 p=base/name;row=next(x for x in report['file_reviews'] if x['path']==p.relative_to(R).as_posix())
 assert row['full_source_read'] and row['sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
sys.dont_write_bytecode=True;sys.path.insert(0,str(base/'research/second_index'))
import index as ix
from derivation.model import EMPTY,AdmitDatum,Supply,AdmitForm,AdmitInst,AdmissionError,replay
from nofirst import Stake,demands
stakes={s.name:s for s in ix.declared_stakes()};checks=[]
a=(AdmitDatum('<n0>'),AdmitDatum('<n1>'));b=(Supply('<z>'),)+a;c=a+(AdmitForm(1),AdmitInst(0,(0,)))
assert replay(a)==replay(b)
counts=[ix.first_index_forward(EMPTY,x,stakes['total_apart'],ix.Observations()) for x in [a,b,c]]
assert counts==[2,3,2]
assert demands(stakes['total_apart'],replay(c[:2])) and not demands(stakes['total_apart'],replay(c))
for hist in [a,b,c]:
 for stake in stakes.values():assert ix.first_index_forward(EMPTY,hist,stake,ix.Observations())==ix.first_index_scan(EMPTY,hist,stake,ix.Observations())
checks.append({'id':'g04_exhibited_history_counts','status':'pass','first_counts':counts,'procedure_comparisons':21,'limit':'Three concrete histories; written Lean countermodels not kernel-replayed.'})
small=ix.Alphabet('<z>',('<n0>','<n1>'),(1,),3,1,2)
results=[]
for base_name in ix.BASE_NAMES:
 rectangle=ix.build_rectangle(base_name,small);assert ix.replay_check(rectangle)==0
 checked=ix.crosscheck(base_name,small,2);assert checked['reach_agrees']
 results.append({'base':base_name,'nodes':len(rectangle.nodes),'distinct_regimes':checked['first_enumerator_regimes']})
checks.append({'id':'g04_small_rectangle','status':'pass','results':results,'limit':'Depth2,one form,three data,two fresh token names; not full historical length4 rectangle or original test suite.'})
r=replay(a);cache=ix.Observations();free=Stake('collision',lambda i,j:'free');apart=Stake('collision',lambda i,j:'apart')
assert not cache.carries(free,r);cached=cache.carries(apart,r);uncached=ix.Observations().carries(apart,r)
assert not cached and uncached
checks.append({'id':'g04_stake_name_cache_admission','status':'counterexample_confirmed','cached_apart':cached,'uncached_apart':uncached,'limit':'Outside unique-name seven-stake discipline: new caller-defined stakes must bind names to immutable rules.'})
try:ix.first_index_scan(ix.base_regime('L'),(AdmitForm(0),),stakes['total_apart'],ix.Observations())
except AdmissionError:reverse_refuses=True
else:reverse_refuses=False
forward=ix.first_index_forward(ix.base_regime('L'),(AdmitForm(0),),stakes['total_apart'],ix.Observations())
assert forward==0 and reverse_refuses
checks.append({'id':'g04_invalid_suffix_domain','status':'domain_difference_confirmed','forward':forward,'reverse_refuses':reverse_refuses,'limit':'Enumerated histories are admitted throughout; equivalence must not be exported to arbitrary invalid-tail histories.'})
historical=json.loads((base/'research/second_index/receipts/index.json').read_text());partitions=0
for row in historical['reports']:
 for entry in row['stakes'].values():
  assert sum(entry['index_distribution'].values())==entry['sequences_with_an_index']==sum(entry['first_event_kinds'].values())
  assert entry['sequences_with_an_index']<=row['nodes'];partitions+=1
checks.append({'id':'g04_retained_partition_arithmetic','status':'pass','stake_base_partitions':partitions,'limit':'Arithmetic consistency of stored aggregates only, not fresh historical receipt regeneration.'})
target=H/(P+'_controls.json');out=json.loads(target.read_text(encoding='utf-8'));out['checks']=[x for x in out['checks'] if not x['id'].startswith('g04_')]+checks
target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(checks,indent=2))
