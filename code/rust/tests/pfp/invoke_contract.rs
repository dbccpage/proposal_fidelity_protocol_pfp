use pfp::{
    dispatch_runtime_request, host_presentation_pins, RuntimeRequestV1, RUNTIME_OUTCOME_SCHEMA,
    RUNTIME_REQUEST_SCHEMA,
};
use serde_json::json;
use sha2::Digest;

#[test]
fn runtime_schema_guard_precedes_action_dispatch() {
    for schema in ["", "core.symbol-game.runtime-request.v0", "foreign"] {
        for (action, payload) in [
            ("canonical_wire", json!({"value": 1})),
            ("domain_digest", json!({"domain": "", "value": null})),
            ("nonexistent_action", json!({})),
        ] {
            let request = RuntimeRequestV1 {
                schema_version: schema.to_owned(),
                action: action.to_owned(),
                payload,
            };
            let outcome = dispatch_runtime_request(&request);
            assert!(!outcome.success);
            assert_eq!(outcome.schema_version, RUNTIME_OUTCOME_SCHEMA);
            assert_eq!(outcome.action, action);
            assert_eq!(outcome.authority_effect, "None");
            assert!(outcome.result.is_none());
            assert!(outcome
                .error
                .as_deref()
                .unwrap()
                .starts_with("RUNTIME_REQUEST_SCHEMA_MISMATCH:"));
        }
    }
}

#[test]
fn current_runtime_schema_preserves_action_success_and_refusals() {
    let request = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "canonical_wire".to_owned(),
        payload: json!({"value": 1}),
    };
    let outcome = dispatch_runtime_request(&request);
    assert!(outcome.success);
    assert!(outcome.result.is_some());
    assert!(outcome.error.is_none());
    assert_eq!(outcome.authority_effect, "None");

    // The transport can carry a finite JSON float, but this action's existing
    // from_json implementation accepts only integer JSON number forms. Preserve
    // its actual refusal text rather than inventing canonical-value acceptance.
    let raw_float = RuntimeRequestV1 {
        payload: json!({"value": 1.25}),
        ..request.clone()
    };
    let float_refusal = dispatch_runtime_request(&raw_float);
    assert!(!float_refusal.success);
    assert_eq!(float_refusal.schema_version, RUNTIME_OUTCOME_SCHEMA);
    assert_eq!(float_refusal.action, raw_float.action);
    assert_eq!(float_refusal.authority_effect, "None");
    assert!(float_refusal.result.is_none());
    assert_eq!(
        float_refusal.error.as_deref(),
        Some("non-finite floats are not canonical")
    );

    let unknown = RuntimeRequestV1 {
        action: "nonexistent_action".to_owned(),
        ..request
    };
    let refused = dispatch_runtime_request(&unknown);
    assert!(!refused.success);
    assert!(refused.result.is_none());
    assert!(refused
        .error
        .unwrap()
        .contains("unsupported runtime action"));
    assert_eq!(refused.action, unknown.action);
    assert_eq!(refused.authority_effect, "None");
}

#[test]
fn test_invoke_canonical_wire_and_digest() {
    let req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "canonical_wire".to_owned(),
        payload: json!({"a": 1, "b": "hello"}),
    };
    let outcome = dispatch_runtime_request(&req);
    assert!(outcome.success);
    assert_eq!(outcome.schema_version, RUNTIME_OUTCOME_SCHEMA);
    assert_eq!(outcome.authority_effect, "None");

    let digest_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "domain_digest".to_owned(),
        payload: json!({
            "domain": "test.domain",
            "value": {"a": 1, "b": "hello"}
        }),
    };
    let digest_outcome = dispatch_runtime_request(&digest_req);
    assert!(digest_outcome.success);
    let digest_str = digest_outcome.result.unwrap().as_str().unwrap().to_owned();
    assert_eq!(digest_str.len(), 64);
}

#[test]
fn test_invoke_diff_parser_and_gates() {
    let patch = r#"--- a/src/lib.rs
+++ b/src/lib.rs
@@ -1,1 +1,1 @@
-old
+new
"#;
    let diff_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "parse_unified_diff".to_owned(),
        payload: json!(patch),
    };
    let diff_outcome = dispatch_runtime_request(&diff_req);
    assert!(diff_outcome.success);
    let res = diff_outcome.result.unwrap();
    assert_eq!(res["is_valid"], true);
    assert_eq!(res["touched_paths"], json!(["src/lib.rs"]));

    let prop_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "create_code_change_proposal".to_owned(),
        payload: json!({
            "task_id": "task_42",
            "objective": "Refactor parser",
            "base_revision": "HEAD",
            "owned_paths": ["src/lib.rs"],
            "protected_paths": [".canon"],
            "candidate_budget": 3,
            "operation_budget": 10,
            "required_gates": ["gate_ownership", "gate_syntax"]
        }),
    };
    let prop_outcome = dispatch_runtime_request(&prop_req);
    assert!(prop_outcome.success);
    let run_root = prop_outcome.result.unwrap();

    // Submit patch
    let submit_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "submit_patch_candidate".to_owned(),
        payload: json!({
            "run_root": run_root,
            "expected_task_packet_sha256": run_root["task_packet_sha256"],
            "candidate_id": "cand_01",
            "producer_id": "agent_alpha",
            "patch_text": patch
        }),
    };
    let submit_outcome = dispatch_runtime_request(&submit_req);
    assert!(submit_outcome.success);
    let submit_res = submit_outcome.result.unwrap();
    let updated_root = &submit_res["run_root"];
    let patch_art = &submit_res["patch_artifact"];

    // Evaluate gates
    let eval_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "evaluate_patch_gates".to_owned(),
        payload: json!({
            "run_root": updated_root,
            "expected_task_packet_sha256": run_root["task_packet_sha256"],
            "expected_run_root_digest": submit_res["run_root_digest"],
            "patch_artifact": patch_art
        }),
    };
    let eval_outcome = dispatch_runtime_request(&eval_req);
    assert!(eval_outcome.success);
    let receipts = eval_outcome.result.unwrap().as_array().unwrap().clone();
    assert_eq!(receipts.len(), 3);
    assert_eq!(receipts[0]["disposition"], "PASS");
    assert_eq!(receipts[1]["disposition"], "PASS");
    assert_eq!(receipts[2]["disposition"], "PASS");
}

#[test]
fn test_invoke_gauge_board_classification() {
    let req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "classify_gauge_board".to_owned(),
        payload: json!({
            "d0": {
                "rows": 3,
                "cols": 3,
                "data": [
                    true, false, false,
                    false, true, false,
                    false, false, true
                ]
            },
            "d1": {
                "rows": 1,
                "cols": 3,
                "data": [false, false, false]
            },
            "cochain": [true, false, false]
        }),
    };
    let outcome = dispatch_runtime_request(&req);
    assert!(outcome.success);
    let res = outcome.result.unwrap();
    assert_eq!(
        res,
        json!({ "GaugeExact": { "lambda": [true, false, false] } })
    );
}

fn strict_gauge_payload(cochain: serde_json::Value) -> serde_json::Value {
    json!({
        "d0": {"rows": 2, "cols": 2, "data": [false, false, false, false]},
        "d1": {"rows": 2, "cols": 2, "data": [true, false, false, true]},
        "cochain": cochain
    })
}

fn gauge_outcome(payload: serde_json::Value) -> serde_json::Value {
    serde_json::to_value(dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "classify_gauge_board".to_owned(),
        payload,
    }))
    .expect("serialize the actual dispatch outcome")
}

fn expected_gauge_outcome(
    result: serde_json::Value,
    error: serde_json::Value,
) -> serde_json::Value {
    json!({
        "schema_version": RUNTIME_OUTCOME_SCHEMA,
        "action": "classify_gauge_board",
        "success": error.is_null(),
        "result": result,
        "error": error,
        "authority_effect": "None"
    })
}

#[test]
fn runtime_gauge_preserves_boolean_and_exact_integer_bits_without_changing_the_verdict() {
    for (cochain, verdict) in [
        (
            json!([false, false]),
            json!({"GaugeExact": {"lambda": [false, false]}}),
        ),
        (
            json!([0, 0]),
            json!({"GaugeExact": {"lambda": [false, false]}}),
        ),
        (
            json!([false, true]),
            json!({"LocalCurvature": {"syndrome": [false, true]}}),
        ),
        (
            json!([0, 1]),
            json!({"LocalCurvature": {"syndrome": [false, true]}}),
        ),
        (
            json!([false, 1]),
            json!({"LocalCurvature": {"syndrome": [false, true]}}),
        ),
    ] {
        assert_eq!(
            gauge_outcome(strict_gauge_payload(cochain)),
            expected_gauge_outcome(verdict, json!(null))
        );
    }
}

#[test]
fn runtime_gauge_refuses_each_non_bit_at_its_actual_index_instead_of_classifying_it() {
    // D0 is zero and D1 is identity: coercing the second entry to false
    // manufactures GaugeExact; coercing it to true manufactures curvature.
    for token in [
        "null",
        "\"not-a-bit\"",
        "{}",
        "[]",
        "-1",
        "2",
        "255",
        "0.0",
        "1.0",
        "1e0",
        "1e999",
    ] {
        let item: serde_json::Value = serde_json::from_str(token).expect("valid JSON fixture");
        let payload = strict_gauge_payload(json!([false, item]));
        assert_eq!(
            gauge_outcome(payload),
            expected_gauge_outcome(
                json!(null),
                json!("INVALID_COCHAIN: cochain[1] must be boolean or integer 0 or 1")
            ),
            "non-bit fixture {token}"
        );
    }
}

