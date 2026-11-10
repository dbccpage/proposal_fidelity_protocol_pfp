"""Read-vetted archived function bodies; injected independent one-qubit algebra.

No package imports, original parser, provider, data fixtures or native execution.
The parser boundary here accepts only synthetic one-qubit controls; this is not
evidence of the original parser's behavior.
"""
import sys
sys.dont_write_bytecode=True
import ast,copy,itertools,json,__future__
from fractions import Fraction
from types import SimpleNamespace
from collections.abc import Mapping
import additional_pfp_tests_remaining_audit as a

base='pfp/tests/fixtures/retired_quantum_reference/'
paths=[base+'stabilizer_solver.py.txt',base+'certificate_checker.py.txt']
class ParseError(ValueError):
    code='SYNTHETIC_INVALID'
class Pauli:
    def __init__(self,word):
        if word not in 'IXYZ' or len(word)!=1:raise ValueError('bounded one qubit only')
        self.word=word
    @classmethod
    def identity(cls,n):
        assert n==1
        return cls('I')
    def to_symplectic_vector(self):return {'I':(0,0),'X':(1,0),'Z':(0,1),'Y':(1,1)}[self.word]
    def commutes_with(self,other):return self.word=='I' or other.word=='I' or self.word==other.word
    def multiply(self,other):
        if self.word=='I':return 0,Pauli(other.word)
        if other.word=='I':return 0,Pauli(self.word)
        if self.word==other.word:return 0,Pauli('I')
        phase,out={('X','Y'):(1,'Z'),('Y','Z'):(1,'X'),('Z','X'):(1,'Y'),('Y','X'):(3,'Z'),('Z','Y'):(3,'X'),('X','Z'):(3,'Y')}[(self.word,other.word)]
        return phase,Pauli(out)
class Term:
    def __init__(self,p,s,w):self.pauli=Pauli(p);self.target_sign=s;self.weight=Fraction(w)
    def penalty_for_eigenvalue(self,lam):return self.weight*(1-self.target_sign*lam)/2
class Hamiltonian:
    def __init__(self,terms):self.terms=terms
    def find_anticommuting_pair(self):
        for i,j in itertools.combinations(range(len(self.terms)),2):
            if not self.terms[i].pauli.commutes_with(self.terms[j].pauli):return i,j,self.terms[i],self.terms[j]
        return None
def parse(case):
    if case.get('num_qubits')!=1:raise ParseError('synthetic parser only supports one qubit')
    ts=[Term(t['p'],t['s'],t['w']) for t in case['terms']]
    return SimpleNamespace(num_qubits=1,term_ids=list(range(len(ts))),hamiltonian=Hamiltonian(ts))
def load_functions(path):
    t=ast.parse('\n'.join(a.source(path)),filename=path)
    t.body=[n for n in t.body if isinstance(n,ast.FunctionDef)]
    g={'Fraction':Fraction,'Mapping':Mapping,'PauliString':Pauli,'parse_challenge':parse,'ChallengeParseError':ParseError}
    exec(compile(t,path,'exec',flags=__future__.annotations.compiler_flag),g)
    return g
solver=load_functions(paths[0]);checker=load_functions(paths[1])
solve=solver['solve'];check=checker['check_certificate']
alphabet=[(p,s,w) for p in 'IXYZ' for s in (-1,1) for w in ('1','1/2')]
counts={'cases':0,'solved':0,'out_of_scope':0,'checked_pass':0}
for size in range(3):
    for choices in itertools.product(alphabet,repeat=size):
        case={'num_qubits':1,'terms':[dict(p=p,s=s,w=w) for p,s,w in choices]}
        result=solve(case);verdict=check(case,result)
        assert verdict['verdict']=='PASS'
        counts['checked_pass']+=1;counts['cases']+=1
        nonidentity={p for p,s,w in choices if p!='I'}
        if len(nonidentity)>1:
            assert result['status']=='OUT_OF_SCOPE';counts['out_of_scope']+=1
        else:
            constant=sum((Fraction(w)*(1-s)/2 if p=='I' else Fraction(w)/2 for p,s,w in choices),Fraction(0))
            coefficient=sum((-Fraction(w)*s/2 for p,s,w in choices if p!='I'),Fraction(0))
            expected_energy=constant-abs(coefficient)
            assert result['status']=='SOLVED' and Fraction(result['ground_state_energy'])==expected_energy
            assert result['degeneracy']==(2 if coefficient==0 else 1)
            counts['solved']+=1
case={'num_qubits':1,'terms':[dict(p='Z',s=1,w='1')]}
good=solve(case)
controls=[]
def observe(label,payload,source_case=case):
    try:
        r=check(source_case,payload)
        controls.append({'label':label,'verdict':r['verdict'],'status':r.get('status'),'error':r.get('error')})
    except Exception as e:controls.append({'label':label,'exception':type(e).__name__,'message':str(e)[:180]})
wrong=copy.deepcopy(good);wrong['ground_state_energy']='1';wrong['energy']=wrong['E']=[1,1];wrong['ground_state_energy_rational']={'numerator':1,'denominator':1}
observe('wrong_energy_control',wrong)
for ref,label in [('²','unicode_isdigit_nondecimal'),('9'*5000,'oversized_decimal_reference')]:
    bad=copy.deepcopy(good);bad['basis']=[ref];observe(label,bad)
bad=copy.deepcopy(good);bad['certificate']['basis']=[999];bad['certificate']['num_generators']=999;bad['num_qubits']=999;bad['n']=999;bad['case_id']='wrong-case'
observe('ignored_auxiliary_identity_and_basis_aliases',bad)
bad=copy.deepcopy(good);bad['certificate']['term_decompositions'][0]['id']=999
# Solver shares the primary and alternate list; split them to test alternate only.
bad=copy.deepcopy(good);bad['certificate']['term_decompositions']=copy.deepcopy(good['decomposition']);bad['certificate']['term_decompositions'][0]['id']=999
observe('unresolved_secondary_decomposition_id',bad)
bad=copy.deepcopy(good);bad['decomposition'][0]['sign']=1.0
observe('floating_sign_one',bad)
observe('unknown_arbitrary_nonempty_refusal',{'status':'UNKNOWN','refusal_code':{'unrelated':True}}, {'num_qubits':0,'terms':[]})
assert controls[0]['verdict']=='FAIL'
assert controls[1]['exception']=='ValueError' and controls[2]['exception']=='ValueError'
assert all(r['verdict']=='PASS' for r in controls[3:])
result={'runtime':sys.version.split()[0],'status':'bounded_observed','source_pins':[{'path':p,'sha256':a.row(p)['sha256']} for p in paths], 'finite_one_qubit_census':counts,'controls':controls,'limits':'AST-extracted full reviewed functions with an independent injected one-qubit Pauli/parser boundary. Original retired parser/Pauli modules and any live/native provider never imported. Counts validate these finite controls only, not original parser compatibility, multi-qubit phases or current production behavior.'}
a.write('_probe25.json',result)
print(json.dumps(result,indent=2))
