#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/hilbert_space.rs"] pub mod hilbert_space;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_hermitian.rs"] pub mod exact_hermitian;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_operator.rs"] pub mod exact_operator;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/pauli.rs"] pub mod pauli;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_state.rs"] pub mod quantum_state;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_channel.rs"] pub mod exact_channel;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/density_matrix.rs"] pub mod density_matrix;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/engine_bridge.rs"] pub mod engine_bridge;

use core_number_theory::rational::{Rational,ri};
use core_number_theory::cyclotomic::GaussianRat as G;
use linear_algebra::backend::basic_matrix::BasicMatrix as M;
use linear_algebra::exact_field::matrix as mx;
use quantum_state::{RayVector,QuantumState};
fn bad()->Rational{Rational::new_raw(1.into(),0.into())}
fn bg()->G{G{re:bad(),im:ri(0)}}
fn report<T:std::fmt::Debug,F:FnOnce()->T+std::panic::UnwindSafe>(name:&str,f:F){
 match std::panic::catch_unwind(f){Ok(x)=>println!("{}={:?}",name,x),Err(_)=>println!("{}=PANIC",name)}
}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 report("ray_bad_admission",||RayVector::try_new(vec![bg()]));
 report("ray_bad_norm",||RayVector::try_new(vec![bg()]).unwrap().norm_sq());
 report("operator_bad_admission",||exact_operator::ExactOperator::try_new(M::from_row_major(1,1,vec![bg()]).unwrap()));
 report("hermitian_bad_control",||exact_hermitian::check_hermitian(&M::from_row_major(1,1,vec![bg()]).unwrap()));
 report("eigenpair_bad_scalar",||exact_hermitian::eigen_residual(&mx::identity(1).unwrap(),&bg(),&[G::from_ints(1,0)]));
 report("weighted_bad_scalar",||exact_channel::ExactKrausChannel::try_weighted(1,1,vec![(bad(),mx::identity(1).unwrap())],"bad"));
 report("weighted_budgeted_bad_control",||{let mut b=linear_algebra::exact_field::rational_bareiss::RationalBudget::new(linear_algebra::exact_field::rational_bareiss::RationalLimits{max_scalar_ops:100,max_elements:4,max_bits:16});exact_channel::ExactKrausChannel::try_weighted_with_budget(1,1,vec![(bad(),mx::identity(1).unwrap())],"bad",&mut b)});
 report("state_public_shape_projector",||QuantumState{dim:1,amplitudes:vec![],label:String::new()}.to_projector_cmatrix());
 report("state_index_overflow",||QuantumState::computational_basis(&hilbert_space::HilbertSpace::try_new(1,"").unwrap(),usize::MAX,""));
 let q=Rational::new(1.into(),num_bigint::BigInt::from(1)<<2000usize);
 report("ray_tiny_f64",||RayVector::try_new(vec![G::from_rational(q.clone())]).unwrap().to_f64_amplitudes());
 report("bridge_tiny_control",||engine_bridge::rational_to_c64(&q));
 for x in [1e-300,1e300]{let z=QuantumState::try_normalized_with_norm(&hilbert_space::HilbertSpace::try_new(1,"").unwrap(),vec![num_complex::Complex::new(x,0.0)],"").unwrap();println!("normalization_{x}_reported_norm={:?};valid={:?}",z.1,z.0.validate());}
 report("stinespring_nonisometry_application",||exact_channel::apply_stinespring(&M::from_row_major(1,1,vec![G::from_ints(2,0)]).unwrap(),1,1,&mx::identity(1).unwrap()));
}
