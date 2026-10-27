//! Univalence witness shape records (ShapeOnly).
//!
//! [`UnivalenceWitness`] holds references that *would* inhabit a univalence
//! statement in a universe. **This module does not claim that the univalence
//! axiom is proved**, does not mint authority, and does not assert that
//! `proof_ref` is a completed formal proof — only that the shape is filled.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// ShapeOnly witness record for univalence in a named universe.
///
/// - `universe_ref` — carrier universe (e.g. `U_i`) in which UA is stated
/// - `proof_ref` — external reference to a purported witness/certificate object
///
/// **AuthorityEffect: None.** Presence of this record is not a proof of UA
/// and must not be promoted as one.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UnivalenceWitness {
    pub universe_ref: String,
    pub proof_ref: String,
}

impl UnivalenceWitness {
    /// Shape-only validation: universe and proof references must be non-empty.
    ///
    /// Does **not** verify that `proof_ref` is a valid univalence proof.
    pub fn validate(&self) -> Result<(), UnivalenceWitnessError> {
        if self.universe_ref.is_empty() || self.proof_ref.is_empty() {
            return Err(UnivalenceWitnessError::MissingReference);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum UnivalenceWitnessError {
    #[error("univalence witness is missing universe or proof reference")]
    MissingReference,
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/univalence_witness.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:univalence-witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn univalence_witness_shape_only_validate() {
        let w = UnivalenceWitness {
            universe_ref: "U0".to_string(),
            proof_ref: "ua-shape-ref".to_string(),
        };
        assert!(w.validate().is_ok());
    }

    #[test]
    fn univalence_witness_rejects_empty() {
        let w = UnivalenceWitness {
            universe_ref: String::new(),
            proof_ref: "p".to_string(),
        };
        assert_eq!(w.validate(), Err(UnivalenceWitnessError::MissingReference));
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransportError { kind: &'static str, left: u128, right: u128 }
impl TransportError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Finite carrier transport. Mutual inverses on 0..n are checked here; this is not a proof of univalence.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FiniteTransport { cardinality: u64 }
fn to_u128(n: usize) -> u128 {
    u128::try_from(n).unwrap_or(u128::MAX)
}

fn lookup_image_and_preimage(
    forward: &[u64],
    backward: &[u64],
    index: u64,
    cardinality: u64,
) -> Result<(u64, u64), TransportError> {
    let position = usize::try_from(index)
        .map_err(|_| TransportError::new("index exceeds usize", u128::from(index), 0))?;
    let image = *forward.get(position).ok_or_else(|| {
        TransportError::new("forward image missing", u128::from(index), u128::from(cardinality))
    })?;
    let preimage = *backward.get(position).ok_or_else(|| {
        TransportError::new("backward image missing", u128::from(index), u128::from(cardinality))
    })?;
    Ok((image, preimage))
}

fn check_inverse_index(
    forward: &[u64],
    backward: &[u64],
    index: u64,
    cardinality: u64,
) -> Result<(), TransportError> {
    let (image, preimage) = lookup_image_and_preimage(forward, backward, index, cardinality)?;
    if image >= cardinality || preimage >= cardinality {
        return Err(TransportError::new(
            "map leaves 0..n",
            u128::from(image.max(preimage)),
            u128::from(cardinality),
        ));
    }
    let image_at = usize::try_from(image)
        .map_err(|_| TransportError::new("image exceeds usize", u128::from(image), 0))?;
    let back = *backward.get(image_at).ok_or_else(|| {
        TransportError::new("backward at image missing", u128::from(image), u128::from(cardinality))
    })?;
    if back != index {
        return Err(TransportError::new(
            "maps are not mutual inverses",
            u128::from(back),
            u128::from(index),
        ));
    }
    Ok(())
}

impl FiniteTransport {
    pub fn try_inverse(forward: &[u64], backward: &[u64]) -> Result<Self, TransportError> {
        if forward.len() != backward.len() {
            return Err(TransportError::new(
                "transport maps have different lengths",
                to_u128(forward.len()),
                to_u128(backward.len()),
            ));
        }
        let cardinality = u64::try_from(forward.len()).map_err(|_| {
            TransportError::new(
                "cardinality exceeds u64",
                to_u128(forward.len()),
                u128::from(u64::MAX),
            )
        })?;
        for index in 0..cardinality {
            check_inverse_index(forward, backward, index, cardinality)?;
        }
        Ok(Self { cardinality })
    }
    pub const fn cardinality(&self) -> u64 { self.cardinality }
}
#[cfg(test)]
mod finite_transport_checks {
    use super::FiniteTransport;
    #[test]
    fn a_transposition_is_its_own_inverse() {
        assert_eq!(FiniteTransport::try_inverse(&[1, 0, 2], &[1, 0, 2]).as_ref().map(FiniteTransport::cardinality), Ok(3));
        assert_eq!(FiniteTransport::try_inverse(&[1, 0], &[0, 1]).map(|_| ()).map_err(|e| e.kind()), Err("maps are not mutual inverses"));
    }
}
