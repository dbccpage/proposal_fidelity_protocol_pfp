pub mod epics {
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/grammar.rs"] pub mod grammar;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/manifold.rs"] pub mod manifold;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/debate.rs"] pub mod debate;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/retraction.rs"] pub mod retraction;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/guard.rs"] pub mod guard;
}

fn main(){
 use epics::*;use num_rational::Ratio;
 let mut acc=manifold::ConstraintPressureAccumulator::new(&[Ratio::new(1,1)]).unwrap();
 assert_eq!(acc.step(&[u64::MAX]),Ratio::new(-1,1));
 println!("nonnegative_count_decreases_pressure_to_minus_one=true");
 let index=grammar::TokenTrieIndex::build(&[vec![0,1]],2).unwrap();
 let score=grammar::ExpectedFutureGrammaticality::score(&index,&[],&[(0,Ratio::new(1,1)),(0,Ratio::new(1,1))]).unwrap();
 assert_eq!(score.score_value(),Ratio::new(2,1));
 let receipt=grammar::TokenFrontierReceiptV1::build(&index,&[1],&score);
 assert_eq!(receipt.support_width,0);assert_eq!(receipt.efg_numerator,2);
 println!("duplicate_probabilities_sum_to_two_and_rebind_to_dead_prefix=true");
 let mut dag=debate::PrecommitmentDAG::new(8).unwrap();
 for node in 0..8 {
  dag.assert_lemma("left",debate::Claim::grounded(node,debate::KernelPrimitive::Carrier,true,"p")).unwrap();
  dag.assert_lemma("right",debate::Claim::grounded(node,debate::KernelPrimitive::Carrier,![1,6,7].contains(&node),"p")).unwrap();
 }
 let receipt=debate::run_debate(&dag,"left","right",&debate::KernelReplayWitness::new(|_,_|true)).unwrap();
 assert_eq!(receipt.locus,6);
 println!("first_divergence_one_but_engine_and_witness_certify_six=true");
 let triad=retraction::DescentTriad::new(0,0,0);
 let mut receipt=retraction::RetractionEngine.run(triad,&[],0).unwrap();
 receipt.authority_effect="invented".into();receipt.admitted=99;receipt.acts.clear();
 assert_eq!(retraction::RetractionEngine.replay(triad,&[],0,&receipt),retraction::ReplayOutcome::Reproduced);
 println!("tampered_authority_count_and_acts_replay=true");
 let exact=guard::LearnedGuard{forbidden:guard::CandidateFingerprint{token_stream:"x".into(),cochain_projection:vec![false]},refusal_code:"r".into(),source_turns:vec![0],scope:guard::GuardScope::Exact};
 let mut generalized=exact.clone();generalized.scope=guard::GuardScope::Generalized{reviewer:"".into(),rationale:"".into()};
 let a:guard::GuardMask=serde_json::from_value(serde_json::json!({"guards":[exact]})).unwrap();
 let b:guard::GuardMask=serde_json::from_value(serde_json::json!({"guards":[generalized]})).unwrap();
 let candidate=retraction::CandidateTurn{token_stream:"x".into(),cochain_projection:vec![true],triad};
 assert!(a.pruning_guard(&candidate).is_none());assert!(b.pruning_guard(&candidate).is_some());assert_eq!(a.digest(),b.digest());
 println!("unreviewed_generalized_guard_changes_pruning_under_same_mask_digest=true");
 let a=guard::CandidateFingerprint{token_stream:"a".into(),cochain_projection:vec![false]};
 let b=guard::CandidateFingerprint{token_stream:"a\0".into(),cochain_projection:vec![]};
 assert_ne!(a,b);assert_eq!(a.digest(),b.digest());
 println!("guard_fingerprint_encoding_alias=true");
}
