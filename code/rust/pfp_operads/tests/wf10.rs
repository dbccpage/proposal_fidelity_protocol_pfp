//! WF10, local-to-global obstruction certificate: a potential that glues the edge values, the
//! cycle that forbids one, and what each patch says on its own.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf10-tests:v1

use pfp_operads::families::wf10::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str =
    "Glue the edge values into one potential, or show the cycle that forbids it.";

/// A triangle 0-1-2 whose edges name the vertices in the order 2, 0, 1, and a tail 1-3. Round
/// the triangle the values sum to `1 + 1/2 + last`.
fn task(last: &str) -> Value {
    json!({"statement": STATEMENT,
           "edges": [[2, 0], [0, 1], [1, 2], [1, 3]],
           "labels": [1, "1/2", last, 2],
           "patches": [[0, 1], [0, 1, 2], [3]]})
}

/// The values are a coboundary: the potential 1, 3/2, 0, 7/2 explains them.
fn glued() -> Value {
    task("-3/2")
}

/// Round the triangle the values sum to 5/2.
fn twisted() -> Value {
    task("1")
}

fn prompt(last: &str) -> String {
    format!(
        concat!(
            "WF10 Local-to-global obstruction certificate. {}\n",
            r#"{{"edges":[[2,0],[0,1],[1,2],[1,3]],"labels":[1,"1/2","{}",2],"#,
            r#""patches":[[0,1],[0,1,2],[3]]}}"#
        ),
        STATEMENT, last
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
    json!({"workflow": "WF10", "task": task, "replies": replies}).to_string()
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

fn triangle() -> Value {
    json!({"obstruction": [[0, 1], [1, 1], [2, 1]]})
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF10",
            "Local-to-global obstruction certificate",
            "cochain_gluing_or_cycle_obstruction"
        )
    );
}

#[test]
fn the_one_question_is_the_task_as_written() {
    let first = ask(&glued(), vec![]);
    assert_eq!(first["stage"], "solve");
    assert_eq!(first["prompt"], prompt("-3/2"));
    assert_eq!(first["prompt_sha256"], sha(&prompt("-3/2")));
    assert_eq!(
        ask(&glued(), vec![json!({"potential": [0, 0, 0, 0]})]),
        Value::Null
    );
}

#[test]
fn a_potential_that_explains_every_edge_is_certified() {
    let (passed, report) = run(&glued(), vec![json!({"potential": [1, "3/2", 0, "7/2"]})]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "GLUED");
    assert_eq!(
        report["detail"],
        json!({"residual_support": [], "local_sections": [true, true, true]})
    );
    assert_eq!(
        report["predicates"],
        json!([{"name": "zero_residual_on_every_edge", "passed": true,
                "evidence_sha256": sha("[]")}])
    );
    assert_eq!(report["every_predicate_passed"], true);
}

#[test]
fn a_potential_shifted_by_a_constant_glues_as_well() {
    let (passed, report) = run(
        &glued(),
        vec![json!({"potential": ["-1/3", "1/6", "-4/3", "13/6"]})],
    );
    assert!(passed);
    assert_eq!(report["code"], "GLUED");
}

#[test]
fn a_potential_is_refused_with_the_edges_it_leaves_unexplained() {
    let (passed, report) = run(&glued(), vec![json!({"potential": [1, "3/2", 0, 3]})]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "ZERO_RESIDUAL_ON_EVERY_EDGE");
    assert_eq!(
        report["detail"],
        json!({"residual_support": [3], "local_sections": [true, true, true],
               "failed": ["zero_residual_on_every_edge"]})
    );
    assert_eq!(
        evidence(&report, "zero_residual_on_every_edge"),
        &json!(sha("[3]"))
    );
    // The value at vertex 0 is read on the edges 0 and 1, which both end there.
    let (_, moved) = run(&glued(), vec![json!({"potential": [2, "3/2", 0, "7/2"]})]);
    assert_eq!(moved["detail"]["residual_support"], json!([0, 1]));
    assert_eq!(
        evidence(&moved, "zero_residual_on_every_edge"),
        &json!(sha("[0,1]"))
    );
}

