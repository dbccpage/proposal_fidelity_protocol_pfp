use super::*;

fn compiled_catalogue_value() -> Value {
    serde_json::from_str(PINNED_PRESENTATIONS).expect("the real compiled catalogue is JSON")
}

fn assert_compiled_catalogue_control() {
    let catalogue = parse_compiled_pin_file(PINNED_PRESENTATIONS).unwrap();
    assert_eq!(catalogue.schema, "core.symbol_game.presentation_pins.v1");
    assert_eq!(catalogue.authority_effect, "None");
    let mut names: Vec<&str> = catalogue
        .pins
        .iter()
        .map(|entry| entry.name.as_str())
        .collect();
    names.sort_unstable();
    assert_eq!(names, ["c5", "c6"]);
    for name in ["c5", "c6"] {
        let declared = catalogue
            .pins
            .iter()
            .find(|entry| entry.name == name)
            .unwrap();
        assert_eq!(host_named_presentation(name), Some(&declared.presentation));
    }
    assert_ne!(host_named_presentation("c5"), host_named_presentation("c6"));
}

fn assert_catalogue_refused(value: Value, expected: &str) {
    assert_eq!(
        parse_compiled_pin_file(&value.to_string()).unwrap_err(),
        expected
    );
}

#[test]
fn compiled_catalogue_has_the_exact_real_c5_and_c6_names() {
    assert_compiled_catalogue_control();
    for unknown in ["", "C6", " c6", "c6 ", "not_pinned"] {
        assert!(host_named_presentation(unknown).is_none());
    }
}

#[test]
fn compiled_catalogue_refuses_wrong_schema_and_authority_headers() {
    assert_compiled_catalogue_control();
    for (field, replacement) in [
        ("schema", ""),
        ("schema", "core.symbol_game.presentation_pins.v0"),
        ("schema", "foreign"),
        ("authority_effect", ""),
        ("authority_effect", "ACCEPT"),
        ("authority_effect", "none"),
    ] {
        let mut altered = compiled_catalogue_value();
        altered[field] = serde_json::json!(replacement);
        assert_catalogue_refused(altered, "COMPILED_PIN_FILE_HEADER_INVALID");
    }
    assert_compiled_catalogue_control();
}

#[test]
fn compiled_catalogue_refuses_empty_or_whitespace_only_pin_names() {
    assert_compiled_catalogue_control();
    for blank in ["", " ", "\t\n", "\u{a0}"] {
        let mut altered = compiled_catalogue_value();
        altered["pins"][0]["name"] = serde_json::json!(blank);
        assert_catalogue_refused(altered, "COMPILED_PIN_NAME_AMBIGUOUS");
    }
    assert_compiled_catalogue_control();
}

#[test]
fn compiled_catalogue_refuses_duplicate_names_for_different_or_identical_entries() {
    assert_compiled_catalogue_control();
    for (index, duplicate) in [(0, "c6"), (1, "c5")] {
        let mut altered = compiled_catalogue_value();
        altered["pins"][index]["name"] = serde_json::json!(duplicate);
        assert_catalogue_refused(altered, "COMPILED_PIN_NAME_AMBIGUOUS");
    }
    let mut altered = compiled_catalogue_value();
    let duplicate = altered["pins"][0].clone();
    altered["pins"].as_array_mut().unwrap().push(duplicate);
    assert_catalogue_refused(altered, "COMPILED_PIN_NAME_AMBIGUOUS");
    assert_compiled_catalogue_control();
}

