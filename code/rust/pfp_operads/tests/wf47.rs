//! WF47, resumable bounded frontier search: the numbering of candidates, the sealed chain of
//! checkpoints, each custody rule in the order the host applies them, and the three ends of a
//! search.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf47-tests:v1

use std::collections::BTreeMap;

use pfp_operads::families::wf47::{FAMILY, MAX_SESSIONS, MAX_VERTICES};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str =
    "Find a sign for every vertex that gives each edge the product of its ends.";

/// A triangle 0-1-2 and a tail 2-3: eight candidates.
const EDGES: &str = "[[0,1],[1,2],[2,0],[2,3]]";

/// Signs with the gauge + + - -, which is candidate 3 in the basis order 0, 1, 2, 3.
const BALANCED: &str = "[1,-1,-1,1]";

/// Signs with one -1 on the triangle: no gauge.
const FRUSTRATED: &str = "[1,1,-1,1]";

fn parsed(text: &str) -> Value {
    serde_json::from_str(text).expect("JSON")
}

fn task(signs: &str, batch: usize, sessions: usize, evals: usize) -> Value {
    json!({"statement": STATEMENT, "edges": parsed(EDGES), "signs": parsed(signs),
           "basis": [0, 1, 2, 3], "representation": "pm1", "batch": batch,
           "max_sessions": sessions, "session_evals": evals})
}

fn prompt(signs: &str, batch: usize, sessions: usize, evals: usize) -> String {
    format!(
        concat!(
            "WF47 Resumable bounded frontier search. {}\n",
            r#"{{"basis":[0,1,2,3],"batch":{},"edges":{},"max_sessions":{},"#,
            r#""representation":"pm1","session_evals":{},"signs":{}}}"#
        ),
        STATEMENT, batch, EDGES, sessions, evals, signs
    )
}

/// The digest of a presentation: its basis, edges, representation and signs.
fn key_of(signs: &str, basis: &str, representation: &str) -> String {
    sha(&format!(
        r#"{{"basis":{basis},"edges":{EDGES},"representation":{representation},"signs":{signs}}}"#
    ))
}

fn key(signs: &str) -> String {
    key_of(signs, "[0,1,2,3]", "\"pm1\"")
}

/// A value as the host hashes it: no spaces, and the fields of an object in key order.
fn written(value: &Value) -> String {
    match value {
        Value::Array(items) => {
            let items: Vec<String> = items.iter().map(written).collect();
            format!("[{}]", items.join(","))
        }
        Value::Object(fields) => {
            let fields: BTreeMap<&String, &Value> = fields.iter().collect();
            let fields: Vec<String> = fields
                .iter()
                .map(|(field, value)| format!("\"{field}\":{}", written(value)))
                .collect();
            format!("{{{}}}", fields.join(","))
        }
        other => other.to_string(),
    }
}

/// The records with their seals: each seal is the hash of the seal before it and the record,
/// starting from the hash of the key as JSON text.
fn sealed_from(start: &str, bodies: Vec<Value>) -> Vec<Value> {
    let mut seal = start.to_owned();
    let seal_next = |mut body: Value| {
        body.as_object_mut().expect("a record").remove("seal");
        seal = sha(&format!("{seal}{}", written(&body)));
        body["seal"] = json!(seal);
        body
    };
    bodies.into_iter().map(seal_next).collect()
}

fn sealed(key: &str, bodies: Vec<Value>) -> Vec<Value> {
    sealed_from(&sha(&format!("\"{key}\"")), bodies)
}

/// The record of the batch `start..end` as an honest search writes it.
fn record(index: usize, key: &str, start: usize, end: usize, gauge: Option<usize>) -> Value {
    json!({"index": index, "key": key, "start": start, "end": end, "spent": end,
           "status": if gauge.is_some() { "verified" } else { "unknown" }, "gauge": gauge})
}

/// The honest records of the first `count` batches of two candidates.
fn bodies(signs: &str, count: usize) -> Vec<Value> {
    let key = key(signs);
    let gauge = |batch: usize| (signs == BALANCED && batch == 1).then_some(3);
    (0..count)
        .map(|batch| record(batch, &key, 2 * batch, 2 * batch + 2, gauge(batch)))
        .collect()
}

fn reply(chain: Vec<Value>) -> Value {
    json!({ "checkpoints": chain })
}

/// The honest reply that replays the first `count` batches of two.
fn honest(signs: &str, count: usize) -> Value {
    reply(sealed(&key(signs), bodies(signs, count)))
}

/// The honest records with one field of one record replaced, sealed again.
fn forged(signs: &str, count: usize, at: usize, field: &str, value: Value) -> Value {
    let mut bodies = bodies(signs, count);
    bodies[at][field] = value;
    reply(sealed(&key(signs), bodies))
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
    json!({"workflow": "WF47", "task": task, "replies": replies}).to_string()
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

/// A run refused in `session` under one custody rule.
fn broken(task: &Value, replies: Vec<Value>, code: &str, session: usize) -> Value {
    let (passed, report) = run(task, replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], code);
    assert_eq!(report["detail"], json!({ "session": session }));
    assert_eq!(outcomes(&report), [(code.to_lowercase().as_str(), false)]);
    report
}

