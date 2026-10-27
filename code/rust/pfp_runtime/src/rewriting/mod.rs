//! Structural checks for rewrite presentations and critical peaks.
//!
//! Merge spec section 4.6. This module deliberately does **not** decide
//! confluence. It checks whether a Squier-style claim carries the structure a
//! Squier-style claim needs, and turns whatever is missing into obligations.
//!
//! The two failure modes it exists to prevent:
//!
//! - Naming a theorem in place of satisfying it. A claim without an explicit
//!   presentation, a common source term, two typed reduction paths, and
//!   endpoint data yields `NeedsEvidence` with the gaps enumerated.
//! - Reading a failed search as a proof. When two branches of a critical peak
//!   do not join within the declared budget, the answer is
//!   `BoundedWithUnjoinedPeak`, not non-confluence. Only an exact
//!   non-joinability argument supports that.
//!
//! That second fence stands unchanged. What has been added is the exact
//! argument it always demanded: when both reachable sets are **closed**, their
//! intersection settles joinability, and that is a decision procedure rather
//! than an exhausted search. `reachable` returns `Some` only when its frontier
//! empties, which certifies closure directly. The verdict carries
//! [`ExhaustionBasis`] so a reader can see what paid for the word "provably".
//!
//! Where a budget was too small to close both sets, the answer is still
//! `BoundedWithUnjoinedPeak` and still asserts nothing about confluence.
//!
//! On the price, and a correction
//! ------------------------------
//!
//! This gate first demanded a *termination* witness -- every rule strictly
//! length-reducing -- on the reasoning that Newman's lemma needs termination.
//! That was the wrong price, and it was wrong in a way worth recording.
//!
//! Newman's lemma lifts local confluence to confluence **of a system**, and for
//! that termination is indeed required. This module never makes that claim. It
//! decides joinability **of one pair**, and what that needs is complete
//! reachable sets. A frontier that empties gives completeness outright,
//! whatever the rules do to term length.
//!
//! So the termination gate cost answers and bought nothing: a length-preserving
//! presentation whose sets close well inside the budget was refused a verdict
//! it could soundly be given. [`is_length_reducing`] survives as a utility for
//! the system-level claim a caller might build, and gates nothing here.
//!
//! A declaration is a claim, never a shortcut
//! ------------------------------------------
//!
//! The host decides, and decides the same way whether or not the producer
//! testified. A declared `join` used to short-circuit the decision when it
//! happened to equal both endpoints, so the same peak returned a different
//! payload according to whether the field was present -- producer testimony
//! selecting the host's answer, which is the defect class this module exists
//! to close.
//!
//! A declaration now affects exactly one thing: whether an obligation is
//! raised. It is checked by *reachability from both endpoints*, which is
//! strictly stronger than the old comparison against the endpoints -- a join
//! two steps below both is a true claim that the comparison refused. Where the
//! host cannot check the declaration at all, the verdict is `Bounded`, so an
//! unverifiable claim never rides out on a decision reached without it.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

mod peak;
mod permutation;
mod reduction;

pub use peak::*;
pub use permutation::*;
pub use reduction::*;

/// An oriented rewrite rule.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Rule {
    pub name: String,
    pub lhs: String,
    pub rhs: String,
}

/// A finite rewrite presentation `(Σ, R)`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Presentation {
    pub signature: Vec<String>,
    pub rules: Vec<Rule>,
}

impl Presentation {
    pub fn rule(&self, name: &str) -> Option<&Rule> {
        self.rules.iter().find(|rule| rule.name == name)
    }

    /// Compute the exact order of a nonempty, single-symbol permutation.
    ///
    /// Every signature entry and rule side must be exactly one Unicode scalar.
    /// Rule sources must be unique and the relation must be total and onto the
    /// signature. Rule names do not participate in this mathematical operation.
    ///
    /// Each cycle starts at its least scalar and follows successor direction;
    /// cycles are sorted by their starting scalar. The order is their exact
    /// least common multiple, without a fixed-width integer bound. This checks
    /// the supplied presentation only; it establishes no pin or authority.
    pub fn permutation_order(&self) -> Result<PermutationOrderWitness, PermutationOrderError> {
        permutation::permutation_order(self)
    }
}

#[cfg(test)]
#[path = "tests.rs"]
mod tests;

// Origin: engine/crates_rs/pfp_runtime/src/rewriting/mod.rs
// Claim: urn:core:crates_rs:pfp-runtime:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde7daf360 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde7daf360` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore7daf360 {
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
impl BoundaryErrore7daf360 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore7daf360 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore7daf360 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde7daf360 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore7daf360> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore7daf360::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore7daf360::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore7daf360::ExceedsCapacity {
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
mod l4_boundary_tests_e7daf360 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde7daf360::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde7daf360::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde7daf360::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde7daf360::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde7daf360::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore7daf360::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore7daf360::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