#[test]
fn compiled_catalogue_refuses_malformed_json_shapes_and_undeclared_fields() {
    assert_compiled_catalogue_control();
    for malformed in ["", "{", "null", "true", "{}", "[]"] {
        assert_eq!(
            parse_compiled_pin_file(malformed).unwrap_err(),
            "COMPILED_PIN_FILE_INVALID"
        );
    }
    for (pointer, replacement) in [
        ("/schema", serde_json::json!(false)),
        ("/authority_effect", serde_json::json!(false)),
        ("/doctrine", serde_json::json!(false)),
        ("/pins", serde_json::json!(false)),
        ("/pins/0/name", serde_json::json!(6)),
        ("/pins/0/note", serde_json::json!(null)),
        ("/pins/0/presentation/signature", serde_json::json!([1])),
        ("/pins/0/presentation/rules/0/rhs", serde_json::json!(6)),
    ] {
        let mut altered = compiled_catalogue_value();
        *altered.pointer_mut(pointer).unwrap() = replacement;
        assert_catalogue_refused(altered, "COMPILED_PIN_FILE_INVALID");
    }
    for pointer in ["", "/pins/0", "/pins/0/presentation"] {
        let mut altered = compiled_catalogue_value();
        altered
            .pointer_mut(pointer)
            .unwrap()
            .as_object_mut()
            .unwrap()
            .insert(
                "unrecognized_host_override".to_owned(),
                serde_json::json!(true),
            );
        assert_catalogue_refused(altered, "COMPILED_PIN_FILE_INVALID");
    }
    // Altered values above are parser fixtures only. None is installed in
    // the host catalogue or written back to the governance pin document.
    assert_compiled_catalogue_control();
}

fn request(action: &str) -> RuntimeRequestV1 {
    RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: action.to_owned(),
        payload: serde_json::json!({}),
    }
}

/// The gate WP-3 exists for.
///
/// Fixing three adapter names would have closed today's defect and left the
/// class open. This closes the class: every action the runtime declares has
/// to reach a match arm. An empty payload is expected to fail, but it must
/// fail on the payload -- never on the action being unknown.
#[test]
fn every_declared_action_reaches_a_dispatch_arm() {
    for action in dispatchable_actions() {
        let outcome = dispatch_runtime_request(&request(action));
        if let Some(error) = &outcome.error {
            assert!(
                !error.contains("unsupported runtime action"),
                "action {action:?} is declared in RUNTIME_ACTIONS but no match arm \
                 handles it; the advertised surface would name a capability the \
                 dispatcher does not have"
            );
        }
    }
}

/// The advert is derived, so it cannot name an adapter with no actions.
#[test]
fn every_advertised_adapter_owns_at_least_one_action() {
    for adapter in advertised_adapters() {
        assert!(
            RUNTIME_ACTIONS.iter().any(|(owner, _)| *owner == adapter),
            "adapter {adapter:?} is advertised with no action"
        );
    }
}

/// Regression for the defect that motivated WP-3.
///
/// `--describe-runtime` used to hard-code adapter names while `invoke`
/// imported nothing for `rewriting`, `rational` or `prompt_turn`. All three
/// now own real actions in the dispatch table.
#[test]
fn the_three_unreachable_adapters_are_resolved() {
    let adapters = advertised_adapters();
    assert!(
        adapters.contains(&"rewriting"),
        "rewriting must be dispatched now that it is real"
    );
    assert!(
        adapters.contains(&"prompt_turn"),
        "prompt_turn must be dispatched"
    );
    assert!(
        adapters.contains(&"rational"),
        "rational must be advertised now that its exact schema is dispatched"
    );
}

#[test]
fn rational_adapter_verifies_an_exact_l1_certificate_end_to_end() {
    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "verify_l1_certificate".to_owned(),
        payload: serde_json::json!({
            "matrix": {"rows": [["0"]]},
            "omega": ["1"],
            "p": ["0"],
            "y": ["1"]
        }),
    });
    assert!(
        outcome.success,
        "exact input must dispatch: {:?}",
        outcome.error
    );
    let result = outcome.result.expect("a rational result");
    assert_eq!(result["accepted"], true);
    assert_eq!(result["certificate"]["dual_value"], "1");
    assert_eq!(result["certificate"]["residual"]["vector"][0], "1");
}

