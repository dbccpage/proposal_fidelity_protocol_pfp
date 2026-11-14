//! Tests of the repair bench on real files and real processes.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:workshop:tests:v1
//!
//! The checks here are the host binary itself: `pfp_operad judge FILE` exits 0 when the stored
//! answer is the exact sum and 1 when it is not. The file under repair is that stored answer.

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command as Process;
use std::sync::atomic::{AtomicU32, Ordering};

use pfp_operads::host::Outcome;
use pfp_operads::repair::{Bench, Check, Exit};
use pfp_operads::workshop::{repair_in, stream, Workshop, MAX_SOURCE_BYTES, WORKSPACE};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

/// The length of a kept stream head, written out so that a change to the limit fails here.
const HEAD: usize = 4096;
/// The variables a check must not inherit, written out for the same reason.
const SCRUBBED: [&str; 12] = [
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "PYTHONPYCACHEPREFIX",
    "PYTHONOPTIMIZE",
];
/// The variables every check gets.
const PINNED: [&str; 3] = [
    "PYTHONDONTWRITEBYTECODE=1",
    "GIT_CONFIG_NOSYSTEM=1",
    "GIT_CONFIG_GLOBAL=/dev/null",
];

const HOST: &str = env!("CARGO_BIN_EXE_pfp_operad");
const ANSWER: &str = "{\n  \"checker\": \"integer_sum_v1\",\n  \"case\": {\"values\": [1, 2, 3]},\n  \"answer\": {\"total\": 5}\n}\n";
const CONTROL: &str = "{\n  \"checker\": \"integer_sum_v1\",\n  \"case\": {\"values\": [4, -1]},\n  \"answer\": {\"total\": 3}\n}\n";
static NEXT: AtomicU32 = AtomicU32::new(0);

fn hex(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

/// A fresh folder holding a `source` tree with the two stored answers.
fn scratch() -> PathBuf {
    let folder = std::env::temp_dir().join(format!(
        "pfp_workshop_{}_{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::SeqCst)
    ));
    let _ = fs::remove_dir_all(&folder);
    fs::create_dir_all(folder.join("source/nested/deep")).unwrap();
    fs::write(folder.join("source/answer.json"), ANSWER).unwrap();
    fs::write(folder.join("source/control.json"), CONTROL).unwrap();
    fs::write(folder.join("source/nested/deep/note.txt"), "deep\n").unwrap();
    folder
}

fn total(path: &str, from: i32, to: i32) -> String {
    format!(
        "--- a/{path}\n+++ b/{path}\n@@ -4 +4 @@\n-  \"answer\": {{\"total\": {from}}}\n+  \"answer\": {{\"total\": {to}}}\n"
    )
}

fn judge(id: &str, file: &str) -> Value {
    json!({"check_id": id, "argv": [HOST, "judge", file]})
}

fn request(candidate: &str) -> Value {
    json!({
        "run_key": "disk-1",
        "objective": "the stored total must be the exact sum",
        "sources": {"answer.json": hex(ANSWER.as_bytes()), "control.json": hex(CONTROL.as_bytes())},
        "write_paths": ["answer.json"],
        "checks": [judge("positive", "answer.json"), judge("control", "control.json")],
        "candidate_patch": candidate,
    })
}

fn ran(body: &Value, folder: &Path) -> (String, Value) {
    match repair_in(
        &body.to_string(),
        &folder.join("source"),
        &folder.join("run"),
        None,
    ) {
        Outcome::Pass { result } => ("PASS".to_owned(), result),
        Outcome::Fail { result } => ("FAIL".to_owned(), result),
        Outcome::Refused { refusal } => (
            "REFUSED".to_owned(),
            json!({"code": refusal.code, "message": refusal.message}),
        ),
    }
}

fn codes(observations: &Value) -> Vec<i64> {
    observations
        .as_array()
        .unwrap()
        .iter()
        .map(|seen| seen["code"].as_i64().unwrap())
        .collect()
}

fn bench(folder: &Path) -> Workshop {
    Workshop::new(&folder.join("source"), &folder.join("run")).unwrap()
}

fn opened(folder: &Path) -> Workshop {
    let mut bench = bench(folder);
    let files = BTreeMap::from([("answer.json".to_owned(), ANSWER.as_bytes().to_vec())]);
    bench.open(&files, &[]).unwrap();
    bench
}

fn check(argv: &[&str], timeout_seconds: u32) -> Check {
    Check {
        check_id: "probe".to_owned(),
        argv: argv.iter().map(|arg| (*arg).to_owned()).collect(),
        timeout_seconds,
    }
}

fn code_of<T: std::fmt::Debug>(result: Result<T, pfp_operads::Refusal>) -> &'static str {
    result.unwrap_err().code
}

