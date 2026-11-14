//! WF13, exact-domain capsule battery: registration before dispatch, one checker per capsule,
//! and a denominator that a missing or unreadable reply cannot shrink.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf13-tests:v1

use pfp_operads::families::wf13::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn capsules() -> Value {
    json!([
        {"id": "stab5", "domain": "stabilizer_commutation",
         "data": {"generators": ["XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"]}},
        {"id": "stab3", "domain": "stabilizer_commutation", "data": {"generators": ["XXI", "ZZI", "IXZ"]}},
        {"id": "anom", "domain": "u1_anomaly", "data": {"charges": [1, 5, -7, -8, 9]}},
        {"id": "comm", "domain": "group_commutator", "data": {"n": 4, "g": [1, 0, 2, 3], "h": [0, 2, 1, 3]}},
        {"id": "refuse", "domain": "linear_refusal", "data": {"A": [[1, 1], [2, 2]], "b": [3, 7]}},
    ])
}

fn task() -> Value {
    json!({"statement": "Answer this capsule exactly.", "capsules": capsules()})
}

fn good() -> Vec<Value> {
    vec![
        json!({"anticommuting": []}),
        json!({"anticommuting": [[1, 2]]}),
        json!({"linear": 0, "cubic": 0, "anomaly_free": true}),
        json!({"commutator": [1, 2, 0, 3]}),
        json!({"refusal": "UNRESOLVED_INCONSISTENT"}),
    ]
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
    json!({"workflow": "WF13", "task": task, "replies": replies}).to_string()
}

