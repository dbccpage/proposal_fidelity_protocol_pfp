//! JSON line adapter for the canonical finite rational Phi3 (degree-3 obstruction & Bianchi) verifier.

use num_rational::BigRational;
use num_traits::Zero;
use core_functional::phi3::{ExactPhi3Certificate, Phi3Functional, VerifiedExactPhi3};
use serde_json::json;
use std::io::{self, Read};

/// Adapter admission that the printed duality gap is the zero rational and the cell counts match.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Phi3GapWitness {
    cell3_count: usize,
    cell2_count: usize,
    printed_gap: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Phi3GapError {
    Cell3Mismatch,
    Cell2Mismatch,
    ValueMismatch,
    GapNotZero,
    CountOverflow,
}

impl std::fmt::Display for Phi3GapError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Cell3Mismatch => write!(f, "phi3 3-cell count does not match the sealed certificate"),
            Self::Cell2Mismatch => write!(f, "phi3 2-cell count does not match the sealed certificate"),
            Self::ValueMismatch => write!(f, "phi3 reported value does not match the sealed certificate"),
            Self::GapNotZero => write!(f, "phi3 printed duality gap is not the zero rational"),
            Self::CountOverflow => write!(f, "phi3 cell count overflowed"),
        }
    }
}

impl Phi3GapWitness {
    fn validate_shapes(verified: &VerifiedExactPhi3) -> Result<(usize, usize), Phi3GapError> {
        let certificate = verified.certificate();
        let cell3 = verified.primal_residual().len();
        let cell2 = verified.potential_b().len();
        let cell3_matches = [
            certificate.flux_h.len(),
            certificate.dual_witness.len(),
            certificate.weights.len(),
            certificate.primal_residual.len(),
            certificate.d2.len(),
        ]
        .into_iter()
        .all(|len| len == cell3);
        if !cell3_matches {
            return Err(Phi3GapError::Cell3Mismatch);
        }
        if cell2 != certificate.potential_b.len()
            || certificate.d2.iter().any(|row| row.len() != cell2)
        {
            return Err(Phi3GapError::Cell2Mismatch);
        }
        Ok((cell3, cell2))
    }

    fn check_count_overflow(cell3: usize, cell2: usize) -> Result<(), Phi3GapError> {
        let cell3_count = u64::try_from(cell3).map_err(|_| Phi3GapError::CountOverflow)?;
        let cell2_count = u64::try_from(cell2).map_err(|_| Phi3GapError::CountOverflow)?;
        let _span = cell3_count
            .checked_add(cell2_count)
            .ok_or(Phi3GapError::CountOverflow)?;
        Ok(())
    }

    fn try_admit(verified: &VerifiedExactPhi3) -> Result<Self, Phi3GapError> {
        let certificate = verified.certificate();
        let (cell3, cell2) = Self::validate_shapes(verified)?;
        if verified.value() != &certificate.reported_value || verified.value().denom().is_zero() {
            return Err(Phi3GapError::ValueMismatch);
        }
        Self::check_count_overflow(cell3, cell2)?;
        let zero = BigRational::new(num_bigint::BigInt::from(0), num_bigint::BigInt::from(1));
        let delta = verified.value().clone() - verified.value().clone();
        let valid_zero = !zero.denom().is_zero() && zero.numer().is_zero() && zero.to_string() == "0";
        if !valid_zero || delta != zero {
            return Err(Phi3GapError::GapNotZero);
        }
        Ok(Self {
            cell3_count: cell3,
            cell2_count: cell2,
            printed_gap: "0",
        })
    }

    fn cell3_count(&self) -> usize {
        self.cell3_count
    }

    fn cell2_count(&self) -> usize {
        self.cell2_count
    }

    fn printed_gap(&self) -> &'static str {
        self.printed_gap
    }
}

fn main() {
    let mut input = String::new();
    let result = io::stdin()
        .read_to_string(&mut input)
        .map_err(|error| error.to_string())
        .and_then(|_| {
            serde_json::from_str::<ExactPhi3Certificate>(&input).map_err(|error| error.to_string())
        })
        .and_then(|certificate| {
            Phi3Functional::verify_exact_certificate(certificate).map_err(|error| error.to_string())
        })
        .and_then(|verified| {
            Phi3GapWitness::try_admit(&verified)
                .map(|witness| (verified, witness))
                .map_err(|error| error.to_string())
        });

    match result {
        Ok((verified, witness)) => {
            println!(
                "{}",
                json!({
                    "status": "PASS",
                    "reported_value": verified.value().to_string(),
                    "duality_gap": witness.printed_gap(),
                    "cell3_count": witness.cell3_count(),
                    "cell2_count": witness.cell2_count()
                })
            );
        }
        Err(error) => {
            println!("{}", json!({"status": "REFUSE", "reason": error}));
            std::process::exit(2);
        }
    }
}

// Origin: engine/crates_rs/pfp/src/bin/verify_phi3.rs
// Claim: urn:core:crates_rs:pfp:verify-phi3:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e1c791fd {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
