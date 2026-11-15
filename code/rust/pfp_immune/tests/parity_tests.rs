//! Parity and Integration Tests for `pfp_immune` Host Binary.
//!
//! Exercises CLI entry point across all 5 subcommands:
//! - `screen`: Negative selection filtering and status codes
//! - `decide`: Two-signal disposition check and exact rational evaluation
//! - `taint`: Lineage graph causal taint propagation and cycle refusal
//! - `select`: Largest-remainder 60/30/10 population reserve partition
//! - `exclusion`: Multi-family consensus classification and falsifier ordering
//!
//! AuthorityEffect: None.

use serde_json::{json, Value};
use std::io::Write;
use std::process::{Command, Stdio};

fn run_cli(subcommand: &str, input_json: &Value) -> (i32, String, String) {
    let mut child = Command::new(env!("CARGO_BIN_EXE_pfp_immune"))
        .arg(subcommand)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("failed to spawn pfp_immune binary");

    let stdin_payload = serde_json::to_string(input_json).expect("failed to serialize payload");
    if let Some(mut stdin) = child.stdin.take() {
        stdin
            .write_all(stdin_payload.as_bytes())
            .expect("failed to write to stdin");
    }

    let output = child
        .wait_with_output()
        .expect("failed to wait on pfp_immune child process");
    let exit_code = output.status.code().unwrap_or(-1);
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    (exit_code, stdout, stderr)
}

fn run_cli_args(args: &[&str], stdin_payload: Option<&str>) -> (i32, String, String) {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_pfp_immune"));
    for arg in args {
        cmd.arg(arg);
    }
    cmd.stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = cmd.spawn().expect("failed to spawn pfp_immune binary");
    if let Some(payload) = stdin_payload {
        if let Some(mut stdin) = child.stdin.take() {
            stdin
                .write_all(payload.as_bytes())
                .expect("failed to write to stdin");
        }
    }

    let output = child
        .wait_with_output()
        .expect("failed to wait on pfp_immune child process");
    let exit_code = output.status.code().unwrap_or(-1);
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    (exit_code, stdout, stderr)
}

// ---------------------------------------------------------------------------
// Subcommand 1: screen
// ---------------------------------------------------------------------------

#[test]
fn test_screen_autoimmune_purged() {
    let input = json!({
        "self_panel": [
            "clean_alpha",
            "clean_beta",
            "exact rational gap"
        ],
        "candidates": [
            {
                "rule_id": "rule_defect",
                "pattern": "defect",
                "capability_kind": "Detector"
            },
            {
                "rule_id": "rule_exact_rational",
                "pattern": "exact rational",
                "capability_kind": "Detector"
            },
            {
                "rule_id": "rule_clean_prefix",
                "pattern": "^clean",
                "capability_kind": "Detector"
            },
            {
                "rule_id": "rule_absent",
                "pattern": "^absent$",
                "capability_kind": "Detector"
            }
        ]
    });

    let (exit_code, stdout, _) = run_cli("screen", &input);
    assert_eq!(exit_code, 1, "purged candidates must exit 1");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "FAIL");
    assert_eq!(parsed["admitted"], json!(["rule_defect", "rule_absent"]));

    let purged = parsed["purged"].as_array().expect("purged array");
    assert_eq!(purged.len(), 2);
    assert_eq!(purged[0]["rule_id"], "rule_exact_rational");
    assert_eq!(
        purged[0]["reason"],
        "SELF_REACTIVE: matched self sample 'exact rational gap'"
    );
    assert_eq!(purged[1]["rule_id"], "rule_clean_prefix");
    assert_eq!(
        purged[1]["reason"],
        "SELF_REACTIVE: matched self sample 'clean_alpha'"
    );
}

