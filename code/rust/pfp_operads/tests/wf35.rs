//! WF35, proposal-channel comparison: arms that share one grader and one budget, the replies
//! graded by the grader alone, and the claims a channel makes about its own answers.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf35-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::families::duality::pin;
use pfp_operads::families::wf35::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn canonical(value: &Value) -> String {
    Datum::parse(&value.to_string())
        .expect("a datum")
        .canonical()
}

fn feasible() -> Value {
    json!({"n": 3, "edges": [[0, 1, 2], [1, 2, -1], [0, 2, 3]]})
}

fn negative() -> Value {
    json!({"n": 3, "edges": [[0, 1, 1], [1, 2, -3], [2, 0, 1]]})
}

fn budget() -> Value {
    json!({"max_output_tokens": 256, "cap_microusd": 1})
}

fn arm(channel: &str) -> Value {
    json!({"channel": channel, "checker_pin": pin(), "budget": budget()})
}

fn task_of(items: &Value, arms: &Value) -> Value {
    json!({"statement": "Answer each weighted digraph item.", "items": items, "arms": arms})
}

fn task() -> Value {
    task_of(
        &json!([feasible(), negative()]),
        &json!([arm("prompt"), arm("grammar_mask")]),
    )
}

fn say(text: &str) -> Option<Value> {
    Some(json!({"text": text}))
}

fn claim(text: &str, accepted: Value) -> Option<Value> {
    Some(json!({"text": text, "accepted": accepted}))
}

