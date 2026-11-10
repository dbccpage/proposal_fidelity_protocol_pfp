#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/phi1.rs"] pub mod phi1;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/binary_degree.rs"] pub mod binary_degree;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/trace_diagnostics.rs"] pub mod trace_diagnostics;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_certifiers/src/mathematical_claim.rs"] pub mod mathematical_claim;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_certifiers/src/meron_certificate.rs"] pub mod meron_certificate;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_certifiers/src/meron_hamiltonian_bridge.rs"] pub mod meron_hamiltonian_bridge;

pub use phi1::Phi1Functional;
use meron_certificate::*;
use meron_hamiltonian_bridge::*;
fn main(){
 let args:Vec<String>=std::env::args().collect();
 let comment=std::path::Path::new(&args[1]);
 assert!(mathematical_claim::mechanized_locus_refusal(comment.parent().unwrap(),"MECHANIZED",Some(comment.file_name().unwrap().to_str().unwrap())).is_none());
 println!("comment_only_lean_file_passes_locus_check=true");
 assert_eq!(trace_diagnostics::phi_struct("a a","a"),0.0);
 assert_eq!(trace_diagnostics::phi_struct("a","a a"),0.5);
 assert_eq!(trace_diagnostics::phi_entropy("x","x"),0.0);
 assert_eq!(trace_diagnostics::trace_structure(&[0.0,0.0,1.0],0.0).jump_position,0.5);
 assert!(trace_diagnostics::normalized_shift_pairing_coherence(&[0.0],0.0).unwrap().is_nan());
 println!("structural_overlap_asymmetric=true;constant_entropy_zero=true;final_jump_position_half=true;zero_normalized_pairing_nan=true");
 let cert=MeronCertificate{system:MeronSystem{name:"public overflow control".into(),num_sites:1,num_configurations:2,zero_meron_sector:vec![0,1],multi_meron_sector:vec![]},configurations:(0..2).map(|id|MeronConfig{id,state:vec![id],amplitude_num:i64::MAX,amplitude_den:1,sign:1,meron_count:0}).collect(),involution:vec![],non_meron_moves:Some(vec![])};
 let overflow=std::panic::catch_unwind(||verify_meron_certificate(&cert));
 println!("meron_sum_overflow_panics={};meron_sum_overflow_returns_ok={}",overflow.is_err(),matches!(overflow,Ok(Ok(()))));
 assert!(is_supported_meron_contract_id("math:meron_sign_problem_toy_exact_cancellation_UNRELATED:v0.2.1"));
 println!("meron_contract_prefix_lookalike_accepted=true");
 let large=std::panic::catch_unwind(||LoopDescriptor{temporal_winding:u32::MAX,bond_count:0}.sign_factor());
 println!("loop_sign_u32_overflow_panics={}",large.is_err());
 let row=|source,target,from,to|LckGlobalSiteTransportRow{source,target,operator:LocalOperatorKind::TemporalPropagation,temporal_wrap:source==1,left_site:0,right_site:1,hu_site:None,source_up_occupancy:vec![0,0,from],target_up_occupancy:vec![0,0,to],source_down_occupancy:vec![0,0,0],target_down_occupancy:vec![0,0,0]};
 let packet=LckGlobalSiteTransportPacket{family_id:LCK_HAMILTONIAN_FAMILY_ID.into(),bipartite_lattice:true,site_count:3,vertex_count:2,rows:vec![row(0,1,0,1),row(1,0,1,0)]};
 let result=packet.verify().unwrap();assert!(result.global_transport_continuity_verified);assert!(result.symbolic_auto_sign_summary.operator_summary.graph_auto_sign_summary.sign_summary.extraction_summary.licenses_independent_loop_theorem);
 println!("temporal_propagation_changes_remote_occupation_but_global_verifier_accepts=true");
 // 2^63 i64 entries exceed Vec's isize capacity and fail before allocation.
 let huge=OperatorToSuccessorGraphWithAutoSignsPacket{family_id:LCK_HAMILTONIAN_FAMILY_ID.into(),bipartite_lattice:true,vertex_count:63,matrix_elements:(0..63).map(|i|LocalHamiltonianMatrixElement{source:i,target:i,operator:LocalOperatorKind::TemporalPropagation,temporal_wrap:true,abs_matrix_element:1}).collect()};
 assert!(std::panic::catch_unwind(||huge.verify()).is_err());
 println!("sixty_three_small_rows_trigger_preallocation_capacity_panic=true");
}