#[test]
fn test_screen_all_admitted() {
    let input = json!({
        "self_panel": [
            "clean_alpha",
            "clean_beta"
        ],
        "candidates": [
            {
                "rule_id": "rule_defect",
                "pattern": "defect",
                "capability_kind": "Detector"
            },
            {
                "rule_id": "rule_fraud",
                "pattern": "fraud",
                "capability_kind": "Detector"
            }
        ]
    });

    let (exit_code, stdout, _) = run_cli("screen", &input);
    assert_eq!(exit_code, 0, "all admitted must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "PASS");
    assert_eq!(parsed["admitted"], json!(["rule_defect", "rule_fraud"]));
    assert_eq!(parsed["purged"], json!([]));
}

#[test]
fn test_screen_invalid_pattern() {
    let input = json!({
        "self_panel": ["clean_sample"],
        "candidates": [
            {
                "rule_id": "bad_regex",
                "pattern": "(unclosed parenthesis",
                "capability_kind": "Detector"
            }
        ]
    });

    let (exit_code, stdout, _) = run_cli("screen", &input);
    assert_eq!(exit_code, 1, "invalid pattern must exit 1");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "FAIL");
    assert_eq!(parsed["admitted"], json!([]));
    assert_eq!(
        parsed["purged"],
        json!([
            {
                "rule_id": "bad_regex",
                "reason": "INVALID_PATTERN: regex compilation error"
            }
        ])
    );
}

// ---------------------------------------------------------------------------
// Subcommand 2: decide
// ---------------------------------------------------------------------------

#[test]
fn test_decide_pass() {
    let input = json!({
        "signal1_matches": [],
        "danger_score": {"num": 0, "den": 1},
        "threshold": {"num": 1, "den": 2}
    });

    let (exit_code, stdout, _) = run_cli("decide", &input);
    assert_eq!(exit_code, 0, "clean signals must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "PASS");
    assert_eq!(parsed["disposition"], "no rule match and no host danger");
}

#[test]
fn test_decide_diagnostic() {
    let input = json!({
        "signal1_matches": ["match.float_call.1"],
        "danger_score": {"num": 1, "den": 4},
        "threshold": {"num": 1, "den": 2}
    });

    let (exit_code, stdout, _) = run_cli("decide", &input);
    assert_eq!(exit_code, 1, "diagnostic must exit 1");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "DIAGNOSTIC_OR_NORMALIZE");
    assert_eq!(
        parsed["disposition"],
        "rule match without host danger: diagnostic only"
    );
}

#[test]
fn test_decide_host_refusal() {
    let input = json!({
        "signal1_matches": [],
        "danger_score": {"num": 3, "den": 4},
        "threshold": {"num": 1, "den": 2}
    });

    let (exit_code, stdout, _) = run_cli("decide", &input);
    assert_eq!(exit_code, 1, "host refusal must exit 1");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "HOLD_OR_REPAIR");
    assert_eq!(
        parsed["disposition"],
        "host danger score 3/4 exceeds threshold 1/2"
    );
}

#[test]
fn test_decide_activation() {
    let input = json!({
        "signal1_matches": ["match.float_call.1"],
        "danger_score": {"num": 1, "den": 1},
        "threshold": {"num": 1, "den": 2}
    });

    let (exit_code, stdout, _) = run_cli("decide", &input);
    assert_eq!(exit_code, 1, "two-signal activation must exit 1");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "HOLD_OR_REPAIR");
    assert_eq!(
        parsed["disposition"],
        "two-signal activation: rule match and host danger score 1/1 exceeds threshold 1/2"
    );
}