#[test]
fn a_stored_answer_is_repaired_on_disk_and_the_source_is_untouched() {
    let folder = scratch();
    let candidate = total("answer.json", 5, 6);
    let (status, record) = ran(&request(&candidate), &folder);
    assert_eq!(
        (status.as_str(), &record["outcome"], &record["trace"]),
        ("PASS", &json!("REPAIRED"), &json!("CREIMT"))
    );
    assert_eq!(
        (codes(&record["baseline"]), codes(&record["after"])),
        (vec![1, 0], vec![0, 0])
    );
    assert_eq!(
        fs::read_to_string(folder.join("source/answer.json")).unwrap(),
        ANSWER
    );
    assert_eq!(
        fs::read_to_string(folder.join("source/control.json")).unwrap(),
        CONTROL
    );
    let run = folder.join("run");
    let patched = fs::read_to_string(run.join(WORKSPACE).join("answer.json")).unwrap();
    assert_eq!(patched, ANSWER.replace("5", "6"));
    assert_eq!(
        patched.len(),
        ANSWER.len(),
        "the edit keeps the file's size"
    );
    assert_eq!(
        record["working_manifest"]["answer.json"],
        hex(patched.as_bytes())
    );
    assert_eq!(
        fs::read_to_string(run.join(WORKSPACE).join("control.json")).unwrap(),
        CONTROL
    );
    assert_eq!(
        fs::read_to_string(run.join("candidate.patch")).unwrap(),
        candidate
    );
    let kept: Value = serde_json::from_slice(&fs::read(run.join("record.json")).unwrap()).unwrap();
    assert_eq!(kept, record);
    let asked: Value =
        serde_json::from_slice(&fs::read(run.join("request.json")).unwrap()).unwrap();
    assert_eq!(
        asked["checks"][0]["argv"],
        json!([HOST, "judge", "answer.json"])
    );
    let mut names: Vec<String> = fs::read_dir(&run)
        .unwrap()
        .map(|entry| entry.unwrap().file_name().into_string().unwrap())
        .collect();
    names.sort();
    assert_eq!(
        names,
        ["candidate.patch", "record.json", "request.json", WORKSPACE]
    );
}

#[test]
fn a_record_keeps_what_each_check_printed() {
    let folder = scratch();
    let (_, record) = ran(&request(&total("answer.json", 5, 6)), &folder);
    let before = &record["baseline"][0]["stdout"];
    let said: Value = serde_json::from_str(before["head"].as_str().unwrap()).unwrap();
    assert_eq!(
        (&said["status"], &said["result"]["accepted"]),
        (&json!("FAIL"), &json!(false))
    );
    assert_eq!(
        before["sha256"],
        hex(before["head"].as_str().unwrap().as_bytes())
    );
    assert_eq!(before["truncated"], false);
    let after: Value =
        serde_json::from_str(record["after"][0]["stdout"]["head"].as_str().unwrap()).unwrap();
    assert_eq!(after["status"], "PASS");
    assert_eq!(
        record["after"][0]["stderr"],
        json!({"sha256": hex(b""), "head": "", "truncated": false})
    );
}

