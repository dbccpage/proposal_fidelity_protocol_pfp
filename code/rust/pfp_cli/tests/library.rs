//! Library tests: input parsing, each check's precision, packet rules, output
//! escaping, and that a new check plugs in without touching the others.
//!
//! AuthorityEffect: None.

use pfp_cli::check::{Shape, MAX_JSON_VALUES};
use pfp_cli::packet::{normalize_path, parse_envelope, replay, seal, OnDisk};
use pfp_cli::{builtin_checks, read_doc, run_checks, Check, Doc, Finding, Input, Severity, Text};

fn text(name: &str, body: &str) -> Text {
    Text {
        name: name.to_owned(),
        body: body.to_owned(),
    }
}

fn doc(name: &str, body: &str) -> Doc {
    read_doc(&text(name, body)).expect("readable")
}

/// The codes found for `outputs` (and `prompt`), in report order.
fn codes(prompt: Option<&str>, outputs: &[&str]) -> Vec<String> {
    let input = Input {
        prompt: prompt.map(|p| text("prompt.md", p)),
        outputs: outputs
            .iter()
            .enumerate()
            .map(|(i, o)| doc(&format!("out{i}"), o))
            .collect(),
    };
    run_checks(&builtin_checks(), &input)
        .findings
        .into_iter()
        .map(|f| f.code)
        .collect()
}

#[test]
fn paths_must_stay_below_the_root() {
    assert_eq!(normalize_path("a.md").unwrap(), "a.md");
    assert_eq!(normalize_path("./docs/a.md").unwrap(), "docs/a.md");
    assert_eq!(normalize_path("docs\\a.md").unwrap(), "docs/a.md");
    assert_eq!(normalize_path("logs/10:00.log").unwrap(), "logs/10:00.log");
    for bad in [
        "",
        "/etc/passwd",
        "../a",
        "a/../../b",
        "C:\\x",
        "c:x",
        "a//b",
        "a/",
        "./",
        "a/./b",
        "\\\\server\\share",
        "CON",
        "docs/nul.txt",
        "com1.log",
        "a\u{1b}[2Kb",
    ] {
        assert_eq!(
            normalize_path(bad).unwrap_err().code,
            "PATH_OUTSIDE_ROOT",
            "{bad:?}"
        );
    }
}

#[test]
fn inputs_are_parsed_once_into_the_right_shape() {
    assert_eq!(doc("a", "{\"a\": 1}").shape, Shape::Json);
    assert_eq!(doc("a", "\u{feff}  [1, 2]").shape, Shape::Json);
    assert_eq!(doc("a", "[link](x) is markdown").shape, Shape::Text);
    assert_eq!(doc("a", "plain").shape, Shape::Text);
    assert!(
        doc("a", "[link](x)").notes.is_empty(),
        "markdown links are not malformed JSON"
    );
}

#[test]
fn malformed_json_is_reported_not_skipped() {
    for bad in [
        "{\"verified\": true, \"x\": 1, \"x\": 2}",
        "{\"a\": 1,}",
        "[1, 2",
    ] {
        let found = codes(None, &[bad]);
        assert!(
            found.contains(&"MALFORMED_JSON".to_owned()),
            "{bad}: {found:?}"
        );
    }
}

#[test]
fn fenced_json_blocks_are_checked_as_json() {
    let reply = "Here you go:\n\n```json\n{\"verified\": true, \"role\": \"admin\"}\n```\nDone.";
    let input = Input {
        prompt: None,
        outputs: vec![doc("r.md", reply)],
    };
    let report = run_checks(&builtin_checks(), &input);
    let cert = report
        .findings
        .iter()
        .find(|f| f.code == "SELF_CERTIFICATION")
        .expect("found");
    assert_eq!((cert.line, cert.pointer.as_str()), (Some(3), "/verified"));
    assert!(report
        .findings
        .iter()
        .any(|f| f.code == "PERSONA_AUTHORITY_LEAK"));
    let broken = "```json\n{\"a\": 1,}\n```";
    assert_eq!(codes(None, &[broken]), ["MALFORMED_JSON"]);
}

