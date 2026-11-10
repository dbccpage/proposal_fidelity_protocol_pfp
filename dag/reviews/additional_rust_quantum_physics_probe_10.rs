#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/stabilizer_code_distance.rs"] pub mod stabilizer_code_distance;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/grover.rs"] pub mod grover;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/feynman_diagram.rs"] pub mod feynman_diagram;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/graded_path_sum.rs"] pub mod graded_path_sum;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/s_matrix.rs"] pub mod s_matrix;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/scattering_amplitude.rs"] pub mod scattering_amplitude;

pub use cached_quantum::pauli;
fn main(){
 use stabilizer_code_distance::*;
 let c=StabilizerCode::try_new_with_length(2,vec![]).unwrap();assert_eq!(c.k(),2);assert_eq!(c.distance().unwrap().distance(),1);
 let pairs=c.logical_pairs();println!("empty_generator_two_qubit_logical_pairs={:?}",pairs);assert!(pairs.as_ref().map(|p|p.len()!=2).unwrap_or(true));
 let enums=c.weight_enumerators(32);println!("empty_generator_two_qubit_weight_enumerators={:?}",enums);if let Ok((a,b))=enums{assert_ne!(b,c.macwilliams_normalizer(&a).unwrap());}
 let identity=StabilizerCode::try_new(vec![vec![pauli::Pauli::I;2]]).unwrap();assert_eq!(identity.logical_pairs().unwrap().len(),2);let(a,b)=identity.weight_enumerators(32).unwrap();assert_eq!(b,identity.macwilliams_normalizer(&a).unwrap());println!("explicit_identity_generator_control=PASS");
 let words=["XX","YY","ZZ"].map(|w|pauli::PauliString::parse(w).unwrap());assert!(SignedStabilizerState::new(words.to_vec()).is_err());let bell=SignedStabilizerState::new(vec![words[0].clone(),words[2].clone()]).unwrap();assert_eq!(bell.entropy(&[0]).unwrap(),1);println!("signed_stabilizer_phase_and_Bell_entropy_control=PASS");
 use std::collections::BTreeSet;use core_number_theory::rational::{ri,rq,Rational};
 let g=grover::GroverInstance::new(8,BTreeSet::from([1,5])).unwrap();for k in 0..=4{let a=g.amplitudes(k).unwrap();let direct: Rational=g.marked().iter().map(|&i|&a[i]*&a[i]/ri(8)).sum();assert_eq!(g.success_probability(k).unwrap(),direct);}println!("Grover_direct_amplitudes_vs_Chebyshev=PASS");
 let d=feynman_diagram::phi4_vacuum_diagrams(2,20000).unwrap();assert_eq!(d.iter().map(|d|d.symmetry_factor(8).unwrap()).sum::<Rational>(),rq(35,384));println!("Wick_graph_sum_control=PASS");
 use graded_path_sum::{TransportGraph,NonNegative,TimeSlicedTransport};let graph=TransportGraph::new(1,vec![(0,0,NonNegative::new(rq(1,2)).unwrap())]).unwrap();let green=graph.closure().unwrap();assert_eq!(green.kernel.get(0,0).unwrap(),ri(2));assert_eq!(green.contraction_bound,rq(1,2));assert!(graph.all_histories(0,0).is_err());let t=TimeSlicedTransport::new(vec![1,2,1],vec![vec![vec![ri(2)],vec![ri(3)]],vec![vec![ri(5),ri(7)]]]).unwrap();assert_eq!(t.path_sum(0,0).unwrap(),ri(31));assert_eq!(t.sliced_composition(0,0,1).unwrap(),ri(31));println!("Green_closure_cycle_vs_finite_history_and_slice_control=PASS");
 use core_number_theory::cyclotomic::GaussianRat as G;use linear_algebra::exact_field::matrix as m;
 let v=m::from_rows(vec![vec![G::zero(),G::from_rational(rq(1,2))],vec![G::from_rational(rq(1,2)),G::zero()]]).unwrap();let s=s_matrix::SMatrix::from_k(&v).unwrap();let a=scattering_amplitude::ScatteringAmplitude::from_s(s);assert_eq!(a.probability(0,1).unwrap(),rq(16,25));assert!(m::is_zero_matrix(&a.optical_theorem_defect().unwrap()));let p=scattering_amplitude::ScatteringProblem::new(vec![ri(1),ri(2)],v).unwrap();let z=G::from_ints(4,0);assert!(m::is_zero_matrix(&p.resolvent_identity_defect(&z).unwrap()));for k in[0,1,4]{assert_eq!(m::sub(&p.t_matrix(&z).unwrap(),&p.born_series(&z,k).unwrap()).unwrap(),p.born_remainder(&z,k).unwrap());}println!("finite_scattering_optical_and_resolvent_remainder_controls=PASS");
}
