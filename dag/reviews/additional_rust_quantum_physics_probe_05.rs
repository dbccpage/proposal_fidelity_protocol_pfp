#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/hilbert_space.rs"] pub mod hilbert_space;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_hermitian.rs"] pub mod exact_hermitian;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_operator.rs"] pub mod exact_operator;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/pauli.rs"] pub mod pauli;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_state.rs"] pub mod quantum_state;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_channel.rs"] pub mod exact_channel;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/density_matrix.rs"] pub mod density_matrix;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/engine_bridge.rs"] pub mod engine_bridge;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/kraus_operators.rs"] pub mod kraus_operators;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_channel.rs"] pub mod quantum_channel;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/completely_positive_map.rs"] pub mod completely_positive_map;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/cptp_channels_stinespring.rs"] pub mod cptp_channels_stinespring;

use linear_algebra::linear_algebra::complex_matrix::{CMatrix,C64};
use quantum_channel::{QuantumChannel,StateSpace};
use completely_positive_map::CompletelyPositiveMap;
use core_number_theory::rational::{Rational,rq};
fn candidate(k:CMatrix)->QuantumChannel{let d=k.nrows();QuantumChannel{dim:d,source:StateSpace::new(d),target:StateSpace::new(d),kraus:kraus_operators::KrausOperators::try_from_cmatrices(d,vec![k],"").unwrap(),label:String::new()}}
fn main(){
 let huge=candidate(CMatrix::from_element(1,1,C64::new(1e200,0.0)));let cp=CompletelyPositiveMap::from_quantum_channel(&huge,"").unwrap();println!("CP_from_finite_Kraus_nonfinite_Choi={}",cp.choi_matrix().iter().any(|z|!z.re.is_finite()||!z.im.is_finite()));
 let k=CMatrix::from_row_slice(2,2,&[C64::new(0.3,0.0),C64::new(0.0,0.0),C64::new(0.7,0.0),C64::new(0.0,0.0)]);let cp=CompletelyPositiveMap::from_quantum_channel(&candidate(k),"").unwrap();
 let a=Rational::from_float(cp.choi_matrix()[(0,0)].re).unwrap();let b=Rational::from_float(cp.choi_matrix()[(0,1)].re).unwrap();let c=Rational::from_float(cp.choi_matrix()[(1,1)].re).unwrap();let determinant=a*c-&b*&b;assert!(determinant<Rational::from_integer(0.into()));println!("CP_from_Kraus_exact_negative_principal_minor={}",determinant);
 println!("same_Choi_exact_admission_refuses={}",CompletelyPositiveMap::try_from_choi_matrix(2,2,cp.choi_matrix().clone(),"",1.0).is_err());
 let ch=exact_channel::ExactKrausChannel::depolarizing_qubit(rq(1,3),"").unwrap();let w=cptp_channels_stinespring::WeightedStinespring::from_channel(&ch).unwrap();assert!(w.verify().unwrap());let rho=linear_algebra::exact_field::matrix::identity(2).unwrap();assert_eq!(w.apply(&rho).unwrap(),ch.apply(&rho).unwrap());println!("weighted_Stinespring_gram_and_independent_application=PASS");
}