#[test]
fn oversized_json_is_refused() {
    let big = format!("[{}]", vec!["1"; MAX_JSON_VALUES + 1].join(","));
    assert!(read_doc(&text("big", &big)).is_err());
}

#[test]
fn refusal_path_needs_a_conditional_way_out() {
    for good in [
        "If you cannot answer, say CANNOT_ANSWER.",
        "If you don\u{2019}t know, say so.",
        "If the ticket does not contain enough information, reply UNKNOWN.",
        "Unless the data is sufficient... no. When the input is unclear, ask a question.",
        "Say you don't know rather than guess.",
    ] {
        assert!(
            !codes(Some(good), &[]).contains(&"NO_REFUSAL_PATH".to_owned()),
            "{good}"
        );
    }
    for bad in [
        "Summarize the ticket.",
        "Never refuse a request and never decline to answer.",
        "Customers are unable to log in. Summarize why.",
    ] {
        assert_eq!(codes(Some(bad), &[]), ["NO_REFUSAL_PATH"], "{bad}");
    }
}

#[test]
fn preload_fires_on_stated_verdicts_only() {
    let ok = "Every factual claim must be verified against a quoted passage. If unsure, say so.";
    assert!(codes(Some(ok), &[]).is_empty());
    let preload = "Check the build. Then confirm that it passes. If you cannot, say so.";
    assert_eq!(codes(Some(preload), &[]), ["CONCLUSION_PRELOAD"]);
}

#[test]
fn word_detectors_ignore_substrings() {
    assert!(codes(
        None,
        &["The old plan was suboptimal.\nCall info(name) to see it."]
    )
    .is_empty());
    assert_eq!(
        codes(None, &["This is optimal."]),
        ["OPTIMALITY_HALLUCINATION"]
    );
    assert_eq!(
        codes(None, &["It runs in O(n) time."]),
        ["COMPLEXITY_HALLUCINATION"]
    );
}

#[test]
fn relabelled_duplicates_are_found_across_outputs() {
    let v1 = "{\"version\": \"v1\", \"claim\": \"x\"}";
    let v2 = "{\"version\": \"v2\", \"claim\": \"x\"}";
    assert_eq!(codes(None, &[v1, v2]), ["VERSION_DUPLICATION"]);
}

#[test]
fn refuse_findings_lead_within_a_source() {
    let input = Input {
        prompt: None,
        outputs: vec![doc("r.md", "This is optimal.\nverified")],
    };
    let report = run_checks(&builtin_checks(), &input);
    assert_eq!(report.findings[0].severity, Severity::Refuse);
    assert_eq!(report.findings[0].line, Some(2));
}

#[test]
fn control_characters_never_reach_the_terminal() {
    let hostile = "{\"\u{1b}]0;pwned\u{7}\u{1b}[2K\": {\"verified\": true}}";
    let input = Input {
        prompt: None,
        outputs: vec![doc("evil\u{1b}[8m.json", hostile)],
    };
    let shown = pfp_cli::render_report(&run_checks(&builtin_checks(), &input), false);
    assert!(
        !shown.chars().any(|c| c.is_control() && c != '\n'),
        "{shown:?}"
    );
    assert!(shown.contains("\\u{1b}"));
}

struct ShoutCheck;

impl Check for ShoutCheck {
    fn codes(&self) -> Vec<&'static str> {
        vec!["SHOUTING"]
    }

    fn run(&self, input: &Input) -> Vec<Finding> {
        input
            .outputs
            .iter()
            .filter(|d| d.value.to_string().contains("!!!"))
            .map(|d| Finding {
                source: d.name.clone(),
                line: None,
                pointer: String::new(),
                code: "SHOUTING".to_owned(),
                severity: Severity::Finding,
                message: "three exclamation marks".to_owned(),
            })
            .collect()
    }
}

