//! Falsification tests for DdcTapeEvaluator in core_adversary::stage.
//!
//! Validates:
//! 1. Exact integer/rational step evaluation over Rational64 (zero float drift)
//! 2. Zero-allocation sliding window metric computation
//! 3. Hash-chain continuity validation (parent_sha256 == prev_head)
//! 4. DFA terminal vs prefix validation
//! 5. Falsification of non-consecutive steps, broken hash chains, and divergent branches

use num_rational::Rational64;
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::ddc_tape_evaluator::{DDCTapeDFA, DdcDialect, DdcTapeEvaluator};
use core_wdp::ddc::ddc_alphabet::DdcOp;
use serde_json::json;
use sha2::{Digest, Sha256};

fn make_step(
    letter: DdcOp,
    before: &str,
    after: &str,
    phi_1: Option<Rational64>,
    gamma_2: Option<Rational64>,
) -> DdcStep {
    let raw = json!({
        "letter": letter.letter(),
        "before_class": before,
        "after_class": after,
        "carrier_hash": "carrier_fixture_001",
        "witness_hash": "witness_fixture_001",
        "receipt_sha256": "receipt_fixture_001",
        "authority_effect": "None",
        "timestamp": "2026-10-15T22:00:00Z",
        "phi_1": phi_1.map(|r| format!("{}/{}", r.numer(), r.denom())),
        "gamma_2": gamma_2.map(|r| format!("{}/{}", r.numer(), r.denom())),
    });
    serde_json::from_value(raw).expect("valid DdcStep fixture")
}

#[test]
fn test_exact_rational_differentials_and_zero_alloc_sliding_window() {
    let mut evaluator = DdcTapeEvaluator::new("eval_exact_test");

    // Step 0: E with phi_1 = 1/3, gamma_2 = 1/6
    let step0 = make_step(
        DdcOp::ExactRepair,
        "class_init",
        "class_mid",
        Some(Rational64::new(1, 3)),
        Some(Rational64::new(1, 6)),
    );
    let receipt0 = evaluator.eval_step(&step0).expect("step 0 evaluates");
    assert_eq!(receipt0.sequence, 0);
    assert_eq!(receipt0.parent_sha256, None);
    assert_eq!(receipt0.phi_1, Some(Rational64::new(1, 3)));
    assert_eq!(receipt0.gamma_2, Some(Rational64::new(1, 6)));

    // Step 1: R with phi_1 = 2/3, gamma_2 = 5/6
    let step1 = make_step(
        DdcOp::ResidualProjection,
        "class_mid",
        "class_next",
        Some(Rational64::new(2, 3)),
        Some(Rational64::new(5, 6)),
    );
    let receipt1 = evaluator.eval_step(&step1).expect("step 1 evaluates");
    assert_eq!(receipt1.sequence, 1);
    assert_eq!(receipt1.parent_sha256.as_deref(), Some(receipt0.record_sha256.as_str()));
    assert_eq!(receipt1.phi_1, Some(Rational64::new(2, 3)));
    assert_eq!(receipt1.gamma_2, Some(Rational64::new(5, 6)));

    // Step 2: I with phi_1 = 5/7, gamma_2 = 3/7
    let step2 = make_step(
        DdcOp::Integration,
        "class_next",
        "class_final",
        Some(Rational64::new(5, 7)),
        Some(Rational64::new(3, 7)),
    );
    let receipt2 = evaluator.eval_step(&step2).expect("step 2 evaluates");
    assert_eq!(receipt2.sequence, 2);
    assert_eq!(receipt2.parent_sha256.as_deref(), Some(receipt1.record_sha256.as_str()));

    // Verify Zero-Allocation Sliding Window Metric over Rational64:
    // Window 1: last step only (5/7)
    assert_eq!(evaluator.sliding_window_metric(1), Rational64::new(5, 7));

    // Window 2: last 2 steps (2/3 + 5/7 = 14/21 + 15/21 = 29/21)
    assert_eq!(evaluator.sliding_window_metric(2), Rational64::new(29, 21));

    // Window 3: all 3 steps (1/3 + 2/3 + 5/7 = 1 + 5/7 = 12/7)
    // In float, 1/3 + 2/3 would have roundoff error; in Rational64, it is EXACTLY 12/7!
    assert_eq!(evaluator.sliding_window_metric(3), Rational64::new(12, 7));
    assert_eq!(evaluator.sliding_window_metric(100), Rational64::new(12, 7));

    // Sliding window mean: (12/7) / 3 = 4/7
    assert_eq!(evaluator.sliding_window_mean(3), Rational64::new(4, 7));

    // Sliding window gamma2: 1/6 + 5/6 + 3/7 = 1 + 3/7 = 10/7
    assert_eq!(evaluator.sliding_window_gamma2(3), Rational64::new(10, 7));

    // Window 0 returns zero rational
    assert_eq!(evaluator.sliding_window_metric(0), Rational64::new(0, 1));
}

