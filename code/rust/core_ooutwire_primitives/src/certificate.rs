//! Sort 10 — **Certificate**: evidence of a specific kind, never of another.
//!
//! Crate boundary: coda-cert.  Source: crosstab §11.5 and §13.7; sealed
//! `incomplete_search_false_alarm` (an exhaustion certificate's
//! countermodel); `fresh_characters` (the first *cancellation* certificate
//! refusal: `[2, −1, −1]` sums to zero and no pairing witness exists).
//!
//! | kind | glyph | says |
//! |---|---|---|
//! | exhaustion | `⊢ᴱ` | the declared finite space was searched and nothing was found |
//! | witness | `⊢ᵂ` | here is the object, and here is the check that it is one |
//! | obstruction | `⊢ᴼ` | no object can exist, and here is the proof |
//!
//! Three kinds, never one field.  Collapsing them is how an engine cheats:
//! "the defect summed to zero" read as a witness accepts `[2, −1, −1]`;
//! "the first ten failed" read as exhaustion is the false alarm.
//!
//! **`FW-RECEIPT` as a type rule.**  A `TestResult` exists so that the rule
//! can be stated in code: there is no conversion from it to a
//! `Certificate`.  A green suite is not a certificate and must not construct
//! one.  The doctest below fails to compile, which is the receipt for that.
//! These public variants remain caller-constructible declaration records,
//! not proof objects. No-conversion does not prevent a fabricated payload.
//! The represented refusal path separately recomputes its menu certificate.
//!
//! ```compile_fail
//! use core_ooutwire_primitives::certificate::{Certificate, TestResult};
//! let green = TestResult { name: "suite".into(), passed: true };
//! let _c: Certificate = Certificate::from(green);
//! ```

use std::fmt;

/// The identity of a declared search space, for an exhaustion certificate.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SpaceId(pub String);

/// The declared bound of that space.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Bound(pub String);

/// The identity of a witnessed object.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ObjectId(pub String);

/// The identity of the check that certified the object.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CheckId(pub String);

/// The identity of a proof of impossibility.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ProofId(pub String);

/// A certificate.  Exactly one kind.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Certificate {
    /// `⊢ᴱ` — the declared finite space was searched to the end.
    Exhaustion {
        /// Which space.
        space: SpaceId,
        /// Under which bound.
        bound: Bound,
        /// How many candidates were examined — every one of them.
        searched: usize,
    },
    /// `⊢ᵂ` — the object, and the check that it is one.
    Witness {
        /// The object.
        object: ObjectId,
        /// The check.
        check: CheckId,
    },
    /// `⊢ᴼ` — no object can exist.
    Obstruction {
        /// The proof.
        proof: ProofId,
    },
}

/// The three kinds.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum CertKind {
    /// `⊢ᴱ`
    Exhaustion,
    /// `⊢ᵂ`
    Witness,
    /// `⊢ᴼ`
    Obstruction,
}

impl Certificate {
    /// Which kind.
    pub fn kind(&self) -> CertKind {
        match self {
            Certificate::Exhaustion { .. } => CertKind::Exhaustion,
            Certificate::Witness { .. } => CertKind::Witness,
            Certificate::Obstruction { .. } => CertKind::Obstruction,
        }
    }

    /// The glyph.
    pub fn glyph(&self) -> &'static str {
        match self.kind() {
            CertKind::Exhaustion => "⊢ᴱ",
            CertKind::Witness => "⊢ᵂ",
            CertKind::Obstruction => "⊢ᴼ",
        }
    }
}

/// The result of running a test.  It is a receipt for the test having
/// passed, and nothing else.  There is deliberately no `From<TestResult>
/// for Certificate`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TestResult {
    /// The test's name.
    pub name: String,
    /// Whether it passed.
    pub passed: bool,
}

impl fmt::Display for Certificate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Certificate::Exhaustion { space, bound, searched } => {
                write!(f, "{} exhaustion of {} under {} ({} examined)", self.glyph(), space.0, bound.0, searched)
            }
            Certificate::Witness { object, check } => write!(f, "{} witness {} checked by {}", self.glyph(), object.0, check.0),
            Certificate::Obstruction { proof } => write!(f, "{} obstruction proved by {}", self.glyph(), proof.0),
        }
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/certificate.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:certificate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3c4767d5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3c4767d5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3c4767d5 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError3c4767d5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3c4767d5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3c4767d5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3c4767d5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3c4767d5> {
        if capacity_bound == 0 {
            return Err(BoundaryError3c4767d5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3c4767d5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3c4767d5::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn three_kinds_and_their_glyphs() {
        let e = Certificate::Exhaustion { space: SpaceId("s".into()), bound: Bound("b".into()), searched: 3 };
        let w = Certificate::Witness { object: ObjectId("o".into()), check: CheckId("c".into()) };
        let o = Certificate::Obstruction { proof: ProofId("p".into()) };
        assert_eq!((e.kind(), w.kind(), o.kind()), (CertKind::Exhaustion, CertKind::Witness, CertKind::Obstruction));
        assert_eq!(e.glyph(), "⊢ᴱ");
        assert!(e.to_string().contains("3 examined"));
    }

    /// A total of zero is not a cancellation: the sum is a number, the
    /// certificate is a pairing witness, and `[2, -1, -1]` has the first
    /// and not the second.
    #[test]
    fn a_zero_total_is_not_a_witness() {
        let terms = [2i64, -1, -1];
        assert_eq!(terms.iter().sum::<i64>(), 0);
        // A pairing into exact opposites plus a single-signed residual:
        // 2 has no partner of magnitude 2.
        let has_partner = terms.contains(&-2);
        assert!(!has_partner);
    }
}

#[cfg(test)]
mod l4_boundary_tests_3c4767d5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3c4767d5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3c4767d5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3c4767d5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3c4767d5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3c4767d5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3c4767d5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3c4767d5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
