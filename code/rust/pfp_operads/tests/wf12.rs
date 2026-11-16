//! WF12, mechanism-control arms: the control checks before anything is asked, the four arm
//! questions and the certificate, the paired totals, and the rank differences that explain them.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf12-tests:v1

use pfp_operads::families::wf12::{ARMS, ARM_PAIRS, FAMILY};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn task() -> Value {
    json!({
        "statement": "Sum each item. The arm note is the only thing that changes.",
        "items": [
            {"id": 0, "values": [1, 2]},
            {"id": 1, "values": [3, 4]},
            {"id": 2, "values": [5, 5]},
            {"id": 3, "values": [2, 7]},
        ],
        "mechanism_vector": [3, 4, 0],
        "null_control_vector": [0, 0, 0],
        "random_control_vector": [0, 0, 5],
    })
}

/// The answers of the four arms: right on 2, 4, 3 and 3 of the four items, the true sums being
/// 3, 7, 10 and 9.
fn arms() -> Vec<Value> {
    vec![
        json!({"answers": [3, 7, 0, 0]}),
        json!({"answers": [3, 7, 10, 9]}),
        json!({"answers": [3, 0, 0, 0]}),
        json!({"answers": [3, 7, 10, 0]}),
    ]
}

/// Ranks whose differences are the paired totals 2, 3, 1 and -1, shifted by 12.
fn ranks() -> Value {
    json!({"ranks": {"baseline": 12, "mechanism": 14, "null_control": 11, "random_control": 13}})
}

fn honest() -> Vec<Value> {
    let mut replies = arms();
    replies.push(ranks());
    replies
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
    json!({"workflow": "WF12", "task": task, "replies": replies}).to_string()
}

fn all(replies: Vec<Value>) -> Vec<Option<Value>> {
    replies.into_iter().map(Some).collect()
}