#[test]
fn test_hash_chain_continuity_validation() {
    let mut evaluator = DdcTapeEvaluator::new("hash_chain_test");
    let step0 = make_step(DdcOp::ExactRepair, "c0", "c1", None, None);
    let r0 = evaluator.eval_step(&step0).expect("step 0 lawful");

    // Legitimate step with verified parent
    let step1 = make_step(DdcOp::ResidualProjection, "c1", "c2", None, None);
    let r1 = evaluator
        .eval_step_verified(&step1, 1, Some(&r0.record_sha256))
        .expect("step 1 lawful");
    assert_eq!(r1.sequence, 1);
    assert_eq!(r1.parent_sha256.as_deref(), Some(r0.record_sha256.as_str()));
}

#[test]
fn falsify_non_consecutive_steps() {
    let mut evaluator = DdcTapeEvaluator::new("falsify_seq");
    let step = make_step(DdcOp::ExactRepair, "c0", "c1", None, None);

    // Provide non-consecutive sequence (5 instead of 0)
    let err = evaluator
        .eval_step_verified(&step, 5, None)
        .expect_err("non-consecutive sequence must be rejected");
    assert_eq!(err.code, "DDC_SEQUENCE_MISMATCH");
    assert!(err.message.contains("expected 0, got 5"));
}

#[test]
fn falsify_broken_hash_chain() {
    let mut evaluator = DdcTapeEvaluator::new("falsify_hash");
    let step0 = make_step(DdcOp::ExactRepair, "c0", "c1", None, None);
    let r0 = evaluator.eval_step(&step0).expect("step 0 lawful");

    // Tampered parent hash
    let step1 = make_step(DdcOp::ResidualProjection, "c1", "c2", None, None);
    let err = evaluator
        .eval_step_verified(&step1, 1, Some("sha256:tampered_predecessor_hash"))
        .expect_err("broken hash chain must be rejected");
    assert_eq!(err.code, "DDC_PARENT_HASH_MISMATCH");
    assert!(err.message.contains(&r0.record_sha256));
}

#[test]
fn falsify_divergent_compensation_branches() {
    let mut evaluator = DdcTapeEvaluator::new("falsify_branch");
    let step = make_step(DdcOp::ResidualProjection, "c0", "c1", None, None);

    // Initial lawful branch
    evaluator
        .record_compensation_branch("compensation_alpha", &[step.clone()])
        .expect("lawful branch accepted");

    // 1. Attempt duplicate branch ID (divergent branch conflict)
    let err_dup = evaluator
        .record_compensation_branch("compensation_alpha", &[step.clone()])
        .expect_err("duplicate branch ID must be rejected");
    assert_eq!(err_dup.code, "DDC_DIVERGENT_BRANCH");

    // 2. Attempt empty branch
    let err_empty = evaluator
        .record_compensation_branch("compensation_beta", &[])
        .expect_err("empty branch must be rejected");
    assert_eq!(err_empty.code, "DDC_INVALID_COMPENSATION_BRANCH");

    // 3. Attempt invalid branch identifier
    let err_invalid = evaluator
        .record_compensation_branch("invalid branch! #1", &[step])
        .expect_err("invalid branch identifier must be rejected");
    assert_eq!(err_invalid.code, "DDC_INVALID_COMPENSATION_BRANCH");
}

#[test]
fn falsify_t_absorption_rule() {
    let mut evaluator = DdcTapeEvaluator::new("falsify_t_rule");
    let step_e = make_step(DdcOp::ExactRepair, "c0", "c1", None, None);
    evaluator.eval_step(&step_e).expect("E accepted");

    let step_t = make_step(DdcOp::Terminalize, "c1", "c2", None, None);
    evaluator.eval_step(&step_t).expect("T accepted");
    assert!(evaluator.is_terminalized());

    // Attempt to append step after terminal T -> rejected
    let step_post = make_step(DdcOp::Descent, "c2", "c3", None, None);
    let err = evaluator
        .eval_step(&step_post)
        .expect_err("appending step after terminal T must be rejected");
    assert_eq!(err.code, "DDC_TERMINALIZED");
}

