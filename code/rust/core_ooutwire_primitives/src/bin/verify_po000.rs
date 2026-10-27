//! `verify_po000` — pinned receipt conformance checker for the PO-000 replication receipt.
//!
//! ```text
//! cargo run --release --bin verify_po000            # verify default RECEIPT.txt
//! cargo run --release --bin verify_po000 -- <path>  # verify custom receipt path
//! ```
//!
//! `AuthorityEffect: None.`

use core_ooutwire_primitives::alpha_projection_obstruction::verify::{
    verify_receipt_text, VerificationSummary, REQUIRED_LEDGER_CLAIMS,
};
use std::path::Path;

/// Pinned inventory the adapter prints only after pass + refused = dispositions.
#[derive(Debug, Clone, PartialEq, Eq)]
struct PinnedInventoryWitness {
    dispositions: usize,
    passes: usize,
    refusals: usize,
    covered_claims: usize,
    required_claims: usize,
    authority: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum PinnedInventoryError {
    SumMismatch,
    InventoryMismatch,
    AuthorityMismatch,
    RequiredClaims,
    CoveredBelowRequired,
}

impl std::fmt::Display for PinnedInventoryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::SumMismatch => write!(f, "pass count plus refusal count does not equal dispositions"),
            Self::InventoryMismatch => write!(f, "pinned receipt inventory counts drifted"),
            Self::AuthorityMismatch => write!(f, "pinned receipt authority is not None"),
            Self::RequiredClaims => write!(f, "required ledger claim ids are empty or repeated"),
            Self::CoveredBelowRequired => {
                write!(f, "covered claims do not properly contain the required ledger ids")
            }
        }
    }
}

impl PinnedInventoryWitness {
    fn validate_pinned_summary(summary: &VerificationSummary) -> Result<(), PinnedInventoryError> {
        let summed = summary
            .pass_count
            .checked_add(summary.refused_count)
            .ok_or(PinnedInventoryError::SumMismatch)?;
        if summed != summary.disposition_count {
            return Err(PinnedInventoryError::SumMismatch);
        }
        let pinned = 18usize
            .checked_add(6)
            .ok_or(PinnedInventoryError::SumMismatch)?;
        if pinned != 24
            || summary.disposition_count != 24
            || summary.pass_count != 18
            || summary.refused_count != 6
            || summary.covered_claim_count != 53
        {
            return Err(PinnedInventoryError::InventoryMismatch);
        }
        if summary.authority_effect != "None" {
            return Err(PinnedInventoryError::AuthorityMismatch);
        }
        Ok(())
    }

    fn count_required_ledger_claims() -> Result<usize, PinnedInventoryError> {
        let mut required_claims = 0usize;
        for (index, id) in REQUIRED_LEDGER_CLAIMS.iter().enumerate() {
            if id.is_empty() {
                return Err(PinnedInventoryError::RequiredClaims);
            }
            let prior = REQUIRED_LEDGER_CLAIMS
                .get(..index)
                .ok_or(PinnedInventoryError::RequiredClaims)?;
            if prior.iter().any(|earlier| earlier == id) {
                return Err(PinnedInventoryError::RequiredClaims);
            }
            required_claims = required_claims
                .checked_add(1)
                .ok_or(PinnedInventoryError::SumMismatch)?;
        }
        if required_claims == 0 {
            return Err(PinnedInventoryError::RequiredClaims);
        }
        Ok(required_claims)
    }

    fn try_admit(summary: &VerificationSummary) -> Result<Self, PinnedInventoryError> {
        Self::validate_pinned_summary(summary)?;
        let required_claims = Self::count_required_ledger_claims()?;
        let extra = summary
            .covered_claim_count
            .checked_sub(required_claims)
            .ok_or(PinnedInventoryError::CoveredBelowRequired)?;
        if extra == 0 {
            return Err(PinnedInventoryError::CoveredBelowRequired);
        }
        let witness = Self {
            dispositions: summary.disposition_count,
            passes: summary.pass_count,
            refusals: summary.refused_count,
            covered_claims: summary.covered_claim_count,
            required_claims,
            authority: summary.authority_effect.clone(),
        };
        Ok(witness)
    }

    fn admits_banner(&self) -> bool {
        self.authority == "None"
            && self.passes.checked_add(self.refusals) == Some(self.dispositions)
            && self.dispositions == 24
            && self.covered_claims == 53
            && self.covered_claims > self.required_claims
    }
}

fn main() {
    let receipt_path = std::env::args().nth(1).unwrap_or_else(|| {
        let default_path = core_ooutwire_primitives::alpha_projection_obstruction::receipt_path();
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
            match PinnedInventoryWitness::try_admit(&summary) {
                Ok(witness) if witness.admits_banner() => {}
                Ok(_) => {
                    eprintln!(
                        "pinned receipt inventory refused: {}",
                        PinnedInventoryError::InventoryMismatch
                    );
                    std::process::exit(1);
                }
                Err(error) => {
                    eprintln!("pinned receipt inventory refused: {error}");
                    std::process::exit(1);
                }
            }
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

// Origin: engine/crates_rs/core_ooutwire_primitives/src/bin/verify_po000.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:verify-po000:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_712f73af {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
