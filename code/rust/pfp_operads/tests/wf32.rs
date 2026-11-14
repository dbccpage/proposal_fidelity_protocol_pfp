//! WF32, claim-scoped receipt: each claim admitted only by its own check, digests bound to the
//! host's witness, and what no check covers named as an open obligation.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf32-tests:v1

use pfp_operads::families::wf32::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const SOURCE: &str = "h\u{e9}llo w\u{f6}rld";

fn task() -> Value {
    json!({
        "statement": "State atomic claims.",
        "sources": {"doc": SOURCE},
        "inputs": {
            "charges": {"checker": "u1_anomaly", "input": {"charges": [1, -1]}},
            "group": {"checker": "group_commutator", "input": {"n": 3, "g": [1, 0, 2], "h": [0, 2, 1]}},
        },
    })
}

fn exact_claim() -> Value {
    json!({"id": "c1", "kind": "exact", "input_ref": "charges",
           "witness": {"linear": 0, "cubic": 0, "anomaly_free": true}})
}

/// The digest the host binds to [`exact_claim`]: the claim and the host's own witness.
fn exact_digest() -> String {
    sha(concat!(
        r#"{"claim":{"id":"c1","input_ref":"charges","kind":"exact","#,
        r#""witness":{"anomaly_free":true,"cubic":0,"linear":0}},"#,
        r#""host":{"cubic":"0","linear":"0"}}"#
    ))
}

/// `wörld` by its bytes in the source: 7 to 13. By characters it would be 6 to 11.
fn quote_claim() -> Value {
    json!({"id": "c2", "kind": "quote", "source": "doc", "span": [7, 13], "text": "w\u{f6}rld"})
}

fn quote_witness() -> String {
    format!(
        r#"{{"source_sha256":"{}","span":[7,13]}}"#,
        sha("\"h\u{e9}llo w\u{f6}rld\"")
    )
}

fn quote_digest() -> String {
    sha(&format!(
        "{}{}{}",
        r#"{"claim":{"id":"c2","kind":"quote","source":"doc","span":[7,13],"text":"wörld"},"host":"#,
        quote_witness(),
        "}"
    ))
}

fn reply(claims: Value, admitted: Value) -> Value {
    json!({"claims": claims, "admitted": admitted})
}

/// The report of the run with this one reply, and whether the host passed it.
fn run(task: Value, content: Value) -> (bool, Value) {
    let request = json!({"workflow": "WF32", "task": task, "replies": [{"content": content}]});
    match judge(&request.to_string()) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn turn(task: Value) -> Outcome {
    next(&json!({"workflow": "WF32", "task": task}).to_string())
}

fn bad_task(task: Value) -> String {
    match turn(task) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

fn accepted(task: Value) {
    match turn(task) {
        Outcome::Pass { result } => assert_eq!(result["ask"]["stage"], "solve"),
        other => panic!("expected a turn, got {other:?}"),
    }
}

fn malformed(content: Value) -> String {
    let (passed, report) = run(task(), content);
    assert!(!passed);
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("reason")
        .to_owned()
}

fn names(report: &Value) -> Vec<String> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["name"].as_str().expect("name").to_owned())
        .collect()
}

fn failed(report: &Value) -> Vec<String> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .filter(|row| row["passed"] == false)
        .map(|row| row["name"].as_str().expect("name").to_owned())
        .collect()
}

fn evidence(report: &Value, name: &str) -> String {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .find(|row| row["name"] == name)
        .unwrap_or_else(|| panic!("no predicate {name}"))["evidence_sha256"]
        .as_str()
        .expect("evidence")
        .to_owned()
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF32",
            "Claim-scoped receipt",
            "per_claim_independent_checkers"
        )
    );
}

