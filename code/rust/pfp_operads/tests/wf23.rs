//! WF23, judge-packet custody audit: the manifest, the views in which the answer is looked
//! for, the sealed checker, the keyed tags on the judge's output, and the order the host
//! records them in.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf23-tests:v1

use pfp_operads::families::wf23::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// A file as the host hashes it.
fn file_hash(text: &str) -> String {
    sha(&text.replace("\r\n", "\n"))
}

const STATEMENT: &str = "Submit the participant packet and the judge run record.";

const CHECKER: &str = "def check(answer):\r\n    return answer == det([[12, 5], [7, 263]])\r\n";

const KEY: &str = "stdout-key-wf23";

const LINE: &str = "ITEM det2 PASS";

fn files() -> Value {
    json!({
        "task.txt": "Compute det(M) for M = [[12, 5], [7, 263]].",
        "format.txt": "Reply with one integer.",
    })
}

fn manifest(files: &Value) -> Value {
    let hashes: Map<String, Value> = files
        .as_object()
        .expect("files")
        .iter()
        .map(|(name, text)| (name.clone(), json!(file_hash(text.as_str().expect("text")))))
        .collect();
    Value::Object(hashes)
}

fn tag(key: &str, line: &Value) -> String {
    sha(&format!("{key}\u{0}{line}"))
}

fn sealed() -> Value {
    json!({
        "expected_answer": 3121,
        "checker_source": CHECKER,
        "recorded_checker_sha256": file_hash(CHECKER),
        "stdout_key": KEY,
        "manifest": manifest(&files()),
    })
}

fn record() -> Value {
    json!({
        "executed_checker_sha256": file_hash(CHECKER),
        "stdout": [{"line": LINE, "tag": tag(KEY, &json!(LINE))}],
    })
}

fn packet() -> Value {
    json!({"participant": files(), "run": record()})
}

fn task() -> Value {
    json!({"statement": STATEMENT})
}

fn request(task: &Value, sealed: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF23", "task": task, "sealed": sealed, "replies": replies}).to_string()
}

