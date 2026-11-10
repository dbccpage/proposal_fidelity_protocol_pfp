#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/entropy.rs"] pub mod entropy;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/fidelity.rs"] pub mod fidelity;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/trace_norm_certificate.rs"] pub mod trace_norm_certificate;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/entanglement.rs"] pub mod entanglement;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/purification.rs"] pub mod purification;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_relative_entropy.rs"] pub mod quantum_relative_entropy;

pub use cached_quantum::{density_matrix,quantum_state,hilbert_space,exact_operator,exact_hermitian,exact_channel,pauli};
use core_number_theory::rational::ri;
fn main(){
 let empty_mass=entropy::Entropy::shannon(&[0.0,0.0]).unwrap();assert_eq!(empty_mass,0.0);println!("zero_mass_Shannon_Ok={empty_mass}");
 let overflow=entropy::Entropy::shannon(&[1e308,1e308]).unwrap();assert!(overflow.is_nan());println!("finite_weights_overflow_Shannon_Ok_NaN=true");
 let ray=quantum_state::RayVector::from_ints(&[(1,0),(0,0),(0,0),(1,0)]).unwrap();let rho=density_matrix::ExactDensityMatrix::pure(&ray).unwrap();
 assert_eq!(entanglement::Entanglement::concurrence_exact(&rho,10000).unwrap(),ri(1));let enc=entanglement::Entanglement::concurrence_enclosure(&rho,16,10000).unwrap();assert!(enc.lo()<=&ri(1)&&enc.hi()>=&ri(1));println!("Bell_concurrence_exact_and_enclosure=PASS");
 let p=purification::WeightedPurification::of(&rho).unwrap();assert_eq!(p.reduced_state().unwrap(),*rho.matrix());assert_eq!(purification::Purification::fidelity_exact(&rho,&rho,10000).unwrap(),ri(1));println!("weighted_purification_replay_and_self_fidelity=PASS");
 let y=pauli::Pauli::Y.to_operator();let cert=trace_norm_certificate::sign_from_spectrum(y.as_matrix(),&[ri(-1),ri(1)]).unwrap();assert_eq!(cert.trace_norm(),&ri(2));let zero=linear_algebra::exact_field::matrix::zeros(2,2).unwrap();assert!(trace_norm_certificate::TraceNormCertificate::try_new(y.as_matrix().clone(),cert.positive_part().clone(),cert.negative_part().clone(),zero).is_err());println!("trace_norm_dual_gap_control=PASS");
 let other=density_matrix::ExactDensityMatrix::pure(&quantum_state::RayVector::basis(4,0).unwrap()).unwrap();assert!(!quantum_relative_entropy::QuantumRelativeEntropy::support_included(&rho,&other).unwrap());println!("noncommuting_pure_support_refusal=PASS");
}