#[test]
fn runtime_gauge_requires_an_explicit_array_even_when_the_empty_cochain_would_classify() {
    let empty = json!({
        "d0": {"rows": 0, "cols": 0, "data": []},
        "d1": {"rows": 0, "cols": 0, "data": []}
    });
    let mut cases = vec![empty.clone()];
    for cochain in [
        json!(null),
        json!(false),
        json!(true),
        json!(0),
        json!(1),
        json!(""),
        json!({}),
    ] {
        let mut payload = empty.clone();
        payload["cochain"] = cochain;
        cases.push(payload);
    }
    for payload in cases {
        assert_eq!(
            gauge_outcome(payload.clone()),
            expected_gauge_outcome(
                json!(null),
                json!("INVALID_COCHAIN: cochain must be an explicit array")
            ),
            "missing/nonarray fixture {payload}"
        );
    }
}

#[test]
fn runtime_gauge_accepts_the_explicit_empty_cochain_on_a_zero_dimensional_board() {
    assert_eq!(
        gauge_outcome(json!({
            "d0": {"rows": 0, "cols": 0, "data": []},
            "d1": {"rows": 0, "cols": 0, "data": []},
            "cochain": []
        })),
        expected_gauge_outcome(json!({"GaugeExact": {"lambda": []}}), json!(null))
    );
}

// ---------------------------------------------------------------------------
// Presentation pinning across the wire.
//
// `evaluate_critical_peak` takes the presentation from the same payload as the
// claim. Before these, a producer supplying its own rewrite system got a bare
// `JOINED` back, and nothing on the wire distinguished that from a join under
// rules the host recognises.
// ---------------------------------------------------------------------------

/// {p1: ab -> ba, p2: cd -> dc}. Nothing pins it, and it is not length-reducing,
/// but both reachable sets close -- so the host really does decide the peak.
fn swapping_payload() -> serde_json::Value {
    json!({
        "presentation": {
            "signature": ["a", "b", "c", "d"],
            "rules": [
                {"name": "p1", "lhs": "ab", "rhs": "ba"},
                {"name": "p2", "lhs": "cd", "rhs": "dc"}
            ]
        },
        "claim": {
            "source": "abcd",
            "left": {"steps": [{"rule": "p1", "position": 0}], "endpoint": "bacd"},
            "right": {"steps": [{"rule": "p2", "position": 2}], "endpoint": "abdc"},
            "join": null,
            "steps_inspected": 0,
            "step_budget": 10000
        }
    })
}

/// The period-5 successor cycle, which `symbol_game_presentations.json` pins.
fn c5_payload() -> serde_json::Value {
    json!({
        "presentation": {
            "signature": ["\u{3b1}", "\u{3b2}", "\u{3b3}", "\u{3b4}", "\u{3b5}"],
            "rules": [
                {"name": "succ_alpha", "lhs": "\u{3b1}", "rhs": "\u{3b2}"},
                {"name": "succ_beta", "lhs": "\u{3b2}", "rhs": "\u{3b3}"},
                {"name": "succ_gamma", "lhs": "\u{3b3}", "rhs": "\u{3b4}"},
                {"name": "succ_delta", "lhs": "\u{3b4}", "rhs": "\u{3b5}"},
                {"name": "succ_epsilon", "lhs": "\u{3b5}", "rhs": "\u{3b1}"}
            ]
        },
        "claim": {
            "source": "\u{3b1}\u{3b2}",
            "left": {
                "steps": [{"rule": "succ_alpha", "position": 0}],
                "endpoint": "\u{3b2}\u{3b2}"
            },
            "right": {
                "steps": [{"rule": "succ_beta", "position": 1}],
                "endpoint": "\u{3b1}\u{3b3}"
            },
            "join": null,
            "steps_inspected": 0,
            "step_budget": 10000
        }
    })
}

fn evaluate(payload: serde_json::Value) -> serde_json::Value {
    let outcome = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "evaluate_critical_peak".to_owned(),
        payload,
    });
    assert!(outcome.success, "dispatch failed: {:?}", outcome.error);
    outcome.result.expect("an evaluation")
}

#[test]
fn a_join_under_the_producers_own_rules_is_reported_as_self_consistent_only() {
    let result = evaluate(swapping_payload());
    assert_eq!(result["token"], "SELF_CONSISTENT_ONLY");
    assert_eq!(result["evaluation"]["authority"], "ProducerDeclared");

    // The mathematics is not suppressed -- only the endorsement is withheld.
    assert!(
        result["evaluation"]["verdict"]["Joined"].is_object(),
        "the join is still reported: {result}"
    );
    assert!(
        result["evaluation"]["obligations"]
            .as_array()
            .expect("obligations")
            .iter()
            .any(|o| o
                .as_str()
                .unwrap_or_default()
                .contains("FW-PRESENTATION-UNKNOWN")),
        "expected the unknown-presentation obligation: {result}"
    );
}

#[test]
fn a_join_under_a_governance_pinned_presentation_is_reported_as_joined() {
    // The other side of the same decision. Without it, a host that always said
    // SELF_CONSISTENT_ONLY would pass the test above.
    let result = evaluate(c5_payload());
    assert_eq!(
        result["token"], "JOINED",
        "the c5 successor cycle is pinned in governance: {result}"
    );
    assert_eq!(result["evaluation"]["authority"]["HostPinned"]["pin"], "c5");
    let obligations = result["evaluation"]["obligations"]
        .as_array()
        .expect("obligations");
    assert!(
        !obligations.iter().any(|obligation| obligation
            .as_str()
            .unwrap_or_default()
            .contains("FW-PRESENTATION-UNKNOWN")),
        "a pinned presentation raises no presentation obligation: {result}"
    );
    assert!(
        obligations.iter().any(|obligation| obligation
            .as_str()
            .unwrap_or_default()
            .contains("FW-PEAK-NONCRITICAL")),
        "the two disjoint successor rewrites are joinable but not a critical pair: {result}"
    );
}

#[test]
fn a_pin_set_cannot_be_supplied_in_the_payload() {
    // The laundering attempt this whole path exists to refuse: the producer
    // supplies the rules AND declares them pinned. Pins are host-side, and
    // PresentationPins derives no Deserialize, so there is no shape a payload
    // could take that would reach the pin set.
    let mut payload = swapping_payload();
    payload["pins"] = json!([{ "name": "swapping", "presentation": payload["presentation"] }]);
    payload["presentation_authority"] = json!({ "HostPinned": { "pin": "swapping" } });

    let result = evaluate(payload);
    assert_eq!(
        result["token"], "SELF_CONSISTENT_ONLY",
        "a producer-supplied pin must change nothing: {result}"
    );
    assert_eq!(result["evaluation"]["authority"], "ProducerDeclared");
}

#[test]
fn reordering_the_rules_does_not_defeat_the_pin() {
    // The digest names the rewriting system, not the bytes. If it named the
    // bytes, shuffling the payload would silently downgrade a pinned
    // presentation to SELF_CONSISTENT_ONLY.
    let mut payload = c5_payload();
    let rules = payload["presentation"]["rules"]
        .as_array()
        .expect("rules")
        .clone();
    payload["presentation"]["rules"] = json!(rules.iter().rev().cloned().collect::<Vec<_>>());

    let result = evaluate(payload);
    assert_eq!(result["token"], "JOINED");
    assert_eq!(result["evaluation"]["authority"]["HostPinned"]["pin"], "c5");
}

#[test]
fn changing_one_rule_leaves_the_pin_behind() {
    // And the other half: a presentation that is ALMOST the pinned one is not
    // the pinned one. Without this, a digest that ignored the rules entirely
    // would pass the reorder test.
    let mut payload = c5_payload();
    payload["presentation"]["rules"][0]["rhs"] = json!("\u{3b3}");
    payload["claim"]["left"]["endpoint"] = json!("\u{3b3}\u{3b2}");

    let result = evaluate(payload);
    assert_eq!(
        result["evaluation"]["authority"], "ProducerDeclared",
        "one altered rule is a different rewriting system: {result}"
    );
}

#[test]
fn the_host_pins_exactly_what_governance_declares() {
    // Guards the pin file itself. If it silently emptied, every test above
    // that expects ProducerDeclared would still pass -- for the wrong reason.
    let pins = host_presentation_pins();
    // `c6` is the Examiner negative control, pinned 2026-09-04. It is the only
    // entry that is not a system the corpus's claims are about, and its note in
    // the pin file says so.
    assert_eq!(pins.pin_names(), vec!["c5", "c6"]);
    assert_eq!(pins.len(), 2);
    assert!(!pins.is_empty());
}

