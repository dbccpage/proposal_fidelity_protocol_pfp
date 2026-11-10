"""Bounded controls over read-vetted scoring owners, without package bootstraps."""
import sys,types,importlib.util,json,hashlib
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sources=[]
for name in ['pfp','pfp.domain','pfp.domain.shared_kernel','pfp.domain.entities','pfp.domain.errors','pfp.domain.validation']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path):
 p=ROOT/path;sources.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
load('pfp.domain.exceptions','pfp/domain/exceptions.py')
for n in ['authority_effect','exact','path','residual_colour','residual_drop']:
 load('pfp.domain.shared_kernel.'+n,'pfp/domain/shared_kernel/'+n+'.py')
shared=load('pfp.domain.shared_kernel.coboundary_score','pfp/domain/shared_kernel/coboundary_score.py')
load('pfp.domain.errors.errors','pfp/domain/errors/errors.py')
load('pfp.domain.errors','pfp/domain/errors/__init__.py')
load('pfp.domain.validation.validation','pfp/domain/validation/validation.py')
load('pfp.domain.validation','pfp/domain/validation/__init__.py')
entity=load('pfp.domain.entities.coboundary_score','pfp/domain/entities/coboundary_score.py')
small=shared.CoboundaryScoreResult(1e-12,0,0,1e-12,True)
assert small.phi1==0 and small.combined_score==0
inconsistent=entity.CoboundaryScoreResult('p',Fraction(5),Fraction(4),Fraction(999),Fraction(1),Fraction(999))
wire=inconsistent.to_dict();wire.update(is_legal='false',is_exact_candidate='false',post_residual_norm='0',dual_witness_ref='a'*64)
decoded=entity.CoboundaryScoreResult.from_dict(wire)
assert decoded.is_legal is True and decoded.is_exact_candidate is True
out={'runtime':sys.version,'source_bindings':sources,'import_context':'Only explicitly loaded, fully reviewed modules and Python stdlib; inert parent namespace packages. No provider or native execution.','controls':[
 {'id':'PFPDOMAIN-C012','rule':'shared_score_positive_residual_preservation','status':'counterexample_observed','input_phi1':'1e-12 float','output':small.to_dict(),'limit':'Shared-kernel class only; native ScoringPort imports the separate stronger entity class.'},
 {'id':'PFPDOMAIN-C013','rule':'entity_score_literal_boolean_wire_admission','status':'counterexample_observed','input_is_legal':'false string','input_is_exact_candidate':'false string','output_is_legal':decoded.is_legal,'output_is_exact_candidate':decoded.is_exact_candidate,'limit':'Constructor still enforces exact zero post-norm and digest syntax; no host workflow execution or verified witness is inferred.'},
 {'id':'PFPDOMAIN-C014','rule':'score_residual_drop_arithmetic_binding','status':'counterexample_observed','prior':'5','post':'4','claimed_drop':str(inconsistent.residual_drop),'actual_difference':'1','normalized_efficiency':str(inconsistent.normalized_efficiency),'limit':'The record trusts host-computed fields; this demonstrates its own admission boundary, not an error in an unexecuted scoring evaluator.'}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_score_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out,indent=2))
