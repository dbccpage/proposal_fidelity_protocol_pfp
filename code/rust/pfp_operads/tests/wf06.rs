//! WF6, dialect sweep: how a dialect rewrites a system, the gate on dialects that change the
//! query, one question per item and dialect, and the table of grades.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf06-tests:v1

use pfp_operads::families::wf06::{FAMILY, MAX_CAPSULES};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Solve A x = b exactly or refuse with a code.";

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF6", "task": task, "replies": replies}).to_string()
}

fn all(replies: Vec<Value>) -> Vec<Option<Value>> {
    replies.into_iter().map(Some).collect()
}

/// The report of a finished run, and whether the host passed it.
fn run(task: &Value, replies: Vec<Value>) -> (bool, Value) {
    match judge(&request(task, &all(replies))) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

/// The next question of a run that is not finished.
fn ask(task: &Value, replies: Vec<Value>) -> Value {
    match next(&request(task, &all(replies))) {
        Outcome::Pass { result } => result["ask"].clone(),
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

/// The digest of the evidence recorded under a predicate.
fn evidence<'r>(report: &'r Value, name: &str) -> &'r Value {
    let rows = report["predicates"].as_array().expect("predicates");
    let row = rows.iter().find(|row| row["name"] == name);
    &row.unwrap_or_else(|| panic!("no predicate {name}"))["evidence_sha256"]
}

/// `u` has the one solution (2, 1) and `n` has none. `swap` exchanges the unknowns, and
/// `scaled` exchanges the equations, doubling one and halving the other.
fn task() -> Value {
    json!({
        "statement": STATEMENT,
        "items": [
            {"id": "u", "A": [[1, 1], [1, -1]], "b": [3, 1]},
            {"id": "n", "A": [[1, 1], [1, 1]], "b": [1, 2]},
        ],
        "dialects": [
            {"name": "plain"},
            {"name": "swap", "col_perm": [1, 0]},
            {"name": "scaled", "row_perm": [1, 0], "row_scale": [2, "1/2"]},
        ],
    })
}

fn with(key: &str, value: Value) -> Value {
    let mut task = task();
    task[key] = value;
    task
}

/// A task with one item and one dialect.
fn single(item: Value, dialect: Value) -> Value {
    json!({"statement": STATEMENT, "items": [item], "dialects": [dialect]})
}

fn answer(values: Value) -> Value {
    json!({ "answer": values })
}

fn none() -> Value {
    json!({"refusal": "UNRESOLVED_INCONSISTENT"})
}

/// The right reply to each of the six questions, in the order they are asked.
fn right() -> Vec<Value> {
    vec![
        answer(json!([2, 1])),
        answer(json!([1, 2])),
        answer(json!([2, 1])),
        none(),
        none(),
        none(),
    ]
}

/// The right replies with one of them replaced.
fn right_but(at: usize, reply: Value) -> Vec<Value> {
    let mut replies = right();
    replies[at] = reply;
    replies
}

/// The stage and the system of every question a task asks when each is answered with `{}`.
fn questions(task: &Value) -> Vec<(String, String)> {
    let mut replies = Vec::new();
    let mut asked = Vec::new();
    loop {
        let turn = ask(task, replies.clone());
        if turn.is_null() {
            return asked;
        }
        let prompt = turn["prompt"].as_str().expect("a prompt");
        assert_eq!(turn["prompt_sha256"], sha(prompt));
        let system = prompt
            .strip_prefix(&format!("{STATEMENT}\n"))
            .expect("the statement, then the system");
        asked.push((
            turn["stage"].as_str().expect("a stage").to_owned(),
            system.to_owned(),
        ));
        replies.push(json!({}));
    }
}

/// The one system a task with one item and one dialect asks.
fn posed(item: Value, dialect: Value) -> String {
    let mut asked = questions(&single(item, dialect));
    assert_eq!(asked.len(), 1);
    asked.remove(0).1
}

/// The pairs a run is refused for because a dialect changes the query.
fn broken(task: &Value) -> Value {
    assert_eq!(ask(task, vec![]), Value::Null);
    let (passed, report) = run(task, vec![]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "DIALECT_CHANGES_QUERY");
    assert_eq!(outcomes(&report), [("dialects_preserve_query", false)]);
    report["detail"]["broken"].clone()
}

/// Whether one dialect keeps the query of one item.
fn keeps(item: Value, dialect: Value) -> bool {
    !ask(&single(item, dialect), vec![]).is_null()
}

fn unique() -> Value {
    json!({"id": "u", "A": [[1, 1], [1, -1]], "b": [3, 1]})
}

fn inconsistent() -> Value {
    json!({"id": "n", "A": [[1, 1], [1, 1]], "b": [1, 2]})
}

fn underdetermined() -> Value {
    json!({"id": "m", "A": [[1, 1], [2, 2]], "b": [1, 2]})
}

/// x = 1, y = 2, z = 3.
fn diagonal() -> Value {
    json!({"id": "d", "A": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "b": [1, 2, 3]})
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        ("WF6", "Dialect sweep", "dialect_query_preservation_sweep")
    );
}