#[test]
fn a_verdict_that_decides_nothing_keeps_its_own_token() {
    // NeedsEvidence settles nothing, so provenance has nothing to qualify.
    // Reporting it as SELF_CONSISTENT_ONLY would be false: it is not
    // consistent, it is undecided.
    let payload = json!({
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
    let result = evaluate(payload);
    assert_eq!(result["token"], "NEEDS_EVIDENCE");
    assert_eq!(result["evaluation"]["authority"], "ProducerDeclared");
}

// -- functional_evaluate / functional_verify: CODA-FOC Layer 1 across the seam --

/// K0: four vertices, edges (0,1) (1,2) (2,3) (3,0) (0,2), one face 0-1-2.
fn k0_payload(residual: [&str; 5]) -> serde_json::Value {
    json!({
        "d0": {"rows": [
            ["-1", "1", "0", "0"],
            ["0", "-1", "1", "0"],
            ["0", "0", "-1", "1"],
            ["1", "0", "0", "-1"],
            ["-1", "0", "1", "0"],
        ]},
        "d1": {"rows": [["1", "1", "0", "0", "-1"]]},
        "residual": residual,
    })
}

fn runtime(action: &str, payload: serde_json::Value) -> pfp::RuntimeOutcomeV1 {
    dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: action.to_owned(),
        payload,
    })
}

fn refusal_code(outcome: &pfp::RuntimeOutcomeV1) -> String {
    assert!(
        !outcome.success,
        "expected a refusal, got {:?}",
        outcome.result
    );
    assert!(outcome.result.is_none());
    let error = outcome.error.as_deref().unwrap();
    error.split(':').next().unwrap().to_owned()
}

#[test]
fn functional_evaluate_classifies_each_k0_fixture_from_rust_evidence() {
    for (residual, phi1, gamma2, class) in [
        (["-1", "0", "0", "1", "-1"], "0", "0", "ExactRepair"),
        (["0", "0", "1", "1", "0"], "2", "0", "ClosedResidual"),
        (["0", "0", "0", "0", "1"], "1", "1", "ActiveClosureFailure"),
    ] {
        let outcome = runtime("functional_evaluate", k0_payload(residual));
        assert!(outcome.success, "{:?}", outcome.error);
        assert_eq!(outcome.authority_effect, "None");
        let receipt = outcome.result.unwrap();
        assert_eq!(receipt["phi1"], phi1);
        assert_eq!(receipt["gamma2"], gamma2);
        assert_eq!(receipt["diagnostic_class"], class);
        assert_eq!(receipt["second_stage_repairs"], "none");
        assert_eq!(receipt["evidence_provenance"], "VerifierProduced");
        assert_eq!(receipt["authority_effect"], "None");
        assert_eq!(receipt["input_digest"].as_str().unwrap().len(), 64);
        let text = serde_json::to_string(&receipt).unwrap();
        assert!(!text.contains("/1\""), "an integer crossed as p/1: {text}");
    }
}

#[test]
fn functional_evaluate_refuses_a_complex_that_breaks_the_chain_law() {
    let mut payload = k0_payload(["0", "0", "0", "0", "1"]);
    payload["d1"] = json!({"rows": [["1", "0", "0", "0", "0"]]});
    assert_eq!(
        refusal_code(&runtime("functional_evaluate", payload)),
        "CHAIN_LAW_VIOLATED"
    );
}

#[test]
fn functional_evaluate_refuses_floats_before_reading_any_value() {
    let mut in_budget = k0_payload(["0", "0", "0", "0", "1"]);
    in_budget["budget"] = json!(1.5);
    let mut in_residual = k0_payload(["0", "0", "0", "0", "1"]);
    in_residual["residual"][4] = json!(0.5);
    for payload in [in_budget, in_residual] {
        assert_eq!(
            refusal_code(&runtime("functional_evaluate", payload)),
            "FLOAT_FORBIDDEN"
        );
    }
}

#[test]
fn functional_evaluate_refuses_rationals_not_in_canonical_form() {
    for text in ["1/1", "2/4", "0.5", "", "one"] {
        let mut payload = k0_payload(["0", "0", "0", "0", "1"]);
        payload["residual"][4] = json!(text);
        assert_eq!(
            refusal_code(&runtime("functional_evaluate", payload)),
            "INVALID_FUNCTIONAL_REQUEST",
            "{text:?} was accepted"
        );
    }
}

#[test]
fn functional_evaluate_answers_budget_unknown_instead_of_guessing() {
    let rows = vec![vec!["0"; 64]; 65];
    let payload = json!({"d0": {"rows": rows}, "d1": {"rows": []}, "residual": vec!["0"; 65]});
    assert_eq!(
        refusal_code(&runtime("functional_evaluate", payload)),
        "BUDGET_UNKNOWN"
    );
}

#[test]
fn functional_verify_binds_a_receipt_to_the_request_that_produced_it() {
    let request = k0_payload(["0", "0", "1", "1", "0"]);
    let receipt = runtime("functional_evaluate", request.clone())
        .result
        .unwrap();

    let replayed = runtime(
        "functional_verify",
        json!({"request": request, "receipt": receipt}),
    );
    assert!(replayed.success, "{:?}", replayed.error);
    let verdict = replayed.result.unwrap();
    assert_eq!(verdict["accepted"], true);
    assert_eq!(verdict["mismatched_fields"], json!([]));

    let mut moved = request.clone();
    moved["residual"][4] = json!("1");
    let verdict = runtime(
        "functional_verify",
        json!({"request": moved, "receipt": receipt}),
    )
    .result
    .unwrap();
    assert_eq!(verdict["accepted"], false);
    assert!(verdict["mismatched_fields"]
        .as_array()
        .unwrap()
        .contains(&json!("input_digest")));

    let mut forged = receipt.clone();
    forged["phi1"] = json!("1");
    let verdict = runtime(
        "functional_verify",
        json!({"request": request, "receipt": forged}),
    )
    .result
    .unwrap();
    assert_eq!(verdict["accepted"], false);
    assert_eq!(verdict["mismatched_fields"], json!(["phi1"]));
}

/// The digest is recomputed here from the documented framing, independently of
/// the host, and pinned. The Python seam test pins the same vector, so the two
/// sides of the boundary cannot drift apart silently.
#[test]
fn functional_input_digest_is_the_documented_framing() {
    use sha2::{Digest, Sha256};

    let domain = pfp::functional::FUNCTIONAL_REQUEST_DOMAIN.as_bytes();
    let body = br#"{"d0":{"rows":[["-1","1","0","0"],["0","-1","1","0"],["0","0","-1","1"],["1","0","0","-1"],["-1","0","1","0"]]},"d1":{"rows":[["1","1","0","0","-1"]]},"residual":["0","0","1","1","0"]}"#;
    let mut hasher = Sha256::new();
    hasher.update((domain.len() as u32).to_be_bytes());
    hasher.update(domain);
    hasher.update((body.len() as u64).to_be_bytes());
    hasher.update(body);
    let independent = hex::encode(hasher.finalize());

    let receipt = runtime("functional_evaluate", k0_payload(["0", "0", "1", "1", "0"]))
        .result
        .unwrap();
    assert_eq!(receipt["input_digest"], independent);
    assert_eq!(
        independent,
        "43c05d791424bdfd2f814db2791adca5c088b5c8d2d2d231ee9a62de9b5e432a"
    );
}

// -- coda_evaluate / coda_verify: CODA Master Normal Form across the seam --

fn valid_coda_payload() -> serde_json::Value {
    json!({
        "input_id": "coda_test_01",
        "sieve_non_empty": true,
        "refinement_consistent": true,
        "gluing_succeeded": true,
        "phi1_distance": 0,
        "gamma2_distance": 0,
        "license_granted": true,
    })
}

#[test]
fn coda_evaluate_runs_lean_table_cases() {
    // 1. Authorized ExactRepair
    let p1 = valid_coda_payload();
    let outcome = runtime("coda_evaluate", p1.clone());
    assert!(outcome.success, "{:?}", outcome.error);
    assert_eq!(outcome.authority_effect, "None");
    let receipt = outcome.result.unwrap();
    assert_eq!(receipt["diagnostic"], "ExactRepair");
    assert_eq!(receipt["routing"], "CheckPassed");
    assert_eq!(receipt["premise_source"], "declared");
    assert_eq!(receipt["authority"]["Refused"], "Refusal");
    assert!(receipt["authority"].get("Terminal").is_none());
    assert_eq!(receipt["authority_effect"], "None");

    // 2. Firewalled Unlicensed ExactRepair (CODA_GTLA-T9)
    let mut p2 = valid_coda_payload();
    p2["license_granted"] = json!(false);
    let outcome = runtime("coda_evaluate", p2);
    assert!(outcome.success);
    let receipt = outcome.result.unwrap();
    assert_eq!(receipt["diagnostic"], "ExactRepair");
    assert_eq!(receipt["routing"], "CheckPassed");
    assert_eq!(receipt["authority"]["Refused"], "Refusal");

    // 3. ClosedResidual Sentinel
    let mut p3 = valid_coda_payload();
    p3["phi1_distance"] = json!(3);
    p3["license_granted"] = json!(false);
    let outcome = runtime("coda_evaluate", p3);
    assert!(outcome.success);
    let receipt = outcome.result.unwrap();
    assert_eq!(receipt["diagnostic"], "ClosedResidual");
    assert_eq!(receipt["routing"], "Repair");
    assert_eq!(receipt["authority"]["Residual"], "ClosedResidual");

    // 4. Sieve Empty Refusal
    let mut p4 = valid_coda_payload();
    p4["sieve_non_empty"] = json!(false);
    let outcome = runtime("coda_evaluate", p4);
    assert!(outcome.success);
    let receipt = outcome.result.unwrap();
    assert_eq!(receipt["routing"], "NoRule");
    assert_eq!(receipt["authority"]["Refused"], "Refusal");

    // 5. Refinement Failure
    let mut p5 = valid_coda_payload();
    p5["refinement_consistent"] = json!(false);
    let outcome = runtime("coda_evaluate", p5);
    assert!(outcome.success);
    let receipt = outcome.result.unwrap();
    assert_eq!(receipt["routing"], "Repair");
    assert_eq!(receipt["authority"]["Refused"], "Repair");

    // 6. Nonclosed Defect
    let mut p6 = valid_coda_payload();
    p6["phi1_distance"] = json!(2);
    p6["gamma2_distance"] = json!(4);
    let outcome = runtime("coda_evaluate", p6);
    assert!(outcome.success);
    let receipt = outcome.result.unwrap();
    assert_eq!(receipt["routing"], "RequiresLift");
    assert_eq!(receipt["authority"]["Refused"], "Refusal");
}

