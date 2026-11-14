//! WF46, boundary sufficiency and gluing diagnostic: which runs are locally accepted, what the
//! packet and the glued trace say of each, and whether the packet decides the glued trace.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf46-tests:v1

use pfp_operads::families::wf46::{FAMILY, MAX_RUNS};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Give one potential per patch; the host glues them on the packet.";

/// A square 0-1-2-3 whose values sum to zero round it. Each patch is two opposite sides, so
/// each patch potential has two parts that the patch itself does not relate. The packet is
/// the vertices 0 and 1.
fn square(runs: usize) -> Value {
    json!({"statement": STATEMENT,
           "edges": [[0, 1], [1, 2], [2, 3], [3, 0]], "labels": [1, 1, 1, -3],
           "patches": [[0, 2], [1, 3]], "packet": [0, 1], "runs": runs})
}

/// A triangle whose first patch is the edge 0-1 and whose second is the other two edges, so
/// the first potential says nothing at vertex 2.
fn triangle(last: i64, packet: Value) -> Value {
    json!({"edges": [[0, 1], [1, 2], [2, 0]], "labels": [1, 2, last],
           "patches": [[0], [1, 2]], "packet": packet, "runs": 1})
}

fn prompt(runs: usize) -> String {
    format!(
        concat!(
            "WF46 Boundary sufficiency and gluing diagnostic. {}\n",
            r#"{{"edges":[[0,1],[1,2],[2,3],[3,0]],"labels":[1,1,1,-3],"#,
            r#""packet":[0,1],"patches":[[0,2],[1,3]],"runs":{}}}"#
        ),
        STATEMENT, runs
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
    json!({"workflow": "WF46", "task": task, "replies": replies}).to_string()
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

/// The first patch's potential: its side 0-1 from 0, and its side 2-3 from `at_two`. It
/// explains the whole square exactly when `at_two` is 2.
fn first(at_two: i64) -> Value {
    json!([[0, 0], [1, 1], [2, at_two], [3, at_two + 1]])
}

/// The second patch's potential: its side 1-2 from `at_one`, and its side 3-0 ending at 0.
/// It differs from `first(_)` by a constant on the packet exactly when `at_one` is 1.
fn second(at_one: i64) -> Value {
    json!([[1, at_one], [2, at_one + 1], [3, 3], [0, 0]])
}

/// The packet passes and the glued trace passes.
fn sound() -> Value {
    json!([first(2), second(1)])
}

/// The packet passes and the glued trace fails.
fn hidden() -> Value {
    json!([first(5), second(1)])
}

/// The packet fails and the glued trace passes.
fn alarm() -> Value {
    json!([first(2), second(4)])
}

/// The packet fails and the glued trace fails.
fn caught() -> Value {
    json!([first(5), second(4)])
}

fn row(run: usize, packet: bool, global: bool) -> Value {
    json!({"run": run, "local": true, "packet": packet, "global": global})
}

fn unaccepted(run: usize) -> Value {
    json!({"run": run, "local": false})
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF46",
            "Boundary sufficiency and gluing diagnostic",
            "glued_trace_global_evaluator"
        )
    );
}

#[test]
fn every_run_is_asked_the_task_as_written() {
    let first = ask(&square(3), vec![]);
    assert_eq!(first["stage"], "run:0");
    assert_eq!(first["prompt"], prompt(3));
    assert_eq!(first["prompt_sha256"], sha(&prompt(3)));
    let third = ask(&square(3), vec![sound(), hidden()]);
    assert_eq!(third["stage"], "run:2");
    assert_eq!(third["prompt"], prompt(3));
    assert_eq!(
        ask(&square(3), vec![sound(), hidden(), sound()]),
        Value::Null
    );
}

#[test]
fn runs_whose_packet_and_glued_trace_agree_are_certified() {
    let (passed, report) = run(&square(3), vec![sound(), caught(), sound()]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "BOUNDARY_SUFFICIENT");
    assert_eq!(
        report["detail"],
        json!({"completed": "3/3", "backlog": 0, "ngd": "1/3",
               "runs": [row(0, true, true), row(1, false, false), row(2, true, true)]})
    );
    let rows = concat!(
        r#"[{"global":true,"local":true,"packet":true,"run":0},"#,
        r#"{"global":false,"local":true,"packet":false,"run":1},"#,
        r#"{"global":true,"local":true,"packet":true,"run":2}]"#
    );
    assert_eq!(
        report["predicates"],
        json!([{"name": "ngd_defined", "passed": true, "evidence_sha256": sha(rows)},
               {"name": "packet_decides_global", "passed": true, "evidence_sha256": sha("0")}])
    );
}