#[test]
fn the_paper_negative_cases_are_told_apart_on_disk() {
    let ineffective = request(&total("answer.json", 5, 7));
    let mut regressive = request(&format!(
        "{}{}",
        total("answer.json", 5, 6),
        total("control.json", 3, 4)
    ));
    regressive["write_paths"] = json!(["answer.json", "control.json"]);
    let forbidden = request(&total("control.json", 3, 4));
    let mut absent = request(&total("answer.json", 5, 6));
    absent["checks"][1]["argv"] = json!(["pfp-no-such-program-anywhere"]);
    let mut drifted = request(&total("answer.json", 5, 6));
    drifted["sources"]["control.json"] = json!(hex(b"an earlier control"));
    for (body, status, outcome, refusal, class) in [
        (
            ineffective,
            "FAIL",
            "INEFFECTIVE",
            Value::Null,
            json!("CounterfeitExactness"),
        ),
        (
            regressive,
            "FAIL",
            "REGRESSION",
            Value::Null,
            json!("BoundaryLeakage"),
        ),
        (
            forbidden,
            "FAIL",
            "REFUSED",
            json!("PATCH_SCOPE_REFUSED"),
            json!("StructuralNonFit"),
        ),
        (
            absent,
            "FAIL",
            "REFUSED",
            json!("CHECK_UNAVAILABLE"),
            Value::Null,
        ),
        (
            drifted,
            "FAIL",
            "REFUSED",
            json!("SOURCE_CHANGED"),
            Value::Null,
        ),
    ] {
        let folder = scratch();
        let (seen, record) = ran(&body, &folder);
        assert_eq!(
            (seen.as_str(), &record["outcome"]),
            (status, &json!(outcome))
        );
        assert_eq!(record["refusal"]["code"], refusal, "{outcome}");
        assert_eq!(record["failure"]["failure_class"], class, "{outcome}");
        assert_eq!(
            fs::read_to_string(folder.join("source/answer.json")).unwrap(),
            ANSWER
        );
        assert_eq!(
            fs::read_to_string(folder.join("source/control.json")).unwrap(),
            CONTROL
        );
        let kept: Value =
            serde_json::from_slice(&fs::read(folder.join("run/record.json")).unwrap()).unwrap();
        assert_eq!(kept, record, "{outcome}");
    }
}

#[test]
fn a_run_never_writes_into_a_folder_that_exists() {
    let folder = scratch();
    fs::create_dir(folder.join("run")).unwrap();
    fs::write(folder.join("run/earlier.txt"), "earlier").unwrap();
    let (status, record) = ran(&request(&total("answer.json", 5, 6)), &folder);
    assert_eq!(
        (
            status.as_str(),
            &record["refusal"]["stage"],
            &record["refusal"]["code"]
        ),
        ("FAIL", &json!("C"), &json!("OUTPUT_CONFLICT"))
    );
    assert_eq!(record["source_intact"], true);
    let names: Vec<_> = fs::read_dir(folder.join("run"))
        .unwrap()
        .map(|entry| entry.unwrap().file_name())
        .collect();
    assert_eq!(names, ["earlier.txt"]);
}

#[test]
fn the_run_folder_must_be_new_and_outside_the_source_tree() {
    let folder = scratch();
    let source = folder.join("source");
    let new = |source: &Path, run: &Path| Workshop::new(source, run).map(|_| ());
    assert_eq!(new(&source, &folder.join("run")), Ok(()));
    assert!(!folder.join("run").exists(), "binding creates nothing");
    for inside in [
        source.join("run"),
        source.join("nested/run"),
        source.clone(),
        folder.clone(),
    ] {
        assert_eq!(
            code_of(new(&source, &inside)),
            "OUTPUT_SCOPE_REFUSED",
            "{}",
            inside.display()
        );
    }
    assert_eq!(
        code_of(new(&source, &folder.join("no/such/parent/run"))),
        "OUTPUT_SCOPE_REFUSED"
    );
    assert_eq!(
        code_of(new(&source, Path::new("/"))),
        "OUTPUT_SCOPE_REFUSED"
    );
    assert_eq!(code_of(new(&source, Path::new(""))), "OUTPUT_SCOPE_REFUSED");
    assert_eq!(
        code_of(new(&folder.join("missing"), &folder.join("run"))),
        "SOURCE_ROOT_REFUSED"
    );
    assert_eq!(
        code_of(new(&source.join("answer.json"), &folder.join("run"))),
        "SOURCE_ROOT_REFUSED"
    );
    assert_eq!(
        new(&source, Path::new("pfp_workshop_relative_run_name")),
        Ok(())
    );
    let sibling = folder.join("source-2");
    assert_eq!(
        new(&source, &sibling),
        Ok(()),
        "a sibling whose name starts like the source is outside it"
    );
    let (status, refusal) = {
        let body = request(&total("answer.json", 5, 6)).to_string();
        match repair_in(&body, &source, &source.join("run"), None) {
            Outcome::Refused { refusal } => ("REFUSED", refusal.code),
            _ => ("RAN", ""),
        }
    };
    assert_eq!((status, refusal), ("REFUSED", "OUTPUT_SCOPE_REFUSED"));
    assert!(!source.join("run").exists());
}

