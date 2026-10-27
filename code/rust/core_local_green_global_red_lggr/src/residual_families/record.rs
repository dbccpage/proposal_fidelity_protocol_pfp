//! `ResidualClassRecord` + opaque local id newtypes.
//!
//! `Q1ClassId` and `Gamma2ClassId` are LOCAL ids only. They carry NO
//! authority. Product-local terminal stamping and checked-packet certification
//! are evidence-only; authority requires the separate authenticated host
//! promotion contract. This module has no dependency on those paths.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_0b01eb18;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_0b01eb18<T> = std::result::Result<T, BoundaryError_0b01eb18>;

/// Local opaque id for a `Q^1` residual class.
///
/// Computed by [`crate::residual_families::wire::derive_q1_class_id`] as a deterministic
/// `blake3`-derived digest over the shape-relevant accessors of
/// `core_functional::phi1::VerifiedExactPhi1` (specifically `.value()` and
/// `.d0()`; see S7b). NO authority — local registry id only.
///
/// # Collision bound
///
/// This id is the low 64 bits of a 256-bit `blake3` digest (see
/// [`crate::residual_families::wire::derive_q1_class_id`]). The birthday bound is therefore
/// `~2^32` distinct classes before a 50% chance of an accidental id collision.
/// At the registry's current scale this is comfortable; if the registry is
/// ever expected to hold `> 2^24` classes, widen this newtype to `u128` /
/// `[u8; 16]`.
#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq)]
pub struct Q1ClassId(u64);

impl Q1ClassId {
    /// Construct from a raw `u64`. Test-and-fixture-only.
    #[must_use]
    pub fn from_u64(bits: u64) -> Self {
        Self(bits)
    }

    /// Borrow the underlying `u64`. For equality testing only; opaque elsewhere.
    #[must_use]
    pub fn as_u64(self) -> u64 {
        self.0
    }
}

/// Local opaque id for a `Gamma_2` closure-defect class.
///
/// Computed by [`crate::residual_families::wire::derive_gamma2_class_id`] as a deterministic
/// `blake3`-derived digest over the shape-relevant accessors of
/// `core_functional::gamma2::ExactGamma2Result` (specifically `.value()` and
/// `.d0()`; see S7b). NO authority — local registry id only.
///
/// # Collision bound
///
/// Same 64-bit-truncation collision bound as [`Q1ClassId`]: the id is the low
/// 64 bits of a 256-bit `blake3` digest, so the birthday bound is `~2^32`
/// classes. Widen to `u128` / `[u8; 16]` if the registry is ever expected to
/// hold `> 2^24` classes.
#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq)]
pub struct Gamma2ClassId(u64);

impl Gamma2ClassId {
    /// Construct from a raw `u64`. Test-and-fixture-only.
    #[must_use]
    pub fn from_u64(bits: u64) -> Self {
        Self(bits)
    }

    /// Borrow the underlying `u64`. For equality testing only; opaque elsewhere.
    #[must_use]
    pub fn as_u64(self) -> u64 {
        self.0
    }
}

/// One residual-class record: a hashed shape key plus the prior
/// `(q1_class_id, gamma2_class_id)` hit and a hit counter.
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub struct ResidualClassRecord {
    pub signature: crate::residual_families::signature::ShapeSignature,
    pub q1_class_id: Q1ClassId,
    pub gamma2_class_id: Gamma2ClassId,
    pub hits: u64,
}

impl ResidualClassRecord {
    #[must_use]
    pub fn new(
        signature: crate::residual_families::signature::ShapeSignature,
        q1_class_id: Q1ClassId,
        gamma2_class_id: Gamma2ClassId,
    ) -> Self {
        Self {
            signature,
            q1_class_id,
            gamma2_class_id,
            hits: 1,
        }
    }
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/residual_families/record.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:record:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::residual_families::signature::ShapeSignature;

    #[test]
    fn record_round_trip_fields() {
        let sig = ShapeSignature::from_bytes([7u8; 32]);
        let q1 = Q1ClassId::from_u64(0x1234_5678_9abc_def0);
        let g2 = Gamma2ClassId::from_u64(0x0fed_cba9_8765_4321);
        let rec = ResidualClassRecord::new(sig, q1, g2);
        assert_eq!(rec.signature, sig);
        assert_eq!(rec.q1_class_id, q1);
        assert_eq!(rec.gamma2_class_id, g2);
        assert_eq!(rec.hits, 1);
        assert_eq!(rec.q1_class_id.as_u64(), 0x1234_5678_9abc_def0);
        assert_eq!(rec.gamma2_class_id.as_u64(), 0x0fed_cba9_8765_4321);
    }
}

/// Checked hit ledger. The stored total equals the sum of the per-class counters.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClassHitLedger {
    classes: usize,
    total: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HitError {
    Empty,
    Bound,
    Zero,
    Overflow,
    Total,
}

impl std::fmt::Display for HitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            HitError::Empty => write!(formatter, "a hit ledger needs at least one class"),
            HitError::Bound => write!(formatter, "at most 64 hit rows are admitted"),
            HitError::Zero => write!(formatter, "a hit increment must be positive"),
            HitError::Overflow => write!(formatter, "the hit counter overflowed u64"),
            HitError::Total => write!(formatter, "the class sum does not equal the running total"),
        }
    }
}

impl std::error::Error for HitError {}

impl ClassHitLedger {
    pub fn record(pairs: &[(u64, u64)]) -> Result<Self, HitError> {
        if pairs.is_empty() {
            return Err(HitError::Empty);
        }
        if pairs.len() > 64 {
            return Err(HitError::Bound);
        }
        let mut map = std::collections::BTreeMap::<u64, u64>::new();
        let mut total: u64 = 0;
        for &(class_id, hits) in pairs {
            if hits == 0 {
                return Err(HitError::Zero);
            }
            let slot = map.entry(class_id).or_insert(0);
            *slot = slot.checked_add(hits).ok_or(HitError::Overflow)?;
            total = total.checked_add(hits).ok_or(HitError::Overflow)?;
        }
        let mut summed: u64 = 0;
        for value in map.values() {
            summed = summed.checked_add(*value).ok_or(HitError::Overflow)?;
        }
        if summed != total {
            return Err(HitError::Total);
        }
        Ok(Self {
            classes: map.len(),
            total,
        })
    }

    pub fn classes(&self) -> usize {
        self.classes
    }

    pub fn total(&self) -> u64 {
        self.total
    }
}

#[cfg(test)]
mod hit_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn duplicate_class_ids_add_and_the_total_matches() {
        let ledger = taken(ClassHitLedger::record(&[(1, 2), (1, 3), (4, 1)]));
        assert_eq!(ledger.classes(), 2);
        assert_eq!(ledger.total(), 6);
        assert!(ClassHitLedger::record(&[]).is_err());
    }
}
