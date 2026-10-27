//! `pfp skills`, `pfp licence` and `pfp export --mcp` over a small catalogue,
//! through the library and the binary.
//!
//! AuthorityEffect: None.

use pfp_cli::skills::{licence, mcp_tools, parse_catalog, render_summary, Licence};
use std::path::Path;
use std::process::{Command, Output};

const CATALOG: &str = concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/tests/corpus/catalog/capability_catalog.json"
);

fn catalog() -> pfp_cli::skills::Catalog {
    parse_catalog(&std::fs::read(CATALOG).expect("fixture")).expect("valid catalogue")
}

fn pfp(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_pfp"))
        .args(args)
        .current_dir(Path::new(env!("CARGO_MANIFEST_DIR")))
        .env("NO_COLOR", "1")
        .output()
        .expect("the pfp binary runs")
}

fn stdout(o: &Output) -> String {
    String::from_utf8_lossy(&o.stdout).into_owned()
}

#[test]
fn summary_counts_bound_skills_and_residuals() {
    let text = render_summary(&catalog());
    assert!(text.starts_with("3 skills: 2 bound to an executor, 1 unbound.\n"));
    assert!(text.contains("Residual effect: 2 neutral, 1 unknown.\n"));
    assert!(text.contains("2 agents.\n"));
    assert!(text.contains("unwrap-hunter"));
    assert!(!text.contains("proof-writer"));
}

#[test]
fn licence_follows_the_catalogue() {
    let c = catalog();
    assert_eq!(licence(&c, "rust-dev", "unwrap-hunter"), Licence::Licensed);
    assert_eq!(
        licence(&c, "rust-dev", "hype-lint"),
        Licence::NotLicensed {
            outside: vec!["Paper".to_owned()]
        }
    );
    assert_eq!(
        licence(&c, "paper-builder", "proof-writer"),
        Licence::NotLicensed {
            outside: vec!["Proof".to_owned()]
        }
    );
    assert_eq!(licence(&c, "nobody", "hype-lint"), Licence::UnknownAgent);
    assert_eq!(licence(&c, "rust-dev", "nothing"), Licence::UnknownSkill);
}

#[test]
fn mcp_export_lists_only_bound_skills() {
    let tools = mcp_tools(&catalog());
    let names: Vec<&str> = tools["tools"]
        .as_array()
        .expect("tools")
        .iter()
        .map(|t| t["name"].as_str().expect("name"))
        .collect();
    assert_eq!(names, ["hype-lint", "unwrap-hunter"]);
    let hype = &tools["tools"][0];
    assert_eq!(hype["inputSchema"]["required"][0], "paper_1");
    assert_eq!(hype["inputSchema"]["additionalProperties"], false);
    assert_eq!(hype["annotations"]["readOnlyHint"], true);
    assert_eq!(hype["_meta"]["operad"]["target_colour"], "Audit");
}

#[test]
fn another_schema_is_refused() {
    let err = parse_catalog(br#"{"schema_version":"other","skills":[],"agents":[]}"#)
        .expect_err("refused");
    assert!(err.contains("expected \"core.oewas.capability_catalog.v1\""));
    assert!(parse_catalog(b"[]").is_err());
}

#[test]
fn cli_skills_and_json() {
    let o = pfp(&["skills", "--catalog", CATALOG]);
    assert_eq!(o.status.code(), Some(0));
    assert!(stdout(&o).contains("2 bound"));
    let o = pfp(&["skills", "--catalog", CATALOG, "--json"]);
    let v: serde_json::Value = serde_json::from_str(&stdout(&o)).expect("json");
    assert_eq!(v["unbound"], 1);
    assert_eq!(v["authority_effect"], "None");
}

#[test]
fn cli_licence_exit_codes() {
    assert_eq!(
        pfp(&["licence", "rust-dev", "unwrap-hunter", "--catalog", CATALOG])
            .status
            .code(),
        Some(0)
    );
    let refused = pfp(&["license", "rust-dev", "hype-lint", "--catalog", CATALOG]);
    assert_eq!(refused.status.code(), Some(1));
    assert!(stdout(&refused).contains("UNLICENSED_SKILL"));
    assert_eq!(
        pfp(&["licence", "ghost", "hype-lint", "--catalog", CATALOG])
            .status
            .code(),
        Some(2)
    );
}

#[test]
fn cli_needs_a_catalogue_and_the_mcp_flag() {
    assert_eq!(pfp(&["skills"]).status.code(), Some(2));
    assert_eq!(
        pfp(&["export", "--catalog", CATALOG]).status.code(),
        Some(2)
    );
    let o = pfp(&["export", "--mcp", "--catalog", CATALOG]);
    assert_eq!(o.status.code(), Some(0));
    let v: serde_json::Value = serde_json::from_str(&stdout(&o)).expect("json");
    assert_eq!(v["tools"].as_array().map(Vec::len), Some(2));
}

#[test]
fn unlicensed_skill_is_explained() {
    let o = pfp(&["explain", "unlicensed-skill"]);
    assert_eq!(o.status.code(), Some(0));
    assert!(stdout(&o).contains("Operads-Skills-and-Catalog"));
}