#[test]
fn a_reply_whose_every_claim_is_checked_is_certified_in_full() {
    let content = reply(json!([exact_claim(), quote_claim()]), json!(["c1", "c2"]));
    let (passed, report) = run(task(), content);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "ALL_CLAIMS_ADMITTED");
    assert_eq!(
        report["detail"],
        json!({"admitted": {"c1": exact_digest(), "c2": quote_digest()}, "unadmitted": []})
    );
    assert_eq!(report["uncertified_obligations"], json!([]));
    assert_eq!(
        report["predicates"],
        json!([
            {"name": "claim:c1", "passed": true, "evidence_sha256": sha(r#"{"cubic":"0","linear":"0"}"#)},
            {"name": "claim:c2", "passed": true, "evidence_sha256": sha(&quote_witness())},
            {"name": "no_admission_overreach", "passed": true, "evidence_sha256": sha("[]")},
            {"name": "some_claim_admitted", "passed": true, "evidence_sha256": sha(r#"["c1","c2"]"#)},
        ])
    );
    assert_eq!(report["asked"][0]["stage"], "solve");
    assert_eq!(report["asked"].as_array().map(Vec::len), Some(1));
}

#[test]
fn what_no_check_covers_is_never_admitted_and_is_owed() {
    let mut worded = exact_claim();
    worded["text"] = json!("so the theory is consistent");
    let claims = json!([
        {"id": "c0", "kind": "interpretive", "text": "this is elegant"},
        worded,
        {"id": "c3", "text": "no kind at all"},
        {"id": "c4", "kind": 7},
        quote_claim(),
    ]);
    let (passed, report) = run(task(), reply(claims, json!(["c2"])));
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CLAIM_SCOPED");
    assert_eq!(
        report["detail"],
        json!({"admitted": {"c1": exact_digest(), "c2": quote_digest()},
               "unadmitted": ["c0", "c1:text", "c3", "c4"]})
    );
    assert_eq!(
        report["uncertified_obligations"],
        json!(["c0", "c1:text", "c3", "c4"])
    );
    assert_eq!(
        names(&report),
        [
            "claim:c1",
            "claim:c2",
            "no_admission_overreach",
            "some_claim_admitted"
        ]
    );
}

#[test]
fn the_admitted_list_is_optional_but_must_be_a_list() {
    let (passed, report) = run(task(), json!({"claims": [exact_claim()]}));
    assert!(passed);
    assert_eq!(report["code"], "ALL_CLAIMS_ADMITTED");
    for admitted in [json!("c1"), json!({"c1": true}), Value::Null, json!(1)] {
        assert_eq!(
            malformed(reply(json!([exact_claim()]), admitted)),
            "admitted must be a list"
        );
    }
}

#[test]
fn a_stated_digest_must_be_the_host_s() {
    let mut bound = exact_claim();
    bound["evidence_sha256"] = json!(exact_digest());
    let (passed, report) = run(task(), reply(json!([bound]), json!(["c1"])));
    assert!(passed);
    assert_eq!(
        names(&report),
        [
            "claim:c1",
            "claim:c1:digest_bound",
            "no_admission_overreach",
            "some_claim_admitted"
        ]
    );
    assert_eq!(
        evidence(&report, "claim:c1:digest_bound"),
        sha(&format!("\"{}\"", exact_digest()))
    );
    assert_eq!(report["detail"]["admitted"]["c1"], exact_digest());

    for stated in [
        json!(quote_digest()),
        json!(exact_digest().to_uppercase()),
        json!(""),
        json!([exact_digest()]),
        Value::Null,
    ] {
        let mut unbound = exact_claim();
        unbound["evidence_sha256"] = stated;
        let (passed, report) = run(task(), reply(json!([unbound]), json!(["c1"])));
        assert!(!passed);
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "CLAIM:C1:DIGEST_BOUND");
        assert_eq!(failed(&report), ["claim:c1:digest_bound"]);
        assert_eq!(
            report["detail"],
            json!({"admitted": ["c1"], "overreach": [], "unadmitted": [],
                   "failed": ["claim:c1:digest_bound"]})
        );
    }
}

#[test]
fn a_digest_covers_the_claim_but_not_its_free_text_or_its_stated_digest() {
    let digest_of = |claim: Value| {
        let id = claim["id"].as_str().expect("id").to_owned();
        let (_, report) = run(task(), reply(json!([claim]), json!([])));
        report["detail"]["admitted"][id.as_str()]
            .as_str()
            .unwrap_or_else(|| panic!("{id} not admitted: {report}"))
            .to_owned()
    };
    assert_eq!(digest_of(exact_claim()), exact_digest());
    let mut worded = exact_claim();
    worded["text"] = json!("free words");
    assert_eq!(digest_of(worded), exact_digest());
    let mut noted = exact_claim();
    noted["note"] = json!("kept");
    assert_ne!(digest_of(noted), exact_digest());
    let mut other_witness = exact_claim();
    other_witness["witness"] = json!({"linear": "0/1", "cubic": 0, "anomaly_free": true});
    assert_ne!(digest_of(other_witness), exact_digest());

    assert_eq!(digest_of(quote_claim()), quote_digest());
    let mut stated = quote_claim();
    stated["evidence_sha256"] = json!(quote_digest());
    assert_eq!(digest_of(stated), quote_digest());
    // A quote's text is the claim, so the digest covers it.
    let shorter =
        json!({"id": "c2", "kind": "quote", "source": "doc", "span": [7, 8], "text": "w"});
    assert_ne!(digest_of(shorter), quote_digest());
}

#[test]
fn an_exact_claim_its_checker_rejects_fails_and_is_not_admitted() {
    let mut wrong = exact_claim();
    wrong["witness"] = json!({"linear": 1, "cubic": 0, "anomaly_free": false});
    let (passed, report) = run(task(), reply(json!([wrong, quote_claim()]), json!(["c2"])));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "CLAIM:C1");
    assert_eq!(failed(&report), ["claim:c1"]);
    assert_eq!(
        report["detail"],
        json!({"admitted": ["c2"], "overreach": [], "unadmitted": [], "failed": ["claim:c1"]})
    );
}

#[test]
fn each_declared_input_runs_under_the_checker_the_task_chose() {
    let claim = json!({"id": "g", "kind": "exact", "input_ref": "group", "witness": {"commutator": [1, 2, 0]}});
    let (passed, report) = run(task(), reply(json!([claim]), json!(["g"])));
    assert!(passed, "{report}");
    assert_eq!(
        evidence(&report, "claim:g"),
        sha(r#"{"commutator":[1,2,0]}"#)
    );
    // The anomaly witness under the commutator's input is not readable by that checker.
    let crossed = json!({"id": "g", "kind": "exact", "input_ref": "group",
                         "witness": {"linear": 0, "cubic": 0, "anomaly_free": true}});
    assert_eq!(
        malformed(reply(json!([crossed]), json!([]))),
        "commutator must be a permutation of 3 points"
    );
    let unreadable =
        json!({"id": "c1", "kind": "exact", "input_ref": "charges", "witness": {"linear": 0}});
    assert_eq!(
        malformed(reply(json!([unreadable]), json!([]))),
        "anomaly_free bool required"
    );
    let none = json!({"id": "c1", "kind": "exact", "input_ref": "charges"});
    assert_eq!(
        malformed(reply(json!([none]), json!([]))),
        "anomaly_free bool required"
    );
}

#[test]
fn an_exact_claim_on_an_input_the_task_did_not_declare_fails() {
    let good = json!({"linear": 0, "cubic": 0, "anomaly_free": true});
    for (claim, reference) in [
        (
            json!({"id": "c1", "kind": "exact", "input_ref": "nope", "witness": good}),
            r#""nope""#,
        ),
        (
            json!({"id": "c1", "kind": "exact", "witness": good}),
            "null",
        ),
        (
            json!({"id": "c1", "kind": "exact", "input_ref": ["charges"], "witness": good}),
            r#"["charges"]"#,
        ),
        (
            json!({"id": "c1", "kind": "exact", "input_ref": 3, "witness": good}),
            "3",
        ),
        (
            json!({"id": "c1", "kind": "exact", "input_ref": "charges", "witness": good,
                   "input": {"charges": [1, -1]}}),
            r#""charges""#,
        ),
        (
            json!({"id": "c1", "kind": "exact", "input_ref": "charges", "witness": good,
                   "checker": "u1_anomaly"}),
            r#""charges""#,
        ),
        (
            json!({"id": "c1", "kind": "exact", "input_ref": "charges", "witness": good, "input": null}),
            r#""charges""#,
        ),
    ] {
        let (passed, report) = run(task(), reply(json!([claim, quote_claim()]), json!(["c2"])));
        assert!(!passed);
        assert_eq!(report["code"], "CLAIM:C1");
        assert_eq!(failed(&report), ["claim:c1"]);
        let witness = json!({ "undeclared_input": reference }).to_string();
        assert_eq!(evidence(&report, "claim:c1"), sha(&witness));
    }
    let lone = json!({"id": "c1", "kind": "exact", "input_ref": "charges", "witness": good});
    let (passed, report) = run(json!({}), reply(json!([lone]), json!([])));
    assert!(!passed);
    assert_eq!(failed(&report), ["claim:c1", "some_claim_admitted"]);
}

#[test]
fn a_quote_holds_only_when_its_byte_span_is_the_quoted_text() {
    let quote = |span: Value, text: &str| json!({"id": "q", "kind": "quote", "source": "doc", "span": span, "text": text});
    for (span, text) in [
        (json!([7, 13]), "w\u{f6}rld"),
        (json!([0, 13]), SOURCE),
        (json!([0, 1]), "h"),
        (json!([1, 3]), "\u{e9}"),
        (json!([12, 13]), "d"),
    ] {
        let (passed, report) = run(
            task(),
            reply(json!([quote(span.clone(), text)]), json!(["q"])),
        );
        assert!(passed, "{span} {text}");
        let witness = format!(
            r#"{{"source_sha256":"{}","span":{span}}}"#,
            sha("\"h\u{e9}llo w\u{f6}rld\"")
        );
        assert_eq!(evidence(&report, "claim:q"), sha(&witness));
    }
    for (span, text) in [
        (json!([6, 11]), "w\u{f6}rld"),
        (json!([7, 13]), "world"),
        (json!([7, 12]), "w\u{f6}rld"),
        (json!([7, 14]), "w\u{f6}rld"),
        (json!([13, 14]), ""),
        (json!([14, 15]), ""),
        (json!([3, 3]), ""),
        (json!([5, 3]), ""),
        (json!([5, 3]), "ll"),
        (json!([-1, 1]), "h"),
        (json!([0, -1]), ""),
    ] {
        let (passed, report) = run(task(), reply(json!([quote(span.clone(), text)]), json!([])));
        assert!(!passed, "{span} {text}");
        assert_eq!(report["code"], "CLAIM:Q");
        assert_eq!(failed(&report), ["claim:q", "some_claim_admitted"]);
        assert_eq!(
            report["detail"],
            json!({"admitted": [], "overreach": [], "unadmitted": [],
                   "failed": ["claim:q", "some_claim_admitted"]})
        );
    }
}

#[test]
fn a_span_beyond_the_machine_s_range_is_an_exact_integer_that_quotes_nothing() {
    let request = format!(
        r#"{{"workflow":"WF32","task":{},"replies":[{{"content":{{"claims":[
            {{"id":"q","kind":"quote","source":"doc","span":[0,99999999999999999999999],"text":"h"}}]}}}}]}}"#,
        task()
    );
    let Outcome::Fail { result: report } = judge(&request) else {
        panic!("expected a failed run");
    };
    assert_eq!(report["code"], "CLAIM:Q");
    let witness = format!(
        r#"{{"source_sha256":"{}","span":[0,99999999999999999999999]}}"#,
        sha("\"h\u{e9}llo w\u{f6}rld\"")
    );
    assert_eq!(evidence(&report, "claim:q"), sha(&witness));
}

