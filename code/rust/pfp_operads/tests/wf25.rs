//! WF25, hierarchical decimation: a smaller graph whose edges stand for walks in the task's
//! graph, and the five checks that it keeps every cycle and what each cycle sums to.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf25-tests:v1

use pfp_operads::families::wf25::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Remove the tree and degree-2 parts without changing any cycle sum.";

/// Two cycles through the edge 2-0 and a tail: 0-1-2-0 sums to 7, 2-3-0-2 to -2, and the walk
/// 0-1-2-3-0 round both to 5. Vertices 0 and 2 have three edges each; vertex 4 is a leaf.
fn task() -> Value {
    json!({"statement": STATEMENT,
           "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [3, 4]],
           "labels": [1, 2, 4, 5, -3, 6]})
}

/// A triangle whose values sum to 7.
fn triangle() -> Value {
    json!({"edges": [[0, 1], [1, 2], [2, 0]], "labels": [1, 2, 4]})
}

fn prompt() -> String {
    format!(
        "WF25 Hierarchical decimation. {STATEMENT}\n{}",
        r#"{"edges":[[0,1],[1,2],[2,0],[2,3],[3,0],[3,4]],"labels":[1,2,4,5,-3,6]}"#
    )
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
    json!({"workflow": "WF25", "task": task, "replies": replies}).to_string()
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

fn reduced(edges: Value, labels: Value, paths: Value) -> Value {
    json!({"edges": edges, "labels": labels, "paths": paths})
}

/// The three walks between the vertices 0 and 2: through 1, along the shared edge, and
/// through 3.
fn theta() -> Value {
    reduced(
        json!([[0, 2], [2, 0], [2, 0]]),
        json!([3, 4, 2]),
        json!([[[0, 1], [1, 1]], [[2, 1]], [[3, 1], [4, 1]]]),
    )
}

const CHECKS: [&str; 5] = [
    "paths_are_walks",
    "labels_are_path_sums",
    "cycle_rank_preserved",
    "lifted_cycles_span_h1",
    "strictly_smaller_without_leaves",
];

/// The five checks, all passed except those named.
fn all_but(failed: &[&str]) -> Vec<(&'static str, bool)> {
    CHECKS
        .into_iter()
        .map(|name| (name, !failed.contains(&name)))
        .collect()
}

/// A run refused under its first failed check, with exactly these checks failed.
fn refused_for(task: &Value, reply: Value, failed: &[&str]) -> Value {
    let (passed, report) = run(task, vec![reply]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], failed[0].to_uppercase());
    assert_eq!(report["detail"]["failed"], json!(failed));
    assert_eq!(outcomes(&report), all_but(failed));
    report
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF25",
            "Hierarchical decimation",
            "cycle_residual_preserving_decimation"
        )
    );
}

#[test]
fn the_one_question_is_the_task_as_written() {
    let first = ask(&task(), vec![]);
    assert_eq!(first["stage"], "solve");
    assert_eq!(first["prompt"], prompt());
    assert_eq!(first["prompt_sha256"], sha(&prompt()));
    assert_eq!(ask(&task(), vec![theta()]), Value::Null);
}

