#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/hilbert_space.rs"] pub mod hilbert_space;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_hermitian.rs"] pub mod exact_hermitian;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_operator.rs"] pub mod exact_operator;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/pauli.rs"] pub mod pauli;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_state.rs"] pub mod quantum_state;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_channel.rs"] pub mod exact_channel;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/density_matrix.rs"] pub mod density_matrix;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/engine_bridge.rs"] pub mod engine_bridge;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/dagger_category.rs"] pub mod dagger_category;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/frobenius_algebra.rs"] pub mod frobenius_algebra;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/classical_structure.rs"] pub mod classical_structure;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/local_operator_algebra.rs"] pub mod local_operator_algebra;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/algebraic_qft.rs"] pub mod algebraic_qft;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/coherent_interference.rs"] pub mod coherent_interference;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/cancellation_certificates.rs"] pub mod cancellation_certificates;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/heisenberg_picture.rs"] pub mod heisenberg_picture;

use linear_algebra::backend::basic_matrix::BasicMatrix as M;
use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::{ri,Rational};
fn report<T:std::fmt::Debug,F:FnOnce()->T+std::panic::UnwindSafe>(name:&str,f:F){match std::panic::catch_unwind(f){Ok(x)=>println!("{}={:?}",name,x),Err(_)=>println!("{}=PANIC",name)}}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 report("frobenius_extreme_shape",||frobenius_algebra::FrobeniusAlgebra::from_trace_form(M::from_row_major(usize::MAX,0,vec![]).unwrap(),M::from_row_major(0,0,vec![]).unwrap(),M::from_row_major(0,0,vec![]).unwrap()));
 let bad=G{re:Rational::new_raw(1.into(),0.into()),im:ri(0)};
 report("classical_bad_scalar",||classical_structure::ClassicalStructure::from_basis(vec![vec![bad.clone()]]));
 report("cayley_bad_scalar",||heisenberg_picture::cayley_jet(&mx::identity(1).unwrap(),&bad.re));
 for d in 1..=3{assert_eq!(dagger_category::DaggerCategory::zigzag(d).unwrap(),mx::identity(d).unwrap());let a=frobenius_algebra::FrobeniusAlgebra::copy(d).unwrap();assert!(a.is_commutative()&&a.is_dagger());assert_eq!(a.special_scalar(),Some(G::from_ints(1,0)));}
 println!("dagger_snake_and_copy_frobenius_dimensions1_3=PASS");
 let net=algebraic_qft::AlgebraicQft::qubit_chain(2).unwrap();assert!(net.defects(true).unwrap().is_empty());println!("two_qubit_net_isotony_locality_duality=PASS");
 let c=[G::from_ints(1,0),G::from_ints(1,0),G::from_ints(0,1)];let twin=coherent_interference::diagonal_twin(&c).unwrap().unwrap();assert_ne!(coherent_interference::interfered_weight(&c).unwrap(),coherent_interference::interfered_weight(&twin.twin).unwrap());
 assert_eq!(coherent_interference::sorkin_interference(&c,&[vec![0],vec![1],vec![2]],8).unwrap(),ri(0));println!("diagonal_twin_and_quadratic_order3_zero=PASS");
 let mut cert=cancellation_certificates::certify_phase_cancellation(3,&[0,1,2]).unwrap().unwrap();assert!(cert.reflected_pairs.is_none());assert!(cancellation_certificates::verify_phase_cancellation(&cert).unwrap());cert.reflected_pairs=Some(vec![(0,1)]);assert!(!cancellation_certificates::verify_phase_cancellation(&cert).unwrap());println!("odd_polygon_cancellation_and_invalid_pairing_refusal=PASS");
}