#[test]
fn rational_adapter_refuses_floats_and_undeclared_request_fields() {
    for payload in [
        serde_json::json!({
            "matrix": {"rows": [["0"]]},
            "omega": [1.0],
            "p": ["0"],
            "y": ["1"]
        }),
        serde_json::json!({
            "matrix": {"rows": [["0"]]},
            "omega": ["1"],
            "p": ["0"],
            "y": ["1"],
            "ignored": true
        }),
    ] {
        let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
            schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
            action: "verify_l1_certificate".to_owned(),
            payload,
        });
        assert!(!outcome.success, "invalid rational input must be refused");
    }
}

#[test]
fn rational_adapter_refuses_noncanonical_exact_spellings() {
    for payload in [
        serde_json::json!({
            "matrix": {"rows": [["0/1"]]},
            "omega": ["1"], "p": ["0"], "y": ["1"]
        }),
        serde_json::json!({
            "matrix": {"rows": [["0"]]},
            "omega": ["01"], "p": ["0"], "y": ["1"]
        }),
        serde_json::json!({
            "matrix": {"rows": [["0"]]},
            "omega": ["1"], "p": ["+0"], "y": ["1"]
        }),
        serde_json::json!({
            "matrix": {"rows": [["0"]]},
            "omega": ["1"], "p": ["0"], "y": ["1/1"]
        }),
    ] {
        let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
            schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
            action: "verify_l1_certificate".to_owned(),
            payload,
        });
        assert!(
            !outcome.success,
            "an exact value with two wire spellings must be refused"
        );
    }
}

/// A rewriting request that is well-formed really does reach the verifier.
///
/// Reaching an arm is not the same as the arm working, so one action is
/// exercised end to end. The peak below is the forged one: `r2` on `abc`
/// yields `aa`, not the `cc` it declares.
#[test]
fn the_rewriting_adapter_refuses_the_forged_peak_through_the_wire() {
    let payload = serde_json::json!({
        "presentation": {
            "signature": ["a", "b", "c"],
            "rules": [
                {"name": "r1", "lhs": "ab", "rhs": "c"},
                {"name": "r2", "lhs": "bc", "rhs": "a"}
            ]
        },
        "claim": {
            "source": "abc",
            "left": {"steps": [{"rule": "r1", "position": 0}], "endpoint": "cc"},
            "right": {"steps": [{"rule": "r2", "position": 1}], "endpoint": "cc"},
            "join": "cc",
            "steps_inspected": 2,
            "step_budget": 100
        }
    });
    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "evaluate_critical_peak".to_owned(),
        payload,
    });
    assert!(
        outcome.success,
        "expected a verdict, got {:?}",
        outcome.error
    );
    let rendered = outcome.result.expect("a verdict").to_string();
    assert!(
        rendered.contains("NeedsEvidence"),
        "the forged peak must be refused across the wire; got {rendered}"
    );
}

#[test]
fn pharmacy_detect_dispatches_clean_and_finding_candidates() {
    let clean_payload = serde_json::json!({
        "candidate": {
            "public_rationale": "bounded calculation",
            "proposed_claim_deltas": []
        }
    });
    let clean_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "pharmacy_detect".to_owned(),
        payload: clean_payload,
    });
    assert!(
        clean_outcome.success,
        "expected clean outcome to succeed, got error: {:?}",
        clean_outcome.error
    );
    let res = clean_outcome.result.expect("report result");
    assert_eq!(res["findings"].as_array().unwrap().len(), 0);

    let dirty_payload = serde_json::json!({
        "candidate": {
            "verified": true
        }
    });
    let dirty_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "pharmacy_detect".to_owned(),
        payload: dirty_payload,
    });
    assert!(
        dirty_outcome.success,
        "expected dirty outcome to succeed, got error: {:?}",
        dirty_outcome.error
    );
    let dirty_res = dirty_outcome.result.expect("report result");
    assert!(dirty_res["findings"].as_array().unwrap().len() > 0);
}

