#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/challenge.rs"] mod challenge;

fn main() {
    use challenge::*;
    let commitment = JudgeCommitmentV1::new("synthetic", b"fixed manifest", "a", "bc");
    let freeze = FreezeRecordV1::new("synthetic", b"fixed deliverable", commitment.commitment_hash());
    let mut judge = JudgePacketV1 {
        challenge_id: "synthetic".into(), commitment_hash: "unrelated".into(),
        committed_at_utc: "after freeze".into(), operator: "changed".into(), version: "changed".into(),
        hidden_cases: vec![serde_json::json!({"input":7,"expected":11})],
        checker_a_id: "unbound-a".into(), checker_b_id: "unbound-b".into(), authority_effect:"anything".into()
    };
    assert!(verify_challenge_commit_reveal_prerequisites(&judge, &commitment, &freeze, b"fixed deliverable").is_ok());
    judge.hidden_cases[0]["expected"] = serde_json::json!(99);
    assert!(verify_challenge_commit_reveal_prerequisites(&judge, &commitment, &freeze, b"fixed deliverable").is_ok());
    println!("changed_judge_content_wrong_commitment_and_reversed_time_pass_prerequisites=true");
    let checker = ExactMatchChecker::new("same", "expected");
    let case = &judge.hidden_cases[0];
    assert_eq!(evaluate_dual_checkers(&checker, &checker, case, case), DisjointOutcome::Correct);
    println!("echo_of_complete_case_passes_same_checker_twice=true");
    let mut alias = commitment.clone(); alias.operator="ab".into(); alias.version="c".into();
    assert_ne!(alias, commitment); assert_eq!(alias.commitment_hash(), commitment.commitment_hash());
    println!("unframed_operator_version_alias=true");
    struct Panics;
    impl CaseChecker for Panics {
        fn checker_id(&self)->&str { "panic" }
        fn check(&self,_:&serde_json::Value,_:&serde_json::Value)->Result<bool,String>{ panic!("synthetic checker panic") }
    }
    assert!(std::panic::catch_unwind(|| evaluate_dual_checkers(&Panics, &checker, case, case)).is_err());
    println!("checker_panic_escapes_pause_classification=true");
}
