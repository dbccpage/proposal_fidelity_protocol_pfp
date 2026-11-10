import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps';F=D.parent/'.fingerprint'
prior=json.loads((H/(P+'_validation_06.json')).read_text());libs={x['extern_name']:R/x['path']for x in prior['libraries']}
meta=json.loads((F/'core_quantum_physics-f9c328b190a84659/lib-core_quantum_physics.json').read_text())
for _,name,_,identity in meta['deps']:
 if name!='serde_json':continue
 found=[p for p in F.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text().strip()),'little')==identity];assert len(found)==1
 libs[name]=D/('lib'+name+'-'+found[0].parent.name.rsplit('-',1)[1]+'.rlib')
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs')for n in ['cptp_trajectory_verifier','unitary_operator','product_defect_bound']}
src=H/(P+'_probe_09.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
pub use cached_quantum::{quantum_state,exact_hermitian};
use cptp_trajectory_verifier::*;
use cptp_trajectory_verifier::workpad::*;
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let wrong=RationalInterval{lo:q(10,1),hi:q(10,1)};
 let w=PfpRationalIntervalWorkpad::from_interval(&[q(1,2),q(1,2)],Some(&[0,0]),15,&wrong,Pg3ClaimStatus::Authorized);
 assert!(w.certified);println!("entropy_ln2_wrong_point10_certified=true");
 let reversed=RationalInterval{lo:q(10,1),hi:q(-10,1)};
 assert!(PfpRationalIntervalWorkpad::from_interval(&[q(1,2),q(1,2)],None,15,&reversed,Pg3ClaimStatus::Authorized).certified);println!("reversed_interval_certified=true");
 let overflow=std::panic::catch_unwind(||PfpRationalIntervalWorkpad::from_interval(&[q(1,1)],None,64,&wrong,Pg3ClaimStatus::EvidenceOnly));println!("precision64_panics={}",overflow.is_err());
 let u=QuantumRelationalUniverse::new(1,vec![Matrix::identity(1).scale(&QC::real(q(2,1))),Matrix::identity(1).scale(&QC::real(q(-1,1)))]);
 assert_eq!(u.profile(&Matrix::identity(1)),vec![q(2,1),q(-1,1)]);let wp=PfpQubitPovmWorkpad::from_universe(&u,Pg3ClaimStatus::Authorized);assert!(wp.sum_is_identity);assert_eq!(wp.claim_status,Pg3ClaimStatus::Authorized);println!("nonpositive_POVM_profile=2,-1;workpad_authorized=true");
 let valid=QuantumRelationalUniverse::new(2,vec![proj0(),proj1()]);
 let invalid_rho=Matrix::identity(2).scale(&QC::real(q(2,1)));
 let bad=evaluate_cptp_trajectory(&valid,|_,_|true,&invalid_rho,&[],0,true);assert_eq!(bad.p2_history,vec![q(8,1)]);println!("trace4_initial_state_accepted_with_purity8=true");
 let channels=vec![unitary(pauli_x()),unitary(pauli_x()),unitary(pauli_x())];
 let res=evaluate_cptp_trajectory(&valid,|_,_|false,&proj0(),&channels,0,false);assert_eq!(res.k_star,2);assert_eq!(res.p2_history.len(),1);
 let wp=PfpPurityBudgetWorkpad::from_trajectory(0,&channels,&res,Pg3ClaimStatus::Authorized);assert_eq!(wp.steps.len(),3);assert!(wp.steps.iter().all(|s|s.admitted));assert!(wp.lemma_q3_checked);println!("terminal_at2_workpad_emits_admitted_steps2_3_4=true");
 let nerve=SimplicialNerve{contexts:vec![vec![0]],support:Box::new(|_,s|s==[0])};
 let wp=PfpContextualityHolonomyWorkpad::from_simplicial_nerve(&nerve,q(2,1),None,Terminal::OverlapGluingRefusal,Pg3ClaimStatus::Authorized);assert_eq!(wp.support_rule,"exactly_one");assert_eq!(wp.contextual_fraction_lower.0,q(2,1));println!("zero_only_support_mislabeled_exactly_one;CF_lower2_accepted=true");
 let exact=RationalInterval::entropy_nats_diag(&[q(1,2),q(1,2)],10);assert!(exact.lo>q(0,1)&&exact.hi<q(1,1)&&exact.width()<=q(1,1024));println!("actual_entropy_series_control=PASS");
 use linear_algebra::linear_algebra::complex_matrix::{CMatrix,C64};
 let mut m=CMatrix::identity(2,2);m[(0,1)]=C64::new(1e-200,0.0);let admitted=unitary_operator::UnitaryOperator::try_new(2,m,"",0.0).unwrap();assert_eq!(admitted.unitarity_defect(),0.0);
 use core_number_theory::cyclotomic::GaussianRat as G;use core_number_theory::rational::{Rational,ri};
 let small=G{re:Rational::from_float(1e-200).unwrap(),im:ri(0)};let op=cached_quantum::exact_operator::ExactOperator::from_rows(vec![vec![G::one(),small],vec![G::zero(),G::one()]]).unwrap();assert!(!op.is_unitary());println!("zero_floating_defect_nonunitary_exact_binary_matrix_accepted=true");
 let bad=product_defect_bound::GeneralOrderDefectBound::lower_bound_at(2,ri(0),ri(-1),ri(1));assert_eq!(bad,ri(64));println!("general_order_unvalidated_negative_coupling_zero_derivative_lowerbound=64");
}
''',encoding='utf-8')
runs=[]
for checked in ['yes','no']:
 cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks='+checked,'-L','dependency='+str(D)]
 for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
 exe=H/(P+'_probe_09_'+checked+'.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'overflow_checks':checked,'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if not c.returncode:
  x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
 runs.append(run)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Three unchanged current owners and pinned cached arithmetic/carrier dependencies; tiny synthetic inputs only, no fixture emission or broad crate build.'}
(H/(P+'_validation_09.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items()if k!='command'}for r in runs],indent=2))