fn good() -> Vec<Option<Value>> {
    vec![
        say("{\"potential\": [0, 2, 1]}"),
        say("{\"potential\": [0, 0, 0]}"),
        claim("{\"potential\": [0, 2, 1]}", json!(true)),
        claim("{\"negative_cycle\": [0, 1, 2]}", json!(true)),
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
    json!({"workflow": "WF35", "task": task, "sealed": {}, "replies": replies}).to_string()
}

fn run_on(task: &Value, replies: &[Option<Value>]) -> (bool, Value) {
    match judge(&request(task, replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn run(replies: &[Option<Value>]) -> (bool, Value) {
    run_on(&task(), replies)
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

fn bad_task(task: &Value) -> String {
    match judge(&request(task, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

fn asked(task: &Value, replies: &[Option<Value>]) -> Value {
    match next(&request(task, replies)) {
        Outcome::Pass { result } => result,
        other => panic!("expected a turn, got {other:?}"),
    }
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF35");
    assert_eq!(FAMILY.name, "Proposal-channel comparison");
    assert_eq!(FAMILY.host_check, "channel_blind_fixed_oracle");
}

#[test]
fn channels_on_one_grader_and_one_budget_are_compared() {
    let (passed, report) = run(&good());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CHANNELS_COMPARED");
    assert_eq!(
        report["detail"],
        json!({
            "accepts": {"grammar_mask": 2, "prompt": 1},
            "discordant": {"first_only": 0, "second_only": 1},
        })
    );
    assert_eq!(
        outcomes(&report),
        [
            ("arms_share_fixed_checker", true),
            ("arms_share_budget", true),
            ("accept_set_depends_only_on_bytes", true),
        ]
    );
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    let budgets = format!("[{0},{0}]", canonical(&budget()));
    assert_eq!(digests, [sha("[true,true]"), sha(&budgets), sha("[]")]);
    let stages: Vec<&str> = report["asked"]
        .as_array()
        .expect("asked")
        .iter()
        .map(|row| row["stage"].as_str().expect("a stage"))
        .collect();
    assert_eq!(
        stages,
        ["prompt:0", "prompt:1", "grammar_mask:0", "grammar_mask:1"]
    );
}

#[test]
fn each_arm_is_asked_each_item_in_turn_with_the_channel_in_the_question() {
    let mut replies = Vec::new();
    let mut seen = Vec::new();
    for _ in 0..4 {
        let turn = asked(&task(), &replies);
        let ask = &turn["ask"];
        seen.push((
            ask["stage"].as_str().expect("a stage").to_owned(),
            ask["prompt"].as_str().expect("a prompt").to_owned(),
        ));
        replies.push(say("{}"));
    }
    assert_eq!(asked(&task(), &replies)["ask"], Value::Null);
    let item = |graph: &Value, channel: &str| {
        let mut question = graph.clone();
        question["channel"] = json!(channel);
        format!(
            "WF35 Proposal-channel comparison. \n{}",
            canonical(&question)
        )
    };
    assert_eq!(
        seen,
        [
            ("prompt:0".to_owned(), item(&feasible(), "prompt")),
            ("prompt:1".to_owned(), item(&negative(), "prompt")),
            (
                "grammar_mask:0".to_owned(),
                item(&feasible(), "grammar_mask")
            ),
            (
                "grammar_mask:1".to_owned(),
                item(&negative(), "grammar_mask")
            ),
        ]
    );
}

#[test]
fn the_arms_channel_replaces_a_channel_an_item_names() {
    let marked = json!({"n": 2, "edges": [], "channel": "the item's own"});
    let task = task_of(&json!([marked]), &json!([arm("prompt"), arm("tree")]));
    let turn = asked(&task, &[]);
    let prompt = turn["ask"]["prompt"].as_str().expect("a prompt");
    assert!(
        prompt.ends_with("{\"channel\":\"prompt\",\"edges\":[],\"n\":2}"),
        "{prompt}"
    );
}

#[test]
fn arms_that_used_different_checkers_are_refused_before_anything_is_asked() {
    let mut other = task();
    other["arms"][1]["checker_pin"] = json!("f".repeat(64));
    let (passed, report) = run_on(&other, &[]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "ARMS_NOT_MATCHED");
    assert_eq!(report["detail"], json!({}));
    assert_eq!(
        outcomes(&report),
        [
            ("arms_share_fixed_checker", false),
            ("arms_share_budget", true)
        ]
    );
    assert_eq!(
        report["predicates"][0]["evidence_sha256"],
        sha("[true,false]")
    );
    assert_eq!(asked(&other, &[])["ask"], Value::Null);
}

#[test]
fn a_checker_pin_that_is_missing_or_not_the_graders_does_not_match() {
    for bad in [
        json!(null),
        json!(5),
        json!(pin().to_uppercase()),
        json!(format!("{} ", pin())),
    ] {
        let mut other = task();
        other["arms"][0]["checker_pin"] = bad.clone();
        let (_, report) = run_on(&other, &[]);
        assert_eq!(report["code"], "ARMS_NOT_MATCHED", "{bad}");
        assert_eq!(
            report["predicates"][0]["evidence_sha256"],
            sha("[false,true]"),
            "{bad}"
        );
    }
    let mut missing = task();
    missing["arms"][1]
        .as_object_mut()
        .expect("an arm")
        .remove("checker_pin");
    let (_, report) = run_on(&missing, &[]);
    assert_eq!(report["code"], "ARMS_NOT_MATCHED");
}

#[test]
fn arms_that_ran_under_different_budgets_are_refused_before_anything_is_asked() {
    let mut other = task();
    other["arms"][1]["budget"] = json!({"max_output_tokens": 4096, "cap_microusd": 1});
    let (passed, report) = run_on(&other, &[]);
    assert!(!passed);
    assert_eq!(report["code"], "ARMS_NOT_MATCHED");
    assert_eq!(
        outcomes(&report),
        [
            ("arms_share_fixed_checker", true),
            ("arms_share_budget", false)
        ]
    );
    let shown = format!(
        "[{},{}]",
        canonical(&budget()),
        canonical(&json!({"max_output_tokens": 4096, "cap_microusd": 1}))
    );
    assert_eq!(report["predicates"][1]["evidence_sha256"], sha(&shown));
    let mut both = other.clone();
    both["arms"][0]["checker_pin"] = json!("0");
    let (_, report) = run_on(&both, &[]);
    assert_eq!(report["code"], "ARMS_NOT_MATCHED");
    let held: Vec<bool> = outcomes(&report).iter().map(|row| row.1).collect();
    assert_eq!(held, [false, false]);
}

#[test]
fn a_budget_is_compared_by_its_canonical_form() {
    let mut reordered = task();
    reordered["arms"][1]["budget"] = json!({"cap_microusd": 1, "max_output_tokens": 256});
    let (passed, report) = run_on(&reordered, &good());
    assert!(passed, "{report}");
    let mut none = task();
    for place in 0..2 {
        none["arms"][place]
            .as_object_mut()
            .expect("an arm")
            .remove("budget");
    }
    let (passed, report) = run_on(&none, &good());
    assert!(passed, "{report}");
    assert_eq!(
        report["predicates"][1]["evidence_sha256"],
        sha("[null,null]")
    );
    let mut one = task();
    one["arms"][1]
        .as_object_mut()
        .expect("an arm")
        .remove("budget");
    let (_, report) = run_on(&one, &[]);
    assert_eq!(report["code"], "ARMS_NOT_MATCHED");
    let mut plain = task();
    plain["arms"][1]["budget"] = json!(null);
    let (_, report) = run_on(&plain, &[]);
    assert_eq!(report["code"], "ARMS_NOT_MATCHED");
}

#[test]
fn every_arm_is_held_to_the_same_budget_not_only_the_first_two() {
    let mut three = task();
    three["arms"] = json!([arm("a"), arm("b"), arm("c")]);
    three["arms"][2]["budget"] = json!({"cap_microusd": 2});
    let (_, report) = run_on(&three, &[]);
    assert_eq!(report["code"], "ARMS_NOT_MATCHED");
    let mut third = task();
    third["arms"] = json!([arm("a"), arm("b"), arm("c")]);
    third["arms"][2]["checker_pin"] = json!("0");
    let (_, report) = run_on(&third, &[]);
    assert_eq!(report["code"], "ARMS_NOT_MATCHED");
    assert_eq!(
        report["predicates"][0]["evidence_sha256"],
        sha("[true,true,false]")
    );
}

#[test]
fn a_channel_that_claims_an_acceptance_the_grader_does_not_give_is_refused() {
    let mut claimed = good();
    claimed[3] = claim("{\"negative_cycle\": [0, 2]}", json!(true));
    let (passed, report) = run(&claimed);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "ACCEPT_SET_DEPENDS_ONLY_ON_BYTES");
    assert_eq!(
        report["detail"],
        json!({
            "accepts": {"grammar_mask": 1, "prompt": 1},
            "discordant": {"first_only": 0, "second_only": 0},
            "failed": ["accept_set_depends_only_on_bytes"],
        })
    );
    assert_eq!(
        report["predicates"][2]["evidence_sha256"],
        sha("[\"grammar_mask:1\"]")
    );
}

#[test]
fn only_the_boolean_the_grader_gave_is_an_honest_claim() {
    let stands = "{\"potential\": [0, 2, 1]}";
    let fails = "{\"potential\": [0, 0, 0]}";
    let cases = [
        (stands, json!(true), true),
        (stands, json!(false), false),
        (stands, json!(1), false),
        (stands, json!("true"), false),
        (stands, json!(null), false),
        (stands, json!([true]), false),
        (fails, json!(false), true),
        (fails, json!(true), false),
        (fails, json!(0), false),
        (fails, json!(null), false),
    ];
    for (text, accepted, honest) in cases {
        let mut replies = good();
        replies[0] = claim(text, accepted.clone());
        let (_, report) = run(&replies);
        let held = outcomes(&report)[2].1;
        assert_eq!(held, honest, "{text} {accepted}");
    }
}

#[test]
fn every_claim_is_listed_with_its_channel_and_item() {
    let mut replies = good();
    replies[1] = claim("{\"potential\": [0, 0, 0]}", json!(true));
    replies[2] = claim("{\"potential\": [0, 0, 0]}", json!(true));
    replies[3] = claim("not json", json!(true));
    let (_, report) = run(&replies);
    assert_eq!(
        report["predicates"][2]["evidence_sha256"],
        sha("[\"prompt:1\",\"grammar_mask:0\",\"grammar_mask:1\"]")
    );
}

#[test]
fn a_parallel_edge_violation_a_mask_accepts_is_the_channels_claim_not_the_graders() {
    let parallel = json!({"n": 2, "edges": [[0, 1, -10], [0, 1, 5]]});
    let task = task_of(
        &json!([parallel]),
        &json!([arm("prompt"), arm("grammar_mask")]),
    );
    let replies = [
        say("{\"potential\": [0, 5]}"),
        claim("{\"potential\": [0, 5]}", json!(true)),
    ];
    let (passed, report) = run_on(&task, &replies);
    assert!(!passed);
    assert_eq!(report["code"], "ACCEPT_SET_DEPENDS_ONLY_ON_BYTES");
    assert_eq!(
        report["detail"]["accepts"],
        json!({"grammar_mask": 0, "prompt": 0})
    );
    assert_eq!(
        report["predicates"][2]["evidence_sha256"],
        sha("[\"grammar_mask:0\"]")
    );
}

#[test]
fn a_reply_with_no_text_or_no_reply_at_all_does_not_stand() {
    let task = task_of(
        &json!([feasible(), negative(), feasible()]),
        &json!([arm("prompt"), arm("grammar_mask")]),
    );
    let replies = [
        say("{\"potential\": [0, 2, 1]}"),
        None,
        Some(json!({"note": "{\"potential\": [0, 2, 1]}"})),
        say("{\"potential\": [0, 2, 1]}"),
        Some(json!("{\"potential\": [0, 2, 1]}")),
        Some(json!({"text": ["{\"potential\": [0, 2, 1]}"]})),
    ];
    let (passed, report) = run_on(&task, &replies);
    assert!(passed, "{report}");
    assert_eq!(
        report["detail"],
        json!({
            "accepts": {"grammar_mask": 1, "prompt": 1},
            "discordant": {"first_only": 0, "second_only": 0},
        })
    );
}

#[test]
fn a_reply_that_is_not_an_object_makes_no_claim() {
    let mut replies = good();
    replies[2] = Some(json!(["accepted"]));
    let (passed, report) = run(&replies);
    assert!(passed, "{report}");
    assert_eq!(report["detail"]["accepts"]["grammar_mask"], 1);
}

#[test]
fn a_reply_stands_when_it_is_a_negative_cycle_or_a_feasible_potential() {
    let replies = [
        say("{\"potential\": [0, 2, 1]}"),
        say("{\"negative_cycle\": [0, 1, 2]}"),
        say("{\"potential\": [0, 2, 1]}"),
        say("{\"negative_cycle\": [0, 1, 2]}"),
    ];
    let (_, report) = run(&replies);
    assert_eq!(
        report["detail"],
        json!({
            "accepts": {"grammar_mask": 2, "prompt": 2},
            "discordant": {"first_only": 0, "second_only": 0},
        })
    );
    let crossed = [
        say("{\"negative_cycle\": [0, 1, 2]}"),
        say("{\"potential\": [0, 2, 1]}"),
        say("{\"potential\": [0, 2, 1]}"),
        say("{\"negative_cycle\": [0, 1, 2]}"),
    ];
    let (_, report) = run(&crossed);
    assert_eq!(
        report["detail"],
        json!({
            "accepts": {"grammar_mask": 2, "prompt": 0},
            "discordant": {"first_only": 0, "second_only": 2},
        })
    );
}

#[test]
fn the_discordant_pairs_are_counted_for_the_first_two_arms_and_the_rest_are_counted_alone() {
    let items = json!([feasible(), feasible(), feasible(), negative()]);
    let three = json!([arm("a"), arm("b"), arm("c")]);
    let task = task_of(&items, &three);
    let yes = "{\"potential\": [0, 2, 1]}";
    let no = "{}";
    let rows = [[yes, yes, yes, no], [yes, no, no, no], [no, yes, yes, yes]];
    let replies: Vec<Option<Value>> = rows.iter().flatten().map(|text| say(text)).collect();
    let (passed, report) = run_on(&task, &replies);
    assert!(passed, "{report}");
    assert_eq!(
        report["detail"],
        json!({
            "accepts": {"a": 3, "b": 1, "c": 2},
            "discordant": {"first_only": 2, "second_only": 0},
        })
    );
    let reversed = json!([arm("b"), arm("a"), arm("c")]);
    let swapped: Vec<Option<Value>> = [rows[1], rows[0], rows[2]]
        .iter()
        .flatten()
        .map(|text| say(text))
        .collect();
    let (_, report) = run_on(&task_of(&items, &reversed), &swapped);
    assert_eq!(
        report["detail"]["discordant"],
        json!({"first_only": 0, "second_only": 2})
    );
}

#[test]
fn the_pairs_are_counted_item_by_item() {
    let items = json!([feasible(), negative(), feasible()]);
    let task = task_of(&items, &json!([arm("a"), arm("b")]));
    let yes = "{\"potential\": [0, 2, 1]}";
    let walk = "{\"negative_cycle\": [0, 1, 2]}";
    let no = "{}";
    let replies = [yes, walk, no, no, walk, yes].map(say);
    let (_, report) = run_on(&task, &replies);
    assert_eq!(
        report["detail"]["discordant"],
        json!({"first_only": 1, "second_only": 1})
    );
    assert_eq!(report["detail"]["accepts"], json!({"a": 2, "b": 2}));
}

#[test]
fn replies_that_are_missing_leave_the_run_waiting_and_extra_ones_are_not_accepted() {
    match judge(&request(&task(), &good()[..3])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "REPLIES_INCOMPLETE");
            assert_eq!(refusal.message, "stage grammar_mask:1 has no reply yet");
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
    let mut extra = good();
    extra.push(say("{}"));
    match judge(&request(&task(), &extra)) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn a_task_states_its_items_and_its_arms() {
    let arms = json!([arm("prompt"), arm("grammar_mask")]);
    let cases = [
        (
            json!({"statement": "s", "arms": arms}),
            "items must be a nonempty list",
        ),
        (task_of(&json!([]), &arms), "items must be a nonempty list"),
        (
            task_of(&json!("items"), &arms),
            "items must be a nonempty list",
        ),
        (task_of(&json!([{"n": 2}]), &arms), "edges must be a list"),
        (
            task_of(&json!([{"n": "2", "edges": []}]), &arms),
            "n must be an exact integer",
        ),
        (
            task_of(&json!([feasible()]), &json!([arm("prompt")])),
            "arms must be a list of at least two",
        ),
        (
            task_of(&json!([feasible()]), &json!([])),
            "arms must be a list of at least two",
        ),
        (
            task_of(&json!([feasible()]), &json!("prompt")),
            "arms must be a list of at least two",
        ),
        (
            json!({"statement": "s", "items": [feasible()]}),
            "arms must be a list of at least two",
        ),
        (
            task_of(
                &json!([feasible()]),
                &json!([arm("prompt"), {"checker_pin": pin()}]),
            ),
            "each arm needs its channel as text",
        ),
        (
            task_of(
                &json!([feasible()]),
                &json!([arm("prompt"), {"channel": 5}]),
            ),
            "each arm needs its channel as text",
        ),
        (
            task_of(
                &json!([feasible()]),
                &json!([arm("prompt"), "grammar_mask"]),
            ),
            "each arm needs its channel as text",
        ),
        (
            task_of(&json!([feasible()]), &json!([arm("prompt"), arm("prompt")])),
            "each arm needs its own channel",
        ),
        (
            task_of(&json!([feasible()]), &json!([arm("a"), arm("b"), arm("a")])),
            "each arm needs its own channel",
        ),
    ];
    for (bad, reason) in cases {
        assert_eq!(bad_task(&bad), reason, "{bad}");
    }
}

#[test]
fn the_items_are_read_before_the_arms() {
    let both = task_of(&json!([]), &json!([]));
    assert_eq!(bad_task(&both), "items must be a nonempty list");
}

#[test]
fn channels_that_differ_only_in_case_are_different_channels() {
    let task = task_of(&json!([feasible()]), &json!([arm("prompt"), arm("Prompt")]));
    let replies = [say("{\"potential\": [0, 2, 1]}"), say("{}")];
    let (passed, report) = run_on(&task, &replies);
    assert!(passed, "{report}");
    assert_eq!(
        report["detail"]["accepts"],
        json!({"Prompt": 0, "prompt": 1})
    );
}

#[test]
fn no_prompt_carries_a_reply_or_a_claim() {
    let turn = asked(&task(), &[say("{\"potential\": [0, 2, 1]}")]);
    let prompt = turn["ask"]["prompt"].as_str().expect("a prompt");
    assert!(!prompt.contains("potential"));
    assert!(!prompt.contains("accepted"));
}
