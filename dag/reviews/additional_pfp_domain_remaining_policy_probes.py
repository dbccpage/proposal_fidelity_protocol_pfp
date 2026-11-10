"""Tiny synthetic inputs for fully read standard-library-only policy owners."""
import sys,types,importlib.util,json,hashlib
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
def load(label,path):
 p=ROOT/path;bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});s=importlib.util.spec_from_file_location(label,p);m=importlib.util.module_from_spec(s);sys.modules[label]=m;s.loader.exec_module(m);return m
en=load('bounded_ensemble','pfp/domain/ensemble/models.py');civ=load('bounded_civilization','pfp/domain/civilization/models.py');el=load('bounded_elenchus','pfp/domain/civilization/elenchus.py');hy=load('bounded_hygiene','pfp/domain/claim_hygiene/models.py')
spec=en.EnsembleSpec((en.ModelRef('a',70.0,'a'),en.ModelRef('b',70.0,'b')),en.EnsembleRole.VERIFY);assert sum(m.total_params_b for m in spec.members)==140
nan=en.EnsembleSpec((en.ModelRef('nan',float('nan'),'c'),),en.EnsembleRole.VERIFY)
try:en.compute_ensemble_calibration({'a':[],'b':[]});empty_error=None
except Exception as e:empty_error=type(e).__name__
state=civ.CivilizationState();state.register_wild_prompt('x','synthetic');state.promote_to_candidate('x');review=state.promote_to_reviewed('x');assert review.to_tier==civ.PopulationTier.REVIEWED
try:state.promote_to_admitted('x','sig:ed25519:unverified');admission_refused=False
except civ.UnauthorizedAdmissionError:admission_refused=True
assert admission_refused
assert not el.SocraticElenchusBureau().interrogate('Use a re-export shim. Theorem correctness follows from quantum gauge invariance.').is_refused
x,_=hy.strip_forbidden_hype_words('This guarantees success.');y,_=hy.strip_forbidden_hype_words(x);assert x!=y
out={'runtime':sys.version,'source_bindings':bindings,'controls':[
 {'id':'PFPDOMAIN-C035','rule':'ensemble_total_parameter_ceiling_and_empty_calibration','status':'counterexamples_observed','accepted_total_params_b':140,'declared_total_ceiling_b':70,'nan_member_accepted':True,'empty_multi_model_error':empty_error},
 {'id':'PFPDOMAIN-C036','rule':'civilization_review_and_authority_boundary','status':'bounded_positive_and_negative_controls_observed','review_without_any_holdout_argument':review.status,'reason_claims_test_pass':'Passed negative selection holdout banks' in review.reason,'signature_prefix_admission_refused':admission_refused},
 {'id':'PFPDOMAIN-C037','rule':'elenchus_and_hygiene_claim_scope','status':'bounded_behavior_observed','advertised_theorem_and_boundary_laundering_example_proceeds':True,'hype_sanitizer_idempotent':False,'first':x,'second':y,'limit':'Only literal examples; no completeness or false-positive-rate estimate.'}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_policy_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
