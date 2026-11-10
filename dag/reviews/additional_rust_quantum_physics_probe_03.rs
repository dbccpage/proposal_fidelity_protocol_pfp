#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/hilbert_space.rs"] pub mod hilbert_space;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_hermitian.rs"] pub mod exact_hermitian;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_operator.rs"] pub mod exact_operator;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/pauli.rs"] pub mod pauli;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/quantum_state.rs"] pub mod quantum_state;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/exact_channel.rs"] pub mod exact_channel;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/density_matrix.rs"] pub mod density_matrix;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/engine_bridge.rs"] pub mod engine_bridge;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/relative_state_branching.rs"] pub mod relative_state_branching;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/branch_finegraining.rs"] pub mod branch_finegraining;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/everett.rs"] pub mod everett;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_quantum_physics/src/no_cloning.rs"] pub mod no_cloning;

// Genuine cached owner for an unused tomography dependency; no dummy implementation.
pub mod composition_tomography{pub use cached_quantum::composition_tomography::complex_hermitian_basis;}
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::{ri,rq,Rational};
fn report<T:std::fmt::Debug,F:FnOnce()->T+std::panic::UnwindSafe>(name:&str,f:F){match std::panic::catch_unwind(f){Ok(x)=>println!("{}={:?}",name,x),Err(_)=>println!("{}=PANIC",name)}}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let mut f=vec![G::from_ints(0,0);1025];f[0]=G::from_ints(1,0);
 let packet=relative_state_branching::RelativeStatePacket::with_system_family(vec![f],vec![G::from_ints(1,0)],vec![vec![G::from_ints(1,0)]]).unwrap();
 println!("relative_packet_dimension1025_admitted=true");report("relative_reduced_state_budget",||packet.reduced_state());
 let raw=Rational::new_raw(2.into(),4.into());let count=branch_finegraining::BranchCounting::new(&[raw.clone(),raw],None).unwrap();println!("unreduced_minimal_multiplicity={}",count.multiplicity);
 let minimal=branch_finegraining::BranchCounting::new(&[rq(1,2),rq(1,2)],None).unwrap();println!("canonical_minimal_multiplicity={}",minimal.multiplicity);assert_eq!(minimal.multiplicity,2.into());assert_eq!(count.multiplicity,4.into());
 let node=everett::EverettForkingNode{dimension:1,branches:vec![everett::Branch{index:0,amplitude_re:ri(1),amplitude_im:ri(0),born_weight:ri(1),count_weight:ri(0),is_active:true}]};let (dec,_,uniform)=node.measure_decoupling_theorem();println!("mutable_everett_asserted_theorem_holds={}",dec==!uniform);assert!(dec&&uniform);
 let u=quantum_state::RayVector::from_ints(&[(1,0),(0,0)]).unwrap();let v=quantum_state::RayVector::from_ints(&[(1,0),(1,0)]).unwrap();assert_eq!(no_cloning::NoCloning::exact_obstruction(&u,&v).unwrap(),rq(1,4));assert_eq!(no_cloning::NoCloning::universal_cloning_fidelity(2,1,2).unwrap(),rq(5,6));println!("exact_clone_obstruction_and_declared_fidelity_formula=PASS");
}
