#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/kochen_specker.rs"] pub mod kochen_specker;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/contextuality_obstruction.rs"] pub mod contextuality_obstruction;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/parity_context_packet.rs"] pub mod parity_context_packet;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/pauli_context_table.rs"] pub mod pauli_context_table;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/separating_predictions.rs"] pub mod separating_predictions;

pub use cached_quantum::exact_hermitian;
fn main(){
 use core_number_theory::rational::ri;use kochen_specker::RaySystem;
 let rays=vec![vec![ri(1),ri(0)],vec![ri(0),ri(1)]];assert!(RaySystem::new(rays.clone(),vec![vec![0,1]]).is_ok());
 let hook=std::panic::take_hook();std::panic::set_hook(Box::new(|_|{}));let short=std::panic::catch_unwind(||RaySystem::new(rays.clone(),vec![vec![0]])).is_err();let index=std::panic::catch_unwind(||RaySystem::new(rays,vec![vec![0,2]])).is_err();std::panic::set_hook(hook);assert!(short&&index);println!("KS_short_context_and_out_of_range_index_panics=true");
 use parity_context_packet::*;let p=ParityContextPacket::new(1,&[vec![0],vec![0]],&[1,0]).unwrap();let d1=vec![vec![1,1]];let c=ParityAdmission::ClosureFailure{defect:vec![1]};assert!(p.verify_admission(1,&d1,&c).unwrap());assert!(p.admit_with_d1(5,&d1).is_err());assert!(p.verify_admission(5,&d1,&c).unwrap());println!("closure_failure_replay_accepts_out_of_domain_bit=true");
 let table=pauli_context_table::PauliContextTable::mermin();assert!(table.observables_are_hermitian_involutions());assert_eq!(table.sign_table().unwrap(),vec![1,1,1,1,1,-1]);let p=table.packet().unwrap();let cert=p.certificate(p.targets()).unwrap();assert!(matches!(cert,ImageCertificate::Separator(_)));assert!(p.verify_certificate(p.targets(),cert).unwrap());assert!(!p.satisfiable(p.all_contexts()).unwrap());assert!(p.is_minimally_unsatisfiable().unwrap());println!("Pauli_operator_products_and_replayed_parity_obstruction=PASS");
 let x1=contextuality_obstruction::construct_cabello_scenario();let o1=contextuality_obstruction::compute_obstruction_class(&x1).unwrap();assert!(!o1.obstruction_class_is_zero);let x2=contextuality_obstruction::construct_product_scenario();let o2=contextuality_obstruction::compute_obstruction_class(&x2).unwrap();assert!(o2.obstruction_class_is_zero);assert!(contextuality_obstruction::verify_global_section(&x2,&o2.exhibited_global_section.unwrap()).0);println!("Cabello_nonzero_and_product_zero_cochain_controls=PASS");
 let s=separating_predictions::MerminPeresSquare::standard();assert!(s.verify_no_noncontextual_assignment().unwrap());println!("independent_Mermin_exhaustive_assignment_control=PASS");
}