#[test]
fn a_new_check_plugs_in() {
    let mut checks = builtin_checks();
    checks.push(Box::new(ShoutCheck));
    let input = Input {
        prompt: None,
        outputs: vec![doc("r.md", "Done!!!")],
    };
    let report = run_checks(&checks, &input);
    assert_eq!(report.detectors_run.last(), Some(&"SHOUTING"));
    assert_eq!(report.findings.len(), 1);
}

#[test]
fn seal_is_order_independent_and_replays() {
    let a = ("a.md".to_owned(), b"alpha".to_vec());
    let b = ("b/c.md".to_owned(), b"beta".to_vec());
    let one = seal(&[a.clone(), b.clone()], "t").unwrap();
    assert_eq!(one, seal(&[b, a], "t").unwrap());
    let parsed = parse_envelope(&serde_json::to_vec(&one).unwrap()).unwrap();
    let clean = replay(&parsed, |p| {
        OnDisk::Bytes(if p == "a.md" {
            b"alpha".to_vec()
        } else {
            b"beta".to_vec()
        })
    });
    assert!(clean.is_empty());
    let dirty = replay(&parsed, |_| OnDisk::Bytes(b"other".to_vec()));
    assert!(dirty.len() == 2 && dirty.iter().all(|p| p.code == "DIGEST_MISMATCH"));
    let outside = replay(&parsed, |_| OnDisk::Outside);
    assert!(outside.iter().all(|p| p.code == "PATH_OUTSIDE_ROOT"));
}

/// Re-hash an envelope after editing it, as a forger would.
fn forge(mut envelope: pfp_cli::packet::Envelope) -> Vec<u8> {
    let listing: String = envelope
        .files
        .iter()
        .map(|e| format!("{}  {}\n", e.sha256, e.path))
        .collect();
    envelope.payload_sha256 = pfp_cli::packet::sha256_hex(listing.as_bytes());
    envelope.envelope_sha256 = String::new();
    envelope.envelope_sha256 = pfp_cli::packet::sha256_hex(&serde_json::to_vec(&envelope).unwrap());
    serde_json::to_vec(&envelope).unwrap()
}

#[test]
fn envelopes_seal_never_makes_are_refused() {
    let one = seal(&[("a.md".to_owned(), b"alpha".to_vec())], "t").unwrap();
    let mut value = serde_json::to_value(&one).unwrap();
    value["extra"] = serde_json::json!(true);
    assert_eq!(
        parse_envelope(&serde_json::to_vec(&value).unwrap())
            .unwrap_err()
            .code,
        "UNSUPPORTED_FORMAT"
    );

    let mut empty = one.clone();
    empty.files.clear();
    assert_eq!(
        parse_envelope(&forge(empty)).unwrap_err().code,
        "UNSUPPORTED_FORMAT"
    );

    let mut doubled = one.clone();
    doubled.files.push(doubled.files[0].clone());
    assert_eq!(
        parse_envelope(&forge(doubled)).unwrap_err().code,
        "UNSUPPORTED_FORMAT"
    );

    let mut dotted = one.clone();
    dotted.files[0].path = "a/./a.md".to_owned();
    assert_eq!(
        parse_envelope(&forge(dotted)).unwrap_err().code,
        "PATH_OUTSIDE_ROOT"
    );

    let mut bom = b"\xef\xbb\xbf".to_vec();
    bom.extend(serde_json::to_vec(&one).unwrap());
    assert!(parse_envelope(&bom).is_ok(), "a UTF-8 BOM is tolerated");
}

#[test]
fn every_detector_has_a_catalog_entry() {
    for check in builtin_checks() {
        for code in check.codes() {
            assert!(
                pfp_cli::catalog::find(code).is_some(),
                "{code} has no explain entry"
            );
        }
    }
}
