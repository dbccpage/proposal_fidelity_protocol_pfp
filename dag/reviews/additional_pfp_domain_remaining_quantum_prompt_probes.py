"""Exact tiny quantum and prompt-integrity controls; no provider execution."""
import sys,types,importlib.util,json,hashlib,itertools
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[];controls=[]
for name in ['pfp','pfp.domain','pfp.domain.quantum','pfp.domain.exact','pfp.domain.prompts','pfp.domain.prompt_representations']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path):
 p=ROOT/path;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return m
def control(i,rule,status,**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':status,**kw})
pauli=load('pfp.domain.quantum.pauli','pfp/domain/quantum/pauli.py');ham=load('pfp.domain.quantum.hamiltonian','pfp/domain/quantum/hamiltonian.py');coset=load('pfp.domain.quantum.c029_coset','pfp/domain/quantum/c029_coset.py')
single={'I':[[1,0],[0,1]],'X':[[0,1],[1,0]],'Y':[[0,-1j],[1j,0]],'Z':[[1,0],[0,-1]]}
def matrix(word):
 a,b=map(single.get,word);return [[a[i//2][j//2]*b[i%2][j%2] for j in range(4)] for i in range(4)]
def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
words=[''.join(w) for w in itertools.product('IXYZ',repeat=2)]
for x,y in itertools.product(words,repeat=2):
 a,b=pauli.PauliString(x),pauli.PauliString(y);phase,result=a.multiply(b);actual=multiply(matrix(x),matrix(y));expected=[[1j**phase*v for v in row] for row in matrix(result.word)];assert actual==expected;assert a.commutes_with(b)==(actual==multiply(matrix(y),matrix(x)));assert pauli.PauliString.from_symplectic_vector(a.to_symplectic_vector(),2)==a
control(78,'finite_pauli_multiplication_phase_and_commutation','bounded_positive_controls_observed',two_qubit_pairs=256,independent_representation='explicit4x4 tensor matrices with entries0,+/-1,+/-i; all operations exact on these small values')
count=0
for rows in itertools.product(range(8),repeat=2):
 basis=coset._kernel(list(rows),3)
 for candidate in range(8):
  compatible=[bits for bits in range(8) if all((row&bits).bit_count()%2==(row&candidate).bit_count()%2 for row in rows)];expected=min(sum(w for q,w in enumerate((1,2,3)) if bits&(1<<q)) for bits in compatible);assert coset._minimum_weight(candidate,basis,[1,2,3])==expected;count+=1
control(79,'GF2_kernel_coset_minimum_independent_enumeration','bounded_positive_controls_observed',matrices=64,candidates_per_matrix=8,cases=count,limit='Tiny internal algebra owners only; no retained challenge examples, native matching certificates or physical code geometry evaluated.')
bad=pauli.PauliString.from_symplectic_vector([0.5,0],1);assert bad.word=='Z'
control(80,'symplectic_input_is_binary','counterexample_observed',supplied_vector=[0.5,0],accepted_word=bad.word)
parsed=ham.parse_challenge({'n':1,'terms':[{'pauli':'X'},{'id':0,'pauli':'Z'}]});assert parsed.term_ids==(0,0)
control(81,'explicit_and_implicit_hamiltonian_term_id_uniqueness','counterexample_observed',accepted_term_ids=list(parsed.term_ids),limit='Parser identity boundary; certificate consumers not executed.')
pack=load('pfp.domain.prompts.packets','pfp/domain/prompts/packets.py');envelope=pack.PacketEnvelope(schema_id='synthetic',task_data={},protected_boundary='x',budget=1,candidate_payload={'x':1});old=envelope.envelope_hash;envelope.candidate_payload['x']=2;envelope.authority_effect='Granted';assert envelope.envelope_hash==old and envelope.candidate_payload['x']==2
control(82,'packet_seal_and_authority_survive_mutation','counterexample_observed',payload_before=1,payload_after=2,hash_unchanged=True,authority_after=envelope.authority_effect,nonfinite_encoding=pack.canonical_json_bytes({'x':float('nan')}).decode(),limit='Construction-time validator does check original hash and None authority; no dispatched request or downstream revalidation was executed.')
load('pfp.domain.exceptions','pfp/domain/exceptions.py');load('pfp.domain.exact.errors','pfp/domain/exact/errors.py');load('pfp.domain.exact.q','pfp/domain/exact/q.py');evaluator=load('pfp.domain.evaluator','pfp/domain/evaluator.py');ev=evaluator.ProposalEvaluator(config=evaluator.EvaluatorConfig(require_exactness=True,max_proposals=0));same=ev.evaluate_proposal('equal',1,1);tiny=ev.evaluate_proposal('rounded',1e-12,0);assert same.is_admissible and tiny.is_admissible and tiny.initial_l1_mass==0
control(83,'proposal_evaluator_strict_descent_and_exactness','counterexample_observed',equal_mass_admissible=same.is_admissible,equal_mass_details=same.details,require_exactness=True,float_initial='1e-12',retained_initial=str(tiny.initial_l1_mass),zero_max_proposals_selects=ev.select_best_proposal([('p',1,0,1,None)]) is not None)
common=load('pfp.domain.prompt_representations.common','pfp/domain/prompt_representations/common.py');compression=load('pfp.domain.prompts.compression','pfp/domain/prompts/compression.py');nodes=[{'node_id':'r','parent_id':None,'system':'system','user':'α😀','task_id':'t','attempt_id':'a','answer_schema':{'type':'string'}},{'node_id':'c','parent_id':'r','slot':0,'system':'system','user':'β','task_id':'t','attempt_id':'b','answer_schema':{'type':'integer'}}];tree=compression.compress_prompt_tree(nodes);expanded=compression.expand_prompt_tree(tree);assert [x['user'] for x in expanded]==['α😀','β'];assert len(tree.environments)==1 and expanded[1]['answer_schema']=={'type':'integer'}
tree.environments[next(iter(tree.environments))].answer_schema['type']='boolean'
try:compression.expand_prompt_tree(tree);raise AssertionError('mutation accepted')
except ValueError as exc:mutation_refused='PROMPT_TREE_DIGEST_MISMATCH' in str(exc)
assert mutation_refused
control(84,'prompt_compression_byte_span_and_use_time_integrity','bounded_positive_and_negative_controls_observed',unicode_user_roundtrip=True,shared_environment_count=1,schema_override_preserved=True,nested_mutation_refused=mutation_refused,provider_token_savings_claim=None)
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_quantum_prompt_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'ids':[x['id'] for x in controls]}))
