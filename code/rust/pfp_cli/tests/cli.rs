//! End-to-end tests of the `pfp` binary: exit codes, output, and the safety
//! contract (no writes without --out, no overwrite, no reads outside the root).
//!
//! AuthorityEffect: None.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

const CORPUS: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/corpus");

fn pfp(dir: &Path, args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_pfp"))
        .args(args)
        .current_dir(dir)
        .env("NO_COLOR", "1")
        .output()
        .expect("the pfp binary runs")
}

fn stdout(o: &Output) -> String {
    String::from_utf8_lossy(&o.stdout).into_owned()
}

/// A fresh, empty folder for one test.
fn scratch(name: &str) -> PathBuf {
    let dir = PathBuf::from(env!("CARGO_TARGET_TMPDIR")).join(name);
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).expect("scratch dir");
    dir
}

/// Every file under `dir` with its bytes, sorted, to prove nothing changed.
fn snapshot(dir: &Path) -> Vec<(PathBuf, Vec<u8>)> {
    let mut out = Vec::new();
    for entry in fs::read_dir(dir).expect("read dir") {
        let path = entry.expect("entry").path();
        if path.is_dir() {
            out.extend(snapshot(&path));
        } else {
            out.push((path.clone(), fs::read(&path).expect("read")));
        }
    }
    out.sort();
    out
}

#[test]
fn demo_shows_findings_and_exits_zero() {
    let o = pfp(Path::new(CORPUS), &["demo"]);
    assert_eq!(o.status.code(), Some(0));
    let text = stdout(&o);
    for code in [
        "CONCLUSION_PRELOAD",
        "NO_REFUSAL_PATH",
        "SELF_CERTIFICATION",
        "FAKE_RECEIPT",
        "PERSONA_AUTHORITY_LEAK",
        "OPTIMALITY_HALLUCINATION",
        "COMPLEXITY_HALLUCINATION",
        "PRIVATE_COT_DEPENDENCY",
    ] {
        assert!(text.contains(code), "demo output lacks {code}:\n{text}");
    }
    assert!(text.contains("9 findings from 13 detectors. Nothing was changed."));
    assert!(!text.contains('\x1b'), "NO_COLOR must turn colors off");
}

#[test]
fn clean_corpus_has_no_findings() {
    let o = pfp(
        Path::new(CORPUS),
        &[
            "check",
            "--prompt",
            "clean/prompt.md",
            "clean/reply.md",
            "clean/reply.json",
        ],
    );
    assert_eq!(o.status.code(), Some(0), "{}", stdout(&o));
    assert!(
        stdout(&o).contains("No findings from 13 detectors. That is not proof the text is right.")
    );
}

#[test]
fn flagged_text_reports_lines() {
    let o = pfp(Path::new(CORPUS), &["check", "flagged/reply.md"]);
    assert_eq!(o.status.code(), Some(1));
    let text = stdout(&o);
    assert!(
        text.contains("SELF_CERTIFICATION") && text.contains("line 4"),
        "{text}"
    );
    assert!(
        text.contains("OPTIMALITY_HALLUCINATION") && text.contains("line 2"),
        "{text}"
    );
    assert!(text.contains("COMPLEXITY_HALLUCINATION"), "{text}");
    assert!(
        text.contains("THEOREM_NAME_LAUNDERING") && text.contains("line 3"),
        "{text}"
    );
}

#[test]
fn json_report_is_deterministic_and_carries_no_authority() {
    let args = [
        "check",
        "--json",
        "--prompt",
        "clean/prompt.md",
        "flagged/reply.md",
    ];
    let first = stdout(&pfp(Path::new(CORPUS), &args));
    let second = stdout(&pfp(Path::new(CORPUS), &args));
    assert_eq!(first, second);
    let value: serde_json::Value = serde_json::from_str(&first).expect("valid JSON");
    assert_eq!(value["authority_effect"], "None");
    assert_eq!(value["inputs"][0]["shape"], "text");
}

#[test]
fn check_reads_stdin_and_drops_a_bom() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_pfp"))
        .args(["check", "-"])
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .expect("spawn");
    use std::io::Write;
    child
        .stdin
        .take()
        .expect("stdin")
        .write_all("\u{feff}{\"verified\": true}".as_bytes())
        .expect("write");
    let o = child.wait_with_output().expect("wait");
    assert_eq!(o.status.code(), Some(1));
    assert!(
        stdout(&o).contains("/verified"),
        "BOM-prefixed JSON is still read as JSON"
    );
}

