"""Manual post-freeze judgments for the delivered ungated answer only."""
import hashlib
import importlib.util
import json
from pathlib import Path

H=Path(__file__).resolve().parent
B=H.parent
spec=importlib.util.spec_from_file_location('validator',B/'summarize_runs.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
run,run_sha=v.read_frozen_receipt(H/'runs/01_ungated/run.json')
assert run_sha=='28a9aa26ee1fa6caa87817541573b3a86d4ead368d4ad8d979a05c5a667eb93c'
assert run['answer_sha256']=='92dff27860cdb2b6db06847c45bf30d4556b1a614ac20805f921024061650a00'
answer=run['answer_text'];lines=answer.splitlines(keepends=True)
assert len(answer)==35015 and len(lines)==641

def q(lo,hi):
    start=sum(map(len,lines[:lo-1]));quote=''.join(lines[lo-1:hi]).rstrip('\r\n')
    return {'quote':quote,'character_range':[start,start+len(quote)],
            'line_range':[lo,lo+len(quote.splitlines())-1]}

def omission():
    return {'kind':'full_final_body_review_for_omission','character_range':[0,len(answer)],
            'line_range':[1,len(lines)]}

rows=[]
def add(cid,points,assessment,*ev):
    rows.append({'criterion_id':cid,'points':points,'assessment':assessment,'evidence':list(ev)})

add('spectrum.block_reduction',4,
    'Correct Pauli tensor products, exact Hamiltonian matrix and invariant even/odd reduction; both factors2 are preserved.',q(21,39),q(49,58),q(75,81))
add('spectrum.energies',4,
    'The odd-block determinant gives -K+/-2epsilon and the even eigenvalueK twice. Later degeneracies are explicitly identified.',q(86,119))
add('spectrum.projectors',6,
    'Correct normalized generic eigenvectors, outer-product projectors and orthogonality. The explicit J=0 diagonal case supplies computational-basis eigenvectors with their energies when the generic denominators vanish. The later epsilon>0 display must be read with that earlier exception; no credit is supplied from a prior answer.',q(178,186),q(188,198),q(229,240),q(304,312))
add('spectrum.coincident_energies',4,
    'Both K=+epsilon and K=-epsilon crossings and their rank3 eigenspaces are explicitly derived and the corresponding projectors merged.',q(122,126),q(243,245),q(314,316))
add('spectrum.zero_radius',2,
    'At epsilon=0 the even/odd computational projectors are explicit, and K=0 is correctly assigned the sole identity projector.',q(318,324))

add('dynamics.state',6,
    'Correct phase-resolved generic ket derived in the final answer, valid for epsilon>0. However, no separate epsilon=0 evolved ket is supplied; the final expression still divides by epsilon. The earlier zero-radius spectrum is not an explicit delivered time-evolution branch.',q(529,553),q(556,565),omission())
add('dynamics.probability',4,
    'Correct transition probability with an explicit zero-radius branch and the J=0,Delta!=0 check.',q(399,421))
add('dynamics.supremum',4,
    'Correct all-parameter piecewise supremum, including the constant zero cases.',q(441,457))
add('dynamics.earliest_and_constant_branches',3,
    'Correct pi/(4epsilon) for J!=0 and recognition that every time maximizes when J=0. It nevertheless incorrectly states there is no unique earliest time; the ordered domain t>=0 has earliest maximizer0.',q(459,476))

add('pure_state.reduced_density',4,
    'The delivered answer completes the partial-trace argument and gives diag(|a|^2,|b|^2) before truncation. The explicit norm calculation gives trace1. The cutoff in a later expanded restatement does not erase this already delivered result.',q(576,578),q(616,635),q(638,641))
add('pure_state.entropy',0,
    'No entropy formula, log-base calculation or endpoint convention is delivered. A section heading naming entropy does not supply the missing result.',q(569,569),q(638,641),omission())
add('pure_state.concurrence',0,
    'No concurrence formula or derivation is delivered before the final-answer cutoff.',q(569,569),q(638,641),omission())
add('pure_state.CHSH',0,
    'No CHSH value, correlation matrix or measurement optimization is delivered. The heading supplies no mathematical credit.',q(569,569),q(638,641),omission())
add('pure_state.maximal_entanglement_reachability',0,
    'No necessary-and-sufficient reachability condition is delivered.',q(638,641),omission())
add('pure_state.earliest_maximal_entanglement',0,
    'No earliest maximally entangled time or its parameter branches is delivered.',q(638,641),omission())

add('thermal.Gibbs_state',0,'No Gibbs density matrix is delivered.',q(638,641),omission())
add('thermal.partition_function',0,'No partition function is delivered.',q(638,641),omission())
add('thermal.partial_transpose',0,'No thermal partial transpose or its four eigenvalues is delivered.',q(638,641),omission())
add('thermal.entanglement_criterion',0,'No thermal entanglement iff or separability boundary is delivered.',q(638,641),omission())
add('thermal.thermal_limits',0,'No beta=0 or zero-radius Gibbs-state limit is delivered.',q(638,641),omission())

add('checks.conventions',1,
    'Pauli matrices, computational basis and Hamiltonian conventions are explicit and correct. Entropy log-base and partial-transpose conventions are not delivered.',q(3,16),q(49,55),omission())
add('checks.normalization',2,
    'The explicit evolved-state norm identity is a valid consistency check on the admitted nonzero-radius branch.',q(576,578))
add('checks.initial_condition',2,
    'The answer explicitly substitutes t=0 and recovers |01>.',q(563,563))
add('checks.decoupled_limit',1,
    'The J=0 diagonal spectrum and vanishing transition probability are checked. A complete decoupled evolved-state/thermal check is not delivered.',q(186,186),q(409,421),omission())
add('checks.nontrivial_numerical_example',0,
    'No nontrivial numerical example is evaluated. Zero-coupling symbolic branches do not constitute such an example.',omission())

counterexamples=[
    {'id':'CP-UNGATED-CE-01','criterion':'dynamics.earliest_and_constant_branches',
     'parameters':{'J':0,'Delta':1,'K':0},'probability_for_every_t':0,
     'maximizers':'[0,infinity)','earliest_maximizer':0,
     'claimed':'No unique earliest time (constant).','evidence':[q(472,476)],
     'method':'Exact constant-function argument on an ordered time domain.'},
    {'id':'CP-UNGATED-CE-02','criterion':'dynamics.state',
     'parameters':{'J':0,'Delta':0,'K':1},'Hamiltonian_diagonal':[1,-1,-1,1],
     'actual_state':'exp(it)|01>','displayed_expression_status':'Undefined Delta/epsilon and J/epsilon with no delivered evolved-ket branch.',
     'evidence':[q(550,565)],'method':'Exact diagonal action on the initial basis ket; this illustrates an omitted branch, not an incorrect generic ket.'}
]
item={'run_path':'runs/01_ungated/run.json','run_sha256':run_sha,
      'answer_sha256':run['answer_sha256'],'parent_confirmed_frozen':True,
      'classification':'delivered_partial_solution_length_truncated',
      'criteria':rows,'counterexamples':counterexamples}
p=H/'criterion_assessments.json';manual=json.loads(p.read_text(encoding='utf-8'))
manual['runs']=[x for x in manual['runs'] if x['run_path']!=item['run_path']]+[item]
assert len(rows)==25 and sum(r['points'] for r in rows)==47
p.write_text(json.dumps(manual,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'criteria':25,'ungated_total':47,'final_lines':641,'final_characters':35015}))
