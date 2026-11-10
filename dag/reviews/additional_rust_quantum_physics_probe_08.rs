#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/hermitian_spectral.rs"] pub mod hermitian_spectral;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/instruments.rs"] pub mod instruments;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/observable.rs"] pub mod observable;

pub use cached_quantum::{exact_hermitian,exact_operator,exact_channel,trace_norm_certificate,density_matrix,quantum_state,pauli};
use core_number_theory::rational::ri;
fn main(){
 use hermitian_spectral::*;
 let mut demo=HermitianMatrix::try_float64_demo(1,vec![(7.0,0.0)]).unwrap();demo.carrier=ScalarCarrier::Rational;assert!(spectral_decompose(&demo).is_err());let v=block_diagonal_eigenvalues(&demo,&BlockStructure{block_sizes:vec![1]}).unwrap();assert_eq!(v[0].re,ri(0));println!("mutated_float7_block_spectrum_returns_exact0=true");
 let mut tiny=HermitianMatrix::try_diagonal_rational(&[ri(1)],ScalarCarrier::Rational).unwrap();tiny.n=2;assert!(spectral_decompose(&tiny).is_err());let v=block_diagonal_eigenvalues(&tiny,&BlockStructure{block_sizes:vec![2]}).unwrap();assert_eq!(v.iter().map(|z|z.re.clone()).collect::<Vec<_>>(),vec![ri(1),ri(0)]);println!("mutated_dimension_block_spectrum_fabricates_zero=true");
 use instruments::*;
 let ev=SpectralEvidence{certificate_id:"unsupported assertion".into(),dim:1,eigenvalues:vec![ri(0)],hypotheses_paid:true};assert!(ev.require_paid().is_ok());let p=Povm{dim:1,effects:vec![PovmEffect{outcome_id:"only".into(),diagonal:vec![ri(4)]}],label:String::new()};let l=LudersInstrument::try_new(ev,p,"").unwrap();let o=l.apply_diagonal_state(&[ri(1)]).unwrap();assert_eq!(o.outcome_probs[0].1,ri(4));println!("legacy_Luders_accepted_single_outcome_probability=4");
 let effect=linear_algebra::exact_field::matrix::from_fn(1,1,|_,_|core_number_theory::cyclotomic::GaussianRat::from_ints(4,0)).unwrap();assert!(ExactPovm::try_new(vec![effect]).is_err());println!("full_exact_POVM_rejects_same_effect=PASS");
 let mut s=quantum_state::QuantumState::computational_basis(&cached_quantum::hilbert_space::HilbertSpace::try_new(1,"").unwrap(),0,"").unwrap();s.amplitudes[0].re=2.0;assert_eq!(observable::Observable::identity(1).unwrap().expectation_value_state(&s).unwrap(),4.0);println!("floating_identity_expectation_on_mutable_unnormalized_state=4");
 let valid=HermitianMatrix::try_diagonal_rational(&[ri(3),ri(-1)],ScalarCarrier::Rational).unwrap();assert_eq!(spectral_decompose(&valid).unwrap().distinct_eigenvalues(),vec![ri(-1),ri(3)]);println!("valid_diagonal_spectrum_control=PASS");
}
