//! WF21, structural prompt rewriting: where the matches may stand, each predicate in the order
//! the host records it, the leak check, and the exact judging of the answer.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf21-tests:v1

use pfp_operads::families::wf21::{FAMILY, FENCES};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = concat!(
    "Please read the task.\n",
    "<<Q>>Compute det(M) for M = [[12, 5], [7, 263]].<</Q>>\n",
    r#"<<OUT>>Reply as {"answer": <int>}.<</OUT>>"#,
    "\nPlease be concise."
);

fn task() -> Value {
    json!({"statement": STATEMENT, "matrix": [[12, 5], [7, 263]]})
}

fn sealed() -> Value {
    json!({"answer_key": 3121})
}

/// The byte offset of `part` in the statement.
fn at(part: &str) -> usize {
    STATEMENT.find(part).expect("part of the statement")
}

fn edit(lhs: &str, rhs: &str, at: Value) -> Value {
    json!({"lhs": lhs, "rhs": rhs, "at": at})
}

/// A rewrite of the lead-in and the closing line, both outside the fences.
fn clean() -> Value {
    json!({"edits": [
        edit("Please read the task.", "Read the task below.", json!(0)),
        edit("Please be concise.", "Keep the reply short.", json!(at("Please be concise."))),
    ]})
}

const CLEAN_TEXT: &str = concat!(
    "Read the task below.\n",
    "<<Q>>Compute det(M) for M = [[12, 5], [7, 263]].<</Q>>\n",
    r#"<<OUT>>Reply as {"answer": <int>}.<</OUT>>"#,
    "\nKeep the reply short."
);

fn request(task: &Value, sealed: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF21", "task": task, "sealed": sealed, "replies": replies}).to_string()
}

fn some(replies: Vec<Value>) -> Vec<Option<Value>> {
    replies.into_iter().map(Some).collect()
}

