//! WF16, substrate crosswalk: a graph cochain carried onto an incidence matrix, with the
//! bijection, the relations and the data each checked.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf16-tests:v1

use pfp_operads::families::wf16::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Map the graph cochain onto the incidence matrix.";

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF16", "task": task, "replies": replies}).to_string()
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

/// The reason of a run refused because a reply could not be read.
fn malformed(task: &Value, replies: Vec<Value>) -> String {
    let (passed, report) = run(task, replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
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

/// A triangle a, b, c with the exact cochain (1, 2, 3). Columns: b, c, a. Row 0 is edge 2,
/// row 1 is edge 0, and row 2 is edge 1 with its sign flipped.
fn task() -> Value {
    json!({
        "statement": STATEMENT,
        "edges": [["a", "b"], ["b", "c"], ["a", "c"]],
        "c": [1, 2, 3],
        "D": [[0, 1, -1], [1, 0, -1], [1, -1, 0]],
        "y": [3, 1, -2],
    })
}

fn with(key: &str, value: Value) -> Value {
    let mut task = task();
    task[key] = value;
    task
}

fn prompt() -> String {
    format!(
        "WF16 Substrate crosswalk. {STATEMENT}\n{}",
        r#"{"D":[[0,1,-1],[1,0,-1],[1,-1,0]],"c":[1,2,3],"edges":[["a","b"],["b","c"],["a","c"]],"y":[3,1,-2]}"#
    )
}

/// The crosswalk the task was built from.
fn walk() -> Value {
    json!({"vertex_col": {"a": 2, "b": 0, "c": 1}, "edge_row": {"0": [1, 1], "1": [2, -1], "2": [0, 1]}})
}

fn walk_with(part: &str, key: &str, value: Value) -> Value {
    let mut walk = walk();
    walk[part][key] = value;
    walk
}

fn reply(crosswalks: Vec<Value>) -> Value {
    json!({ "crosswalks": crosswalks })
}

const FIRST: [&str; 4] = [
    "verdicts_identical",
    "crosswalk0:bijective",
    "crosswalk0:relations_preserved",
    "crosswalk0:data_transported",
];

/// The four checks of a run with one bijective crosswalk, with these outcomes.
fn four(passed: [bool; 4]) -> Vec<(&'static str, bool)> {
    FIRST.into_iter().zip(passed).collect()
}

/// A run with one crosswalk that is not bijective.
fn not_bijective(task: &Value, crosswalk: Value) {
    let (passed, report) = run(task, vec![reply(vec![crosswalk.clone()])]);
    assert!(!passed, "{crosswalk}");
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "CROSSWALK0:BIJECTIVE", "{crosswalk}");
    assert_eq!(
        outcomes(&report),
        [
            ("verdicts_identical", true),
            ("crosswalk0:bijective", false)
        ]
    );
    assert_eq!(report["detail"]["choices"], json!([]));
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        ("WF16", "Substrate crosswalk", "incidence_rank_crosswalk")
    );
}

#[test]
fn the_one_question_is_the_task_as_written() {
    let first = ask(&task(), vec![]);
    assert_eq!(first["stage"], "solve");
    assert_eq!(first["prompt"], prompt());
    assert_eq!(first["prompt_sha256"], sha(&prompt()));
    assert_eq!(ask(&task(), vec![reply(vec![walk()])]), Value::Null);
}

