#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/hilbert_space.rs"] pub mod hilbert_space;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_hermitian.rs"] pub mod exact_hermitian;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_operator.rs"] pub mod exact_operator;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/pauli.rs"] pub mod pauli;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_state.rs"] pub mod quantum_state;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_channel.rs"] pub mod exact_channel;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/density_matrix.rs"] pub mod density_matrix;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/engine_bridge.rs"] pub mod engine_bridge;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/measurement.rs"] pub mod measurement;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/measurement_update.rs"] pub mod measurement_update;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/kraus_operators.rs"] pub mod kraus_operators;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_channel.rs"] pub mod quantum_channel;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/stinespring_dilation.rs"] pub mod stinespring_dilation;

pub mod entanglement{pub use cached_quantum::entanglement::{Entanglement,EntanglementError};}
use linear_algebra::linear_algebra::complex_matrix::{CMatrix,C64};
use quantum_state::QuantumState;
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::Rational;
fn report<T:std::fmt::Debug,F:FnOnce()->T+std::panic::UnwindSafe>(name:&str,f:F){match std::panic::catch_unwind(f){Ok(x)=>println!("{}={:?}",name,x),Err(_)=>println!("{}=PANIC",name)}}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let m=measurement::Measurement::computational_basis(1);
 for a in [2.0,f64::NAN]{report("measurement_unvalidated_state",||m.probabilities_state(&QuantumState{dim:1,amplitudes:vec![C64::new(a,0.0)],label:String::new()}));}
 let two=measurement::Measurement::computational_basis(2);let rho=CMatrix::from_diagonal(&nalgebra::DVector::from_vec(vec![C64::new(1e-320,0.0),C64::new(1.0,0.0)]));
 report("positive_tiny_outcome_update",||measurement_update::MeasurementUpdate::update_density(&two,&rho,0).map(|r|r.iter().all(|x|x.re.is_finite()&&x.im.is_finite())));
 let k=kraus_operators::KrausOperators::try_from_cmatrices(1,vec![CMatrix::from_element(1,1,C64::new(1.0,0.0)),CMatrix::from_element(1,1,C64::new(1e-200,0.0))],"").unwrap();
 println!("rounded_zero_residual_is_trace_preserving={}",k.is_trace_preserving(0.0));assert!(k.is_trace_preserving(0.0));
 let tiny=Rational::from_float(1e-200).unwrap();let mat=|q|linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(1,1,vec![G::from_rational(q)]).unwrap();
 report("same_binary_float_coefficients_exact_TP_control",||exact_channel::ExactKrausChannel::try_new(1,1,vec![mat(Rational::from_integer(1.into())),mat(tiny)],""));
 let bad=quantum_channel::QuantumChannel{dim:1,source:quantum_channel::StateSpace::new(2),target:quantum_channel::StateSpace::new(1),kraus:kraus_operators::KrausOperators::identity(1,"").unwrap(),label:String::new()};
 report("stinespring_mismatched_source",||stinespring_dilation::StinespringDilation::from_quantum_channel(&bad,1e-6));
}