#[test]
fn ngd_is_the_share_of_accepted_runs_whose_glued_trace_fails() {
    let (_, none) = run(&square(1), vec![sound()]);
    assert_eq!(none["detail"]["ngd"], "0/1");
    let (passed, every) = run(&square(2), vec![caught(), caught()]);
    assert!(passed);
    assert_eq!(every["code"], "BOUNDARY_SUFFICIENT");
    assert_eq!(every["detail"]["ngd"], "1/1");
    let (_, half) = run(&square(4), vec![sound(), caught(), caught(), sound()]);
    assert_eq!(half["detail"]["ngd"], "1/2");
}

#[test]
fn a_glued_trace_that_fails_behind_a_passing_packet_is_a_hidden_failure() {
    let (passed, report) = run(&square(4), vec![sound(), hidden(), caught(), hidden()]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "BOUNDARY_INSUFFICIENT");
    assert_eq!(
        report["detail"],
        json!({"completed": "4/4", "backlog": 0, "ngd": "3/4", "hidden_failures": 2,
               "runs": [row(0, true, true), row(1, true, false), row(2, false, false),
                        row(3, true, false)]})
    );
    assert_eq!(
        outcomes(&report),
        [("ngd_defined", true), ("packet_decides_global", false)]
    );
    assert_eq!(evidence(&report, "packet_decides_global"), &json!(sha("2")));
}

#[test]
fn a_packet_that_fails_before_a_passing_glued_trace_does_not_decide_it_either() {
    let (passed, report) = run(&square(2), vec![sound(), alarm()]);
    assert!(!passed);
    assert_eq!(report["code"], "BOUNDARY_INSUFFICIENT");
    assert_eq!(report["detail"]["hidden_failures"], 0);
    assert_eq!(report["detail"]["ngd"], "0/1");
    assert_eq!(
        report["detail"]["runs"],
        json!([row(0, true, true), row(1, false, true)])
    );
    assert_eq!(evidence(&report, "packet_decides_global"), &json!(sha("0")));
}

#[test]
fn a_constant_added_to_a_patch_potential_changes_nothing() {
    let lifted = json!([[1, 11], [2, 12], [3, 13], [0, 10]]);
    let lowered = json!([[0, "-1/2"], [1, "1/2"], [2, "3/2"], [3, "5/2"]]);
    let (passed, report) = run(&square(1), vec![json!([lowered, lifted])]);
    assert!(passed);
    assert_eq!(report["detail"]["runs"], json!([row(0, true, true)]));
}

#[test]
fn a_potential_that_misses_its_patch_is_not_locally_accepted() {
    // The first potential breaks its own side 2-3; then the second its side 1-2.
    let wrong_first = json!([[[0, 0], [1, 1], [2, 2], [3, 4]], second(1)]);
    let wrong_second = json!([first(2), [[1, 1], [2, 3], [3, 3], [0, 0]]]);
    // A potential that leaves out a vertex of its patch.
    let short_first = json!([[[0, 0], [1, 1], [2, 2]], second(1)]);
    let short_second = json!([first(2), [[1, 1], [2, 2], [3, 3]]]);
    let (passed, report) = run(
        &square(5),
        vec![
            wrong_first,
            wrong_second,
            short_first,
            short_second,
            hidden(),
        ],
    );
    assert!(!passed);
    assert_eq!(
        report["detail"]["runs"],
        json!([
            unaccepted(0),
            unaccepted(1),
            unaccepted(2),
            unaccepted(3),
            row(4, true, false)
        ])
    );
    // Only the accepted run counts.
    assert_eq!(report["detail"]["ngd"], "1/1");
    assert_eq!(report["detail"]["hidden_failures"], 1);
    assert_eq!(report["detail"]["completed"], "5/5");
}

