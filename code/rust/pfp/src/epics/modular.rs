//! Integer modular arithmetic shared by Rust-side Symbol Game re-derivations.
//!
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_3497af1b;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_3497af1b<T> = std::result::Result<T, BoundaryError_3497af1b>;

/// Return the least non-negative residue of `lhs` modulo a positive `modulus`.
///
/// Rust's `%` is a truncated remainder: `-17 % 5 == -2`.  Symbol Game's
/// cross-language contract uses the cyclic-group convention instead, where
/// `-17 mod 5 == 3`.  `rem_euclid` states that convention directly.
///
/// # Panics
///
/// Panics when `modulus <= 0`. A modulus is a cycle order on this interface and
/// therefore strictly positive; rejecting the invalid domain keeps the helper
/// from silently assigning a second convention to negative moduli.
pub fn least_non_negative_residue(lhs: i128, modulus: i128) -> i128 {
    assert!(modulus > 0, "modulus must be strictly positive");
    lhs.rem_euclid(modulus)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn negative_dividends_use_the_cyclic_group_convention() {
        assert_eq!(least_non_negative_residue(-17, 5), 3);
        assert_ne!(least_non_negative_residue(-17, 5), -17 % 5);
    }

    #[test]
    #[should_panic(expected = "modulus must be strictly positive")]
    fn nonpositive_moduli_are_outside_the_contract() {
        let _ = least_non_negative_residue(17, 0);
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/pfp/src/epics/modular.rs
// Claim: urn:core:symbol-game:modular:residue-certificate:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResidueCertificate {
    quotient: i128,
    residue: i128,
    modulus: i128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResidueError {
    NonPositiveModulus,
    ResidueOutOfRange { residue: i128, modulus: i128 },
    ReconstructionOverflow,
    ReconstructionMismatch { rebuilt: i128, lhs: i128 },
}

// Origin: engine/crates_rs/pfp/src/epics/modular.rs
// Claim: urn:core:crates_rs:pfp:modular:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ResidueError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ResidueError {}

pub fn try_residue_certificate(lhs: i128, modulus: i128) -> Result<ResidueCertificate, ResidueError> {
    if modulus <= 0 {
        return Err(ResidueError::NonPositiveModulus);
    }
    let residue = lhs.rem_euclid(modulus);
    if residue < 0 || residue >= modulus {
        return Err(ResidueError::ResidueOutOfRange { residue, modulus });
    }
    let shifted = lhs.checked_sub(residue).ok_or(ResidueError::ReconstructionOverflow)?;
    let quotient = shifted.checked_div(modulus).ok_or(ResidueError::ReconstructionOverflow)?;
    let rebuilt = quotient
        .checked_mul(modulus)
        .ok_or(ResidueError::ReconstructionOverflow)?
        .checked_add(residue)
        .ok_or(ResidueError::ReconstructionOverflow)?;
    if rebuilt != lhs {
        return Err(ResidueError::ReconstructionMismatch { rebuilt, lhs });
    }
    Ok(ResidueCertificate { quotient, residue, modulus })
}

impl ResidueCertificate {
    pub fn quotient(&self) -> i128 {
        self.quotient
    }

    pub fn residue(&self) -> i128 {
        self.residue
    }
}

#[cfg(test)]
mod residue_certificate_tests {
    use super::*;

    #[test]
    fn negative_seventeen_mod_five_is_three() {
        let witness = try_residue_certificate(-17, 5);
        assert!(matches!(
            witness,
            Ok(ref row) if row.residue() == 3 && row.quotient() == -4
        ));
    }

    #[test]
    fn a_nonpositive_modulus_is_an_error() {
        assert!(matches!(
            try_residue_certificate(17, 0),
            Err(ResidueError::NonPositiveModulus)
        ));
        assert!(matches!(
            try_residue_certificate(17, -5),
            Err(ResidueError::NonPositiveModulus)
        ));
    }
}