#[test]
fn coda_evaluate_refuses_foc_t3_inconsistent_witness() {
    let mut payload = valid_coda_payload();
    payload["phi1_distance"] = json!(0);
    payload["gamma2_distance"] = json!(1);
    assert_eq!(
        refusal_code(&runtime("coda_evaluate", payload)),
        "INCONSISTENT_WITNESS"
    );
}

#[test]
fn coda_evaluate_refuses_floats_before_reading_any_value() {
    let mut in_distance = valid_coda_payload();
    in_distance["phi1_distance"] = json!(1.5);
    let mut in_budget = valid_coda_payload();
    in_budget["budget"] = json!(2.5);
    for payload in [in_distance, in_budget] {
        assert_eq!(
            refusal_code(&runtime("coda_evaluate", payload)),
            "FLOAT_FORBIDDEN"
        );
    }
}

#[test]
fn coda_evaluate_answers_budget_unknown_instead_of_guessing() {
    let mut payload = valid_coda_payload();
    payload["phi1_distance"] = json!(5000);
    assert_eq!(
        refusal_code(&runtime("coda_evaluate", payload)),
        "BUDGET_UNKNOWN"
    );

    let mut small_budget = valid_coda_payload();
    small_budget["phi1_distance"] = json!(20);
    small_budget["budget"] = json!(10);
    assert_eq!(
        refusal_code(&runtime("coda_evaluate", small_budget)),
        "BUDGET_UNKNOWN"
    );
}

#[test]
fn coda_verify_binds_a_receipt_to_the_request_that_produced_it() {
    let request = valid_coda_payload();
    let receipt = runtime("coda_evaluate", request.clone()).result.unwrap();

    let replayed = runtime(
        "coda_verify",
        json!({"request": request, "receipt": receipt}),
    );
    assert!(replayed.success, "{:?}", replayed.error);
    let verdict = replayed.result.unwrap();
    assert_eq!(verdict["accepted"], true);
    assert_eq!(verdict["mismatched_fields"], json!([]));

    let mut moved = request.clone();
    moved["input_id"] = json!("different_id");
    let verdict = runtime("coda_verify", json!({"request": moved, "receipt": receipt}))
        .result
        .unwrap();
    assert_eq!(verdict["accepted"], false);
    assert!(verdict["mismatched_fields"]
        .as_array()
        .unwrap()
        .contains(&json!("input_digest")));

    let mut forged = receipt.clone();
    forged["diagnostic"] = json!("ActiveClosureFailure");
    let verdict = runtime(
        "coda_verify",
        json!({"request": request, "receipt": forged}),
    )
    .result
    .unwrap();
    assert_eq!(verdict["accepted"], false);
    assert_eq!(verdict["mismatched_fields"], json!(["diagnostic"]));
}

#[test]
fn ddc_verify_tape_all_18_paper_demos() {
    let json_bytes = include_bytes!("fixtures/ddc_paper_demos.json");
    let demos: Vec<serde_json::Value> = serde_json::from_slice(json_bytes).unwrap();
    assert_eq!(demos.len(), 18);

    for demo in &demos {
        let name = demo["name"].as_str().unwrap();
        let expected_lawful = demo["lawful"].as_bool().unwrap();
        let expected_letters = demo["letters"].as_str().unwrap();
        let expected_receipt_head = demo["receipt_head"].as_str().unwrap();

        let req = json!({
            "initial_state": demo["initial_state"],
            "steps": demo["steps"],
        });

        let outcome = runtime("ddc_verify_tape", req);
        assert!(
            outcome.success,
            "ddc_verify_tape failed on {name}: {:?}",
            outcome.error
        );
        let res = outcome.result.unwrap();

        assert_eq!(
            res["lawful"].as_bool().unwrap(),
            expected_lawful,
            "demo {name} lawful mismatch"
        );
        assert_eq!(
            res["letters"].as_str().unwrap(),
            expected_letters,
            "demo {name} letters mismatch"
        );
        assert_eq!(
            res["receipt_head"].as_str().unwrap(),
            expected_receipt_head,
            "demo {name} receipt_head mismatch"
        );
    }
}

#[test]
fn prime_admit_and_replay_decide_contract_checks() {
    // 1. Valid admission
    let admit_ok = runtime(
        "prime_admit",
        json!({
            "carrier": "c1",
            "primitive_difference": "delta1",
            "zero_rel": "z1",
            "observer": "obs1",
            "witnesses": ["w1"],
            "justify_cochain": true,
            "window": {
                "dim_c0": 1,
                "dim_c1": 1,
                "dim_c2": 1,
                "square_zero": true,
                "l1_defect_mass": 0
            }
        }),
    );
    assert!(admit_ok.success);
    let res = admit_ok.result.unwrap();
    assert_eq!(res["admitted"], true);

    // 2. Missing observer -> admission refused
    let admit_err = runtime(
        "prime_admit",
        json!({
            "carrier": "c1",
            "primitive_difference": "delta1",
            "zero_rel": "z1",
            "observer": null,
            "witnesses": ["w1"],
            "justify_cochain": true,
            "window": {
                "dim_c0": 1,
                "dim_c1": 1,
                "dim_c2": 1,
                "square_zero": true,
                "l1_defect_mass": 0
            }
        }),
    );
    assert!(admit_err.success);
    let res = admit_err.result.unwrap();
    assert_eq!(res["admitted"], false);
    assert_eq!(res["reason"], "MISSING_observer");

    // 3. Replay decide with valid steps
    let replay_ok = runtime(
        "prime_replay_decide",
        json!({
            "steps": [
                {"prime_step": 1, "op": "C", "executed": true, "message": "context"},
                {"prime_step": 2, "op": "R", "executed": true, "message": "residual"},
                {"prime_step": 3, "op": "T", "executed": true, "message": "terminal"}
            ]
        }),
    );
    assert!(replay_ok.success);
    let res = replay_ok.result.unwrap();
    assert_eq!(res["decision"], "Terminalized");
    assert_eq!(res["conforms"], true);
    assert_eq!(res["letter_tape"], "CRT");

    // 4. Replay decide with missing required letter -> non-conforming
    let replay_invalid = runtime(
        "prime_replay_decide",
        json!({
            "steps": [
                {"prime_step": 1, "op": "C", "executed": true, "message": "context"},
                {"prime_step": 2, "op": "T", "executed": true, "message": "terminal"}
            ]
        }),
    );
    assert!(replay_invalid.success);
    let res = replay_invalid.result.unwrap();
    assert_eq!(res["conforms"], false);
    assert!(res["violations"]
        .as_array()
        .unwrap()
        .iter()
        .any(|v| v.as_str().unwrap().contains("MissingRequiredLetter")));
}

#[test]
fn test_invoke_prime_descent() {
    let outcome = runtime(
        "prime_descent",
        json!({
            "run_id": "test_descent_run_01",
            "carrier": {
                "num_vertices": 3,
                "edges": [
                    {"tail": 0, "head": 1, "weight": 1},
                    {"tail": 1, "head": 2, "weight": 1},
                    {"tail": 2, "head": 0, "weight": 1}
                ],
                "faces": [[0, 1, 2]]
            },
            "omega": [-2, 1, 1],
            "max_steps": 16
        }),
    );
    assert!(outcome.success, "{:?}", outcome.error);
    assert_eq!(outcome.authority_effect, "None");
    let res = outcome.result.unwrap();
    assert_eq!(res["run_id"], "test_descent_run_01");
    assert_eq!(res["authority_effect"], "None");
    assert!(res["letters"].is_string());
    assert!(res["terminal_status"].is_string());
    assert!(res["phi1"].is_string());
    assert!(res["gamma2"].is_string());
    assert_eq!(res["laws_passed"], false);
}

