"""Read-vetted local immune owner probes; no EIS import or coordinator constructor."""
import sys,types,importlib.util,json,hashlib,ast
from pathlib import Path
from fractions import Fraction
from dataclasses import dataclass
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
for name in ['pfp','pfp.domain','pfp.domain.immune']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(stem):
 p=ROOT/f'pfp/domain/immune/{stem}.py';bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});name='pfp.domain.immune.'+stem;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
allostery=load('allostery');complement=load('complement');danger=load('danger_gate');mhc=load('mhc');proof=load('proofreading');thymus=load('thymus');clonal=load('clonal_selection')
p=ROOT/'pfp/domain/immune/turn_loop_wiring.py';tree=ast.parse(p.read_text());verdict=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ImmuneTurnVerdict');owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='TurnLoopImmuneCoordinator');method=next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_candidate_move')
m=types.ModuleType('bounded_immune_method');sys.modules[m.__name__]=m;m.__dict__.update(dataclass=dataclass,DangerDecision=danger.DangerDecision)
future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0);module=ast.fix_missing_locations(ast.Module(body=[future,verdict,method],type_ignores=[]));exec(compile(module,str(p),'exec'),m.__dict__)
bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'isolated_ast_ranges':[[40,54],[76,134]],'omitted':'imports and coordinator constructor; no EIS or default fixture loading'})
fake_self=types.SimpleNamespace(mhc=mhc.MhcPresentationWindow(),allostery=allostery.AllostericQuorumGate(),proofreader=proof.KineticProofreader(),danger_gate=danger.TwoSignalDangerGate(),complement=complement.ComplementCascade())
v=m.evaluate_candidate_move(fake_self,1,'independent tiny text',[danger.Signal1AstMatch('x','x',Fraction(1))],danger.Signal2DangerState('x',danger.DangerSeverity.HIGH,1,'unchecked'),detector_votes=0)
assert v.quarantined and not v.proofreading_confirmed and v.quorum_state==allostery.QuorumState.QUIESCENT and v.complement_effectors>0
fixture=ROOT/'dag/reviews/additional_pfp_domain_remaining_immune_synthetic_panel.json';fixture.write_text(json.dumps({'fixture_count':999,'sealed_sha256':'z'*64,'entries':[{'entry_id':'one','category':'synthetic','content':'clean','content_sha256':'z'*64}]}),encoding='utf8')
panel=thymus.SelfPanel.load_canonical(fixture);assert panel.sealed_sha256=='z'*64 and panel.fixture_count==1 and panel.entries[0].content_sha256=='z'*64
entry=thymus.SelfPanelEntry;g1=thymus.ThymusGate([entry('same','test','alpha','a'*64)]);g2=thymus.ThymusGate([entry('same','test','beta','b'*64)]);assert g1.self_panel.sealed_sha256==g2.self_panel.sealed_sha256
parent=clonal.ClonalCandidate('unrelated','x','clean');clone=clonal.ClonalCandidate('child','x','clean',parent_id='actual_parent');killed,receipt=clonal.ClonalSelectionEngine.check_kill_condition(clone,parent,thymus.SelfPanel.from_strings(['clean']));assert killed and receipt.parent_id=='unrelated'
base=clonal.ClonalCandidate('base','x','x',affinity_score=Fraction(5),half_life_runs=3);batched=clonal.ClonalSelectionEngine.apply_half_life_decay(base,7,tau=2);stepped=base
for _ in range(7):stepped=clonal.ClonalSelectionEngine.apply_half_life_decay(stepped,1,tau=2)
assert batched==stepped and batched.affinity_score==Fraction(5,8)
out={'runtime':sys.version,'source_bindings':bindings,'controls':[
 {'id':'PFPDOMAIN-C031','rule':'coordinator_delay_and_quorum_enforcement','status':'counterexample_observed','quarantined':v.quarantined,'proofreading_confirmed':v.proofreading_confirmed,'quorum_state':v.quorum_state.value,'effectors':v.complement_effectors,'limit':'Exact isolated source method with actual read-vetted local components; no coordinator constructor, EIS import or irreversible host effect.'},
 {'id':'PFPDOMAIN-C032','rule':'self_panel_content_custody','status':'counterexample_observed','nonhex_unrelated_content_and_seal_accepted':True,'declared_count_999_became':panel.fixture_count,'different_contents_same_id_sequence_seal':True,'fixture_path':fixture.relative_to(ROOT).as_posix()},
 {'id':'PFPDOMAIN-C033','rule':'clone_parent_receipt_binding','status':'counterexample_observed','clone_parent_id':clone.parent_id,'receipt_parent_id':receipt.parent_id,'purge_claim':killed,'actual_deletion_performed':False},
 {'id':'PFPDOMAIN-C034','rule':'fixed_tau_decay_telescoping','status':'bounded_positive_control_observed','initial_affinity':'5','elapsed':7,'tau':2,'batched_and_seven_single_steps_equal':True,'final_affinity':str(batched.affinity_score),'limit':'One exact example supports the source floor-difference telescoping identity for fixed tau; no biological or learned-affinity claim.'}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_immune_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