#[test]
fn a_quote_needs_an_exact_span_and_its_text() {
    let shape = "quote needs [start, end] and text";
    for claim in [
        json!({"id": "q", "kind": "quote", "source": "doc", "span": [7], "text": "w"}),
        json!({"id": "q", "kind": "quote", "source": "doc", "span": [7, 8, 9], "text": "w"}),
        json!({"id": "q", "kind": "quote", "source": "doc", "span": [], "text": "w"}),
        json!({"id": "q", "kind": "quote", "source": "doc", "span": [7, 8]}),
        json!({"id": "q", "kind": "quote", "source": "doc", "span": [7, 8], "text": ["w"]}),
    ] {
        assert_eq!(malformed(reply(json!([claim]), json!([]))), shape);
    }
    for span in [
        json!([7.0, 8]),
        json!([7, "8"]),
        json!([null, 8]),
        json!([7, 8.5]),
        json!([true, 8]),
    ] {
        let claim = json!({"id": "q", "kind": "quote", "source": "doc", "span": span, "text": "w"});
        assert_eq!(
            malformed(reply(json!([claim]), json!([]))),
            "span must be exact ints"
        );
    }
}

#[test]
fn a_quote_with_no_declared_source_or_no_span_list_stays_open() {
    for claim in [
        json!({"id": "q", "kind": "quote", "source": "other", "span": [0, 1], "text": "h"}),
        json!({"id": "q", "kind": "quote", "span": [0, 1], "text": "h"}),
        json!({"id": "q", "kind": "quote", "source": ["doc"], "span": [0, 1], "text": "h"}),
        json!({"id": "q", "kind": "quote", "source": "doc", "text": "h"}),
        json!({"id": "q", "kind": "quote", "source": "doc", "span": "0-1", "text": "h"}),
        json!({"id": "q", "kind": "quote", "source": "doc", "span": {"start": 0, "end": 1}, "text": "h"}),
    ] {
        let (passed, report) = run(task(), reply(json!([exact_claim(), claim]), json!(["c1"])));
        assert!(passed, "{report}");
        assert_eq!(report["code"], "CLAIM_SCOPED");
        assert_eq!(report["uncertified_obligations"], json!(["q"]));
        assert_eq!(
            names(&report),
            ["claim:c1", "no_admission_overreach", "some_claim_admitted"]
        );
    }
    let lone = json!({"id": "q", "kind": "quote", "source": "doc", "span": [0, 1], "text": "h"});
    let (passed, report) = run(json!({}), reply(json!([lone]), json!([])));
    assert!(!passed);
    assert_eq!(report["detail"]["unadmitted"], json!(["q"]));
}

