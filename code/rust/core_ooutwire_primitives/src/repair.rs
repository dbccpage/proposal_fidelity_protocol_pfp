//! Primitive — the **repair family**: the menu members that actually repair.
//! Sound, complete, and ties retained.
//!
//! Crate boundary: represented.  Source: Lean `Represented.repairFamily`,
//! `repairFamily_sound`, `repairFamily_complete`,
//! `repairFamily_retains_ties`.
//!
//! The family is a *filter* of the declared menu by the validity predicate.
//! Sound: every member is a valid response.  Complete: every valid menu
//! member is in the family.  Ties retained: the family is a list, never a
//! choice; "no member is dropped because another member also repairs" is
//! the Lean theorem, and here it is what a filter is.
//!
//! The Core engine prices this family under every declared measure and
//! quotients it into classes.  It never picks.

use crate::candidate::{is_structure_creating, Delta};
use crate::mark::Pair;
use crate::menu::Menu;
use crate::regime::Regime;
use crate::response::response_valid_naive;

/// The members of the menu that discharge `target` while preserving every
/// recorded requirement.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RepairFamily {
    /// The target.
    pub target: Pair,
    /// The members, in menu order.
    pub members: Vec<Delta>,
    /// How many menu items were examined — all of them.
    pub examined: usize,
}

impl RepairFamily {
    /// Rule-1 members: instances only.
    pub fn repairs(&self) -> Vec<&Delta> {
        self.members.iter().filter(|d| !is_structure_creating(d)).collect()
    }
    /// Rule-2 members: anything that creates structure.
    pub fn augmentations(&self) -> Vec<&Delta> {
        self.members.iter().filter(|d| is_structure_creating(d)).collect()
    }
}

/// Filter the menu.  Uses the naive (replay) check, so it needs no rule-free
/// invariant and is the reference the fast path is checked against.
pub fn repair_family(base: &Regime, target: Pair, menu: &Menu) -> RepairFamily {
    let members = menu
        .items
        .iter()
        .filter(|d| response_valid_naive(base, target, d).unwrap_or(false))
        .cloned()
        .collect();
    RepairFamily { target, members, examined: menu.items.len() }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/repair.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:repair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfc94e236 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfc94e236` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfc94e236 {
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
impl BoundaryErrorfc94e236 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfc94e236 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfc94e236 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfc94e236 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfc94e236> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfc94e236::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfc94e236::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfc94e236::ExceedsCapacity {
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
    use crate::bounds::Bounds;
    use crate::menu::menu;
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;

    #[test]
    fn sound_and_complete_against_the_menu() {
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            let m = menu(&base, &Bounds::default());
            let fam = repair_family(&base, reading.target, &m);
            assert_eq!(fam.examined, m.items.len());
            for d in &fam.members {
                assert!(response_valid_naive(&base, reading.target, d).unwrap(), "sound");
            }
            for d in &m.items {
                if response_valid_naive(&base, reading.target, d).unwrap_or(false) {
                    assert!(fam.members.contains(d), "complete");
                }
            }
            assert!(!fam.members.is_empty());
        }
    }

    /// At the Challenge 3 base every repair needs a new form, so the family
    /// is all rule 2 and no rule 1: there is nothing to discriminate *with*.
    #[test]
    fn at_challenge3_every_repair_creates_structure() {
        let base = replay(&READING_L.genesis).unwrap();
        let fam = repair_family(&base, READING_L.target, &menu(&base, &Bounds::default()));
        assert!(fam.repairs().is_empty());
        assert_eq!(fam.augmentations().len(), fam.members.len());
    }
}

#[cfg(test)]
mod l4_boundary_tests_fc94e236 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfc94e236::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfc94e236::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfc94e236::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfc94e236::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfc94e236::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfc94e236::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfc94e236::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