#[test]
fn a_source_is_a_regular_file_of_bounded_size_under_the_root() {
    let folder = scratch();
    let mut bench = bench(&folder);
    assert_eq!(bench.source("answer.json").unwrap(), ANSWER.as_bytes());
    assert_eq!(bench.source("nested/deep/note.txt").unwrap(), b"deep\n");
    assert_eq!(code_of(bench.source("missing.txt")), "SOURCE_FILE_REFUSED");
    assert_eq!(
        code_of(bench.source("nested/missing/note.txt")),
        "SOURCE_FILE_REFUSED"
    );
    assert_eq!(code_of(bench.source("nested")), "SOURCE_FILE_REFUSED");
    assert_eq!(
        code_of(bench.source("answer.json/x")),
        "SOURCE_FILE_REFUSED"
    );
    assert_eq!(
        code_of(bench.source("../source/answer.json")),
        "SOURCE_PATH_REFUSED"
    );
    let limit = usize::try_from(MAX_SOURCE_BYTES).unwrap();
    fs::write(folder.join("source/full.bin"), vec![7; limit]).unwrap();
    fs::write(folder.join("source/over.bin"), vec![7; limit + 1]).unwrap();
    assert_eq!(bench.source("full.bin").unwrap().len(), limit);
    let over = bench.source("over.bin").unwrap_err();
    assert_eq!(
        (over.code, over.message.as_str()),
        (
            "SOURCE_FILE_REFUSED",
            "over.bin is not a regular file of at most 2097152 bytes"
        )
    );
    fs::create_dir(folder.join("source/sub")).unwrap();
    assert_eq!(
        bench.source("sub").unwrap_err().message,
        "sub is not a regular file of at most 2097152 bytes"
    );
    assert!(
        !folder.join("run").exists(),
        "reading sources creates nothing"
    );
}

#[cfg(unix)]
#[test]
fn a_link_on_the_way_to_a_source_is_refused() {
    use std::os::unix::fs::symlink;
    let folder = scratch();
    fs::write(folder.join("outside.txt"), "outside").unwrap();
    symlink(folder.join("outside.txt"), folder.join("source/link.txt")).unwrap();
    symlink(folder.join("source/nested"), folder.join("source/alias")).unwrap();
    let mut bench = bench(&folder);
    let refused = bench.source("link.txt").unwrap_err();
    assert_eq!(
        (refused.code, refused.message.as_str()),
        ("SOURCE_LINK_REFUSED", "link.txt goes through a link")
    );
    assert_eq!(
        code_of(bench.source("alias/deep/note.txt")),
        "SOURCE_LINK_REFUSED"
    );
    let files = BTreeMap::from([("answer.json".to_owned(), ANSWER.as_bytes().to_vec())]);
    bench.open(&files, &[]).unwrap();
    let copy = folder.join("run").join(WORKSPACE).join("answer.json");
    fs::remove_file(&copy).unwrap();
    symlink(folder.join("outside.txt"), &copy).unwrap();
    assert_eq!(code_of(bench.copy("answer.json")), "SOURCE_LINK_REFUSED");
    assert_eq!(
        code_of(bench.write("answer.json", b"through the link")),
        "SOURCE_LINK_REFUSED"
    );
    assert_eq!(
        fs::read_to_string(folder.join("outside.txt")).unwrap(),
        "outside"
    );
}

#[test]
fn opening_makes_the_working_copy_and_keeps_the_named_files() {
    let folder = scratch();
    let mut bench = bench(&folder);
    let files = BTreeMap::from([
        ("answer.json".to_owned(), ANSWER.as_bytes().to_vec()),
        ("nested/deep/note.txt".to_owned(), b"deep\n".to_vec()),
    ]);
    bench
        .open(
            &files,
            &[
                ("request.json", b"{}".to_vec()),
                ("candidate.patch", b"p".to_vec()),
            ],
        )
        .unwrap();
    let run = folder.join("run");
    assert_eq!(fs::read(run.join("request.json")).unwrap(), b"{}");
    assert_eq!(fs::read(run.join("candidate.patch")).unwrap(), b"p");
    assert_eq!(bench.copy("nested/deep/note.txt").unwrap(), b"deep\n");
    assert_eq!(bench.copy("answer.json").unwrap(), ANSWER.as_bytes());
    assert_eq!(code_of(bench.copy("control.json")), "SOURCE_FILE_REFUSED");

    bench.write("answer.json", b"new").unwrap();
    assert_eq!(bench.copy("answer.json").unwrap(), b"new");
    assert_eq!(
        fs::read_to_string(folder.join("source/answer.json")).unwrap(),
        ANSWER
    );
    assert_eq!(
        code_of(bench.write("created.txt", b"x")),
        "SOURCE_FILE_REFUSED"
    );
    assert_eq!(
        code_of(bench.write("../request.json", b"x")),
        "SOURCE_PATH_REFUSED"
    );
    assert!(!run.join(WORKSPACE).join("created.txt").exists());

    bench.keep("record.json", b"r").unwrap();
    assert_eq!(fs::read(run.join("record.json")).unwrap(), b"r");
    let again = bench.keep("record.json", b"other").unwrap_err();
    assert_eq!(again.code, "OUTPUT_CONFLICT");
    assert!(again.message.contains("record.json"));
    assert_eq!(fs::read(run.join("record.json")).unwrap(), b"r");
    assert_eq!(
        code_of(bench.keep("../escape.json", b"x")),
        "SOURCE_PATH_REFUSED"
    );
    assert_eq!(
        code_of(bench.keep("workspace/answer.json", b"x")),
        "OUTPUT_CONFLICT"
    );
    assert_eq!(bench.copy("answer.json").unwrap(), b"new");
}

