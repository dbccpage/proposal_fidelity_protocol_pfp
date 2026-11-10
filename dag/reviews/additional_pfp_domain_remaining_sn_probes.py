"""Tiny pure S(n) state and algebra controls after full source reads."""
import sys,types,json,hashlib,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
def load(short):
 p=ROOT/('pfp/domain/sn_tower/'+short+'.py');name='audit_'+short;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return m
r=load('sn_realizations');v=load('sn_verification');app=load('sn_applications');core=load('sn_core')
channel=r.RGBChannel();channel.propose_red('p','claim');assert channel.verify_blue('p',lambda:True);assert not channel.verify_blue('p',lambda:False);assert 'p' in channel.green
firewall=v.VerificationRGBFirewall();firewall.submit_red('p');assert firewall.execute_blue('p',lambda:True);assert not firewall.execute_blue('p',lambda:False);assert 'p' in firewall.green_receipts
assert channel.verify_blue('p',lambda:'false')
simplex=r.Simplex1('x','x');assert simplex.boundary()=={'x':-1}
arrow=r.DaggerArrow('a','b','f^dagger^dagger');double=arrow.dagger().dagger();assert double!=arrow and arrow.verify_double_dagger()
session=app.SessionChannel();session.send('one');session.send('two');assert session.recv()=='ACK'
degenerate=core.S5Lift().verify_lift_orientation('x','x','x');assert degenerate
controls=[
 {'id':'PFPDOMAIN-C074','rule':'RGB_verification_revocation_and_literal_verdict','status':'counterexample_observed','channel_green_after_false':True,'firewall_green_after_false':True,'string_false_accepted':True,'limit':'Pure in-memory toy channels; no signatures or actual external authorization issued.'},
 {'id':'PFPDOMAIN-C075','rule':'simplex_degenerate_boundary','status':'counterexample_observed','endpoints':['x','x'],'computed_boundary':simplex.boundary(),'expected_formal_difference':{},'degenerate_triangle_orientation_check':degenerate},
 {'id':'PFPDOMAIN-C076','rule':'dagger_involution_includes_label','status':'counterexample_observed','original_label':arrow.label,'double_label':double.label,'endpoint_only_verifier':arrow.verify_double_dagger()},
 {'id':'PFPDOMAIN-C077','rule':'single_use_session_send_count','status':'counterexample_observed','sends_before_one_receive':2,'accepted':True,'limit':'No transport or actual message was sent; state-only object ignores payload.'}
]
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_sn_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'ids':[x['id'] for x in controls]}))