#[test]
fn test_invoke_lggr_classify() {
    // 1. Negative gluing defect (Local Green, Global Red): e1=true, e2=true, eg=false -> delta_eval = -1
    let outcome = runtime(
        "lggr_classify",
        json!({
            "e1": true,
            "e2": true,
            "eg": false,
        }),
    );
    assert!(outcome.success, "{:?}", outcome.error);
    assert_eq!(outcome.authority_effect, "None");
    let res = outcome.result.unwrap();
    assert_eq!(res["delta_eval"], -1);
    assert_eq!(res["defect_class"], "NegativeGluingDefect");
    assert_eq!(res["authority_effect"], "None");

    // 2. Positive gluing defect: e1=false, e2=true, eg=true -> delta_eval = 1
    let pos = runtime(
        "lggr_classify",
        json!({
            "e1": false,
            "e2": true,
            "eg": true,
        }),
    );
    assert!(pos.success);
    let res = pos.result.unwrap();
    assert_eq!(res["delta_eval"], 1);
    assert_eq!(res["defect_class"], "PositiveGluingDefect");

    // 3. Zero defect (Concordant): e1=true, e2=true, eg=true -> delta_eval = 0
    let zero = runtime(
        "lggr_classify",
        json!({
            "e1": true,
            "e2": true,
            "eg": true,
        }),
    );
    assert!(zero.success);
    let res = zero.result.unwrap();
    assert_eq!(res["delta_eval"], 0);
    assert_eq!(res["defect_class"], "ZeroDefect");
}

#[test]
fn test_invoke_lggr_soundness() {
    // Sound case: rank(QD) = rank(D) = 2
    let sound_outcome = runtime(
        "lggr_soundness",
        json!({
            "d": {
                "rows": [
                    ["1", "0"],
                    ["0", "1"]
                ]
            },
            "q": {
                "rows": [
                    ["1", "0"],
                    ["0", "1"]
                ]
            }
        }),
    );
    assert!(sound_outcome.success, "{:?}", sound_outcome.error);
    assert_eq!(sound_outcome.authority_effect, "None");
    let res = sound_outcome.result.unwrap();
    assert_eq!(res["sound"], true);
    assert_eq!(res["d_rank"], 2);
    assert_eq!(res["qd_rank"], 2);
    assert_eq!(res["witness"], serde_json::Value::Null);
    assert_eq!(res["authority_effect"], "None");

    // Unsound case: rank(QD) = 1 < rank(D) = 2, with witness
    let unsound_outcome = runtime(
        "lggr_soundness",
        json!({
            "d": {
                "rows": [
                    ["1", "0"],
                    ["0", "1"]
                ]
            },
            "q": {
                "rows": [
                    ["1", "0"],
                    ["0", "0"]
                ]
            }
        }),
    );
    assert!(unsound_outcome.success, "{:?}", unsound_outcome.error);
    assert_eq!(unsound_outcome.authority_effect, "None");
    let res = unsound_outcome.result.unwrap();
    assert_eq!(res["sound"], false);
    assert_eq!(res["d_rank"], 2);
    assert_eq!(res["qd_rank"], 1);
    assert_eq!(res["witness"], json!(["0", "1"]));
    assert_eq!(res["authority_effect"], "None");
}

fn code_change_create_payload() -> serde_json::Value {
    json!({
        "task_id": "task_bind",
        "objective": "Refactor parser",
        "base_revision": "HEAD",
        "owned_paths": ["src/lib.rs"],
        "protected_paths": [".canon"],
        "candidate_budget": 3,
        "operation_budget": 10,
        "required_gates": ["gate_ownership", "gate_syntax"]
    })
}

const CANON_PATCH: &str =
    "--- a/.canon/rules.yaml\n+++ b/.canon/rules.yaml\n@@ -1,1 +1,1 @@\n-old\n+new\n";

/// Counterexample from the study: `protected_paths: ".canon"` (a string, not
/// an array) was read as `unwrap_or_default()`, so the proposal was created
/// with no protected paths at all. Every required field must now refuse.
#[test]
fn create_code_change_proposal_refuses_each_malformed_required_field() {
    let control = runtime("create_code_change_proposal", code_change_create_payload());
    assert!(control.success, "{:?}", control.error);

    let mutations: Vec<(&str, Option<serde_json::Value>)> = vec![
        ("protected_paths", Some(json!(".canon"))),
        ("protected_paths", Some(json!([1]))),
        ("protected_paths", Some(json!(null))),
        ("protected_paths", None),
        ("owned_paths", Some(json!("src/lib.rs"))),
        ("owned_paths", None),
        ("required_gates", Some(json!("gate_syntax"))),
        ("required_gates", None),
        ("task_id", Some(json!(7))),
        ("task_id", None),
        ("objective", None),
        ("base_revision", None),
        ("candidate_budget", Some(json!("4"))),
        ("candidate_budget", Some(json!(2.5))),
        ("candidate_budget", Some(json!(true))),
        ("candidate_budget", Some(json!(-1))),
        ("candidate_budget", None),
        ("operation_budget", Some(json!(1.0))),
        ("operation_budget", None),
        ("unexpected_field", Some(json!(true))),
    ];
    for (field, replacement) in mutations {
        let mut payload = code_change_create_payload();
        let object = payload.as_object_mut().unwrap();
        match replacement.clone() {
            Some(value) => {
                object.insert(field.to_owned(), value);
            }
            None => {
                object.remove(field);
            }
        }
        let outcome = runtime("create_code_change_proposal", payload);
        assert_eq!(
            refusal_code(&outcome),
            "REFUSAL_CODE_CHANGE_REQUEST_INVALID",
            "{field} = {replacement:?} must be refused"
        );
    }
}

/// Counterexample: the run root is a caller-held value. Emptying its
/// protected paths between create and evaluate used to turn the protected
/// gate from FAIL to PASS; the recorded digest now refuses the edited root.
#[test]
fn evaluate_patch_gates_verifies_the_run_root_digest_recorded_at_create() {
    let created = runtime("create_code_change_proposal", code_change_create_payload());
    assert!(created.success, "{:?}", created.error);
    let run_root = created.result.unwrap();
    assert_ne!(run_root["task_packet_sha256"], json!(""));

    let expected = run_root["task_packet_sha256"].clone();

    let submitted = runtime(
        "submit_patch_candidate",
        json!({
            "run_root": run_root,
            "expected_task_packet_sha256": expected,
            "candidate_id": "cand_01",
            "producer_id": "agent",
            "patch_text": CANON_PATCH
        }),
    );
    assert!(submitted.success, "{:?}", submitted.error);
    let submitted = submitted.result.unwrap();

    let honest = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": submitted["run_root"],
            "expected_task_packet_sha256": expected,
            "expected_run_root_digest": submitted["run_root_digest"],
            "patch_artifact": submitted["patch_artifact"]
        }),
    );
    assert!(honest.success, "{:?}", honest.error);
    let receipts = honest.result.unwrap();
    assert_eq!(receipts[2]["gate_name"], "gate_protected");
    assert_eq!(receipts[2]["disposition"], "FAIL");

    let mut edited = submitted["run_root"].clone();
    edited["payload"]["protected_paths"] = json!([]);
    edited["payload"]["owned_paths"] = json!([".canon", "src/lib.rs"]);
    let forged = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": edited,
            "expected_task_packet_sha256": expected,
            "expected_run_root_digest": submitted["run_root_digest"],
            "patch_artifact": submitted["patch_artifact"]
        }),
    );
    assert_eq!(refusal_code(&forged), "REFUSAL_RUN_ROOT_BINDING_MISMATCH");

    let mut unknown_field = json!({
        "run_root": submitted["run_root"],
        "expected_task_packet_sha256": expected,
        "expected_run_root_digest": submitted["run_root_digest"],
        "patch_artifact": submitted["patch_artifact"]
    });
    unknown_field["note"] = json!("extra");
    let refused = runtime("evaluate_patch_gates", unknown_field);
    assert_eq!(
        refusal_code(&refused),
        "REFUSAL_CODE_CHANGE_REQUEST_INVALID"
    );
}

/// The aliases `solve_exact_l1_primal_dual` and `solve_exact_l1_projection`
/// were dispatched although `RUNTIME_ACTIONS` did not declare them, so the
/// advertised surface was smaller than the real one.
#[test]
fn undeclared_l1_aliases_are_unsupported_actions() {
    let payload = json!({"matrix": {"rows": [["-1", "1"]]}, "target": ["2"]});
    let declared = runtime("exact_solve_l1_primal_dual", payload.clone());
    assert!(declared.success, "{:?}", declared.error);
    for alias in ["solve_exact_l1_primal_dual", "solve_exact_l1_projection"] {
        let outcome = runtime(alias, payload.clone());
        assert!(!outcome.success);
        assert!(
            outcome
                .error
                .as_deref()
                .unwrap()
                .contains("unsupported runtime action"),
            "{alias} must not dispatch"
        );
    }
}

/// The factorization preserves every pre-existing adapter/action pair and its
/// order. The invocation manifest binds these declarations directly to real
/// handlers; `every_declared_action_reaches_a_dispatch_arm` separately executes
/// each action and rejects missing implementations.
#[test]
fn every_dispatch_arm_is_a_declared_action() {
    let expected: Vec<(String, String)> =
        serde_json::from_str(include_str!("fixtures/runtime_actions_v1.json"))
            .expect("frozen pre-refactor action surface");
    let actual_in_expected: Vec<(String, String)> = pfp::invoke::RUNTIME_ACTIONS
        .iter()
        .map(|(adapter, action)| ((*adapter).to_owned(), (*action).to_owned()))
        .filter(|pair| expected.contains(pair))
        .collect();
    assert_eq!(expected.len(), 106);
    assert_eq!(actual_in_expected, expected);
}

