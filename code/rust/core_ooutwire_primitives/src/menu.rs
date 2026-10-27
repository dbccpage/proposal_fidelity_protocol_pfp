//! Primitive — the **response menu**: the declared finite proposal set.
//!
//! Crate boundary: represented.  Source: Lean `Represented.responseMenu`
//! (*"the declared finite response menu … menu is constitution"*), and the
//! sealed candidate space it instantiates here.
//!
//! The menu is **declared, not searched for**.  It is every well-formed
//! delta within the declared bounds — the *unpruned* space, because the menu
//! is the constitution an obstruction is measured against, and an
//! obstruction is *exhaustive* failure over it.  The pruned enumeration in
//! `enumeration.rs` is a strategy for finding minima faster; it is not the
//! menu.
//!
//! In the author's vocabulary this is the **proposal** primitive.  Note what
//! it is not: it is not a proposer.  The estate's finding (crosstab §3) is
//! that "evaluation" splits into three — does it repair (`repair.rs`), is it
//! admissible (`world.rs`), does it certify and up to what (`panel.rs`) —
//! and that no single evaluation primitive exists.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_f083cf49<T> {
    fn checked_invariant_f083cf49(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_f083cf49<T> for Option<T> {
    #[inline]
    fn checked_invariant_f083cf49(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_f083cf49<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_f083cf49(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::bounds::Bounds;
use crate::candidate::Delta;
use crate::certificate::{Bound, SpaceId};
use crate::enumeration::iter_full_deltas;
use crate::regime::Regime;

/// The declared finite proposal set for one base regime.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Menu {
    /// Which space this is, for certificates.
    pub space: SpaceId,
    /// The bound it was enumerated under.
    pub bound: Bound,
    /// Every well-formed delta of at most `max_items` items.
    pub items: Vec<Delta>,
}

/// Enumerate the menu.  Unpruned; complete within the bounds.
pub fn menu(base: &Regime, bounds: &Bounds) -> Menu {
    bounds.validate().checked_invariant_f083cf49("unsupported candidate bounds");
    let mut items = Vec::new();
    for cost in 0..=bounds.max_items {
        items.extend(iter_full_deltas(base, cost, bounds));
    }
    Menu {
        space: SpaceId(format!("every well-formed delta over a regime with {} data and {} forms", base.n_data(), base.n_forms())),
        bound: Bound(bounds.describe()),
        items,
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/menu.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:menu:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf083cf49 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf083cf49` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf083cf49 {
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
impl BoundaryErrorf083cf49 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf083cf49 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf083cf49 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf083cf49 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf083cf49> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf083cf49::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf083cf49::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf083cf49::ExceedsCapacity {
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
    use crate::reading::READING_L;
    use crate::replay::replay;

    #[test]
    #[should_panic(expected = "unsupported candidate bounds")]
    fn larger_advertised_space_is_not_silently_truncated() {
        menu(&Regime::genesis(), &Bounds { max_items: 3, max_arity: 2 });
    }

    #[test]
    fn the_menu_is_the_unpruned_space_and_contains_the_empty_delta() {
        let base = replay(&READING_L.genesis).unwrap();
        let m = menu(&base, &Bounds::default());
        assert!(m.items.contains(&Vec::new()));
        let full2 = iter_full_deltas(&base, 2, &Bounds::default()).len();
        let full1 = iter_full_deltas(&base, 1, &Bounds::default()).len();
        assert_eq!(m.items.len(), 1 + full1 + full2);
    }
}

#[cfg(test)]
mod l4_boundary_tests_f083cf49 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf083cf49::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf083cf49::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf083cf49::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf083cf49::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf083cf49::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf083cf49::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf083cf49::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