/// A request with one number of its task written out as an integer too large for a machine
/// word. The task carries `stand_in` where the large number goes.
fn enlarged(task: &Value, replies: Vec<Value>, field: &str, stand_in: u64) -> String {
    let small = format!("\"{field}\":{stand_in}");
    let large = format!("\"{field}\":1000000000000000000000000000000");
    let request = request(task, &all(replies));
    assert!(request.contains(&small));
    request.replace(&small, &large)
}

fn stages(report: &Value) -> Vec<&str> {
    report["asked"]
        .as_array()
        .expect("asked")
        .iter()
        .filter_map(|asked| asked["stage"].as_str())
        .collect()
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF47",
            "Resumable bounded frontier search",
            "sign_gauge_checkpoint_chain"
        )
    );
}

#[test]
fn the_search_opens_with_the_task_as_written() {
    let first = ask(&task(BALANCED, 2, 3, 4), vec![]);
    assert_eq!(first["stage"], "search");
    assert_eq!(first["prompt"], prompt(BALANCED, 2, 3, 4));
    assert_eq!(first["prompt_sha256"], sha(&prompt(BALANCED, 2, 3, 4)));
}

#[test]
fn a_resumed_session_is_told_the_last_seal_and_how_many_records_it_follows() {
    let task = task(FRUSTRATED, 2, 4, 2);
    let chain = sealed(&key(FRUSTRATED), bodies(FRUSTRATED, 2));
    let second = ask(&task, vec![honest(FRUSTRATED, 1)]);
    assert_eq!(second["stage"], "resume:1");
    let expected = format!(
        "{}\nResume after seal {} at index 1.",
        prompt(FRUSTRATED, 2, 4, 2),
        chain[0]["seal"].as_str().expect("a seal")
    );
    assert_eq!(second["prompt"], expected);
    assert_eq!(second["prompt_sha256"], sha(&expected));
    let third = ask(&task, vec![honest(FRUSTRATED, 1), honest(FRUSTRATED, 2)]);
    assert_eq!(third["stage"], "resume:2");
    assert_eq!(
        third["prompt"],
        format!(
            "{}\nResume after seal {} at index 2.",
            prompt(FRUSTRATED, 2, 4, 2),
            chain[1]["seal"].as_str().expect("a seal")
        )
    );
}

#[test]
fn a_seal_is_the_hash_of_the_seal_before_it_and_the_record() {
    let key = key(BALANCED);
    let first = format!(
        r#"{{"end":2,"gauge":null,"index":0,"key":"{key}","spent":2,"start":0,"status":"unknown"}}"#
    );
    let second = format!(
        r#"{{"end":4,"gauge":3,"index":1,"key":"{key}","spent":4,"start":2,"status":"verified"}}"#
    );
    let opening = sha(&format!("\"{key}\""));
    let one = sha(&format!("{opening}{first}"));
    let two = sha(&format!("{one}{second}"));
    let mut records = vec![parsed(&first), parsed(&second)];
    records[0]["seal"] = json!(one);
    records[1]["seal"] = json!(two);
    let (passed, report) = run(&task(BALANCED, 2, 3, 4), vec![reply(records)]);
    assert!(passed);
    assert_eq!(report["code"], "GAUGE_VERIFIED");
    assert_eq!(
        evidence(&report, "checkpoint_chain_valid"),
        &json!(sha(&format!("\"{two}\"")))
    );
}

#[test]
fn a_search_that_finds_a_gauge_is_certified() {
    let (passed, report) = run(&task(BALANCED, 2, 3, 4), vec![honest(BALANCED, 2)]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "GAUGE_VERIFIED");
    assert_eq!(report["detail"], json!({"gauge": 3, "checkpoints": 2}));
    assert_eq!(
        outcomes(&report),
        [
            ("checkpoint_chain_valid", true),
            ("gauge_balances_every_edge", true)
        ]
    );
    assert_eq!(
        evidence(&report, "gauge_balances_every_edge"),
        &json!(sha("3"))
    );
    assert_eq!(stages(&report), ["search"]);
}

#[test]
fn a_search_resumed_from_its_checkpoint_is_certified_the_same() {
    let replies = vec![honest(BALANCED, 1), honest(BALANCED, 2)];
    let (passed, report) = run(&task(BALANCED, 2, 3, 2), replies.clone());
    assert!(passed);
    assert_eq!(report["detail"], json!({"gauge": 3, "checkpoints": 2}));
    assert_eq!(stages(&report), ["search", "resume:1"]);
    // Nothing more is asked once a gauge is found.
    assert_eq!(ask(&task(BALANCED, 2, 3, 2), replies), Value::Null);
}

