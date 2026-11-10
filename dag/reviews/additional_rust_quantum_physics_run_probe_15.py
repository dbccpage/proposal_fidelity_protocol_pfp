import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps'
libs={x['extern_name']:R/x['path'] for x in json.loads((H/(P+'_validation_14.json')).read_text())['libraries']}
for x in json.loads((H/(P+'_validation_10.json')).read_text())['libraries']:
 if x['extern_name']=='core_combinatorics':libs[x['extern_name']]=R/x['path']
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs') for n in ['atomic_dirac_lamb_hartree_fock','pauli_spin_statistics_graph','composition_tomography','qddc','phase_estimation','time_sliced_action_shadow']}
scope={x['path']:x['sha256']for x in json.loads((H/(P+'_scope.json')).read_text())['files']}
for p in owners.values():assert hashlib.sha256(p.read_bytes()).hexdigest()==scope[p.relative_to(R).as_posix()]
src=H/(P+'_probe_15.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
pub use cached_quantum::{density_matrix,exact_channel,exact_operator,exact_hermitian,pair_exchange_characters,graded_path_sum};
use core_number_theory::rational::{ri,rq};
fn main(){
 use atomic_dirac_lamb_hartree_fock::*;
 let hook=std::panic::take_hook();std::panic::set_hook(Box::new(|_|{}));
 let empty=std::panic::catch_unwind(||run_closed_shell_rhf_scf("He",2,vec![],vec![],rq(1,2),0)).is_err();
 let short=std::panic::catch_unwind(||run_closed_shell_rhf_scf("Be",4,vec![ri(4)],vec![ri(1)],rq(1,2),0)).is_err();
 let overflow=std::panic::catch_unwind(||dirac_coulomb_alpha4_coeff(1u32<<31,1)).is_err();
 let shell=std::panic::catch_unwind(||pauli_spin_statistics_graph::pauli_shell_capacity(46341)).is_err();
 let phase=std::panic::catch_unwind(||phase_estimation::DiscretePhaseEstimation::verify_all_dyadic_phases(usize::BITS as usize)).is_err();
 std::panic::set_hook(hook);assert!(empty&&short&&overflow&&shell);println!("atomic_empty_and_short_shell_panics={empty},{short}; quantum_number_overflow={overflow}; shell_capacity_overflow={shell}; phase_shift_panic={phase}");
 let malformed=run_closed_shell_rhf_scf("He",2,vec![],vec![ri(1)],rq(1,2),1).unwrap();assert!(malformed.converged_iterate_z_eff.is_empty());assert_eq!(malformed.final_fixed_point_l1_residual,ri(0));println!("empty_iterate_nonempty_fixed_point_residual=0; accepted=true");
 assert_eq!(dirac_coulomb_alpha4_coeff(2,1).unwrap(),rq(5,128));assert!(verify_qm224_dirac_coulomb_and_lamb_shift().unwrap().lundeen_pipkin_enclosed);
 let y=pauli_spin_statistics_graph::analyze_conf2_graph(4,&[(0,1),(0,2),(0,3)]).unwrap();assert_eq!(y.conf2_betti_1,1);assert!(!y.has_y_junction_exchange_cycle);println!("Y_exchange_cycle_betti=1; named_flag=false");
 assert_eq!(composition_tomography::local_tomography_spanning_complex(2,2).unwrap().product_rank,16);assert_eq!(composition_tomography::local_tomography_spanning_real(2,2).unwrap().product_rank,9);let(p,m)=composition_tomography::rebit_state_pair().unwrap();let effect=composition_tomography::rebit_separating_projector().unwrap();let hs=linear_algebra::exact_field::involution::hs_inner;assert_eq!(hs(&effect,&p).unwrap()-hs(&effect,&m).unwrap(),rq(1,2));println!("complex_rank16_real_rank9_and_rebit_separation_half=PASS");
 use exact_operator::ExactOperator;use density_matrix::ExactDensityMatrix;use core_number_theory::cyclotomic::GaussianRat as G;use qddc::{RetractionChannel,ExactDensityStep};
 let projector=ExactOperator::from_rows(vec![vec![G::one(),G::zero()],vec![G::zero(),G::zero()]]).unwrap();let reset=RetractionChannel::try_new(projector.clone()).unwrap();let rho=ExactDensityMatrix::try_from_operator(ExactOperator::identity(2).unwrap().scale_rat(&rq(1,2)).unwrap()).unwrap();let out=reset.step(&rho,&ri(1)).unwrap();assert_eq!(out.as_operator(),&projector);assert_eq!(reset.outside_weight(&out).unwrap(),ri(0));reset.weighted_kraus().unwrap();println!("QDDC_reset_and_weighted_Kraus_admission=PASS");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_15.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=45);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Six unchanged scoped modules with cached lower dependencies. Tiny exact controls and bounded panic probes; no whole crate build or physical-theory validation.'}
(H/(P+'_validation_15.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))
