#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/transport.rs"] pub mod transport;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/dda.rs"] pub mod dda;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/derivation_dag_witnesses.rs"] pub mod derivation;

fn main() {
 use pfp_runtime::f2::{F2Matrix,GaugeBoard};
 use dda::*;
 let board=GaugeBoard::new(F2Matrix::zeros(1,1),F2Matrix::from_rows(&[vec![1]]).unwrap());
 let surgery=MeronSurgery{fused:(0,0),sigma_before:vec![true],sigma_after:vec![false],positive_witness:vec![true],negative_witness:vec![true],defects_before:99,defects_after:97};
 let verdict=MeronSurgeryVerifier.verify(&board,&surgery).unwrap();
 assert_eq!(verdict,WitnessVerdict::Verified);
 assert_eq!(defects(&board,&surgery.sigma_before).unwrap().len(),1);
 assert_eq!(defects(&board,&surgery.sigma_after).unwrap().len(),0);
 let receipt=MeronSurgeryReceiptV1::build(&board,&surgery,verdict).unwrap();
 assert_eq!(receipt.defects_before,99);assert_eq!(receipt.defects_after,97);
 println!("same_index_single_defect_surgery_verified_with_fabricated_counts=true");
 use transport::*;
 let reversed:SimplicialMorphism=serde_json::from_value(serde_json::json!({"vertex_map":[1,0],"target_vertices":2})).unwrap();
 assert!(SimplicialMorphism::new(vec![1,0],2).is_err());
 assert!(TransportCertificateV1::issue(&reversed,&[0,1]).is_ok());
 println!("deserialized_orientation_reversal_receives_certificate=true");
 let malformed:SimplicialMorphism=serde_json::from_value(serde_json::json!({"vertex_map":[9],"target_vertices":1})).unwrap();
 assert!(std::panic::catch_unwind(||malformed.pushforward(&[true])).is_err());
 println!("deserialized_out_of_range_morphism_panics=true");
 let f=SimplicialMorphism::new(vec![0],3).unwrap();
 let g=SimplicialMorphism::new(vec![0,1],2).unwrap();
 assert!(f.compose(&g).is_err());
 assert!(LossLedgerV1::for_chain(&f,&g,&[0]).is_ok());
 println!("noncomposable_carriers_receive_chain_loss_ledgers=true");
 let master=derivation::build_derivation_dag_master_witness_receipt();
 assert_eq!(master.families.len(),33);assert!(master.all_passed);
 let nodes:std::collections::BTreeSet<_>=master.families.iter().flat_map(|x|x.covered_nodes.iter()).collect();
 println!("literal_fixture_master_passed=true;families={};listed_nodes={}",master.families.len(),nodes.len());
}
