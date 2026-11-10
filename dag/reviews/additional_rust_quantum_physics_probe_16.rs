#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/derivation_dag_witnesses.rs"] pub mod derivation_dag_witnesses;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/pairing_audit.rs"] pub mod pairing_audit;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_regge_bridge.rs"] pub mod quantum_regge_bridge;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/regge_gravity_ghz_chern_finite_maps.rs"] pub mod regge_gravity_ghz_chern_finite_maps;
pub mod quantum_import_finite_maps { pub use cached_quantum::quantum_import_finite_maps::*; pub fn q(n:i64,d:i64)->Q { num_rational::Ratio::new(n,d) } pub mod page_wootters_tsirelson_wigner { #[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_import_finite_maps/page_wootters_tsirelson_wigner/cyclotomic_rings.rs"] pub mod cyclotomic_rings; }}

pub use cached_quantum::{composition_tomography,density_matrix,exact_channel,exact_hermitian,hilbert_space,kraus_operators,quantum_channel,spin_area_spectrum};
use core_number_theory::rational::{ri,rq};
fn main(){
 use regge_gravity_ghz_chern_finite_maps::*; use quantum_import_finite_maps::Qi;
 let mut ghz=build_ghz_mermin_audit().unwrap();assert!(ghz.passed());ghz.ghz=vec![Qi::zero();8];assert!(ghz.passed());println!("zero_GHZ_state_stale_audit_passes=true");
 let mut chern=build_chern_parity_audit();assert!(chern.passed());for(_,c)in &mut chern.haldane_grid{*c=Some(99);}assert!(chern.passed());println!("Chern_grid_all_99_passes=true");
 let ev=exact_eigenvalue(&vec![vec![Qi::one()]],&[Qi::one(),Qi::one()]).unwrap();assert_eq!(ev,Qi::one());println!("one_dimensional_operator_two_dimensional_eigenvector_accepted=true");
 let hook=std::panic::take_hook();std::panic::set_hook(Box::new(|_|{}));let malformed=std::panic::catch_unwind(||exact_eigenvalue(&vec![vec![Qi::one(),Qi::zero()],vec![Qi::zero(),Qi::one()]],&[Qi::one()])).is_err();std::panic::set_hook(hook);assert!(malformed);println!("short_eigenvector_panics=true");
 use quantum_regge_bridge::*;use linear_algebra::linear_algebra::complex_matrix::{CMatrix,NComplex};
 let wdw=DiscreteMiniSuperspaceWheelerDeWitt::new(1.,1.,0.,0.,1.,3).unwrap();assert_eq!(wdw.apply_hamiltonian(&[1.,1.,1.]).unwrap(),vec![1.,0.,1.]);assert_eq!(wdw.compute_residual_norm(&[1.,1.,1.]).unwrap(),0.);println!("WDW_nonzero_boundary_Hpsi=[1,0,1]; reported_residual=0");
 let basis=CMatrix::from_element(1,1,NComplex::new(2.,0.));let thermal=simplicial_dirac_thermal_cmatrix(&[0.],&basis,1.).unwrap();assert_eq!(thermal[(0,0)],NComplex::new(4.,0.));println!("unnormalized_thermal_basis_accepted_trace=4");
 let awdw=AnisotropicBianchiWheelerDeWitt::new(1.,1.,0.,[0.;3],[1.;3],[2;3]).unwrap();let mut psi=vec![0.;8];psi[0]=1.;let invalid=awdw.apply_anisotropic_decoherence(&psi,[-1.,f64::NAN,0.]).unwrap();assert_eq!(invalid,awdw.wavefunction_to_density_matrix(&psi).unwrap());println!("negative_NaN_directional_probabilities_accepted=true");
 use pairing_audit::*;use linear_algebra::backend::basic_matrix::BasicMatrix;
 for row in declared_registry().unwrap(){println!("registry {}: {:?}",row.name,audit_row(&row).unwrap());}
 assert_eq!(audit_row(&transport_gram_row().unwrap()).unwrap(),PairingTerminal::Passes);assert_eq!(audit_row(&noisy_born_row().unwrap()).unwrap(),PairingTerminal::Passes);
 let e1=vec![ri(1),ri(0)];let e2=vec![ri(0),ri(1)];let vectors=vec![e1.clone(),e2.clone()];let gram=BasicMatrix::from_row_major(2,2,vec![rq(1,2);4]).unwrap();let packet=PairingPacket::new(vectors.clone(),vectors,vec![vec![0,1]],Pairing::Bilinear(gram),vec![]).unwrap();for e in 0..2{assert_eq!(packet.value(e,&e1).unwrap(),packet.value(e,&e2).unwrap());}assert_eq!(packet.product_effect_rank().unwrap(),4);
 let table=JointTable{measurement_a:0,measurement_b:0,marginal_a:e1.clone(),marginal_b:e1,probabilities:vec![vec![rq(1,4);2];2]};let row=PairingRow{name:"degenerate_gram",origin:PairingOrigin::Imported,packet,composite:CompositeTier::Declared{joint_effect_dim:4,tables:vec![table]}};assert_eq!(audit_row(&row).unwrap(),PairingTerminal::Passes);println!("degenerate_pairing_identical_state_statistics_raw_rank4_passes=true");
 let mut empty=classical_simplex_row().unwrap();empty.composite=CompositeTier::Declared{joint_effect_dim:4,tables:vec![]};assert_eq!(audit_row(&empty).unwrap(),PairingTerminal::Passes);empty.composite=CompositeTier::Declared{joint_effect_dim:0,tables:vec![]};assert_eq!(audit_row(&empty).unwrap(),PairingTerminal::Passes);println!("empty_composite_tables_and_declared_dimension0_pass=true");
 let receipt=derivation_dag_witnesses::build_derivation_dag_master_witness_receipt();assert_eq!(receipt.families.len(),33);assert!(receipt.all_passed);let mut names=std::collections::BTreeSet::new();for family in &receipt.families{assert!(family.passed);for n in &family.covered_nodes{names.insert(n);}}println!("fixed_DAG_master_families=33; all_passed=true; distinct_labels={}",names.len());
}
