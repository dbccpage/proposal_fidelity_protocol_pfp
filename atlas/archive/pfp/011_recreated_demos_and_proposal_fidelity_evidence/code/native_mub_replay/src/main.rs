//! Matolcsi-Weiner Conjecture 2 verifier binary.
//!
//! Verifies the algebraic identity from arXiv:2503.14752 on the catalog of known
//! MUB-triples in core_mub, using exact Cyc24 arithmetic.
//!
//! The chain: Conj2 + Conj3 ⟹ Zauner's conjecture (MUB(6) = 3).
//!
//! Usage:
//!   cargo run --bin mub6_conj2_verifier
//!
//! AuthorityEffect: None
//! Firewall: NOT MUB(6)=3, NOT MUB(6)<=3; stated region only; mints no authority

use core_mub::core_native::d6_exact_curvature_cochain::{canonical_triple_exact, inner};
use core_mub::core_native::mub6_dita_seed_cover::{
    all_genuine_dita_seeds, dita_seed_triple_columns_qa,
};
use core_mub::core_native::mub6_matolcsi_weiner_conj2::{
    verify_conjecture2_single, Conj2SingleResult,
};
use core_number_theory::cyclotomic::Cyc24;

use serde::Serialize;
use sha2::{Digest, Sha256};

const FIREWALL: &str = "NOT MUB(6)=3, NOT MUB(6)<=3; stated region only; mints no authority";
const DIGEST_CONTRACT: &str =
    "sha256(UTF-8 serde_json::to_vec(ReportPayload)); lowercase hex; sha256 field excluded";

type ExactVec = [Cyc24; 6];

/// Compute the CHM transition H = sqrt(6) * <U1_j, U2_k>.
fn transition_matrix(basis1_cols: &[ExactVec], basis2_cols: &[ExactVec]) -> [[Cyc24; 6]; 6] {
    let sqrt_six = Cyc24::sqrt2().mul(&Cyc24::sqrt3());
    std::array::from_fn(|row| {
        std::array::from_fn(|col| {
            let ip = inner(&basis1_cols[row], &basis2_cols[col]);
            sqrt_six.mul(&ip)
        })
    })
}

fn extract_bases(all_cols: &[[Cyc24; 6]]) -> (Vec<ExactVec>, Vec<ExactVec>, Vec<ExactVec>) {
    let b1: Vec<ExactVec> = all_cols[0..6].to_vec();
    let b2: Vec<ExactVec> = all_cols[6..12].to_vec();
    let b3: Vec<ExactVec> = all_cols[12..18].to_vec();
    (b1, b2, b3)
}

/// Verify Conjecture 2 on a single MUB-triple, returning per-matrix results.
fn verify_triple(triple_id: &str, all_cols: &[ExactVec]) -> TripleResult {
    let (b1, b2, b3) = extract_bases(all_cols);

    let h12 = transition_matrix(&b1, &b2);
    let h23 = transition_matrix(&b2, &b3);
    let h31 = transition_matrix(&b3, &b1);

    let r12 = verify_conjecture2_single(&format!("{triple_id}_H12"), &h12);
    let r23 = verify_conjecture2_single(&format!("{triple_id}_H23"), &h23);
    let r31 = verify_conjecture2_single(&format!("{triple_id}_H31"), &h31);

    let all_hold = r12.conjecture_2_holds && r23.conjecture_2_holds && r31.conjecture_2_holds;

    TripleResult {
        triple_id: triple_id.to_string(),
        h12: r12,
        h23: r23,
        h31: r31,
        all_hold,
    }
}

#[derive(Serialize)]
struct TripleResult {
    triple_id: String,
    h12: Conj2SingleResult,
    h23: Conj2SingleResult,
    h31: Conj2SingleResult,
    all_hold: bool,
}

#[derive(Serialize)]
struct ReportPayload {
    schema: String,
    firewall: String,
    authority_effect: String,
    digest_contract: String,
    total_triples_tested: usize,
    total_triples_passed: usize,
    total_triples_failed: usize,
    results: Vec<TripleResult>,
}

#[derive(Serialize)]
struct FullReport {
    #[serde(flatten)]
    payload: ReportPayload,
    sha256: String,
}

fn payload_sha256(payload: &ReportPayload) -> String {
    let bytes = serde_json::to_vec(payload).expect("ReportPayload must serialize");
    format!("{:x}", Sha256::digest(bytes))
}

fn finalize_report(payload: ReportPayload) -> FullReport {
    let sha256 = payload_sha256(&payload);
    FullReport { payload, sha256 }
}

fn report_digest_is_valid(report: &FullReport) -> bool {
    report.sha256 == payload_sha256(&report.payload)
}

fn render_report(report: &FullReport) -> String {
    let mut rendered = serde_json::to_string_pretty(report).expect("FullReport must serialize");
    rendered.push('\n');
    rendered
}