#[test]
fn opening_refuses_a_bad_name_and_a_second_run_in_the_same_folder() {
    let folder = scratch();
    let bad = BTreeMap::from([("../escape.txt".to_owned(), b"x".to_vec())]);
    assert_eq!(
        code_of(bench(&folder).open(&bad, &[])),
        "SOURCE_PATH_REFUSED"
    );
    assert!(!folder.join("escape.txt").exists());
    let other = scratch();
    let files = BTreeMap::from([("answer.json".to_owned(), ANSWER.as_bytes().to_vec())]);
    assert_eq!(
        code_of(bench(&other).open(&files, &[("a/../b", vec![])])),
        "SOURCE_PATH_REFUSED"
    );
    let first = scratch();
    opened(&first);
    assert_eq!(code_of(bench(&first).open(&files, &[])), "OUTPUT_CONFLICT");
    assert_eq!(
        code_of(bench(&first).keep("late.json", b"x")),
        "OUTPUT_CONFLICT"
    );
    assert!(!first.join("run/late.json").exists());
}

#[test]
fn keeping_a_record_makes_the_run_folder_when_capture_never_opened_it() {
    let folder = scratch();
    let mut bench = bench(&folder);
    bench.keep("record.json", b"refused run").unwrap();
    bench.keep("second.json", b"same run").unwrap();
    assert_eq!(
        fs::read(folder.join("run/record.json")).unwrap(),
        b"refused run"
    );
    assert_eq!(
        fs::read(folder.join("run/second.json")).unwrap(),
        b"same run"
    );
    assert!(!folder.join("run").join(WORKSPACE).exists());
}

#[test]
fn a_check_runs_in_the_working_copy_and_reports_its_exit_code() {
    let folder = scratch();
    let mut bench = opened(&folder);
    let wrong = bench
        .run(&check(&[HOST, "judge", "answer.json"], 20))
        .unwrap();
    assert_eq!(wrong.code, 1);
    assert!(wrong.stdout.head.contains("\"status\":\"FAIL\""));
    bench
        .write("answer.json", ANSWER.replace('5', "6").as_bytes())
        .unwrap();
    assert_eq!(
        bench
            .run(&check(&[HOST, "judge", "answer.json"], 20))
            .unwrap()
            .code,
        0
    );
    let usage = bench.run(&check(&[HOST, "no-such-command"], 20)).unwrap();
    assert_eq!((usage.code, usage.stdout.head.as_str()), (2, ""));
    assert!(usage.stderr.head.starts_with("pfp_operad: usage:"));
    assert_eq!(usage.stderr.sha256, hex(usage.stderr.head.as_bytes()));
    assert_eq!(usage.stdout.sha256, hex(b""));
    let outside = bench
        .run(&check(&[HOST, "judge", "control.json"], 20))
        .unwrap();
    assert_eq!(
        outside.code, 2,
        "a file that is only in the source tree is not in the working copy"
    );
}

#[test]
fn a_check_that_cannot_start_is_unavailable() {
    let folder = scratch();
    let mut bench = opened(&folder);
    let absent = bench
        .run(&check(&["pfp-no-such-program-anywhere"], 20))
        .unwrap_err();
    assert_eq!(absent.code, "CHECK_UNAVAILABLE");
    assert!(absent.message.starts_with("probe: "), "{}", absent.message);
    let empty = bench.run(&check(&[], 20)).unwrap_err();
    assert_eq!(
        (empty.code, empty.message.as_str()),
        ("CHECK_UNAVAILABLE", "probe: no program")
    );
    let unopened = self::bench(&scratch())
        .run(&check(&[HOST, "version"], 20))
        .unwrap_err();
    assert_eq!(unopened.code, "CHECK_UNAVAILABLE");
}