#[test]
fn a_crosswalk_that_carries_relations_and_data_is_certified() {
    let (passed, report) = run(&task(), vec![reply(vec![walk()])]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CROSSWALK_PRESERVED");
    assert_eq!(
        report["detail"],
        json!({"verdict": "exact", "choices": [{"flipped_edges": [1]}], "differ_on_vertices": []})
    );
    assert_eq!(outcomes(&report), four([true; 4]));
    assert_eq!(
        evidence(&report, "verdicts_identical"),
        &json!(sha("[true,true]"))
    );
    let written =
        r#"{"edge_row":{"0":[1,1],"1":[2,-1],"2":[0,1]},"vertex_col":{"a":2,"b":0,"c":1}}"#;
    for name in &FIRST[1..] {
        assert_eq!(evidence(&report, name), &json!(sha(written)), "{name}");
    }
}

#[test]
fn a_cochain_that_is_not_exact_on_either_side_is_certified_as_not_exact() {
    let mut task = with("c", json!([1, 2, 4]));
    task["y"] = json!([4, 1, -2]);
    let (passed, report) = run(&task, vec![reply(vec![walk()])]);
    assert!(passed);
    assert_eq!(report["code"], "CROSSWALK_PRESERVED");
    assert_eq!(report["detail"]["verdict"], "not_exact");
    assert_eq!(
        evidence(&report, "verdicts_identical"),
        &json!(sha("[false,false]"))
    );
}

#[test]
fn verdicts_that_differ_between_the_substrates_are_refused() {
    // Exact on the graph, inconsistent on the matrix.
    let (passed, report) = run(&with("y", json!([4, 1, -2])), vec![reply(vec![walk()])]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "VERDICTS_IDENTICAL");
    assert_eq!(outcomes(&report), four([false, true, true, false]));
    assert_eq!(
        report["detail"]["failed"],
        json!(["verdicts_identical", "crosswalk0:data_transported"])
    );
    assert_eq!(report["detail"]["verdict"], "exact");
    assert_eq!(
        evidence(&report, "verdicts_identical"),
        &json!(sha("[true,false]"))
    );
    // Not exact on the graph, consistent on the matrix.
    let (_, other) = run(&with("c", json!([1, 2, 4])), vec![reply(vec![walk()])]);
    assert_eq!(other["code"], "VERDICTS_IDENTICAL");
    assert_eq!(other["detail"]["verdict"], "not_exact");
    assert_eq!(
        evidence(&other, "verdicts_identical"),
        &json!(sha("[false,true]"))
    );
}

#[test]
fn the_target_is_exact_when_y_adds_no_rank_to_d() {
    // A fourth row of zeros keeps the matrix consistent only while its entry of y is zero.
    let tall = |last: i64| {
        let mut task = with("D", json!([[0, 1, -1], [1, 0, -1], [1, -1, 0], [0, 0, 0]]));
        task["y"] = json!([3, 1, -2, last]);
        run(&task, vec![reply(vec![walk()])]).1
    };
    assert_eq!(
        evidence(&tall(0), "verdicts_identical"),
        &json!(sha("[true,true]"))
    );
    assert_eq!(
        evidence(&tall(1), "verdicts_identical"),
        &json!(sha("[true,false]"))
    );
    // Three edges cannot fill four rows.
    assert_eq!(tall(0)["code"], "CROSSWALK0:BIJECTIVE");
}

#[test]
fn data_that_is_not_carried_is_refused_on_its_own() {
    // Twice the cochain on the matrix side: still consistent, but not the data of the graph.
    let (passed, report) = run(&with("y", json!([6, 2, -4])), vec![reply(vec![walk()])]);
    assert!(!passed);
    assert_eq!(report["code"], "CROSSWALK0:DATA_TRANSPORTED");
    assert_eq!(outcomes(&report), four([true, true, true, false]));
}

#[test]
fn a_row_that_is_not_the_signed_incidence_row_is_refused() {
    // Edge 1 without its flip: the row has the wrong sign, and so has the data.
    let unflipped = walk_with("edge_row", "1", json!([2, 1]));
    let (passed, report) = run(&task(), vec![reply(vec![unflipped])]);
    assert!(!passed);
    assert_eq!(report["code"], "CROSSWALK0:RELATIONS_PRESERVED");
    assert_eq!(outcomes(&report), four([true, true, false, false]));
    assert_eq!(report["detail"]["choices"], json!([{"flipped_edges": []}]));
    // Two edges with their rows exchanged, on a cochain of zeros: the data still fits.
    let mut zero = with("c", json!([0, 0, 0]));
    zero["y"] = json!([0, 0, 0]);
    let mut exchanged = walk();
    exchanged["edge_row"] = json!({"0": [0, 1], "1": [2, -1], "2": [1, 1]});
    let (_, report) = run(&zero, vec![reply(vec![exchanged])]);
    assert_eq!(report["code"], "CROSSWALK0:RELATIONS_PRESERVED");
    assert_eq!(outcomes(&report), four([true, true, false, true]));
    // Vertices sent to the wrong columns.
    let mut turned = walk();
    turned["vertex_col"] = json!({"a": 0, "b": 1, "c": 2});
    let (_, report) = run(&task(), vec![reply(vec![turned])]);
    assert_eq!(outcomes(&report), four([true, true, false, true]));
}

#[test]
fn a_matrix_wider_or_narrower_than_the_vertices_preserves_no_relation() {
    for rows in [
        json!([[0, 1, -1, 0], [1, 0, -1, 0], [1, -1, 0, 0]]),
        json!([[0, 1], [1, 0], [1, -1]]),
    ] {
        let (_, report) = run(&with("D", rows), vec![reply(vec![walk()])]);
        assert_eq!(outcomes(&report)[1..], four([true, true, false, true])[1..]);
    }
}

#[test]
fn a_loop_is_a_zero_row_under_either_sign() {
    let task = json!({
        "edges": [["a", "a"], ["a", "b"]],
        "c": [0, 1],
        "D": [[0, 0], [-1, 1]],
        "y": [0, 1],
    });
    for (sign, flipped) in [(1, json!([])), (-1, json!([0]))] {
        let walk =
            json!({"vertex_col": {"a": 0, "b": 1}, "edge_row": {"0": [0, sign], "1": [1, 1]}});
        let (passed, report) = run(&task, vec![reply(vec![walk])]);
        assert!(passed);
        assert_eq!(
            report["detail"]["choices"],
            json!([{ "flipped_edges": flipped }])
        );
    }
}

#[test]
fn rationals_are_read_exactly_on_both_sides() {
    let task = json!({
        "edges": [["a", "b"]],
        "c": ["1/2"],
        "D": [["2/2", "-3/3"]],
        "y": ["-2/4"],
    });
    let walk = json!({"vertex_col": {"a": 0, "b": 1}, "edge_row": {"0": [0, -1]}});
    let (passed, report) = run(&task, vec![reply(vec![walk])]);
    assert!(passed);
    assert_eq!(report["detail"]["choices"], json!([{"flipped_edges": [0]}]));
}

#[test]
fn the_empty_graph_crosswalks_to_the_empty_matrix() {
    let task = json!({"edges": [], "c": [], "D": [], "y": []});
    let (passed, report) = run(
        &task,
        vec![reply(vec![json!({"vertex_col": {}, "edge_row": {}})])],
    );
    assert!(passed);
    assert_eq!(report["detail"]["verdict"], "exact");
}

/// Two edges between a and b, one each way, with the cochain (1, 1): not exact.
fn pair() -> Value {
    json!({"edges": [["a", "b"], ["b", "a"]], "c": [1, 1], "D": [[-1, 1], [1, -1]], "y": [1, 1]})
}

#[test]
fn several_crosswalks_are_each_checked_and_compared_with_the_first() {
    let straight = json!({"vertex_col": {"a": 0, "b": 1}, "edge_row": {"0": [0, 1], "1": [1, 1]}});
    let turned = json!({"vertex_col": {"a": 1, "b": 0}, "edge_row": {"0": [1, 1], "1": [0, 1]}});
    let (passed, report) = run(
        &pair(),
        vec![reply(vec![
            straight.clone(),
            turned.clone(),
            straight.clone(),
        ])],
    );
    assert!(passed);
    assert_eq!(
        report["detail"],
        json!({
            "verdict": "not_exact",
            "choices": [{"flipped_edges": []}, {"flipped_edges": []}, {"flipped_edges": []}],
            "differ_on_vertices": [["a", "b"], []],
        })
    );
    let names: Vec<&str> = outcomes(&report)
        .into_iter()
        .map(|(name, _)| name)
        .collect();
    assert_eq!(
        names,
        [
            "verdicts_identical",
            "crosswalk0:bijective",
            "crosswalk0:relations_preserved",
            "crosswalk0:data_transported",
            "crosswalk1:bijective",
            "crosswalk1:relations_preserved",
            "crosswalk1:data_transported",
            "crosswalk2:bijective",
            "crosswalk2:relations_preserved",
            "crosswalk2:data_transported",
        ]
    );
    // Later crosswalks are compared with the first one kept, whichever comes first.
    let (_, other) = run(&pair(), vec![reply(vec![turned.clone(), straight, turned])]);
    assert_eq!(
        other["detail"]["differ_on_vertices"],
        json!([["a", "b"], []])
    );
}

#[test]
fn a_crosswalk_that_is_not_bijective_is_dropped_and_the_rest_are_still_checked() {
    let clash = walk_with("vertex_col", "c", json!(0));
    let (passed, report) = run(&task(), vec![reply(vec![clash, walk(), walk()])]);
    assert!(!passed);
    assert_eq!(report["code"], "CROSSWALK0:BIJECTIVE");
    assert_eq!(
        outcomes(&report),
        [
            ("verdicts_identical", true),
            ("crosswalk0:bijective", false),
            ("crosswalk1:bijective", true),
            ("crosswalk1:relations_preserved", true),
            ("crosswalk1:data_transported", true),
            ("crosswalk2:bijective", true),
            ("crosswalk2:relations_preserved", true),
            ("crosswalk2:data_transported", true),
        ]
    );
    assert_eq!(
        report["detail"],
        json!({
            "failed": ["crosswalk0:bijective"],
            "verdict": "exact",
            "choices": [{"flipped_edges": [1]}, {"flipped_edges": [1]}],
            "differ_on_vertices": [[]],
        })
    );
}

#[test]
fn columns_must_fill_the_columns_once_each() {
    for column in [json!(0), json!(3), json!(-1), json!(u64::MAX)] {
        not_bijective(&task(), walk_with("vertex_col", "c", column));
    }
}

#[test]
fn rows_must_fill_the_rows_once_each() {
    for row in [json!(1), json!(3), json!(-1), json!(u64::MAX)] {
        not_bijective(&task(), walk_with("edge_row", "2", json!([row, 1])));
    }
}

#[test]
fn a_sign_must_be_one_or_minus_one() {
    for sign in [0, 2, -2] {
        not_bijective(&task(), walk_with("edge_row", "2", json!([0, sign])));
    }
}

#[test]
fn entries_beyond_the_vertices_and_edges_are_not_looked_at() {
    let mut extra = walk();
    extra["vertex_col"]["zz"] = json!("x");
    extra["edge_row"]["7"] = json!(null);
    extra["note"] = json!("ignored");
    let (passed, _) = run(&task(), vec![reply(vec![extra])]);
    assert!(passed);
}

#[test]
fn a_reply_without_crosswalks_is_malformed_after_the_verdicts_are_compared() {
    for reply in [
        json!({}),
        json!({"crosswalks": []}),
        json!({"crosswalks": {"0": walk()}}),
        json!([walk()]),
        json!("none"),
    ] {
        assert_eq!(
            malformed(&task(), vec![reply.clone()]),
            "crosswalks required"
        );
        let (_, report) = run(&task(), vec![reply]);
        assert_eq!(outcomes(&report), [("verdicts_identical", true)]);
    }
}

#[test]
fn a_crosswalk_without_its_two_maps_is_malformed() {
    let mut listed = walk();
    listed["edge_row"] = json!([[1, 1], [2, -1], [0, 1]]);
    let mut bare = walk();
    bare.as_object_mut()
        .expect("an object")
        .remove("vertex_col");
    for crosswalk in [listed, bare, json!("walk"), json!(null), json!([])] {
        assert_eq!(
            malformed(&task(), vec![reply(vec![crosswalk])]),
            "vertex_col and edge_row maps required"
        );
    }
}

#[test]
fn a_column_that_is_missing_or_not_an_integer_is_malformed() {
    let mut short = walk();
    short["vertex_col"] = json!({"a": 2, "b": 0});
    let odd = [json!("1"), json!(1.5), json!(true), json!(null), json!([1])];
    let odd = odd.map(|column| walk_with("vertex_col", "c", column));
    for crosswalk in odd.into_iter().chain([short]) {
        assert_eq!(
            malformed(&task(), vec![reply(vec![crosswalk])]),
            "column must be an exact int"
        );
    }
}

#[test]
fn an_edge_entry_that_is_missing_or_not_a_pair_is_malformed() {
    let mut short = walk();
    short["edge_row"] = json!({"0": [1, 1], "1": [2, -1]});
    let odd = [
        json!([0]),
        json!([0, 1, 1]),
        json!("01"),
        json!({"row": 0, "sign": 1}),
    ];
    let odd = odd.map(|entry| walk_with("edge_row", "2", entry));
    for crosswalk in odd.into_iter().chain([short]) {
        assert_eq!(
            malformed(&task(), vec![reply(vec![crosswalk])]),
            "edge_row entries are [row, sign]"
        );
    }
    // Every entry is read as a pair before any row or sign is read.
    let mut both = walk_with("edge_row", "0", json!(["x", 1]));
    both["edge_row"]["2"] = json!([0]);
    assert_eq!(
        malformed(&task(), vec![reply(vec![both])]),
        "edge_row entries are [row, sign]"
    );
}

#[test]
fn a_row_or_a_sign_that_is_not_an_integer_is_malformed() {
    for odd in [json!("0"), json!(0.5), json!(null), json!(false)] {
        let row = walk_with("edge_row", "2", json!([odd, 1]));
        assert_eq!(
            malformed(&task(), vec![reply(vec![row])]),
            "row must be an exact int"
        );
        let sign = walk_with("edge_row", "2", json!([0, odd]));
        assert_eq!(
            malformed(&task(), vec![reply(vec![sign])]),
            "sign must be an exact int"
        );
    }
    // The row is read before the sign.
    let both = walk_with("edge_row", "2", json!(["x", "y"]));
    assert_eq!(
        malformed(&task(), vec![reply(vec![both])]),
        "row must be an exact int"
    );
}

#[test]
fn a_malformed_crosswalk_keeps_the_predicates_recorded_before_it() {
    let (_, report) = run(&task(), vec![reply(vec![walk(), json!({})])]);
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    assert_eq!(outcomes(&report), four([true; 4]));
}

#[test]
fn a_task_whose_edges_are_not_pairs_of_text_is_refused() {
    let mut bare = task();
    bare.as_object_mut().expect("an object").remove("edges");
    for task in [
        bare,
        with("edges", json!([[0, 1], [1, 2], [0, 2]])),
        with("edges", json!([["a", "b"], ["b", "c"], ["a"]])),
        with("edges", json!({"a": "b"})),
    ] {
        assert_eq!(bad_task(task), "edges must be a list of pairs of text");
    }
}

#[test]
fn a_task_whose_cochain_does_not_fit_the_edges_is_refused() {
    for values in [
        json!([1, 2]),
        json!([1, 2, 3, 4]),
        json!([1, 2, 0.5]),
        json!("123"),
        json!(null),
    ] {
        assert_eq!(
            bad_task(with("c", values)),
            "c must be one exact rational per edge"
        );
    }
}

#[test]
fn a_task_whose_matrix_is_not_rectangular_and_exact_is_refused() {
    for rows in [
        json!("D"),
        json!(null),
        json!([[0, 1, "x"]]),
        json!([[0, 1, 0.5]]),
        json!([0, 1]),
    ] {
        assert_eq!(
            bad_task(with("D", rows)),
            "D must be a list of rows of exact rationals"
        );
    }
    for rows in [
        json!([[0, 1, -1], [1, 0, -1], [1, -1]]),
        json!([[0, 1], [1, 0, -1], [1, -1, 0]]),
    ] {
        assert_eq!(
            bad_task(with("D", rows)),
            "the rows of D must have one length"
        );
    }
}

#[test]
fn a_task_whose_vector_does_not_fit_the_rows_is_refused() {
    for data in [
        json!([3, 1]),
        json!([3, 1, -2, 0]),
        json!([3, 1, 1.5]),
        json!(null),
    ] {
        assert_eq!(
            bad_task(with("y", data)),
            "y must be one exact rational per row of D"
        );
    }
}

#[test]
fn the_parts_of_a_task_are_read_in_a_fixed_order() {
    let mut task = with("edges", json!(null));
    task["c"] = json!(null);
    task["D"] = json!(null);
    task["y"] = json!(null);
    assert_eq!(
        bad_task(task.clone()),
        "edges must be a list of pairs of text"
    );
    task["edges"] = json!([["a", "b"]]);
    assert_eq!(
        bad_task(task.clone()),
        "c must be one exact rational per edge"
    );
    task["c"] = json!([1]);
    assert_eq!(
        bad_task(task.clone()),
        "D must be a list of rows of exact rationals"
    );
    task["D"] = json!([[1, 0], [1]]);
    assert_eq!(bad_task(task.clone()), "the rows of D must have one length");
    task["D"] = json!([[1, 0], [1, 0]]);
    assert_eq!(bad_task(task), "y must be one exact rational per row of D");
}

#[test]
fn a_missing_reply_is_refused() {
    let outcome = judge(&request(&task(), &[None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}