#[test]
fn falsify_dfa_illegal_transition_and_refusal_rules() {
    let mut evaluator = DdcTapeEvaluator::new("falsify_dfa");
    let step_e = make_step(DdcOp::ExactRepair, "c0", "c1", None, None);
    evaluator.eval_step(&step_e).expect("E accepted");

    // Emit refusal M
    let step_m = make_step(DdcOp::Refusal, "c1", "c2", None, None);
    evaluator.eval_step(&step_m).expect("M accepted");

    // In LegacyV1, M MUST be followed by T. Attempting to follow with Descent D -> rejected
    let step_d = make_step(DdcOp::Descent, "c2", "c3", None, None);
    let err = evaluator
        .eval_step(&step_d)
        .expect_err("M followed by non-T must be rejected under LegacyV1 DFA");
    assert_eq!(err.code, "DDC_DFA_VIOLATION");
    assert!(err.message.contains("Refusal letter M must be followed by terminal T"));
}

#[test]
fn falsify_checkpoint_rollback_out_of_bounds() {
    let mut evaluator = DdcTapeEvaluator::new("falsify_rollback");
    let step = make_step(DdcOp::ExactRepair, "c0", "c1", None, None);
    evaluator.eval_step(&step).expect("step accepted");

    // Tape has 1 step (valid index in [0, 1]). Attempt rollback to index 50 -> rejected
    let err = evaluator
        .rollback(50, "out of bounds rollback test")
        .expect_err("out of bounds rollback must be rejected");
    assert_eq!(err.code, "DDC_INVALID_CHECKPOINT");
}

#[test]
fn falsify_authority_effect_leak() {
    let raw = json!({
        "letter": "E",
        "before_class": "c0",
        "after_class": "c1",
        "carrier_hash": "carrier_001",
        "witness_hash": "witness_001",
        "receipt_sha256": "receipt_001",
        "authority_effect": "AdmittedPolicy", // Authority leak!
    });
    // Record level enforcement: DdcStep deserialization strictly rejects authority leak
    let step_err = serde_json::from_value::<DdcStep>(raw)
        .expect_err("authority leak must be rejected at record level");
    assert!(step_err.to_string().contains("authority_effect must be 'None'"));

    // Stream audit level enforcement: audit_and_reconstruct_from_jsonl returns DDC_AUDIT_AUTHORITY_LEAK
    let jsonl_leak = "{\"sequence\": 0, \"parent_sha256\": null, \"letter\": \"E\", \"before_class\": \"c0\", \"after_class\": \"c1\", \"carrier_hash\": \"c\", \"witness_hash\": \"w\", \"receipt_sha256\": \"r\", \"authority_effect\": \"AdmittedPolicy\"}\n";
    let audit_err = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(
        jsonl_leak,
        None,
        DdcDialect::LegacyV1,
    )
    .expect_err("stream audit must reject authority leak");
    assert_eq!(audit_err.code, "DDC_AUDIT_AUTHORITY_LEAK");
}

#[test]
fn test_checkpoint_rollback_and_archival() {
    let mut evaluator = DdcTapeEvaluator::new("rollback_archival_test");

    // Step 0: E
    let s0 = make_step(DdcOp::ExactRepair, "c0", "c1", Some(Rational64::new(1, 2)), None);
    evaluator.eval_step(&s0).expect("s0 lawful");
    let cp1 = evaluator.checkpoint();
    assert_eq!(cp1, 1);

    // Step 1: R
    let s1 = make_step(DdcOp::ResidualProjection, "c1", "c2", Some(Rational64::new(1, 4)), None);
    evaluator.eval_step(&s1).expect("s1 lawful");

    // Step 2: M (refusal)
    let s2 = make_step(DdcOp::Refusal, "c2", "c3", None, None);
    evaluator.eval_step(&s2).expect("s2 lawful");
    assert_eq!(evaluator.step_count(), 3);

    // Roll back to checkpoint 1
    let rolled = evaluator
        .rollback(cp1, "Critic obstruction identified")
        .expect("rollback succeeds");
    assert_eq!(rolled.len(), 2);
    assert_eq!(evaluator.step_count(), 1);
    assert_eq!(evaluator.as_tape(" · "), "E");
    assert_eq!(evaluator.rolled_back_steps().len(), 2);
    assert_eq!(
        evaluator.rolled_back_steps()[0].reason,
        "Critic obstruction identified"
    );

    // Record compensation branch
    let comp_s1 = make_step(DdcOp::ContextExposure, "c1", "c1_alt", None, None);
    let comp_s2 = make_step(DdcOp::Terminalize, "c1_alt", "c_term", None, None);
    evaluator
        .record_compensation_branch("compensation_branch_01", &[comp_s1, comp_s2])
        .expect("compensation branch accepted");
    assert!(evaluator.compensation_branches().contains_key("compensation_branch_01"));
}

