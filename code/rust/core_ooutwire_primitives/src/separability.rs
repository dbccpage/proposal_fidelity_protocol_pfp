//! Primitive — **internal separability**: two data are separable exactly
//! when their profiles differ.
//!
//! Crate boundary: coda-observe.  Source: `observe.py::separable`,
//! `witness`, `collapsed_pairs`, `satisfies`; sealed claim `CL-2-COLLAPSE`;
//! Lean `Inertia.collapsed_of_no_insts`.
//!
//! This is the *declared* meaning of internal separability in the sealed
//! derivation: behavioural separation by positive derivability.  The boundary
//! derivation declares a different one — no permitted automorphism carries
//! one mark to the other — and the comparison records that **no equivalence
//! between the two senses is proved** (`B3-REQUIREMENT`).  Two words, two
//! definitions, one file each.
//!
//! **`FW-ABSENCE`.**  A collapsed pair is a pair with *equal profiles*.  It
//! is not an equal pair.  The two tokens are distinct in the metatheory; the
//! object language simply has no context that tells them apart yet.
//! Absence of a separating test is never converted into equality.

use crate::context::{contexts, plug, Context};
use crate::mark::{Mark, Pair};
use crate::profile::{derivable, profile, profiles};
use crate::regime::Regime;

/// `≭` — do the two marks have different profiles?
pub fn separable(r: &Regime, i: Mark, j: Mark) -> bool {
    r.has_mark(i) && r.has_mark(j) && profile(r, i) != profile(r, j)
}

/// The first context, in the fixed order, at which the two marks differ.
/// `None` when the pair is collapsed.
pub fn witness(r: &Regime, i: Mark, j: Mark) -> Option<Context> {
    if !r.has_mark(i) || !r.has_mark(j) {
        return None;
    }
    contexts(r)
        .into_iter()
        .find(|c| derivable(r, &plug(c, i)) != derivable(r, &plug(c, j)))
}

/// All pairs `i < j` with equal profiles, lexicographically ordered.  These
/// are the unresolved separation demands the closure policy will reissue.
pub fn collapsed_pairs(r: &Regime) -> Vec<Pair> {
    let profs = profiles(r);
    let n = r.n_data();
    let mut out = Vec::new();
    for i in 0..n {
        for j in (i + 1)..n {
            if profs[i] == profs[j] {
                out.push(Pair::of(i, j));
            }
        }
    }
    out
}

/// Do all imposed requirements hold?
pub fn satisfies(r: &Regime) -> bool {
    let profs = profiles(r);
    r.reqs.iter().all(|p| profs[p.i.0] != profs[p.j.0])
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/separability.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:separability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfe9aad29 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfe9aad29` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfe9aad29 {
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
impl BoundaryErrorfe9aad29 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfe9aad29 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfe9aad29 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfe9aad29 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfe9aad29> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfe9aad29::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfe9aad29::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfe9aad29::ExceedsCapacity {
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
    use crate::replay::replay;

    /// Sealed Challenge 2, both readings: total observational collapse.
    /// L: one collapsed pair; F: three, with one observational class each.
    #[test]
    fn challenge2_collapse_is_total_in_both_readings() {
        let l = replay(&READING_L.genesis).unwrap();
        assert_eq!(collapsed_pairs(&l), vec![Pair::of(0, 1)]);
        let f = replay(&READING_F.genesis).unwrap();
        assert_eq!(collapsed_pairs(&f), vec![Pair::of(0, 1), Pair::of(0, 2), Pair::of(1, 2)]);
        for r in [&l, &f] {
            let profs = profiles(r);
            let classes: std::collections::BTreeSet<_> = profs.iter().collect();
            assert_eq!(classes.len(), 1);
        }
    }

    #[test]
    fn a_witness_exists_exactly_when_separable() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(witness(&base, Mark(0), Mark(1)).is_none());
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[0])).unwrap();
        assert!(separable(&r, Mark(0), Mark(1)));
        assert_eq!(witness(&r, Mark(0), Mark(1)).unwrap().slots, vec![None]);
        assert!(collapsed_pairs(&r).is_empty());
    }

    #[test]
    fn fw_absence_collapsed_is_not_equal() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(!separable(&base, Mark(0), Mark(1)));
        assert_ne!(base.data[0], base.data[1], "the tokens differ in the metatheory");
    }

    #[test]
    fn satisfies_reads_every_requirement() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(satisfies(&base), "no requirements, vacuously");
        let r = step(&base, &Event::Impose(Pair::of(0, 1))).unwrap();
        assert!(!satisfies(&r));
    }
}

#[cfg(test)]
mod l4_boundary_tests_fe9aad29 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfe9aad29::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfe9aad29::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfe9aad29::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfe9aad29::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfe9aad29::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfe9aad29::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfe9aad29::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
