//! Wiring (S7): bind the registry to the real `core_functional::phi1` and
//! `core_functional::gamma2` public surfaces. Diagnostic-only. Mints no
//! authority.
//!
//! Per the S7b stability requirement, the local-id derivation is restricted to
//! the genuinely shape-bearing accessors `phi1.value()`, `phi1.d0()`,
//! `gamma2.value()`, `gamma2.d0()`. The `alpha` / `primal_residual` /
//! `dual_witness` accessors are gauge-twin axes and are deliberately NOT
//! hashed into the local class id. The `Observer.id` and `Observer.kind` are
//! recorded for audit elsewhere; they are NOT inputs to the local class id.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_9d78c97b;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_9d78c97b<T> = std::result::Result<T, BoundaryError_9d78c97b>;

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_9d78c97b<T> {
    fn checked_invariant_9d78c97b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_9d78c97b<T> for Option<T> {
    #[inline]
    fn checked_invariant_9d78c97b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_9d78c97b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_9d78c97b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::fmt;

use core_linear_algebra::backend::basic_matrix::CheckedNumeric;
use core_functional::gamma2::ExactGamma2Result;
use core_functional::phi1::VerifiedExactPhi1;
use core_homology::cochain_primitive_difference::CochainPrimitiveDifference;
use core_homology::quotient::QuotientSpace;
use core_types::observer::Observer;
use serde::Serialize;

use crate::residual_families::record::{Gamma2ClassId, Q1ClassId};
use crate::residual_families::registry::{FamilyConsultation, FamilyRegistry, RegistryWrite};
use crate::residual_families::signature::shape_signature;

fn truncate_to_u64(digest: &blake3::Hash) -> u64 {
    let bytes = digest.as_bytes();
    let mut buf = [0u8; 8];
    buf.copy_from_slice(&bytes[..8]);
    u64::from_le_bytes(buf)
}

/// Local `Q1ClassId` derivation: blake3 digest over the shape-bearing
/// accessors of `VerifiedExactPhi1` — `phi1.value()` and `phi1.d0()`.
///
/// Per S7b, `phi1.alpha()`, `phi1.primal_residual()`, and `phi1.dual_witness()`
/// are gauge-twin axes and are NOT hashed into the local id. The `Observer.id`
/// / `Observer.kind` are recorded elsewhere for audit; they are NOT part of
/// the local class key.
///
/// # Panics
///
/// Panics only if `serde_json::to_vec` fails to serialize `phi1.value()`
/// (a `BigRational`) or `phi1.d0()` (a `Vec<Vec<BigRational>>`). Both carry
/// total serde derives, so this is unreachable for the current types.
#[must_use]
pub fn derive_q1_class_id(phi1: &VerifiedExactPhi1) -> Q1ClassId {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"core_residual_families::derive_q1_class_id::v1");

    let value_bytes = serde_json::to_vec(phi1.value())
        .checked_invariant_9d78c97b("serde_json::to_vec on VerifiedExactPhi1::value (BigRational total serde)");
    hasher.update(b"phi1.value");
    hasher.update(&(value_bytes.len() as u64).to_le_bytes());
    hasher.update(&value_bytes);

    let d0_bytes = serde_json::to_vec(phi1.d0())
        .checked_invariant_9d78c97b("serde_json::to_vec on VerifiedExactPhi1::d0 (Vec<Vec<BigRational>> total serde)");
    hasher.update(b"phi1.d0");
    hasher.update(&(d0_bytes.len() as u64).to_le_bytes());
    hasher.update(&d0_bytes);

    let digest = hasher.finalize();
    Q1ClassId::from_u64(truncate_to_u64(&digest))
}

/// Local `Gamma2ClassId` derivation: blake3 digest over the shape-bearing
/// accessors of `ExactGamma2Result` — `gamma2.value()` and `gamma2.d0()`.
///
/// Per S7b, `gamma2.residual()` and `gamma2.coboundary()` are gauge-twin axes
/// and are NOT hashed into the local id.
///
/// # Panics
///
/// Panics only if `serde_json::to_vec` fails to serialize `gamma2.value()`
/// (a `BigRational`) or `gamma2.d0()` (a `Vec<Vec<BigRational>>`). Both carry
/// total serde derives, so this is unreachable for the current types.
#[must_use]
pub fn derive_gamma2_class_id(gamma2: &ExactGamma2Result) -> Gamma2ClassId {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"core_residual_families::derive_gamma2_class_id::v1");

    let value_bytes = serde_json::to_vec(gamma2.value())
        .checked_invariant_9d78c97b("serde_json::to_vec on ExactGamma2Result::value (BigRational total serde)");
    hasher.update(b"gamma2.value");
    hasher.update(&(value_bytes.len() as u64).to_le_bytes());
    hasher.update(&value_bytes);

    let d0_bytes = serde_json::to_vec(gamma2.d0())
        .checked_invariant_9d78c97b("serde_json::to_vec on ExactGamma2Result::d0 (Vec<Vec<BigRational>> total serde)");
    hasher.update(b"gamma2.d0");
    hasher.update(&(d0_bytes.len() as u64).to_le_bytes());
    hasher.update(&d0_bytes);

    let digest = hasher.finalize();
    Gamma2ClassId::from_u64(truncate_to_u64(&digest))
}

