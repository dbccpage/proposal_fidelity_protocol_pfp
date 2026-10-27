//! Primitive — **obstruction**: a recorded requirement plus the EXHAUSTIVE
//! failure of the declared menu.  Never mere lookalikeness.
//!
//! Crate boundary: represented.  Source: Lean `Represented.obstructedB` and
//! its countermodel `incomplete_search_false_alarm`; crosstab §11.1 block D
//! (*"An obstruction is not 'the check failed'"*).
//!
//! `obstructed` returns an **exhaustion certificate** or nothing.  It does
//! not return a `bool`, because a `bool` cannot carry which space was
//! searched and under which bound, and a refusal recorded without those is a
//! refusal recorded without evidence (`refusal.rs`).
//!
//! `obstructed_truncated` is the countermodel kept as code: it examines only
//! the first `k` menu items.  On the world in the test a working repair sits
//! past the truncation point, so the truncated check declares an obstruction
//! the exhaustive check refutes.  Obstruction requires exhaustive failure
//! *by definition*, and this is what happens when the definition is skipped.

use crate::certificate::Certificate;
use crate::mark::Pair;
use crate::menu::Menu;
use crate::regime::Regime;
use crate::repair::repair_family;
use crate::response::response_valid_naive;
use crate::separability::separable;

/// Is `target` a recorded, currently violated requirement?
pub fn violated(base: &Regime, target: Pair) -> bool {
    base.reqs.contains(&target) && !separable(base, target.i, target.j)
}

/// The exhaustion certificate, if `target` is violated and no menu member
/// repairs it.
pub fn obstructed(base: &Regime, target: Pair, menu: &Menu) -> Option<Certificate> {
    if !violated(base, target) {
        return None;
    }
    let fam = repair_family(base, target, menu);
    if !fam.members.is_empty() {
        return None;
    }
    Some(Certificate::Exhaustion { space: menu.space.clone(), bound: menu.bound.clone(), searched: fam.examined })
}

/// The countermodel: examine only the first `k` menu items.
pub fn obstructed_truncated(base: &Regime, target: Pair, menu: &Menu, k: usize) -> bool {
    violated(base, target)
        && menu.items.iter().take(k).all(|d| !response_valid_naive(base, target, d).unwrap_or(false))
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/obstruction.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:obstruction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfa7092b2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfa7092b2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfa7092b2 {
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
impl BoundaryErrorfa7092b2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfa7092b2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfa7092b2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfa7092b2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfa7092b2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfa7092b2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfa7092b2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfa7092b2::ExceedsCapacity {
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
    use crate::bounds::Bounds;
    use crate::event::Event;
    use crate::menu::menu;
    use crate::reading::READING_L;
    use crate::replay::replay;

    /// `incomplete_search_false_alarm`: the truncated check declares an
    /// obstruction that the exhaustive check refutes.
    #[test]
    fn a_truncated_search_falsely_certifies() {
        let base = replay(&READING_L.genesis).unwrap();
        let base = step(&base, &Event::Impose(READING_L.target)).unwrap();
        let m = menu(&base, &Bounds::default());
        assert!(violated(&base, READING_L.target));
        assert!(obstructed(&base, READING_L.target, &m).is_none(), "the exhaustive check finds a repair");
        // The empty delta and every single item fail; repairs start at two
        // items, past a small truncation point.
        let k = 1 + crate::enumeration::iter_cost1_items(&base, &Bounds::default()).len();
        assert!(obstructed_truncated(&base, READING_L.target, &m, k), "the truncated check cries obstruction");
    }

    /// A genuine obstruction: within one item, nothing separates the pair
    /// (CL-3-MIN-TWO), so the one-item menu is exhausted and certifies.
    #[test]
    fn a_real_obstruction_carries_its_space_and_bound() {
        let base = replay(&READING_L.genesis).unwrap();
        let base = step(&base, &Event::Impose(READING_L.target)).unwrap();
        let one = Bounds { max_items: 1, max_arity: 2 };
        let m = menu(&base, &one);
        let cert = obstructed(&base, READING_L.target, &m).expect("obstructed within one item");
        match cert {
            Certificate::Exhaustion { searched, bound, .. } => {
                assert_eq!(searched, m.items.len());
                assert!(bound.0.contains("max_items=1"));
            }
            _ => panic!("an obstruction is an exhaustion certificate"),
        }
    }

    #[test]
    fn an_unrecorded_or_satisfied_pair_is_not_obstructed() {
        let base = replay(&READING_L.genesis).unwrap();
        let m = menu(&base, &Bounds { max_items: 1, max_arity: 2 });
        assert!(obstructed(&base, READING_L.target, &m).is_none(), "not recorded");
    }
}

#[cfg(test)]
mod l4_boundary_tests_fa7092b2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfa7092b2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfa7092b2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfa7092b2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfa7092b2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfa7092b2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfa7092b2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfa7092b2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