#[cfg(unix)]
#[test]
fn a_check_past_its_deadline_is_stopped_and_unavailable() {
    let folder = scratch();
    let mut bench = opened(&folder);
    let started = std::time::Instant::now();
    let late = bench.run(&check(&["sleep", "30"], 1)).unwrap_err();
    let took = started.elapsed();
    assert_eq!(
        (late.code, late.message.as_str()),
        ("CHECK_UNAVAILABLE", "probe: no exit within 1 s")
    );
    assert!(took.as_millis() >= 1000 && took.as_secs() < 10, "{took:?}");
    let quick = std::time::Instant::now();
    assert_eq!(bench.run(&check(&["sleep", "0.3"], 5)).unwrap().code, 0);
    assert!(quick.elapsed().as_millis() >= 300 && quick.elapsed().as_secs() < 4);
    let killed = bench
        .run(&check(&["sh", "-c", "kill -9 $$"], 5))
        .unwrap_err();
    assert_eq!(killed.message, "probe: ended without an exit code");
}

#[cfg(unix)]
#[test]
fn a_check_gets_the_fixed_environment_no_input_and_no_shell() {
    let folder = scratch();
    let mut bench = opened(&folder);
    for name in SCRUBBED {
        std::env::set_var(name, "inherited");
    }
    std::env::set_var("PFP_WORKSHOP_KEPT", "kept");
    let filter = "env | grep -E '^(GIT_|PYTHON|PFP_WORKSHOP_)'";
    let seen = bench.run(&check(&["sh", "-c", filter], 5)).unwrap();
    assert!(!seen.stdout.truncated);
    for name in SCRUBBED {
        std::env::remove_var(name);
    }
    let lines: Vec<&str> = seen.stdout.head.lines().collect();
    for name in SCRUBBED {
        assert!(
            !lines
                .iter()
                .any(|line| line.starts_with(&format!("{name}="))),
            "{name}"
        );
    }
    for pinned in PINNED {
        assert!(lines.contains(&pinned), "{pinned}");
    }
    assert!(lines.contains(&"PFP_WORKSHOP_KEPT=kept"));
    assert_eq!(
        bench.run(&check(&["cat"], 5)).unwrap().stdout.head,
        "",
        "input is closed"
    );
    let literal = bench.run(&check(&["echo", "$HOME;", "*"], 5)).unwrap();
    assert_eq!(literal.stdout.head, "$HOME; *\n");
    let both = bench
        .run(&check(&["sh", "-c", "echo out; echo err >&2; exit 3"], 5))
        .unwrap();
    assert_eq!(
        (
            both.code,
            both.stdout.head.as_str(),
            both.stderr.head.as_str()
        ),
        (3, "out\n", "err\n")
    );
    let cwd = bench.run(&check(&["pwd"], 5)).unwrap();
    assert!(
        cwd.stdout.head.trim_end().ends_with("/run/workspace"),
        "{}",
        cwd.stdout.head
    );
}

#[test]
fn a_stream_is_hashed_whole_and_kept_to_a_bounded_head() {
    let empty = stream(&b""[..]);
    assert_eq!(
        (empty.sha256.as_str(), empty.head.as_str(), empty.truncated),
        (hex(b"").as_str(), "", false)
    );
    let small = stream(&b"hello\n"[..]);
    assert_eq!(
        (small.sha256, small.head.as_str(), small.truncated),
        (hex(b"hello\n"), "hello\n", false)
    );
    let full = vec![b'a'; HEAD];
    let exact = stream(&full[..]);
    assert_eq!(
        (exact.head.len(), exact.truncated, exact.sha256),
        (HEAD, false, hex(&full))
    );
    let mut long = vec![b'a'; HEAD];
    long.push(b'b');
    let over = stream(&long[..]);
    assert_eq!(
        (over.head.len(), over.truncated, over.sha256),
        (HEAD, true, hex(&long))
    );
    assert!(!over.head.contains('b'));
    let big: Vec<u8> = (0..50_000u32)
        .map(|n| b'a' + u8::try_from(n % 26).unwrap())
        .collect();
    let chunks = stream(&big[..]);
    assert_eq!(chunks.sha256, hex(&big));
    assert_eq!(chunks.head.as_bytes(), &big[..HEAD]);
    assert_eq!(stream(&[0xff, b'a'][..]).head, "\u{fffd}a");
    assert_eq!(Exit::default().stdout.sha256, "");
}