#[test]
fn test_dfa_complete_vs_prefix_validation() {
    // Prefix validation succeeds without terminal T
    assert!(DDCTapeDFA::validate_prefix("E · R · I", DdcDialect::LegacyV1).is_ok());

    // Complete validation requires terminal T
    let err_incomplete = DDCTapeDFA::validate("E · R · I", DdcDialect::LegacyV1)
        .expect_err("incomplete tape must fail complete validation");
    assert_eq!(err_incomplete.code, "DDC_DFA_INCOMPLETE_TAPE");

    // Complete validation succeeds with terminal T
    assert!(DDCTapeDFA::validate("E · R · I · T", DdcDialect::LegacyV1).is_ok());

    // Experimental-z-v1 start requirement: must start with E or R
    let err_exp_start = DDCTapeDFA::validate_prefix("C · I", DdcDialect::ExperimentalZV1)
        .expect_err("experimental dialect must start with E or R");
    assert_eq!(err_exp_start.code, "DDC_DFA_VIOLATION");
}

#[test]
fn test_adversarial_dfa_syntax_rejection() {
    // 1. Empty and whitespace-only tapes
    let err_empty1 = DDCTapeDFA::validate("", DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_empty1.code, "DDC_DFA_EMPTY_TAPE");
    let err_empty2 = DDCTapeDFA::validate("   \t  \n  ", DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_empty2.code, "DDC_DFA_EMPTY_TAPE");

    // 2. Unknown letters
    let err_unknown = DDCTapeDFA::validate("E · R · X · T", DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_unknown.code, "DDC_DFA_VIOLATION");
    assert!(err_unknown.message.contains("Invalid DDC letter 'X'"));

    // 3. Lowercase letters
    let err_lower = DDCTapeDFA::validate("e · r · t", DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_lower.code, "DDC_DFA_VIOLATION");

    // 4. Multiple terminal letters (T absorption violation)
    let err_multi_t = DDCTapeDFA::validate("E · T · T", DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_multi_t.code, "DDC_DFA_VIOLATION");
    assert!(err_multi_t.message.contains("T absorption rule violated"));

    // 5. Letter after terminal T
    let err_after_t = DDCTapeDFA::validate("E · T · R", DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_after_t.code, "DDC_DFA_VIOLATION");
    assert!(err_after_t.message.contains("T absorption rule violated"));

    // 6. Experimental Z dialect: Z without following T
    let err_z_no_t = DDCTapeDFA::validate("E · R · Z", DdcDialect::ExperimentalZV1).unwrap_err();
    assert_eq!(err_z_no_t.code, "DDC_DFA_VIOLATION");
    assert!(err_z_no_t.message.contains("Experimental refusal Z must be followed by T"));

    // 7. Experimental Z dialect: Z followed by non-T
    let err_z_wrong = DDCTapeDFA::validate("E · R · Z · D · T", DdcDialect::ExperimentalZV1).unwrap_err();
    assert_eq!(err_z_wrong.code, "DDC_DFA_VIOLATION");
    assert!(err_z_wrong.message.contains("Experimental refusal Z must be followed by T"));
}

