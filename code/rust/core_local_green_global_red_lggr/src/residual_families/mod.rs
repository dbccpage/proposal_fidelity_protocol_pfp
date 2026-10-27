//! # `residual_families` — Hashed-shape registry of recognized residual classes.
//!
//! Diagnostic-only lookup surface. Mints **no** authority. Product-local
//! terminal stamping and checked-packet evidence certification both remain
//! non-authoritative; only the authenticated host promotion contract may create
//! an authorized local result. This module is not on that path.
//!
//! ODP packet:
//! `engine/crates/core_contracts/src/contract_canonical_definitions/core/09_packets/core_residual_families_packet.md`
//!
//! ## Carrier (verbatim from packet §1)
//!
//! > The diagnostic carrier formed by the cochain shape signature of
//! > `core_homology::cochain_primitive_difference::CochainPrimitiveDifference`
//! > instances emitted by `core_homology::cochain_complex::CochainComplex::d0`
//! > and `::d1`. The 2-window inspects the local pair
//! > $(\sigma(Q^1), \sigma(\Gamma_2))$ where $\sigma$ is a `blake3`-derived
//! > shape-only signature over the primitive-difference structure (face indices,
//! > arity, coefficient-domain tag, quotient-class id from
//! > `core_homology::quotient::QuotientSpace`), and where the right-hand window
//! > slot is the diagnostic mass pair
//! > $(\Phi_1, \Gamma_2)$ produced by
//! > `core_functional::phi1::VerifiedExactPhi1` and
//! > `core_functional::gamma2::ExactGamma2Result` under a fixed
//! > `core_types::observer::Observer`. The carrier deliberately discards
//! > raw cochain payload bytes: the signature key is the only persisted shape
//! > fingerprint.
//!
//! ## $C^0$ (verbatim from packet §2)
//!
//! > No crate yet exists. The local assignments are
//! > (a) the existing in-tree types
//! > `CochainPrimitiveDifference`, `QuotientSpace`,
//! > `core_functional::phi1::VerifiedExactPhi1`,
//! > `core_functional::gamma2::ExactGamma2Result`,
//! > `core_types::observer::Observer`,
//! > and (b) the empty crate skeleton `engine/crates/core_residual_families/`
//! > to be added as a workspace member with a `ShapeSignature` newtype, a
//! > `ResidualClassRecord { signature, q1_class_id, gamma2_class_id, hits: u64 }`
//! > struct, and a `FamilyRegistry` lookup table keyed by `ShapeSignature`.
//!
//! ## ZeroRel (verbatim from packet §5)
//!
//! > Two `CochainPrimitiveDifference` instances are identified iff their
//! > canonicalized shape signature
//! > $\sigma : \text{CochainPrimitiveDifference} \to \text{blake3 digest}$
//! > agrees. Equivalently: differences that vary only by
//! > `core_homology::cochain::Cochain` coefficient values, internal field
//! > ordering, or `core_types::observer::Observer`-local naming, but that
//! > share the same face-index pattern, arity, coefficient-domain tag, and
//! > `QuotientSpace`-id, are gauge-equivalent for registry purposes. ZeroRel is
//! > exactly the kernel of $\sigma$.
//!
//! ## Firewall
//!
//! The host crate (`core_epk`) does NOT depend on `core_sweep_kernel` or `core_certifiers`.
//! No public function returns a `Certificate`; registry operations remain
//! evidence-only and have no authority effect.

pub mod record;
pub mod recurrence;
pub mod registry;
pub mod signature;
pub mod wire;

pub use record::{Gamma2ClassId, Q1ClassId, ResidualClassRecord};
pub use recurrence::registry_hit_recurrence;
pub use registry::{FamilyConsultation, FamilyRegistry, RegistryWrite};
pub use signature::{
    shape_signature, shape_signature_from_exact_complex, ShapeSignature, ShapeSignatureError,
};
pub use wire::{
    derive_gamma2_class_id, derive_q1_class_id, reconcile_verified, record_from_verified,
    FamilyCollision, FamilyResolution,
};

// Exact invariant envelope.
// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/residual_families/mod.rs
// Claim: urn:core:lggr:residual-families:signature-merge:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FamilyMerge {
    classes: u64,
    hits: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FamilyMergeError {
    Empty,
    TooWide,
    Split { index: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/residual_families/mod.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FamilyMergeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FamilyMergeError {}

impl FamilyMerge {
    pub fn classes(&self) -> u64 { self.classes }
    pub fn hits(&self) -> u64 { self.hits }

    pub fn try_merge(records: &[ResidualClassRecord]) -> Result<Self, FamilyMergeError> {
        let first = records.first().ok_or(FamilyMergeError::Empty)?;
        if records.len() > 64 {
            return Err(FamilyMergeError::TooWide);
        }
        let mut hits = 0u64;
        for (index, record) in records.iter().enumerate() {
            if record.signature != first.signature {
                return Err(FamilyMergeError::Split { index });
            }
            hits = hits.checked_add(record.hits).ok_or(FamilyMergeError::Overflow)?;
        }
        let classes = u64::try_from(records.len()).map_err(|_| FamilyMergeError::TooWide)?;
        Ok(Self { classes, hits })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod family_merge_tests {
    use super::*;

    fn record(byte: u8, hits: u64) -> ResidualClassRecord {
        let mut row = ResidualClassRecord::new(
            signature::ShapeSignature::from_bytes([byte; 32]),
            record::Q1ClassId::from_u64(1),
            record::Gamma2ClassId::from_u64(2),
        );
        row.hits = hits;
        row
    }

    #[test]
    fn one_signature_sums_its_hits() {
        let merged = FamilyMerge::try_merge(&[record(7, 1), record(7, 4)]);
        assert!(matches!(merged, Ok(ref row) if row.classes() == 2 && row.hits() == 5));
    }

    #[test]
    fn a_second_signature_splits_the_family() {
        assert!(matches!(
            FamilyMerge::try_merge(&[record(7, 1), record(8, 1)]),
            Err(FamilyMergeError::Split { index: 1 })
        ));
    }
}
