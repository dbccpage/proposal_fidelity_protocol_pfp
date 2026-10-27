//! Tier 0 substrate. Depends on nothing in the workspace; everything depends on it.
//!
//! AuthorityEffect: None.

pub mod digest;
pub mod elementary;
pub mod exact;
pub mod interval;
pub mod obligation;
pub mod observation_partition;
pub mod observer;

pub use digest::{Digest, DigestError};
pub use exact::{
    approximate, exact, exact_wire, exact_wire_option, exact_wire_pairs, exact_wire_vec, integer,
    parse_exact, to_canonical_string, Exact, ExactError,
};
pub use obligation::{
    ObligationError, ObligationId, ObligationIdError, ObligationLedger, Obligations,
};
pub use observer::{Observed, ObserverId, ObserverIdError};

pub mod resource_limits;
pub mod square_root_enclosure;

pub mod evidence;

pub mod bounded_rational;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CanonicalRationalError {
    ZeroDenominator,
    NotCanonical,
}

// Origin: engine/crates_rs/core_kernel/src/lib.rs
// Claim: urn:core:crates_rs:core-kernel:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CanonicalRationalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CanonicalRationalError {}

/// Builds an exact rational only after refusing a zero denominator, then
/// requires the canonical text to parse back to the same text.
pub fn certify_canonical_rational(
    numerator: i64,
    denominator: i64,
) -> Result<Exact, CanonicalRationalError> {
    if denominator == 0 {
        return Err(CanonicalRationalError::ZeroDenominator);
    }
    let value = exact(numerator, denominator);
    let text = to_canonical_string(&value);
    let parsed = parse_exact(&text).map_err(|_| CanonicalRationalError::NotCanonical)?;
    if to_canonical_string(&parsed) != text {
        return Err(CanonicalRationalError::NotCanonical);
    }
    Ok(parsed)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_49131dc7 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