fn run_task(task: &Value, replies: Vec<Option<Value>>) -> (bool, Value) {
    match judge(&request(task, &replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn run(replies: Vec<Value>) -> (bool, Value) {
    run_task(&task(), all(replies))
}

fn turn(task: &Value, replies: Vec<Option<Value>>) -> Value {
    match next(&request(task, &replies)) {
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

/// The predicates of a report as name and outcome, in the order they were recorded.
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

/// The reason a run is refused because a reply could not be read.
fn malformed(replies: Vec<Value>) -> String {
    let (passed, report) = run(replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF12");
    assert_eq!(FAMILY.name, "Mechanism-control arms");
    assert_eq!(FAMILY.host_check, "integer_rank_difference_certificate");
    assert_eq!(
        ARMS,
        ["baseline", "mechanism", "null_control", "random_control"]
    );
    assert_eq!(ARM_PAIRS, [(0, 1), (2, 1), (3, 1), (0, 2)]);
}

#[test]
fn matched_controls_and_ranks_that_explain_every_total_are_certified() {
    let (passed, report) = run(honest());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "ARMS_COMPARED");
    assert_eq!(
        report["detail"],
        json!({
            "paired_totals": {
                "baseline->mechanism": 2,
                "null_control->mechanism": 3,
                "random_control->mechanism": 1,
                "baseline->null_control": -1,
            },
            "gauge_fixed_ranks": {
                "baseline": 0, "mechanism": 2, "null_control": -1, "random_control": 1,
            },
            "residual": [0, 0, 0, 0],
        })
    );
    assert_eq!(
        outcomes(&report),
        [
            ("null_control_is_zero", true),
            ("random_norm_matches_mechanism", true),
            ("random_differs_from_mechanism", true),
            ("rank_differences_match_paired_totals", true),
        ]
    );
    assert_eq!(report["every_predicate_passed"], true);
}

#[test]
fn the_evidence_of_each_predicate_is_what_it_looked_at() {
    let (_, report) = run(honest());
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    assert_eq!(
        digests,
        [
            sha("[0,0,0]"),
            sha(r#"{"mechanism":25,"random_control":25}"#),
            sha("[0,0,5]"),
            sha("[0,0,0,0]"),
        ]
    );
}

#[test]
fn the_arms_are_asked_in_order_then_the_certificate() {
    let stages = [
        "arm:baseline",
        "arm:mechanism",
        "arm:null_control",
        "arm:random_control",
    ];
    let mut replies: Vec<Option<Value>> = Vec::new();
    for (stage, arm) in stages.iter().zip(arms()) {
        let asked = turn(&task(), replies.clone());
        assert_eq!(asked["ask"]["stage"], *stage);
        replies.push(Some(arm));
    }
    let asked = turn(&task(), replies.clone());
    assert_eq!(asked["ask"]["stage"], "certificate");
    replies.push(Some(ranks()));
    assert_eq!(turn(&task(), replies)["ask"], Value::Null);
}

#[test]
fn each_prompt_is_the_default_prompt_with_its_own_line_added() {
    let start = turn(&task(), vec![]);
    let prompt = start["ask"]["prompt"].as_str().expect("a prompt");
    assert!(
        prompt.starts_with("WF12 Mechanism-control arms. Sum each item. The arm note is the only thing that changes.\n{"),
        "{prompt}"
    );
    assert!(prompt.ends_with("\nArm: baseline"), "{prompt}");
    assert_eq!(start["ask"]["prompt_sha256"], sha(prompt));
    let all_arms = turn(&task(), all(arms()));
    let last = all_arms["ask"]["prompt"].as_str().expect("a prompt");
    assert!(last.ends_with("\nReport integer arm ranks."), "{last}");
    assert!(
        last.starts_with(&prompt[..prompt.len() - "Arm: baseline".len()]),
        "{last}"
    );
    let second = turn(&task(), all(arms()[..1].to_vec()));
    let second = second["ask"]["prompt"].as_str().expect("a prompt");
    assert!(second.ends_with("\nArm: mechanism"), "{second}");
    assert!(
        second.starts_with(&prompt[..prompt.len() - "Arm: baseline".len()]),
        "{second}"
    );
}

#[test]
fn ranks_may_move_together_without_changing_the_verdict() {
    for shift in [0, 100, -7] {
        let moved = json!({"ranks": {
            "baseline": shift, "mechanism": shift + 2, "null_control": shift - 1,
            "random_control": shift + 1,
        }});
        let mut replies = arms();
        replies.push(moved);
        let (passed, report) = run(replies);
        assert!(passed, "shift {shift}");
        assert_eq!(
            report["detail"]["gauge_fixed_ranks"],
            json!({"baseline": 0, "mechanism": 2, "null_control": -1, "random_control": 1})
        );
    }
}

#[test]
fn an_inflated_mechanism_effect_leaves_a_residual_and_is_refused() {
    let inflated = json!({"ranks": {
        "baseline": 2, "mechanism": 6, "null_control": 1, "random_control": 3,
    }});
    let mut replies = arms();
    replies.push(inflated);
    let (passed, report) = run(replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "RANK_DIFFERENCES_MATCH_PAIRED_TOTALS");
    assert_eq!(
        report["detail"]["failed"],
        json!(["rank_differences_match_paired_totals"])
    );
    assert_eq!(report["detail"]["residual"], json!([-2, -2, -2, 0]));
    assert_eq!(report["detail"]["paired_totals"]["baseline->mechanism"], 2);
    assert_eq!(report["every_predicate_passed"], false);
}

#[test]
fn the_residual_is_the_total_less_the_difference_of_ranks_for_each_pair() {
    let skewed = json!({"ranks": {
        "baseline": 0, "mechanism": 5, "null_control": 20, "random_control": -4,
    }});
    let mut replies = arms();
    replies.push(skewed);
    let (_, report) = run(replies);
    assert_eq!(report["detail"]["residual"], json!([-3, 18, -8, -21]));
}

#[test]
fn a_null_control_that_is_not_zero_is_refused_before_anything_is_asked() {
    let mut bad = task();
    bad["null_control_vector"] = json!([0, 1, 0]);
    let (passed, report) = run_task(&bad, vec![]);
    assert!(!passed);
    assert_eq!(report["code"], "CONTROLS_UNMATCHED");
    assert_eq!(report["detail"]["failed"], json!(["null_control_is_zero"]));
    assert_eq!(
        report["detail"]["squared_norms"],
        json!({"mechanism": 25, "random_control": 25})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("null_control_is_zero", false),
            ("random_norm_matches_mechanism", true),
            ("random_differs_from_mechanism", true),
        ]
    );
    assert_eq!(report["asked"], json!([]));
}

#[test]
fn a_null_control_of_another_length_is_not_zero() {
    let mut bad = task();
    bad["null_control_vector"] = json!([0, 0]);
    let (_, report) = run_task(&bad, vec![]);
    assert_eq!(report["detail"]["failed"], json!(["null_control_is_zero"]));
}

#[test]
fn a_random_control_with_another_norm_is_refused() {
    let mut bad = task();
    bad["random_control_vector"] = json!([1, 1, 1]);
    let (passed, report) = run_task(&bad, vec![]);
    assert!(!passed);
    assert_eq!(report["code"], "CONTROLS_UNMATCHED");
    assert_eq!(
        report["detail"]["failed"],
        json!(["random_norm_matches_mechanism"])
    );
    assert_eq!(
        report["detail"]["squared_norms"],
        json!({"mechanism": 25, "random_control": 3})
    );
}

#[test]
fn a_random_control_of_another_length_is_refused_even_with_the_same_norm() {
    let mut bad = task();
    bad["random_control_vector"] = json!([0, 0, 5, 0]);
    let (_, report) = run_task(&bad, vec![]);
    assert_eq!(
        report["detail"]["failed"],
        json!(["random_norm_matches_mechanism"])
    );
}

#[test]
fn a_random_control_equal_to_the_mechanism_is_refused() {
    let mut bad = task();
    bad["random_control_vector"] = json!([3, 4, 0]);
    let (_, report) = run_task(&bad, vec![]);
    assert_eq!(
        report["detail"]["failed"],
        json!(["random_differs_from_mechanism"])
    );
}

#[test]
fn every_failed_control_is_named_in_the_order_recorded() {
    let bad = json!({
        "items": [{"values": [1]}],
        "mechanism_vector": [1, 2],
        "null_control_vector": [1, 0],
        "random_control_vector": [1, 2],
    });
    let (_, report) = run_task(&bad, vec![]);
    assert_eq!(
        report["detail"]["failed"],
        json!(["null_control_is_zero", "random_differs_from_mechanism"])
    );
}

#[test]
fn an_arm_with_no_reply_stops_the_run_naming_the_arm() {
    for (missing, arm) in ARMS.iter().enumerate() {
        let mut replies = all(arms()[..missing].to_vec());
        replies.push(None);
        let (passed, report) = run_task(&task(), replies);
        assert!(!passed, "arm {missing}");
        assert_eq!(report["code"], "NO_ADMISSIBLE_REPLY");
        assert_eq!(report["detail"], json!({"arm": arm}));
    }
}

#[test]
fn a_missing_certificate_stops_the_run_naming_it() {
    let mut replies = all(arms());
    replies.push(None);
    let (passed, report) = run_task(&task(), replies);
    assert!(!passed);
    assert_eq!(report["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(report["detail"], json!({"arm": "certificate"}));
}

#[test]
fn an_arm_that_answers_other_items_is_malformed() {
    let mut replies = arms();
    replies[1] = json!({"answers": [3, 7, 10]});
    replies.truncate(2);
    assert_eq!(malformed(replies), "every arm must answer the same items");
    let mut replies = arms();
    replies[1] = json!({"answers": [3, 7, 10, 9, 9]});
    replies.truncate(2);
    assert_eq!(malformed(replies), "every arm must answer the same items");
}

#[test]
fn an_arm_reply_must_be_an_object_with_exact_integer_answers() {
    let cases = [
        (json!([3, 7, 0, 0]), "arm:baseline reply must be an object"),
        (json!("3 7 0 0"), "arm:baseline reply must be an object"),
        (json!({}), "answers must be a list of exact integers"),
        (
            json!({"answers": "3"}),
            "answers must be a list of exact integers",
        ),
        (
            json!({"answers": [3, 7, 0, 0.5]}),
            "answers must be a list of exact integers",
        ),
        (
            json!({"answers": [3, 7, 0, "0"]}),
            "answers must be a list of exact integers",
        ),
        (
            json!({"answers": [3, 7, 0, true]}),
            "answers must be a list of exact integers",
        ),
        (
            json!({"answers": [3, 7, 0, null]}),
            "answers must be a list of exact integers",
        ),
    ];
    for (reply, reason) in cases {
        assert_eq!(malformed(vec![reply.clone()]), reason, "{reply}");
    }
}

#[test]
fn a_later_arm_is_read_as_strictly_as_the_first() {
    let mut replies = arms();
    replies[3] = json!({"answers": "none"});
    assert_eq!(
        malformed(replies),
        "answers must be a list of exact integers"
    );
    let mut replies = arms();
    replies[2] = json!(5);
    replies.truncate(3);
    assert_eq!(
        malformed(replies),
        "arm:null_control reply must be an object"
    );
}

#[test]
fn a_certificate_needs_one_integer_rank_per_arm_and_no_other() {
    let cases = [
        (json!([1, 2, 3, 4]), "certificate reply must be an object"),
        (json!({}), "one rank per arm"),
        (json!({"ranks": [1, 2, 3, 4]}), "one rank per arm"),
        (
            json!({"ranks": {"baseline": 0, "mechanism": 2, "null_control": -1}}),
            "one rank per arm",
        ),
        (
            json!({"ranks": {"baseline": 0, "mechanism": 2, "null_control": -1, "other": 1}}),
            "one rank per arm",
        ),
        (
            json!({"ranks": {"baseline": 0, "mechanism": 2, "null_control": -1, "random_control": 1, "extra": 0}}),
            "one rank per arm",
        ),
        (
            json!({"ranks": {"baseline": 0, "mechanism": "2", "null_control": -1, "random_control": 1}}),
            "rank must be an exact int",
        ),
        (
            json!({"ranks": {"baseline": 0, "mechanism": 2.0, "null_control": -1, "random_control": 1}}),
            "rank must be an exact int",
        ),
        (
            json!({"ranks": {"baseline": 0, "mechanism": 2, "null_control": null, "random_control": 1}}),
            "rank must be an exact int",
        ),
    ];
    for (certificate, reason) in cases {
        let mut replies = arms();
        replies.push(certificate.clone());
        assert_eq!(malformed(replies), reason, "{certificate}");
    }
}

#[test]
fn ranks_are_exact_integers_of_any_size() {
    let big = "123456789012345678901234567890";
    let mut replies = arms();
    replies.push(json!({"ranks": {
        "baseline": 7_777_777, "mechanism": 2, "null_control": 3, "random_control": 4,
    }}));
    let text = request(&task(), &all(replies)).replace("7777777", big);
    let Outcome::Fail { result: report } = judge(&text) else {
        panic!("expected a refused run");
    };
    assert_eq!(report["code"], "RANK_DIFFERENCES_MATCH_PAIRED_TOTALS");
    assert_eq!(
        report["detail"]["gauge_fixed_ranks"]["mechanism"],
        json!("-123456789012345678901234567888")
    );
    assert_eq!(
        report["detail"]["residual"][0],
        json!("123456789012345678901234567890")
    );
}

#[test]
fn a_task_must_be_readable_before_anything_is_asked() {
    let cases = [
        (
            {
                let mut t = task();
                t["items"] = json!([]);
                t
            },
            "items must be a nonempty list",
        ),
        (
            {
                let mut t = task();
                t["items"] = json!("a");
                t
            },
            "items must be a nonempty list",
        ),
        (
            {
                let mut t = task();
                t.as_object_mut().expect("object").remove("items");
                t
            },
            "items must be a nonempty list",
        ),
        (
            {
                let mut t = task();
                t["items"] = json!([{"id": 0}]);
                t
            },
            "every item needs values, a list of exact integers",
        ),
        (
            {
                let mut t = task();
                t["items"] = json!([{"values": [1, "2"]}]);
                t
            },
            "every item needs values, a list of exact integers",
        ),
        (
            {
                let mut t = task();
                t["items"] = json!([{"values": [1]}, 7]);
                t
            },
            "every item needs values, a list of exact integers",
        ),
        (
            {
                let mut t = task();
                t["mechanism_vector"] = json!([1.5]);
                t
            },
            "mechanism_vector must be a list of exact integers",
        ),
        (
            {
                let mut t = task();
                t["null_control_vector"] = json!("zero");
                t
            },
            "null_control_vector must be a list of exact integers",
        ),
        (
            {
                let mut t = task();
                t.as_object_mut()
                    .expect("object")
                    .remove("random_control_vector");
                t
            },
            "random_control_vector must be a list of exact integers",
        ),
    ];
    for (bad, reason) in cases {
        assert_eq!(bad_task(bad.clone()), reason, "{bad}");
    }
}

#[test]
fn an_item_with_no_values_has_the_sum_zero() {
    let mut empty = task();
    empty["items"] = json!([{"values": []}, {"values": [4]}]);
    let replies = vec![
        json!({"answers": [0, 4]}),
        json!({"answers": [0, 4]}),
        json!({"answers": [1, 4]}),
        json!({"answers": [0, 3]}),
        json!({"ranks": {"baseline": 0, "mechanism": 0, "null_control": 0, "random_control": 0}}),
    ];
    let (passed, report) = run_task(&empty, all(replies));
    assert!(!passed);
    assert_eq!(
        report["detail"]["paired_totals"],
        json!({
            "baseline->mechanism": 0,
            "null_control->mechanism": 1,
            "random_control->mechanism": 1,
            "baseline->null_control": -1,
        })
    );
}

#[test]
fn a_run_that_ends_early_cannot_be_sent_more_replies_than_it_used() {
    let mut bad = task();
    bad["null_control_vector"] = json!([1, 1, 1]);
    match judge(&request(&bad, &all(arms()))) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}
