"""Small independent finite controls; imports no repository implementation."""
import sys,json,hashlib,itertools,collections,datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PREFIX=ROOT/'dag/reviews/additional_paper_011_history_ledgers'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(s):return json.loads(PREFIX.with_name(PREFIX.name+s).read_text(encoding='utf8'))
sc=json.loads((ROOT/'dag/reviews/additional_paper_011_history_ledger_scope.json').read_text(encoding='utf8'))
read_ledger=load('_read_ledger.json');out=[]
for r in sc['files']:
 p=ROOT/r['path'];body=p.read_text(encoding='utf-8-sig');lines=body.splitlines();spans=[x['lines'] for x in read_ledger if x['path']==r['path']]
 coverage=collections.Counter(i for lo,hi in spans for i in range(lo,hi+1))
 assert sha(p)==r['sha256'];assert set(coverage)==set(range(1,len(lines)+1));assert set(coverage.values())=={1}
 out.append({'path':r['path'],'sha256':sha(p),'bytes':len(p.read_bytes()),'line_count':len(lines),'chunk_count':len(spans),'checks':[{'rule':'frozen_source_hash','status':'matched'},{'rule':'body_line_coverage','status':'exactly_once'}]})
# R2L/R2F source contract: cardinality and requirement endpoints are represented fields.
lf={'L':{'num_data':2,'required_pair':[0,1]},'F':{'num_data':3,'required_pair':[1,2]}}
assert lf['L']['num_data']!=lf['F']['num_data']
# Two finite kernels with identical endpoints, diagonal law and chosen witness,
# but an extra oriented relation away from that designated pair.
carrier=range(3);a,b=0,1;edge_sets=[{(0,1)},{(0,1),(1,2)}]
kernel_rows=[]
for edges in edge_sets:
 delta=lambda x,y:(x,y) in edges
 zero=lambda value:not value
 assert all(zero(delta(x,x)) for x in carrier)
 assert not zero(delta(a,b))
 kernel_rows.append({'a':a,'b':b,'nonzero_pairs':[list(p) for p in sorted(edges)],'diagonal_zero':True,'chosen_pair_nonzero':True,'apart_1_2':not zero(delta(1,2)),'apart_2_1':not zero(delta(2,1))})
assert kernel_rows[0]['apart_1_2']==False and kernel_rows[1]['apart_1_2']==True and kernel_rows[1]['apart_2_1']==False
# Four-gate abstraction from the stated convention: no observation yields D=0,Z=1.
valuations=set(itertools.product([False,True],[False,True],[(False,True),(True,False),(True,True)]))
flat={(r,p,d,z) for r,p,(d,z) in valuations};assert len(flat)==12
omissions=[]
for gate in range(4):
 witness=tuple(i!=gate for i in range(4));assert witness in flat
 omissions.append({'omitted_gate':gate,'other_three_true_omitted_false':list(witness)})
# Direct double-deletion boundary, implemented without any source code import.
def boundary(cell,signed=True):
 result=collections.Counter()
 for i in range(len(cell)):result[cell[:i]+cell[i+1:]]+=(-1)**i if signed else 1
 return result
def double_boundary(cell,signed=True):
 result=collections.Counter()
 for face,c in boundary(cell,signed).items():
  for lower,d in boundary(face,signed).items():result[lower]+=c*d
 return {str(k):v for k,v in result.items() if v}
cell_count=0
for length in range(7):
 for cell in itertools.product(range(2),repeat=length):
  assert double_boundary(cell)=={};cell_count+=1
signless=double_boundary((0,1,2),False);assert signless
# Native F016's initial facts, without claiming bounded enumeration proves all traces.
cols=[[0]];prot={(1,0)}
sep=lambda i,j:any((i in c)!=(j in c) for c in cols)
prot_sep=lambda i,j:(i,j) in prot and sep(i,j)
assert sep(0,1) and sep(1,0) and prot_sep(1,0) and not prot_sep(0,1)
result={'runtime':sys.version,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(Path(__file__)),'source_execution':'none; independent controls only','source_files':out,'controls':[
 {'id':'P011LEDGER-C01','rule':'L_F_internal_fields_are_distinguishable','status':'counterexample_observed','result':lf,'limit':'Distinguishability does not justify selecting an admission reading.'},
 {'id':'P011LEDGER-C02','rule':'kernel_can_encode_orientation_beyond_chosen_pair','status':'counterexample_observed','result':kernel_rows,'limit':'Finite instantiations of the read structure contract; no Lean elaboration or original execution.'},
 {'id':'P011LEDGER-C03','rule':'four_gate_nonentailment_is_not_sixteen_valuation_independence','status':'finite_abstraction_checked','result':{'valuation_count':len(flat),'omission_witnesses':omissions},'limit':'Abstracts the ledger convention; does not independently certify every native state realization.'},
 {'id':'P011LEDGER-C04','rule':'alternating_double_deletion_cancels_with_repeated_vertices','status':'bounded_control_passed','result':{'binary_vertex_lists_lengths_0_through_6':cell_count,'signless_triangle_nonzero':signless},'limit':'127 finite controls support the elementary pairing argument, not fresh validation of the general Lean theorem.'},
 {'id':'P011LEDGER-C05','rule':'reverse_protection_initial_state_for_native_F016','status':'initial_facts_checked','result':{'occ':[0,1],'asserted':[[1,0]],'wit':[[1,0]],'prot':[[1,0]],'obs':cols,'budget':1,'licensed':True,'halted':False,'sep_0_1':sep(0,1),'sep_1_0':sep(1,0),'protSep_0_1':prot_sep(0,1),'protSep_1_0':prot_sep(1,0)},'limit':'All-traces stability follows from the separately read sufficiency theorem plus symmetric separation; it is not established by this finite initial-state check.'}
]}
PREFIX.with_name(PREFIX.name+'_controls.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'source_files':len(out),'line_count':sum(r['line_count'] for r in out),'controls':[{'id':r['id'],'status':r['status']} for r in result['controls']]}))
