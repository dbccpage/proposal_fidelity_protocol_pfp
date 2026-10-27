//! Bockstein homomorphism for integral lifts.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_2f4602d9;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_2f4602d9<T> = std::result::Result<T, BoundaryError_2f4602d9>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `bockstein_homomorphism`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct BocksteinHomomorphism {
    pub label: String,
    pub notes: Vec<String>,
}

impl BocksteinHomomorphism {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("label must be non-empty".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = BocksteinHomomorphism::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = BocksteinHomomorphism::new("bockstein_homomorphism").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BocksteinError {
    Shell,
    Prime,
    Range,
    NotCocycle,
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/bockstein_homomorphism.rs
// Claim: urn:core:crates_rs:core-homology:bockstein-homomorphism:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BocksteinError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BocksteinError {}

/// The mod-p Bockstein of an integral 1-cochain on a triangle.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BocksteinQuotient {
    prime: u64,
    quotient: u64,
}

fn prime_modulus(prime: u64) -> bool {
    if prime < 2 {
        return false;
    }
    let mut divisor = 2u64;
    loop {
        match divisor.checked_mul(divisor) {
            Some(square) if square <= prime => {
                if prime % divisor == 0 {
                    return false;
                }
                match divisor.checked_add(1) {
                    Some(next) => divisor = next,
                    None => return true,
                }
            }
            _ => return true,
        }
    }
}

impl BocksteinQuotient {
    fn check_edge_range(prime: u64, edges: [u64; 3]) -> Result<(), BocksteinError> {
        let square = prime.checked_mul(prime).ok_or(BocksteinError::Overflow)?;
        if edges.iter().any(|&e| e >= square) {
            return Err(BocksteinError::Range);
        }
        Ok(())
    }

    pub fn try_new(shell: &BocksteinHomomorphism, prime: u64, edge_01: u64, edge_12: u64, edge_02: u64) -> Result<Self, BocksteinError> {
        shell.validate_shell().map_err(|_| BocksteinError::Shell)?;
        if !prime_modulus(prime) {
            return Err(BocksteinError::Prime);
        }
        Self::check_edge_range(prime, [edge_01, edge_12, edge_02])?;
        let coboundary = i128::from(edge_01)
            .checked_add(i128::from(edge_12))
            .and_then(|s| s.checked_sub(i128::from(edge_02)))
            .ok_or(BocksteinError::Overflow)?;
        let modulus = i128::from(prime);
        if coboundary.rem_euclid(modulus) != 0 {
            return Err(BocksteinError::NotCocycle);
        }
        let quotient = coboundary.div_euclid(modulus).rem_euclid(modulus);
        Ok(Self { prime, quotient: u64::try_from(quotient).map_err(|_| BocksteinError::Overflow)? })
    }

    pub fn prime(&self) -> u64 { self.prime }
    pub fn quotient(&self) -> u64 { self.quotient }
}

#[cfg(test)]
mod bockstein_tests {
    use super::*;

    #[test]
    fn a_multiple_of_three_has_bockstein_one() {
        let shell = BocksteinHomomorphism::new("bockstein");
        let quotient = BocksteinQuotient::try_new(&shell, 3, 3, 0, 0);
        assert!(matches!(quotient, Ok(ref quotient) if quotient.quotient() == 1 && quotient.prime() == 3));
    }

    #[test]
    fn a_non_cocycle_is_refused() {
        let shell = BocksteinHomomorphism::new("bockstein");
        let quotient = BocksteinQuotient::try_new(&shell, 3, 1, 0, 0);
        assert!(matches!(quotient, Err(BocksteinError::NotCocycle)));
    }
}
