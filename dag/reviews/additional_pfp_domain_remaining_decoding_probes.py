"""Exact tiny decoding controls; record original import failures separately from isolated arithmetic."""
import sys,types,ast,importlib.util,json,hashlib
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
for name in ['pfp','pfp.domain','pfp.domain.decoding','pfp.domain.mssn_research','pfp.domain.mssn_research.shared_kernel']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path,omit_result_import=False):
 p=ROOT/path;m=types.ModuleType(name);m.__file__=str(p);sys.modules[name]=m;tree=ast.parse(p.read_text());omitted=[]
 if omit_result_import:
  omitted=[n.lineno for n in tree.body if isinstance(n,ast.ImportFrom) and n.module=='pfp.domain.mssn_research.shared_kernel.result'];tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and n.module=='pfp.domain.mssn_research.shared_kernel.result')]
 bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'omitted_import_lines':omitted});exec(compile(tree,str(p),'exec'),m.__dict__);return m
load('pfp.domain.mssn_research.shared_kernel.result','pfp/domain/mssn_research/shared_kernel/result.py')
load('pfp.domain.decoding.errors','pfp/domain/decoding/errors.py');vocab=load('pfp.domain.decoding.vocabulary','pfp/domain/decoding/vocabulary.py');coh=load('pfp.domain.decoding.cohomology','pfp/domain/decoding/cohomology.py')
failures={};modules={}
for stem in ['antimorphism','polygraph','token_frontier']:
 name='pfp.domain.decoding.'+stem;path=f'pfp/domain/decoding/{stem}.py'
 try:load(name,path);failures[stem]=None
 except ImportError as e:failures[stem]=str(e)
 modules[stem]=load(name,path,True)
assert all(failures.values())
anti=modules['antimorphism'];model=anti.AntimorphismTransitionModel('test',frozenset({'a','b'}),frozenset(),anti.ReversalMap(()),frozenset({anti.ProtectedDistinction('a','b')}));first=model.down_map({'a':'x','b':'y'});second=first.down_map({'x':'z','y':'z'});assert second.states==frozenset({'z'})
nil=coh.EntropyCocycle(-5,('not a rational',)).coboundary_is_nilpotent();assert nil
poly=modules['polygraph'];r1=poly.RewriteStep('l','root','L','J');r2=poly.RewriteStep('r','root','R','J');g=poly.TarskiPolygraph((r1,r2));cell=poly.Confluence2Cell('NO_REGISTERED_APEX','L','R',(r1,),(r2,),'J');assert g.validate_confluence(cell)
bad=poly.Confluence2Cell('NO_REGISTERED_APEX','L','R',(poly.RewriteStep('l','other','L','J'),),(r2,),'J')
try:g.validate_confluence(bad);bad_refused=False
except Exception:bad_refused=True
assert bad_refused
front=modules['token_frontier'];v=vocab.WireVocabulary(('a','b','c'));f=front.TokenFrontier.evaluate_step(v,[-1,2,1],[2]);assert f.retained_mass.mass==Fraction(1,2) and f.candidates[0].constrained_probability==1
out={'runtime':sys.version,'source_bindings':bindings,'controls':[
 {'id':'PFPDOMAIN-C038','rule':'decoding_result_owner_import_contract','status':'import_failures_observed','failures':failures,'limit':'Exact module bodies loaded with inert package shells and read-vetted dependencies, no package-wide import effects.'},
 {'id':'PFPDOMAIN-C039','rule':'protected_distinctions_under_composed_down_maps','status':'counterexample_observed_in_isolated_body','first_states':sorted(first.states),'second_states':sorted(second.states),'protected_original_pair':['a','b'],'limit':'Failed Result import alone omitted; unmodified down_map body. Ordinary module import currently blocked.'},
 {'id':'PFPDOMAIN-C040','rule':'entropy_cocycle_nilpotency_check','status':'vacuous_acceptance_observed','negative_degree_and_nonrational_coefficient_accepted':nil,'operator_supplied':False},
 {'id':'PFPDOMAIN-C041','rule':'finite_registered_tail_join_boundary','status':'bounded_positive_and_negative_controls_observed_in_isolated_body','registered_tail_join_accepted':True,'altered_location_refused':bad_refused,'unregistered_apex_ignored':True,'limit':'Proves tail-join checking, not peak registration or global confluence; failed import omitted.'},
 {'id':'PFPDOMAIN-C042','rule':'global_probability_weight_nonnegativity','status':'counterexample_observed_in_isolated_body','weights':[-1,2,1],'admitted_ids':[2],'accepted_retained_mass':'1/2','constrained_probability':'1','limit':'Negative masked weight survives exact math path; ordinary module import blocked.'}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_decoding_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out['controls'],indent=2))