#[test]
fn a_decimation_that_keeps_every_cycle_is_certified() {
    let (passed, report) = run(&task(), vec![theta()]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "DECIMATED");
    assert_eq!(
        report["detail"],
        json!({"edges": 3, "b1": 2, "cycle_residuals": ["7/1", "5/1"]})
    );
    assert_eq!(outcomes(&report), all_but(&[]));
    assert_eq!(
        evidence(&report, "paths_are_walks"),
        &json!(sha("[[[0,1],[1,1]],[[2,1]],[[3,1],[4,1]]]"))
    );
    assert_eq!(
        evidence(&report, "labels_are_path_sums"),
        &json!(sha(r#"[["3/1","4/1","2/1"],["3/1","4/1","2/1"]]"#))
    );
    assert_eq!(
        evidence(&report, "cycle_rank_preserved"),
        &json!(sha("[2,2]"))
    );
    // Each reduced cycle as a chain of the task's six edges.
    assert_eq!(
        evidence(&report, "lifted_cycles_span_h1"),
        &json!(sha(concat!(
            r#"[["1/1","1/1","1/1","0/1","0/1","0/1"],"#,
            r#"["1/1","1/1","0/1","1/1","1/1","0/1"]]"#
        )))
    );
    // The degree of each reduced vertex, by name.
    assert_eq!(
        evidence(&report, "strictly_smaller_without_leaves"),
        &json!(sha("[[0,3],[2,3]]"))
    );
}

#[test]
fn a_path_may_take_an_edge_backwards() {
    let reply = reduced(
        json!([[0, 2], [0, 2], [2, 0]]),
        json!([3, -4, 2]),
        json!([[[0, 1], [1, 1]], [[2, -1]], [[3, 1], [4, 1]]]),
    );
    let (passed, report) = run(&task(), vec![reply]);
    assert!(passed);
    assert_eq!(report["detail"]["cycle_residuals"], json!(["-7/1", "5/1"]));
    assert_eq!(
        evidence(&report, "labels_are_path_sums"),
        &json!(sha(r#"[["3/1","-4/1","2/1"],["3/1","-4/1","2/1"]]"#))
    );
    assert_eq!(
        evidence(&report, "lifted_cycles_span_h1"),
        &json!(sha(concat!(
            r#"[["-1/1","-1/1","-1/1","0/1","0/1","0/1"],"#,
            r#"["1/1","1/1","0/1","1/1","1/1","0/1"]]"#
        )))
    );
}

#[test]
fn a_cycle_of_degree_two_vertices_shrinks_to_one_loop() {
    let loop_at_zero = reduced(
        json!([[0, 0]]),
        json!([7]),
        json!([[[0, 1], [1, 1], [2, 1]]]),
    );
    let (passed, report) = run(&triangle(), vec![loop_at_zero]);
    assert!(passed);
    assert_eq!(
        report["detail"],
        json!({"edges": 1, "b1": 1, "cycle_residuals": ["7/1"]})
    );
    // A loop counts twice toward the degree of its vertex.
    assert_eq!(
        evidence(&report, "strictly_smaller_without_leaves"),
        &json!(sha("[[0,2]]"))
    );
}

#[test]
fn a_loop_that_goes_twice_round_a_cycle_still_spans_it() {
    // The span is taken over the rationals, so twice a cycle spans what the cycle does.
    let twice = reduced(
        json!([[0, 0]]),
        json!([14]),
        json!([[[0, 1], [1, 1], [2, 1], [0, 1], [1, 1], [2, 1]]]),
    );
    let (passed, report) = run(&triangle(), vec![twice]);
    assert!(passed);
    assert_eq!(report["detail"]["cycle_residuals"], json!(["14/1"]));
    // Every step on an edge counts, not the last one alone.
    assert_eq!(
        evidence(&report, "lifted_cycles_span_h1"),
        &json!(sha(r#"[["2/1","2/1","2/1"]]"#))
    );
}

#[test]
fn a_path_that_is_not_a_walk_between_its_ends_fails_the_first_check() {
    // The steps of the first path in the other order: the same sum, starting at vertex 1.
    let mut swapped = theta();
    swapped["paths"][0] = json!([[1, 1], [0, 1]]);
    let report = refused_for(&task(), swapped, &["paths_are_walks"]);
    assert_eq!(
        evidence(&report, "paths_are_walks"),
        &json!(sha("[[[1,1],[0,1]],[[2,1]],[[3,1],[4,1]]]"))
    );
    // A path that stops one vertex short of its edge's head.
    let mut short = theta();
    short["paths"][0] = json!([[0, 1]]);
    short["labels"][0] = json!(1);
    refused_for(&task(), short, &["paths_are_walks"]);
    // A walk between the right ends, written under an edge that names them the other way round.
    let mut turned = theta();
    turned["edges"][1] = json!([0, 2]);
    refused_for(&task(), turned, &["paths_are_walks"]);
    // Every path is checked, not only the first.
    let mut last = theta();
    last["paths"][2] = json!([[4, 1], [3, 1]]);
    refused_for(&task(), last, &["paths_are_walks"]);
}

#[test]
fn a_label_that_is_not_the_sum_along_its_path_fails() {
    let mut reply = theta();
    reply["labels"][2] = json!("5/2");
    let report = refused_for(&task(), reply, &["labels_are_path_sums"]);
    assert_eq!(
        evidence(&report, "labels_are_path_sums"),
        &json!(sha(r#"[["3/1","4/1","5/2"],["3/1","4/1","2/1"]]"#))
    );
    assert_eq!(report["detail"]["cycle_residuals"], json!(["7/1", "11/2"]));
}

#[test]
fn a_reduced_graph_with_fewer_or_more_cycles_fails() {
    // Without the walk through vertex 3 one cycle is gone.
    let fewer = reduced(
        json!([[0, 2], [2, 0]]),
        json!([3, 4]),
        json!([[[0, 1], [1, 1]], [[2, 1]]]),
    );
    let report = refused_for(
        &task(),
        fewer,
        &["cycle_rank_preserved", "lifted_cycles_span_h1"],
    );
    assert_eq!(
        evidence(&report, "cycle_rank_preserved"),
        &json!(sha("[1,2]"))
    );
    assert_eq!(report["detail"]["b1"], 2);
    assert_eq!(report["detail"]["cycle_residuals"], json!(["7/1"]));
    // With a loop round the first triangle added there is one cycle too many, and the three
    // still span the task's two.
    let mut more = theta();
    more["edges"]
        .as_array_mut()
        .expect("edges")
        .push(json!([0, 0]));
    more["labels"]
        .as_array_mut()
        .expect("labels")
        .push(json!(7));
    more["paths"]
        .as_array_mut()
        .expect("paths")
        .push(json!([[0, 1], [1, 1], [2, 1]]));
    let report = refused_for(&task(), more, &["cycle_rank_preserved"]);
    assert_eq!(
        evidence(&report, "cycle_rank_preserved"),
        &json!(sha("[3,2]"))
    );
}

#[test]
fn reduced_cycles_that_repeat_one_cycle_of_the_task_do_not_span_it() {
    // Two reduced edges both stand for the shared edge: two cycles, both the first triangle.
    let reply = reduced(
        json!([[0, 2], [2, 0], [2, 0]]),
        json!([3, 4, 4]),
        json!([[[0, 1], [1, 1]], [[2, 1]], [[2, 1]]]),
    );
    let report = refused_for(&task(), reply, &["lifted_cycles_span_h1"]);
    let row = r#"["1/1","1/1","1/1","0/1","0/1","0/1"]"#;
    assert_eq!(
        evidence(&report, "lifted_cycles_span_h1"),
        &json!(sha(&format!("[{row},{row}]")))
    );
}

#[test]
fn a_graph_that_is_no_smaller_fails_the_last_check() {
    let itself = reduced(
        json!([[0, 1], [1, 2], [2, 0]]),
        json!([1, 2, 4]),
        json!([[[0, 1]], [[1, 1]], [[2, 1]]]),
    );
    let report = refused_for(&triangle(), itself, &["strictly_smaller_without_leaves"]);
    assert_eq!(
        evidence(&report, "strictly_smaller_without_leaves"),
        &json!(sha("[[0,2],[1,2],[2,2]]"))
    );
    assert_eq!(report["detail"]["edges"], 3);
    // One edge fewer is enough.
    let merged = reduced(
        json!([[0, 2], [2, 0]]),
        json!([3, 4]),
        json!([[[0, 1], [1, 1]], [[2, 1]]]),
    );
    let (passed, report) = run(&triangle(), vec![merged]);
    assert!(passed);
    assert_eq!(report["detail"]["edges"], 2);
}

#[test]
fn a_smaller_graph_that_keeps_a_leaf_fails_the_last_check() {
    let mut reply = theta();
    reply["edges"]
        .as_array_mut()
        .expect("edges")
        .push(json!([3, 4]));
    reply["labels"]
        .as_array_mut()
        .expect("labels")
        .push(json!(6));
    reply["paths"]
        .as_array_mut()
        .expect("paths")
        .push(json!([[5, 1]]));
    // The tail hangs off vertex 3, which the reduced graph reaches by no other edge.
    let report = refused_for(&task(), reply, &["strictly_smaller_without_leaves"]);
    assert_eq!(
        evidence(&report, "strictly_smaller_without_leaves"),
        &json!(sha("[[0,3],[2,3],[3,1],[4,1]]"))
    );
    // A loop with a tail: the loop's vertex has degree 3 and the tail's end degree 1.
    let tailed = json!({"edges": [[0, 1], [1, 2], [2, 0], [0, 3], [3, 4]],
                        "labels": [1, 2, 4, 1, 1]});
    let reply = reduced(
        json!([[0, 0], [0, 3]]),
        json!([7, 1]),
        json!([[[0, 1], [1, 1], [2, 1]], [[3, 1]]]),
    );
    let report = refused_for(&tailed, reply, &["strictly_smaller_without_leaves"]);
    assert_eq!(
        evidence(&report, "strictly_smaller_without_leaves"),
        &json!(sha("[[0,3],[3,1]]"))
    );
}

#[test]
fn a_reply_the_host_cannot_read_is_malformed() {
    assert_eq!(
        malformed(&task(), vec![json!("decimated")]),
        "reply must be an object"
    );
    let lists = "edges, labels and paths must be lists";
    assert_eq!(malformed(&task(), vec![json!({})]), lists);
    for missing in ["edges", "labels", "paths"] {
        let mut reply = theta();
        reply.as_object_mut().expect("a reply").remove(missing);
        assert_eq!(malformed(&task(), vec![reply]), lists, "{missing}");
        let mut reply = theta();
        reply[missing] = json!({});
        assert_eq!(malformed(&task(), vec![reply]), lists, "{missing}");
    }
    let counts = "one label and one path per reduced edge, and at least one edge";
    assert_eq!(
        malformed(&task(), vec![reduced(json!([]), json!([]), json!([]))]),
        counts
    );
    let mut labels = theta();
    labels["labels"] = json!([3, 4]);
    assert_eq!(malformed(&task(), vec![labels]), counts);
    let mut paths = theta();
    paths["paths"]
        .as_array_mut()
        .expect("paths")
        .push(json!([[5, 1]]));
    assert_eq!(malformed(&task(), vec![paths]), counts);
    let (_, report) = run(&task(), vec![json!({})]);
    assert_eq!(report["predicates"], json!([]));
}

#[test]
fn reduced_edges_labels_and_paths_are_read_exactly() {
    let with = |key: &str, at: usize, value: Value| {
        let mut reply = theta();
        reply[key][at] = value;
        malformed(&task(), vec![reply])
    };
    let pairs = "reduced edges must be pairs of exact integers";
    assert_eq!(with("edges", 0, json!([0, 2, 0])), pairs);
    assert_eq!(with("edges", 1, json!([2])), pairs);
    assert_eq!(with("edges", 2, json!([2, "0"])), pairs);
    assert_eq!(with("edges", 2, json!([2.0, 0])), pairs);
    assert_eq!(with("edges", 2, json!(2)), pairs);
    let known = "reduced vertices must be vertices of the task";
    assert_eq!(with("edges", 0, json!([0, 5])), known);
    assert_eq!(with("edges", 0, json!([-1, 2])), known);
    let labels = "reduced labels must be exact rationals";
    assert_eq!(with("labels", 0, json!(3.0)), labels);
    assert_eq!(with("labels", 2, json!("two")), labels);
    let step = "a chain step is [edge, sign] with the edge in range and sign 1 or -1";
    assert_eq!(with("paths", 0, json!([[0, 1], [6, 1]])), step);
    assert_eq!(with("paths", 1, json!([[2, 0]])), step);
    assert_eq!(
        with("paths", 2, json!([])),
        "a chain must be a nonempty list of steps"
    );
    // Edges are read before labels, and labels before paths.
    let mut reply = theta();
    reply["edges"][0] = json!([0, 5]);
    reply["labels"][0] = json!(3.0);
    reply["paths"][0] = json!([]);
    assert_eq!(malformed(&task(), vec![reply.clone()]), known);
    reply["edges"][0] = json!([0, 2]);
    assert_eq!(malformed(&task(), vec![reply]), labels);
}

#[test]
fn a_missing_reply_is_refused() {
    let outcome = judge(&request(&task(), &[None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    assert_eq!(
        bad_task(json!({"labels": [1]})),
        "edges must be a nonempty list of pairs of exact integers"
    );
    assert_eq!(
        bad_task(json!({"edges": [[1, 2]], "labels": [1]})),
        "vertices must be 0..n-1"
    );
    assert_eq!(
        bad_task(json!({"edges": [[0, 1]], "labels": [1, 2]})),
        "labels must be one exact rational per edge"
    );
}