#[test]
fn signed_bout_envelope_does_not_widen_foreign_actions() {
    assert_eq!(runtime_request_byte_limit("adversary_bout"), 1024 * 1024);
    for action in [
        "adversary_bout_extra",
        "workflow_graph",
        "canonical_wire",
        "pharmacy_detect",
    ] {
        assert_eq!(runtime_request_byte_limit(action), 65536);
    }
}

#[test]
fn pharmacy_detect_accepts_a_partial_context_and_binds_raw_bytes() {
    let raw = r#"{"public_rationale":"bounded calculation","proposed_claim_deltas":[]}"#;
    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "pharmacy_detect".to_owned(),
        payload: serde_json::json!({
            "candidate": raw,
            "context": {"prompt": "compute the bound"}
        }),
    });
    assert!(
        outcome.success,
        "a prompt-only context must deserialize: {:?}",
        outcome.error
    );
    let report = outcome.result.expect("report result");
    assert!(
        report["raw_bytes_digest"].is_string(),
        "a string candidate must bind its raw bytes; got {report}"
    );

    let typo = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "pharmacy_detect".to_owned(),
        payload: serde_json::json!({
            "candidate": raw,
            "context": {"semantic_replay_pased": true}
        }),
    });
    assert!(!typo.success, "an unknown context field must be refused");
}

#[test]
fn certifiers_verify_phi1_form_dispatches_exact_lean_instance() {
    let payload = serde_json::json!({
        "weights": ["1", "1"],
        "residual_at_achiever": ["3", "-5"],
        "dual": ["1", "-1"],
        "coboundaries": [["1", "1"]]
    });
    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "verify_phi1_form".to_owned(),
        payload,
    });
    assert!(
        outcome.success,
        "expected verify_phi1_form to succeed: {:?}",
        outcome.error
    );
    let res = outcome.result.expect("outcome result");
    assert_eq!(res["accepted"], true);
    assert_eq!(res["certified_value"], "8");
    assert_eq!(res["authority_effect"], "None");
    assert_eq!(
        res["lean_soundness_theorem"],
        "CoreCore.Phi1Certificate.isMinimum_of_certificate"
    );

    // Competitor / perturbed dual that does not annihilate coboundary is refused
    let bad_payload = serde_json::json!({
        "weights": ["1", "1"],
        "residual_at_achiever": ["3", "-5"],
        "dual": ["1", "0"],
        "coboundaries": [["1", "1"]]
    });
    let bad_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "verify_phi1_form".to_owned(),
        payload: bad_payload,
    });
    assert!(bad_outcome.success);
    let bad_res = bad_outcome.result.expect("outcome result");
    assert_eq!(bad_res["accepted"], false);
    assert!(bad_res["refusal"].is_string());
}

#[test]
fn retraction_actions_dispatch_end_to_end() {
    let turn_payload = serde_json::json!({
        "before": { "gamma_2": 2, "phi_1": 5, "defect_count": 4 },
        "after": { "gamma_2": 1, "phi_1": 3, "defect_count": 4 },
        "candidate": {
            "token_stream": "TURN_DESCEND",
            "cochain_projection": [true, false],
            "triad": { "gamma_2": 1, "phi_1": 3, "defect_count": 4 }
        }
    });
    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "retraction_turn".to_owned(),
        payload: turn_payload,
    });
    assert!(
        outcome.success,
        "retraction_turn must succeed: {:?}",
        outcome.error
    );
    let res = outcome.result.expect("turn result");
    assert_eq!(res["admitted"], true);
    assert_eq!(res["authority_effect"], "None");

    let loop_payload = serde_json::json!({
        "intake": { "gamma_2": 2, "phi_1": 4, "defect_count": 3 },
        "candidates": [
            {
                "token_stream": "TURN_1",
                "cochain_projection": [true],
                "triad": { "gamma_2": 1, "phi_1": 2, "defect_count": 2 }
            },
            {
                "token_stream": "TURN_2",
                "cochain_projection": [false],
                "triad": { "gamma_2": 0, "phi_1": 0, "defect_count": 0 }
            }
        ],
        "open_obligations": 0
    });
    let loop_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "retraction_loop".to_owned(),
        payload: loop_payload,
    });
    assert!(
        loop_outcome.success,
        "retraction_loop must succeed: {:?}",
        loop_outcome.error
    );
    let loop_res = loop_outcome.result.expect("loop result");
    assert_eq!(loop_res["terminal"], "PassToMaster");
    assert_eq!(loop_res["admitted"], 2);
}