#[test]
fn listing_a_claim_the_host_did_not_admit_is_overreach() {
    let open = json!({"id": "c9", "kind": "interpretive", "text": "elegant"});
    for (listed, overreach) in [
        (json!(["c1", "c9"]), json!(["c9"])),
        (
            json!(["c1", "zz", "c9", "aa", "zz"]),
            json!(["aa", "c9", "zz"]),
        ),
        (
            json!(["c1", 7, null, ["c1"]]),
            json!(["7", "[\"c1\"]", "null"]),
        ),
        (json!(["C1"]), json!(["C1"])),
        (json!(["c1:text"]), json!(["c1:text"])),
    ] {
        let content = reply(json!([exact_claim(), open.clone()]), listed);
        let (passed, report) = run(task(), content);
        assert!(!passed);
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "NO_ADMISSION_OVERREACH");
        assert_eq!(failed(&report), ["no_admission_overreach"]);
        assert_eq!(
            evidence(&report, "no_admission_overreach"),
            sha(&overreach.to_string())
        );
        assert_eq!(
            report["detail"],
            json!({"admitted": ["c1"], "overreach": overreach, "unadmitted": ["c9"],
                   "failed": ["no_admission_overreach"]})
        );
        assert_eq!(report["uncertified_obligations"], json!(["c9"]));
    }
}

