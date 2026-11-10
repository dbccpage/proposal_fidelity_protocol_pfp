"""Exact synthetic C040 controls; no original writes or external calls."""
import copy
import importlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import additional_challenges_031_040_validate as audit

def guard(event,args):
    if event in {'socket.connect','socket.getaddrinfo','subprocess.Popen','os.system'}:
        raise RuntimeError('AUDIT_FORBIDDEN:'+event)
sys.addaudithook(guard)
FAMILY='c040_m_theory_toroidal_cremmer_julia_scalar_count'
solve,evaluate=audit.load_owners(FAMILY)
records=[]
def record(name,case,answer=None):
    answer=copy.deepcopy(solve(case) if answer is None else answer)
    try:verdict=evaluate(case,answer)
    except Exception as e:verdict={'exception':type(e).__name__,'message':str(e)}
    records.append({'name':name,'case':case,'answer':answer,'evaluation':verdict})
    return answer
def case(k,query,**kwargs):return {'id':'audit_fixture','k':k,'query':query,**kwargs}

positive=[]
for k in range(1,9):
    for query in ['scalars','coset','branching','vectors']:
        c=case(k,query);a=solve(c)
        positive.append({'k':k,'query':query,'evaluation':evaluate(c,a),'independent':audit.independent(FAMILY,c,a)})
c=case(7,'coset');a=solve(c);a['coset'].update(G='made_up_group',K='1');record('false_group_and_compact_names',c,a)
a=solve(c);del a['coset']['G'];del a['coset']['K'];record('missing_group_names',c,a)
c=case(7,'branching');a=solve(c);a['branching']=[['adjoint(fiction)',63],['banana',70]];record('false_representation_labels',c,a)
c=case(6,'vectors');a=solve(c);a['vectors']['dual_forms']=-999;record('negative_inconsistent_vector_component',c,a)
a=solve(c);a['vectors']={'total':27};record('omitted_vector_components',c,a)
c=case(1,'scalars');a=solve(c);a['scalars'].update(dual_C_mu_nu_i=99,dual_kk_vectors=-99);record('canceling_invalid_scalar_components',c,a)
c=case(7,'scalars');a=solve(c);del a['id'];del a['D'];record('missing_binding_and_dimension',c,a)
record('unknown_query_reference_refusal',case(7,'fermions'))
record('missing_k_reference_refusal',{'id':'audit_fixture','query':'scalars'})
record('IIB_k1_reference_checker_disagreement',case(1,'scalars',theory='IIB'))
# Mutating a returned branching answer should not alter future solves. Restore
# the source module's in-memory table in finally; never modify source bytes.
algebra=importlib.import_module(FAMILY+'.reference_solver.coset_algebra')
original=copy.deepcopy(algebra.COSET_DATA[7]['branching'])
try:
    a=solve(case(7,'branching'));a['branching'][1][0]='mutated_return_alias'
    record('returned_branching_alias_contaminates_future_solve',case(7,'branching'))
finally:algebra.COSET_DATA[7]['branching']=original
out={'scope':'Harmless synthetic fixtures only; owner imports after full-body review; no network/provider or child calls.',
     'positive_controls':positive,'root_closure_controls':audit.reduction_root_data(),'counterexamples':records,
     'limits':['Dimension matching does not prove representation branching or physical duality.','Cartan matrices and real-form/compact-subgroup identifications are admitted.','Shared mutable return was probed only in memory and restored.']}
(HERE/'additional_challenges_031_040_c040_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'positive_controls':len(positive),'positive_verdicts':[r['evaluation']['verdict'] for r in positive],
                  'counterexamples':[(r['name'],r['evaluation'].get('verdict',r['evaluation'].get('exception'))) for r in records]}))