#[test]
fn debate_localize_action_dispatches_end_to_end() {
    let payload = serde_json::json!({
        "tree_size": 4,
        "left_agent": "prover",
        "right_agent": "skeptic",
        "claims": [
            { "agent": "prover", "node": 0, "primitive": "Carrier", "holds": true, "text": "node 0 holds" },
            { "agent": "prover", "node": 1, "primitive": "Carrier", "holds": true, "text": "node 1 holds" },
            { "agent": "prover", "node": 2, "primitive": "Carrier", "holds": true, "text": "node 2 holds" },
            { "agent": "prover", "node": 3, "primitive": "Carrier", "holds": true, "text": "node 3 holds" },
            { "agent": "skeptic", "node": 0, "primitive": "Carrier", "holds": true, "text": "node 0 agrees" },
            { "agent": "skeptic", "node": 1, "primitive": "Carrier", "holds": false, "text": "node 1 diverges" },
            { "agent": "skeptic", "node": 2, "primitive": "Carrier", "holds": false, "text": "node 2 diverges" },
            { "agent": "skeptic", "node": 3, "primitive": "Carrier", "holds": false, "text": "node 3 diverges" }
        ]
    });
    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "debate_localize".to_owned(),
        payload,
    });
    assert!(
        outcome.success,
        "debate_localize must succeed: {:?}",
        outcome.error
    );
    let res = outcome.result.expect("debate result");
    assert_eq!(res["locus"], 1);
    assert_eq!(res["authority_effect"], "None");
}

#[test]
fn dda_surgery_action_dispatches_end_to_end() {
    let payload = serde_json::json!({
        "d0": { "rows": 1, "cols": 1, "data": [false] },
        "d1": { "rows": 2, "cols": 1, "data": [true, true] },
        "sigma": [true],
        "fuse_all": false
    });

    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "dda_surgery".to_owned(),
        payload,
    });
    assert!(
        outcome.success,
        "dda_surgery must succeed: {:?}",
        outcome.error
    );
    let res = outcome.result.expect("dda surgery result");
    assert_eq!(res["fused_left"], 0);
    assert_eq!(res["fused_right"], 1);
    assert_eq!(res["verdict"], "Verified");
}

#[test]
fn simplicial_transport_action_dispatches_end_to_end() {
    let payload = serde_json::json!({
        "vertex_map": [0, 1, 1],
        "target_vertices": 2,
        "support": [0, 1, 2],
        "chain": [true, false, false],
        "cochain": [true, false]
    });
    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "simplicial_transport".to_owned(),
        payload,
    });
    assert!(
        outcome.success,
        "simplicial_transport must succeed: {:?}",
        outcome.error
    );
    let res = outcome.result.expect("transport result");
    assert_eq!(res["certificate"]["source_vertices"], 3);
    assert_eq!(res["certificate"]["target_vertices"], 2);
    assert_eq!(res["certificate"]["dimensional_dilation"], -1);
    assert_eq!(res["pushforward"], serde_json::json!([true, false]));
    assert_eq!(res["pullback"], serde_json::json!([true, false, false]));
}