#[test]
fn no_potential_glues_values_that_twist_round_a_cycle() {
    let (passed, report) = run(&twisted(), vec![json!({"potential": [1, "3/2", 0, "7/2"]})]);
    assert!(!passed);
    assert_eq!(report["code"], "ZERO_RESIDUAL_ON_EVERY_EDGE");
    assert_eq!(report["detail"]["residual_support"], json!([2]));
    assert_eq!(
        report["detail"]["local_sections"],
        json!([true, false, true])
    );
}

#[test]
fn a_closed_cycle_with_a_nonzero_sum_stands_as_the_obstruction() {
    let (passed, report) = run(&twisted(), vec![triangle()]);
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "GLOBAL_OBSTRUCTION");
    assert_eq!(
        report["detail"],
        json!({"holonomy": "5/2", "cycle": [[0, 1], [1, 1], [2, 1]],
               "local_sections": [true, false, true]})
    );
    assert_eq!(
        report["predicates"],
        json!([{"name": "witness_is_closed_cycle", "passed": true, "evidence_sha256": sha("{}")},
               {"name": "nonzero_holonomy", "passed": true,
                "evidence_sha256": sha("\"5/2\"")}])
    );
}

#[test]
fn a_cycle_walked_backwards_or_twice_sums_accordingly() {
    let backwards = json!({"obstruction": [[2, -1], [1, -1], [0, -1]]});
    let (passed, report) = run(&twisted(), vec![backwards]);
    assert!(passed);
    assert_eq!(report["detail"]["holonomy"], "-5/2");
    assert_eq!(
        report["detail"]["cycle"],
        json!([[2, -1], [1, -1], [0, -1]])
    );
    let twice = json!({"obstruction": [[0, 1], [1, 1], [2, 1], [0, 1], [1, 1], [2, 1]]});
    let (_, doubled) = run(&twisted(), vec![twice]);
    assert_eq!(doubled["code"], "GLOBAL_OBSTRUCTION");
    assert_eq!(doubled["detail"]["holonomy"], "5/1");
}