#[test]
fn listing_a_claim_that_failed_its_check_is_overreach_too() {
    let mut wrong = exact_claim();
    wrong["witness"] = json!({"linear": 0, "cubic": 0, "anomaly_free": false});
    let (passed, report) = run(
        task(),
        reply(json!([wrong, quote_claim()]), json!(["c1", "c2"])),
    );
    assert!(!passed);
    assert_eq!(failed(&report), ["claim:c1", "no_admission_overreach"]);
    assert_eq!(report["detail"]["overreach"], json!(["c1"]));
}

#[test]
fn a_reply_that_admits_nothing_is_refused() {
    let claims = json!([
        {"id": "a", "kind": "interpretive", "text": "elegant"},
        {"id": "b", "kind": "exact-ish"},
    ]);
    let (passed, report) = run(task(), reply(claims, json!([])));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "SOME_CLAIM_ADMITTED");
    assert_eq!(
        report["predicates"],
        json!([
            {"name": "no_admission_overreach", "passed": true, "evidence_sha256": sha("[]")},
            {"name": "some_claim_admitted", "passed": false, "evidence_sha256": sha("[]")},
        ])
    );
    assert_eq!(
        report["detail"],
        json!({"admitted": [], "overreach": [], "unadmitted": ["a", "b"],
               "failed": ["some_claim_admitted"]})
    );
    assert_eq!(report["uncertified_obligations"], json!(["a", "b"]));
}

