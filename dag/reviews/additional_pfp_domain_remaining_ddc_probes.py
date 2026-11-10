"""Tiny fixed-carrier linear algebra, trace-boundary and scalar-conversion controls."""
import sys,types,importlib.util,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
for name in ['pfp','pfp.domain','pfp.domain.ddc','pfp.domain.value_objects']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path):
 p=ROOT/path;bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
cx=load('pfp.domain.ddc.complex','pfp/domain/ddc/complex.py');co=load('pfp.domain.ddc.cochains','pfp/domain/ddc/cochains.py');cb=load('pfp.domain.ddc.coboundary','pfp/domain/ddc/coboundary.py');tr=load('pfp.domain.ddc.triad','pfp/domain/ddc/triad.py');dda=load('pfp.domain.ddc.dda','pfp/domain/ddc/dda.py')
load('pfp.domain.value_objects.base','pfp/domain/value_objects/base.py');num=load('pfp.domain.value_objects.numerics','pfp/domain/value_objects/numerics.py')
k=cx.SimplicialComplex.cycle_graph(3,with_faces=True);receipt=cb.audit_nilpotency_all_basis(k);assert receipt.is_nilpotent and receipt.num_faces_evaluated==3
matrix_missing=[list(e) for row in k.build_incidence_d1().values() for e in row if e not in k.edge_keys];assert matrix_missing==[['v0','v2']]
tracker=dda.LyapunovTracker();tracker.record_step(dda.DDALetter.C,types.SimpleNamespace(phi_1=F(1),gamma_2=F(0),xi=F(0)),'initial');tracker.record_step(dda.DDALetter.E,types.SimpleNamespace(phi_1=F(1),gamma_2=F(9),xi=F(0)),'gamma increased');tracker.record_step(dda.DDALetter.LAMBDA,types.SimpleNamespace(phi_1=F(10),gamma_2=F(9),xi=F(0)),'phi increased');assert tracker.is_strictly_monotonic()
try:dda.DDACascadeSolver(k).solve(co.Cochain1({}));refused=False
except tr.FunctionalBoundaryUnavailable:refused=True
assert refused
value=Decimal('9007199254.740993');money=num.MicroUsdSpend.from_usd(value);expected=int(value*1000000);assert money.value!=expected
assert num.MicroUsdSpend.from_usd(Decimal('-0.0000001')).value==0
nan=num.BoundedTemperature(float('nan'));tiny=co.Cochain0({'x':1e-12});assert tiny.get('x')==0
out={'runtime':sys.version,'source_bindings':bindings,'controls':[
 {'id':'PFPDOMAIN-C043','rule':'fixed_triangle_coboundary_nilpotency','status':'bounded_positive_control_observed','vertex_bases_checked':3,'face_basis_evaluations':receipt.num_faces_evaluated,'nilpotent':receipt.is_nilpotent,'limit':'One triangle carrier with a reversed boundary edge; source telescoping proves the conditional linear identity. No physical/semantic interpretation.'},
 {'id':'PFPDOMAIN-C044','rule':'d1_incidence_declared_edge_carrier','status':'counterexample_observed','declared_edge_keys':[list(e) for e in k.edge_keys],'incidence_keys_outside_edge_carrier':matrix_missing,'direct_d1_handles_reverse_orientation':True},
 {'id':'PFPDOMAIN-C045','rule':'lyapunov_total_energy_and_lambda_enforcement','status':'counterexample_observed','energy_sequence':[str(n.phi_1+n.gamma_2) for n in tracker.nodes],'letters':[n.letter.value for n in tracker.nodes],'is_strictly_monotonic':tracker.is_strictly_monotonic(),'cascade_compute_fail_closed':refused,'limit':'Trace methods consume explicit synthetic passive triad values; no disabled functional implementation substituted or native calculator executed.'},
 {'id':'PFPDOMAIN-C046','rule':'exact_and_bounded_scalar_ingress','status':'counterexamples_observed','decimal_usd':str(value),'expected_micro_usd':expected,'actual_micro_usd':money.value,'negative_tiny_usd_becomes_zero':True,'temperature_nan_accepted':True,'cochain_float_1e_minus12_becomes_zero':True}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_ddc_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out['controls'],indent=2))