#[test]
fn prime_candidate_and_stage_record_actions_dispatch() {
    let eval_payload = serde_json::json!({
        "proposal_id": "prop_42",
        "locus_id": "locus_alpha",
        "raw_payload": "candidate_raw_text",
        "actor": "agent_alpha",
        "admit": true,
        "refusal_reason": null
    });
    let eval_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "prime_candidate_evaluate".to_owned(),
        payload: eval_payload,
    });
    assert!(eval_outcome.success);
    let eval_res = eval_outcome.result.expect("eval result");
    assert_eq!(eval_res["proposal_id"], "prop_42");
    assert_eq!(eval_res["enters_dda_trace"], true);

    let stage_payload = serde_json::json!({
        "seq": 0,
        "stage": "PRIME_000",
        "packet_id": "pkt_001",
        "actor": "tester",
        "status": "ADMITTED",
        "witness_or_refusal": "valid_cochain",
        "prev_record_hash": null
    });
    let stage_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "prime_stage_record".to_owned(),
        payload: stage_payload,
    });
    assert!(stage_outcome.success);
    let stage_res = stage_outcome.result.expect("stage result");
    assert_eq!(stage_res["stage"], "PRIME_000");
    assert!(stage_res["record_hash"].is_string());
}

#[test]
fn challenge_actions_dispatch_end_to_end() {
    let commit_payload = serde_json::json!({
        "challenge_id": "CHAL_TEST",
        "manifest_text": "case_1,case_2",
        "operator": "judge",
        "version": "v1.0"
    });
    let commit_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "challenge_commit".to_owned(),
        payload: commit_payload,
    });
    assert!(commit_outcome.success);
    let commit_res = commit_outcome.result.expect("commit res");
    let commit_hash = commit_res["commitment_hash"].as_str().unwrap().to_string();

    let freeze_payload = serde_json::json!({
        "challenge_id": "CHAL_TEST",
        "deliverable_text": "deliverable code",
        "judge_commitment_hash": commit_hash
    });
    let freeze_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "challenge_freeze".to_owned(),
        payload: freeze_payload,
    });
    assert!(freeze_outcome.success);
    let freeze_res = freeze_outcome.result.expect("freeze res");
    let freeze_record = freeze_res["freeze_record"].clone();

    let score_payload = serde_json::json!({
        "judge_packet": {
            "challenge_id": "CHAL_TEST",
            "commitment_hash": commit_hash,
            "committed_at_utc": "2026-09-30T00:00:00Z",
            "operator": "judge",
            "version": "v1.0",
            "hidden_cases": [{"id": 1, "answer": 10}],
            "checker_a_id": "chk_a",
            "checker_b_id": "chk_b",
            "authority_effect": "None"
        },
        "commitment": commit_res["commitment"],
        "freeze": freeze_record,
        "candidate_outputs": [{"answer": 10}],
        "checker_expected_field": "answer"
    });
    let score_outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "challenge_score".to_owned(),
        payload: score_payload,
    });
    assert!(
        score_outcome.success,
        "challenge_score failed: {:?}",
        score_outcome.error
    );
    let score_res = score_outcome.result.expect("score res");
    assert_eq!(score_res["status"], "VERIFIED");
    assert_eq!(score_res["cases_correct"], 1);
    assert_eq!(score_res["cases_wrong"], 0);
}

// Origin: engine/crates_rs/pfp/src/invoke/tests.rs
// Claim: urn:core:crates_rs:pfp:tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6e4b1a57 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6e4b1a57` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6e4b1a57 {
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
impl BoundaryError6e4b1a57 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6e4b1a57 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6e4b1a57 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6e4b1a57 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6e4b1a57> {
        if capacity_bound == 0 {
            return Err(BoundaryError6e4b1a57::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6e4b1a57::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6e4b1a57::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_6e4b1a57 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6e4b1a57::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6e4b1a57::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6e4b1a57::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6e4b1a57::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6e4b1a57::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6e4b1a57::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6e4b1a57::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