#[test]
fn the_basis_order_numbers_the_candidates() {
    // With vertex 2 first and so +1, the gauge is - - + + on 0, 1, 2, 3: vertices 0 and 1 are
    // the two highest bits, which is candidate 6.
    let mut moved = task(BALANCED, 2, 1, 8);
    moved["basis"] = json!([2, 0, 1, 3]);
    let key = key_of(BALANCED, "[2,0,1,3]", "\"pm1\"");
    let chain = vec![
        record(0, &key, 0, 2, None),
        record(1, &key, 2, 4, None),
        record(2, &key, 4, 6, None),
        record(3, &key, 6, 8, Some(6)),
    ];
    let (passed, report) = run(&moved, vec![reply(sealed(&key, chain))]);
    assert!(passed);
    assert_eq!(report["detail"], json!({"gauge": 6, "checkpoints": 4}));
    // The chain of the other basis order is a chain for another presentation.
    broken(
        &moved,
        vec![honest(BALANCED, 2)],
        "PRESENTATION_KEY_CHANGED",
        0,
    );
}

#[test]
fn the_first_gauge_of_a_batch_is_the_one_recorded() {
    // Two separate edges: vertex 1 follows vertex 0, and vertex 3 is opposite to vertex 2.
    // Candidates 1 and 2 are both gauges.
    let apart = json!({"edges": [[0, 1], [2, 3]], "signs": [1, -1], "basis": [0, 1, 2, 3],
                       "representation": "pm1", "batch": 4, "max_sessions": 1,
                       "session_evals": 4});
    let key = sha(concat!(
        r#"{"basis":[0,1,2,3],"edges":[[0,1],[2,3]],"#,
        r#""representation":"pm1","signs":[1,-1]}"#
    ));
    let (passed, report) = run(
        &apart,
        vec![reply(sealed(&key, vec![record(0, &key, 0, 4, Some(1))]))],
    );
    assert!(passed);
    assert_eq!(report["detail"], json!({"gauge": 1, "checkpoints": 1}));
    let later = reply(sealed(&key, vec![record(0, &key, 0, 4, Some(2))]));
    broken(&apart, vec![later], "STATUS_NOT_RECOMPUTED", 0);
}

#[test]
fn all_plus_signs_are_balanced_by_the_first_candidate() {
    let plus = "[1,1,1,1]";
    let key = key(plus);
    let chain = sealed(&key, vec![record(0, &key, 0, 2, Some(0))]);
    let (passed, report) = run(&task(plus, 2, 1, 2), vec![reply(chain)]);
    assert!(passed);
    assert_eq!(report["detail"], json!({"gauge": 0, "checkpoints": 1}));
    assert_eq!(
        evidence(&report, "gauge_balances_every_edge"),
        &json!(sha("0"))
    );
}

#[test]
fn an_exhausted_search_on_a_frustrated_graph_ends_as_the_typed_obstruction() {
    let replies = vec![honest(FRUSTRATED, 2), honest(FRUSTRATED, 4)];
    let (passed, report) = run(&task(FRUSTRATED, 2, 3, 4), replies.clone());
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "RESTRICTED_OBSTRUCTION");
    assert_eq!(
        report["detail"],
        json!({"frustrated_cycles": [0], "checkpoints": 4})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("checkpoint_chain_valid", true),
            ("frustrated_cycle_witness", true)
        ]
    );
    assert_eq!(
        evidence(&report, "frustrated_cycle_witness"),
        &json!(sha("[0]"))
    );
    assert_eq!(stages(&report), ["search", "resume:1"]);
    // Nothing more is asked once every candidate is tried.
    assert_eq!(ask(&task(FRUSTRATED, 2, 3, 4), replies), Value::Null);
}

#[test]
fn the_obstruction_names_the_fundamental_cycles_with_an_odd_number_of_minus_edges() {
    // Two triangles on the edge 2-0. Cycle 0 is the edges 1, 2, 0 and cycle 1 the edges 3, 4, 2.
    let kite = |signs: Value| {
        json!({"edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], "signs": signs,
               "basis": [0, 1, 2, 3], "representation": "pm1", "batch": 8,
               "max_sessions": 1, "session_evals": 8})
    };
    let odd = |signs: &str| {
        let key = sha(&format!(
            concat!(
                r#"{{"basis":[0,1,2,3],"edges":[[0,1],[1,2],[2,0],[2,3],[3,0]],"#,
                r#""representation":"pm1","signs":{}}}"#
            ),
            signs
        ));
        let chain = sealed(&key, vec![record(0, &key, 0, 8, None)]);
        let (passed, report) = run(&kite(parsed(signs)), vec![reply(chain)]);
        assert!(passed, "{signs}");
        assert_eq!(report["code"], "RESTRICTED_OBSTRUCTION");
        assert_eq!(report["detail"]["checkpoints"], 1);
        report["detail"]["frustrated_cycles"].clone()
    };
    assert_eq!(odd("[-1,1,1,1,1]"), json!([0]));
    assert_eq!(odd("[1,1,1,1,-1]"), json!([1]));
    assert_eq!(odd("[1,1,-1,1,1]"), json!([0, 1]));
    assert_eq!(odd("[-1,-1,-1,1,1]"), json!([0, 1]));
    assert_eq!(odd("[1,-1,1,-1,-1]"), json!([0]));
}

