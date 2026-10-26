//! `verify_po000` — pinned receipt conformance checker for the PO-000 replication receipt.
//!
//! ```text
//! cargo run --release --bin verify_po000            # verify default RECEIPT.txt
//! cargo run --release --bin verify_po000 -- <path>  # verify custom receipt path
//! ```
//!
//! `AuthorityEffect: None.`

use omega_ooutwire_primitives::alpha_projection_obstruction::verify::verify_receipt_text;
use std::path::Path;

fn main() {
    let receipt_path = std::env::args().nth(1).unwrap_or_else(|| {
        let default_path = omega_ooutwire_primitives::alpha_projection_obstruction::receipt_path();
        default_path.to_string_lossy().into_owned()
    });

    let path = Path::new(&receipt_path);
    if !path.exists() {
        eprintln!("receipt file not found: {}", path.display());
        std::process::exit(2);
    }

    let text = match std::fs::read_to_string(path) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("failed to read receipt {}: {e}", path.display());
            std::process::exit(2);
        }
    };

    match verify_receipt_text(&text) {
        Ok(summary) => {
            println!("PINNED RECEIPT CONFORMANCE PASSED");
            println!("  Dispositions matched: {}", summary.disposition_count);
            println!("  Passes: {}", summary.pass_count);
            println!("  Refusals: {}", summary.refused_count);
            println!("  Covered claims: {}", summary.covered_claim_count);
            println!("  AuthorityEffect: {}", summary.authority_effect);
            println!("  Trust: compiled-in reference; no independent mathematical verification.");
        }
        Err(failures) => {
            eprintln!(
                "PINNED RECEIPT CONFORMANCE FAILED ({} errors):",
                failures.len()
            );
            for (idx, err) in failures.iter().enumerate() {
                eprintln!("  [{}] {err}", idx + 1);
            }
            std::process::exit(1);
        }
    }
}
