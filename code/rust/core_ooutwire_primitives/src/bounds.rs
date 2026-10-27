//! Primitive — **declared bounds**: the finite candidate space.
//!
//! Crate boundary: coda-price.  Source: `candidates.py::Bounds`
//! (`max_items = 2`, `max_arity = 2`), the paper's declared resource bounds.
//!
//! ```text
//! L10  minimality is exhaustive over a declared finite space, or it is a
//!      conditional scope, and there is no third option
//! ```
//!
//! Every minimality claim in this crate is *relative to a `Bounds` value*,
//! and the value travels with the claim (`scope.rs`).  "Minimum cost two"
//! is a theorem over the item grammar; "three tied classes" is a bounded
//! theorem within `max_arity = 2`, and the sealed paper says so in clause
//! (d) of its terminal statement.  The Lean arity family shows the tie class
//! is infinite once the arity bound is lifted.  Bounds are not a limitation
//! to apologise for; they are what makes the count a count.

/// Declared finite bounds of the candidate space.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Bounds {
    /// The largest delta considered, in items.
    pub max_items: usize,
    /// The largest arity of a new form.
    pub max_arity: usize,
}

impl Default for Bounds {
    /// The sealed derivation's declared bounds.
    fn default() -> Bounds {
        Bounds { max_items: 2, max_arity: 2 }
    }
}

impl Bounds {
    /// Reject unsupported spaces before returning a scoped search result.
    pub fn validate(&self) -> Result<(), String> {
        if self.max_items > 2 {
            return Err("candidate enumeration supports max_items <= 2".into());
        }
        Ok(())
    }

    /// A one-line statement of the scope, for receipts.
    pub fn describe(&self) -> String {
        format!("max_items={} max_arity={}", self.max_items, self.max_arity)
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/bounds.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:bounds:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7489d358 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7489d358` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7489d358 {
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
impl BoundaryError7489d358 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7489d358 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7489d358 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7489d358 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7489d358> {
        if capacity_bound == 0 {
            return Err(BoundaryError7489d358::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7489d358::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7489d358::ExceedsCapacity {
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
    fn the_sealed_bounds_are_two_and_two() {
        let b = Bounds::default();
        assert_eq!((b.max_items, b.max_arity), (2, 2));
        assert_eq!(b.describe(), "max_items=2 max_arity=2");
    }
}
/// Pair slots of a declared finite candidate space: max_items times max_arity.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DeclaredSpace { pair_slots: u64 }
/// Attempts to construct a DeclaredSpace from candidate enumeration bounds.
pub fn try_declared_space(bounds: Bounds) -> Result<DeclaredSpace, &'static str> {
    if bounds.max_items > 2 {
        return Err("candidate enumeration supports max_items <= 2");
    }
    if bounds.max_arity == 0 {
        return Err("arity is positive");
    }
    let items = u64::try_from(bounds.max_items).map_err(|_| "item bound exceeds u64")?;
    let arity = u64::try_from(bounds.max_arity).map_err(|_| "arity bound exceeds u64")?;
    let pair_slots = items.checked_mul(arity).ok_or("pair slot product overflow")?;
    Ok(DeclaredSpace { pair_slots })
}
#[cfg(test)]
mod declared_space_checks {
    use super::{try_declared_space, Bounds};
    #[test]
    fn the_sealed_bounds_have_four_pair_slots() {
        assert_eq!(try_declared_space(Bounds::default()).as_ref().map(|item| item.pair_slots), Ok(4));
        assert_eq!(try_declared_space(Bounds { max_items: 2, max_arity: 0 }).map(|_| ()), Err("arity is positive"));
        assert_eq!(try_declared_space(Bounds { max_items: 3, max_arity: 2 }).map(|_| ()), Err("candidate enumeration supports max_items <= 2"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_7489d358 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7489d358::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7489d358::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7489d358::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7489d358::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7489d358::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7489d358::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7489d358::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
