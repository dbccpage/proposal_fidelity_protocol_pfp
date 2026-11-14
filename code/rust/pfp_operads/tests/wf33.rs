//! WF33, recursive re-entry with shared fuel: the plan, each child's binding to its parent, the
//! one fuel counter every question draws on, and the map back to the task's edges.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf33-tests:v1

use pfp_operads::families::wf33::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Repair the labels by delegating disjoint parts to child derivations.";

/// Two triangles sharing an edge, with the first odd, and a separate odd triangle. The least
/// repair flips one of the edges 0, 1 and one of the edges 5, 6, 7.
fn task(fuel: i64) -> Value {
    json!({"statement": STATEMENT,
           "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [4, 5], [5, 6], [6, 4]],
           "labels": [1, 0, 0, 0, 0, 0, 0, 1], "fuel": fuel})
}

const EDGES: &str = "[[0,1],[1,2],[2,0],[2,3],[3,0],[4,5],[5,6],[6,4]]";
const LABELS: &str = "[1,0,0,0,0,0,0,1]";

/// The task without its statement, as the prompt writes it.
fn rest(fuel: i64) -> String {
    format!(r#"{{"edges":{EDGES},"fuel":{fuel},"labels":{LABELS}}}"#)
}

fn prompt(fuel: i64) -> String {
    format!(
        "WF33 Recursive re-entry with shared fuel. {STATEMENT}\n{}",
        rest(fuel)
    )
}

/// The prompt a child's part of the task is put under.
fn part(edges: &str, labels: &str, limit: usize) -> String {
    format!(
        concat!(
            "WF33 Recursive re-entry with shared fuel. {}\n",
            r#"{{"edges":{},"labels":{},"max_attempts":{}}}"#
        ),
        STATEMENT, edges, labels, limit
    )
}

fn task_digest(fuel: i64) -> String {
    sha(&format!(
        r#"{{"edges":{EDGES},"fuel":{fuel},"labels":{LABELS},"statement":"{STATEMENT}"}}"#
    ))
}

/// The receipt of the plan: the digest of the task and the plan as written.
fn root_receipt(fuel: i64, plan: &str) -> String {
    sha(&format!(
        r#"{{"plan":{plan},"root":"{}"}}"#,
        task_digest(fuel)
    ))
}

/// The receipt after a child: the receipt before it, its number, its flips and the fuel left.
fn child_receipt(parent: &str, child: usize, flips: &str, fuel: i64) -> String {
    sha(&format!(
        r#"{{"child":{child},"flips":{flips},"fuel":{fuel},"parent":"{parent}"}}"#
    ))
}

const PLAN: &str = "[[0,1,2,3,4],[5,6,7]]";

fn plan() -> Value {
    json!({"children": [[0, 1, 2, 3, 4], [5, 6, 7]]})
}

fn header(receipt: &str, fuel_in_task: i64, fuel_left: i64) -> Value {
    json!({"parent_receipt": receipt, "task_digest": task_digest(fuel_in_task),
           "fuel": fuel_left})
}

fn flip(edges: &[usize]) -> Value {
    json!({ "flip": edges })
}

/// The replies of the run that certifies with twelve units of fuel.
fn good() -> Vec<Value> {
    let root = root_receipt(12, PLAN);
    let after = child_receipt(&root, 0, "[0]", 9);
    vec![
        plan(),
        header(&root, 12, 10),
        flip(&[0]),
        header(&after, 12, 8),
        flip(&[2]),
    ]
}

/// The good run with one reply replaced.
fn with_reply(at: usize, reply: Value) -> Vec<Value> {
    let mut replies = good();
    replies[at] = reply;
    replies.truncate(at + 1);
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
    json!({"workflow": "WF33", "task": task, "replies": replies}).to_string()
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
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

fn predicate<'r>(report: &'r Value, name: &str) -> &'r Value {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .find(|row| row["name"] == name)
        .unwrap_or_else(|| panic!("no predicate {name}"))
}

fn names(report: &Value) -> Vec<&str> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .filter_map(|row| row["name"].as_str())
        .collect()
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF33",
            "Recursive re-entry with shared fuel",
            "shared_fuel_parent_bound_reentry"
        )
    );
}