#[test]
fn the_claims_are_a_nonempty_list_of_objects_with_unique_text_ids() {
    for content in [
        json!({}),
        json!({"claims": []}),
        json!({"claims": {"id": "c1"}}),
        json!({"claims": "c1"}),
        json!({"admitted": ["c1"]}),
    ] {
        assert_eq!(malformed(content), "claims required");
    }
    for claims in [json!(["c1"]), json!([exact_claim(), 3]), json!([null])] {
        assert_eq!(malformed(reply(claims, json!([]))), "claims are objects");
    }
    for claims in [
        json!([{"kind": "exact"}]),
        json!([{"id": 1, "kind": "exact"}]),
        json!([exact_claim(), exact_claim()]),
        json!([exact_claim(), {"id": "c1", "kind": "interpretive"}]),
        json!([exact_claim(), {"id": null}]),
    ] {
        assert_eq!(
            malformed(reply(claims, json!([]))),
            "claims need unique string ids"
        );
    }
}

#[test]
fn sources_are_texts_and_declared_inputs_name_a_registered_checker() {
    let sources = "sources must be an object of texts";
    for value in [
        json!(["doc"]),
        json!("doc"),
        Value::Null,
        json!({"doc": 7}),
        json!({"doc": "x", "other": ["x"]}),
    ] {
        assert_eq!(bad_task(json!({ "sources": value })), sources);
    }
    let inputs = "declared inputs need a registered checker and an input object";
    for value in [
        json!([]),
        json!("charges"),
        Value::Null,
        json!({"a": {"checker": "regge_deficit", "input": {}}}),
        json!({"a": {"checker": 3, "input": {}}}),
        json!({"a": {"input": {}}}),
        json!({"a": {"checker": "u1_anomaly"}}),
        json!({"a": {"checker": "u1_anomaly", "input": [1, -1]}}),
        json!({"a": "u1_anomaly"}),
        json!({"ok": {"checker": "u1_anomaly", "input": {}}, "bad": {"checker": "U1_ANOMALY", "input": {}}}),
    ] {
        assert_eq!(bad_task(json!({ "inputs": value })), inputs);
    }
    accepted(json!({}));
    accepted(json!({"sources": {}, "inputs": {}}));
    accepted(task());
    for name in [
        "group_commutator",
        "linear_refusal",
        "stabilizer_commutation",
        "u1_anomaly",
    ] {
        accepted(json!({"inputs": {"a": {"checker": name, "input": {}}}}));
    }
}