#[test]
fn a_chain_that_is_not_closed_is_refused_with_its_boundary_by_vertex_name() {
    // Edge 0 runs from vertex 2 to vertex 0, and edge 3 from vertex 1 to vertex 3.
    let (passed, report) = run(&twisted(), vec![json!({"obstruction": [[0, 1], [3, 1]]})]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "OPEN_CYCLE_WITNESS");
    assert_eq!(
        report["detail"],
        json!({"boundary": {"0": 1, "1": -1, "2": -1, "3": 1},
               "local_sections": [true, false, true]})
    );
    assert_eq!(outcomes(&report), [("witness_is_closed_cycle", false)]);
    assert_eq!(
        evidence(&report, "witness_is_closed_cycle"),
        &json!(sha(r#"{"0":1,"1":-1,"2":-1,"3":1}"#))
    );
    // Two sides of the triangle leave its third side open, however large their sum.
    let (_, sides) = run(&twisted(), vec![json!({"obstruction": [[0, 1], [1, 1]]})]);
    assert_eq!(sides["code"], "OPEN_CYCLE_WITNESS");
    assert_eq!(sides["detail"]["boundary"], json!({"1": 1, "2": -1}));
    let (_, counted) = run(&twisted(), vec![json!({"obstruction": [[3, 1], [3, 1]]})]);
    assert_eq!(counted["detail"]["boundary"], json!({"1": -2, "3": 2}));
}

#[test]
fn a_closed_cycle_that_sums_to_zero_is_no_obstruction() {
    let (passed, report) = run(&glued(), vec![triangle()]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "ZERO_HOLONOMY_WITNESS");
    assert_eq!(
        report["detail"],
        json!({"local_sections": [true, true, true]})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("witness_is_closed_cycle", true),
            ("nonzero_holonomy", false)
        ]
    );
    assert_eq!(
        evidence(&report, "nonzero_holonomy"),
        &json!(sha("\"0/1\""))
    );
    // An edge out and back is closed and sums to zero on any values.
    let (_, retraced) = run(&twisted(), vec![json!({"obstruction": [[3, 1], [3, -1]]})]);
    assert_eq!(retraced["code"], "ZERO_HOLONOMY_WITNESS");
}

#[test]
fn each_patch_is_reported_on_its_own_values_and_decides_nothing() {
    let mut task = twisted();
    task["patches"] = json!([[0, 1, 2], [0, 1, 2, 3], [], [2, 1], [3, 3]]);
    let (passed, report) = run(&task, vec![triangle()]);
    assert!(passed);
    assert_eq!(
        report["detail"]["local_sections"],
        json!([false, false, true, true, true])
    );
    let mut bare = glued();
    bare.as_object_mut().expect("a task").remove("patches");
    let (certified, report) = run(&bare, vec![json!({"potential": [1, "3/2", 0, "7/2"]})]);
    assert!(certified);
    assert_eq!(report["detail"]["local_sections"], json!([]));
}

#[test]
fn a_potential_is_read_before_an_obstruction() {
    let both = json!({"potential": [1, "3/2", 0, "7/2"], "obstruction": [[0, 1], [1, 1], [2, 1]]});
    let (passed, report) = run(&glued(), vec![both.clone()]);
    assert!(passed);
    assert_eq!(report["code"], "GLUED");
    let (refused, report) = run(&twisted(), vec![both]);
    assert!(!refused);
    assert_eq!(report["code"], "ZERO_RESIDUAL_ON_EVERY_EDGE");
}

#[test]
fn a_reply_that_is_a_claim_is_malformed() {
    let neither = "reply must carry a potential or an obstruction cycle, not a claim";
    assert_eq!(malformed(&glued(), vec![json!({})]), neither);
    assert_eq!(
        malformed(&glued(), vec![json!({"claim": "it glues"})]),
        neither
    );
    assert_eq!(
        malformed(&glued(), vec![json!("the values glue")]),
        "reply must be an object"
    );
    assert_eq!(
        malformed(&glued(), vec![json!([1, "3/2", 0, "7/2"])]),
        "reply must be an object"
    );
}

#[test]
fn a_potential_or_chain_the_host_cannot_read_is_malformed() {
    let potential = "potential must be one exact rational per vertex";
    assert_eq!(
        malformed(&glued(), vec![json!({"potential": [1, 2, 3]})]),
        potential
    );
    assert_eq!(
        malformed(&glued(), vec![json!({"potential": [1, 1.5, 0, 3.5]})]),
        potential
    );
    assert_eq!(
        malformed(&glued(), vec![json!({"potential": "flat"})]),
        potential
    );
    assert_eq!(
        malformed(&twisted(), vec![json!({"obstruction": []})]),
        "a chain must be a nonempty list of steps"
    );
    let step = "a chain step is [edge, sign] with the edge in range and sign 1 or -1";
    assert_eq!(
        malformed(&twisted(), vec![json!({"obstruction": [[4, 1]]})]),
        step
    );
    assert_eq!(
        malformed(&twisted(), vec![json!({"obstruction": [[0, 2]]})]),
        step
    );
    assert_eq!(
        malformed(&twisted(), vec![json!({"obstruction": [0, 1, 2]})]),
        step
    );
    let (_, report) = run(&twisted(), vec![json!({"obstruction": [[4, 1]]})]);
    assert_eq!(report["predicates"], json!([]));
}

#[test]
fn a_missing_reply_is_refused() {
    let outcome = judge(&request(&twisted(), &[None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    assert_eq!(
        bad_task(json!({"edges": [], "labels": []})),
        "edges must be a nonempty list of pairs of exact integers"
    );
    assert_eq!(
        bad_task(json!({"edges": [[0, 2]], "labels": [1]})),
        "vertices must be 0..n-1"
    );
    assert_eq!(
        bad_task(json!({"edges": [[0, 1]], "labels": [0.5]})),
        "labels must be one exact rational per edge"
    );
    let patches = "patches must be lists of edge indices";
    for listed in [
        json!([[0, 4]]),
        json!([[0], [-1]]),
        json!([0, 1]),
        json!("all"),
        json!({}),
    ] {
        let mut task = glued();
        task["patches"] = listed.clone();
        assert_eq!(bad_task(task), patches, "{listed}");
    }
    let mut task = glued();
    task["patches"] = json!([]);
    assert_eq!(ask(&task, vec![])["stage"], "solve");
}