fn judged(sealed: &Value, replies: Vec<Option<Value>>) -> (bool, Value) {
    match judge(&request(&task(), sealed, &replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

/// A run of this packet over this sealed part.
fn audit(sealed: &Value, packet: Value) -> (bool, Value) {
    judged(sealed, vec![Some(packet)])
}

/// A run of this packet over the sealed part of `files`, with the manifest the host recorded.
fn with_files(participant: &Value) -> (bool, Value) {
    let mut held = sealed();
    held["manifest"] = manifest(participant);
    audit(&held, json!({"participant": participant, "run": record()}))
}

/// Honest files with one more, `notes.txt`, holding this text.
fn with_notes(text: &str) -> (bool, Value) {
    let mut participant = files();
    participant["notes.txt"] = json!(text);
    with_files(&participant)
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

const NAMES: [&str; 6] = [
    "manifest_complete",
    "file_hashes_match",
    "answer_not_derivable",
    "recorded_hash_is_checker",
    "executed_checker_is_recorded",
    "stdout_lines_authentic",
];

/// The six predicates, every one passing but those named.
fn all_but(failed: &[&str]) -> Vec<(String, bool)> {
    NAMES
        .iter()
        .map(|name| ((*name).to_owned(), !failed.contains(name)))
        .collect()
}

/// A run that fails these predicates and no others, under the code of the first of them.
fn fails(report: &(bool, Value), failed: &[&str]) {
    let (passed, report) = report;
    assert!(!passed, "{report}");
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], failed[0].to_uppercase(), "{report}");
    assert_eq!(outcomes(report), all_but(failed), "{report}");
}

fn passes(report: &(bool, Value)) {
    let (passed, report) = report;
    assert!(passed, "{report}");
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CUSTODY_INTACT");
    assert_eq!(outcomes(report), all_but(&[]));
}

/// The names of the files a report says held the answer.
fn leaked(report: &(bool, Value)) -> Value {
    report.1["detail"]["leaked_files"].clone()
}

/// The reason of a run refused because a reply could not be read, and how many predicates were
/// recorded before that.
fn malformed(packet: Value) -> (String, usize) {
    let (passed, report) = audit(&sealed(), packet);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    let reason = report["detail"]["reason"].as_str().expect("a reason");
    (reason.to_owned(), outcomes(&report).len())
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF23");
    assert_eq!(FAMILY.name, "Judge-packet custody audit");
    assert_eq!(FAMILY.host_check, "judge_packet_custody_audit");
}

#[test]
fn a_clean_packet_is_certified_with_its_digest() {
    let report = audit(&sealed(), packet());
    passes(&report);
    let hashes = format!(
        r#"{{"format.txt":"{}","task.txt":"{}"}}"#,
        file_hash("Reply with one integer."),
        file_hash("Compute det(M) for M = [[12, 5], [7, 263]].")
    );
    assert_eq!(
        report.1["detail"],
        json!({"participant_sha256": sha(&hashes), "leaked_files": [], "forged_lines": 0})
    );
    assert_eq!(report.1["every_predicate_passed"], true);
    assert_eq!(report.1["asked"].as_array().expect("asked").len(), 1);
    assert_eq!(report.1["asked"][0]["stage"], "packet");
}

#[test]
fn the_packet_is_asked_for_with_the_statement_only() {
    let prompt = format!("WF23 Judge-packet custody audit. {STATEMENT}\n{{}}");
    match next(&request(&task(), &sealed(), &[])) {
        Outcome::Pass { result } => {
            assert_eq!(result["ask"]["stage"], "packet");
            assert_eq!(result["ask"]["prompt"], prompt);
            assert_eq!(result["ask"]["prompt_sha256"], sha(&prompt));
        }
        other => panic!("expected a turn, got {other:?}"),
    }
}

#[test]
fn a_prompt_that_carries_a_sealed_value_is_not_sent() {
    let leaky = json!({"statement": "The checker says return answer == det, and 3121 is it."});
    match next(&request(&leaky, &sealed(), &[])) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "SEALED_LEAK"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn a_manifest_in_the_reply_is_not_read() {
    let mut edited = files();
    edited["format.txt"] = json!("Reply with one integer or a guess.");
    let mut packet = json!({"participant": edited, "run": record()});
    packet["manifest"] = manifest(&edited);
    fails(&audit(&sealed(), packet), &["file_hashes_match"]);
}

#[test]
fn a_file_edited_after_the_manifest_fails_its_hash() {
    let mut edited = files();
    edited["format.txt"] = json!("Reply with one integer or a guess.");
    fails(
        &audit(&sealed(), json!({"participant": edited, "run": record()})),
        &["file_hashes_match"],
    );
}

#[test]
fn a_file_the_manifest_does_not_list_fails_both_its_checks() {
    let mut more = files();
    more["extra.txt"] = json!("one more");
    fails(
        &audit(&sealed(), json!({"participant": more, "run": record()})),
        &["manifest_complete", "file_hashes_match"],
    );
}

#[test]
fn a_file_missing_from_the_reply_fails_the_manifest_only() {
    let mut fewer = files();
    fewer.as_object_mut().expect("files").remove("format.txt");
    fails(
        &audit(&sealed(), json!({"participant": fewer, "run": record()})),
        &["manifest_complete"],
    );
}

#[test]
fn line_endings_do_not_change_a_files_hash() {
    let participant = json!({"a.txt": "one\r\ntwo\r\nthree", "b.txt": "x\ry\r\r\nz"});
    let mut held = sealed();
    held["manifest"] = json!({
        "a.txt": sha("one\ntwo\nthree"),
        "b.txt": sha("x\ry\r\nz"),
    });
    passes(&audit(
        &held,
        json!({"participant": participant, "run": record()}),
    ));
}

#[test]
fn the_expected_answer_in_a_file_is_a_leak() {
    let report = with_notes("Hint: the answer is 3121.");
    fails(&report, &["answer_not_derivable"]);
    assert_eq!(leaked(&report), json!(["notes.txt"]));
    assert_eq!(report.1["detail"]["forged_lines"], 0);
    assert_eq!(
        report.1["detail"]["failed"],
        json!(["answer_not_derivable"])
    );
    passes(&with_notes("Hint: the answer is 3122."));
}

#[test]
fn the_answer_is_found_in_the_text_reversed() {
    fails(&with_notes("backwards: 1213"), &["answer_not_derivable"]);
}

#[test]
fn the_answer_is_found_with_white_space_taken_out() {
    for notes in [
        "3 1 2 1",
        "3\n1\t2\r\n1",
        "3\u{1c}1\u{1d}2\u{1e}1\u{1f}",
        "3\u{1c}1\u{1c}2\u{1c}1",
        "3\u{1f}1\u{1f}2\u{1f}1",
        "3\u{a0}1\u{85}2\u{3000}1\u{2003}",
        "3\u{2028}1\u{2029}2\u{202f}1\u{205f}\u{1680}",
        "3\u{b}1\u{c}2 1",
    ] {
        let report = with_notes(notes);
        assert_eq!(leaked(&report), json!(["notes.txt"]), "{notes:?}");
        fails(&report, &["answer_not_derivable"]);
    }
}

#[test]
fn a_character_that_is_not_white_space_does_not_join_the_digits() {
    for notes in [
        "3\u{200b}1\u{200b}2\u{200b}1",
        "3\u{180e}1\u{180e}2\u{180e}1",
        "3-1-2-1",
        "3\u{1b}1\u{1b}2\u{1b}1",
    ] {
        assert_eq!(leaked(&with_notes(notes)), json!([]), "{notes:?}");
    }
}

#[test]
fn the_answer_is_found_in_base64() {
    for notes in [
        "cache: MzEyMQ==",
        "MzEyMQ==",
        "x MzEyMQ== y",
        "(dGhlIGFuc3dlciBpcyAzMTIx)",
        "MzEyMQ==\nMzEyMQ==",
    ] {
        let report = with_notes(notes);
        assert_eq!(leaked(&report), json!(["notes.txt"]), "{notes:?}");
        fails(&report, &["answer_not_derivable"]);
    }
}

/// The evidence digests of a report, in the order the predicates were recorded.
fn digests(report: &(bool, Value)) -> Vec<String> {
    report.1["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| {
            row["evidence_sha256"]
                .as_str()
                .expect("a digest")
                .to_owned()
        })
        .collect()
}

#[test]
fn the_evidence_of_a_predicate_is_what_it_was_judged_on() {
    let null = sha("null");
    let clean = digests(&audit(&sealed(), packet()));
    assert_eq!(
        clean,
        [
            null.clone(),
            null.clone(),
            sha("[]"),
            null.clone(),
            null.clone(),
            sha("0")
        ]
    );
    let leaking = digests(&with_notes("1213"));
    assert_eq!(leaking[2], sha(r#"["notes.txt"]"#));
    let mut run = record();
    run["stdout"] = json!([
        {"line": LINE, "tag": "forged"},
        {"line": "ITEM det3 PASS", "tag": "forged too"},
    ]);
    let forged = digests(&audit(
        &sealed(),
        json!({"participant": files(), "run": run}),
    ));
    assert_eq!(forged[5], sha("2"));
}

#[test]
fn every_kind_of_base64_digit_is_read() {
    for notes in ["MzEyMTBZ", "MzEyMTA9", "MzEyMT4+", "MzEyMT8/", "MzEyMSA="] {
        assert_eq!(leaked(&with_notes(notes)), json!(["notes.txt"]), "{notes}");
    }
}

#[test]
fn a_token_of_four_characters_is_read() {
    let mut participant = files();
    participant["notes.txt"] = json!("OA==");
    let mut held = sealed();
    held["expected_answer"] = json!(8);
    held["manifest"] = manifest(&participant);
    let report = audit(&held, json!({"participant": participant, "run": record()}));
    assert_eq!(leaked(&report), json!(["notes.txt"]));
}

#[test]
fn base64_must_be_strict_to_be_read() {
    for notes in [
        "MzEyMQ",
        "MzEyMQ=",
        "MzEyMQ===",
        "MzEy MQ==",
        "Mz=EyMQ=",
        "xxMzEyMQ==",
        "MzEyMQ==x",
        "MzEyM===",
        "MzEyMXh4A===",
        "MzEyMS=zMTIx",
        "MzEy",
        "key=MzEyMQ==.",
    ] {
        assert_eq!(leaked(&with_notes(notes)), json!([]), "{notes:?}");
    }
}

#[test]
fn a_token_ends_at_the_first_character_outside_the_base64_alphabet() {
    for notes in ["-MzEyMQ==", "MzEyMQ==_", "MzEyMQ==.", "MzEyMQ==\u{e9}"] {
        assert_eq!(
            leaked(&with_notes(notes)),
            json!(["notes.txt"]),
            "{notes:?}"
        );
    }
    assert_eq!(leaked(&with_notes("MzEyMQ_=")), json!([]));
    assert_eq!(leaked(&with_notes("MzEy.MQ==")), json!([]));
}

#[test]
fn text_that_is_not_utf8_once_decoded_is_not_a_view() {
    for notes in ["MzEyMf8=", "33313231ff", "MzEyMQ==/w==", "gzEyMQ=="] {
        assert_eq!(leaked(&with_notes(notes)), json!([]), "{notes:?}");
    }
}

#[test]
fn the_answer_is_found_in_hex() {
    for notes in [
        "33313231",
        "hex 33313231 done",
        "74686520616E73776572206973203331323131",
        "33 31 32 31 and 33313231",
    ] {
        let report = with_notes(notes);
        assert_eq!(leaked(&report), json!(["notes.txt"]), "{notes:?}");
        fails(&report, &["answer_not_derivable"]);
    }
}

#[test]
fn hex_must_be_whole_bytes_to_be_read() {
    for notes in [
        "0x33313231",
        "A33313231",
        "74686520616e73776572206973203331323",
        "7468652061 6e73776572 3331 3231",
        "3331323",
    ] {
        assert_eq!(leaked(&with_notes(notes)), json!([]), "{notes:?}");
    }
}

#[test]
fn the_answer_is_found_inside_a_longer_number() {
    fails(
        &with_notes("order 931214 shipped"),
        &["answer_not_derivable"],
    );
    assert_eq!(leaked(&with_notes("3 121")), json!(["notes.txt"]));
    assert_eq!(leaked(&with_notes("312")), json!([]));
}

#[test]
fn every_file_is_searched_and_the_leaks_are_listed_by_name() {
    let mut participant = files();
    participant["b.txt"] = json!("the answer is 3121");
    participant["é.txt"] = json!("MzEyMQ==");
    participant["a.txt"] = json!("1213");
    participant["clean.txt"] = json!("nothing to see");
    let report = with_files(&participant);
    assert_eq!(leaked(&report), json!(["a.txt", "b.txt", "é.txt"]));
    fails(&report, &["answer_not_derivable"]);
}

#[test]
fn the_answer_is_written_as_an_integer_or_as_a_ratio() {
    let cases = [
        (json!("7/2"), "ratio 7/2 here", true),
        (json!("7/2"), "the number 72 and 7 and 2", false),
        (json!("14/4"), "ratio 7/2 here", true),
        (json!("6/2"), "has a 3 in it", true),
        (json!("6/2"), "no digit here", false),
        (json!(-5), "minus -5 here", true),
        (json!(-5), "plus 5 here", false),
        (json!("-10/4"), "see -5/2", true),
        (json!("0"), "zero 0 here", true),
    ];
    for (answer, notes, expected) in cases {
        let mut participant = files();
        participant["notes.txt"] = json!(notes);
        let mut held = sealed();
        held["expected_answer"] = answer.clone();
        held["manifest"] = manifest(&participant);
        let report = audit(&held, json!({"participant": participant, "run": record()}));
        let names = report.1["detail"]["leaked_files"]
            .as_array()
            .expect("names");
        let found = names.iter().any(|name| name == "notes.txt");
        assert_eq!(found, expected, "{answer} in {notes:?}: {}", report.1);
    }
}

#[test]
fn a_recorded_hash_that_is_not_the_checkers_fails_its_check() {
    let mut held = sealed();
    held["recorded_checker_sha256"] = json!(sha("another checker"));
    let mut run = record();
    run["executed_checker_sha256"] = json!(sha("another checker"));
    fails(
        &audit(&held, json!({"participant": files(), "run": run})),
        &["recorded_hash_is_checker"],
    );
}

#[test]
fn a_checker_other_than_the_recorded_one_fails_its_check() {
    for executed in [
        json!(sha("def check(answer): return True")),
        json!(null),
        json!(7),
        json!(""),
    ] {
        let mut run = record();
        run["executed_checker_sha256"] = executed.clone();
        fails(
            &audit(&sealed(), json!({"participant": files(), "run": run})),
            &["executed_checker_is_recorded"],
        );
    }
    let mut run = record();
    run.as_object_mut()
        .expect("run")
        .remove("executed_checker_sha256");
    fails(
        &audit(&sealed(), json!({"participant": files(), "run": run})),
        &["executed_checker_is_recorded"],
    );
}

#[test]
fn the_checker_is_hashed_with_unix_line_endings() {
    let mut held = sealed();
    held["checker_source"] = json!(CHECKER.replace("\r\n", "\n"));
    passes(&audit(&held, packet()));
    held["checker_source"] = json!(CHECKER.replace("\r\n", "\r"));
    fails(&audit(&held, packet()), &["recorded_hash_is_checker"]);
}

#[test]
fn a_line_whose_tag_is_not_the_keyed_hash_is_forged() {
    let mut run = record();
    run["stdout"]
        .as_array_mut()
        .expect("stdout")
        .push(json!({"line": "ITEM det3 PASS", "tag": "0".repeat(64)}));
    let report = audit(&sealed(), json!({"participant": files(), "run": run}));
    fails(&report, &["stdout_lines_authentic"]);
    assert_eq!(report.1["detail"]["forged_lines"], 1);
}

#[test]
fn every_forged_line_is_counted() {
    let mut run = record();
    let lines = run["stdout"].as_array_mut().expect("stdout");
    lines.push(json!({"line": "b", "tag": "x"}));
    lines.push(json!({"line": "c"}));
    lines.push(json!({"line": "d", "tag": 5}));
    lines.push(json!({"line": "e", "tag": tag("another key", &json!("e"))}));
    lines.push(json!({}));
    let report = audit(&sealed(), json!({"participant": files(), "run": run}));
    fails(&report, &["stdout_lines_authentic"]);
    assert_eq!(report.1["detail"]["forged_lines"], 5);
}

#[test]
fn a_line_may_be_any_value_and_a_missing_one_is_null() {
    let mut run = record();
    let lines = run["stdout"].as_array_mut().expect("stdout");
    lines.push(json!({"line": {"item": [1, 2], "pass": true}, "tag": tag(KEY, &json!({"item": [1, 2], "pass": true}))}));
    lines.push(json!({"line": 7, "tag": tag(KEY, &json!(7))}));
    lines.push(json!({"tag": tag(KEY, &json!(null))}));
    lines.push(json!({"line": "é ü", "tag": tag(KEY, &json!("é ü"))}));
    passes(&audit(
        &sealed(),
        json!({"participant": files(), "run": run}),
    ));
}

#[test]
fn a_tag_is_keyed_by_the_sealed_key_and_a_zero_byte() {
    let mut run = record();
    run["stdout"] = json!([{"line": LINE, "tag": sha(&format!("{KEY}{LINE}"))}]);
    let report = audit(&sealed(), json!({"participant": files(), "run": run}));
    fails(&report, &["stdout_lines_authentic"]);
    let mut run = record();
    run["stdout"] = json!([{"line": LINE, "tag": sha(&format!("{KEY}\u{0}\"{LINE}\""))}]);
    passes(&audit(
        &sealed(),
        json!({"participant": files(), "run": run}),
    ));
}

#[test]
fn no_output_at_all_is_not_authentic() {
    let mut run = record();
    run["stdout"] = json!([]);
    fails(
        &audit(&sealed(), json!({"participant": files(), "run": run})),
        &["stdout_lines_authentic"],
    );
    let mut run = record();
    run.as_object_mut().expect("run").remove("stdout");
    fails(
        &audit(&sealed(), json!({"participant": files(), "run": run})),
        &["stdout_lines_authentic"],
    );
}

#[test]
fn every_predicate_is_recorded_even_after_one_fails() {
    let mut participant = files();
    participant["notes.txt"] = json!("3121");
    let mut run = record();
    run["executed_checker_sha256"] = json!("0");
    run["stdout"] = json!([]);
    let mut held = sealed();
    held["recorded_checker_sha256"] = json!("1");
    let (passed, report) = audit(&held, json!({"participant": participant, "run": run}));
    assert!(!passed);
    assert_eq!(report["code"], "MANIFEST_COMPLETE");
    assert_eq!(
        outcomes(&report),
        all_but(&[
            "manifest_complete",
            "file_hashes_match",
            "answer_not_derivable",
            "recorded_hash_is_checker",
            "executed_checker_is_recorded",
            "stdout_lines_authentic",
        ])
    );
    assert_eq!(report["every_predicate_passed"], false);
}

#[test]
fn stdout_that_is_not_a_list_of_objects_is_malformed_after_five_predicates() {
    for stdout in [
        json!("ITEM det2 PASS"),
        json!({"line": LINE}),
        json!(null),
        json!(7),
        json!([LINE]),
        json!([{"line": LINE}, 5]),
        json!([null]),
        json!([[]]),
    ] {
        let mut run = record();
        run["stdout"] = stdout.clone();
        let (reason, rows) = malformed(json!({"participant": files(), "run": run}));
        assert_eq!(reason, "stdout is a list of lines", "{stdout}");
        assert_eq!(rows, 5, "{stdout}");
    }
}

#[test]
fn a_reply_that_is_not_a_packet_is_malformed_before_any_predicate() {
    for packet in [
        json!("a packet"),
        json!({}),
        json!({"participant": files()}),
        json!({"run": record()}),
        json!({"participant": "files", "run": record()}),
        json!({"participant": files(), "run": "record"}),
        json!({"participant": [], "run": record()}),
        json!({"participant": files(), "run": []}),
        json!({"participant": null, "run": null}),
    ] {
        let (reason, rows) = malformed(packet.clone());
        assert_eq!(reason, "packet fields", "{packet}");
        assert_eq!(rows, 0);
    }
}

#[test]
fn participant_files_must_be_text() {
    for file in [
        json!(7),
        json!(null),
        json!(["a"]),
        json!({"k": "v"}),
        json!(true),
    ] {
        let mut participant = files();
        participant["bad.txt"] = file.clone();
        let (reason, rows) = malformed(json!({"participant": participant, "run": record()}));
        assert_eq!(reason, "participant files are text", "{file}");
        assert_eq!(rows, 0);
    }
}

#[test]
fn a_missing_reply_is_refused_without_a_predicate() {
    let (passed, report) = judged(&sealed(), vec![None]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "NO_ADMISSIBLE_REPLY");
    assert!(outcomes(&report).is_empty());
}

#[test]
fn a_sealed_part_the_host_cannot_audit_with_is_refused_before_anything_is_asked() {
    let without = |key: &str| {
        let mut held = sealed();
        held.as_object_mut().expect("sealed").remove(key);
        held
    };
    let replacing = |key: &str, value: Value| {
        let mut held = sealed();
        held[key] = value;
        held
    };
    let missing = "the host-held manifest is missing from the sealed packet";
    let cases = [
        (without("manifest"), missing),
        (replacing("manifest", json!([])), missing),
        (replacing("manifest", json!("m")), missing),
        (
            without("expected_answer"),
            "expected_answer must be an exact rational",
        ),
        (
            replacing("expected_answer", json!(3.5)),
            "expected_answer must be an exact rational",
        ),
        (
            replacing("expected_answer", json!("three")),
            "expected_answer must be an exact rational",
        ),
        (without("checker_source"), "checker_source must be text"),
        (
            replacing("checker_source", json!(5)),
            "checker_source must be text",
        ),
        (
            without("recorded_checker_sha256"),
            "recorded_checker_sha256 must be text",
        ),
        (
            replacing("recorded_checker_sha256", json!(null)),
            "recorded_checker_sha256 must be text",
        ),
        (without("stdout_key"), "stdout_key must be text"),
        (replacing("stdout_key", json!(1)), "stdout_key must be text"),
    ];
    for (held, expected) in cases {
        match next(&request(&task(), &held, &[])) {
            Outcome::Pass { result } => assert_eq!(result["ask"], Value::Null, "{held}"),
            other => panic!("expected a turn, got {other:?}"),
        }
        let (passed, report) = judged(&held, vec![]);
        assert!(!passed, "{held}");
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "MALFORMED_CANDIDATE");
        assert_eq!(report["detail"]["reason"], expected, "{held}");
        assert!(outcomes(&report).is_empty());
    }
}

#[test]
fn a_task_may_have_any_fields() {
    let (passed, report) = match judge(&request(&json!({}), &sealed(), &[Some(packet())])) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    };
    assert!(passed, "{report}");
}