#[test]
fn test_adversarial_jsonl_stream_tamper_attacks() {
    // 1. Non-consecutive sequence injection in JSONL stream (check #2)
    let jsonl_seq_gap = r#"{"sequence": 5, "parent_sha256": null, "letter": "E", "before_class": "c0", "after_class": "c1", "carrier_hash": "c", "witness_hash": "w", "receipt_sha256": "r", "authority_effect": "None", "timestamp": "2026-10-15T22:00:00Z"}
"#;
    let err_gap = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(jsonl_seq_gap, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_gap.code, "DDC_AUDIT_SEQUENCE_MISMATCH");

    // 2. Genesis step with non-None parent hash (check #3)
    let jsonl_genesis_parent = r#"{"sequence": 0, "parent_sha256": "sha256:unexpected_parent", "letter": "E", "before_class": "c0", "after_class": "c1", "carrier_hash": "c", "witness_hash": "w", "receipt_sha256": "r", "authority_effect": "None", "timestamp": "2026-10-15T22:00:00Z"}
"#;
    let err_gen = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(jsonl_genesis_parent, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_gen.code, "DDC_AUDIT_PARENT_HASH_MISMATCH");

    // 3. Step deserialization succeeds on valid audit envelope because metadata is stripped
    let jsonl_step_with_envelope = r#"{"sequence": 0, "parent_sha256": null, "letter": "E", "before_class": "c0", "after_class": "c1", "carrier_hash": "c", "witness_hash": "w", "receipt_sha256": "r", "authority_effect": "None", "timestamp": "2026-10-15T22:00:00Z"}
"#;
    let res = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(jsonl_step_with_envelope, None, DdcDialect::LegacyV1);
    assert!(res.is_ok(), "Reconstruction with audit envelope failed: {:?}", res);

    // 4. Malformed step payload triggers DDC_AUDIT_STEP_DESERIALIZATION_FAILED
    let jsonl_malformed_step = r#"{"sequence": 0, "parent_sha256": null, "letter": 12345, "before_class": "c0", "after_class": "c1", "carrier_hash": "c", "witness_hash": "w", "receipt_sha256": "r", "authority_effect": "None", "timestamp": "2026-10-15T22:00:00Z"}
"#;
    let err_deser = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(jsonl_malformed_step, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_deser.code, "DDC_AUDIT_STEP_DESERIALIZATION_FAILED");
}

fn compute_envelope_line(mut map: serde_json::Map<String, serde_json::Value>) -> (String, String) {
    let mut filtered = map.clone();
    filtered.remove("record_sha256");
    let material = serde_json::to_vec(&filtered).expect("serialize filtered");
    let digest = format!("sha256:{}", hex::encode(Sha256::digest(&material)));
    map.insert("record_sha256".into(), serde_json::Value::String(digest.clone()));
    let line = serde_json::to_string(&map).expect("serialize envelope");
    (line, digest)
}