#[test]
fn one_question_is_asked_per_item_and_dialect_items_first() {
    let asked = questions(&task());
    let expected = [
        ("u:plain", r#"{"A":[[1,1],[1,-1]],"b":[3,1]}"#),
        ("u:swap", r#"{"A":[[1,1],[-1,1]],"b":[3,1]}"#),
        ("u:scaled", r#"{"A":[[2,-2],["1/2","1/2"]],"b":[2,"3/2"]}"#),
        ("n:plain", r#"{"A":[[1,1],[1,1]],"b":[1,2]}"#),
        ("n:swap", r#"{"A":[[1,1],[1,1]],"b":[1,2]}"#),
        ("n:scaled", r#"{"A":[[2,2],["1/2","1/2"]],"b":[4,"1/2"]}"#),
    ];
    let asked: Vec<(&str, &str)> = asked
        .iter()
        .map(|(stage, system)| (stage.as_str(), system.as_str()))
        .collect();
    assert_eq!(asked, expected);
}

#[test]
fn a_sweep_answered_rightly_in_every_dialect_is_certified() {
    let (passed, report) = run(&task(), right());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "SWEEP_GRADED");
    assert_eq!(
        report["detail"],
        json!({
            "acceptance": {"plain": 1, "swap": 1, "scaled": 1},
            "items": {
                "u": {"plain": true, "swap": true, "scaled": true},
                "n": {"plain": true, "swap": true, "scaled": true},
            },
            "flips_vs_first": [],
        })
    );
    assert_eq!(
        outcomes(&report),
        [
            ("dialects_preserve_query", true),
            ("every_capsule_graded_once", true)
        ]
    );
    assert_eq!(
        evidence(&report, "dialects_preserve_query"),
        &json!(sha("[]"))
    );
    assert_eq!(
        evidence(&report, "every_capsule_graded_once"),
        &json!(sha("[]"))
    );
}

#[test]
fn a_sweep_is_certified_whatever_the_grades_and_lists_what_flipped() {
    // The plain answer given to the swapped question, and a bluff on the last one.
    let mut replies = right_but(1, answer(json!([2, 1])));
    replies[5] = answer(json!([0, 0]));
    let (passed, report) = run(&task(), replies);
    assert!(passed);
    assert_eq!(report["code"], "SWEEP_GRADED");
    assert_eq!(
        report["detail"],
        json!({
            "acceptance": {"plain": 1, "swap": "1/2", "scaled": "1/2"},
            "items": {
                "u": {"plain": true, "swap": false, "scaled": true},
                "n": {"plain": true, "swap": true, "scaled": false},
            },
            "flips_vs_first": [["u", "swap"], ["n", "scaled"]],
        })
    );
}

#[test]
fn a_flip_is_a_grade_that_differs_from_the_first_dialect_either_way() {
    // Wrong in the first dialect and right in the two after it.
    let (passed, report) = run(&task(), right_but(0, answer(json!([0, 0]))));
    assert!(passed);
    assert_eq!(
        report["detail"]["flips_vs_first"],
        json!([["u", "swap"], ["u", "scaled"]])
    );
    assert_eq!(
        report["detail"]["acceptance"],
        json!({"plain": "1/2", "swap": 1, "scaled": 1})
    );
    // Wrong everywhere: nothing flips, and nothing is accepted.
    let wrong = vec![json!({"answer": [0, 0]}); 6];
    let (passed, report) = run(&task(), wrong);
    assert!(passed);
    assert_eq!(report["detail"]["flips_vs_first"], json!([]));
    assert_eq!(
        report["detail"]["acceptance"],
        json!({"plain": 0, "swap": 0, "scaled": 0})
    );
}

#[test]
fn each_reply_is_graded_as_wf7_grades_it() {
    let graded = |at: usize, reply: Value| {
        let (passed, report) = run(&task(), right_but(at, reply.clone()));
        assert!(passed, "{reply}");
        let (item, dialect) = [("u", "plain"), ("n", "plain")][at / 3];
        report["detail"]["items"][item][dialect] == json!(true)
    };
    // The item with one solution.
    assert!(graded(0, answer(json!([2, 1]))));
    assert!(graded(0, answer(json!(["4/2", "3/3"]))));
    for wrong in [
        answer(json!([1, 2])),
        answer(json!([2])),
        answer(json!("21")),
        answer(json!([2, 1.0])),
        none(),
        json!({"refusal": "UNRESOLVED_UNDERDETERMINED"}),
        json!({}),
        json!("x = 2, y = 1"),
        json!([2, 1]),
        json!(null),
    ] {
        assert!(!graded(0, wrong.clone()), "{wrong}");
    }
    // The item with none.
    assert!(graded(3, none()));
    for wrong in [
        json!({"refusal": "UNRESOLVED_UNDERDETERMINED"}),
        json!({"refusal": "NONE"}),
        answer(json!([0, 0])),
        json!({}),
        json!("no solution"),
    ] {
        assert!(!graded(3, wrong.clone()), "{wrong}");
    }
}

#[test]
fn a_question_left_without_a_reply_refuses_the_sweep_as_incomplete() {
    let mut replies: Vec<Option<Value>> = right().into_iter().map(Some).collect();
    replies[1] = None;
    replies[5] = None;
    let outcome = judge(&request(&task(), &replies));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "INCOMPLETE_SWEEP");
    assert_eq!(
        result["detail"],
        json!({"missing": [["u", "swap"], ["n", "scaled"]]})
    );
    assert_eq!(
        outcomes(&result),
        [
            ("dialects_preserve_query", true),
            ("every_capsule_graded_once", false)
        ]
    );
    assert_eq!(
        evidence(&result, "every_capsule_graded_once"),
        &json!(sha(r#"[["u","swap"],["n","scaled"]]"#))
    );
    // The questions after a missing reply are still asked.
    let turn = next(&request(&task(), &[Some(json!({})), None]));
    let Outcome::Pass { result } = turn else {
        panic!("expected a turn, got {turn:?}");
    };
    assert_eq!(result["ask"]["stage"], "u:scaled");
}

#[test]
fn a_dialect_that_changes_the_query_refuses_the_run_before_anything_is_asked() {
    let mut task = task();
    task["dialects"]
        .as_array_mut()
        .expect("a list")
        .push(json!({"name": "shifted", "b_shift": [1, 0]}));
    // A new solution for u, and solutions where n had none.
    assert_eq!(broken(&task), json!([["u", "shifted"], ["n", "shifted"]]));
    let (_, report) = run(&task, vec![]);
    assert_eq!(
        evidence(&report, "dialects_preserve_query"),
        &json!(sha(r#"[["u","shifted"],["n","shifted"]]"#))
    );
    assert_eq!(
        report["detail"],
        json!({"broken": [["u", "shifted"], ["n", "shifted"]]})
    );
}

#[test]
fn a_dialect_keeps_the_query_when_answerability_and_solution_are_the_same() {
    // Exchanging or scaling equations by a number that is not zero changes nothing.
    assert!(keeps(unique(), json!({"name": "d", "row_perm": [1, 0]})));
    assert!(keeps(
        unique(),
        json!({"name": "d", "row_scale": [-3, "2/7"]})
    ));
    assert!(keeps(unique(), json!({"name": "d", "b_shift": [0, 0]})));
    assert!(keeps(
        underdetermined(),
        json!({"name": "d", "row_scale": [5, 1]})
    ));
    assert!(keeps(
        inconsistent(),
        json!({"name": "d", "col_perm": [1, 0]})
    ));
    // Scaling an equation away, or moving a right-hand side.
    assert!(!keeps(unique(), json!({"name": "d", "row_scale": [0, 1]})));
    assert!(!keeps(unique(), json!({"name": "d", "b_shift": [0, 1]})));
    assert!(!keeps(
        underdetermined(),
        json!({"name": "d", "b_shift": [1, 0]})
    ));
    assert!(!keeps(
        inconsistent(),
        json!({"name": "d", "b_shift": [1, 0]})
    ));
    // No solution before and none after is the same query, whatever moved.
    assert!(keeps(
        inconsistent(),
        json!({"name": "d", "b_shift": [5, 0]})
    ));
    // One of many solutions is not the query of a system with one.
    assert!(!keeps(
        unique(),
        json!({"name": "d", "row_scale": [1, 0], "b_shift": [0, 0]})
    ));
}

#[test]
fn a_solution_is_read_back_through_the_column_order_before_it_is_compared() {
    // Three unknowns sent round a cycle: the rewritten system has the solution (2, 3, 1).
    let cycle = json!({"name": "cycle", "col_perm": [1, 2, 0]});
    assert!(keeps(diagonal(), cycle.clone()));
    assert_eq!(
        posed(diagonal(), cycle.clone()),
        r#"{"A":[[0,0,1],[1,0,0],[0,1,0]],"b":[1,2,3]}"#
    );
    let (passed, report) = run(&single(diagonal(), cycle), vec![answer(json!([2, 3, 1]))]);
    assert!(passed);
    assert_eq!(report["detail"]["acceptance"], json!({"cycle": 1}));
}

#[test]
fn a_row_of_the_rewritten_system_is_a_scaled_row_of_the_item_plus_a_shift() {
    let rows = json!({"name": "rows", "row_perm": [1, 2, 0]});
    assert_eq!(
        posed(diagonal(), rows),
        r#"{"A":[[0,1,0],[0,0,1],[1,0,0]],"b":[2,3,1]}"#
    );
    // The scale belongs to the place a row lands in, not the place it came from.
    let scaled = json!({"name": "s", "row_perm": [1, 2, 0], "row_scale": [10, 100, "1/2"]});
    assert_eq!(
        posed(diagonal(), scaled),
        r#"{"A":[[0,10,0],[0,0,100],["1/2",0,0]],"b":[20,300,"1/2"]}"#
    );
    // The shift is added after the scale.
    let both = json!({"name": "b", "row_scale": [2, 1], "b_shift": [1, "1/2"]});
    assert_eq!(
        posed(inconsistent(), both),
        r#"{"A":[[2,2],[1,1]],"b":[3,"5/2"]}"#
    );
    // Rows and columns at once, on a system that is not square.
    let wide = json!({"id": "w", "A": [[1, 2, 3], [4, 5, 6]], "b": [7, 8]});
    let turned = json!({"name": "t", "row_perm": [1, 0], "col_perm": [2, 0, 1]});
    assert_eq!(posed(wide, turned), r#"{"A":[[6,4,5],[3,1,2]],"b":[8,7]}"#);
}

#[test]
fn a_task_needs_a_statement_items_and_dialects() {
    let mut bare = task();
    bare.as_object_mut().expect("an object").remove("statement");
    assert_eq!(bad_task(bare), "statement must be text");
    assert_eq!(
        bad_task(with("statement", json!(5))),
        "statement must be text"
    );
    for key in ["items", "dialects"] {
        for listed in [json!([]), json!(null), json!({"0": {}}), json!("all")] {
            assert_eq!(bad_task(with(key, listed)), format!("{key} required"));
        }
    }
}

#[test]
fn an_item_is_a_text_id_and_a_system_as_wf7_reads_it() {
    let item = |written: Value| bad_task(with("items", json!([written])));
    assert_eq!(
        item(json!({"A": [[1]], "b": [1]})),
        "every item needs a text id"
    );
    assert_eq!(
        item(json!({"id": 7, "A": [[1]], "b": [1]})),
        "every item needs a text id"
    );
    assert_eq!(item(json!("u")), "every item needs a text id");
    assert_eq!(
        item(json!({"id": "u", "A": [], "b": []})),
        "A must be a nonempty list of rows"
    );
    assert_eq!(
        item(json!({"id": "u", "A": [[1, 0.5]], "b": [1]})),
        "every row of A must be a list of exact rationals"
    );
    assert_eq!(
        item(json!({"id": "u", "A": [[1, 1]]})),
        "b must be a list of exact rationals"
    );
    assert_eq!(
        item(json!({"id": "u", "A": [[1, 1], [1]], "b": [1, 2]})),
        "A must be rectangular, with a column, and match b"
    );
}

#[test]
fn a_dialect_is_a_text_name_with_permutations_and_exact_lists() {
    let dialect = |written: Value| bad_task(with("dialects", json!([written])));
    assert_eq!(
        dialect(json!({"col_perm": [1, 0]})),
        "every dialect needs a text name"
    );
    assert_eq!(
        dialect(json!({"name": 3})),
        "every dialect needs a text name"
    );
    assert_eq!(dialect(json!("plain")), "every dialect needs a text name");
    for key in ["row_perm", "col_perm"] {
        for listed in [
            json!([0, 0]),
            json!([1, 2]),
            json!([0, 2]),
            json!([-1, 0]),
            json!(["0", "1"]),
            json!([true, false]),
            json!([0.0, 1.0]),
            json!("10"),
            json!(null),
            json!({"0": 1, "1": 0}),
        ] {
            let mut written = json!({"name": "d"});
            written[key] = listed.clone();
            assert_eq!(
                dialect(written),
                format!("{key} must be a permutation"),
                "{listed}"
            );
        }
    }
    for key in ["row_scale", "b_shift"] {
        for listed in [
            json!([1, 0.5]),
            json!([1, "x"]),
            json!("11"),
            json!(null),
            json!({"0": 1}),
        ] {
            let mut written = json!({"name": "d"});
            written[key] = listed.clone();
            assert_eq!(
                dialect(written),
                format!("{key} must be a list of exact rationals"),
                "{listed}"
            );
        }
    }
}

#[test]
fn the_parts_of_a_task_are_read_in_a_fixed_order() {
    let mut task = json!({
        "statement": 5,
        "items": [{"id": 7}, {"id": "u", "A": [[1]], "b": [1]}],
        "dialects": [{
            "name": 3, "row_perm": [0, 0], "col_perm": [0, 0], "row_scale": "x", "b_shift": "x"
        }],
    });
    let mut step = |fix: &dyn Fn(&mut Value), expected: &str| {
        assert_eq!(bad_task(task.clone()), expected);
        fix(&mut task);
    };
    step(
        &|task| task["statement"] = json!(STATEMENT),
        "statement must be text",
    );
    step(
        &|task| task["items"][0] = json!({"id": "u", "A": [[1]], "b": [1]}),
        "every item needs a text id",
    );
    step(
        &|task| task["dialects"][0]["name"] = json!("d"),
        "every dialect needs a text name",
    );
    step(
        &|task| task["dialects"][0]["row_perm"] = json!([0]),
        "row_perm must be a permutation",
    );
    step(
        &|task| task["dialects"][0]["col_perm"] = json!([0]),
        "col_perm must be a permutation",
    );
    step(
        &|task| task["dialects"][0]["row_scale"] = json!([1]),
        "row_scale must be a list of exact rationals",
    );
    step(
        &|task| task["dialects"][0]["b_shift"] = json!([0, 0]),
        "b_shift must be a list of exact rationals",
    );
    step(
        &|task| task["items"][1]["id"] = json!("v"),
        "item ids must be distinct",
    );
    step(
        &|task| task["dialects"][0]["b_shift"] = json!([0]),
        "every dialect must fit the rows and columns of every item",
    );
    assert_eq!(ask(&task, vec![])["stage"], "u:d");
}

#[test]
fn ids_and_names_are_distinct() {
    let twice = json!([unique(), inconsistent(), unique()]);
    assert_eq!(bad_task(with("items", twice)), "item ids must be distinct");
    let twice = json!([{"name": "plain"}, {"name": "swap", "col_perm": [1, 0]}, {"name": "plain"}]);
    assert_eq!(
        bad_task(with("dialects", twice)),
        "dialect names must be distinct"
    );
}

#[test]
fn a_sweep_asks_at_most_64_questions() {
    assert_eq!(MAX_CAPSULES, 64);
    let sized = |items: usize, dialects: usize| {
        let items: Vec<Value> = (0..items)
            .map(|at| json!({"id": format!("i{at}"), "A": [[1]], "b": [1]}))
            .collect();
        let dialects: Vec<Value> = (0..dialects)
            .map(|at| json!({ "name": format!("d{at}") }))
            .collect();
        json!({"statement": STATEMENT, "items": items, "dialects": dialects})
    };
    assert_eq!(bad_task(sized(13, 5)), "at most 64 questions");
    assert_eq!(bad_task(sized(65, 1)), "at most 64 questions");
    assert_eq!(bad_task(sized(1, 65)), "at most 64 questions");
    assert_eq!(ask(&sized(8, 8), vec![])["stage"], "i0:d0");
    assert_eq!(ask(&sized(64, 1), vec![])["stage"], "i0:d0");
    assert_eq!(ask(&sized(1, 64), vec![])["stage"], "i0:d0");
}

#[test]
fn every_dialect_must_be_written_for_the_shape_of_every_item() {
    let reason = "every dialect must fit the rows and columns of every item";
    // Two equations in three unknowns.
    let wide = json!({"id": "w", "A": [[1, 2, 3], [4, 5, 6]], "b": [7, 8]});
    let fits = |dialect: Value| {
        let task = single(wide.clone(), dialect);
        !matches!(next(&request(&task, &[])), Outcome::Refused { .. })
    };
    assert!(fits(json!({"name": "d"})));
    assert!(fits(
        json!({"name": "d", "row_perm": [1, 0], "col_perm": [2, 0, 1]})
    ));
    assert!(fits(
        json!({"name": "d", "row_scale": [1, 1], "b_shift": [0, 0]})
    ));
    for dialect in [
        json!({"name": "d", "row_perm": [1, 2, 0]}),
        json!({"name": "d", "row_perm": [0]}),
        json!({"name": "d", "col_perm": [1, 0]}),
        json!({"name": "d", "col_perm": [1, 0, 2, 3]}),
        json!({"name": "d", "row_scale": [1, 1, 1]}),
        json!({"name": "d", "row_scale": [1]}),
        json!({"name": "d", "b_shift": [0, 0, 0]}),
        json!({"name": "d", "b_shift": []}),
    ] {
        assert_eq!(bad_task(single(wide.clone(), dialect)), reason);
    }
    // One dialect cannot fit two items of different shapes, unless it rewrites nothing.
    let mut mixed = with("items", json!([unique(), wide.clone()]));
    assert_eq!(bad_task(mixed.clone()), reason);
    mixed["dialects"] = json!([{"name": "plain"}]);
    assert_eq!(ask(&mixed, vec![])["stage"], "u:plain");
}

#[test]
fn replies_beyond_the_questions_are_refused() {
    let mut replies = right();
    replies.push(json!({}));
    let outcome = judge(&request(&task(), &all(replies)));
    let Outcome::Refused { refusal } = outcome else {
        panic!("expected a refusal, got {outcome:?}");
    };
    assert_eq!(refusal.code, "BAD_REQUEST");
}