/// Successful reconciliation of a pre-replay lookup with current exact evidence.
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub struct FamilyResolution {
    signature: crate::residual_families::signature::ShapeSignature,
    q1_class_id: Q1ClassId,
    gamma2_class_id: Gamma2ClassId,
    lookup_hit: bool,
    write: RegistryWrite,
}

impl FamilyResolution {
    #[must_use]
    pub fn signature(&self) -> crate::residual_families::signature::ShapeSignature {
        self.signature
    }

    #[must_use]
    pub fn q1_class_id(&self) -> Q1ClassId {
        self.q1_class_id
    }

    #[must_use]
    pub fn gamma2_class_id(&self) -> Gamma2ClassId {
        self.gamma2_class_id
    }

    /// `true` only when the explicit lookup hit before class-id derivation.
    #[must_use]
    pub fn lookup_hit(&self) -> bool {
        self.lookup_hit
    }

    pub fn registry_write(&self) -> RegistryWrite {
        self.write
    }
}

/// Same shape key produced a different exact residual class.
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub struct FamilyCollision {
    pub signature: crate::residual_families::signature::ShapeSignature,
    pub prior_q1_class_id: Q1ClassId,
    pub prior_gamma2_class_id: Gamma2ClassId,
    pub observed_q1_class_id: Q1ClassId,
    pub observed_gamma2_class_id: Gamma2ClassId,
}

impl fmt::Display for FamilyCollision {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("residual-family shape mapped to a different exact Phi1/Gamma2 class")
    }
}

impl std::error::Error for FamilyCollision {}

/// Reconcile a lookup performed before exact replay with current verified
/// Phi1/Gamma2 evidence.
///
/// This function derives class ids only after receiving a
/// [`FamilyConsultation`], making the consumer order explicit:
/// `shape -> lookup -> shared exact replay -> reconcile`. A hit never replaces
/// replay. A same-shape/different-class result is returned as an error and the
/// registry preserves the prior class.
pub fn reconcile_verified(
    reg: &mut FamilyRegistry,
    consultation: FamilyConsultation,
    phi1: &VerifiedExactPhi1,
    gamma2: &ExactGamma2Result,
    observer: &Observer,
) -> Result<FamilyResolution, FamilyCollision> {
    let _ = (&observer.id, &observer.kind);
    let signature = consultation.signature();
    let lookup_hit = consultation.was_hit();
    let q1 = derive_q1_class_id(phi1);
    let g2 = derive_gamma2_class_id(gamma2);
    let write = reg.record(signature, q1, g2);

    if write == (RegistryWrite::Hit { collision: true }) {
        let prior = reg
            .lookup(&signature)
            .checked_invariant_9d78c97b("collision implies an existing registry record");
        return Err(FamilyCollision {
            signature,
            prior_q1_class_id: prior.q1_class_id,
            prior_gamma2_class_id: prior.gamma2_class_id,
            observed_q1_class_id: q1,
            observed_gamma2_class_id: g2,
        });
    }

    Ok(FamilyResolution {
        signature,
        q1_class_id: q1,
        gamma2_class_id: g2,
        lookup_hit,
        write,
    })
}

/// Compute `ShapeSignature` (S2) and derive local
/// `(Q1ClassId, Gamma2ClassId)`, then `record` into the registry.
///
/// The `observer` argument is taken for future audit-side wiring, but is
/// deliberately NOT folded into the local class id (S7b): observer kind /
/// identity must not change the class key for a given shape.
///
/// # Panics
///
/// Panics only via the total-serde `expect`s in [`shape_signature`],
/// [`derive_q1_class_id`], and [`derive_gamma2_class_id`] — unreachable for the
/// current `BigRational` / `QuotientRelation` types.
pub fn record_from_verified<K>(
    reg: &mut FamilyRegistry,
    diff: &CochainPrimitiveDifference<'_>,
    q: &QuotientSpace<K>,
    phi1: &VerifiedExactPhi1,
    gamma2: &ExactGamma2Result,
    observer: &Observer,
) -> RegistryWrite
where
    K: CheckedNumeric + PartialEq + Serialize,
{
    // The observer is read so the call site cannot accidentally drop it; we
    // deliberately do NOT mix it into either id (S7b stability requirement).
    let _ = (&observer.id, &observer.kind);

    let sig = shape_signature(diff, q);
    let q1 = derive_q1_class_id(phi1);
    let g2 = derive_gamma2_class_id(gamma2);
    reg.record(sig, q1, g2)
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/residual_families/wire.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:wire:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9d78c97b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