fn main() {
    println!("╔══════════════════════════════════════════════════════════════════╗");
    println!("║  Matolcsi-Weiner Conjecture 2 Verifier (arXiv:2503.14752)      ║");
    println!("╠══════════════════════════════════════════════════════════════════╣");
    println!("║  Firewall: {FIREWALL}");
    println!("╚══════════════════════════════════════════════════════════════════╝");
    println!();

    let mut results = Vec::new();

    // --- Triple 1: Canonical product triple T0 ---
    println!("[1/7] Canonical triple T0 = {{I, X2⊗Q0, Y2⊗Q1}}");
    let t0_cols = canonical_triple_exact();
    assert_eq!(t0_cols.len(), 18);
    let r = verify_triple("T0_canonical", &t0_cols);
    println!(
        "  H12: γ₁={} γ₂={} | H23: γ₁={} γ₂={} | H31: γ₁={} γ₂={} → {}",
        r.h12.gamma1_failures,
        r.h12.gamma2_failures,
        r.h23.gamma1_failures,
        r.h23.gamma2_failures,
        r.h31.gamma1_failures,
        r.h31.gamma2_failures,
        if r.all_hold { "✅ HOLDS" } else { "❌ FAILS" }
    );
    results.push(r);

    // --- Triples 2-7: All 6 genuine Diță seeds ---
    let seeds = all_genuine_dita_seeds();
    for (i, &(dx, dy, qa)) in seeds.iter().enumerate() {
        println!("[{}/7] Diță seed F6({dx},{dy}) + Y2⊗Q{qa}", i + 2);
        let cols = dita_seed_triple_columns_qa(dx, dy, qa);
        assert_eq!(cols.len(), 18);
        let r = verify_triple(&format!("Dita_F6_{dx}_{dy}_Y2Q{qa}"), &cols);
        println!(
            "  H12: γ₁={} γ₂={} | H23: γ₁={} γ₂={} | H31: γ₁={} γ₂={} → {}",
            r.h12.gamma1_failures,
            r.h12.gamma2_failures,
            r.h23.gamma1_failures,
            r.h23.gamma2_failures,
            r.h31.gamma1_failures,
            r.h31.gamma2_failures,
            if r.all_hold { "✅ HOLDS" } else { "❌ FAILS" }
        );
        results.push(r);
    }

    let total = results.len();
    let passed = results.iter().filter(|r| r.all_hold).count();
    let failed = total - passed;

    println!();
    println!("╔══════════════════════════════════════════════════════════════════╗");
    println!("║  SUMMARY: {passed}/{total} triples satisfy Conjecture 2");
    if failed == 0 {
        println!("║  ✅ All tested MUB-triples satisfy the algebraic identity       ║");
    } else {
        println!("║  ❌ {failed} triple(s) FAIL the identity                         ║");
    }
    println!("║                                                                  ║");
    println!("║  What this supports:                                             ║");
    println!("║    The Matolcsi-Weiner identity is consistent with {total} exact     ║");
    println!("║    MUB-triples over Q(zeta_24) from the core_mub catalog.       ║");
    println!("║  What this does NOT support:                                     ║");
    println!("║    This is finite-sample verification, not a proof of Conj. 2.   ║");
    println!("║  Narrowest defensible claim:                                     ║");
    println!("║    Conj. 2 holds on all {total} tested triples in the catalog.       ║");
    println!("║  Next test needed:                                               ║");
    println!("║    Verify on generic points of the Szöllősi curve B6(theta).     ║");
    println!("╚══════════════════════════════════════════════════════════════════╝");

    let payload = ReportPayload {
        schema: "core.mub6.conj2-verification.v3".to_string(),
        firewall: FIREWALL.to_string(),
        authority_effect: "None".to_string(),
        digest_contract: DIGEST_CONTRACT.to_string(),
        total_triples_tested: total,
        total_triples_passed: passed,
        total_triples_failed: failed,
        results,
    };
    let report = finalize_report(payload);
    assert!(report_digest_is_valid(&report));
    let final_json = render_report(&report);

    let out_dir = std::path::PathBuf::from(std::env::args().nth(1).expect("Paper 011 requires an explicit output directory"));
    std::fs::create_dir_all(&out_dir).expect("artifact directory must be creatable");
    let out_path = out_dir.join("mub6_conj2_verification.json");
    std::fs::write(&out_path, final_json.as_bytes()).expect("artifact report must be writable");
    println!("\nReport written to: {}", out_path.display());
    println!("Payload SHA-256: {}", report.sha256);
}

#[cfg(test)]
mod tests {
    use super::*;

    fn empty_payload() -> ReportPayload {
        ReportPayload {
            schema: "core.mub6.conj2-verification.test".to_string(),
            firewall: FIREWALL.to_string(),
            authority_effect: "None".to_string(),
            digest_contract: DIGEST_CONTRACT.to_string(),
            total_triples_tested: 0,
            total_triples_passed: 0,
            total_triples_failed: 0,
            results: Vec::new(),
        }
    }

    #[test]
    fn payload_digest_excludes_only_the_digest_field_and_detects_tampering() {
        let mut report = finalize_report(empty_payload());
        assert!(report_digest_is_valid(&report));

        report.payload.total_triples_tested = 1;
        assert!(!report_digest_is_valid(&report));
    }

    #[test]
    fn rendered_artifact_has_final_newline() {
        let report = finalize_report(empty_payload());
        assert!(render_report(&report).ends_with('\n'));
    }
}