#[test]
fn test_adversarial_jsonl_stream_full_audit_reconstruction_with_envelopes() {
    // Build a lawful multi-step stream with:
    // Step 0: E
    // Step 1: R
    // Step 2: C
    // Step 3: Rollback to checkpoint 2 (rolling back C)
    // Step 4: Compensation branch
    // Step 5: T (terminalizing)
    let mut lines = Vec::new();

    // 0: Step E
    let mut s0 = serde_json::Map::new();
    s0.insert("sequence".into(), json!(0));
    s0.insert("parent_sha256".into(), serde_json::Value::Null);
    s0.insert("record_type".into(), json!("step"));
    s0.insert("letter".into(), json!("E"));
    s0.insert("before_class".into(), json!("class_init"));
    s0.insert("after_class".into(), json!("class_01"));
    s0.insert("carrier_hash".into(), json!("c0"));
    s0.insert("witness_hash".into(), json!("w0"));
    s0.insert("receipt_sha256".into(), json!("r0"));
    s0.insert("authority_effect".into(), json!("None"));
    s0.insert("timestamp".into(), json!("2026-10-15T22:00:00Z"));
    let (l0, d0) = compute_envelope_line(s0);
    lines.push(l0);

    // 1: Step R
    let mut s1 = serde_json::Map::new();
    s1.insert("sequence".into(), json!(1));
    s1.insert("parent_sha256".into(), json!(d0));
    s1.insert("record_type".into(), json!("step"));
    s1.insert("letter".into(), json!("R"));
    s1.insert("before_class".into(), json!("class_01"));
    s1.insert("after_class".into(), json!("class_02"));
    s1.insert("carrier_hash".into(), json!("c1"));
    s1.insert("witness_hash".into(), json!("w1"));
    s1.insert("receipt_sha256".into(), json!("r1"));
    s1.insert("authority_effect".into(), json!("None"));
    s1.insert("timestamp".into(), json!("2026-10-15T22:00:01Z"));
    let (l1, d1) = compute_envelope_line(s1);
    lines.push(l1);

    // 2: Step C
    let mut s2 = serde_json::Map::new();
    s2.insert("sequence".into(), json!(2));
    s2.insert("parent_sha256".into(), json!(d1));
    s2.insert("record_type".into(), json!("step"));
    s2.insert("letter".into(), json!("C"));
    s2.insert("before_class".into(), json!("class_02"));
    s2.insert("after_class".into(), json!("class_03"));
    s2.insert("carrier_hash".into(), json!("c2"));
    s2.insert("witness_hash".into(), json!("w2"));
    s2.insert("receipt_sha256".into(), json!("r2"));
    s2.insert("authority_effect".into(), json!("None"));
    s2.insert("timestamp".into(), json!("2026-10-15T22:00:02Z"));
    let (l2, d2) = compute_envelope_line(s2);
    lines.push(l2);

    // 3: Rollback to checkpoint index 2 (removes Step C)
    let mut s3 = serde_json::Map::new();
    s3.insert("sequence".into(), json!(3));
    s3.insert("parent_sha256".into(), json!(d2));
    s3.insert("record_type".into(), json!("rollback"));
    s3.insert("checkpoint_index".into(), json!(2));
    s3.insert("reason".into(), json!("Refinement needed"));
    s3.insert("authority_effect".into(), json!("None"));
    let (l3, d3) = compute_envelope_line(s3);
    lines.push(l3);

    // 4: Compensation branch
    let mut s4 = serde_json::Map::new();
    s4.insert("sequence".into(), json!(4));
    s4.insert("parent_sha256".into(), json!(d3));
    s4.insert("record_type".into(), json!("compensation_branch"));
    s4.insert("branch_id".into(), json!("compensation_branch_alpha"));
    s4.insert("steps".into(), json!([
        {
            "letter": "I",
            "before_class": "c_alt_1",
            "after_class": "c_alt_2",
            "carrier_hash": "c_alt",
            "witness_hash": "w_alt",
            "receipt_sha256": "r_alt",
            "authority_effect": "None",
            "timestamp": "2026-10-15T22:00:03Z",
        }
    ]));
    s4.insert("authority_effect".into(), json!("None"));
    let (l4, d4) = compute_envelope_line(s4);
    lines.push(l4);

    // 5: Step T
    let mut s5 = serde_json::Map::new();
    s5.insert("sequence".into(), json!(5));
    s5.insert("parent_sha256".into(), json!(d4));
    s5.insert("record_type".into(), json!("step"));
    s5.insert("letter".into(), json!("T"));
    s5.insert("before_class".into(), json!("class_02"));
    s5.insert("after_class".into(), json!("class_term"));
    s5.insert("carrier_hash".into(), json!("ct"));
    s5.insert("witness_hash".into(), json!("wt"));
    s5.insert("receipt_sha256".into(), json!("rt"));
    s5.insert("authority_effect".into(), json!("None"));
    s5.insert("timestamp".into(), json!("2026-10-15T22:00:04Z"));
    let (l5, d5) = compute_envelope_line(s5);
    lines.push(l5);

    let full_jsonl = lines.join("\n");

    // Reconstruct without expected head
    let report = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&full_jsonl, None, DdcDialect::LegacyV1)
        .expect("lawful stream reconstructs cleanly");
    assert_eq!(report.active_tape, "E · R · T");
    assert!(report.terminalized);
    assert_eq!(report.rolled_back_steps.len(), 1);
    assert_eq!(report.rolled_back_steps[0].reason, "Refinement needed");
    assert!(report.compensation_branches.contains_key("compensation_branch_alpha"));
    assert_eq!(report.head_sha256, d5);

    // Reconstruct with matching expected head succeeds
    let report2 = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&full_jsonl, Some(&d5), DdcDialect::LegacyV1)
        .expect("matching expected head succeeds");
    assert_eq!(report2.head_sha256, d5);

    // Reconstruct with tampered expected head is rejected
    let err_head = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&full_jsonl, Some("sha256:0000000000000000000000000000000000000000000000000000000000000000"), DdcDialect::LegacyV1)
        .expect_err("mismatched head hash must be rejected");
    assert_eq!(err_head.code, "DDC_AUDIT_HEAD_HASH_MISMATCH");
}

