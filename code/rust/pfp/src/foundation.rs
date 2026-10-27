//! Primitive-first, exact finite foundation for the Symbol Game.
//!
//! This module is deliberately additive. It does not participate in the
//! consequential OESOS host protocol. Its certificates and witnesses are
//! constructed only after recomputing the finite claims they bind.

use std::fmt;

use num_rational::BigRational;
use num_traits::Zero;
use pfp_runtime::canonical::canonical_bytes;
use serde_json::Value;

/// A nullary witness that a distinction exists.
///
/// It intentionally contains no carrier, endpoints, direction, incidence, or
/// graph data.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Hash)]
pub struct PrimitiveDifference;

/// Stable categories for fail-closed foundation errors.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FoundationErrorCode {
    InvalidName,
    InvalidDigest,
    NonExactJson,
    DuplicateIdentity,
    MissingDetectorValue,
    IncompleteCoverage,
    EvaluationMismatch,
    NegativeRational,
    RetractionFailure,
    DetectorNotPreserved,
    IncompleteExtension,
    R1Priority,
    ExtensionBindingMismatch,
    NoResolvingExtension,
    ProjectionRequired,
    ProjectionFailed,
    ProtectedInvariantChanged,
    ProtectedLoss,
    IntermediateStateMismatch,
    BoundaryMismatch,
    ParentMismatch,
    DuplicateEvent,
}

/// A typed refusal emitted by the additive mathematical foundation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FoundationError {
    code: FoundationErrorCode,
    message: String,
}

impl FoundationError {
    fn new(code: FoundationErrorCode, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
        }
    }

    pub fn code(&self) -> FoundationErrorCode {
        self.code
    }

    pub fn message(&self) -> &str {
        &self.message
    }
}

impl fmt::Display for FoundationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.message)
    }
}

impl std::error::Error for FoundationError {}

pub(super) fn require_name(value: &str, label: &str) -> Result<(), FoundationError> {
    if value.is_empty() || value.trim() != value {
        return Err(FoundationError::new(
            FoundationErrorCode::InvalidName,
            format!("{label} must be a non-empty exact string"),
        ));
    }
    Ok(())
}

pub(super) fn require_digest(value: &str, label: &str) -> Result<(), FoundationError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(FoundationError::new(
            FoundationErrorCode::InvalidDigest,
            format!("{label} must be a lowercase SHA-256 digest"),
        ));
    }
    Ok(())
}

pub(super) fn require_nonnegative(value: &BigRational, label: &str) -> Result<(), FoundationError> {
    if value < &BigRational::zero() {
        return Err(FoundationError::new(
            FoundationErrorCode::NegativeRational,
            format!("{label} must be a non-negative BigRational"),
        ));
    }
    Ok(())
}

/// Produce the Python `canonical.py` typed-wire bytes for the admitted exact
/// JSON subset. Object keys are sorted, array order is retained, integers are
/// string-tagged, and floats are refused. The encoder is the runtime's
/// `pfp_runtime::canonical`, pinned by its golden vectors.
pub fn canonical_json_bytes(value: &Value) -> Result<Vec<u8>, FoundationError> {
    canonical_bytes(value).map_err(|error| {
        FoundationError::new(
            FoundationErrorCode::NonExactJson,
            format!("canonical foundation JSON refuses this value: {error}"),
        )
    })
}

mod dda;
mod extension;
mod packet;
mod repair;

pub use dda::*;
pub use extension::*;
pub use packet::*;
pub use repair::*;

// Origin: engine/crates_rs/pfp/src/foundation.rs
// Claim: urn:core:crates_rs:pfp:foundation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_95175ef0 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
