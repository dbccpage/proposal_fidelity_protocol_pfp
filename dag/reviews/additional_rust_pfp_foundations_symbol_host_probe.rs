#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp_runtime/src/symbol_game_host.rs"] mod owner;

use owner::*;use num_rational::BigRational;use num_bigint::BigInt;
fn q(n:i64)->BigRational{BigRational::from_integer(BigInt::from(n))}
fn main(){
 let mut p=SymbolGameProblem::new("synthetic".into(),vec!["a".into(),"b".into()],vec![ProblemEdge{u:"a".into(),v:"b".into(),weight:q(1)}],vec![q(1)]).unwrap();
 p.edges[0].weight=q(-1);p.digest=p.compute_digest();let host=SymbolGameHost::try_new(p).unwrap();assert_eq!(host.section_defect(),q(-1));println!("self_consistent_negative_weight_problem_admitted_with_negative_defect=true");
 let p=SymbolGameProblem::new("synthetic".into(),vec!["a".into(),"b".into()],vec![ProblemEdge{u:"a".into(),v:"b".into(),weight:q(1)}],vec![q(1)]).unwrap();let mut host=SymbolGameHost::try_new(p).unwrap();let pinned=host.problem.digest.clone();host.problem.initial_claims[0]=q(0);assert_ne!(host.problem.compute_digest(),pinned);
 let post=SymbolGameHost::calculate_state_digest(&pinned,&host.current_state_digest,1,&host.section,&q(0));let r=host.process_proposal(&UntrustedProposal{proposer_id:"synthetic".into(),problem_digest:pinned,parent_state_digest:host.current_state_digest.clone(),op:HostMoveOp::Verify,proposed_section:None,dual_witness:None,target_property:Some("ZERO_OBSTRUCTION".into()),target_event_id:None,claimed_post_state_digest:post,claimed_defect:None,rationale:"synthetic".into()});assert!(r.admitted);println!("changed_problem_claim_admitted_under_original_digest=true");
}