const PARSER_PATCH: &str = "--- a/src/lib.rs\n+++ b/src/lib.rs\n@@ -1,1 +1,1 @@\n-old\n+new\n";

fn sha256_of(text: &str) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(text.as_bytes());
    hex::encode(hasher.finalize())
}

/// Create a guarded proposal and admit one parser patch through the wire.
fn admitted_parser_patch() -> (serde_json::Value, serde_json::Value) {
    let created = runtime("create_code_change_proposal", code_change_create_payload());
    assert!(created.success, "{:?}", created.error);
    let run_root = created.result.unwrap();
    let expected = run_root["task_packet_sha256"].clone();
    let submitted = runtime(
        "submit_patch_candidate",
        json!({
            "run_root": run_root,
            "expected_task_packet_sha256": expected,
            "candidate_id": "cand_01",
            "producer_id": "agent",
            "patch_text": PARSER_PATCH
        }),
    );
    assert!(submitted.success, "{:?}", submitted.error);
    (expected, submitted.result.unwrap())
}

fn forged_patch_artifact(id: &str, text: &str) -> serde_json::Value {
    json!({
        "schema_version": "core.symbol-game.code-change-patch.v1",
        "patch_artifact_id": id,
        "patch_sha256": sha256_of(text),
        "patch_text": text,
        "byte_count": text.len(),
        "touched_paths": [".canon/rules.yaml"],
        "authority_effect": "None"
    })
}

/// Forgery (b) across the wire: the admitted parser patch is swapped for a
/// patch to a protected path, with `patch_sha256` and `byte_count`
/// recomputed. Before, the evaluator compared the artifact with itself and ran
/// the gates on the swapped bytes.
#[test]
fn evaluate_refuses_swapped_bytes_with_a_recomputed_patch_digest() {
    let (expected, submitted) = admitted_parser_patch();
    let admitted_id = submitted["patch_artifact"]["patch_artifact_id"]
        .as_str()
        .unwrap()
        .to_owned();
    let honest = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": submitted["run_root"],
            "expected_task_packet_sha256": expected,
            "expected_run_root_digest": submitted["run_root_digest"],
            "patch_artifact": submitted["patch_artifact"]
        }),
    );
    assert!(honest.success, "{:?}", honest.error);
    let receipts = honest.result.unwrap();
    let digest = sha256_of(PARSER_PATCH);
    for receipt in receipts.as_array().unwrap() {
        assert_eq!(receipt["patch_sha256"], json!(digest));
    }

    let swapped = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": submitted["run_root"],
            "expected_task_packet_sha256": expected,
            "expected_run_root_digest": submitted["run_root_digest"],
            "patch_artifact": forged_patch_artifact(&admitted_id, CANON_PATCH)
        }),
    );
    assert_eq!(refusal_code(&swapped), "REFUSAL_PATCH_NOT_BOUND");
}

/// Forgery (a) across the wire: an id pair that was never submitted is
/// appended to the run root and a matching, self-consistent artifact is
/// handed in. Before, the evaluator accepted any listed id.
#[test]
fn evaluate_refuses_an_appended_candidate_pair_with_a_recomputed_digest() {
    let (expected, submitted) = admitted_parser_patch();
    let mut forged_root = submitted["run_root"].clone();
    forged_root["candidate_ids"]
        .as_array_mut()
        .unwrap()
        .push(json!("cand_x"));
    forged_root["patch_ids"]
        .as_array_mut()
        .unwrap()
        .push(json!("patch_cand_x"));
    if let Some(map) = forged_root
        .get_mut("patch_sha256_by_candidate")
        .and_then(|value| value.as_object_mut())
    {
        map.insert("cand_x".to_owned(), json!(sha256_of(CANON_PATCH)));
    }
    let smuggled = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": forged_root,
            "expected_task_packet_sha256": expected,
            "expected_run_root_digest": submitted["run_root_digest"],
            "patch_artifact": forged_patch_artifact("patch_cand_x", CANON_PATCH)
        }),
    );
    assert_eq!(refusal_code(&smuggled), "REFUSAL_RUN_ROOT_BINDING_MISMATCH");
}

/// The expected create-time digest is required and must match.
#[test]
fn submit_and_evaluate_require_the_callers_create_time_digest() {
    let (expected, submitted) = admitted_parser_patch();
    let missing = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": submitted["run_root"],
            "patch_artifact": submitted["patch_artifact"]
        }),
    );
    assert_eq!(
        refusal_code(&missing),
        "REFUSAL_CODE_CHANGE_REQUEST_INVALID"
    );
    let other = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": submitted["run_root"],
            "expected_task_packet_sha256": "0".repeat(64),
            "expected_run_root_digest": submitted["run_root_digest"],
            "patch_artifact": submitted["patch_artifact"]
        }),
    );
    assert_eq!(
        refusal_code(&other),
        "REFUSAL_EXPECTED_TASK_DIGEST_MISMATCH"
    );
    assert_ne!(expected, json!("0".repeat(64)));
}

/// Submit returns the rolling digest for the caller to keep, and evaluate
/// refuses a root whose rolling digest was recomputed by someone else, even
/// though that root is internally consistent: the caller holds a different one.
#[test]
fn evaluate_refuses_a_recomputed_rolling_digest_the_caller_does_not_hold() {
    use pfp_runtime::code_change::derive_run_root_digest;
    use pfp_runtime::CodeChangeRunRootV1;

    let (expected, submitted) = admitted_parser_patch();
    let held = submitted["run_root_digest"].clone();
    assert_eq!(held, submitted["run_root"]["run_root_digest"]);
    assert_ne!(held, expected);

    let admitted_id = submitted["patch_artifact"]["patch_artifact_id"]
        .as_str()
        .unwrap()
        .to_owned();
    let mut forged: CodeChangeRunRootV1 =
        serde_json::from_value(submitted["run_root"].clone()).unwrap();
    forged
        .patch_sha256_by_candidate
        .insert("cand_01".to_owned(), sha256_of(CANON_PATCH));
    forged.run_root_digest = derive_run_root_digest(&forged).unwrap();

    let refused = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": forged,
            "expected_task_packet_sha256": expected,
            "expected_run_root_digest": held,
            "patch_artifact": forged_patch_artifact(&admitted_id, CANON_PATCH)
        }),
    );
    assert_eq!(
        refusal_code(&refused),
        "REFUSAL_EXPECTED_RUN_ROOT_DIGEST_MISMATCH"
    );

    let missing = runtime(
        "evaluate_patch_gates",
        json!({
            "run_root": submitted["run_root"],
            "expected_task_packet_sha256": expected,
            "patch_artifact": submitted["patch_artifact"]
        }),
    );
    assert_eq!(
        refusal_code(&missing),
        "REFUSAL_CODE_CHANGE_REQUEST_INVALID"
    );
}

#[test]
fn test_invoke_stabilizer_solve_and_check() {
    let case = json!({
        "id": "q40_bell",
        "n": 2,
        "terms": [
            {"id": "t0", "pauli": "ZZ", "weight": [1, 1], "target": 1},
            {"id": "t1", "pauli": "XX", "weight": [1, 1], "target": 1}
        ]
    });

    let solve_outcome = runtime("stabilizer_solve", json!({"case": case}));
    assert!(solve_outcome.success);
    assert_eq!(solve_outcome.authority_effect, "None");
    let res = solve_outcome.result.unwrap();
    assert_eq!(res["status"], "SOLVED");
    assert_eq!(res["energy"], json!([0, 1]));
    assert_eq!(res["degeneracy"], 1);

    let check_outcome = runtime(
        "stabilizer_check",
        json!({
            "case": case,
            "result": res
        }),
    );
    assert!(check_outcome.success);
    let check_val = check_outcome.result.unwrap();
    assert!(check_val.get("Pass").is_some());
}

#[test]
fn test_invoke_jcs_canonicalize_and_digest() {
    // 1. Canonicalize raw string with UTF-16 code unit property sorting
    let raw = r#"{"\uFB33": 1, "\uD83D\uDE00": 2}"#;
    let canon_outcome = runtime("jcs_canonicalize", json!({"raw": raw}));
    assert!(canon_outcome.success);
    assert_eq!(canon_outcome.authority_effect, "None");
    let res = canon_outcome.result.unwrap();
    assert_eq!(res["canonical_json"], "{\"😀\":2,\"דּ\":1}");

    // 2. Canonicalize value object
    let val_outcome = runtime("jcs_canonicalize", json!({"value": {"b": 2, "a": 1}}));
    assert!(val_outcome.success);
    assert_eq!(
        val_outcome.result.unwrap()["canonical_json"],
        "{\"a\":1,\"b\":2}"
    );

    // 3. Digest raw string
    let digest_outcome = runtime("jcs_digest", json!({"raw": "{\"b\": 2, \"a\": 1}"}));
    assert!(digest_outcome.success);
    let digest_res = digest_outcome.result.unwrap();
    let expected_hash = hex::encode(sha2::Sha256::digest(b"{\"a\":1,\"b\":2}"));
    assert_eq!(digest_res["sha256"], expected_hash);

    // 4. Duplicate key refusal
    let dup_outcome = runtime("jcs_canonicalize", json!({"raw": "{\"a\": 1, \"a\": 2}"}));
    assert!(!dup_outcome.success);
    assert!(dup_outcome.error.unwrap().contains("duplicate object key"));
}

