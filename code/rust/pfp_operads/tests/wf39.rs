//! WF39, authority firewall gate: each guard of the vector, the order they are recorded in, and
//! what the host refuses before it replays anything.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf39-tests:v1

use pfp_operads::families::wf39::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn digest(value: &Value) -> String {
    sha(&value.to_string())
}

fn task() -> Value {
    json!({
        "statement": "Give a potential phi for the public cochain and a receipt from the registered verifier.",
        "nonce": "run-0042",
        "registered_verifiers": ["exact.cochain_residual.v1"],
        "edges": [[0, 1], [1, 2], [2, 0]],
        "c": [1, 1, -2],
    })
}

fn good() -> Value {
    json!({"edges": [[0, 1], [1, 2], [2, 0]], "c": [1, 1, -2], "phi": [0, 1, 2]})
}

fn bad() -> Value {
    json!({"edges": [[0, 1], [1, 2], [2, 0]], "c": [1, 1, -2], "phi": [0, 1, 3]})
}

fn replay_of_good() -> Value {
    json!({"residual": [0, 0, 0], "defect": 0})
}

fn replay_of_bad() -> Value {
    json!({"residual": [0, -1, 1], "defect": 2})
}

/// A receipt as an honest proposer writes it for `payload`, bound to `bound`.
fn receipt(bound: &Value, replay: &Value) -> Value {
    json!({
        "authority_effect": "None",
        "verifier_id": "exact.cochain_residual.v1",
        "payload_sha256": digest(bound),
        "replay_sha256": digest(replay),
        "claimed": replay,
        "nonce": "run-0042",
    })
}

fn reply(payload: &Value, receipt: &Value) -> Value {
    json!({"payload": payload, "receipt": receipt})
}

fn honest() -> Value {
    reply(&good(), &receipt(&good(), &replay_of_good()))
}

fn with(mut receipt_reply: Value, key: &str, value: Value) -> Value {
    receipt_reply["receipt"][key] = value;
    receipt_reply
}

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF39", "task": task, "replies": replies}).to_string()
}

fn run_task(task: &Value, reply: &Value) -> (bool, Value) {
    match judge(&request(task, &[Some(reply.clone())])) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn run(reply: &Value) -> (bool, Value) {
    run_task(&task(), reply)
}

fn outcomes(report: &Value) -> Vec<(&str, bool)> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| {
            (
                row["name"].as_str().expect("a name"),
                row["passed"].as_bool().expect("an outcome"),
            )
        })
        .collect()
}

fn malformed(reply: &Value) -> (String, Value) {
    let (passed, report) = run(reply);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    let reason = report["detail"]["reason"].as_str().expect("a reason");
    (reason.to_owned(), report)
}

