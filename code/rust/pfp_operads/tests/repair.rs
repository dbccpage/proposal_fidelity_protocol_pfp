//! Tests of the six-stage repair slice on a bench that keeps everything in memory.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:repair:tests:v1

use std::collections::BTreeMap;

use pfp_operads::host::Outcome;
use pfp_operads::ledger::{Ledger, Record};
use pfp_operads::repair::{
    assess, relative_file, repair, respond, Bench, Check, Disposition, Exit, Observation, Request,
    StageStatus, Terminal, COUNTERFEIT, LEAK, MISFIT, PATCH_FILE, RECORD_FILE, REQUEST_FILE,
};
use pfp_operads::Refusal;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const ADJUST: &str = "def adjust(n):\n    if n < 0:\n        return n\n    return n - 1\n";
const FIXED: &str = "def adjust(n):\n    if n < 0:\n        return n\n    return n + 1\n";
const NOTES: &str = "notes\n";

fn hex(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

fn patch(path: &str, from: &str, to: &str) -> String {
    format!("--- a/{path}\n+++ b/{path}\n@@ -4 +4 @@\n-    return {from}\n+    return {to}\n")
}

fn check(id: &str, argv: &[&str]) -> Value {
    json!({"check_id": id, "argv": argv})
}

/// The worked example: `positive` fails until the last line returns `n + 1`; `control` passes.
fn request(candidate: &str) -> Value {
    json!({
        "run_key": "run-1",
        "objective": "adjust(2) must be 3 and adjust(-2) must stay -2",
        "sources": {"adjust.py": hex(ADJUST.as_bytes()), "notes.txt": hex(NOTES.as_bytes())},
        "write_paths": ["adjust.py"],
        "checks": [check("positive", &["has", "adjust.py", "return n + 1"]),
                   check("control", &["has", "adjust.py", "        return n\n"])],
        "candidate_patch": candidate,
    })
}

fn with(mut base: Value, field: &str, value: Value) -> Value {
    base[field] = value;
    base
}

/// A bench in memory. A check's argv says what it does:
/// `has FILE TEXT` passes when the working copy's file contains the text; `exit N` exits with N;
/// `scribble FILE` rewrites a working-copy file; `drift FILE` rewrites an original source;
/// `absent` cannot be started.
#[derive(Default)]
struct Fake {
    source: BTreeMap<String, Vec<u8>>,
    copy: BTreeMap<String, Vec<u8>>,
    kept: BTreeMap<String, Vec<u8>>,
    log: Vec<String>,
    refuse_open: bool,
    refuse_write: bool,
    refuse_keep: bool,
}

impl Fake {
    fn new() -> Self {
        let source = [("adjust.py", ADJUST), ("notes.txt", NOTES)]
            .into_iter()
            .map(|(name, text)| (name.to_owned(), text.as_bytes().to_vec()))
            .collect();
        Self {
            source,
            ..Self::default()
        }
    }

    fn effects(&self) -> Vec<&str> {
        self.log
            .iter()
            .map(String::as_str)
            .filter(|line| !line.starts_with("source ") && !line.starts_with("copy "))
            .collect()
    }
}

fn missing(what: &str, path: &str) -> Refusal {
    Refusal::new("SOURCE_FILE_REFUSED", format!("{what} has no {path}"))
}

impl Bench for Fake {
    fn source(&mut self, path: &str) -> Result<Vec<u8>, Refusal> {
        self.log.push(format!("source {path}"));
        self.source
            .get(path)
            .cloned()
            .ok_or_else(|| missing("source", path))
    }

    fn open(
        &mut self,
        files: &BTreeMap<String, Vec<u8>>,
        kept: &[(&str, Vec<u8>)],
    ) -> Result<(), Refusal> {
        self.log.push("open".to_owned());
        if self.refuse_open {
            return Err(Refusal::new("OUTPUT_CONFLICT", "the run folder exists"));
        }
        self.copy = files.clone();
        for (name, bytes) in kept {
            self.kept.insert((*name).to_owned(), bytes.clone());
        }
        Ok(())
    }

    fn copy(&mut self, path: &str) -> Result<Vec<u8>, Refusal> {
        self.log.push(format!("copy {path}"));
        self.copy
            .get(path)
            .cloned()
            .ok_or_else(|| missing("working copy", path))
    }

    fn write(&mut self, path: &str, bytes: &[u8]) -> Result<(), Refusal> {
        self.log.push(format!("write {path}"));
        if self.refuse_write {
            return Err(Refusal::new(
                "IO_UNAVAILABLE",
                "the working copy is read-only",
            ));
        }
        self.copy.insert(path.to_owned(), bytes.to_vec());
        Ok(())
    }

    fn run(&mut self, check: &Check) -> Result<Exit, Refusal> {
        self.log.push(format!("run {}", check.check_id));
        let argv: Vec<&str> = check.argv.iter().map(String::as_str).collect();
        let code = match argv.as_slice() {
            ["has", file, text] => {
                let body =
                    String::from_utf8_lossy(self.copy.get(*file).map_or(&[][..], Vec::as_slice));
                i32::from(!body.contains(text))
            }
            ["exit", code] => code.parse().unwrap(),
            ["scribble", file] => {
                self.copy.insert((*file).to_owned(), b"scribbled".to_vec());
                0
            }
            ["drift", file] => {
                self.source.insert((*file).to_owned(), b"drifted".to_vec());
                0
            }
            _ => {
                return Err(Refusal::new(
                    "CHECK_UNAVAILABLE",
                    format!("{}: not found", check.check_id),
                ))
            }
        };
        Ok(Exit {
            code,
            ..Exit::default()
        })
    }

    fn keep(&mut self, name: &str, bytes: &[u8]) -> Result<(), Refusal> {
        self.log.push(format!("keep {name}"));
        if self.refuse_keep {
            return Err(Refusal::new(
                "OUTPUT_UNAVAILABLE",
                "the run folder cannot be written",
            ));
        }
        self.kept.insert(name.to_owned(), bytes.to_vec());
        Ok(())
    }
}

fn ran(request: &Value) -> (Terminal, Fake) {
    let mut bench = Fake::new();
    let record = repair(&request.to_string(), &mut bench).unwrap();
    (record, bench)
}

fn exits(observations: &[Observation]) -> Vec<(&str, i32)> {
    observations
        .iter()
        .map(|seen| (seen.check_id.as_str(), seen.exit.code))
        .collect()
}

fn statuses(record: &Terminal) -> String {
    record
        .stages
        .iter()
        .map(|report| match report.status {
            StageStatus::Done => report.stage.to_owned(),
            StageStatus::Skipped => "-".to_owned(),
            StageStatus::Refused => "!".to_owned(),
        })
        .collect()
}

fn refusal(record: &Terminal) -> (&str, &str, &str) {
    let refusal = record.refusal.as_ref().unwrap();
    (refusal.stage, refusal.code, refusal.message.as_str())
}

fn evidence(record: &Terminal) -> &str {
    match record.failure.as_ref().unwrap() {
        Record::Failure {
            evidence_sha256, ..
        } => evidence_sha256,
        other => panic!("not a failure record: {other:?}"),
    }
}

/// The evidence hash a record must carry for what the run saw, built here from its parts.
fn stated(record: &Terminal, refusal: Option<&str>, baseline: &Exits, after: &Exits) -> String {
    let seen = serde_json::to_vec(&(&record.request_digest, refusal, baseline, after)).unwrap();
    hex(&[b"pfp.operads.repair.evidence.v1\n".as_slice(), &seen].concat())
}

fn failure(record: &Terminal) -> (&str, &str, &str, &str, &str) {
    match record.failure.as_ref().unwrap() {
        Record::Failure {
            id,
            workflow,
            run,
            failure_class,
            ddc_trace,
            ..
        } => (id, workflow, run, failure_class, ddc_trace),
        other => panic!("not a failure record: {other:?}"),
    }
}

#[test]
fn the_worked_example_is_repaired_and_the_source_is_untouched() {
    let candidate = patch("adjust.py", "n - 1", "n + 1");
    let (record, bench) = ran(&request(&candidate));
    assert_eq!(record.outcome, Disposition::Repaired);
    assert_eq!(exits(&record.baseline), [("positive", 1), ("control", 0)]);
    assert_eq!(exits(&record.after), [("positive", 0), ("control", 0)]);
    assert_eq!(
        (record.trace.as_str(), statuses(&record).as_str()),
        ("CREIMT", "CREIMT")
    );
    assert_eq!(
        record
            .stages
            .iter()
            .map(|report| report.name)
            .collect::<Vec<_>>(),
        [
            "capture",
            "observe",
            "evaluate",
            "incorporate",
            "disposition",
            "terminal"
        ]
    );
    assert_eq!(record.changed_paths, ["adjust.py"]);
    assert_eq!(record.refusal, None);
    assert_eq!(record.failure, None);
    assert!(record.source_intact);
    assert_eq!(bench.source["adjust.py"], ADJUST.as_bytes());
    assert_eq!(bench.copy["adjust.py"], FIXED.as_bytes());
    assert_eq!(bench.copy["notes.txt"], NOTES.as_bytes());
    assert_eq!(record.source_manifest["adjust.py"], hex(ADJUST.as_bytes()));
    assert_eq!(record.working_manifest["adjust.py"], hex(FIXED.as_bytes()));
    assert_eq!(record.working_manifest["notes.txt"], hex(NOTES.as_bytes()));
    assert_eq!(record.run_key, "run-1");
    assert_eq!(
        record.candidate_id,
        format!("sha256:{}", hex(candidate.as_bytes()))
    );
}

#[test]
fn the_run_folder_keeps_the_request_the_patch_and_the_record() {
    let candidate = patch("adjust.py", "n - 1", "n + 1");
    let (record, bench) = ran(&request(&candidate));
    assert_eq!(
        bench.kept.keys().map(String::as_str).collect::<Vec<_>>(),
        [PATCH_FILE, RECORD_FILE, REQUEST_FILE]
    );
    assert_eq!(bench.kept[PATCH_FILE], candidate.as_bytes());
    let kept: Request = serde_json::from_slice(&bench.kept[REQUEST_FILE]).unwrap();
    assert_eq!(
        kept,
        Request::read(&request(&candidate).to_string()).unwrap()
    );
    assert_eq!(
        bench.kept[RECORD_FILE],
        serde_json::to_vec(&record).unwrap()
    );
    let written: Value = serde_json::from_slice(&bench.kept[RECORD_FILE]).unwrap();
    for (fence, value) in [
        ("source_application", "NOT_PERFORMED"),
        ("admission", "Unadmitted"),
        ("production_activation", "HOLD"),
        ("evidence_scope", "FIXED_LOCAL_COMMANDS"),
        ("mathematical_measurement", "NOT_MEASURED"),
        ("authority_effect", "None"),
    ] {
        assert_eq!(written[fence], value, "{fence}");
    }
    assert_eq!(written["outcome"], "REPAIRED");
    assert_eq!(
        written["baseline"][0],
        json!({
            "check_id": "positive", "code": 1,
            "stdout": {"sha256": "", "head": "", "truncated": false},
            "stderr": {"sha256": "", "head": "", "truncated": false},
        })
    );
    assert_eq!(
        written["stages"][2],
        json!({"stage": "E", "name": "evaluate", "status": "DONE"})
    );
}

#[test]
fn effects_happen_in_stage_order() {
    let (_, bench) = ran(&request(&patch("adjust.py", "n - 1", "n + 1")));
    assert_eq!(
        bench.effects(),
        [
            "open",
            "run positive",
            "run control",
            "write adjust.py",
            "run positive",
            "run control",
            "keep record.json"
        ]
    );
    let reads = |prefix: &str| {
        bench
            .log
            .iter()
            .filter(|line| line.starts_with(prefix))
            .count()
    };
    assert_eq!(
        reads("source "),
        8,
        "both sources are read at C, R, E and T"
    );
    assert_eq!(
        reads("copy "),
        17,
        "both copies around each of four checks, and the patched file"
    );
    assert_eq!(bench.log[0], "source adjust.py");
    assert_eq!(bench.log.last().unwrap(), "keep record.json");
}

#[test]
fn a_patch_that_leaves_the_failing_check_failing_is_a_recorded_failure() {
    let body = request(&patch("adjust.py", "n - 1", "n + 2"));
    let (record, bench) = ran(&body);
    assert_eq!(record.outcome, Disposition::Ineffective);
    assert_eq!(exits(&record.after), [("positive", 1), ("control", 0)]);
    assert_eq!(record.changed_paths, ["adjust.py"]);
    assert_eq!(bench.source["adjust.py"], ADJUST.as_bytes());
    let id = format!("{}@run-1", record.case);
    assert_eq!(
        failure(&record),
        (
            id.as_str(),
            "bounded_repair",
            "run-1",
            COUNTERFEIT,
            "CREIMT"
        )
    );
    let same = [("positive", 1), ("control", 0)];
    assert_eq!(evidence(&record), stated(&record, None, &same, &same));
    let mut ledger = Ledger::new();
    ledger.append(record.failure.clone().unwrap()).unwrap();
    assert_eq!(ledger.entries().len(), 1);
}

#[test]
fn the_failure_names_the_workflow_the_request_gives() {
    let body = with(
        request(&patch("adjust.py", "n - 1", "n + 2")),
        "workflow",
        json!("WF57"),
    );
    let (record, _) = ran(&body);
    assert_eq!(failure(&record).1, "WF57");
}

#[test]
fn fixing_one_of_two_failing_checks_is_partial() {
    let checks = json!([
        check("positive", &["has", "adjust.py", "return n + 1"]),
        check("typed", &["has", "adjust.py", "-> int"]),
        check("control", &["has", "adjust.py", "        return n\n"])
    ]);
    let body = with(
        request(&patch("adjust.py", "n - 1", "n + 1")),
        "checks",
        checks,
    );
    let (record, _) = ran(&body);
    assert_eq!(record.outcome, Disposition::Partial);
    assert_eq!(
        exits(&record.baseline),
        [("positive", 1), ("typed", 1), ("control", 0)]
    );
    assert_eq!(
        exits(&record.after),
        [("positive", 0), ("typed", 1), ("control", 0)]
    );
    assert_eq!(failure(&record).3, COUNTERFEIT);
}

#[test]
fn breaking_a_check_that_passed_is_a_regression_even_when_the_target_is_fixed() {
    let breaks = "--- a/adjust.py\n+++ b/adjust.py\n@@ -3,2 +3,2 @@\n-        return n\n-    return n - 1\n+        return -n\n+    return n + 1\n";
    let (record, _) = ran(&request(breaks));
    assert_eq!(record.outcome, Disposition::Regression);
    assert_eq!(exits(&record.after), [("positive", 0), ("control", 1)]);
    assert_eq!(failure(&record).3, LEAK);
    assert_eq!(record.trace, "CREIMT");
    assert_eq!(
        evidence(&record),
        stated(
            &record,
            None,
            &[("positive", 1), ("control", 0)],
            &[("positive", 0), ("control", 1)]
        ),
        "the evidence binds the exits before and after, in that order"
    );
}

#[test]
fn a_clean_baseline_needs_no_repair_and_the_patch_is_not_applied() {
    let checks = json!([check(
        "control",
        &["has", "adjust.py", "        return n\n"]
    )]);
    for candidate in [
        patch("adjust.py", "n - 1", "n + 1"),
        "not a patch\n".to_owned(),
    ] {
        let (record, bench) = ran(&with(request(&candidate), "checks", checks.clone()));
        assert_eq!(record.outcome, Disposition::NoRepairNeeded);
        assert_eq!(
            (record.trace.as_str(), statuses(&record).as_str()),
            ("CRIMT", "CR-IMT")
        );
        assert_eq!(bench.copy["adjust.py"], ADJUST.as_bytes());
        assert_eq!(record.working_manifest, record.source_manifest);
        assert!(record.changed_paths.is_empty() && record.after.is_empty());
        assert_eq!(
            (record.failure.clone(), record.refusal.clone()),
            (None, None)
        );
        assert!(!bench.log.iter().any(|line| line.starts_with("write")));
    }
}

#[test]
fn a_patch_outside_the_write_set_is_refused_before_anything_is_written() {
    let read_only = "--- a/notes.txt\n+++ b/notes.txt\n@@ -1 +1 @@\n-notes\n+return n + 1\n";
    let both = format!("{}{read_only}", patch("adjust.py", "n - 1", "n + 1"));
    let unknown = patch("other.py", "n - 1", "n + 1");
    for (candidate, why) in [
        (read_only.to_owned(), "notes.txt is not in the write set"),
        (both, "notes.txt is not in the write set"),
        (unknown, "other.py is not in the write set"),
        (
            "diff --git a/adjust.py b/adjust.py\n".to_owned(),
            "the patch edits no file",
        ),
    ] {
        let (record, bench) = ran(&request(&candidate));
        assert_eq!(refusal(&record), ("E", "PATCH_SCOPE_REFUSED", why));
        assert_eq!(record.outcome, Disposition::Refused);
        assert_eq!(
            (record.trace.as_str(), statuses(&record).as_str()),
            ("CRIMT", "CR!IMT")
        );
        assert_eq!(failure(&record).3, MISFIT);
        assert_eq!(failure(&record).4, "CRIMT");
        assert_eq!(
            evidence(&record),
            stated(
                &record,
                Some("PATCH_SCOPE_REFUSED"),
                &[("positive", 1), ("control", 0)],
                &[]
            ),
            "the evidence binds the refusal"
        );
        assert_eq!(bench.copy, bench.source);
        assert!(record.after.is_empty() && record.changed_paths.is_empty());
        assert_eq!(record.working_manifest, record.source_manifest);
    }
}

#[test]
fn a_patch_that_does_not_fit_is_refused_as_a_whole() {
    let two_files = with(
        with(
            request(""),
            "write_paths",
            json!(["adjust.py", "notes.txt"]),
        ),
        "candidate_patch",
        json!(format!(
            "{}--- a/notes.txt\n+++ b/notes.txt\n@@ -1 +1 @@\n-other\n+x\n",
            patch("adjust.py", "n - 1", "n + 1")
        )),
    );
    let same = patch("adjust.py", "n - 1", "n - 1");
    for (body, why) in [
        (request("garbage\n"), "unexpected line \"garbage\""),
        (
            request(&patch("adjust.py", "n - 3", "n + 1")),
            "the hunk at old line 4 of adjust.py does not match the file",
        ),
        (request(&same), "the patch changes no byte"),
        (
            two_files,
            "the hunk at old line 1 of notes.txt does not match the file",
        ),
    ] {
        let (record, bench) = ran(&body);
        assert_eq!(refusal(&record), ("E", "PATCH_REFUSED", why));
        assert_eq!(failure(&record).3, MISFIT);
        assert_eq!(bench.copy, bench.source, "{why}");
        assert!(!bench.log.iter().any(|line| line.starts_with("write")));
    }
}

#[test]
fn a_file_that_is_not_text_cannot_be_patched() {
    let mut bench = Fake::new();
    bench
        .source
        .insert("adjust.py".to_owned(), vec![0xff, 0xfe, b'\n']);
    let body = with(
        request(&patch("adjust.py", "n - 1", "n + 1")),
        "sources",
        json!({"adjust.py": hex(&[0xff, 0xfe, b'\n']), "notes.txt": hex(NOTES.as_bytes())}),
    );
    let record = repair(&body.to_string(), &mut bench).unwrap();
    assert_eq!(
        refusal(&record),
        ("E", "PATCH_REFUSED", "adjust.py is not UTF-8 text")
    );
}

#[test]
fn a_source_that_differs_from_its_declared_hash_stops_the_run_at_capture() {
    let mut bench = Fake::new();
    bench
        .source
        .insert("notes.txt".to_owned(), b"edited\n".to_vec());
    let record = repair(
        &request(&patch("adjust.py", "n - 1", "n + 1")).to_string(),
        &mut bench,
    )
    .unwrap();
    assert_eq!(
        refusal(&record),
        (
            "C",
            "SOURCE_CHANGED",
            "notes.txt does not have its declared hash"
        )
    );
    assert_eq!(
        (record.trace.as_str(), statuses(&record).as_str()),
        ("IM", "!--IM!")
    );
    assert_eq!(record.outcome, Disposition::Refused);
    assert_eq!(record.failure, None);
    assert!(!record.source_intact);
    assert!(record.working_manifest.is_empty() && record.baseline.is_empty());
    assert_eq!(bench.effects(), ["keep record.json"]);
    assert!(bench.copy.is_empty());
}

#[test]
fn a_missing_source_is_refused_with_the_code_the_bench_gives() {
    let mut bench = Fake::new();
    bench.source.remove("notes.txt");
    let record = repair(
        &request(&patch("adjust.py", "n - 1", "n + 1")).to_string(),
        &mut bench,
    )
    .unwrap();
    assert_eq!(
        refusal(&record),
        ("C", "SOURCE_FILE_REFUSED", "source has no notes.txt")
    );
}

#[test]
fn a_source_that_changes_during_the_run_refuses_it_even_after_a_repair() {
    let drift = |when: &[Value]| {
        let mut checks = vec![check("positive", &["has", "adjust.py", "return n + 1"])];
        checks.extend_from_slice(when);
        with(
            request(&patch("adjust.py", "n - 1", "n + 1")),
            "checks",
            json!(checks),
        )
    };
    let (during_baseline, _) = ran(&drift(&[check("drifts", &["drift", "notes.txt"])]));
    assert_eq!(refusal(&during_baseline).0, "E");
    assert_eq!(refusal(&during_baseline).1, "SOURCE_CHANGED");
    assert_eq!(statuses(&during_baseline), "CR!IM!");
    assert_eq!(during_baseline.failure, None);

    let mut bench = Fake::new();
    bench.copy.clear();
    let body = with(
        request(&patch("adjust.py", "n - 1", "n + 1")),
        "checks",
        json!([
            check("positive", &["has", "adjust.py", "return n + 1"]),
            check("late", &["has-then-drift"])
        ]),
    );
    let late = Late {
        inner: bench,
        runs: 0,
    };
    let (record, late) = ran_on(&body, late);
    assert_eq!(exits(&record.after), [("positive", 0), ("late", 0)]);
    assert_eq!(
        refusal(&record),
        (
            "T",
            "SOURCE_CHANGED",
            "notes.txt does not have its declared hash"
        )
    );
    assert_eq!(record.outcome, Disposition::Refused);
    assert_eq!(
        (record.trace.as_str(), statuses(&record).as_str()),
        ("CREIM", "CREIM!")
    );
    assert!(!record.source_intact);
    assert_eq!(
        late.inner.kept[RECORD_FILE],
        serde_json::to_vec(&record).unwrap()
    );
}

/// A bench whose `late` check passes, and rewrites an original source the second time it runs.
struct Late {
    inner: Fake,
    runs: u32,
}

impl Bench for Late {
    fn source(&mut self, path: &str) -> Result<Vec<u8>, Refusal> {
        self.inner.source(path)
    }
    fn open(
        &mut self,
        files: &BTreeMap<String, Vec<u8>>,
        kept: &[(&str, Vec<u8>)],
    ) -> Result<(), Refusal> {
        self.inner.open(files, kept)
    }
    fn copy(&mut self, path: &str) -> Result<Vec<u8>, Refusal> {
        self.inner.copy(path)
    }
    fn write(&mut self, path: &str, bytes: &[u8]) -> Result<(), Refusal> {
        self.inner.write(path, bytes)
    }
    fn run(&mut self, check: &Check) -> Result<Exit, Refusal> {
        if check.check_id != "late" {
            return self.inner.run(check);
        }
        self.runs += 1;
        if self.runs == 2 {
            self.inner
                .source
                .insert("notes.txt".to_owned(), b"drifted".to_vec());
        }
        Ok(Exit::default())
    }
    fn keep(&mut self, name: &str, bytes: &[u8]) -> Result<(), Refusal> {
        self.inner.keep(name, bytes)
    }
}

fn ran_on<B: Bench>(request: &Value, mut bench: B) -> (Terminal, B) {
    let record = repair(&request.to_string(), &mut bench).unwrap();
    (record, bench)
}

#[test]
fn a_regression_seen_before_the_source_drifted_is_not_recorded_as_a_failure() {
    let breaks = "--- a/adjust.py\n+++ b/adjust.py\n@@ -3,2 +3,2 @@\n-        return n\n-    return n - 1\n+        return -n\n+    return n + 1\n";
    let checks = json!([
        check("positive", &["has", "adjust.py", "return n + 1"]),
        check("control", &["has", "adjust.py", "        return n\n"]),
        check("late", &["has-then-drift"])
    ]);
    let late = Late {
        inner: Fake::new(),
        runs: 0,
    };
    let (record, _) = ran_on(&with(request(breaks), "checks", checks), late);
    assert_eq!(
        exits(&record.after),
        [("positive", 0), ("control", 1), ("late", 0)]
    );
    assert_eq!(refusal(&record).0, "T");
    assert_eq!(
        (record.outcome, record.failure),
        (Disposition::Refused, None)
    );
}

#[test]
fn a_check_that_rewrites_the_working_copy_is_refused() {
    let scribbles = |position: usize| {
        let mut checks = vec![check("positive", &["has", "adjust.py", "return n + 1"])];
        checks.insert(position, check("scribbles", &["scribble", "notes.txt"]));
        with(
            request(&patch("adjust.py", "n - 1", "n + 1")),
            "checks",
            json!(checks),
        )
    };
    for position in [0, 1] {
        let (record, _) = ran(&scribbles(position));
        assert_eq!(
            refusal(&record),
            (
                "R",
                "WORKING_COPY_CHANGED",
                "notes.txt changed in the working copy outside the patch"
            )
        );
        assert_eq!(
            (statuses(&record).as_str(), record.failure.clone()),
            ("C!-IMT", None)
        );
        assert!(record.baseline.is_empty());
        assert!(record.source_intact);
    }
}

#[test]
fn a_check_that_cannot_run_refuses_the_run_and_blames_no_candidate() {
    let checks = json!([
        check("positive", &["has", "adjust.py", "return n + 1"]),
        check("tool", &["absent"])
    ]);
    let (record, _) = ran(&with(
        request(&patch("adjust.py", "n - 1", "n + 1")),
        "checks",
        checks,
    ));
    assert_eq!(
        refusal(&record),
        ("R", "CHECK_UNAVAILABLE", "tool: not found")
    );
    assert_eq!(
        (record.outcome, record.failure.clone()),
        (Disposition::Refused, None)
    );
    assert_eq!(record.trace, "CIMT");
}

#[test]
fn a_bench_that_cannot_open_or_write_refuses_the_run() {
    let body = request(&patch("adjust.py", "n - 1", "n + 1")).to_string();
    let mut closed = Fake {
        refuse_open: true,
        refuse_keep: true,
        ..Fake::new()
    };
    let record = repair(&body, &mut closed).unwrap();
    assert_eq!(
        refusal(&record),
        ("C", "OUTPUT_CONFLICT", "the run folder exists")
    );
    assert_eq!(statuses(&record), "!--IMT");
    assert!(record.source_intact && closed.kept.is_empty());

    let mut read_only = Fake {
        refuse_write: true,
        ..Fake::new()
    };
    let record = repair(&body, &mut read_only).unwrap();
    assert_eq!(
        refusal(&record),
        ("E", "IO_UNAVAILABLE", "the working copy is read-only")
    );
    assert_eq!(record.failure, None);
}

#[test]
fn a_run_without_a_refusal_exists_only_with_its_record_kept() {
    let body = request(&patch("adjust.py", "n - 1", "n + 1")).to_string();
    let mut bench = Fake {
        refuse_keep: true,
        ..Fake::new()
    };
    assert_eq!(
        repair(&body, &mut bench).unwrap_err(),
        Refusal::new("OUTPUT_UNAVAILABLE", "the run folder cannot be written")
    );
    let refused = respond(
        &body,
        &mut Fake {
            refuse_keep: true,
            ..Fake::new()
        },
    );
    assert!(
        matches!(refused, Outcome::Refused { refusal } if refusal.code == "OUTPUT_UNAVAILABLE")
    );
}

#[test]
fn the_host_passes_only_a_repair() {
    let outcome = |candidate: &str| respond(&request(candidate).to_string(), &mut Fake::new());
    let Outcome::Pass { result } = outcome(&patch("adjust.py", "n - 1", "n + 1")) else {
        panic!("a repair passes");
    };
    assert_eq!(
        (&result["outcome"], &result["trace"]),
        (&json!("REPAIRED"), &json!("CREIMT"))
    );
    for (candidate, verdict) in [
        (patch("adjust.py", "n - 1", "n + 2"), "INEFFECTIVE"),
        (patch("notes.txt", "n - 1", "n + 1"), "REFUSED"),
    ] {
        let Outcome::Fail { result } = outcome(&candidate) else {
            panic!("{verdict} is a FAIL with its record");
        };
        assert_eq!(result["outcome"], verdict);
        assert_eq!(result["failure"]["kind"], "failure");
    }
    let Outcome::Refused { refusal } = respond("{}", &mut Fake::new()) else {
        panic!("an unreadable request is refused");
    };
    assert_eq!(refusal.code, "BAD_REQUEST");
}

type Exits = [(&'static str, i32)];

fn observed(pairs: &Exits) -> Vec<Observation> {
    pairs
        .iter()
        .map(|(id, code)| Observation {
            check_id: (*id).to_owned(),
            exit: Exit {
                code: *code,
                ..Exit::default()
            },
        })
        .collect()
}

#[test]
fn the_disposition_compares_the_failing_checks_before_and_after() {
    let table: [(&Exits, &Exits, Disposition); 10] = [
        (
            &[("a", 1), ("b", 0)],
            &[("a", 0), ("b", 0)],
            Disposition::Repaired,
        ),
        (
            &[("a", 2), ("b", -1)],
            &[("a", 0), ("b", 0)],
            Disposition::Repaired,
        ),
        (
            &[("a", 1), ("b", 1)],
            &[("a", 0), ("b", 1)],
            Disposition::Partial,
        ),
        (
            &[("a", 1), ("b", 0)],
            &[("a", 1), ("b", 0)],
            Disposition::Ineffective,
        ),
        (
            &[("a", 1), ("b", 0)],
            &[("a", 7), ("b", 0)],
            Disposition::Ineffective,
        ),
        (
            &[("a", 1), ("b", 0)],
            &[("a", 0), ("b", 1)],
            Disposition::Regression,
        ),
        (
            &[("a", 1), ("b", 0)],
            &[("a", 1), ("b", 1)],
            Disposition::Regression,
        ),
        (&[("a", -1)], &[("a", -1)], Disposition::Ineffective),
        (&[("a", 0), ("b", 0)], &[], Disposition::NoRepairNeeded),
        (&[("a", 0)], &[("a", 1)], Disposition::NoRepairNeeded),
    ];
    for (before, after, expected) in table {
        assert_eq!(
            assess(false, &observed(before), &observed(after)),
            expected,
            "{before:?} {after:?}"
        );
        assert_eq!(
            assess(true, &observed(before), &observed(after)),
            Disposition::Refused
        );
    }
}

fn read(body: &Value) -> Result<Request, &'static str> {
    Request::read(&body.to_string()).map_err(|refusal| refusal.code)
}

fn base() -> Value {
    request(&patch("adjust.py", "n - 1", "n + 1"))
}

#[test]
fn a_request_has_defaults_and_no_unknown_field() {
    let request = read(&base()).unwrap();
    assert_eq!(request.checks[0].timeout_seconds, 20);
    assert_eq!(request.workflow, "bounded_repair");
    assert_eq!(
        read(&with(base(), "verdict", json!("REPAIRED"))),
        Err("BAD_REQUEST")
    );
    let mut extra = base();
    extra["checks"][0]["shell"] = json!(true);
    assert_eq!(read(&extra), Err("BAD_REQUEST"));
    assert_eq!(Request::read("not json").unwrap_err().code, "BAD_REQUEST");
}

#[test]
fn names_and_text_are_bounded() {
    for (key, accepted) in [
        ("a", true),
        ("A9_-", true),
        ("-a", false),
        ("_a", false),
        ("", false),
        ("a b", false),
        ("a/b", false),
        ("a\n", false),
    ] {
        assert_eq!(
            read(&with(base(), "run_key", json!(key))).is_ok(),
            accepted,
            "{key:?}"
        );
    }
    assert!(read(&with(base(), "run_key", json!("k".repeat(80)))).is_ok());
    assert_eq!(
        read(&with(base(), "run_key", json!("k".repeat(81)))),
        Err("RUN_KEY_REFUSED")
    );
    for field in ["objective", "workflow"] {
        assert!(read(&with(base(), field, json!("\u{e9}".repeat(2048)))).is_ok());
        for bad in ["\u{e9}".repeat(2049), String::new(), "  \n".to_owned()] {
            assert_eq!(
                read(&with(base(), field, json!(bad))),
                Err("OBJECTIVE_REFUSED"),
                "{field}"
            );
        }
    }
    let long = |bytes: usize| with(base(), "candidate_patch", json!("x".repeat(bytes)));
    assert!(read(&long(65536)).is_ok());
    assert_eq!(read(&long(65537)), Err("PATCH_REFUSED"));
    assert_eq!(read(&long(0)), Err("PATCH_REFUSED"));
}

#[test]
fn a_source_path_is_a_plain_relative_path() {
    for good in [
        "adjust.py",
        "src/pkg/mod.rs",
        "a b/c-d_e.txt",
        ".github/x",
        "CONSOLE.txt",
        "COM10",
        "com",
        "LPT0",
        "gitx/.gitignore",
    ] {
        assert_eq!(relative_file(good), Ok(()), "{good}");
    }
    for bad in [
        "",
        "/abs",
        "a//b",
        "./a",
        "a/./b",
        "../a",
        "a/..",
        "a\\b",
        "C:/a",
        "a:b",
        "a\0b",
        "a\rb",
        "a\nb",
        "a\tb",
        ".git/config",
        "a/.GIT/x",
        "a./b",
        "a /b",
        "dir/name.",
        "dir/name ",
        "CON",
        "con.txt",
        "a/PRN",
        "aux.tar.gz",
        "NUL",
        "COM1",
        "com9.log",
        "LPT1",
        "lpt9",
    ] {
        let refusal = relative_file(bad).unwrap_err();
        assert_eq!(refusal.code, "SOURCE_PATH_REFUSED", "{bad:?}");
        assert_eq!(
            refusal.message,
            format!("{bad:?} is not a plain relative path")
        );
        let sources = json!({bad: hex(b"x"), "adjust.py": hex(ADJUST.as_bytes())});
        assert_eq!(
            read(&with(base(), "sources", sources)),
            Err("SOURCE_PATH_REFUSED"),
            "{bad:?}"
        );
    }
}

#[test]
fn a_source_hash_is_64_lowercase_hex_digits() {
    let digest = hex(ADJUST.as_bytes());
    let sources = |value: &str| with(base(), "sources", json!({"adjust.py": value}));
    assert!(read(&sources(&digest)).is_ok());
    for bad in [
        digest.to_uppercase(),
        digest[1..].to_owned(),
        format!("{digest}0"),
        digest.replace(&digest[..1], "g"),
        format!("sha256:{}", &digest[7..]),
    ] {
        assert_eq!(read(&sources(&bad)), Err("SOURCE_DIGEST_REFUSED"), "{bad}");
    }
}

fn many(count: usize) -> Value {
    let digest = hex(b"x");
    Value::Object(
        (0..count)
            .map(|n| (format!("f{n}.txt"), json!(digest)))
            .collect(),
    )
}

#[test]
fn the_scope_is_nonempty_bounded_and_distinct() {
    let scope = |sources: Value, writes: Value| {
        with(with(base(), "sources", sources), "write_paths", writes)
    };
    assert!(read(&scope(many(64), json!(["f0.txt"]))).is_ok());
    let writes =
        |count: usize| Value::Array((0..count).map(|n| json!(format!("f{n}.txt"))).collect());
    assert!(read(&scope(many(64), writes(32))).is_ok());
    let checks = |count: usize| {
        Value::Array(
            (0..count)
                .map(|n| check(&format!("c{n}"), &["exit", "0"]))
                .collect(),
        )
    };
    assert!(read(&with(base(), "checks", checks(16))).is_ok());
    for refused in [
        scope(many(65), json!(["f0.txt"])),
        scope(many(0), json!([])),
        scope(many(64), writes(33)),
        scope(many(2), json!([])),
        scope(many(2), json!(["f0.txt", "f0.txt"])),
        scope(many(2), json!(["f2.txt"])),
        scope(many(2), json!(["f0.txt", "other.txt"])),
        scope(
            json!({"A.py": hex(b"x"), "a.py": hex(b"x")}),
            json!(["a.py"]),
        ),
        scope(
            json!({"\u{c9}.py": hex(b"x"), "\u{e9}.py": hex(b"x")}),
            json!(["\u{e9}.py"]),
        ),
        with(base(), "checks", checks(17)),
        with(base(), "checks", checks(0)),
        with(
            base(),
            "checks",
            json!([check("same", &["exit", "0"]), check("same", &["exit", "1"])]),
        ),
    ] {
        assert_eq!(read(&refused), Err("REPAIR_SCOPE_REFUSED"), "{refused}");
    }
}

#[test]
fn a_check_is_a_named_bounded_command() {
    let one = |value: Value| with(base(), "checks", json!([value]));
    let timed =
        |seconds: u32| one(json!({"check_id": "c", "argv": ["x"], "timeout_seconds": seconds}));
    assert_eq!(read(&timed(1)).unwrap().checks[0].timeout_seconds, 1);
    assert!(read(&timed(60)).is_ok());
    let arguments = |count: usize| one(json!({"check_id": "c", "argv": vec!["x"; count]}));
    assert!(read(&arguments(32)).is_ok());
    assert!(read(&one(check(&format!("c{}", "x".repeat(63)), &["x"]))).is_ok());
    assert!(read(&one(check("a9_-", &["x"]))).is_ok());
    for refused in [
        timed(0),
        timed(61),
        arguments(0),
        arguments(33),
        one(check("c", &["x", ""])),
        one(check("c", &["x", "a\0b"])),
        one(check("", &["x"])),
        one(check("9c", &["x"])),
        one(check("C", &["x"])),
        one(check("c d", &["x"])),
        one(check(&format!("c{}", "x".repeat(64)), &["x"])),
    ] {
        assert_eq!(read(&refused), Err("CHECK_REFUSED"), "{refused}");
    }
    let second = with(
        base(),
        "checks",
        json!([check("a", &["x"]), check("B", &["x"])]),
    );
    assert_eq!(read(&second), Err("CHECK_REFUSED"), "every check is read");
    assert_eq!(
        Request::read(&one(check("9c", &["x"])).to_string())
            .unwrap_err()
            .message,
        "check \"9c\" is not well formed"
    );
}

#[test]
fn the_three_identities_bind_different_things() {
    let read = |body: &Value| Request::read(&body.to_string()).unwrap();
    let first = read(&base());
    let other_patch = read(&request(&patch("adjust.py", "n - 1", "n + 2")));
    let other_run = read(&with(base(), "run_key", json!("run-2")));
    let mut slower = base();
    slower["checks"][0]["timeout_seconds"] = json!(21);
    let other_check = read(&slower);
    let mut explicit = base();
    explicit["checks"][0]["timeout_seconds"] = json!(20);
    explicit["workflow"] = json!("bounded_repair");
    let mut other_source = base();
    other_source["sources"]["notes.txt"] = json!(hex(b"other"));
    let other_source = read(&other_source);

    assert_eq!(first.candidate_id(), other_run.candidate_id());
    assert_eq!(first.candidate_id(), other_check.candidate_id());
    assert_ne!(first.candidate_id(), other_patch.candidate_id());

    assert_eq!(first.digest(), read(&explicit).digest());
    for different in [&other_patch, &other_run, &other_check, &other_source] {
        assert_ne!(first.digest(), different.digest());
    }

    assert_eq!(first.case(), other_patch.case());
    assert_eq!(first.case(), other_run.case());
    assert_ne!(first.case(), other_check.case());
    assert_ne!(first.case(), other_source.case());
}

#[test]
fn the_identities_are_hashes_of_stated_bytes() {
    let body = json!({
        "run_key": "k", "objective": "o", "sources": {"b": hex(b"2"), "a": hex(b"1")},
        "write_paths": ["a"], "checks": [{"check_id": "c", "argv": ["x", "y"]}],
        "candidate_patch": "p",
    });
    let request = Request::read(&body.to_string()).unwrap();
    let sources = format!("{{\"a\":\"{}\",\"b\":\"{}\"}}", hex(b"1"), hex(b"2"));
    let checks = "[{\"check_id\":\"c\",\"argv\":[\"x\",\"y\"],\"timeout_seconds\":20}]";
    let whole = format!(
        "pfp.operads.repair.request.v1\n{{\"run_key\":\"k\",\"objective\":\"o\",\"sources\":{sources},\
         \"write_paths\":[\"a\"],\"checks\":{checks},\"candidate_patch\":\"p\",\"workflow\":\"bounded_repair\"}}"
    );
    assert_eq!(
        request.digest().unwrap(),
        format!("sha256:{}", hex(whole.as_bytes()))
    );
    assert_eq!(request.candidate_id(), format!("sha256:{}", hex(b"p")));
    let case = hex(format!("pfp.operads.repair.case.v1\n{sources}\n{checks}").as_bytes());
    assert_eq!(request.case().unwrap(), format!("r{}", &case[..16]));
}

#[test]
fn a_record_carries_the_identities_of_its_request() {
    let body = base();
    let request = Request::read(&body.to_string()).unwrap();
    let (record, _) = ran(&body);
    assert_eq!(record.request_digest, request.digest().unwrap());
    assert_eq!(record.candidate_id, request.candidate_id());
    assert_eq!(record.case, request.case().unwrap());
    assert_eq!(record.source_manifest, request.sources);
}