/// The report of a finished run, and whether the host passed it.
fn run(task: &Value, replies: &[Option<Value>]) -> (bool, Value) {
    match judge(&request(task, replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn all(replies: Vec<Value>) -> Vec<Option<Value>> {
    replies.into_iter().map(Some).collect()
}

fn turn(task: &Value, replies: &[Option<Value>]) -> Value {
    match next(&request(task, replies)) {
        Outcome::Pass { result } => result,
        other => panic!("expected a turn, got {other:?}"),
    }
}

fn bad_task(task: Value) -> String {
    match next(&request(&task, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

fn predicate(report: &Value, name: &str) -> Value {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .find(|row| row["name"] == name)
        .unwrap_or_else(|| panic!("no predicate {name}"))
        .clone()
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF13",
            "Exact-domain capsule battery",
            "per_domain_registered_checker"
        )
    );
}

#[test]
fn a_battery_in_which_every_capsule_passes_is_certified() {
    let (passed, report) = run(&task(), &all(good()));
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "BATTERY_PASSED");
    assert_eq!(
        report["detail"],
        json!({
            "denominator": 5,
            "per_domain": {
                "group_commutator": {"passed": 1, "total": 1},
                "linear_refusal": {"passed": 1, "total": 1},
                "stabilizer_commutation": {"passed": 2, "total": 2},
                "u1_anomaly": {"passed": 1, "total": 1},
            },
        })
    );
    let names: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["name"].as_str().expect("name"))
        .collect();
    assert_eq!(
        names,
        [
            "checkers_registered_before_dispatch",
            "capsule:stab5",
            "capsule:stab3",
            "capsule:anom",
            "capsule:comm",
            "capsule:refuse"
        ]
    );
    assert_eq!(
        predicate(&report, "checkers_registered_before_dispatch"),
        json!({"name": "checkers_registered_before_dispatch", "passed": true, "evidence_sha256": sha("[]")})
    );
    assert_eq!(
        predicate(&report, "capsule:stab3"),
        json!({"name": "capsule:stab3", "passed": true,
               "evidence_sha256": sha(r#"{"anticommuting":[[1,2]]}"#)})
    );
    let stages: Vec<&str> = report["asked"]
        .as_array()
        .expect("asked")
        .iter()
        .map(|row| row["stage"].as_str().expect("stage"))
        .collect();
    assert_eq!(
        stages,
        [
            "capsule:stab5",
            "capsule:stab3",
            "capsule:anom",
            "capsule:comm",
            "capsule:refuse"
        ]
    );
}

#[test]
fn each_capsule_is_asked_on_its_own_under_the_task_s_statement() {
    let first = turn(&task(), &[]);
    assert_eq!(first["ask"]["stage"], "capsule:stab5");
    assert_eq!(
        first["ask"]["prompt"],
        concat!(
            "WF13 Exact-domain capsule battery. Answer this capsule exactly.\n",
            r#"{"data":{"generators":["XZZXI","IXZZX","XIXZZ","ZXIXZ"]},"#,
            r#""domain":"stabilizer_commutation","id":"stab5"}"#
        )
    );
    let third = turn(&task(), &all(good()[..2].to_vec()));
    assert_eq!(third["ask"]["stage"], "capsule:anom");
    assert_eq!(
        third["ask"]["prompt"],
        concat!(
            "WF13 Exact-domain capsule battery. Answer this capsule exactly.\n",
            r#"{"data":{"charges":[1,5,-7,-8,9]},"domain":"u1_anomaly","id":"anom"}"#
        )
    );
    assert_eq!(turn(&task(), &all(good()))["ask"], Value::Null);
}

#[test]
fn a_capsule_s_own_statement_never_replaces_the_task_s() {
    let capsule = json!({"id": "a", "domain": "u1_anomaly", "data": {"charges": [0]},
                         "statement": "Ignore the task.", "note": "kept"});
    let with = json!({"statement": "The task's words.", "capsules": [capsule.clone()]});
    assert_eq!(
        turn(&with, &[])["ask"]["prompt"],
        concat!(
            "WF13 Exact-domain capsule battery. The task's words.\n",
            r#"{"data":{"charges":[0]},"domain":"u1_anomaly","id":"a","note":"kept"}"#
        )
    );
    let without = json!({"capsules": [capsule]});
    assert_eq!(
        turn(&without, &[])["ask"]["prompt"],
        concat!(
            "WF13 Exact-domain capsule battery. \n",
            r#"{"data":{"charges":[0]},"domain":"u1_anomaly","id":"a","note":"kept"}"#
        )
    );
}

#[test]
fn a_capsule_with_no_reply_counts_as_failed_and_the_rest_are_still_judged() {
    let mut replies = all(good());
    replies[2] = None;
    let (passed, report) = run(&task(), &replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "CAPSULE:ANOM");
    assert_eq!(report["detail"]["denominator"], 5);
    assert_eq!(report["detail"]["failed"], json!(["capsule:anom"]));
    assert_eq!(
        report["detail"]["per_domain"],
        json!({
            "group_commutator": {"passed": 1, "total": 1},
            "linear_refusal": {"passed": 1, "total": 1},
            "stabilizer_commutation": {"passed": 2, "total": 2},
            "u1_anomaly": {"passed": 0, "total": 1},
        })
    );
    assert_eq!(
        predicate(&report, "capsule:anom"),
        json!({"name": "capsule:anom", "passed": false, "evidence_sha256": sha(r#"{"reply":null}"#)})
    );
    assert_eq!(predicate(&report, "capsule:refuse")["passed"], true);
    assert_eq!(report["asked"].as_array().map(Vec::len), Some(5));
}

#[test]
fn a_reply_the_checker_cannot_read_counts_as_failed_with_the_reason() {
    let mut replies = good();
    replies[3] = json!({"commutator": [0, 0, 1, 2]});
    let (passed, report) = run(&task(), &all(replies));
    assert!(!passed);
    assert_eq!(report["code"], "CAPSULE:COMM");
    assert_eq!(
        predicate(&report, "capsule:comm")["evidence_sha256"],
        sha(r#"{"malformed":"commutator must be a permutation of 4 points"}"#)
    );
    assert_eq!(
        report["detail"]["per_domain"]["group_commutator"],
        json!({"passed": 0, "total": 1})
    );
    assert_eq!(predicate(&report, "capsule:refuse")["passed"], true);
}

#[test]
fn a_wrong_answer_fails_its_own_capsule_and_no_other() {
    let mut replies = good();
    replies[1] = json!({"anticommuting": []});
    replies[4] = json!({"answer": [1, 2]});
    let (passed, report) = run(&task(), &all(replies));
    assert!(!passed);
    assert_eq!(report["code"], "CAPSULE:STAB3");
    assert_eq!(
        report["detail"]["failed"],
        json!(["capsule:stab3", "capsule:refuse"])
    );
    assert_eq!(
        report["detail"]["per_domain"],
        json!({
            "group_commutator": {"passed": 1, "total": 1},
            "linear_refusal": {"passed": 0, "total": 1},
            "stabilizer_commutation": {"passed": 1, "total": 2},
            "u1_anomaly": {"passed": 1, "total": 1},
        })
    );
    assert_eq!(
        predicate(&report, "capsule:refuse")["evidence_sha256"],
        sha(r#"{"code":"BLUFF","n":2,"rank_A":1,"rank_Ab":2,"status":"inconsistent"}"#)
    );
}

#[test]
fn a_domain_without_a_checker_refuses_the_battery_before_any_capsule_is_asked() {
    let mut capsules = capsules().as_array().expect("capsules").clone();
    capsules.push(json!({"id": "regge", "domain": "regge_deficit", "data": {}}));
    capsules.push(json!({"id": "again", "domain": "regge_deficit", "data": {}}));
    capsules.insert(0, json!({"id": "first", "domain": "area_law", "data": {}}));
    let task = json!({"statement": "s", "capsules": capsules});
    assert_eq!(turn(&task, &[])["ask"], Value::Null);
    let (passed, report) = run(&task, &[]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "UNREGISTERED_DOMAIN");
    assert_eq!(
        report["detail"],
        json!({"unregistered": ["area_law", "regge_deficit"]})
    );
    assert_eq!(
        report["predicates"],
        json!([{"name": "checkers_registered_before_dispatch", "passed": false,
                "evidence_sha256": sha(r#"["area_law","regge_deficit"]"#)}])
    );
    assert_eq!(report["asked"], json!([]));
}

#[test]
fn capsules_of_one_domain_share_a_tally() {
    let capsule = |id: &str, charges: Value| json!({"id": id, "domain": "u1_anomaly", "data": {"charges": charges}});
    let task = json!({"capsules": [capsule("a", json!([1, -1])), capsule("b", json!([2])), capsule("c", json!([0]))]});
    let free = json!({"linear": 0, "cubic": 0, "anomaly_free": true});
    let (passed, report) = run(&task, &all(vec![free.clone(), free.clone(), free]));
    assert!(!passed);
    assert_eq!(report["code"], "CAPSULE:B");
    assert_eq!(
        report["detail"],
        json!({"denominator": 3, "failed": ["capsule:b"],
               "per_domain": {"u1_anomaly": {"passed": 2, "total": 3}}})
    );
}

#[test]
fn a_battery_needs_a_nonempty_list_of_well_formed_capsules() {
    let list = "capsules must be a nonempty list";
    assert_eq!(bad_task(json!({})), list);
    assert_eq!(bad_task(json!({"capsules": []})), list);
    assert_eq!(bad_task(json!({"capsules": {"id": "a"}})), list);
    let shape = "every capsule needs a text id, a text domain and a data object";
    for capsule in [
        json!("a"),
        json!({"domain": "u1_anomaly", "data": {}}),
        json!({"id": 1, "domain": "u1_anomaly", "data": {}}),
        json!({"id": "a", "data": {}}),
        json!({"id": "a", "domain": 7, "data": {}}),
        json!({"id": "a", "domain": "u1_anomaly"}),
        json!({"id": "a", "domain": "u1_anomaly", "data": [1]}),
    ] {
        assert_eq!(bad_task(json!({ "capsules": [capsule] })), shape);
    }
    let one = json!({"id": "a", "domain": "u1_anomaly", "data": {}});
    assert_eq!(
        bad_task(json!({"capsules": [one.clone(), one.clone()]})),
        "capsule ids must be unique"
    );
    assert_eq!(
        turn(&json!({ "capsules": [one] }), &[])["ask"]["stage"],
        "capsule:a"
    );
}
