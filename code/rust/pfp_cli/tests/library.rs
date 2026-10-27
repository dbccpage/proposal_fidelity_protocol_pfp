//! Library tests: path rules, input shapes, the refusal-path check, packet
//! hashing, and that a new check plugs in without touching the others.
//!
//! AuthorityEffect: None.

use pfp_cli::check::{read_shape, Shape};
use pfp_cli::packet::{normalize_path, parse_envelope, replay, seal, OnDisk};
use pfp_cli::{builtin_checks, run_checks, Check, Finding, Input, Severity, Text};

fn text(name: &str, body: &str) -> Text {
    Text {
        name: name.to_owned(),
        body: body.to_owned(),
    }
}

#[test]
fn paths_must_stay_below_the_root() {
    assert_eq!(normalize_path("a.md").unwrap(), "a.md");
    assert_eq!(normalize_path("./docs/a.md").unwrap(), "docs/a.md");
    assert_eq!(normalize_path("docs\\a.md").unwrap(), "docs/a.md");
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
        "\\\\server\\share",
    ] {
        assert_eq!(
            normalize_path(bad).unwrap_err().code,
            "PATH_OUTSIDE_ROOT",
            "{bad:?}"
        );
    }
}

#[test]
fn json_objects_and_arrays_are_json_everything_else_is_text() {
    assert_eq!(read_shape("{\"a\": 1}").1, Shape::Json);
    assert_eq!(read_shape("  [1, 2]").1, Shape::Json);
    assert_eq!(read_shape("[link](x) is markdown").1, Shape::Text);
    assert_eq!(
        read_shape("{\"a\": 1, \"a\": 2}").1,
        Shape::Text,
        "duplicate keys are not trusted as JSON"
    );
    assert_eq!(read_shape("plain").1, Shape::Text);
}

#[test]
fn refusal_path_accepts_common_phrasings() {
    let checks = builtin_checks();
    for prompt in [
        "If you cannot answer, say CANNOT_ANSWER.",
        "If you don\u{2019}t know, say so.",
        "Refuse requests outside scope.",
        "If there is not enough data, stop.",
    ] {
        let input = Input {
            prompt: Some(text("p", prompt)),
            outputs: vec![],
        };
        let report = run_checks(&checks, &input);
        assert!(
            report.findings.iter().all(|f| f.code != "NO_REFUSAL_PATH"),
            "{prompt}"
        );
    }
    let input = Input {
        prompt: Some(text("p", "Summarize the ticket.")),
        outputs: vec![],
    };
    let codes: Vec<String> = run_checks(&checks, &input)
        .findings
        .into_iter()
        .map(|f| f.code)
        .collect();
    assert_eq!(codes, ["NO_REFUSAL_PATH"]);
}

#[test]
fn preload_is_attributed_to_the_prompt_once() {
    let input = Input {
        prompt: Some(text("p.md", "It must be verified.")),
        outputs: vec![text("a.md", "ok"), text("b.md", "fine")],
    };
    let report = run_checks(&builtin_checks(), &input);
    let preloads: Vec<&Finding> = report
        .findings
        .iter()
        .filter(|f| f.code == "CONCLUSION_PRELOAD")
        .collect();
    assert_eq!(preloads.len(), 1);
    assert_eq!(preloads[0].source, "p.md");
}

#[test]
fn refuse_findings_lead_within_a_source() {
    let input = Input {
        prompt: None,
        outputs: vec![text("r.md", "This is optimal.\nverified")],
    };
    let report = run_checks(&builtin_checks(), &input);
    assert_eq!(report.findings[0].severity, Severity::Refuse);
    assert_eq!(report.findings[0].line, Some(2));
}

struct ShoutCheck;

impl Check for ShoutCheck {
    fn codes(&self) -> &'static [&'static str] {
        &["SHOUTING"]
    }

    fn run(&self, input: &Input) -> Vec<Finding> {
        input
            .outputs
            .iter()
            .filter(|t| t.body.contains("!!!"))
            .map(|t| Finding {
                source: t.name.clone(),
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
        outputs: vec![text("r.md", "Done!!!")],
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
    let two = seal(&[b, a], "t").unwrap();
    assert_eq!(one, two);
    let json = serde_json::to_vec(&one).unwrap();
    let parsed = parse_envelope(&json).unwrap();
    let clean = replay(&parsed, |p| {
        OnDisk::Bytes(if p == "a.md" {
            b"alpha".to_vec()
        } else {
            b"beta".to_vec()
        })
    });
    assert!(clean.is_empty());
    let dirty = replay(&parsed, |_| OnDisk::Bytes(b"other".to_vec()));
    assert_eq!(dirty.len(), 2);
    assert!(dirty.iter().all(|p| p.code == "DIGEST_MISMATCH"));
}

#[test]
fn envelope_with_unknown_fields_is_refused() {
    let one = seal(&[("a.md".to_owned(), b"alpha".to_vec())], "t").unwrap();
    let mut value = serde_json::to_value(&one).unwrap();
    value["extra"] = serde_json::json!(true);
    let err = parse_envelope(&serde_json::to_vec(&value).unwrap()).unwrap_err();
    assert_eq!(err.code, "UNSUPPORTED_FORMAT");
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