#[test]
fn test_decide_boundary_equality() {
    let input = json!({
        "signal1_matches": [],
        "danger_score": {"num": 1, "den": 2},
        "threshold": {"num": 1, "den": 2}
    });

    let (exit_code, stdout, _) = run_cli("decide", &input);
    assert_eq!(exit_code, 0, "danger == threshold must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "PASS");
    assert_eq!(parsed["disposition"], "no rule match and no host danger");
}

// ---------------------------------------------------------------------------
// Subcommand 3: taint
// ---------------------------------------------------------------------------

#[test]
fn test_taint_propagation_cascade() {
    let input = json!({
        "edges": [
            {
                "parent": "p0",
                "child": "p1",
                "witness": "sha256:0000000000000000000000000000000000000000000000000000000000000001"
            },
            {
                "parent": "p1",
                "child": "p2",
                "witness": "sha256:0000000000000000000000000000000000000000000000000000000000000002"
            },
            {
                "parent": "p_unrelated",
                "child": "p_clean",
                "witness": "sha256:0000000000000000000000000000000000000000000000000000000000000003"
            }
        ],
        "revoked_parents": ["p0"]
    });

    let (exit_code, stdout, _) = run_cli("taint", &input);
    assert_eq!(exit_code, 0, "valid taint computation must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["tainted_nodes"], json!(["p0", "p1", "p2"]));
}

#[test]
fn test_taint_cycle_detected() {
    let input = json!({
        "edges": [
            {
                "parent": "x",
                "child": "y",
                "witness": "sha256:0000000000000000000000000000000000000000000000000000000000000001"
            },
            {
                "parent": "y",
                "child": "x",
                "witness": "sha256:0000000000000000000000000000000000000000000000000000000000000002"
            }
        ],
        "revoked_parents": ["x"]
    });

    let (exit_code, stdout, _) = run_cli("taint", &input);
    assert_eq!(exit_code, 1, "cycle refusal must exit 1");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "REFUSED");
    assert_eq!(
        parsed["reason"],
        "LINEAGE_CYCLE_REFUSED: Cycle detected in inheritance DAG"
    );
}

// ---------------------------------------------------------------------------
// Subcommand 4: select
// ---------------------------------------------------------------------------

#[test]
fn test_select_population_10() {
    let input = json!({
        "population": [
            {"id": "c01", "fitness": {"num": 99, "den": 100}, "lineage_depth": 3},
            {"id": "c02", "fitness": {"num": 95, "den": 100}, "lineage_depth": 2},
            {"id": "c03", "fitness": {"num": 90, "den": 100}, "lineage_depth": 4},
            {"id": "c04", "fitness": {"num": 85, "den": 100}, "lineage_depth": 1},
            {"id": "c05", "fitness": {"num": 80, "den": 100}, "lineage_depth": 5},
            {"id": "c06", "fitness": {"num": 75, "den": 100}, "lineage_depth": 3},
            {"id": "c07", "fitness": {"num": 70, "den": 100}, "lineage_depth": 2},
            {"id": "c08", "fitness": {"num": 65, "den": 100}, "lineage_depth": 1},
            {"id": "c09", "fitness": {"num": 60, "den": 100}, "lineage_depth": 0},
            {"id": "c10", "fitness": {"num": 50, "den": 100}, "lineage_depth": 0}
        ]
    });

    let (exit_code, stdout, _) = run_cli("select", &input);
    assert_eq!(exit_code, 0, "select partition must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(
        parsed["core_60"],
        json!(["c01", "c02", "c03", "c04", "c05", "c06"])
    );
    assert_eq!(parsed["exploratory_30"], json!(["c07", "c08", "c09"]));
    assert_eq!(parsed["novel_10"], json!(["c10"]));
}

#[test]
fn test_select_population_empty() {
    let input = json!({
        "population": []
    });

    let (exit_code, stdout, _) = run_cli("select", &input);
    assert_eq!(exit_code, 0, "empty population must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["core_60"], json!([]));
    assert_eq!(parsed["exploratory_30"], json!([]));
    assert_eq!(parsed["novel_10"], json!([]));
}

// ---------------------------------------------------------------------------
// Subcommand 5: exclusion
// ---------------------------------------------------------------------------

#[test]
fn test_exclusion_probably_dead() {
    let input = json!({
        "family_votes": {
            "claude_family": "EXCLUDE",
            "gpt_family": "EXCLUDE"
        },
        "hypotheses": ["hyp_branch_b1", "hyp_branch_b2"]
    });

    let (exit_code, stdout, _) = run_cli("exclusion", &input);
    assert_eq!(exit_code, 0, "exclusion classification must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["consensus"], "PROBABLY_DEAD");
    assert_eq!(
        parsed["falsifiers"],
        json!([
            {"id": "hyp_branch_b1", "cost": 1},
            {"id": "hyp_branch_b2", "cost": 1}
        ])
    );
}

#[test]
fn test_exclusion_frontier_disagreement() {
    let input = json!({
        "family_votes": {
            "claude_family": "EXCLUDE",
            "gpt_family": "INCLUDE"
        },
        "hypotheses": ["hyp_contested"]
    });

    let (exit_code, stdout, _) = run_cli("exclusion", &input);
    assert_eq!(exit_code, 0, "frontier disagreement must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["consensus"], "FRONTIER");
    assert_eq!(
        parsed["falsifiers"],
        json!([
            {"id": "hyp_contested", "cost": 1}
        ])
    );
}

#[test]
fn test_exclusion_uncorroborated() {
    let input = json!({
        "family_votes": {
            "claude_family": "EXCLUDE"
        },
        "hypotheses": ["hyp_lone"]
    });

    let (exit_code, stdout, _) = run_cli("exclusion", &input);
    assert_eq!(exit_code, 0, "uncorroborated must exit 0");

    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["consensus"], "UNCORROBORATED");
    assert_eq!(
        parsed["falsifiers"],
        json!([
            {"id": "hyp_lone", "cost": 1}
        ])
    );
}

// ---------------------------------------------------------------------------
// Usage and Error Tests (Exit Code 2)
// ---------------------------------------------------------------------------

#[test]
fn test_help_flag_exits_two() {
    let (exit_code, _, stderr) = run_cli_args(&["--help"], None);
    assert_eq!(exit_code, 2);
    assert!(stderr.contains("usage: pfp_immune"));
}

#[test]
fn test_help_short_flag_exits_two() {
    let (exit_code, _, stderr) = run_cli_args(&["-h"], None);
    assert_eq!(exit_code, 2);
    assert!(stderr.contains("usage: pfp_immune"));
}

#[test]
fn test_usage_no_args_exits_two() {
    let (exit_code, _, stderr) = run_cli_args(&[], None);
    assert_eq!(exit_code, 2);
    assert!(stderr.contains("usage: pfp_immune"));
}

#[test]
fn test_unknown_subcommand_exits_two() {
    let (exit_code, _, stderr) = run_cli_args(&["unknown_cmd"], Some("{}"));
    assert_eq!(exit_code, 2);
    assert!(stderr.contains("unknown subcommand: 'unknown_cmd'"));
    assert!(stderr.contains("usage: pfp_immune"));
}

#[test]
fn test_malformed_json_exits_two() {
    let (exit_code, _, stderr) = run_cli_args(&["screen"], Some("{bad json"));
    assert_eq!(exit_code, 2);
    assert!(stderr.contains("invalid screen input"));
}

#[test]
fn test_file_input_flag() {
    let temp_file = std::env::temp_dir().join("test_pfp_immune_input.json");
    let input = json!({
        "signal1_matches": [],
        "danger_score": {"num": 0, "den": 1},
        "threshold": {"num": 1, "den": 2}
    });
    std::fs::write(&temp_file, input.to_string()).expect("failed to write temp file");

    let temp_path = temp_file.to_str().expect("valid temp path");
    let (exit_code, stdout, _) = run_cli_args(&["decide", "--input", temp_path], None);
    let _ = std::fs::remove_file(&temp_file);

    assert_eq!(exit_code, 0);
    let parsed: Value = serde_json::from_str(stdout.trim()).expect("valid JSON stdout");
    assert_eq!(parsed["status"], "PASS");
}

#[test]
fn test_missing_file_exits_two() {
    let (exit_code, _, stderr) =
        run_cli_args(&["decide", "--input", "non_existent_file.json"], None);
    assert_eq!(exit_code, 2);
    assert!(stderr.contains("cannot read file"));
}

#[test]
fn test_decide_division_by_zero_exits_two() {
    let input = json!({
        "signal1_matches": [],
        "danger_score": {"num": 1, "den": 0},
        "threshold": {"num": 1, "den": 2}
    });
    let (exit_code, _, stderr) = run_cli("decide", &input);
    assert_eq!(exit_code, 2);
    assert!(stderr.contains("division by zero"));
}
