//! WF31, held-out tournament: disjoint splits, exact held-out scores, and a winner that must
//! beat the baseline.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf31-tests:v1

use pfp_operads::families::wf31::{FAMILY, MAX_PROPOSERS};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// Points of `y = 2 x^2 + 1`, ids from `first`.
fn points(first: i64, xs: &[i64]) -> Value {
    Value::Array(
        xs.iter()
            .zip(first..)
            .map(|(&x, id)| json!({"id": id, "x": x, "y": 2 * x * x + 1}))
            .collect(),
    )
}

fn task(proposers: u64) -> Value {
    json!({"statement": "Fit an exact polynomial to the training points.",
           "train": points(0, &[0, 1, 2, 3]), "proposers": proposers, "baseline_coefficients": [1]})
}

fn held_out() -> Value {
    json!({"held_out": points(10, &[5, 7, -4])})
}

fn request(task: Value, sealed: Value, replies: Value) -> String {
    json!({"workflow": "WF31", "task": task, "sealed": sealed, "replies": replies}).to_string()
}

fn coefficients(list: Value) -> Value {
    json!({"content": {"coefficients": list}})
}

fn run(task: Value, sealed: Value, replies: Value) -> (bool, Value) {
    match judge(&request(task, sealed, replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn turn(task: Value, sealed: Value, replies: Value) -> Value {
    match next(&request(task, sealed, replies)) {
        Outcome::Pass { result } => result,
        other => panic!("expected PASS, got {other:?}"),
    }
}

fn bad_task(task: Value, sealed: Value) -> String {
    match next(&request(task, sealed, json!([]))) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF31",
            "Multi-agent tournament with held-out cross-validation",
            "exact_held_out_referee"
        )
    );
    assert_eq!(MAX_PROPOSERS, 64);
}

#[test]
fn each_proposer_is_asked_in_turn_with_the_public_task_only() {
    let first = turn(task(3), held_out(), json!([]));
    assert_eq!(first["ask"]["stage"], "proposer:0");
    let prompt = first["ask"]["prompt"].as_str().expect("prompt");
    assert!(prompt.starts_with("WF31 Multi-agent tournament with held-out cross-validation. Fit an exact polynomial to the training points.\n{\"baseline_coefficients\":[1],\"proposers\":3,\"train\":[{\"id\":0,"));
    assert!(!prompt.contains("held_out"));
    let second = turn(task(3), held_out(), json!([coefficients(json!([1, 0, 2]))]));
    assert_eq!(second["ask"]["stage"], "proposer:1");
    assert_eq!(second["ask"]["prompt"], first["ask"]["prompt"]);
    assert_eq!(
        second["asked"],
        json!([{"stage": "proposer:0", "prompt_sha256": sha(prompt)}])
    );
    let third = turn(task(3), held_out(), json!([null, null]));
    assert_eq!(third["ask"]["stage"], "proposer:2");
    let done = turn(task(3), held_out(), json!([null, null, null]));
    assert_eq!(done["ask"], Value::Null);
    assert_eq!(done["asked"].as_array().map(Vec::len), Some(3));
}

#[test]
fn the_proposer_that_fits_the_held_out_points_wins_and_is_certified() {
    let replies = json!([
        coefficients(json!([1, 0, 2])),
        coefficients(json!([1, 2])),
        coefficients(json!(["1/2", 1])),
    ]);
    let (passed, report) = run(task(3), held_out(), replies);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "WINNER_SELECTED");
    assert_eq!(
        report["detail"],
        json!({"winner": "proposer:0", "baseline": 0, "held_out": 3,
               "scores": {"proposer:0": 3, "proposer:1": 0, "proposer:2": 0}})
    );
    assert_eq!(
        report["predicates"],
        json!([
            {"name": "splits_disjoint", "passed": true, "evidence_sha256": sha("[]")},
            {"name": "winner_beats_baseline", "passed": true, "evidence_sha256":
                sha(r#"{"baseline":0,"scores":{"proposer:0":3,"proposer:1":0,"proposer:2":0}}"#)},
        ])
    );
}

#[test]
fn a_winner_that_only_ties_the_baseline_is_refused() {
    let replies = json!([
        coefficients(json!([1, 2])),
        coefficients(json!([3])),
        coefficients(json!([1, 4])),
    ]);
    let (passed, report) = run(task(3), held_out(), replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "WINNER_BEATS_BASELINE");
    assert_eq!(report["detail"]["winner"], "proposer:0");
    assert_eq!(report["detail"]["failed"], json!(["winner_beats_baseline"]));
    assert_eq!(
        report["detail"]["scores"],
        json!({"proposer:0": 0, "proposer:1": 0, "proposer:2": 0})
    );
}

#[test]
fn a_partial_fit_scores_the_points_it_hits_and_the_baseline_is_scored_the_same_way() {
    let sealed = json!({"held_out": [
        {"id": 10, "x": 0, "y": 1}, {"id": 11, "x": 1, "y": 3},
        {"id": 12, "x": 2, "y": 9}, {"id": 13, "x": "1/2", "y": "3/2"},
    ]});
    let mut public = task(2);
    public["baseline_coefficients"] = json!([1, 2]);
    let replies = json!([coefficients(json!([1, 0, 2])), coefficients(json!([1]))]);
    let (passed, report) = run(public.clone(), sealed.clone(), replies);
    assert!(passed);
    assert_eq!(
        report["detail"]["scores"],
        json!({"proposer:0": 4, "proposer:1": 1})
    );
    assert_eq!(report["detail"]["baseline"], 2);
    assert_eq!(report["detail"]["held_out"], 4);
    public["baseline_coefficients"] = json!([1, 0, 2, 0]);
    let tied = json!([coefficients(json!([1, 0, 2])), null]);
    let (passed, report) = run(public.clone(), sealed.clone(), tied);
    assert!(!passed);
    assert_eq!(report["code"], "WINNER_BEATS_BASELINE");
    assert_eq!(report["detail"]["scores"], json!({"proposer:0": 4}));
    assert_eq!(report["detail"]["baseline"], 4);
    let behind = json!([coefficients(json!([1, 2])), coefficients(json!([1]))]);
    let (passed, report) = run(public, sealed, behind);
    assert!(!passed);
    assert_eq!(
        report["detail"]["scores"],
        json!({"proposer:0": 2, "proposer:1": 1})
    );
    assert_eq!(report["detail"]["winner"], "proposer:0");
}

#[test]
fn the_baseline_is_the_zero_polynomial_when_the_task_names_none() {
    let public = json!({"train": [{"id": 0}], "proposers": 1});
    let sealed = json!({"held_out": [{"id": 5, "x": 3, "y": 0}, {"id": 6, "x": 4, "y": 8}]});
    let (passed, report) = run(
        public.clone(),
        sealed.clone(),
        json!([coefficients(json!([0, 2]))]),
    );
    assert!(!passed);
    assert_eq!(report["detail"]["baseline"], 1);
    assert_eq!(report["detail"]["scores"], json!({"proposer:0": 1}));
    let (passed, report) = run(public, sealed, json!([coefficients(json!([-24, 8]))]));
    assert!(passed);
    assert_eq!(report["detail"]["scores"], json!({"proposer:0": 2}));
}

#[test]
fn a_shared_id_refuses_the_run_before_any_proposer_is_asked() {
    let leaky = json!({"held_out": [
        {"id": 10, "x": 5, "y": 51}, {"id": 3, "x": 0, "y": 1},
        {"id": 0, "x": 0, "y": 1}, {"id": 3, "x": 1, "y": 3},
    ]});
    assert_eq!(turn(task(3), leaky.clone(), json!([]))["ask"], Value::Null);
    let (passed, report) = run(task(3), leaky, json!([]));
    assert!(!passed);
    assert_eq!(report["code"], "SPLIT_OVERLAP");
    assert_eq!(report["detail"], json!({"overlap": [0, 3]}));
    assert_eq!(
        report["predicates"],
        json!([{"name": "splits_disjoint", "passed": false, "evidence_sha256": sha("[0,3]")}])
    );
    assert_eq!(report["asked"], json!([]));
}

#[test]
fn a_proposer_with_no_reply_has_no_score() {
    let replies = json!([null, coefficients(json!([1, 0, 2])), null]);
    let (passed, report) = run(task(3), held_out(), replies);
    assert!(passed);
    assert_eq!(report["detail"]["winner"], "proposer:1");
    assert_eq!(report["detail"]["scores"], json!({"proposer:1": 3}));
}

#[test]
fn a_run_where_no_proposer_replies_is_refused() {
    let (passed, report) = run(task(2), held_out(), json!([null, null]));
    assert!(!passed);
    assert_eq!(report["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(report["detail"], json!({}));
    assert_eq!(report["predicates"][0]["name"], "splits_disjoint");
    assert_eq!(report["predicates"].as_array().map(Vec::len), Some(1));
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["every_predicate_passed"], true);
}

#[test]
fn a_reply_that_cannot_be_read_scores_minus_one() {
    let replies = json!([
        {"content": {"coefficients": [1, 0.5]}},
        {"content": {}},
        {"content": [1, 0, 2]},
        {"content": {"coefficients": "12"}},
        {"content": null},
    ]);
    let (passed, report) = run(task(5), held_out(), replies);
    assert!(!passed);
    assert_eq!(report["code"], "WINNER_BEATS_BASELINE");
    assert_eq!(report["detail"]["winner"], "proposer:0");
    assert_eq!(
        report["detail"]["scores"],
        json!({"proposer:0": -1, "proposer:1": -1, "proposer:2": -1, "proposer:3": -1, "proposer:4": -1})
    );
    let mixed = json!([{"content": {}}, coefficients(json!([]))]);
    let (_, report) = run(task(2), held_out(), mixed);
    assert_eq!(report["detail"]["winner"], "proposer:1");
    assert_eq!(
        report["detail"]["scores"],
        json!({"proposer:0": -1, "proposer:1": 0})
    );
}

#[test]
fn a_tie_goes_to_the_name_that_sorts_first() {
    let mut replies = vec![json!(null); 11];
    replies[2] = coefficients(json!([1, 0, 2]));
    replies[10] = coefficients(json!([1, 0, 2]));
    replies[3] = coefficients(json!([1]));
    let (passed, report) = run(task(11), held_out(), Value::Array(replies));
    assert!(passed);
    assert_eq!(report["detail"]["winner"], "proposer:10");
    assert_eq!(
        report["detail"]["scores"],
        json!({"proposer:10": 3, "proposer:2": 3, "proposer:3": 0})
    );
    let later = json!([coefficients(json!([1])), coefficients(json!([1, 0, 2]))]);
    let (_, report) = run(task(2), held_out(), later);
    assert_eq!(report["detail"]["winner"], "proposer:1");
}

#[test]
fn a_run_with_no_held_out_points_certifies_nobody() {
    for sealed in [json!({}), json!({"held_out": []})] {
        let (passed, report) = run(task(1), sealed, json!([coefficients(json!([1, 0, 2]))]));
        assert!(!passed);
        assert_eq!(report["code"], "WINNER_BEATS_BASELINE");
        assert_eq!(report["detail"]["held_out"], 0);
        assert_eq!(report["detail"]["baseline"], 0);
    }
}

#[test]
fn the_training_share_is_a_nonempty_list_of_points_with_integer_ids() {
    let list = "train must be a nonempty list of points";
    assert_eq!(bad_task(json!({"proposers": 1}), json!({})), list);
    assert_eq!(
        bad_task(json!({"train": [], "proposers": 1}), json!({})),
        list
    );
    assert_eq!(
        bad_task(json!({"train": {"id": 0}, "proposers": 1}), json!({})),
        list
    );
    let ids = "every training point needs an exact integer id";
    assert_eq!(
        bad_task(json!({"train": [{"x": 0}], "proposers": 1}), json!({})),
        ids
    );
    assert_eq!(
        bad_task(
            json!({"train": [{"id": 0}, {"id": "a"}], "proposers": 1}),
            json!({})
        ),
        ids
    );
    assert_eq!(
        bad_task(json!({"train": [{"id": 1.0}], "proposers": 1}), json!({})),
        ids
    );
    assert_eq!(
        bad_task(json!({"train": [7], "proposers": 1}), json!({})),
        ids
    );
}

#[test]
fn the_number_of_proposers_is_an_exact_integer_from_one_to_sixty_four() {
    let count = "proposers must be an exact integer from 1 to 64";
    let with = |proposers: Value| json!({"train": [{"id": 0}], "proposers": proposers});
    assert_eq!(bad_task(json!({"train": [{"id": 0}]}), json!({})), count);
    assert_eq!(bad_task(with(json!(0)), json!({})), count);
    assert_eq!(bad_task(with(json!(65)), json!({})), count);
    assert_eq!(bad_task(with(json!(-1)), json!({})), count);
    assert_eq!(bad_task(with(json!("2")), json!({})), count);
    assert_eq!(bad_task(with(json!(2.0)), json!({})), count);
    assert_eq!(
        turn(with(json!(1)), json!({}), json!([]))["ask"]["stage"],
        "proposer:0"
    );
    let all = Value::Array(vec![json!(null); 63]);
    assert_eq!(
        turn(with(json!(64)), json!({}), all)["ask"]["stage"],
        "proposer:63"
    );
}

#[test]
fn the_baseline_and_the_held_out_share_are_read_strictly() {
    let public = |baseline: Value| json!({"train": [{"id": 0}], "proposers": 1, "baseline_coefficients": baseline});
    let baseline = "baseline_coefficients must be a list of exact rationals";
    assert_eq!(bad_task(public(json!(1)), json!({})), baseline);
    assert_eq!(bad_task(public(json!([0.5])), json!({})), baseline);
    assert_eq!(bad_task(public(json!(null)), json!({})), baseline);
    assert_eq!(
        bad_task(task(1), json!({"held_out": {"id": 1}})),
        "held_out must be a list of points"
    );
    let point = "every held-out point needs an integer id and exact rational x and y";
    for held in [
        json!([{"x": 1, "y": 3}]),
        json!([{"id": "a", "x": 1, "y": 3}]),
        json!([{"id": 9, "y": 3}]),
        json!([{"id": 9, "x": 1}]),
        json!([{"id": 9, "x": 1.5, "y": 3}]),
        json!([{"id": 9, "x": 1, "y": "3.0"}]),
        json!([{"id": 9, "x": 1, "y": 3}, 4]),
    ] {
        assert_eq!(bad_task(task(1), json!({ "held_out": held })), point);
    }
}
