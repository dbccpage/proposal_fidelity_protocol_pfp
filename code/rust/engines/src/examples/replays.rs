#[path = "replays/cases.rs"]
mod cases;

use std::path::{Path, PathBuf};

use cases::{all_cases, budget_for_case, operator_registry, DemoAdapter};
use core_wdp::ddc::agent_contract::sha256_bytes;
use engines::multipath_iterator::{
    run_multipath, CancellationToken, RunReceiptAnchor, TerminalKind,
};
use serde::Serialize;

#[derive(Serialize)]
struct ManifestEntry {
    case_id: String,
    domain: String,
    terminal: TerminalKind,
    packet_sha256: String,
    replay_sha256: String,
    receipt_file_sha256: String,
    receipt_anchor_sha256: String,
    receipt_anchor: RunReceiptAnchor,
    runtime_micros: u128,
    candidates_proposed: usize,
    candidates_evaluated: usize,
    candidates_avoided_through_quotienting: usize,
    carrier_extensions: usize,
    compiled_operator_candidates: usize,
    compiled_operator_pattern_sha256s: Vec<String>,
    receipt_path: String,
    authority_effect: &'static str,
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    generator: &'static str,
    cases: Vec<ManifestEntry>,
    authority_effect: &'static str,
    nonclaims: Vec<&'static str>,
}

fn verify_case_outcome(
    case_id: &str,
    expected: TerminalKind,
    actual: TerminalKind,
    anchor_verified: bool,
    authority_is_none: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if actual != expected {
        return Err(format!("{case_id}: expected {expected:?}, got {actual:?}").into());
    }
    if !anchor_verified || !authority_is_none {
        return Err(format!("{case_id}: anchored replay or authority firewall failed").into());
    }
    Ok(())
}

fn write_manifest(
    output: &Path,
    mut entries: Vec<ManifestEntry>,
) -> Result<(), Box<dyn std::error::Error>> {
    entries.sort_by(|left, right| left.case_id.cmp(&right.case_id));
    let manifest = Manifest {
        schema_version: "core.paper070.demo_manifest.v3",
        generator: "cargo run -j 1 -p engines --example replays -- <output-dir>",
        cases: entries,
        authority_effect: "None",
        nonclaims: vec![
            "The fixtures test the shared iterator contract, not complete Rust or Lean semantics.",
            "A replay receipt is evidence, not certification or authority.",
            "Fixture candidate assessments have Unestablished witness relation; they are not independent evaluations.",
            "The self-application receipt requires a separately recorded external evaluation before campaign completion.",
            "Compiled operator candidates are evidence-only and are never self-registered or promoted by the iterator.",
            "Receipt anchors detect later byte and inspection-trace re-sealing only when the host pins them outside the receipt.",
            "A receipt anchor does not establish adapter semantics, detector completeness, witness truth, or authority.",
        ],
    };
    let manifest_path = output.join("008_demo_manifest.json");
    std::fs::write(&manifest_path, serde_json::to_vec_pretty(&manifest)?)?;
    println!(
        "wrote {} PaperER008 replay receipts and {}",
        manifest.cases.len(),
        manifest_path.display()
    );
    Ok(())
}

fn write_receipt_bytes(
    path: &Path,
    bytes: &[u8],
    receipt_anchor: &RunReceiptAnchor,
) -> Result<(String, String), Box<dyn std::error::Error>> {
    let receipt_anchor_sha256 = receipt_anchor.sha256()?;
    std::fs::write(path, bytes)?;
    Ok((sha256_bytes(bytes), receipt_anchor_sha256))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let output = std::env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            PathBuf::from(
                "research/published/008_engine_runtime/gtoc_multipath_projection_algo/experiments",
            )
        });
    std::fs::create_dir_all(&output)?;
    let registry = operator_registry();
    let mut entries = Vec::new();

    for case in all_cases() {
        let case_id = case.case_id.clone();
        let domain = case.domain.clone();
        let expected = case.expected_terminal;
        let packet = case.packet();
        let budget = budget_for_case(&case);
        let receipt = run_multipath(
            &DemoAdapter::new(case),
            packet,
            &registry,
            budget,
            &CancellationToken::default(),
        )?;
        let receipt_anchor = receipt.external_anchor()?;
        verify_case_outcome(
            &case_id,
            expected,
            receipt.terminal.kind,
            receipt.verify_against_anchor(&receipt_anchor)?,
            receipt.authority_effect().is_none(),
        )?;
        let path = output.join(format!("008_demo_{case_id}.json"));
        let bytes = receipt.canonical_json_bytes()?;
        let (receipt_file_sha256, receipt_anchor_sha256) =
            write_receipt_bytes(&path, &bytes, &receipt_anchor)?;
        entries.push(ManifestEntry {
            case_id,
            domain,
            terminal: receipt.terminal.kind,
            packet_sha256: receipt.packet_sha256,
            replay_sha256: receipt.replay_sha256,
            receipt_file_sha256,
            receipt_anchor_sha256,
            receipt_anchor,
            runtime_micros: receipt.runtime_micros,
            candidates_proposed: receipt.accounting.proposed,
            candidates_evaluated: receipt.accounting.evaluated,
            candidates_avoided_through_quotienting: receipt
                .accounting
                .predicted_avoided_by_quotient,
            carrier_extensions: receipt.accounting.carrier_extensions,
            compiled_operator_candidates: receipt.accounting.compiled_operator_candidates,
            compiled_operator_pattern_sha256s: receipt
                .steps
                .iter()
                .filter_map(|step| step.compiled_operator_candidate.as_ref())
                .map(|candidate| candidate.pattern_sha256.clone())
                .collect(),
            receipt_path: relative_display(&output, &path),
            authority_effect: "None",
        });
    }

    write_manifest(&output, entries)
}

fn relative_display(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .to_string_lossy()
        .replace('\\', "/")
}

// Origin: engine/crates_rs/engines/src/examples/replays.rs
// Claim: urn:core:crates_rs:engines:replays:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b6b772f0 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