#[test]
fn check_never_writes() {
    let dir = scratch("check_never_writes");
    fs::write(dir.join("reply.md"), "This is optimal.\n").expect("write");
    let before = snapshot(&dir);
    pfp(&dir, &["check", "reply.md"]);
    pfp(&dir, &["check", "--json", "reply.md"]);
    pfp(&dir, &["demo"]);
    pfp(&dir, &["explain"]);
    assert_eq!(before, snapshot(&dir));
}

#[test]
fn usage_errors_exit_two() {
    let dir = Path::new(CORPUS);
    for args in [
        vec!["frobnicate"],
        vec!["check"],
        vec!["check", "--jsn", "clean/reply.md"],
        vec!["check", "missing.md"],
        vec!["check", "-", "-"],
        vec!["check", "--prompt"],
        vec!["explain", "NOT_A_CODE"],
        vec!["replay"],
        vec!["seal"],
    ] {
        assert_eq!(pfp(dir, &args).status.code(), Some(2), "args {args:?}");
    }
}

#[test]
fn non_utf8_input_is_refused() {
    let dir = scratch("non_utf8");
    fs::write(dir.join("bad.md"), [0xff, 0xfe, 0x00, 0x41]).expect("write");
    let o = pfp(&dir, &["check", "bad.md"]);
    assert_eq!(o.status.code(), Some(2));
}

#[test]
fn explain_lists_and_details_every_detector() {
    let o = pfp(Path::new(CORPUS), &["explain"]);
    assert_eq!(o.status.code(), Some(0));
    let report = pfp(Path::new(CORPUS), &["check", "--json", "clean/reply.md"]);
    let value: serde_json::Value = serde_json::from_str(&stdout(&report)).expect("json");
    for code in value["detectors_run"].as_array().expect("array") {
        let code = code.as_str().expect("string");
        let detail = pfp(Path::new(CORPUS), &["explain", &code.to_lowercase()]);
        assert_eq!(detail.status.code(), Some(0), "no explain entry for {code}");
        assert!(stdout(&detail).contains("/wiki/"));
    }
}

#[test]
fn seal_prints_by_default_and_writes_only_with_out() {
    let dir = scratch("seal_out");
    fs::write(dir.join("a.md"), "alpha\n").expect("write");
    let before = snapshot(&dir);
    let o = pfp(&dir, &["seal", "a.md"]);
    assert_eq!(o.status.code(), Some(0));
    assert!(stdout(&o).contains("\"format\": \"pfp.packet.v1\""));
    assert_eq!(before, snapshot(&dir), "seal without --out writes nothing");

    assert_eq!(
        pfp(&dir, &["seal", "a.md", "--out", "p.json"])
            .status
            .code(),
        Some(0)
    );
    let sealed = fs::read(dir.join("p.json")).expect("packet written");
    let again = pfp(&dir, &["seal", "a.md", "--out", "p.json"]);
    assert_eq!(again.status.code(), Some(2), "never overwrites");
    assert_eq!(sealed, fs::read(dir.join("p.json")).expect("still there"));
}

#[test]
fn seal_refuses_paths_outside_the_folder() {
    let dir = scratch("seal_paths");
    fs::write(dir.join("a.md"), "alpha\n").expect("write");
    let absolute = dir.join("a.md").display().to_string();
    for bad in ["../a.md", absolute.as_str(), "sub/../a.md"] {
        let o = pfp(&dir, &["seal", bad]);
        assert_eq!(o.status.code(), Some(2), "{bad}");
        assert!(String::from_utf8_lossy(&o.stderr).contains("PATH_OUTSIDE_ROOT"));
    }
    assert_eq!(
        pfp(&dir, &["seal", "a.md", "a.md"]).status.code(),
        Some(2),
        "duplicate"
    );
}