#[test]
fn the_plan_is_asked_for_with_the_fuel_left_after_asking() {
    let first = ask(&task(12), vec![]);
    assert_eq!(first["stage"], "plan");
    let expected = format!("{}\nFuel: 11", prompt(12));
    assert_eq!(first["prompt"], expected);
    assert_eq!(first["prompt_sha256"], sha(&expected));
}

#[test]
fn a_child_is_entered_with_its_edges_the_parent_receipt_and_the_fuel_left() {
    let enter = ask(&task(12), good()[..1].to_vec());
    assert_eq!(enter["stage"], "enter:0");
    let expected = format!(
        "{}\nChild 0 edges: [0, 1, 2, 3, 4]\nParent receipt: {}\nFuel: 10",
        prompt(12),
        root_receipt(12, PLAN)
    );
    assert_eq!(enter["prompt"], expected);
    assert_eq!(enter["prompt_sha256"], sha(&expected));
}

#[test]
fn a_bound_child_is_put_its_own_edges_and_labels_as_a_task() {
    let attempt = ask(&task(12), good()[..2].to_vec());
    assert_eq!(attempt["stage"], "child:0:attempt:0");
    assert_eq!(
        attempt["prompt"],
        part("[[0,1],[1,2],[2,0],[2,3],[3,0]]", "[1,0,0,0,0]", 5)
    );
}

#[test]
fn the_second_child_is_entered_under_the_receipt_of_the_first() {
    let enter = ask(&task(12), good()[..3].to_vec());
    assert_eq!(enter["stage"], "enter:1");
    let after = child_receipt(&root_receipt(12, PLAN), 0, "[0]", 9);
    assert_eq!(
        enter["prompt"],
        format!(
            "{}\nChild 1 edges: [5, 6, 7]\nParent receipt: {after}\nFuel: 8",
            prompt(12)
        )
    );
    let attempt = ask(&task(12), good()[..4].to_vec());
    assert_eq!(attempt["stage"], "child:1:attempt:0");
    assert_eq!(attempt["prompt"], part("[[4,5],[5,6],[6,4]]", "[0,0,1]", 5));
}