#[test]
fn a_search_that_runs_out_of_sessions_is_incomplete() {
    let (passed, report) = run(&task(FRUSTRATED, 2, 1, 4), vec![honest(FRUSTRATED, 2)]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "SEARCH_INCOMPLETE");
    assert_eq!(report["detail"], json!({"suffix": 4, "checkpoints": 2}));
    assert_eq!(outcomes(&report), [("checkpoint_chain_valid", true)]);
    // Two sessions of one batch each, and no third.
    let replies = vec![honest(FRUSTRATED, 1), honest(FRUSTRATED, 2)];
    assert_eq!(
        ask(&task(FRUSTRATED, 2, 2, 2), replies.clone()),
        Value::Null
    );
    let (_, report) = run(&task(FRUSTRATED, 2, 2, 2), replies);
    assert_eq!(report["code"], "SEARCH_INCOMPLETE");
    assert_eq!(report["detail"], json!({"suffix": 4, "checkpoints": 2}));
    assert_eq!(stages(&report), ["search", "resume:1"]);
}

#[test]
fn a_session_with_no_reply_ends_the_search_where_it_stood() {
    let outcome = judge(&request(
        &task(FRUSTRATED, 2, 3, 4),
        &[Some(honest(FRUSTRATED, 1)), None],
    ));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["code"], "SEARCH_INCOMPLETE");
    assert_eq!(result["detail"], json!({"suffix": 2, "checkpoints": 1}));
    assert_eq!(stages(&result), ["search", "resume:1"]);
    let outcome = judge(&request(&task(FRUSTRATED, 2, 3, 4), &[None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}

#[test]
fn a_chain_starts_at_index_zero() {
    let task = task(FRUSTRATED, 2, 3, 4);
    // A resumed session that sends only its new records.
    let tail = sealed(&key(FRUSTRATED), bodies(FRUSTRATED, 4)).split_off(2);
    let report = broken(
        &task,
        vec![honest(FRUSTRATED, 2), reply(tail.clone())],
        "RESUME_NOT_REPLAYED_FROM_ZERO",
        1,
    );
    assert_eq!(
        evidence(&report, "resume_not_replayed_from_zero"),
        &json!(sha(&written(&json!(tail))))
    );
    let late = forged(FRUSTRATED, 2, 0, "index", json!(1));
    broken(&task, vec![late], "RESUME_NOT_REPLAYED_FROM_ZERO", 0);
    let unnumbered = forged(FRUSTRATED, 2, 0, "index", json!("0"));
    broken(&task, vec![unnumbered], "RESUME_NOT_REPLAYED_FROM_ZERO", 0);
}

#[test]
fn the_indices_of_a_chain_are_contiguous() {
    let task = task(FRUSTRATED, 2, 3, 4);
    let gap = forged(FRUSTRATED, 2, 1, "index", json!(2));
    broken(&task, vec![gap], "CHAIN_NOT_CONTIGUOUS", 0);
    let repeat = forged(FRUSTRATED, 2, 1, "index", json!(0));
    broken(&task, vec![repeat], "CHAIN_NOT_CONTIGUOUS", 0);
    let mut missing = bodies(FRUSTRATED, 2);
    missing[1]
        .as_object_mut()
        .expect("a record")
        .remove("index");
    broken(
        &task,
        vec![reply(sealed(&key(FRUSTRATED), missing))],
        "CHAIN_NOT_CONTIGUOUS",
        0,
    );
}

#[test]
fn a_resumed_chain_extends_the_chain_before_it_unchanged() {
    let task = task(FRUSTRATED, 2, 4, 4);
    let first = honest(FRUSTRATED, 2);
    let resumed = |second: Value| {
        broken(
            &task,
            vec![first.clone(), second],
            "RESUME_DIVERGES_FROM_CHECKPOINT",
            1,
        )
    };
    // No new record, and then fewer records than before.
    resumed(honest(FRUSTRATED, 2));
    resumed(honest(FRUSTRATED, 1));
    // An earlier record rewritten, with every seal recomputed.
    let mut rewritten = bodies(FRUSTRATED, 3);
    rewritten[0]["note"] = json!("kept");
    resumed(reply(sealed(&key(FRUSTRATED), rewritten)));
    // The last record of the earlier chain rewritten.
    let mut rewritten = bodies(FRUSTRATED, 3);
    rewritten[1]["note"] = json!("kept");
    resumed(reply(sealed(&key(FRUSTRATED), rewritten)));
    // A first session has nothing to extend, and may carry such a note.
    let mut noted = bodies(FRUSTRATED, 2);
    noted[0]["note"] = json!("kept");
    let once = self::task(FRUSTRATED, 2, 1, 4);
    let (_, report) = run(&once, vec![reply(sealed(&key(FRUSTRATED), noted))]);
    assert_eq!(report["code"], "SEARCH_INCOMPLETE");
}

#[test]
fn every_record_carries_the_key_of_the_presentation() {
    let task = task(FRUSTRATED, 2, 3, 4);
    let other = key_of(FRUSTRATED, "[0,1,2,3]", "\"zero-one\"");
    let one = forged(FRUSTRATED, 2, 1, "key", json!(other));
    broken(&task, vec![one], "PRESENTATION_KEY_CHANGED", 0);
    // On resume: the records before stay as they were, and the new ones carry another key.
    let mut bodies = bodies(FRUSTRATED, 4);
    bodies[3]["key"] = json!(other);
    let resumed = reply(sealed(&key(FRUSTRATED), bodies));
    broken(
        &task,
        vec![honest(FRUSTRATED, 2), resumed],
        "PRESENTATION_KEY_CHANGED",
        1,
    );
    // The representation is part of the presentation.
    let mut renamed = self::task(FRUSTRATED, 2, 1, 4);
    renamed["representation"] = json!("zero-one");
    broken(
        &renamed,
        vec![honest(FRUSTRATED, 2)],
        "PRESENTATION_KEY_CHANGED",
        0,
    );
    let chain = sealed(
        &other,
        vec![record(0, &other, 0, 2, None), record(1, &other, 2, 4, None)],
    );
    let (_, report) = run(&renamed, vec![reply(chain)]);
    assert_eq!(report["code"], "SEARCH_INCOMPLETE");
}

#[test]
fn every_seal_is_recomputed() {
    let task = task(FRUSTRATED, 2, 3, 4);
    let chain = || sealed(&key(FRUSTRATED), bodies(FRUSTRATED, 2));
    let refused = |chain: Vec<Value>| broken(&task, vec![reply(chain)], "SEAL_MISMATCH", 0);
    for at in [0, 1] {
        let mut wrong = chain();
        wrong[at]["seal"] = json!(sha("forged"));
        refused(wrong);
        let mut missing = chain();
        missing[at]
            .as_object_mut()
            .expect("a record")
            .remove("seal");
        refused(missing);
    }
    // Each record sealed on its own from the opening seal, not from the seal before it.
    let opening = sha(&format!("\"{}\"", key(FRUSTRATED)));
    let apart: Vec<Value> = bodies(FRUSTRATED, 2)
        .into_iter()
        .flat_map(|body| sealed_from(&opening, vec![body]))
        .collect();
    refused(apart);
    // A chain that opens from the key itself and not from its hash.
    refused(sealed_from(&key(FRUSTRATED), bodies(FRUSTRATED, 2)));
    // A field added after sealing.
    let mut noted = chain();
    noted[1]["note"] = json!("added");
    refused(noted);
}

#[test]
fn the_batches_are_the_hosts() {
    let task = task(FRUSTRATED, 2, 3, 8);
    let refused = |reply: Value| broken(&task, vec![reply], "BATCH_NOT_LEXICOGRAPHIC", 0);
    // A skipped batch, a short batch, a long batch, and a batch that starts late.
    let mut skipped = bodies(FRUSTRATED, 2);
    skipped[1] = record(1, &key(FRUSTRATED), 4, 6, None);
    refused(reply(sealed(&key(FRUSTRATED), skipped)));
    let mut short = bodies(FRUSTRATED, 2);
    short[0] = record(0, &key(FRUSTRATED), 0, 1, None);
    refused(reply(sealed(&key(FRUSTRATED), short)));
    let mut long = bodies(FRUSTRATED, 2);
    long[1] = record(1, &key(FRUSTRATED), 2, 5, None);
    refused(reply(sealed(&key(FRUSTRATED), long)));
    refused(forged(FRUSTRATED, 2, 1, "start", json!(3)));
    refused(forged(FRUSTRATED, 2, 0, "start", json!(1)));
    // A bound that is not an exact integer.
    refused(forged(FRUSTRATED, 2, 1, "start", json!(2.0)));
    refused(forged(FRUSTRATED, 2, 1, "end", json!("4")));
    refused(forged(FRUSTRATED, 2, 0, "start", json!(null)));
}

#[test]
fn no_record_follows_the_batch_that_tries_the_last_candidate() {
    let task = task(FRUSTRATED, 2, 3, 8);
    let mut padded = bodies(FRUSTRATED, 4);
    padded.push(record(4, &key(FRUSTRATED), 8, 8, None));
    broken(
        &task,
        vec![reply(sealed(&key(FRUSTRATED), padded))],
        "BATCH_NOT_LEXICOGRAPHIC",
        0,
    );
}

#[test]
fn the_last_batch_stops_at_the_last_candidate() {
    let key = key(FRUSTRATED);
    let thirds = vec![
        record(0, &key, 0, 3, None),
        record(1, &key, 3, 6, None),
        record(2, &key, 6, 8, None),
    ];
    let (passed, report) = run(
        &task(FRUSTRATED, 3, 1, 8),
        vec![reply(sealed(&key, thirds))],
    );
    assert!(passed);
    assert_eq!(
        report["detail"],
        json!({"frustrated_cycles": [0], "checkpoints": 3})
    );
    // A batch larger than the search is the whole search.
    let whole = || reply(sealed(&key, vec![record(0, &key, 0, 8, None)]));
    let (passed, report) = run(&task(FRUSTRATED, 100, 1, 8), vec![whole()]);
    assert!(passed);
    assert_eq!(report["detail"]["checkpoints"], 1);
    let huge = enlarged(&task(FRUSTRATED, 77, 1, 8), vec![whole()], "batch", 77);
    let Outcome::Pass { result } = judge(&huge) else {
        panic!("expected a typed refusal");
    };
    assert_eq!(result["code"], "RESTRICTED_OBSTRUCTION");
    assert_eq!(result["detail"]["checkpoints"], 1);
}

#[test]
fn the_spend_is_every_candidate_tried_so_far() {
    let task = task(FRUSTRATED, 2, 3, 4);
    // The second session counts its own candidates only.
    let mut reset = bodies(FRUSTRATED, 4);
    reset[2]["spent"] = json!(2);
    reset[3]["spent"] = json!(4);
    broken(
        &task,
        vec![
            honest(FRUSTRATED, 2),
            reply(sealed(&key(FRUSTRATED), reset)),
        ],
        "BUDGET_RESET",
        1,
    );
    broken(
        &task,
        vec![forged(FRUSTRATED, 2, 0, "spent", json!(0))],
        "BUDGET_RESET",
        0,
    );
    broken(
        &task,
        vec![forged(FRUSTRATED, 2, 1, "spent", json!(5))],
        "BUDGET_RESET",
        0,
    );
}

#[test]
fn status_and_gauge_are_the_hosts() {
    let balanced = task(BALANCED, 2, 3, 4);
    let wrong = |task: &Value, reply: Value| broken(task, vec![reply], "STATUS_NOT_RECOMPUTED", 0);
    // The batch that holds the gauge, written as if it held none.
    let mut hidden = bodies(BALANCED, 2);
    hidden[1] = record(1, &key(BALANCED), 2, 4, None);
    wrong(&balanced, reply(sealed(&key(BALANCED), hidden)));
    // The right status with another candidate, and with none.
    wrong(&balanced, forged(BALANCED, 2, 1, "gauge", json!(2)));
    wrong(&balanced, forged(BALANCED, 2, 1, "gauge", json!(null)));
    wrong(
        &balanced,
        forged(BALANCED, 2, 1, "status", json!("unknown")),
    );
    // A gauge claimed where there is none.
    let frustrated = task(FRUSTRATED, 2, 3, 4);
    let mut claimed = bodies(FRUSTRATED, 2);
    claimed[1] = record(1, &key(FRUSTRATED), 2, 4, Some(3));
    wrong(&frustrated, reply(sealed(&key(FRUSTRATED), claimed)));
    wrong(
        &frustrated,
        forged(FRUSTRATED, 2, 0, "status", json!("verified")),
    );
    wrong(&frustrated, forged(FRUSTRATED, 2, 0, "gauge", json!(0)));
}

#[test]
fn nothing_follows_the_batch_that_found_a_gauge() {
    let report = broken(
        &task(BALANCED, 2, 3, 8),
        vec![honest(BALANCED, 3)],
        "SEARCH_CONTINUED_AFTER_VERIFIED",
        0,
    );
    assert_eq!(stages(&report), ["search"]);
    broken(
        &task(BALANCED, 2, 3, 8),
        vec![honest(BALANCED, 4)],
        "SEARCH_CONTINUED_AFTER_VERIFIED",
        0,
    );
}

#[test]
fn a_session_tries_no_more_candidates_than_its_budget() {
    // Two batches of two in one session with a budget of 3.
    broken(
        &task(FRUSTRATED, 2, 4, 3),
        vec![honest(FRUSTRATED, 2)],
        "SESSION_BUDGET_EXCEEDED",
        0,
    );
    // A budget of exactly the candidates tried is enough.
    let (_, report) = run(&task(FRUSTRATED, 2, 1, 4), vec![honest(FRUSTRATED, 2)]);
    assert_eq!(report["code"], "SEARCH_INCOMPLETE");
    // On resume only the candidates after the checkpoint count.
    let (_, report) = run(
        &task(FRUSTRATED, 2, 2, 4),
        vec![honest(FRUSTRATED, 2), honest(FRUSTRATED, 4)],
    );
    assert_eq!(report["code"], "RESTRICTED_OBSTRUCTION");
    broken(
        &task(FRUSTRATED, 2, 4, 3),
        vec![honest(FRUSTRATED, 1), honest(FRUSTRATED, 3)],
        "SESSION_BUDGET_EXCEEDED",
        1,
    );
    let (_, report) = run(
        &task(FRUSTRATED, 2, 2, 3),
        vec![honest(FRUSTRATED, 1), honest(FRUSTRATED, 2)],
    );
    assert_eq!(report["code"], "SEARCH_INCOMPLETE");
    // A budget beyond any machine integer is a budget.
    let vast = enlarged(
        &task(FRUSTRATED, 2, 1, 77),
        vec![honest(FRUSTRATED, 4)],
        "session_evals",
        77,
    );
    let Outcome::Pass { result } = judge(&vast) else {
        panic!("expected a typed refusal");
    };
    assert_eq!(result["code"], "RESTRICTED_OBSTRUCTION");
}

#[test]
fn the_first_rule_broken_names_the_refusal() {
    let task = task(FRUSTRATED, 2, 3, 2);
    let key = key(FRUSTRATED);
    let other = key_of(FRUSTRATED, "[0,1,2,3]", "\"zero-one\"");
    let mut chain = sealed(&key, bodies(FRUSTRATED, 2));
    // Over budget only.
    broken(
        &task,
        vec![reply(chain.clone())],
        "SESSION_BUDGET_EXCEEDED",
        0,
    );
    // And a wrong status, a wrong spend, a wrong batch, a wrong seal, a wrong key.
    let mut bodies = bodies(FRUSTRATED, 2);
    for (field, value, code) in [
        ("status", json!("verified"), "STATUS_NOT_RECOMPUTED"),
        ("spent", json!(2), "BUDGET_RESET"),
        ("end", json!(5), "BATCH_NOT_LEXICOGRAPHIC"),
    ] {
        bodies[1][field] = value;
        chain = sealed(&key, bodies.clone());
        broken(&task, vec![reply(chain.clone())], code, 0);
    }
    chain[1]["seal"] = json!(sha("forged"));
    broken(&task, vec![reply(chain.clone())], "SEAL_MISMATCH", 0);
    chain[1]["key"] = json!(other);
    broken(
        &task,
        vec![reply(chain.clone())],
        "PRESENTATION_KEY_CHANGED",
        0,
    );
    // On resume, the same chain also fails to extend the one before it.
    let first = honest(FRUSTRATED, 1);
    let mut resumed = chain.clone();
    resumed[0]["note"] = json!("rewritten");
    broken(
        &task,
        vec![first.clone(), reply(resumed.clone())],
        "RESUME_DIVERGES_FROM_CHECKPOINT",
        1,
    );
    resumed[1]["index"] = json!(5);
    broken(
        &task,
        vec![first.clone(), reply(resumed.clone())],
        "CHAIN_NOT_CONTIGUOUS",
        1,
    );
    resumed[0]["index"] = json!(4);
    broken(
        &task,
        vec![first, reply(resumed)],
        "RESUME_NOT_REPLAYED_FROM_ZERO",
        1,
    );
}

#[test]
fn a_reply_without_a_chain_of_records_is_malformed() {
    let task = task(FRUSTRATED, 2, 3, 4);
    let wanted = "checkpoints must be a nonempty list of records";
    for reply in [
        json!({}),
        json!({"checkpoints": []}),
        json!({"checkpoints": "none"}),
        json!({"checkpoints": [7]}),
        json!({"checkpoints": [bodies(FRUSTRATED, 1)[0].clone(), null]}),
        json!({"chain": bodies(FRUSTRATED, 1)}),
        json!("no gauge"),
        json!([{"index": 0}]),
    ] {
        assert_eq!(malformed(&task, vec![reply.clone()]), wanted, "{reply}");
    }
    // A resumed session's reply is read as closely.
    assert_eq!(
        malformed(&task, vec![honest(FRUSTRATED, 1), json!({})]),
        wanted
    );
    let (_, report) = run(&task, vec![honest(FRUSTRATED, 1), json!({})]);
    assert_eq!(report["predicates"], json!([]));
}

/// A path on `vertices` vertices with every sign +1.
fn path(vertices: usize) -> Value {
    let edges: Vec<[usize; 2]> = (1..vertices).map(|vertex| [vertex - 1, vertex]).collect();
    json!({"edges": edges, "signs": vec![1; vertices - 1],
           "basis": (0..vertices).collect::<Vec<usize>>(), "representation": "pm1",
           "batch": 1, "max_sessions": 1, "session_evals": 1})
}

#[test]
fn a_task_has_at_most_sixteen_vertices() {
    assert_eq!(MAX_VERTICES, 16);
    assert_eq!(bad_task(path(17)), "at most 16 vertices");
    assert_eq!(ask(&path(16), vec![])["stage"], "search");
    // Every vertex +1 is candidate 0 of the 32768.
    let key = sha(&written(&json!({
        "basis": path(16)["basis"], "edges": path(16)["edges"],
        "representation": "pm1", "signs": path(16)["signs"]})));
    let chain = sealed(&key, vec![record(0, &key, 0, 1, Some(0))]);
    let (passed, report) = run(&path(16), vec![reply(chain)]);
    assert!(passed);
    assert_eq!(report["detail"], json!({"gauge": 0, "checkpoints": 1}));
}

#[test]
fn a_task_allows_at_most_sixty_four_sessions() {
    assert_eq!(MAX_SESSIONS, 64);
    assert_eq!(
        bad_task(task(BALANCED, 2, 65, 4)),
        "max_sessions must be at most 64"
    );
    let vast = enlarged(&task(BALANCED, 2, 77, 4), vec![], "max_sessions", 77);
    let Outcome::Refused { refusal } = next(&vast) else {
        panic!("expected a refused task");
    };
    assert_eq!(refusal.code, "BAD_TASK");
    assert_eq!(refusal.message, "max_sessions must be at most 64");
    assert_eq!(ask(&task(BALANCED, 2, 64, 4), vec![])["stage"], "search");
}

#[test]
fn the_signs_are_one_or_minus_one_on_every_edge() {
    let with = |signs: Value| {
        let mut task = task(BALANCED, 2, 3, 4);
        task["signs"] = signs;
        bad_task(task)
    };
    let wanted = "signs must be 1 or -1, one per edge";
    assert_eq!(with(json!([1, -1, -1])), wanted);
    assert_eq!(with(json!([1, -1, -1, 1, 1])), wanted);
    assert_eq!(with(json!([1, -1, 0, 1])), wanted);
    assert_eq!(with(json!([1, -1, 2, 1])), wanted);
    assert_eq!(with(json!([1, -1, -2, 1])), wanted);
    assert_eq!(with(json!([1, -1, "-1", 1])), wanted);
    assert_eq!(with(json!([1, -1, -1.0, 1])), wanted);
    assert_eq!(with(json!("+--+")), wanted);
    let mut missing = task(BALANCED, 2, 3, 4);
    missing.as_object_mut().expect("a task").remove("signs");
    assert_eq!(bad_task(missing), wanted);
}

#[test]
fn the_basis_lists_every_vertex_once() {
    let with = |basis: Value| {
        let mut task = task(BALANCED, 2, 3, 4);
        task["basis"] = basis;
        bad_task(task)
    };
    let wanted = "basis must list every vertex once";
    assert_eq!(with(json!([0, 1, 2])), wanted);
    assert_eq!(with(json!([0, 1, 2, 2])), wanted);
    assert_eq!(with(json!([0, 1, 2, 3, 3])), wanted);
    assert_eq!(with(json!([0, 1, 2, 4])), wanted);
    assert_eq!(with(json!([0, 1, 2, "3"])), wanted);
    assert_eq!(with(json!("0123")), wanted);
    let mut missing = task(BALANCED, 2, 3, 4);
    missing.as_object_mut().expect("a task").remove("basis");
    assert_eq!(bad_task(missing), wanted);
}

#[test]
fn the_three_bounds_are_positive_exact_integers() {
    for bound in ["batch", "max_sessions", "session_evals"] {
        let wanted = format!("{bound} must be a positive exact int");
        for stated in [json!(0), json!(-1), json!("2"), json!(2.0), json!(null)] {
            let mut task = task(BALANCED, 2, 3, 4);
            task[bound] = stated.clone();
            assert_eq!(bad_task(task), wanted, "{stated}");
        }
        let mut missing = task(BALANCED, 2, 3, 4);
        missing.as_object_mut().expect("a task").remove(bound);
        assert_eq!(bad_task(missing), wanted);
    }
    assert_eq!(ask(&task(BALANCED, 1, 1, 1), vec![])["stage"], "search");
}

#[test]
fn a_task_is_read_in_order() {
    let mut task = json!({"edges": [[0, 2]], "batch": 0, "max_sessions": 65,
                          "session_evals": 0});
    assert_eq!(bad_task(task.clone()), "vertices must be 0..n-1");
    task["edges"] = path(17)["edges"].clone();
    assert_eq!(bad_task(task.clone()), "at most 16 vertices");
    task["edges"] = parsed(EDGES);
    assert_eq!(
        bad_task(task.clone()),
        "signs must be 1 or -1, one per edge"
    );
    task["signs"] = parsed(BALANCED);
    assert_eq!(bad_task(task.clone()), "basis must list every vertex once");
    task["basis"] = json!([3, 2, 1, 0]);
    assert_eq!(bad_task(task.clone()), "representation required");
    task["representation"] = json!(null);
    assert_eq!(bad_task(task.clone()), "batch must be a positive exact int");
    task["batch"] = json!(1);
    assert_eq!(bad_task(task.clone()), "max_sessions must be at most 64");
    task["max_sessions"] = json!(0);
    assert_eq!(
        bad_task(task.clone()),
        "max_sessions must be a positive exact int"
    );
    task["max_sessions"] = json!(1);
    assert_eq!(
        bad_task(task.clone()),
        "session_evals must be a positive exact int"
    );
    task["session_evals"] = json!(1);
    assert_eq!(ask(&task, vec![])["stage"], "search");
    assert_eq!(
        bad_task(json!({"edges": []})),
        "edges must be a nonempty list of pairs of exact integers"
    );
}