fn judged(task: &Value, sealed: &Value, replies: Vec<Option<Value>>) -> (bool, Value) {
    match judge(&request(task, sealed, &replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

/// A run of this rewrite and this answer over the standard task.
fn run(rewrite: Value, answer: Value) -> (bool, Value) {
    judged(
        &task(),
        &sealed(),
        some(vec![rewrite, json!({ "answer": answer })]),
    )
}

/// A run that stops at the rewrite: its refusal, checked against the code.
fn refused(rewrite: Value, code: &str) -> Value {
    let (passed, report) = judged(&task(), &sealed(), some(vec![rewrite]));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], code);
    report
}

fn ask(task: &Value, sealed: &Value, replies: Vec<Value>) -> Value {
    match next(&request(task, sealed, &some(replies))) {
        Outcome::Pass { result } => result["ask"].clone(),
        other => panic!("expected a turn, got {other:?}"),
    }
}

fn bad_task(task: &Value, sealed: &Value) -> String {
    match next(&request(task, sealed, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

/// The reason of a run refused because a reply could not be read, and the predicates recorded.
fn malformed(replies: Vec<Value>) -> (String, usize) {
    let (passed, report) = judged(&task(), &sealed(), some(replies));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    let reason = report["detail"]["reason"].as_str().expect("a reason");
    (
        reason.to_owned(),
        report["predicates"].as_array().expect("predicates").len(),
    )
}

/// The predicates of a report as name and outcome, in the order they were recorded.
fn outcomes(report: &Value) -> Vec<(String, bool)> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| {
            (
                row["name"].as_str().expect("a name").to_owned(),
                row["passed"].as_bool().expect("an outcome"),
            )
        })
        .collect()
}

fn recorded(report: &Value, names: &[&str], last: bool) -> bool {
    let expected: Vec<(String, bool)> = names
        .iter()
        .enumerate()
        .map(|(index, name)| ((*name).to_owned(), last || index + 1 < names.len()))
        .collect();
    outcomes(report) == expected
}

#[test]
fn the_registry_names_the_family_and_its_fences() {
    assert_eq!(FAMILY.workflow, "WF21");
    assert_eq!(FAMILY.name, "Structural prompt rewriting");
    assert_eq!(FAMILY.host_check, "fenced_rewrite_exact_judge");
    assert_eq!(FENCES.len(), 2);
    assert_eq!(
        (FENCES[0].begin, FENCES[0].end, FENCES[0].name),
        ("<<Q>>", "<</Q>>", "question")
    );
    assert_eq!(
        (FENCES[1].begin, FENCES[1].end, FENCES[1].name),
        ("<<OUT>>", "<</OUT>>", "output")
    );
}

#[test]
fn a_rewrite_outside_the_fences_is_solved_and_certified() {
    let (passed, report) = run(clean(), json!(3121));
    assert!(passed, "{report}");
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "REWRITE_CERTIFIED");
    assert_eq!(
        report["detail"],
        json!({"rewritten_sha256": sha(CLEAN_TEXT)})
    );
    assert!(recorded(
        &report,
        &[
            "matches_exact",
            "match_injective",
            "edits_outside_fences",
            "protected_bytes_unchanged",
            "no_answer_key_leak",
            "answer_key_consistent",
            "answer_exact",
        ],
        true
    ));
    assert_eq!(report["every_predicate_passed"], true);
}

#[test]
fn each_predicate_carries_the_evidence_it_was_judged_on() {
    let (passed, report) = run(clean(), json!(3121));
    assert!(passed, "{report}");
    let lead = "Please read the task.".len();
    let close = at("Please be concise.");
    let pairs = json!([[0, lead], [close, close + "Please be concise.".len()]]).to_string();
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    assert_eq!(
        digests,
        [
            sha(&pairs),
            sha(&pairs),
            sha(&pairs),
            sha(&json!(CLEAN_TEXT).to_string()),
            sha("null"),
            sha("null"),
            sha(r#"{"answer":3121}"#),
        ]
    );
}

#[test]
fn the_rewrite_is_asked_for_first_and_the_rewritten_text_is_the_next_prompt() {
    let prompt = format!(
        "WF21 Structural prompt rewriting. {STATEMENT}\n{}",
        r#"{"matrix":[[12,5],[7,263]]}"#
    );
    let first = ask(&task(), &sealed(), vec![]);
    assert_eq!(first["stage"], "rewrite");
    assert_eq!(first["prompt"], prompt);
    assert_eq!(first["prompt_sha256"], sha(&prompt));
    let second = ask(&task(), &sealed(), vec![clean()]);
    assert_eq!(second["stage"], "solve");
    assert_eq!(second["prompt"], CLEAN_TEXT);
    assert_eq!(second["prompt_sha256"], sha(CLEAN_TEXT));
}

#[test]
fn an_empty_rewrite_leaves_the_statement_as_it_was() {
    let (passed, report) = run(json!({"edits": []}), json!(3121));
    assert!(passed, "{report}");
    assert_eq!(
        report["detail"],
        json!({"rewritten_sha256": sha(STATEMENT)})
    );
}

#[test]
fn adjacent_matches_and_matches_beside_a_fence_are_allowed() {
    let rewrite = json!({"edits": [
        edit("Please", "Kindly", json!(0)),
        edit(" read", " scan", json!(6)),
        edit("task.\n", "page.\n", json!(at("task.\n"))),
        edit("\n", " ", json!(at("<</Q>>") + 6)),
    ]});
    let (passed, report) = run(rewrite, json!(3121));
    assert!(passed, "{report}");
    let text = "Kindly scan the page.\n<<Q>>Compute det(M) for M = [[12, 5], [7, 263]].<</Q>> \
                <<OUT>>Reply as {\"answer\": <int>}.<</OUT>>\nPlease be concise.";
    assert_eq!(report["detail"], json!({"rewritten_sha256": sha(text)}));
}

#[test]
fn matches_may_be_given_in_any_order() {
    let rewrite = json!({"edits": [
        edit("Please be concise.", "Keep the reply short.", json!(at("Please be concise."))),
        edit("Please read the task.", "Read the task below.", json!(0)),
    ]});
    let (passed, report) = run(rewrite, json!(3121));
    assert!(passed, "{report}");
    assert_eq!(
        report["detail"],
        json!({"rewritten_sha256": sha(CLEAN_TEXT)})
    );
}

#[test]
fn offsets_and_lengths_are_in_bytes() {
    let statement = "Café: <<Q>>Compute.<</Q>> <<OUT>>Reply.<</OUT>> Merci.";
    let task = json!({"statement": statement, "matrix": [[2, 1], [1, 3]]});
    let sealed = json!({"answer_key": 5});
    let position = |part: &str| statement.find(part).expect("part");
    let rewrite = json!({"edits": [
        edit("é", "e", json!(position("é"))),
        edit("Merci.", "Thanks.", json!(position("Merci."))),
    ]});
    let replies = some(vec![rewrite, json!({"answer": 5})]);
    let (passed, report) = judged(&task, &sealed, replies);
    assert!(passed, "{report}");
    let text = "Cafe: <<Q>>Compute.<</Q>> <<OUT>>Reply.<</OUT>> Thanks.";
    assert_eq!(report["detail"], json!({"rewritten_sha256": sha(text)}));
}

#[test]
fn a_match_that_is_not_where_it_says_is_no_match() {
    let end = STATEMENT.len();
    for rewrite in [
        edit("Please", "Kindly", json!(1)),
        edit("Please", "Kindly", json!(-1)),
        edit("Please", "Kindly", json!(end + 1)),
        edit("Please", "Kindly", json!(end)),
        edit("concise.!", "short", json!(end - 8)),
        edit("e.", "e!", json!(end - 1)),
        edit(
            "Please be concise.",
            "Short.",
            json!(-i64::try_from(at("Please be concise.")).expect("a small position")),
        ),
    ] {
        let report = refused(json!({"edits": [rewrite.clone()]}), "NO_MATCH");
        assert_eq!(report["detail"], json!({}));
        assert_eq!(outcomes(&report), vec![("matches_exact".to_owned(), false)]);
    }
}

#[test]
fn a_match_that_runs_past_the_largest_position_is_no_match_and_is_not_shown() {
    for position in [u64::MAX, u64::MAX - 2] {
        let rewrite = json!({"edits": [edit("Please", "Kindly", json!(position))]});
        let report = refused(rewrite, "NO_MATCH");
        assert_eq!(outcomes(&report), vec![("matches_exact".to_owned(), false)]);
        assert_eq!(report["predicates"][0]["evidence_sha256"], sha("[]"));
    }
}

#[test]
fn a_position_too_large_to_count_is_no_match() {
    for position in ["100000000000000000000000", "-100000000000000000000000"] {
        let rewrite = json!({"edits": [edit("Please", "Kindly", json!(424_242))]});
        let text = request(&task(), &sealed(), &some(vec![rewrite]));
        let text = text.replace("424242", position);
        let Outcome::Fail { result } = judge(&text) else {
            panic!("expected a refused verdict");
        };
        assert_eq!(result["code"], "NO_MATCH", "{position}");
        assert_eq!(result["detail"], json!({}));
    }
}

#[test]
fn one_match_in_the_wrong_place_refuses_the_whole_rewrite() {
    let rewrite = json!({"edits": [
        edit("Please read the task.", "Read.", json!(0)),
        edit("Please be concise.", "Short.", json!(0)),
    ]});
    refused(rewrite, "NO_MATCH");
}

#[test]
fn matches_that_overlap_are_refused_before_their_places_are_looked_at() {
    let rewrite = json!({"edits": [
        edit("Please", "Kindly", json!(0)),
        edit("Please read", "Read", json!(0)),
    ]});
    let report = refused(rewrite, "OVERLAPPING_MATCHES");
    assert!(recorded(
        &report,
        &["matches_exact", "match_injective"],
        false
    ));
    let inner = json!({"edits": [
        edit("Please read the task.", "Read.", json!(0)),
        edit("read", "scan", json!(7)),
    ]});
    refused(inner, "OVERLAPPING_MATCHES");
}

#[test]
fn an_edit_in_a_fence_is_refused_after_the_matches_are_known_good() {
    let inside = at("263");
    for rewrite in [
        edit("263", "264", json!(inside)),
        edit("<<Q>>", "<<Q>>Hint: ", json!(at("<<Q>>"))),
        edit("<</Q>>", "<</Q>> ", json!(at("<</Q>>"))),
        edit("task.\n<<Q>>", "task. ", json!(at("task.\n<<Q>>"))),
        edit("<</Q>>\n<<OUT>>", "", json!(at("<</Q>>\n<<OUT>>"))),
        edit("<int>", "<float>", json!(at("<int>"))),
        edit(
            "<</OUT>>\nPlease",
            "<</OUT>> Please",
            json!(at("<</OUT>>\nPlease")),
        ),
    ] {
        let report = refused(json!({"edits": [rewrite.clone()]}), "EDIT_INSIDE_FENCE");
        assert_eq!(report["detail"], json!({}));
        assert!(
            recorded(
                &report,
                &["matches_exact", "match_injective", "edits_outside_fences"],
                false
            ),
            "{rewrite}"
        );
    }
}

#[test]
fn a_rewrite_that_carries_a_fence_twice_does_not_preserve_it() {
    let question = &STATEMENT[at("<<Q>>")..at("<</Q>>") + 6];
    let output = &STATEMENT[at("<<OUT>>")..at("<</OUT>>") + 8];
    let tail = json!(at("Please be concise."));
    for (rhs, lost) in [
        (question.to_owned(), json!(["question"])),
        (output.to_owned(), json!(["output"])),
        (
            format!("{question} {output}"),
            json!(["question", "output"]),
        ),
    ] {
        let rewrite = json!({"edits": [edit("Please be concise.", &rhs, tail.clone())]});
        let report = refused(rewrite, "QUESTION_NOT_PRESERVED");
        assert_eq!(report["detail"], json!({ "violations": lost }));
        assert!(recorded(
            &report,
            &[
                "matches_exact",
                "match_injective",
                "edits_outside_fences",
                "protected_bytes_unchanged",
            ],
            false
        ));
    }
}

#[test]
fn a_rewrite_that_names_the_answer_key_is_refused() {
    for rhs in ["Hint: it is 3121.", "3121", "The key is 3121 exactly"] {
        let rewrite = json!({"edits": [
            edit("Please be concise.", rhs, json!(at("Please be concise."))),
        ]});
        let report = refused(rewrite, "ANSWER_KEY_LEAK");
        assert_eq!(report["detail"], json!({}));
        assert!(recorded(
            &report,
            &[
                "matches_exact",
                "match_injective",
                "edits_outside_fences",
                "protected_bytes_unchanged",
                "no_answer_key_leak",
            ],
            false
        ));
    }
}

#[test]
fn a_key_is_looked_for_as_text_wherever_it_occurs() {
    let rewrite = json!({"edits": [
        edit("Please be concise.", "Reference 13121x.", json!(at("Please be concise."))),
    ]});
    refused(rewrite, "ANSWER_KEY_LEAK");
    let text_key = json!({"answer_key": "6242/2"});
    let sealed_task = judged(
        &task(),
        &text_key,
        some(vec![json!({"edits": [
            edit("Please be concise.", "Cf. 6242/2.", json!(at("Please be concise."))),
        ]})]),
    );
    assert_eq!(sealed_task.1["code"], "ANSWER_KEY_LEAK");
}

#[test]
fn a_short_key_is_found_inside_a_word_whether_it_is_given_as_a_number_or_as_text() {
    let statement = "Café: <<Q>>Compute.<</Q>> <<OUT>>Reply.<</OUT>> Merci.";
    let task = json!({"statement": statement, "matrix": [[2, 1], [1, 3]]});
    let place = statement.find("Merci.").expect("part");
    for key in [json!(5), json!("5")] {
        let sealed = json!({"answer_key": key});
        let rewrite = json!({"edits": [edit("Merci.", "Merci5y.", json!(place))]});
        let (passed, report) = judged(&task, &sealed, some(vec![rewrite]));
        assert!(!passed, "{key}");
        assert_eq!(report["code"], "ANSWER_KEY_LEAK", "{key}");
    }
}

#[test]
fn any_sealed_value_in_the_rewrite_is_a_leak() {
    let sealed = json!({"answer_key": 3121, "note": "hunter2"});
    let rewrite = json!({"edits": [
        edit("Please be concise.", "Use hunter2.", json!(at("Please be concise."))),
    ]});
    let (passed, report) = judged(&task(), &sealed, some(vec![rewrite]));
    assert!(!passed);
    assert_eq!(report["code"], "ANSWER_KEY_LEAK");
}

#[test]
fn a_wrong_answer_fails_the_exact_judge() {
    let (passed, report) = run(clean(), json!(3122));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "ANSWER_EXACT");
    let rows = outcomes(&report);
    assert_eq!(rows[5], ("answer_key_consistent".to_owned(), true));
    assert_eq!(rows[6], ("answer_exact".to_owned(), false));
}

#[test]
fn a_sealed_key_that_is_not_the_determinant_fails_its_own_check() {
    let sealed = json!({"answer_key": 3120});
    let replies = some(vec![clean(), json!({"answer": 3121})]);
    let (passed, report) = judged(&task(), &sealed, replies);
    assert!(!passed);
    assert_eq!(report["code"], "ANSWER_KEY_CONSISTENT");
    let rows = outcomes(&report);
    assert_eq!(rows[5], ("answer_key_consistent".to_owned(), false));
    assert_eq!(rows[6], ("answer_exact".to_owned(), true));
}

#[test]
fn an_answer_may_be_written_as_any_exact_rational() {
    for answer in [json!("3121"), json!("6242/2"), json!("3121/1")] {
        let (passed, report) = run(clean(), answer.clone());
        assert!(passed, "{answer}: {report}");
    }
}

/// A run of a statement with no digits, so that a short key cannot be found in it.
fn plain(matrix: &Value, key: &Value, answer: &Value) -> (bool, Value) {
    let statement =
        "<<Q>>Find the determinant.<</Q>> <<OUT>>Reply as an integer.<</OUT>> Be brief.";
    let task = json!({"statement": statement, "matrix": matrix});
    let rewrite =
        json!({"edits": [edit("Be brief.", "Be short.", json!(at_in(statement, "Be brief.")))]});
    let replies = some(vec![rewrite, json!({"answer": answer})]);
    judged(&task, &json!({"answer_key": key}), replies)
}

fn at_in(text: &str, part: &str) -> usize {
    text.find(part).expect("part")
}

#[test]
fn the_determinant_is_exact_for_any_square_matrix() {
    let cases = [
        (json!([[1, 2], [2, 4]]), json!(0)),
        (json!([[1, 1], [1, 1]]), json!(0)),
        (json!([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), json!(0)),
        (json!([[2, 1], [1, 3]]), json!(5)),
        (json!([["1/2", 1], [3, 4]]), json!(-1)),
        (json!([[1, 2, 3], [2, 4, 5], [1, 1, 1]]), json!(-1)),
        (json!([[2, 1, 1], [1, 3, 2], [1, 0, 4]]), json!(19)),
        (json!([[0, 1], [1, 0]]), json!(-1)),
        (json!([[0, 2], [3, 0]]), json!(-6)),
        (json!([[2, 0], [0, 3]]), json!(6)),
        (json!([[0, 0, 2], [0, 3, 0], [4, 0, 0]]), json!(-24)),
        (json!([["14/2"]]), json!(7)),
        (json!([[2, 4], [8, 16]]), json!(0)),
        (json!([]), json!(1)),
    ];
    for (matrix, key) in cases {
        let (passed, report) = plain(&matrix, &key, &key);
        assert!(passed, "{matrix}: {report}");
    }
}

#[test]
fn a_wrong_determinant_is_refused_for_every_kind_of_matrix() {
    for (matrix, key, wrong) in [
        (json!([[2, 1], [1, 3]]), json!(5), json!(-5)),
        (json!([[0, 1], [1, 0]]), json!(-1), json!(1)),
        (json!([[0, 2], [3, 0]]), json!(-6), json!(6)),
        (json!([[1, 2], [2, 4]]), json!(0), json!(1)),
    ] {
        let (passed, report) = plain(&matrix, &key, &wrong);
        assert!(!passed, "{matrix}");
        assert_eq!(report["code"], "ANSWER_EXACT", "{matrix}");
        let rows = outcomes(&report);
        assert_eq!(
            rows[5],
            ("answer_key_consistent".to_owned(), true),
            "{matrix}"
        );
    }
}

#[test]
fn a_rewrite_that_cannot_be_read_is_malformed_before_any_predicate() {
    let bad_edits = [
        json!({}),
        json!({"edits": "none"}),
        json!({"edits": {"lhs": "Please", "rhs": "Kindly", "at": 0}}),
        json!("a rewrite"),
        json!({"edits": [5]}),
        json!({"edits": [{"rhs": "Kindly", "at": 0}]}),
        json!({"edits": [{"lhs": "", "rhs": "Kindly", "at": 0}]}),
        json!({"edits": [{"lhs": 3, "rhs": "Kindly", "at": 0}]}),
        json!({"edits": [{"lhs": "Please", "at": 0}]}),
        json!({"edits": [{"lhs": "Please", "rhs": 3, "at": 0}]}),
    ];
    for rewrite in bad_edits {
        let (reason, rows) = malformed(vec![rewrite.clone()]);
        assert!(
            reason == "edits list required" || reason == "edits are {lhs, rhs, at}",
            "{rewrite}: {reason}"
        );
        assert_eq!(rows, 0, "{rewrite}");
    }
    for position in [json!(1.5), json!("0"), json!(true), json!(null)] {
        let rewrite = json!({"edits": [
            edit("Please", "Kindly", position.clone()),
        ]});
        let (reason, rows) = malformed(vec![rewrite]);
        assert_eq!(reason, "at must be an exact int", "{position}");
        assert_eq!(rows, 0);
    }
    let missing = json!({"edits": [{"lhs": "Please", "rhs": "Kindly"}]});
    let (reason, _) = malformed(vec![missing]);
    assert_eq!(reason, "at must be an exact int");
}

#[test]
fn one_unreadable_edit_stops_the_rewrite_even_after_a_good_one() {
    let rewrite = json!({"edits": [
        edit("Please read the task.", "Read.", json!(0)),
        {"lhs": "x", "rhs": "y", "at": 1.5},
    ]});
    let (reason, rows) = malformed(vec![rewrite]);
    assert_eq!(reason, "at must be an exact int");
    assert_eq!(rows, 0);
}

#[test]
fn an_answer_that_cannot_be_read_is_malformed_after_the_rewrite_is_checked() {
    for answer in [
        json!({}),
        json!({"answer": 3121.0}),
        json!({"answer": null}),
        json!({"answer": "many"}),
        json!({"answer": true}),
        json!("3121"),
    ] {
        let (reason, rows) = malformed(vec![clean(), answer.clone()]);
        assert_eq!(reason, "answer must be an exact rational", "{answer}");
        assert_eq!(rows, 5, "{answer}");
    }
}

#[test]
fn a_missing_reply_is_refused_wherever_it_is_missing() {
    let (passed, report) = judged(&task(), &sealed(), vec![None]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "NO_ADMISSIBLE_REPLY");
    assert!(outcomes(&report).is_empty());
    let (passed, report) = judged(&task(), &sealed(), vec![Some(clean()), None]);
    assert!(!passed);
    assert_eq!(report["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(outcomes(&report).len(), 5);
}

#[test]
fn a_task_the_host_cannot_read_is_a_bad_task() {
    let with = |key: &str, value: Value| {
        let mut changed = task();
        changed[key] = value;
        changed
    };
    let cases = [
        (
            with("statement", json!(7)),
            sealed(),
            "statement must be text",
        ),
        (
            with("statement", json!("no fences")),
            sealed(),
            "FENCE_MARKERS_NOT_UNIQUE: the question fence",
        ),
        (
            with("statement", json!("<<Q>>only a question<</Q>>")),
            sealed(),
            "FENCE_MARKERS_NOT_UNIQUE: the output fence",
        ),
        (
            with(
                "statement",
                json!("<<Q>>a<</Q>> <<Q>>b<</Q>> <<OUT>>c<</OUT>>"),
            ),
            sealed(),
            "FENCE_MARKERS_NOT_UNIQUE: the question fence",
        ),
        (with("matrix", json!(4)), sealed(), "matrix must be square"),
        (
            with("matrix", json!([[1, 2]])),
            sealed(),
            "matrix must be square",
        ),
        (
            with("matrix", json!([[1, 2], [3]])),
            sealed(),
            "matrix must be square",
        ),
        (
            with("matrix", json!([[1, 2], [3, 4.5]])),
            sealed(),
            "matrix must be square",
        ),
        (
            with("matrix", json!([1, 2])),
            sealed(),
            "matrix must be square",
        ),
    ];
    for (case, sealed, expected) in cases {
        let message = bad_task(&case, &sealed);
        assert!(message.contains(expected), "{message}");
    }
    let mut no_statement = task();
    no_statement
        .as_object_mut()
        .expect("an object")
        .remove("statement");
    assert!(bad_task(&no_statement, &sealed()).contains("statement must be text"));
    let mut no_matrix = task();
    no_matrix
        .as_object_mut()
        .expect("an object")
        .remove("matrix");
    assert!(bad_task(&no_matrix, &sealed()).contains("matrix must be square"));
}

#[test]
fn a_sealed_part_without_a_usable_key_is_refused_before_anything_is_asked() {
    for (held, reason) in [
        (json!({}), "answer_key required"),
        (
            json!({"answer_key": 1.5}),
            "answer_key must be an exact rational",
        ),
        (
            json!({"answer_key": "three"}),
            "answer_key must be an exact rational",
        ),
        (
            json!({"answer_key": null}),
            "answer_key must be an exact rational",
        ),
        (json!({"key": 3121}), "answer_key required"),
    ] {
        match next(&request(&task(), &held, &[])) {
            Outcome::Pass { result } => assert_eq!(result["ask"], Value::Null, "{held}"),
            other => panic!("expected a turn, got {other:?}"),
        }
        let (passed, report) = judged(&task(), &held, vec![]);
        assert!(!passed, "{held}");
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "MALFORMED_CANDIDATE");
        assert_eq!(report["detail"]["reason"], reason, "{held}");
        assert!(outcomes(&report).is_empty());
    }
}