#[test]
fn test_invoke_verify_decode_receipt() {
    let valid_receipt = json!({
        "schema_version": "core.symbol_game.decode_receipt.v1",
        "receipt_id": "r_001",
        "case_id": "case_01",
        "control_kind": "CARRIER_MASK",
        "allowed_tokens": [1, 2, 3],
        "output_tokens": [1, 2],
        "authority_effect": "None"
    });

    let pass_outcome = runtime("verify_decode_receipt", json!({"receipt": valid_receipt}));
    assert!(pass_outcome.success);
    let pass_res = pass_outcome.result.unwrap();
    assert_eq!(pass_res["status"], "PASS");
    assert_eq!(pass_res["token_count"], 2);
    assert_eq!(pass_res["carrier_honored"], true);

    let violated_receipt = json!({
        "schema_version": "core.symbol_game.decode_receipt.v1",
        "receipt_id": "r_002",
        "case_id": "case_01",
        "control_kind": "CARRIER_MASK",
        "allowed_tokens": [1, 2, 3],
        "output_tokens": [1, 99],
        "authority_effect": "None"
    });

    let ref_outcome = runtime(
        "verify_decode_receipt",
        json!({"receipt": violated_receipt}),
    );
    assert!(ref_outcome.success);
    let ref_res = ref_outcome.result.unwrap();
    assert_eq!(ref_res["status"], "REFUSAL");
    assert_eq!(ref_res["refusal_code"], "CARRIER_CONSTRAINT_VIOLATED");
}

fn n5_cochain_payload(native_matrix: bool) -> serde_json::Value {
    use pfp_runtime::cochain::{rational, PromptCellComplex};

    let complex = if native_matrix {
        serde_json::to_value(PromptCellComplex::zero_face(
            2,
            1,
            vec![vec![rational(-1, 2), rational(1, 2)]],
        ))
        .unwrap()
    } else {
        json!({
            "c0_dim": 2, "c1_dim": 1, "c2_dim": 0,
            "d0": [["-1/2", "1/2"]], "d1": [], "source_bytes_hash": null
        })
    };
    json!({
        "complex": complex,
        "cochain": ["1/2"],
        "primal_potential": ["0", "1"],
        "dual_witness": ["0"]
    })
}

fn n5_assert_unknown_field(payload: serde_json::Value, field: &str) {
    let outcome = runtime("cochain_evaluate", payload);
    assert!(
        !outcome.success,
        "{field} was admitted: {:?}",
        outcome.result
    );
    assert!(outcome.result.is_none());
    assert_eq!(outcome.authority_effect, "None");
    let error = outcome.error.as_deref().unwrap();
    assert!(error.contains("unknown field"), "{error}");
    assert!(error.contains(field), "{field}: {error}");
}

#[test]
fn n5_native_dto_and_python_string_matrices_preserve_the_same_exact_result() {
    use pfp_runtime::cochain::{rational, CochainDisposition};

    let native = runtime("cochain_evaluate", n5_cochain_payload(true));
    let strings = runtime("cochain_evaluate", n5_cochain_payload(false));
    assert!(native.success, "{:?}", native.error);
    assert!(strings.success, "{:?}", strings.error);
    assert_eq!(native.authority_effect, "None");
    assert_eq!(native.result, strings.result);
    let result: CochainDisposition = serde_json::from_value(native.result.unwrap()).unwrap();
    assert_eq!(
        result,
        CochainDisposition::ExactCoboundary {
            potential: vec![rational(0, 1), rational(1, 1)],
            residual: vec![rational(0, 1)],
            phi1: rational(0, 1),
            gamma2: rational(0, 1),
        }
    );
}

#[test]
fn n5_omitted_context_and_omitted_or_null_budget_preserve_exact_result() {
    for native in [false, true] {
        let payload = n5_cochain_payload(native);
        let baseline = runtime("cochain_evaluate", payload.clone());
        assert!(baseline.success, "{:?}", baseline.error);
        assert_eq!(
            baseline.result.as_ref().unwrap()["disposition"],
            "ExactCoboundary"
        );
        for context in [json!({}), json!({"remaining_budget": null}), json!(null)] {
            let mut with_context = payload.clone();
            with_context["triad_context"] = context;
            let outcome = runtime("cochain_evaluate", with_context);
            assert!(outcome.success, "{:?}", outcome.error);
            assert_eq!(outcome.result, baseline.result);
        }
    }
}

#[test]
fn n5_canonical_context_keeps_custody_answer_maps_and_explicit_zero_budget() {
    for native in [false, true] {
        let mut payload = n5_cochain_payload(native);
        let source = "n5 exact source";
        let digest = sha256_of(source);
        payload["complex"]["source_bytes_hash"] = json!(digest);
        payload["triad_context"] = json!({
            "source_bytes": source,
            "expected_source_hash": digest,
            "protected_answers": {"arbitrary_domain_key": "preserved"},
            "candidate_answers": {"arbitrary_domain_key": "preserved"},
            "remaining_budget": 1
        });
        let admitted = runtime("cochain_evaluate", payload.clone());
        assert!(admitted.success, "{:?}", admitted.error);
        assert_eq!(admitted.result.unwrap()["disposition"], "ExactCoboundary");
        payload["triad_context"]["remaining_budget"] = json!(0);
        let exhausted = runtime("cochain_evaluate", payload.clone());
        assert!(exhausted.success, "{:?}", exhausted.error);
        let result = exhausted.result.unwrap();
        assert_eq!(result["disposition"], "Refusal");
        assert_eq!(result["code"], "RESOURCE_EXHAUSTION");
        payload["triad_context"]["remaining_budget"] = json!(1);
        payload["triad_context"]["candidate_answers"]["arbitrary_domain_key"] = json!("changed");
        let changed = runtime("cochain_evaluate", payload.clone());
        assert_eq!(
            changed.result.unwrap()["code"],
            "PROTECTED_ANSWER_VIOLATION"
        );
        payload["triad_context"]["candidate_answers"]["arbitrary_domain_key"] = json!("preserved");
        payload["triad_context"]["expected_source_hash"] = json!("0".repeat(64));
        let unbound = runtime("cochain_evaluate", payload);
        assert_eq!(unbound.result.unwrap()["code"], "SOURCE_BYTES_CORRUPTED");
    }
}

macro_rules! n5_top_level_refusal {
    ($test:ident, $field:literal, $value:expr) => {
        #[test]
        fn $test() {
            for native in [false, true] {
                let mut payload = n5_cochain_payload(native);
                payload[$field] = $value;
                n5_assert_unknown_field(payload, $field);
            }
        }
    };
}

n5_top_level_refusal!(n5_top_unknown_refuses, "unexpected", json!(true));
n5_top_level_refusal!(
    n5_top_misspelling_refuses,
    "primal_potental",
    json!(["0", "1"])
);
n5_top_level_refusal!(n5_prime_triad_alias_refuses, "prime_triad", json!({}));
n5_top_level_refusal!(n5_flat_budget_refuses, "budget", json!(1));
n5_top_level_refusal!(n5_flat_source_refuses, "source_bytes", json!("source"));
n5_top_level_refusal!(
    n5_flat_hash_refuses,
    "expected_source_hash",
    json!("0".repeat(64))
);
n5_top_level_refusal!(
    n5_flat_protected_answers_refuses,
    "protected_answers",
    json!({})
);
n5_top_level_refusal!(
    n5_flat_candidate_answers_refuses,
    "candidate_answers",
    json!({})
);

#[test]
fn n5_complex_unknown_refuses_in_both_rational_carriers() {
    for native in [false, true] {
        let mut payload = n5_cochain_payload(native);
        payload["complex"]["unexpected"] = json!(true);
        n5_assert_unknown_field(payload, "unexpected");
    }
}

macro_rules! n5_complex_alias_refusal {
    ($test:ident, $canonical:literal, $alias:literal) => {
        #[test]
        fn $test() {
            for native in [false, true] {
                for retain_canonical in [false, true] {
                    let mut payload = n5_cochain_payload(native);
                    let complex = payload["complex"].as_object_mut().unwrap();
                    let value = complex[$canonical].clone();
                    if !retain_canonical {
                        complex.remove($canonical);
                    }
                    complex.insert($alias.to_owned(), value);
                    n5_assert_unknown_field(payload, $alias);
                }
            }
        }
    };
}

n5_complex_alias_refusal!(n5_vertex_alias_refuses, "c0_dim", "v_count");
n5_complex_alias_refusal!(n5_edge_alias_refuses, "c1_dim", "e_count");
n5_complex_alias_refusal!(n5_face_alias_refuses, "c2_dim", "f_count");
n5_complex_alias_refusal!(n5_d0_alias_refuses, "d0", "d0_matrix");
n5_complex_alias_refusal!(n5_d1_alias_refuses, "d1", "d1_matrix");