/// A reader that hands out at most `step` bytes at a time.
struct Slow<'a> {
    rest: &'a [u8],
    step: usize,
}

impl std::io::Read for Slow<'_> {
    fn read(&mut self, buffer: &mut [u8]) -> std::io::Result<usize> {
        let count = self.step.min(self.rest.len()).min(buffer.len());
        let (now, later) = self.rest.split_at(count);
        buffer[..count].copy_from_slice(now);
        self.rest = later;
        Ok(count)
    }
}

#[test]
fn a_head_is_filled_across_short_reads() {
    let big: Vec<u8> = (0..10_000u32)
        .map(|n| b'a' + u8::try_from(n % 26).unwrap())
        .collect();
    let slow = stream(Slow {
        rest: &big,
        step: 1000,
    });
    assert_eq!(slow.head.as_bytes(), &big[..HEAD]);
    assert_eq!((slow.sha256, slow.truncated), (hex(&big), true));
    let short = stream(Slow {
        rest: &big[..HEAD],
        step: 7,
    });
    assert_eq!((short.head.len(), short.truncated), (HEAD, false));
}

#[test]
fn a_working_copy_that_cannot_be_laid_out_is_refused() {
    let folder = scratch();
    let clash = BTreeMap::from([
        ("a".to_owned(), b"file".to_vec()),
        ("a/b".to_owned(), b"needs a folder named a".to_vec()),
    ]);
    let refused = bench(&folder).open(&clash, &[]).unwrap_err();
    assert_eq!(refused.code, "IO_UNAVAILABLE");
    assert!(refused.message.contains("workspace"), "{}", refused.message);
}

#[cfg(target_os = "linux")]
#[test]
fn a_regular_file_that_cannot_be_read_is_refused_as_a_source() {
    let folder = scratch();
    let mut bench = Workshop::new(Path::new("/proc/self"), &folder.join("run")).unwrap();
    let refused = bench.source("mem").unwrap_err();
    assert_eq!(refused.code, "SOURCE_FILE_REFUSED");
    assert!(refused.message.contains("mem: "), "{}", refused.message);
}

#[cfg(unix)]
#[test]
fn a_check_past_its_deadline_is_no_longer_running() {
    let folder = scratch();
    let mut bench = opened(&folder);
    let script = "echo $$ > pid.txt; exec sleep 30";
    let late = bench.run(&check(&["sh", "-c", script], 1)).unwrap_err();
    assert_eq!(late.message, "probe: no exit within 1 s");
    let pid = fs::read_to_string(folder.join("run").join(WORKSPACE).join("pid.txt")).unwrap();
    let alive = Process::new("kill")
        .args(["-0", pid.trim()])
        .output()
        .unwrap();
    assert!(!alive.status.success(), "process {} still runs", pid.trim());
}