fn bad_task(task: &Value) -> String {
    match judge(&request(task, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

const ALL: [&str; 8] = [
    "payload_bound_to_task",
    "authority_effect_none",
    "witness_verifier_registered",
    "witness_bound_to_payload",
    "replay_hash",
    "replay_match",
    "zero_defect",
    "fresh_nonce",
];

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF39");
    assert_eq!(FAMILY.name, "Authority firewall gate");
    assert_eq!(FAMILY.host_check, "authority_guard_vector");
}

#[test]
fn a_reply_that_passes_every_guard_is_certified() {
    let (passed, report) = run(&honest());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "ALL_GUARDS_PASS");
    assert_eq!(report["detail"], json!({"residual_evidence": []}));
    let held: Vec<(&str, bool)> = ALL.iter().map(|name| (*name, true)).collect();
    assert_eq!(outcomes(&report), held);
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    let verifier = sha(r#""exact.cochain_residual.v1""#);
    let replay = sha(r#"{"defect":0,"residual":[0,0,0]}"#);
    assert_eq!(
        digests,
        [
            digest(&good()),
            sha(r#"{"effect":"None","extra":[]}"#),
            verifier.clone(),
            verifier.clone(),
            verifier,
            replay.clone(),
            replay,
            sha(r#""run-0042""#),
        ]
    );
    assert_eq!(report["asked"][0]["stage"], "solve");
}

#[test]
fn a_payload_may_leave_out_the_public_cochain() {
    let payload = json!({"phi": [0, 1, 2]});
    let (passed, _) = run(&reply(&payload, &receipt(&good(), &replay_of_good())));
    assert!(
        passed,
        "the host binds the payload to the task's own cochain"
    );
    let (passed, report) = run(&reply(
        &json!({"phi": [0, 1, 2]}),
        &receipt(&payload, &replay_of_good()),
    ));
    assert!(!passed);
    assert_eq!(report["code"], "WITNESS_BOUND_TO_PAYLOAD");
}

#[test]
fn a_payload_that_names_another_cochain_is_not_bound_to_the_task() {
    let trivial = json!({"edges": [[0, 1]], "c": [0], "phi": [0, 0]});
    let (passed, report) = run(&reply(
        &trivial,
        &receipt(&trivial, &json!({"residual": [0], "defect": 0})),
    ));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "PAYLOAD_NOT_BOUND_TO_TASK");
    assert_eq!(
        report["detail"],
        json!({"residual_evidence": ["payload_bound_to_task"]})
    );
    assert_eq!(outcomes(&report), [("payload_bound_to_task", false)]);
    let mut other = good();
    other["c"] = json!([1, 1, -1]);
    let (_, report) = run(&reply(&other, &receipt(&other, &replay_of_good())));
    assert_eq!(report["code"], "PAYLOAD_NOT_BOUND_TO_TASK");
    let mut other = good();
    other["edges"] = json!([[0, 1], [1, 2], [0, 2]]);
    let (_, report) = run(&reply(&other, &receipt(&other, &replay_of_good())));
    assert_eq!(report["code"], "PAYLOAD_NOT_BOUND_TO_TASK");
}

#[test]
fn a_payload_with_a_field_of_its_own_is_not_bound_to_the_task() {
    let mut extended = good();
    extended["verdict"] = json!("HOST_CERTIFIED");
    let (_, report) = run(&reply(&extended, &receipt(&good(), &replay_of_good())));
    assert_eq!(report["code"], "PAYLOAD_NOT_BOUND_TO_TASK");
    let (_, report) = run(&reply(
        &json!({"phi": [0, 1, 2], "note": 1}),
        &receipt(&good(), &replay_of_good()),
    ));
    assert_eq!(report["code"], "PAYLOAD_NOT_BOUND_TO_TASK");
}

#[test]
fn a_receipt_that_claims_authority_is_an_escalation() {
    let escalated = with(honest(), "authority_effect", json!("Host"));
    let (passed, report) = run(&escalated);
    assert!(!passed);
    assert_eq!(report["code"], "AUTHORITY_ESCALATION");
    assert_eq!(
        report["detail"],
        json!({"escalating_fields": [], "residual_evidence": ["authority"]})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("payload_bound_to_task", true),
            ("authority_effect_none", false)
        ]
    );
    for effect in [json!(null), json!(false), json!("none"), json!(0)] {
        let (_, report) = run(&with(honest(), "authority_effect", effect.clone()));
        assert_eq!(report["code"], "AUTHORITY_ESCALATION", "{effect}");
    }
    let mut absent = honest();
    absent["receipt"]
        .as_object_mut()
        .expect("object")
        .remove("authority_effect");
    let (_, report) = run(&absent);
    assert_eq!(report["code"], "AUTHORITY_ESCALATION");
}

#[test]
fn a_receipt_with_fields_of_its_own_names_them_in_order() {
    let mut loud = honest();
    loud["receipt"]["verdict"] = json!("HOST_CERTIFIED");
    loud["receipt"]["alpha"] = json!(1);
    loud["receipt"]["zeta"] = json!(null);
    let (_, report) = run(&loud);
    assert_eq!(report["code"], "AUTHORITY_ESCALATION");
    assert_eq!(
        report["detail"]["escalating_fields"],
        json!(["alpha", "verdict", "zeta"])
    );
    let digest_seen = report["predicates"][1]["evidence_sha256"]
        .as_str()
        .expect("digest");
    assert_eq!(
        digest_seen,
        sha(r#"{"effect":"None","extra":["alpha","verdict","zeta"]}"#)
    );
}

#[test]
fn a_self_certifying_receipt_is_refused_for_the_field_it_adds() {
    let mut selfish = honest();
    selfish["receipt"]["verifier_id"] = json!("self");
    selfish["receipt"]["verdict"] = json!("HOST_CERTIFIED");
    let (_, report) = run(&selfish);
    assert_eq!(report["code"], "AUTHORITY_ESCALATION");
    assert_eq!(report["detail"]["escalating_fields"], json!(["verdict"]));
}

#[test]
fn a_verifier_the_task_does_not_register_is_not_replayed() {
    let selfish = with(honest(), "verifier_id", json!("self"));
    let (passed, report) = run(&selfish);
    assert!(!passed);
    assert_eq!(report["code"], "WITNESS_VERIFIER_REGISTERED");
    assert_eq!(
        outcomes(&report),
        [
            ("payload_bound_to_task", true),
            ("authority_effect_none", true),
            ("witness_verifier_registered", false),
            ("witness_bound_to_payload", true),
            ("replay_hash", false),
            ("replay_match", false),
            ("zero_defect", false),
            ("fresh_nonce", true),
        ]
    );
    assert_eq!(
        report["detail"],
        json!({
            "residual_evidence": ["witness_verifier_registered", "replay_hash", "replay_match", "zero_defect"],
            "failed": ["witness_verifier_registered", "replay_hash", "replay_match", "zero_defect"],
        })
    );
    assert_eq!(report["predicates"][4]["evidence_sha256"], sha(r#""self""#));
    assert_eq!(report["predicates"][5]["evidence_sha256"], sha("null"));
}

#[test]
fn a_verifier_the_task_leaves_off_its_list_is_not_replayed() {
    let mut unlisted = task();
    unlisted["registered_verifiers"] = json!(["something.else.v1", 7]);
    let (passed, report) = run_task(&unlisted, &honest());
    assert!(!passed);
    assert_eq!(report["code"], "WITNESS_VERIFIER_REGISTERED");
    let mut empty = task();
    empty["registered_verifiers"] = json!([]);
    let (_, report) = run_task(&empty, &honest());
    assert_eq!(report["code"], "WITNESS_VERIFIER_REGISTERED");
    let mut later = task();
    later["registered_verifiers"] = json!(["something.else.v1", "exact.cochain_residual.v1"]);
    let (passed, _) = run_task(&later, &honest());
    assert!(passed);
    for named in [json!(null), json!(7), json!(["exact.cochain_residual.v1"])] {
        let (_, report) = run(&with(honest(), "verifier_id", named.clone()));
        assert_eq!(report["code"], "WITNESS_VERIFIER_REGISTERED", "{named}");
    }
}

#[test]
fn a_witness_bound_to_another_payload_is_refused() {
    let swapped = reply(&bad(), &receipt(&good(), &replay_of_good()));
    let swapped = with(swapped, "replay_sha256", json!(digest(&replay_of_bad())));
    let (passed, report) = run(&swapped);
    assert!(!passed);
    assert_eq!(report["code"], "WITNESS_BOUND_TO_PAYLOAD");
    assert_eq!(
        outcomes(&report),
        [
            ("payload_bound_to_task", true),
            ("authority_effect_none", true),
            ("witness_verifier_registered", true),
            ("witness_bound_to_payload", false),
            ("replay_hash", true),
            ("replay_match", false),
            ("zero_defect", false),
            ("fresh_nonce", true),
        ]
    );
}

#[test]
fn the_digest_is_of_the_canonical_form_of_edges_c_and_phi() {
    let spaced = with(
        honest(),
        "payload_sha256",
        json!(sha(
            r#"{"edges": [[0, 1], [1, 2], [2, 0]], "c": [1, 1, -2], "phi": [0, 1, 2]}"#
        )),
    );
    let (_, report) = run(&spaced);
    assert_eq!(report["code"], "WITNESS_BOUND_TO_PAYLOAD");
    let ordered = with(
        honest(),
        "payload_sha256",
        json!(sha(
            r#"{"c":[1,1,-2],"edges":[[0,1],[1,2],[2,0]],"phi":[0,1,2]}"#
        )),
    );
    let (passed, _) = run(&ordered);
    assert!(passed);
    for wrong in [
        json!(null),
        json!(7),
        json!(digest(&good()).to_uppercase()),
        json!(""),
    ] {
        let (_, report) = run(&with(honest(), "payload_sha256", wrong.clone()));
        assert_eq!(report["code"], "WITNESS_BOUND_TO_PAYLOAD", "{wrong}");
    }
}

#[test]
fn a_truthful_receipt_for_a_nonzero_defect_is_refused_for_its_defect() {
    let truthful = reply(&bad(), &receipt(&bad(), &replay_of_bad()));
    let (passed, report) = run(&truthful);
    assert!(!passed);
    assert_eq!(report["code"], "ZERO_DEFECT");
    assert_eq!(report["detail"]["failed"], json!(["zero_defect"]));
    assert_eq!(
        report["detail"]["residual_evidence"],
        json!(["zero_defect"])
    );
    let held: Vec<(&str, bool)> = ALL
        .iter()
        .map(|name| (*name, *name != "zero_defect"))
        .collect();
    assert_eq!(outcomes(&report), held);
    assert_eq!(
        report["predicates"][6]["evidence_sha256"],
        sha(r#"{"defect":2,"residual":[0,-1,1]}"#)
    );
}

#[test]
fn a_claim_that_is_not_the_replay_is_refused() {
    let lying = reply(&bad(), &receipt(&bad(), &replay_of_bad()));
    let lying = with(lying, "claimed", replay_of_good());
    let (_, report) = run(&lying);
    assert_eq!(report["code"], "REPLAY_MATCH");
    assert_eq!(
        report["detail"]["failed"],
        json!(["replay_match", "zero_defect"])
    );
    for claimed in [
        json!({"residual": [0, 0, 0]}),
        json!({"residual": [0, 0, 0], "defect": 0, "note": 1}),
        json!({"residual": [0, 0, 0], "defect": "0"}),
        json!([0, 0, 0]),
        json!(null),
    ] {
        let (_, report) = run(&with(honest(), "claimed", claimed.clone()));
        assert_eq!(report["code"], "REPLAY_MATCH", "{claimed}");
    }
    let mut absent = honest();
    absent["receipt"]
        .as_object_mut()
        .expect("object")
        .remove("claimed");
    let (_, report) = run(&absent);
    assert_eq!(report["code"], "REPLAY_MATCH");
}

#[test]
fn a_replay_hash_that_is_not_the_replay_digest_is_refused() {
    for wrong in [json!(digest(&good())), json!(null), json!(0)] {
        let (_, report) = run(&with(honest(), "replay_sha256", wrong.clone()));
        assert_eq!(report["code"], "REPLAY_HASH", "{wrong}");
        assert_eq!(report["detail"]["failed"], json!(["replay_hash"]));
    }
}

#[test]
fn a_stale_nonce_is_refused() {
    for nonce in [
        json!("run-0041"),
        json!(null),
        json!(42),
        json!(["run-0042"]),
        json!(""),
    ] {
        let (passed, report) = run(&with(honest(), "nonce", nonce.clone()));
        assert!(!passed, "{nonce}");
        assert_eq!(report["code"], "FRESH_NONCE", "{nonce}");
        assert_eq!(report["detail"]["failed"], json!(["fresh_nonce"]));
    }
    let mut absent = honest();
    absent["receipt"]
        .as_object_mut()
        .expect("object")
        .remove("nonce");
    let (_, report) = run(&absent);
    assert_eq!(report["code"], "FRESH_NONCE");
    let (_, report) = run(&with(honest(), "nonce", json!("run-0041")));
    assert_eq!(
        report["predicates"][7]["evidence_sha256"],
        sha(r#""run-0041""#)
    );
}

#[test]
fn the_first_failed_guard_names_the_refusal_and_all_are_listed() {
    let mut shabby = honest();
    shabby["receipt"]["nonce"] = json!("old");
    shabby["receipt"]["replay_sha256"] = json!("0");
    shabby["receipt"]["claimed"] = json!({});
    let (_, report) = run(&shabby);
    assert_eq!(report["code"], "REPLAY_HASH");
    assert_eq!(
        report["detail"]["failed"],
        json!(["replay_hash", "replay_match", "fresh_nonce"])
    );
    assert_eq!(
        report["detail"]["residual_evidence"],
        report["detail"]["failed"]
    );
}

#[test]
fn the_witness_must_be_a_potential_of_exact_integers_one_to_a_vertex() {
    let cases = [
        (json!(null), "phi must be a list of exact integers"),
        (json!("0 1 2"), "phi must be a list of exact integers"),
        (json!([0, 1, 2.0]), "phi must be a list of exact integers"),
        (json!([0, 1, "2"]), "phi must be a list of exact integers"),
        (json!([0, 1, true]), "phi must be a list of exact integers"),
        (json!({"0": 0}), "phi must be a list of exact integers"),
        (json!([0, 1]), "phi needs one integer per vertex 0..n-1"),
        (
            json!([0, 1, 2, 3]),
            "phi needs one integer per vertex 0..n-1",
        ),
        (json!([]), "phi needs one integer per vertex 0..n-1"),
    ];
    for (phi, reason) in cases {
        let mut payload = good();
        payload["phi"] = phi.clone();
        let (found, report) = malformed(&reply(&payload, &receipt(&payload, &replay_of_good())));
        assert_eq!(found, reason, "{phi}");
        assert_eq!(
            report["predicates"].as_array().expect("rows").len(),
            4,
            "{phi}"
        );
    }
    let absent = json!({"edges": [[0, 1], [1, 2], [2, 0]], "c": [1, 1, -2]});
    let (found, _) = malformed(&reply(&absent, &receipt(&absent, &replay_of_good())));
    assert_eq!(found, "phi must be a list of exact integers");
}

#[test]
fn a_witness_that_is_not_read_is_no_error_when_the_verifier_is_not_replayed() {
    let mut payload = good();
    payload["phi"] = json!("junk");
    let selfish = with(
        reply(&payload, &receipt(&payload, &replay_of_good())),
        "verifier_id",
        json!("self"),
    );
    let (passed, report) = run(&selfish);
    assert!(!passed);
    assert_eq!(report["code"], "WITNESS_VERIFIER_REGISTERED");
}

#[test]
fn the_potential_is_taken_up_to_the_graph_only() {
    let mut payload = good();
    payload["phi"] = json!([5, 6, 7]);
    let replay = json!({"residual": [0, 0, 0], "defect": 0});
    let (passed, _) = run(&reply(&payload, &receipt(&payload, &replay)));
    assert!(passed, "a shifted potential has the same coboundary");
    payload["phi"] = json!([0, 1, 3]);
    let (_, report) = run(&reply(&payload, &receipt(&payload, &replay_of_bad())));
    assert_eq!(report["code"], "ZERO_DEFECT");
}

#[test]
fn the_replay_sums_the_sizes_of_the_residual() {
    let mut payload = good();
    payload["phi"] = json!([10, 0, -3]);
    let replay = json!({"residual": [11, 4, -15], "defect": 30});
    let (passed, report) = run(&reply(&payload, &receipt(&payload, &replay)));
    assert!(!passed);
    assert_eq!(report["code"], "ZERO_DEFECT");
    assert_eq!(outcomes(&report)[5], ("replay_match", true));
    assert_eq!(
        report["predicates"][6]["evidence_sha256"],
        sha(r#"{"defect":30,"residual":[11,4,-15]}"#)
    );
}

#[test]
fn the_reply_must_carry_a_payload_and_a_receipt_that_are_objects() {
    let cases = [
        json!("payload and receipt"),
        json!([good(), receipt(&good(), &replay_of_good())]),
        json!({"payload": good()}),
        json!({"receipt": receipt(&good(), &replay_of_good())}),
        json!({"payload": [1], "receipt": receipt(&good(), &replay_of_good())}),
        json!({"payload": good(), "receipt": "signed"}),
        json!({"payload": null, "receipt": null}),
    ];
    for case in cases {
        let (reason, report) = malformed(&case);
        assert_eq!(reason, "payload and receipt objects required", "{case}");
        assert_eq!(report["predicates"], json!([]));
    }
}

#[test]
fn a_task_must_fix_a_nonce_a_verifier_list_and_a_public_cochain() {
    let edit = |key: &str, value: Value| {
        let mut changed = task();
        changed[key] = value;
        changed
    };
    let remove = |key: &str| {
        let mut changed = task();
        changed.as_object_mut().expect("object").remove(key);
        changed
    };
    let cases = [
        (remove("nonce"), "nonce and registered_verifiers required"),
        (
            edit("nonce", json!(7)),
            "nonce and registered_verifiers required",
        ),
        (
            remove("registered_verifiers"),
            "nonce and registered_verifiers required",
        ),
        (
            edit("registered_verifiers", json!("exact.cochain_residual.v1")),
            "nonce and registered_verifiers required",
        ),
        (
            edit("c", json!([1, 1])),
            "c must be one exact integer per edge",
        ),
        (
            edit("c", json!([1, 1, -2, 0])),
            "c must be one exact integer per edge",
        ),
        (
            edit("c", json!([1, 1, 0.5])),
            "c must be one exact integer per edge",
        ),
        (
            edit("c", json!("1 1 -2")),
            "c must be one exact integer per edge",
        ),
        (remove("c"), "c must be one exact integer per edge"),
        (
            edit("edges", json!([])),
            "edges must be a nonempty list of pairs of exact integers",
        ),
        (
            remove("edges"),
            "edges must be a nonempty list of pairs of exact integers",
        ),
        (
            edit("edges", json!([[0, 1], [1, 5], [5, 0]])),
            "vertices must be 0..n-1",
        ),
    ];
    for (bad, reason) in cases {
        assert_eq!(bad_task(&bad), reason, "{bad}");
    }
}

#[test]
fn a_missing_reply_stops_the_run() {
    let Outcome::Fail { result } = judge(&request(&task(), &[None])) else {
        panic!("expected a refused run");
    };
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}

#[test]
fn the_prompt_names_the_task_without_the_witness() {
    let Outcome::Pass { result } = next(&request(&task(), &[])) else {
        panic!("expected a turn");
    };
    let prompt = result["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt.starts_with("WF39 Authority firewall gate. Give a potential phi"));
    assert!(prompt.contains("run-0042"));
}

#[test]
fn a_second_reply_is_not_accepted() {
    match judge(&request(&task(), &[Some(honest()), Some(honest())])) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}