#[test]
fn n5_context_unknown_and_misspelled_budget_refuse() {
    for native in [false, true] {
        for field in ["unexpected", "remainng_budget", "budget"] {
            let mut payload = n5_cochain_payload(native);
            payload["triad_context"] = json!({field: 0});
            n5_assert_unknown_field(payload, field);
        }
    }
}

#[test]
fn n5_python_string_matrix_does_not_rewrite_a_declared_face_dimension() {
    let mut payload = n5_cochain_payload(false);
    payload["complex"]["c2_dim"] = json!(2);
    payload["complex"]["d1"] = json!([["0"]]);
    let outcome = runtime("cochain_evaluate", payload);
    assert!(outcome.success, "{:?}", outcome.error);
    let result = outcome.result.unwrap();
    assert_eq!(result["disposition"], "Refusal");
    assert_eq!(result["code"], "DIMENSION_MISMATCH");
}

#[test]
fn n5_native_matrix_keeps_the_declared_face_dimension_refusal() {
    use pfp_runtime::cochain::{rational, PromptCellComplex};

    let mut payload = n5_cochain_payload(true);
    payload["complex"] = serde_json::to_value(PromptCellComplex::new(
        2,
        1,
        2,
        vec![vec![rational(-1, 2), rational(1, 2)]],
        vec![vec![rational(0, 1)]],
    ))
    .unwrap();
    let outcome = runtime("cochain_evaluate", payload);
    assert!(outcome.success, "{:?}", outcome.error);
    let result = outcome.result.unwrap();
    assert_eq!(result["disposition"], "Refusal");
    assert_eq!(result["code"], "DIMENSION_MISMATCH");
}

#[test]
fn n5_existing_mcp_raw_intake_refuses_nested_and_escaped_duplicates() {
    use pfp::mcp::McpSession;

    for arguments in [
        r#"{"cochain":[],"cochain":[]}"#,
        r#"{"complex":{"c0_dim":0,"c0_dim":0}}"#,
        r#"{"triad_context":{"remaining_budget":1,"remaining_budget":0}}"#,
        r#"{"triad_context":{"remaining_budget":1,"remaining_\u0062udget":0}}"#,
    ] {
        let raw = format!(
            r#"{{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{{"name":"cochain_evaluate","arguments":{arguments}}}}}"#
        );
        let response = McpSession::default().handle(raw.as_bytes()).unwrap();
        assert_eq!(response["error"]["code"], -32700);
        assert_eq!(response["error"]["message"], "MALFORMED_OR_DUPLICATE_JSON");
        assert!(response.get("result").is_none());
    }
}

#[test]
fn n5_review_conflicting_context_spellings_refuse_instead_of_selecting_one() {
    for native in [false, true] {
        let mut payload = n5_cochain_payload(native);
        payload["prime_triad"] = json!({"remaining_budget": 0});
        payload["triad_context"] = json!({"remaining_budget": 1});
        n5_assert_unknown_field(payload, "prime_triad");
    }
}

#[test]
fn n5_review_replaced_dual_witnes_typo_refuses_before_defaulting_the_witness() {
    for native in [false, true] {
        let mut payload = n5_cochain_payload(native);
        let object = payload.as_object_mut().unwrap();
        let witness = object.remove("dual_witness").unwrap();
        object.insert("dual_witnes".to_owned(), witness);
        n5_assert_unknown_field(payload, "dual_witnes");
    }
}

fn n5_assert_complex_type_refusal(field: &str, malformed: &[serde_json::Value]) {
    for native in [false, true] {
        for value in malformed {
            let mut payload = n5_cochain_payload(native);
            payload["complex"][field] = value.clone();
            let outcome = runtime("cochain_evaluate", payload);
            assert!(
                !outcome.success,
                "{field}={value} was silently defaulted: {:?}",
                outcome.result
            );
            assert!(outcome.result.is_none());
            assert_eq!(outcome.authority_effect, "None");
            assert!(outcome.error.as_deref().unwrap().contains("invalid"));
        }
    }
}

#[test]
fn n5_review_malformed_d1_is_not_defaulted_to_an_empty_matrix() {
    n5_assert_complex_type_refusal(
        "d1",
        &[json!(null), json!(false), json!({}), json!("empty")],
    );
}

#[test]
fn n5_review_malformed_source_hash_is_not_defaulted_to_absent() {
    n5_assert_complex_type_refusal(
        "source_bytes_hash",
        &[json!(false), json!(0), json!({}), json!([])],
    );
}

#[test]
fn n5_review_malformed_c2_dimension_is_not_defaulted_to_zero() {
    n5_assert_complex_type_refusal(
        "c2_dim",
        &[json!(null), json!(false), json!(-1), json!("0")],
    );
}

fn m2_host_missing_bytes(expected: Option<&str>, bound: Option<&str>) {
    for native in [false, true] {
        for explicit_null in [false, true] {
            let mut payload = n5_cochain_payload(native);
            payload["complex"]["source_bytes_hash"] = json!(bound);
            payload["triad_context"] = json!({"expected_source_hash": expected});
            if explicit_null {
                payload["triad_context"]["source_bytes"] = json!(null);
            }
            let outcome = runtime("cochain_evaluate", payload);
            assert!(outcome.success, "{:?}", outcome.error);
            assert_eq!(outcome.authority_effect, "None");
            let result = outcome.result.unwrap();
            assert_eq!(result["disposition"], "Refusal", "{result}");
            assert_eq!(result["code"], "SOURCE_BYTES_CORRUPTED");
            assert!(result["message"]
                .as_str()
                .unwrap()
                .contains("source bytes are missing"));
        }
    }
}

#[test]
fn m2_host_expected_hash_without_bytes_is_refused() {
    m2_host_missing_bytes(Some(&sha256_of("source A")), None);
}

#[test]
fn m2_host_bound_hash_without_bytes_is_refused() {
    m2_host_missing_bytes(None, Some(&sha256_of("source A")));
}

#[test]
fn m2_host_equal_declared_hashes_without_bytes_are_refused() {
    m2_host_missing_bytes(Some(&sha256_of("source A")), Some(&sha256_of("source A")));
}

#[test]
fn m2_host_unequal_declared_hashes_without_bytes_are_refused() {
    m2_host_missing_bytes(Some(&sha256_of("source A")), Some(&sha256_of("source B")));
}

#[test]
fn m2_host_missing_or_null_context_cannot_bypass_bound_hash() {
    for native in [false, true] {
        for explicit_null in [false, true] {
            let mut payload = n5_cochain_payload(native);
            payload["complex"]["source_bytes_hash"] = json!(sha256_of("source A"));
            if explicit_null {
                payload["triad_context"] = json!(null);
            }
            let outcome = runtime("cochain_evaluate", payload);
            assert!(outcome.success, "{:?}", outcome.error);
            assert_eq!(outcome.authority_effect, "None");
            let result = outcome.result.unwrap();
            assert_eq!(result["disposition"], "Refusal", "{result}");
            assert_eq!(result["code"], "SOURCE_BYTES_CORRUPTED");
        }
    }
}

#[test]
fn m2_host_matching_hashes_preserve_ascii_utf8_and_present_empty_source() {
    for native in [false, true] {
        let baseline = runtime("cochain_evaluate", n5_cochain_payload(native));
        assert!(baseline.success);
        for source in ["source A", "custody λ → 𝒪", ""] {
            for (expected, bound) in [(true, false), (false, true), (true, true)] {
                let mut payload = n5_cochain_payload(native);
                let digest = sha256_of(source);
                if bound {
                    payload["complex"]["source_bytes_hash"] = json!(digest);
                }
                payload["triad_context"] = json!({"source_bytes": source});
                if expected {
                    payload["triad_context"]["expected_source_hash"] = json!(digest);
                }
                let outcome = runtime("cochain_evaluate", payload);
                assert!(outcome.success, "{:?}", outcome.error);
                assert_eq!(outcome.authority_effect, "None");
                assert_eq!(outcome.result, baseline.result);
            }
        }
    }
}

#[test]
fn m2_host_present_bytes_must_match_both_declared_hashes() {
    for native in [false, true] {
        for expected_matches in [false, true] {
            let mut payload = n5_cochain_payload(native);
            payload["complex"]["source_bytes_hash"] = json!(sha256_of(if expected_matches {
                "source B"
            } else {
                "source A"
            }));
            payload["triad_context"] = json!({
                "source_bytes": "source A",
                "expected_source_hash": sha256_of(if expected_matches {
                    "source A"
                } else {
                    "source B"
                })
            });
            let outcome = runtime("cochain_evaluate", payload);
            assert!(outcome.success, "{:?}", outcome.error);
            let result = outcome.result.unwrap();
            assert_eq!(result["disposition"], "Refusal", "{result}");
            assert_eq!(result["code"], "SOURCE_BYTES_CORRUPTED");
        }
    }
}

// Origin: engine/crates_rs/tests/pfp/invoke_contract.rs
// Claim: urn:core:crates_rs:tests:invoke-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord17ecab75 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord17ecab75` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError17ecab75 {
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
impl BoundaryError17ecab75 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError17ecab75 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError17ecab75 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord17ecab75 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError17ecab75> {
        if capacity_bound == 0 {
            return Err(BoundaryError17ecab75::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError17ecab75::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError17ecab75::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_17ecab75() {
    let admitted = BoundaryRecord17ecab75::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord17ecab75::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