#[cfg(unix)]
#[test]
fn a_check_cannot_read_what_the_host_is_given_on_input() {
    use std::io::Write;
    use std::process::Stdio;
    let folder = scratch();
    let mut body = request(&total("answer.json", 5, 6));
    body["checks"][1] = json!({"check_id": "reads", "argv": ["cat"], "timeout_seconds": 5});
    let path = folder.join("request.json");
    fs::write(&path, body.to_string()).unwrap();
    let mut host = Process::new(HOST)
        .arg("repair")
        .arg(folder.join("source"))
        .arg(folder.join("run"))
        .arg(&path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    host.stdin.take().unwrap().write_all(b"leaked\n").unwrap();
    let output = host.wait_with_output().unwrap();
    let outcome: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(outcome["result"]["outcome"], "REPAIRED");
    assert_eq!(outcome["result"]["baseline"][1]["stdout"]["head"], "");
    assert_eq!(outcome["result"]["baseline"][1]["code"], 0);
}

#[test]
fn a_check_named_pfp_operad_runs_the_host_the_bench_was_given() {
    let folder = scratch();
    let named = ["pfp_operad", "judge", "answer.json"];
    let mut bench = opened(&folder).hosted(Some(Path::new(HOST)));
    let judged = bench.run(&check(&named, 5)).unwrap();
    assert_eq!(judged.code, 1, "the stored total is wrong");
    assert!(
        judged.stdout.head.starts_with("{\"status\":\"FAIL\""),
        "{}",
        judged.stdout.head
    );
    let other = bench
        .run(&check(&["pfp_operad-x", "judge", "answer.json"], 5))
        .unwrap_err();
    assert_eq!(other.code, "CHECK_UNAVAILABLE", "only the exact name");
    let nowhere = folder.join("no-such-host");
    let mut unhosted = bench.hosted(Some(&nowhere));
    assert_eq!(
        unhosted.run(&check(&named, 5)).unwrap_err().code,
        "CHECK_UNAVAILABLE",
        "the name is the given host and nothing else"
    );
    assert_eq!(
        unhosted.run(&check(&[HOST, "version"], 5)).unwrap().code,
        0,
        "any other program is run as named"
    );

    let by_name =
        |id: &str, file: &str| json!({"check_id": id, "argv": ["pfp_operad", "judge", file]});
    let body = with_checks(
        request(&total("answer.json", 5, 6)),
        json!([
            by_name("positive", "answer.json"),
            by_name("control", "control.json")
        ]),
    );
    let run = scratch();
    let outcome = repair_in(
        &body.to_string(),
        &run.join("source"),
        &run.join("run"),
        Some(Path::new(HOST)),
    );
    assert!(matches!(outcome, Outcome::Pass { .. }), "{outcome:?}");
    let written = folder_text(&run.join("run/request.json"));
    assert!(
        written.contains("\"pfp_operad\""),
        "the request keeps the name"
    );
    assert!(!written.contains(HOST), "and no path of this machine");
}

fn with_checks(mut body: Value, checks: Value) -> Value {
    body["checks"] = checks;
    body
}

fn folder_text(path: &Path) -> String {
    fs::read_to_string(path).unwrap()
}

fn cli(args: &[&str]) -> (i32, Value) {
    let output = Process::new(HOST)
        .args(args)
        .env("PATH", "")
        .output()
        .unwrap();
    (
        output.status.code().unwrap(),
        serde_json::from_slice(&output.stdout).unwrap_or(Value::Null),
    )
}

#[test]
fn the_binary_runs_a_repair_and_exits_by_outcome() {
    let folder = scratch();
    let write = |name: &str, body: &Value| {
        let path = folder.join(name);
        fs::write(&path, body.to_string()).unwrap();
        path.to_str().unwrap().to_owned()
    };
    let source = folder.join("source").to_str().unwrap().to_owned();
    let run = |name: &str| folder.join(name).to_str().unwrap().to_owned();
    let good = write("good.json", &request(&total("answer.json", 5, 6)));
    let (code, outcome) = cli(&["repair", &source, &run("run-good"), &good]);
    assert_eq!(
        (code, &outcome["status"], &outcome["result"]["outcome"]),
        (0, &json!("PASS"), &json!("REPAIRED"))
    );
    assert!(folder.join("run-good/record.json").is_file());

    let named = with_checks(
        request(&total("answer.json", 5, 6)),
        json!([{"check_id": "positive", "argv": ["pfp_operad", "judge", "answer.json"]}]),
    );
    let named = write("named.json", &named);
    let (code, outcome) = cli(&["repair", &source, &run("run-named"), &named]);
    assert_eq!(
        (code, &outcome["result"]["outcome"]),
        (0, &json!("REPAIRED")),
        "the binary is the host its checks name, with no search path"
    );

    let weak = write("weak.json", &request(&total("answer.json", 5, 7)));
    let (code, outcome) = cli(&["repair", &source, &run("run-weak"), &weak]);
    assert_eq!(
        (code, &outcome["status"], &outcome["result"]["outcome"]),
        (1, &json!("FAIL"), &json!("INEFFECTIVE"))
    );

    let (code, outcome) = cli(&["repair", &run("no-source"), &run("run-none"), &good]);
    assert_eq!(
        (code, &outcome["status"], &outcome["refusal"]["code"]),
        (1, &json!("REFUSED"), &json!("SOURCE_ROOT_REFUSED"))
    );
    assert!(!folder.join("run-none").exists());

    assert_eq!(
        cli(&["repair", &source, &run("run-x"), &run("no-request.json")]).0,
        2
    );
    assert_eq!(cli(&["repair", &source, &good]).0, 2);
    assert_eq!(
        cli(&["repair", &source, &run("run-y"), &good, "extra"]).0,
        2
    );
    assert_eq!(
        cli(&["repair", &good, &source, &run("run-z")]).0,
        2,
        "the request comes last"
    );
    assert!(!folder.join("run-z").exists());
    assert!(!folder.join("run-x").exists() && !folder.join("run-y").exists());
    assert_eq!(
        fs::read_to_string(folder.join("source/answer.json")).unwrap(),
        ANSWER
    );
}