#[test]
fn two_children_that_share_the_fuel_are_certified() {
    let (passed, report) = run(&task(12), good());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "REENTRY_CERTIFIED");
    let root = root_receipt(12, PLAN);
    let first = child_receipt(&root, 0, "[0]", 9);
    // The second child flips its own edge 2, which is the task's edge 7.
    let last = child_receipt(&first, 1, "[7]", 7);
    assert_eq!(
        report["detail"],
        json!({"flips": [0, 7], "fuel_trace": [12, 11, 10, 9, 8, 7], "receipt": last})
    );
    let digest = task_digest(12);
    let row = |name: &str, evidence: &str| json!({"name": name, "passed": true, "evidence_sha256": sha(evidence)});
    assert_eq!(
        report["predicates"],
        json!([
            row("forward_coverage_partition", PLAN),
            row("child0:parent_bound", &format!("\"{root}\"")),
            row("child0:task_unchanged", &format!("\"{digest}\"")),
            row("child0:fuel_not_reset", r#"{"claimed":10,"left":10}"#),
            row("child0:certified", r#""certificate""#),
            row("child1:parent_bound", &format!("\"{first}\"")),
            row("child1:task_unchanged", &format!("\"{digest}\"")),
            row("child1:fuel_not_reset", r#"{"claimed":8,"left":8}"#),
            row("child1:certified", r#""certificate""#),
            row("backward_solution_map", "[0,7]"),
        ])
    );
    let stages: Vec<&str> = report["asked"]
        .as_array()
        .expect("asked")
        .iter()
        .filter_map(|asked| asked["stage"].as_str())
        .collect();
    assert_eq!(
        stages,
        [
            "plan",
            "enter:0",
            "child:0:attempt:0",
            "enter:1",
            "child:1:attempt:0"
        ]
    );
}

#[test]
fn a_plan_is_read_as_sets_of_edges_and_listed_in_ascending_order() {
    let shuffled = json!({"children": [[4, 2, 0, 0, 1, 3], [7, 5, 6]]});
    let enter = ask(&task(12), vec![shuffled]);
    let text = enter["prompt"].as_str().expect("text");
    assert!(
        text.contains("\nChild 0 edges: [0, 1, 2, 3, 4]\n"),
        "{text}"
    );
    assert!(
        text.contains(&format!("\nParent receipt: {}\n", root_receipt(12, PLAN))),
        "{text}"
    );
}

#[test]
fn the_children_of_a_plan_may_come_in_any_order() {
    let enter = ask(
        &task(12),
        vec![json!({"children": [[5, 6, 7], [0, 1, 2, 3, 4]]})],
    );
    assert_eq!(enter["stage"], "enter:0");
    assert_eq!(
        enter["prompt"],
        format!(
            "{}\nChild 0 edges: [5, 6, 7]\nParent receipt: {}\nFuel: 10",
            prompt(12),
            root_receipt(12, "[[5,6,7],[0,1,2,3,4]]")
        )
    );
}

#[test]
fn a_plan_that_is_not_a_partition_of_the_edges_is_refused() {
    for (children, listed) in [
        (
            json!([[0, 1, 2, 3, 4], [4, 5, 6, 7]]),
            "[[0,1,2,3,4],[4,5,6,7]]",
        ),
        (json!([[0, 1, 2, 3, 4], [5, 6]]), "[[0,1,2,3,4],[5,6]]"),
        // Eight entries for eight edges, with the edge 0 twice and the edge 7 missing.
        (
            json!([[1, 2, 3, 4], [0, 5, 6], [0]]),
            "[[1,2,3,4],[0,5,6],[0]]",
        ),
        (json!([]), "[]"),
    ] {
        let (passed, report) = run(&task(12), vec![json!({ "children": children })]);
        assert!(!passed);
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "COVERAGE_NOT_A_PARTITION");
        assert_eq!(report["detail"], json!({ "plan": children }));
        assert_eq!(
            report["predicates"],
            json!([{"name": "forward_coverage_partition", "passed": false,
                    "evidence_sha256": sha(listed)}])
        );
    }
}

#[test]
fn a_plan_the_host_cannot_read_is_malformed_by_its_reason() {
    assert_eq!(
        malformed(&task(12), vec![json!({"plan": [[0]]})]),
        "children must be a list"
    );
    assert_eq!(
        malformed(&task(12), vec![json!({"children": "all"})]),
        "children must be a list"
    );
    assert_eq!(
        malformed(&task(12), vec![json!({"children": [3]})]),
        "flip list required"
    );
    assert_eq!(
        malformed(&task(12), vec![json!({"children": [[0, "1"]]})]),
        "flip must be an exact int"
    );
    assert_eq!(
        malformed(&task(12), vec![json!({"children": [[0, 8]]})]),
        "flip index out of range"
    );
}

#[test]
fn a_plan_that_never_comes_ends_the_run_with_no_reply() {
    let Outcome::Fail { result } = judge(&request(&task(12), &[None])) else {
        panic!("expected a failed run");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}

#[test]
fn a_child_under_another_receipt_is_refused_as_stale() {
    let root = root_receipt(12, PLAN);
    // The second child states the plan's receipt, not the receipt after the first child.
    let (passed, report) = run(&task(12), with_reply(3, header(&root, 12, 8)));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "STALE_PARENT_RECEIPT");
    assert_eq!(report["detail"], json!({"child": 1}));
    let row = predicate(&report, "child1:parent_bound");
    assert_eq!(row["passed"], false);
    let after = child_receipt(&root, 0, "[0]", 9);
    assert_eq!(row["evidence_sha256"], sha(&format!("\"{after}\"")));
    assert_eq!(names(&report).last(), Some(&"child1:parent_bound"));
    // No receipt, or one that is not text, is no better.
    for head in [
        json!({"task_digest": task_digest(12), "fuel": 10}),
        json!({"parent_receipt": [root], "task_digest": task_digest(12), "fuel": 10}),
    ] {
        let (_, first) = run(&task(12), with_reply(1, head));
        assert_eq!(first["code"], "STALE_PARENT_RECEIPT");
        assert_eq!(first["detail"], json!({"child": 0}));
    }
}

#[test]
fn a_child_that_states_another_task_is_refused() {
    let root = root_receipt(12, PLAN);
    let other = json!({"parent_receipt": root, "task_digest": task_digest(11), "fuel": 10});
    let (passed, report) = run(&task(12), with_reply(1, other));
    assert!(!passed);
    assert_eq!(report["code"], "TASK_CHANGED");
    assert_eq!(report["detail"], json!({"child": 0}));
    assert_eq!(predicate(&report, "child0:parent_bound")["passed"], true);
    let row = predicate(&report, "child0:task_unchanged");
    assert_eq!(row["passed"], false);
    assert_eq!(
        row["evidence_sha256"],
        sha(&format!("\"{}\"", task_digest(12)))
    );
    let silent = json!({"parent_receipt": root_receipt(12, PLAN), "fuel": 10});
    let (_, missing) = run(&task(12), with_reply(1, silent));
    assert_eq!(missing["code"], "TASK_CHANGED");
}

#[test]
fn a_child_that_states_more_fuel_than_is_left_is_refused_as_a_reset() {
    let after = child_receipt(&root_receipt(12, PLAN), 0, "[0]", 9);
    let (passed, report) = run(&task(12), with_reply(3, header(&after, 12, 12)));
    assert!(!passed);
    assert_eq!(report["code"], "FUEL_RESET");
    assert_eq!(report["detail"], json!({"child": 1}));
    let row = predicate(&report, "child1:fuel_not_reset");
    assert_eq!(row["passed"], false);
    assert_eq!(row["evidence_sha256"], sha(r#"{"claimed":12,"left":8}"#));
    let (_, nine) = run(&task(12), with_reply(3, header(&after, 12, 9)));
    assert_eq!(nine["code"], "FUEL_RESET");
}

#[test]
fn a_child_that_states_less_fuel_than_is_left_is_refused_as_a_mismatch() {
    let after = child_receipt(&root_receipt(12, PLAN), 0, "[0]", 9);
    let (passed, report) = run(&task(12), with_reply(3, header(&after, 12, 7)));
    assert!(!passed);
    assert_eq!(report["code"], "FUEL_MISMATCH");
    assert_eq!(report["detail"], json!({"child": 1}));
    assert_eq!(
        predicate(&report, "child1:fuel_not_reset")["evidence_sha256"],
        sha(r#"{"claimed":7,"left":8}"#)
    );
}

#[test]
fn a_header_the_host_cannot_read_is_malformed_by_its_reason() {
    let root = root_receipt(12, PLAN);
    assert_eq!(
        malformed(&task(12), with_reply(1, json!("enter"))),
        "enter:0 header must be an object"
    );
    let after = child_receipt(&root, 0, "[0]", 9);
    let loose = json!({"parent_receipt": after, "task_digest": task_digest(12), "fuel": "8"});
    assert_eq!(
        malformed(&task(12), with_reply(3, loose)),
        "fuel must be an exact int"
    );
    let outcome = judge(&request(
        &task(12),
        &[
            Some(plan()),
            Some(header(&root, 12, 10)),
            Some(flip(&[0])),
            None,
        ],
    ));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["code"], "MALFORMED_CANDIDATE");
    assert_eq!(
        result["detail"]["reason"],
        "enter:1 header must be an object"
    );
}

#[test]
fn every_question_draws_on_the_one_counter() {
    // One unit: the plan takes it, and the first child cannot be entered.
    let (passed, one) = run(&task(1), vec![plan()]);
    assert!(!passed);
    assert_eq!(one["verdict"], "REFUSED");
    assert_eq!(one["code"], "FUEL_EXHAUSTED");
    assert_eq!(one["detail"], json!({"child": 0, "fuel_trace": [1, 0]}));
    assert_eq!(
        ask(&task(1), vec![])["prompt"],
        format!("{}\nFuel: 0", prompt(1))
    );
    // Two units: the child is entered and cannot be asked for an attempt.
    let root = root_receipt(2, PLAN);
    let (_, two) = run(&task(2), vec![plan(), header(&root, 2, 0)]);
    assert_eq!(two["code"], "CHILD_HALTED_ON_FUEL");
    assert_eq!(two["detail"], json!({"child": 0, "fuel_trace": [2, 1, 0]}));
    let row = predicate(&two, "child0:certified");
    assert_eq!(row["passed"], false);
    assert_eq!(row["evidence_sha256"], sha(r#""fuel""#));
}

#[test]
fn a_child_cannot_be_asked_more_often_than_the_fuel_allows() {
    // Five units: plan, header and three attempts. The limit of five attempts is never reached.
    let root = root_receipt(5, PLAN);
    let mut replies = vec![plan(), header(&root, 5, 3)];
    replies.extend(vec![flip(&[2]); 3]);
    assert_eq!(
        ask(&task(5), replies[..4].to_vec())["stage"],
        "child:0:attempt:2"
    );
    let (_, report) = run(&task(5), replies);
    assert_eq!(report["code"], "CHILD_HALTED_ON_FUEL");
    assert_eq!(
        report["detail"],
        json!({"child": 0, "fuel_trace": [5, 4, 3, 2, 1, 0]})
    );
    // The fuel spent by the first child is gone for the second.
    let root = root_receipt(4, PLAN);
    let after = child_receipt(&root, 0, "[1]", 1);
    let replies = vec![
        plan(),
        header(&root, 4, 2),
        flip(&[1]),
        header(&after, 4, 0),
    ];
    let (_, second) = run(&task(4), replies);
    assert_eq!(second["code"], "CHILD_HALTED_ON_FUEL");
    assert_eq!(
        second["detail"],
        json!({"child": 1, "fuel_trace": [4, 3, 2, 1, 0]})
    );
}

#[test]
fn a_child_that_uses_its_attempts_or_loses_a_reply_halts_the_run() {
    let mut limited = task(12);
    limited["max_attempts"] = json!(2);
    let digest = sha(&format!(
        concat!(
            r#"{{"edges":{},"fuel":12,"labels":{},"max_attempts":2,"#,
            r#""statement":"{}"}}"#
        ),
        EDGES, LABELS, STATEMENT
    ));
    let root = sha(&format!(r#"{{"plan":{PLAN},"root":"{digest}"}}"#));
    let head = json!({"parent_receipt": root, "task_digest": digest, "fuel": 10});
    // The child's own task carries the limit.
    let first = ask(&limited, vec![plan(), head.clone()]);
    assert_eq!(
        first["prompt"],
        part("[[0,1],[1,2],[2,0],[2,3],[3,0]]", "[1,0,0,0,0]", 2)
    );
    let replies = vec![plan(), head.clone(), flip(&[2]), flip(&[3])];
    let (passed, report) = run(&limited, replies);
    assert!(!passed);
    assert_eq!(report["code"], "CHILD_HALTED_ON_LIMIT");
    assert_eq!(
        report["detail"],
        json!({"child": 0, "fuel_trace": [12, 11, 10, 9, 8]})
    );
    assert_eq!(
        predicate(&report, "child0:certified")["evidence_sha256"],
        sha(r#""limit""#)
    );
    let outcome = judge(&request(
        &limited,
        &[Some(plan()), Some(head.clone()), Some(flip(&[2])), None],
    ));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["code"], "CHILD_HALTED_ON_BUDGET");
    let greedy = json!({"flip": [0], "lift_request": "labels"});
    let (_, scope) = run(&limited, vec![plan(), head, greedy]);
    assert_eq!(scope["code"], "CHILD_HALTED_ON_SCOPE");
    assert_eq!(
        scope["detail"],
        json!({"child": 0, "fuel_trace": [12, 11, 10, 9]})
    );
}

#[test]
fn a_child_repairs_under_the_residual_of_its_own_part() {
    let mut replies = good()[..2].to_vec();
    replies.push(flip(&[2]));
    let second = ask(&task(12), replies.clone());
    assert_eq!(second["stage"], "child:0:attempt:1");
    assert_eq!(
        second["prompt"],
        format!(
            "{}\nHost residual: {}",
            part("[[0,1],[1,2],[2,0],[2,3],[3,0]]", "[1,0,0,0,0]", 5),
            r#"{"flip_count":1,"minimal_known":false,"odd_cycles":[1]}"#
        )
    );
    // The repair on the second attempt costs one more unit, and the receipt says so.
    replies.push(flip(&[1]));
    let root = root_receipt(12, PLAN);
    let after = child_receipt(&root, 0, "[1]", 8);
    replies.extend([header(&after, 12, 7), flip(&[0])]);
    let (passed, report) = run(&task(12), replies);
    assert!(passed);
    assert_eq!(
        report["detail"],
        json!({"flips": [1, 5], "fuel_trace": [12, 11, 10, 9, 8, 7, 6],
               "receipt": child_receipt(&after, 1, "[5]", 6)})
    );
}

#[test]
fn children_that_each_pass_alone_can_still_fail_the_task() {
    // One triangle with an odd label sum, split so that neither part holds a cycle.
    let split = json!({"statement": STATEMENT, "edges": [[0, 1], [1, 2], [2, 0]],
                       "labels": [1, 0, 0], "fuel": 9});
    let digest = sha(&format!(
        r#"{{"edges":[[0,1],[1,2],[2,0]],"fuel":9,"labels":[1,0,0],"statement":"{STATEMENT}"}}"#
    ));
    let root = sha(&format!(r#"{{"plan":[[0,1],[2]],"root":"{digest}"}}"#));
    let after = child_receipt(&root, 0, "[]", 6);
    let head = |receipt: &str, fuel: i64| json!({"parent_receipt": receipt, "task_digest": digest, "fuel": fuel});
    let replies = vec![
        json!({"children": [[0, 1], [2]]}),
        head(&root, 7),
        flip(&[]),
        head(&after, 5),
        flip(&[]),
    ];
    let (passed, report) = run(&split, replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "BACKWARD_SOLUTION_MAP");
    assert_eq!(report["detail"]["flips"], json!([]));
    assert_eq!(report["detail"]["failed"], json!(["backward_solution_map"]));
    assert_eq!(predicate(&report, "child1:certified")["passed"], true);
    let row = predicate(&report, "backward_solution_map");
    assert_eq!(row["passed"], false);
    assert_eq!(row["evidence_sha256"], sha("[]"));
}

#[test]
fn a_union_of_the_least_size_that_leaves_a_cycle_odd_fails_the_task() {
    // Two triangles, both odd through the edge 2 they share. Flipping the edge 2 mends both.
    // The first child holds one whole triangle and mends it with the edge 0, so the union has
    // the least size, one flip, and the second triangle is still odd.
    let kite = json!({"statement": STATEMENT,
                      "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]],
                      "labels": [0, 0, 1, 0, 0], "fuel": 9});
    let digest = sha(&format!(
        concat!(
            r#"{{"edges":[[0,1],[1,2],[2,0],[2,3],[3,0]],"fuel":9,"#,
            r#""labels":[0,0,1,0,0],"statement":"{}"}}"#
        ),
        STATEMENT
    ));
    let root = sha(&format!(r#"{{"plan":[[0,1,2],[3,4]],"root":"{digest}"}}"#));
    let after = child_receipt(&root, 0, "[0]", 6);
    let head = |receipt: &str, fuel: i64| json!({"parent_receipt": receipt, "task_digest": digest, "fuel": fuel});
    let replies = vec![
        json!({"children": [[0, 1, 2], [3, 4]]}),
        head(&root, 7),
        flip(&[0]),
        head(&after, 5),
        flip(&[]),
    ];
    let (passed, report) = run(&kite, replies);
    assert!(!passed);
    assert_eq!(report["code"], "BACKWARD_SOLUTION_MAP");
    assert_eq!(report["detail"]["flips"], json!([0]));
    assert_eq!(predicate(&report, "child0:certified")["passed"], true);
    assert_eq!(predicate(&report, "child1:certified")["passed"], true);
    assert_eq!(
        predicate(&report, "backward_solution_map")["evidence_sha256"],
        sha("[0]")
    );
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    let with = |key: &str, value: Value| {
        let mut task = task(12);
        task[key] = value;
        task
    };
    assert_eq!(bad_task(task(0)), "fuel must be positive");
    assert_eq!(bad_task(task(-3)), "fuel must be positive");
    assert_eq!(
        bad_task(with("fuel", json!("12"))),
        "fuel must be an exact int"
    );
    let mut none = task(12);
    none.as_object_mut().expect("object").remove("fuel");
    assert_eq!(bad_task(none), "fuel must be an exact int");
    assert_eq!(
        bad_task(with("labels", json!([1, 0, 0, 0, 0, 0, 0, 3]))),
        "every label must be the exact integer 0 or 1"
    );
    assert_eq!(
        bad_task(with("max_attempts", json!(6))),
        "max_attempts must be in 1..5"
    );
    assert!(matches!(
        next(&request(&task(1), &[])),
        Outcome::Pass { .. }
    ));
}
