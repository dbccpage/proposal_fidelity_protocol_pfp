"""Persist the full Monte Carlo diagnostic source review while grading is pending."""
import hashlib,json,runpy
from fractions import Fraction as F
from pathlib import Path
H=Path(__file__).resolve().parent;P='additional_rust_quantum_probability_remaining'
np=H/(P+'_notes.json');n=json.loads(np.read_text())
n['35']={'assessment':'Full347-line noise_mc owner read. A seedable wrapping LCG supplies low32-bit threshold draws (19-49); the planar-grid simulation classifies each generated edge vector, counts three classes, and emits empirical fractions/mean Hamming weight (71-130). Positive grid/trial admission is present, and a size sweep varies dimensions/seeds (133-150). Tests248-319 cover zero/one noise, one finite p=.5 sample, a particular .05-versus.4 comparison, grid counts and zero-argument refusals.',
 'limitations':['No native simulation was run. Source tests and a deterministic pseudorandom sequence are not evidence of IID physical noise, a threshold theorem or decoder latency.','Probability p is neither finite-checked nor restricted to[0,1]. Values<=0 and>=1 silently clamp at the Bernoulli helper while the receipt retains the invalid input p (RQPR-F011).','Threshold quantization uses floor(p*(2^32-1))/2^32 rather than exact p; consecutive LCG values are deterministic and seed|1 aliases adjacent even/odd seeds.','The open fraction is not globally increasing in p: for one square face its ideal IID probability is(1-(1-2p)^4)/2, zero at both0and1 and1/2atp1/2. The source own p=1 test also has all Exact.','No grid/trial work bound, accumulation overflow guard, uncertainty interval or empirical model-validation step is supplied. The separate count scaffold is not connected to the simulation.']}
np.write_text(json.dumps(n,indent=2)+'\n');runpy.run_path(str(H/(P+'_checkpoint.py')))
rp=H/(P+'.json');r=json.loads(rp.read_text());f=json.loads((H/(P+'_scope.json')).read_text())['files'][35]
ev=lambda a,b:{'path':f['path'],'sha256':f['sha256'],'lines':[a,b]}
finding={'id':'RQPR-F011','severity':'medium','title':'Noise simulation accepts invalid Bernoulli parameters',
 'finding':'noise_mc_planar_grid validates m and trials but not p. Lcg::bernoulli returns false for p<=0 and true for p>=1, while the receipt retains the supplied p and labels the run IID Bernoulli(p). Thus p=-1 and p=2 produce accepted diagnostic receipts for nonexistent probability models instead of typed refusals. Nonfinite inputs are also not rejected at admission.',
 'evidence':[ev(38,48),ev(71,85),ev(110,129)],
 'recommended_action':'Require finite0<=p<=1 at the public simulation boundary and describe the discrete pseudorandom threshold approximation explicitly. Add out-of-range and nonfinite parameter regressions.',
 'validation':'Exact control-flow substitution at p=-1 and p=2; no original Rust execution.'}
r['findings']=[x for x in r['findings'] if x['id']!=finding['id']]+[finding]
c={'id':'RQPR-C014','claim':'The noise module produces reproducible empirical class counts under a declared pseudorandom finite bit-flip model. The ideal single-face open probability is not monotone over the whole p interval, and finite simulation counts do not prove physical noise assumptions or code thresholds.',
 'evidence':[ev(19,49),ev(71,150),ev(273,281),ev(311,319)],
 'dependencies':['Valid finite p in[0,1] as a missing caller/admission premise','The declared finite planar complex and classifier','Distinguishing pseudorandom threshold output from an ideal IID probability law'],
 'limitations':['No native replay, confidence interval, hardware measurement or threshold proof.','A selected low-p/high-p comparison supplies no global monotonicity theorem.']}
r['claims']=[x for x in r['claims'] if x['id']!=c['id']]+[c]
prob=lambda p:(1-(1-2*p)**4)/2
values=[{'p':str(p),'ideal_single_face_open_probability':str(prob(p))} for p in [F(0),F(1,2),F(1)]]
assert [prob(p) for p in [F(0),F(1,2),F(1)]]==[F(0),F(1,2),F(0)]
cp=H/(P+'_noise_controls.json');cp.write_text(json.dumps({'method':'Independent exact binomial-parity identity, not source simulation','passed':True,'single_face_values':values,'invalid_parameter_source_branches':[{'p':-1,'every_draw':False},{'p':2,'every_draw':True}]},indent=2)+'\n')
r['validation']=[x for x in r['validation'] if x.get('id')!='RQPR-NOISE-CONTROLS']
r['validation'].append({'id':'RQPR-NOISE-CONTROLS','path':str(cp.relative_to(H.parents[1])).replace('\\','/'),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'passed':True,'native_execution':False})
r['audit_state']='frozen_while_awaiting_repaired_model_control_post_freeze_evaluation'
rp.write_text(json.dumps(r,indent=2)+'\n')
with (H/(P+'.md')).open('a',encoding='utf-8') as md:md.write('\n\n## Monte Carlo source checkpoint\n\nCoverage is36/51 full bodies,15pending. The complete noise_mc owner exposes an invalid-p admission gap(RQPR-F011), empirical-versus-IID limits, and a globally false monotonic reading of open fraction. An exact single-face parity control gives0,1/2,0atp=0,1/2,1. No native simulation was executed. The checkpoint is frozen while the separate repaired model control awaits grading.\n')
print(json.dumps({'full':r['full_source_read_count'],'remaining':len(r['remaining_work']),'claims':len(r['claims']),'findings':len(r['findings']),'report_sha256':hashlib.sha256(rp.read_bytes()).hexdigest()}))
