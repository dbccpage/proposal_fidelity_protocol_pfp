#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/cptp_trajectory_verifier.rs"] pub mod cptp_trajectory_verifier;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/unitary_operator.rs"] pub mod unitary_operator;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/product_defect_bound.rs"] pub mod product_defect_bound;

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