#[test]
fn replay_matches_then_catches_changes() {
    let dir = scratch("replay");
    fs::create_dir_all(dir.join("docs")).expect("mkdir");
    fs::write(dir.join("a.md"), "alpha\n").expect("write");
    fs::write(dir.join("docs/b.md"), "beta\n").expect("write");
    pfp(&dir, &["seal", "a.md", "docs/b.md", "--out", "p.json"]);
    let before = snapshot(&dir);

    let ok = pfp(&dir, &["replay", "p.json"]);
    assert_eq!(ok.status.code(), Some(0));
    assert!(stdout(&ok).contains("2 files match the packet byte for byte."));
    assert_eq!(before, snapshot(&dir), "replay never writes");

    fs::write(dir.join("a.md"), "alpha!\n").expect("edit");
    fs::remove_file(dir.join("docs/b.md")).expect("remove");
    let bad = pfp(&dir, &["replay", "p.json"]);
    assert_eq!(bad.status.code(), Some(1));
    let text = stdout(&bad);
    assert!(
        text.contains("DIGEST_MISMATCH") && text.contains("FILE_MISSING"),
        "{text}"
    );
}

#[test]
fn replay_uses_root() {
    let dir = scratch("replay_root");
    fs::create_dir_all(dir.join("work")).expect("mkdir");
    fs::write(dir.join("work/a.md"), "alpha\n").expect("write");
    pfp(&dir.join("work"), &["seal", "a.md", "--out", "../p.json"]);
    assert_eq!(pfp(&dir, &["replay", "p.json"]).status.code(), Some(1));
    assert_eq!(
        pfp(&dir, &["replay", "p.json", "--root", "work"])
            .status
            .code(),
        Some(0)
    );
}

#[test]
fn replay_refuses_tampered_and_foreign_packets() {
    let dir = scratch("replay_tamper");
    fs::write(dir.join("a.md"), "alpha\n").expect("write");
    pfp(&dir, &["seal", "a.md", "--out", "p.json"]);
    let packet = fs::read_to_string(dir.join("p.json")).expect("read");

    fs::write(
        dir.join("t.json"),
        packet.replace("\"bytes\": 6", "\"bytes\": 7"),
    )
    .expect("write");
    let o = pfp(&dir, &["replay", "t.json"]);
    assert_eq!(o.status.code(), Some(1));
    assert!(stdout(&o).contains("ENVELOPE_TAMPERED"));

    fs::write(dir.join("f.json"), "{\"format\": \"other\"}").expect("write");
    let o = pfp(&dir, &["replay", "f.json"]);
    assert_eq!(o.status.code(), Some(1));
    assert!(stdout(&o).contains("UNSUPPORTED_FORMAT"));
}

#[test]
fn replay_never_reads_outside_root_even_with_valid_hashes() {
    let dir = scratch("replay_escape");
    // A packet whose hashes are self-consistent but whose path climbs out.
    let entry = pfp_cli::packet::Entry {
        path: "../secret".to_owned(),
        bytes: 0,
        sha256: pfp_cli::packet::sha256_hex(b""),
    };
    let mut envelope =
        pfp_cli::packet::seal(&[("x".to_owned(), Vec::new())], "test").expect("seal");
    envelope.files = vec![entry];
    let listing = format!("{}  ../secret\n", pfp_cli::packet::sha256_hex(b""));
    envelope.payload_sha256 = pfp_cli::packet::sha256_hex(listing.as_bytes());
    envelope.envelope_sha256 = String::new();
    envelope.envelope_sha256 =
        pfp_cli::packet::sha256_hex(&serde_json::to_vec(&envelope).expect("json"));
    fs::write(
        dir.join("evil.json"),
        serde_json::to_vec(&envelope).expect("json"),
    )
    .expect("write");
    let o = pfp(&dir, &["replay", "evil.json"]);
    assert_eq!(o.status.code(), Some(1));
    assert!(stdout(&o).contains("PATH_OUTSIDE_ROOT"), "{}", stdout(&o));
}

#[test]
fn version_and_help() {
    let v = pfp(Path::new(CORPUS), &["--version"]);
    assert_eq!(
        stdout(&v),
        format!("pfp-cli {}\n", env!("CARGO_PKG_VERSION"))
    );
    let h = pfp(Path::new(CORPUS), &[]);
    assert_eq!(h.status.code(), Some(0));
    assert!(stdout(&h).contains("Read-only unless you pass --out"));
}