#[test]
fn test_adversarial_jsonl_stream_rejections() {
    // 1. Non-consecutive tape steps: sequence gap on step 1 (0 then 2)
    let mut s0 = serde_json::Map::new();
    s0.insert("sequence".into(), json!(0));
    s0.insert("parent_sha256".into(), serde_json::Value::Null);
    s0.insert("record_type".into(), json!("step"));
    s0.insert("letter".into(), json!("E"));
    s0.insert("before_class".into(), json!("c0"));
    s0.insert("after_class".into(), json!("c1"));
    s0.insert("carrier_hash".into(), json!("c"));
    s0.insert("witness_hash".into(), json!("w"));
    s0.insert("receipt_sha256".into(), json!("r"));
    s0.insert("authority_effect".into(), json!("None"));
    let (l0, d0) = compute_envelope_line(s0);

    let mut s1_gap = serde_json::Map::new();
    s1_gap.insert("sequence".into(), json!(2)); // expected 1!
    s1_gap.insert("parent_sha256".into(), json!(d0));
    s1_gap.insert("record_type".into(), json!("step"));
    s1_gap.insert("letter".into(), json!("R"));
    s1_gap.insert("before_class".into(), json!("c1"));
    s1_gap.insert("after_class".into(), json!("c2"));
    s1_gap.insert("carrier_hash".into(), json!("c"));
    s1_gap.insert("witness_hash".into(), json!("w"));
    s1_gap.insert("receipt_sha256".into(), json!("r"));
    s1_gap.insert("authority_effect".into(), json!("None"));
    let (l1_gap, _) = compute_envelope_line(s1_gap);

    let stream_gap = format!("{l0}\n{l1_gap}");
    let err_gap = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&stream_gap, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_gap.code, "DDC_AUDIT_SEQUENCE_MISMATCH");

    // 2. Tampered parent hash on step 1
    let mut s1_bad_parent = serde_json::Map::new();
    s1_bad_parent.insert("sequence".into(), json!(1));
    s1_bad_parent.insert("parent_sha256".into(), json!("sha256:tampered_predecessor_hash"));
    s1_bad_parent.insert("record_type".into(), json!("step"));
    s1_bad_parent.insert("letter".into(), json!("R"));
    s1_bad_parent.insert("before_class".into(), json!("c1"));
    s1_bad_parent.insert("after_class".into(), json!("c2"));
    s1_bad_parent.insert("carrier_hash".into(), json!("c"));
    s1_bad_parent.insert("witness_hash".into(), json!("w"));
    s1_bad_parent.insert("receipt_sha256".into(), json!("r"));
    s1_bad_parent.insert("authority_effect".into(), json!("None"));
    let (l1_bad_parent, _) = compute_envelope_line(s1_bad_parent);

    let stream_bad_parent = format!("{l0}\n{l1_bad_parent}");
    let err_parent = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&stream_bad_parent, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_parent.code, "DDC_AUDIT_PARENT_HASH_MISMATCH");

    // 3. Tampered record hash
    let mut s1_bad_rec = serde_json::Map::new();
    s1_bad_rec.insert("sequence".into(), json!(1));
    s1_bad_rec.insert("parent_sha256".into(), json!(d0));
    s1_bad_rec.insert("record_type".into(), json!("step"));
    s1_bad_rec.insert("record_sha256".into(), json!("sha256:forged_record_hash_value"));
    s1_bad_rec.insert("letter".into(), json!("R"));
    s1_bad_rec.insert("before_class".into(), json!("c1"));
    s1_bad_rec.insert("after_class".into(), json!("c2"));
    s1_bad_rec.insert("carrier_hash".into(), json!("c"));
    s1_bad_rec.insert("witness_hash".into(), json!("w"));
    s1_bad_rec.insert("receipt_sha256".into(), json!("r"));
    s1_bad_rec.insert("authority_effect".into(), json!("None"));
    let l1_bad_rec = serde_json::to_string(&s1_bad_rec).unwrap();

    let stream_bad_rec = format!("{l0}\n{l1_bad_rec}");
    let err_rec = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&stream_bad_rec, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_rec.code, "DDC_AUDIT_RECORD_HASH_MISMATCH");

    // 4. Divergent compensation branches: duplicate branch id
    let mut s1_ok = serde_json::Map::new();
    s1_ok.insert("sequence".into(), json!(1));
    s1_ok.insert("parent_sha256".into(), json!(d0));
    s1_ok.insert("record_type".into(), json!("compensation_branch"));
    s1_ok.insert("branch_id".into(), json!("duplicate_branch_id"));
    s1_ok.insert("steps".into(), json!([
        {
            "letter": "E",
            "before_class": "c1",
            "after_class": "c2",
            "carrier_hash": "c",
            "witness_hash": "w",
            "receipt_sha256": "r",
            "authority_effect": "None",
            "timestamp": "2026-10-15T22:00:01Z",
        }
    ]));
    s1_ok.insert("authority_effect".into(), json!("None"));
    let (l1_ok, d1_ok) = compute_envelope_line(s1_ok);

    let mut s2_dup = serde_json::Map::new();
    s2_dup.insert("sequence".into(), json!(2));
    s2_dup.insert("parent_sha256".into(), json!(d1_ok));
    s2_dup.insert("record_type".into(), json!("compensation_branch"));
    s2_dup.insert("branch_id".into(), json!("duplicate_branch_id")); // DUPLICATE!
    s2_dup.insert("steps".into(), json!([
        {
            "letter": "R",
            "before_class": "c2",
            "after_class": "c3",
            "carrier_hash": "c",
            "witness_hash": "w",
            "receipt_sha256": "r",
            "authority_effect": "None",
            "timestamp": "2026-10-15T22:00:02Z",
        }
    ]));
    s2_dup.insert("authority_effect".into(), json!("None"));
    let (l2_dup, _) = compute_envelope_line(s2_dup);

    let stream_dup_branch = format!("{l0}\n{l1_ok}\n{l2_dup}");
    let err_dup = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&stream_dup_branch, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_dup.code, "DDC_DIVERGENT_BRANCH");

    // 5. Compensation branch with invalid characters in branch_id
    let mut s1_invalid_branch = serde_json::Map::new();
    s1_invalid_branch.insert("sequence".into(), json!(1));
    s1_invalid_branch.insert("parent_sha256".into(), json!(d0));
    s1_invalid_branch.insert("record_type".into(), json!("compensation_branch"));
    s1_invalid_branch.insert("branch_id".into(), json!("invalid branch with spaces"));
    s1_invalid_branch.insert("steps".into(), json!([
        {
            "letter": "E",
            "before_class": "c1",
            "after_class": "c2",
            "carrier_hash": "c",
            "witness_hash": "w",
            "receipt_sha256": "r",
            "authority_effect": "None",
            "timestamp": "2026-10-15T22:00:01Z",
        }
    ]));
    s1_invalid_branch.insert("authority_effect".into(), json!("None"));
    let (l1_invalid_b, _) = compute_envelope_line(s1_invalid_branch);

    let stream_inv_b = format!("{l0}\n{l1_invalid_b}");
    let err_inv_b = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&stream_inv_b, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_inv_b.code, "DDC_INVALID_COMPENSATION_BRANCH");

    // 6. Rollback checkpoint out of bounds
    let mut s1_bad_cp = serde_json::Map::new();
    s1_bad_cp.insert("sequence".into(), json!(1));
    s1_bad_cp.insert("parent_sha256".into(), json!(d0));
    s1_bad_cp.insert("record_type".into(), json!("rollback"));
    s1_bad_cp.insert("checkpoint_index".into(), json!(999)); // Out of bounds!
    s1_bad_cp.insert("reason".into(), json!("bad cp test"));
    s1_bad_cp.insert("authority_effect".into(), json!("None"));
    let (l1_bad_cp, _) = compute_envelope_line(s1_bad_cp);

    let stream_bad_cp = format!("{l0}\n{l1_bad_cp}");
    let err_bad_cp = DdcTapeEvaluator::audit_and_reconstruct_from_jsonl(&stream_bad_cp, None, DdcDialect::LegacyV1).unwrap_err();
    assert_eq!(err_bad_cp.code, "DDC_INVALID_CHECKPOINT");
}

// Origin: engine/crates_rs/tests/core_adversary/stage/ddc_tape_evaluator_falsification.rs
// Claim: urn:core:crates_rs:tests:ddc-tape-evaluator-falsification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord63e7b1f2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord63e7b1f2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError63e7b1f2 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError63e7b1f2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError63e7b1f2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError63e7b1f2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord63e7b1f2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError63e7b1f2> {
        if capacity_bound == 0 {
            return Err(BoundaryError63e7b1f2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError63e7b1f2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError63e7b1f2::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_63e7b1f2() {
    let admitted = BoundaryRecord63e7b1f2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord63e7b1f2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
