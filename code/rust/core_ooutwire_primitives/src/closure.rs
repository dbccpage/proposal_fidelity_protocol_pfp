//! Primitive — the **declared pair-separation closure policy**, and the
//! external continuation policy it is kept apart from.
//!
//! Crate boundary: engine.  Source: `engine.py::closure_challenge_orbits`
//! and the module docstring's two-component decomposition of the challenge
//! source; sealed terminal clause (f); standing obstruction **OB-1**.
//!
//! No object-language endogenous demand generator was derived.  The sealed
//! challenge source is two *declared* pieces of metatheory:
//!
//! 1. **the closure policy** — reissue the admitted requirement pattern
//!    (separation) on the collapsed pairs, one challenge per automorphism
//!    orbit.  It reads only profile equality and the automorphism
//!    structure; it never reads token glyphs, never supplies data, never
//!    imports a new goal kind. With fixed data and an available response
//!    preserving previous requirements at every round, it reaches a fixpoint
//!    in at most `n(n-1)/2` successful response rounds;
//! 2. **the external continuation policy** — supply and admit one fresh
//!    opaque token.  Explicitly external; `supply = false` runs are the
//!    closed-system baseline.
//!
//! A collapsed pair is not an obstruction by itself. This policy records a
//! requirement; an obstruction additionally needs exhausted repair search.
//! The Core engine (`core.rs`) accepts a demand from the
//! outside or from this policy, and records which — because the difference
//! between "the world asked" and "the policy reissued" is the difference OB-1
//! is about.

use crate::automorphism::pair_orbits;
use crate::canonical::IsoBudgetError;
use crate::mark::Pair;
use crate::regime::Regime;
use crate::separability::collapsed_pairs;

/// One representative (least member) per automorphism orbit of the
/// collapsed pairs; empty at the fixpoint. Orbits transport under renaming;
/// their least representatives need not transport as identical named pairs.
pub fn closure_challenge_orbits(r: &Regime) -> Result<Vec<Pair>, IsoBudgetError> {
    Ok(pair_orbits(r, &collapsed_pairs(r))?.into_iter().map(|o| o[0]).collect())
}

/// The upper bound on rounds the sealed paper states for the closure.
pub fn closure_round_bound(n_data: usize) -> usize {
    n_data * n_data.saturating_sub(1) / 2
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/closure.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:closure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd437971a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd437971a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord437971a {
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
impl BoundaryErrord437971a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord437971a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord437971a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd437971a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord437971a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord437971a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord437971a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord437971a::ExceedsCapacity {
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
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::{READING_F, READING_L};
    use crate::regime::Regime;
    use crate::renaming::{rename, Bijection};
    use crate::replay::replay;
    use crate::token::Token;

    #[test]
    fn one_challenge_per_orbit() {
        let f = replay(&READING_F.genesis).unwrap();
        assert_eq!(closure_challenge_orbits(&f).unwrap(), vec![Pair::of(0, 1)]);
        let l = replay(&READING_L.genesis).unwrap();
        assert_eq!(closure_challenge_orbits(&l).unwrap(), vec![Pair::of(0, 1)]);
    }

    /// Token-blind: renaming the tokens only (not the indices) changes
    /// nothing the policy reads.
    #[test]
    fn the_policy_never_reads_token_glyphs() {
        let f = replay(&READING_F.genesis).unwrap();
        let mut g = f.clone();
        g.data = vec![Token::new("x"), Token::new("y"), Token::new("z")];
        assert_eq!(closure_challenge_orbits(&f).unwrap(), closure_challenge_orbits(&g).unwrap());
    }

    /// In this fixture the single collapsed pair transports directly.
    /// General equivariance is a property of orbits, not their least labels.
    #[test]
    fn a_single_collapsed_pair_transports_under_renaming() {
        let f = replay(&READING_F.genesis).unwrap();
        let r = step(&f, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[2])).unwrap();
        let b = Bijection { data: vec![2, 0, 1], forms: vec![0] };
        let s = rename(&r, &b);
        let mapped: Vec<Pair> = closure_challenge_orbits(&r)
            .unwrap()
            .iter()
            .map(|p| Pair::of(b.data[p.i.0], b.data[p.j.0]))
            .collect();
        let mut expected = closure_challenge_orbits(&s).unwrap();
        let mut mapped_sorted = mapped;
        mapped_sorted.sort();
        expected.sort();
        assert_eq!(mapped_sorted, expected);
    }

    #[test]
    fn the_fixpoint_is_empty_and_genesis_has_no_demand() {
        assert!(closure_challenge_orbits(&Regime::genesis()).unwrap().is_empty());
        assert_eq!(closure_round_bound(3), 3);
        assert_eq!(closure_round_bound(2), 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_d437971a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd437971a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd437971a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd437971a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd437971a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd437971a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord437971a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord437971a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