#[test]
fn a_potential_covers_exactly_the_vertices_of_its_patch() {
    let task = triangle(-3, json!([0, 1]));
    let good = json!([[[0, 0], [1, 1]], [[1, 1], [2, 3], [0, 0]]]);
    let (passed, report) = run(&task, vec![good]);
    assert!(passed);
    assert_eq!(report["detail"]["runs"], json!([row(0, true, true)]));
    // Vertex 2 is not on the first patch.
    let extra = json!([[[0, 0], [1, 1], [2, 3]], [[1, 1], [2, 3], [0, 0]]]);
    let (refused, report) = run(&task, vec![extra]);
    assert!(!refused);
    assert_eq!(report["code"], "NGD_UNDEFINED");
    assert_eq!(report["detail"]["runs"], json!([unaccepted(0)]));
}

#[test]
fn a_vertex_listed_twice_keeps_its_last_value() {
    let repeated = json!([[0, 9], [1, 1], [2, 2], [3, 3], [0, 0]]);
    let (passed, report) = run(&square(1), vec![json!([repeated, second(1)])]);
    assert!(passed);
    assert_eq!(report["detail"]["runs"], json!([row(0, true, true)]));
    let spoiled = json!([[0, 0], [1, 1], [2, 2], [3, 3], [0, 9]]);
    let (_, report) = run(&square(1), vec![json!([spoiled, second(1)])]);
    assert_eq!(report["detail"]["runs"], json!([unaccepted(0)]));
}

#[test]
fn the_second_potential_is_shifted_to_the_first_where_the_first_says_nothing() {
    // The second potential sits 10 above the first: only the shift makes vertex 2 fit.
    let reply = json!([[[0, 0], [1, 1]], [[1, 11], [2, 13], [0, 10]]]);
    let (passed, report) = run(&triangle(-3, json!([0, 1])), vec![reply.clone()]);
    assert!(passed);
    assert_eq!(report["detail"]["runs"], json!([row(0, true, true)]));
    assert_eq!(report["detail"]["ngd"], "0/1");
    let (one, report) = run(&triangle(-3, json!([1])), vec![reply]);
    assert!(one);
    assert_eq!(report["detail"]["runs"], json!([row(0, true, true)]));
}

#[test]
fn the_shift_is_taken_at_the_first_packet_vertex() {
    // Round this triangle the values sum to 1, so the two potentials cannot agree at both
    // shared vertices. The second potential here agrees with the first at vertex 1.
    let reply = json!([[[0, 0], [1, 1]], [[1, 1], [2, 3], [0, 1]]]);
    // A packet of one vertex always passes, and the glued trace breaks at the other.
    for packet in [json!([0]), json!([1])] {
        let (passed, report) = run(&triangle(-2, packet.clone()), vec![reply.clone()]);
        assert!(!passed, "{packet}");
        assert_eq!(report["code"], "BOUNDARY_INSUFFICIENT");
        assert_eq!(report["detail"]["runs"], json!([row(0, true, false)]));
        assert_eq!(report["detail"]["hidden_failures"], 1);
    }
    // Both shared vertices in the packet: the packet fails with the glued trace.
    for packet in [json!([0, 1]), json!([1, 0]), json!([1, 1, 0])] {
        let (passed, report) = run(&triangle(-2, packet.clone()), vec![reply.clone()]);
        assert!(passed, "{packet}");
        assert_eq!(report["code"], "BOUNDARY_SUFFICIENT");
        assert_eq!(report["detail"]["runs"], json!([row(0, false, false)]));
        assert_eq!(report["detail"]["ngd"], "1/1");
    }
}

#[test]
fn the_first_packet_vertex_alone_fixes_the_shift() {
    // Edges 1 and 2 both join the vertices 1 and 2, one in each patch, and the second patch
    // also holds the edge 0-3. Its potential has two parts: one on 1 and 2, one on 0 and 3.
    // Only the part on 0 and 3 reaches a vertex the first potential says nothing about.
    let fork = |packet: Value| {
        json!({"edges": [[0, 1], [1, 2], [1, 2], [0, 3]], "labels": [1, 2, 2, 5],
               "patches": [[0, 1], [2, 3]], "packet": packet, "runs": 1})
    };
    // The second potential agrees with the first at vertex 0 and sits 6 above it at vertex 1.
    let reply = json!([[[0, 0], [1, 1], [2, 3]], [[1, 7], [2, 9], [0, 0], [3, 5]]]);
    let (_, report) = run(&fork(json!([0, 1])), vec![reply.clone()]);
    assert_eq!(report["detail"]["runs"], json!([row(0, false, true)]));
    let (_, report) = run(&fork(json!([1, 0])), vec![reply.clone()]);
    assert_eq!(report["detail"]["runs"], json!([row(0, false, false)]));
    let (_, report) = run(&fork(json!([0])), vec![reply.clone()]);
    assert_eq!(report["detail"]["runs"], json!([row(0, true, true)]));
    let (_, report) = run(&fork(json!([1])), vec![reply]);
    assert_eq!(report["detail"]["runs"], json!([row(0, true, false)]));
}

