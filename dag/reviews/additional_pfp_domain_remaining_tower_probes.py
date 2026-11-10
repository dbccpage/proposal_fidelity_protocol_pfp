"""Finite tower controls after complete owner reads; no retained runs or external sources."""
import sys,types,json,hashlib,importlib.util
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[];controls=[]
for name in ['pfp','pfp.domain','pfp.domain.tower']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(short):
 p=ROOT/('pfp/domain/tower/'+short+'.py');name='pfp.domain.tower.'+short;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);setattr(sys.modules['pfp.domain.tower'],short,m);bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return m
gold=load('golden_corpus');g=load('grammar');w=load('wire');registry=load('registry');status=load('stage_status');checks=load('checks');parser=load('parser');profile=load('profile');alt=load('alternation');pol=load('tower_policies');up=load('updown_maps');cells=load('cells')
def control(i,rule,status,**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':status,**kw})
calls=[]
def checker(_):calls.append(1);raise AssertionError('synthetic failing checker')
status.BINDINGS=(status.CheckerBinding(35,'synthetic_failing_checker',run=checker),);grade=status.stage_status(35).grade;assert grade=='COMPUTED' and not calls
control(69,'stage_grade_requires_observed_checker_evidence','counterexample_observed',stage=35,returned_grade=grade,synthetic_checker_calls=len(calls),registry_status=registry.STAGES[35].status,limit='Only in-memory audit module binding changed; original source preserved.')
def q(value):
 value=Fraction(value);return w.application(18,g.Atom(str(int(value<0))),g.Atom(format(abs(value.numerator),'b')),g.Atom(format(value.denominator,'b')))
emptydual=w.application(17,q(7),q(7),w.application(3));parser.validate_dual_cert(emptydual)
edges=(('a','b'),('b','c'),('c','a'));residual=w.application(3,*(w.application(2,g.Atom(u),g.Atom(v),q(1)) for u,v in edges));flow=w.application(3,*(w.application(19,g.Atom(u),g.Atom(v),q(1)) for u,v in edges));dual=w.application(17,q(3),q(3),flow);harmonic=w.application(16,g.Atom('h'),residual,dual);host={edge:Fraction(1) for edge in edges};strong=checks.check_l1_cycle(harmonic,host,host);assert strong=='FINITE_LOCAL_CHECKED'
fake=w.application(16,g.Atom('h'),residual,emptydual)
try:checks.check_l1_cycle(fake,host,host);raise AssertionError('accepted fake')
except w.WireError as exc:refusal=str(exc)
control(70,'weak_dual_shape_versus_bound_weighted_L1_certificate','bounded_positive_and_negative_controls_observed',equal_scalars_empty_flow_accepted_by_parser=True,bound_triangle_strong_status=strong,fake_receipt_strong_refusal=refusal,limit='Exact three-edge host c,w only; physical interpretation and host custody are supplied.')
postfix='! '+' '.join(['#1/1']*65);deep=w.parse_postfix(postfix)
try:w.parse_wire(w.emit_wire(deep));raise AssertionError('accepted deep raw')
except w.WireError as exc:depth_refusal=str(exc)
control(71,'wire_profile_depth_agreement','counterexample_observed',postfix_accepted_nested_applications=65,raw_roundtrip_refusal=depth_refusal,limit='Small bounded depth discrepancy only; no exponential DAG expansion or resource exhaustion executed.')
same=w.application(0,g.Diff(),g.Atom('0'),g.Atom('0'));parser.validate_packet_semantics(same)
try:profile.validate_stage(same,1);raise AssertionError('accepted wrong lift')
except w.WireError:pass
simplex=w.application(5,g.Atom('10'),g.Atom('0'),g.Atom('1'),g.Atom('10'));edge=w.application(6,g.Atom('x'),g.Atom('y'),g.Atom('1'));badmetric=w.application(7,simplex,edge,edge,edge);parser.validate_packet_semantics(badmetric)
badtriangle=w.application(7,simplex,w.application(6,g.Atom('0'),g.Atom('1'),g.Atom('1')),w.application(6,g.Atom('0'),g.Atom('10'),g.Atom('1')),w.application(6,g.Atom('1'),g.Atom('10'),g.Atom('11')));parser.validate_packet_semantics(badtriangle)
control(72,'tower_semantic_lift_and_metric_boundary','counterexample_observed',same_two_generators_accepted_by_parser=True,same_generators_rejected_by_profile=True,metric_three_duplicate_foreign_edges_accepted=True,triangle_lengths_1_1_3_accepted=True,limit='Partial parser checks only; separate geometry owners may supply stronger validation.')
triples=[]
for source in ['<>','op<>','<a>','op<<1><0>>','op<<11>op<<1><0>>op<<1><1>>>']:
 node=parser.parse_packet(source);assert parser.serialize_packet(node)==source and w.parse_wire(source)==node
 assert w.parse_tagged_json(w.emit_tagged_json(node))==node and w.parse_dag(w.emit_dag(node))==node;triples.append(source)
assert up.d_1(up.u_0(g.Diff()))==g.Diff() and isinstance(up.d_1(g.Atom('0')),up.NonDescentReceipt)
assert alt.evaluate_full_five_alternation((0,1)) and not alt.evaluate_naive_four_collapse((0,1));assert not alt.evaluate_full_five_alternation((1,2))
state=pol.SurvivorState(0,frozenset({('a','b'),('c','d')}));new=pol.apply_birth_death_step(state,frozenset({('a','b')}),frozenset({('e','f')}));assert len(new.raw_survivors)==2
registry.check_registry();assert len(registry.STAGES)==101
control(73,'bounded_grammar_maps_alternation_and_set_accounting','bounded_positive_and_negative_controls_observed',syntax_roundtrips=len(triples),old_singleton_left_inverse=True,new_atom_explicit_non_descent=True,five_quantifier_true_domain_0_1=True,naive_paired_collapse_false=True,five_quantifier_false_domain_1_2=True,birth_death_cardinality=[2,1,1,2],registry_entries=101,limit='The finite alternation example requires 0 in the domain; registry collision checks are not proofs of all101 stage obligations.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_tower_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'ids':[c['id'] for c in controls]}))
