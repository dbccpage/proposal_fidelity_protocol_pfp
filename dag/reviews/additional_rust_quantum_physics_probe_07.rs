#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/finite_chsh_correlations.rs"] pub mod finite_chsh_correlations;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/tensor_commuting_correlation_frontier.rs"] pub mod tensor_commuting_correlation_frontier;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/phase_blind_quotient.rs"] pub mod phase_blind_quotient;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/phase_averaged_shadow.rs"] pub mod phase_averaged_shadow;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/finite_bell_extension.rs"] pub mod finite_bell_extension;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/finite_bell_preparation.rs"] pub mod finite_bell_preparation;

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
