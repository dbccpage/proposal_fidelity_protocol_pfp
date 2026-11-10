import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps';F=D.parent/'.fingerprint'
prior=json.loads((H/(P+'_validation_06.json')).read_text());libs={x['extern_name']:R/x['path']for x in prior['libraries']}
meta=json.loads((F/'core_quantum_physics-f9c328b190a84659/lib-core_quantum_physics.json').read_text())
for _,name,_,identity in meta['deps']:
 if name!='core_solvers':continue
 found=[p for p in F.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text().strip()),'little')==identity];assert len(found)==1
 libs[name]=D/('lib'+name+'-'+found[0].parent.name.rsplit('-',1)[1]+'.rlib')
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs')for n in ['finite_chsh_correlations','tensor_commuting_correlation_frontier','phase_blind_quotient','phase_averaged_shadow','finite_bell_extension','finite_bell_preparation']}
src=H/(P+'_probe_07.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
pub use cached_quantum::{exact_hermitian,exact_channel};
use core_number_theory::{rational::{ri,rq},cyclotomic::GaussianRat as G};
fn main(){
 use finite_chsh_correlations::*;
 let game=tensor_commuting_correlation_frontier::chsh_game_certificate().unwrap();let tau=game.operator_bound.bound.scale(&rq(1,2));
 assert!(verify_tsirelson_certificate(&game.alice,&game.bob,&tau,&game.operator_bound).unwrap());let mut wrong=game.operator_bound.clone();wrong.bound=core_number_theory::cyclotomic_field::Cyclotomic::<8>::rational(ri(0));assert!(!verify_tsirelson_certificate(&game.alice,&game.bob,&tau,&wrong).unwrap());println!("CHSH_attainment_SOS_and_tampered_bound_refusal=PASS");
 let (a,b)=tensor_embedding(&game.alice,&game.bob).unwrap();let mut v=commuting_chsh_value(&game.state,&a,&b).unwrap();v.value=core_number_theory::cyclotomic_field::Cyclotomic::<8>::rational(ri(0));assert_eq!(v.extreme(),Some(ChshExtreme::PositiveTsirelson));println!("mutable_CHSH_zero_value_reports_positive_extreme=true");
 let raw=JointAssignment{a:[2,2],b:[2,2]};assert_eq!(raw.chsh(),8);println!("public_non_sign_JointAssignment_CHSH=8");
 let group=phase_blind_quotient::UnitPhaseGroup::new(vec![G::one(),G::from_ints(-1,0)]).unwrap();assert!(phase_averaged_shadow::averages_to_dephasing(2,&group).unwrap());let m=linear_algebra::exact_field::matrix::from_fn(2,2,|_,_|G::one()).unwrap();match phase_blind_quotient::classify_descent(&m).unwrap(){phase_blind_quotient::Descent::Obstructed(w)=>assert!(phase_blind_quotient::separates(&m,&w.cancelled,&w.reinforced).unwrap()),_=>panic!()};assert!(phase_blind_quotient::gaussian_lift(&[rq(1,4),rq(3,4)]).unwrap().is_none());println!("phase_average_descent_and_nonlift_control=PASS");
 use finite_bell_preparation::{PreparedBellProblem,ResponseFunctions};use finite_bell_extension::BellLimits;use core_finite_probability::local_deterministic::LocalVertexLimits;
 let prep=PreparedBellProblem::new(vec![2,2],vec![2,2],&[ResponseFunctions{left:vec![0,0],right:vec![1,1]}],&vec![vec![ri(1)];4],BellLimits{vertices:LocalVertexLimits{assignments:16,coordinates:16,entries:256},solver_cells:10000},1000).unwrap();let c=prep.decide(0).unwrap();prep.verify(&c).unwrap();let mut wrong=c.clone();wrong.rows[0][0]=ri(1);assert!(prep.verify(&wrong).is_err());println!("shared_prior_Bell_constructive_model_and_tamper_refusal=PASS");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_07.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Six unchanged current owners, genuine pinned cached arithmetic/solvers/carriers, small synthetic exact checks only.'}
(H/(P+'_validation_07.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))