#[test]
fn a_run_with_no_reply_is_left_in_the_backlog() {
    let outcome = judge(&request(
        &square(4),
        &[Some(sound()), None, Some(caught()), None],
    ));
    let Outcome::Pass { result } = outcome else {
        panic!("expected a certified run, got {outcome:?}");
    };
    assert_eq!(result["code"], "BOUNDARY_SUFFICIENT");
    assert_eq!(
        result["detail"],
        json!({"completed": "2/4", "backlog": 2, "ngd": "1/2",
               "runs": [row(0, true, true), row(2, false, false)]})
    );
    let stages: Vec<&str> = result["asked"]
        .as_array()
        .expect("asked")
        .iter()
        .filter_map(|asked| asked["stage"].as_str())
        .collect();
    assert_eq!(stages, ["run:0", "run:1", "run:2", "run:3"]);
}

#[test]
fn with_no_accepted_run_ngd_is_undefined() {
    let outcome = judge(&request(&square(2), &[None, None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NGD_UNDEFINED");
    assert_eq!(
        result["detail"],
        json!({"completed": "0/2", "backlog": 2, "runs": [], "ngd": null})
    );
    assert_eq!(
        result["predicates"],
        json!([{"name": "ngd_defined", "passed": false, "evidence_sha256": sha("[]")}])
    );
    let unaccepted_only = json!([first(2), [[1, 1], [2, 3], [3, 3], [0, 0]]]);
    let (passed, report) = run(&square(1), vec![unaccepted_only]);
    assert!(!passed);
    assert_eq!(report["code"], "NGD_UNDEFINED");
    assert_eq!(
        report["detail"],
        json!({"completed": "1/1", "backlog": 0, "runs": [unaccepted(0)], "ngd": null})
    );
    assert_eq!(
        evidence(&report, "ngd_defined"),
        &json!(sha(r#"[{"local":false,"run":0}]"#))
    );
}

#[test]
fn a_reply_the_host_cannot_read_ends_the_run_as_malformed() {
    let patches = "one potential per patch";
    assert_eq!(malformed(&square(1), vec![json!([first(2)])]), patches);
    assert_eq!(
        malformed(&square(1), vec![json!([first(2), second(1), second(1)])]),
        patches
    );
    assert_eq!(
        malformed(&square(1), vec![json!({"first": first(2)})]),
        patches
    );
    assert_eq!(malformed(&square(1), vec![json!("glued")]), patches);
    let entries = "a patch potential is a list of [vertex, value] with exact entries";
    for bad in [
        json!({"0": 0}),
        json!([[0, 0.5]]),
        json!([["0", 0]]),
        json!([[0.0, 0]]),
        json!([[0]]),
        json!([[0, 0, 0]]),
        json!([0, 0]),
        json!([[0, 0], [1, "x"]]),
    ] {
        assert_eq!(
            malformed(&square(1), vec![json!([bad.clone(), second(1)])]),
            entries,
            "{bad}"
        );
        assert_eq!(
            malformed(&square(1), vec![json!([first(2), bad.clone()])]),
            entries,
            "{bad}"
        );
    }
    // A later run that cannot be read ends the whole run.
    assert_eq!(
        malformed(&square(3), vec![sound(), json!("glued")]),
        patches
    );
    let (_, report) = run(&square(3), vec![sound(), json!("glued")]);
    assert_eq!(report["predicates"], json!([]));
    assert_eq!(report["asked"].as_array().expect("asked").len(), 2);
}

#[test]
fn the_patches_are_two_lists_that_hold_every_edge_once() {
    let with = |patches: Value| {
        let mut task = square(1);
        task["patches"] = patches;
        bad_task(task)
    };
    let two = "patches must be two lists of edge indices";
    assert_eq!(with(json!([[0, 1, 2, 3]])), two);
    assert_eq!(with(json!([[0], [1], [2, 3]])), two);
    assert_eq!(with(json!([[0, 2], [1, 4]])), two);
    assert_eq!(with(json!([[0, 2], [1, -3]])), two);
    assert_eq!(with(json!([[0, "2"], [1, 3]])), two);
    assert_eq!(with(json!([[0, 2], 13])), two);
    assert_eq!(with(json!({"a": [0, 2], "b": [1, 3]})), two);
    let mut missing = square(1);
    missing.as_object_mut().expect("a task").remove("patches");
    assert_eq!(bad_task(missing), two);
    let once = "patches must hold every edge exactly once";
    assert_eq!(with(json!([[0, 2], [1]])), once);
    assert_eq!(with(json!([[0, 2], [1, 3, 0]])), once);
    assert_eq!(with(json!([[0, 0, 2], [1]])), once);
    assert_eq!(with(json!([[], []])), once);
    // The order of the edges within a patch does not matter.
    let mut task = square(1);
    task["patches"] = json!([[2, 0], [3, 1]]);
    assert_eq!(ask(&task, vec![])["stage"], "run:0");
}

#[test]
fn the_packet_is_a_nonempty_list_of_vertices_on_both_patches() {
    let with = |packet: Value| bad_task(triangle(-3, packet));
    let list = "packet must be a nonempty list of exact integers";
    assert_eq!(with(json!([])), list);
    assert_eq!(with(json!([0, "1"])), list);
    assert_eq!(with(json!([0.0])), list);
    assert_eq!(with(json!(0)), list);
    let mut missing = triangle(-3, json!([0]));
    missing.as_object_mut().expect("a task").remove("packet");
    assert_eq!(bad_task(missing), list);
    // Vertex 2 is on the second patch only.
    let both = "packet vertices must lie on both patches";
    assert_eq!(with(json!([2])), both);
    assert_eq!(with(json!([0, 2])), both);
    assert_eq!(with(json!([7])), both);
    assert_eq!(with(json!([-1])), both);
    // With every edge in one patch, no vertex is on the other.
    let mut lopsided = triangle(-3, json!([0]));
    lopsided["patches"] = json!([[0, 1, 2], []]);
    assert_eq!(bad_task(lopsided), both);
}

#[test]
fn a_task_asks_for_one_to_sixty_four_runs() {
    assert_eq!(MAX_RUNS, 64);
    let runs = "runs must be an exact integer from 1 to 64";
    assert_eq!(bad_task(square(0)), runs);
    assert_eq!(bad_task(square(65)), runs);
    for stated in [json!("3"), json!(3.0), json!(-1), json!(null)] {
        let mut task = square(1);
        task["runs"] = stated;
        assert_eq!(bad_task(task), runs);
    }
    let mut missing = square(1);
    missing.as_object_mut().expect("a task").remove("runs");
    assert_eq!(bad_task(missing), runs);
    assert_eq!(ask(&square(64), vec![sound(); 63])["stage"], "run:63");
    assert_eq!(ask(&square(64), vec![sound(); 64]), Value::Null);
    assert_eq!(ask(&square(1), vec![])["stage"], "run:0");
}

#[test]
fn a_task_is_read_in_order() {
    // Graph, labels, patches, packet, runs, then whether the packet is shared.
    let mut task = json!({"edges": [[0, 2]], "labels": [], "patches": 0, "packet": [],
                          "runs": 0});
    assert_eq!(bad_task(task.clone()), "vertices must be 0..n-1");
    task["edges"] = json!([[0, 1], [1, 2], [2, 0]]);
    assert_eq!(
        bad_task(task.clone()),
        "labels must be one exact rational per edge"
    );
    task["labels"] = json!([1, 2, -3]);
    assert_eq!(
        bad_task(task.clone()),
        "patches must be two lists of edge indices"
    );
    task["patches"] = json!([[0], [1]]);
    assert_eq!(
        bad_task(task.clone()),
        "patches must hold every edge exactly once"
    );
    task["patches"] = json!([[0], [1, 2]]);
    assert_eq!(
        bad_task(task.clone()),
        "packet must be a nonempty list of exact integers"
    );
    task["packet"] = json!([2]);
    assert_eq!(
        bad_task(task.clone()),
        "runs must be an exact integer from 1 to 64"
    );
    task["runs"] = json!(1);
    assert_eq!(bad_task(task), "packet vertices must lie on both patches");
}
