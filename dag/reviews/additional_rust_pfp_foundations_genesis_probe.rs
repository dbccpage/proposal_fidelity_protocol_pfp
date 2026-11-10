mod foundation { pub use pfp::foundation::PrimitiveDifference; }
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/genesis.rs"] mod genesis;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/prime.rs"] mod prime;

fn main(){
 use genesis::*;
 let selfloop=ExaminerChallenge::new(1,[(0,0)]).unwrap();
 assert!(verify_examiner(&selfloop).is_asymmetric());
 println!("self_loop_is_asymmetric=true");
 let triangle=ExaminerChallenge::new(3,[(0,1),(1,2),(2,0)]).unwrap();
 assert!(verify_examiner(&triangle).is_strict());
 println!("directed_three_cycle_is_strict=true; transitivity_is_not_checked");
 let codec=PresentationCodec::with_glyphs(0x80,0x81).unwrap();
 assert!(codec.scan(&codec.render(OpaqueDatum::new(),1)).is_err());
 println!("admitted_nonascii_codec_refuses_own_render=true");
 let regime=ObserverRegime::admit_contexts(vec![ObserverContext::new("a",1),ObserverContext::new("b",1)],evaluate_depth).unwrap();
 assert_eq!(regime.contexts().len(),2);
 println!("same_wrap_different_names_count_twice=true");
 static COUNTER:std::sync::atomic::AtomicUsize=std::sync::atomic::AtomicUsize::new(0);
 fn impure(_: &AdmittedContext)->num_rational::BigRational {
  num_rational::BigRational::from_integer(COUNTER.fetch_add(1,std::sync::atomic::Ordering::SeqCst).into())
 }
 let regime=ObserverRegime::admit_contexts(vec![ObserverContext::new("context",1)],impure).unwrap();
 assert!(!regime.equivalent(OpaqueDatum::new(),OpaqueDatum::new()).unwrap());
 println!("stateful_evaluator_breaks_reflexivity=true");
 let out=prime::prime_replay_decide(&serde_json::json!({"steps":[{"prime_step":255,"op":"CRT","executed":false,"message":"not executed"}]})).unwrap();
 assert!(out.conforms);assert_eq!(out.decision,"Terminalized");
 println!("unexecuted_compound_operation_conforms_and_terminalizes=true");
 let out=prime::prime_replay_decide(&serde_json::json!({"receipt":{"letter_tape":"CRT","terminal":"CallerChosen"}})).unwrap();
 assert!(out.conforms);assert_eq!(out.decision,"CallerChosen");
 println!("receipt_without_gamma_or_step_evidence_conforms=true");
}
