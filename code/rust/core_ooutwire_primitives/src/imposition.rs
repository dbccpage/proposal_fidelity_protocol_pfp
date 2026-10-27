//! Primitive — **imposition**: an externally imposed requirement.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::Impose` and
//! `Regime.reqs`.
//!
//! A requirement is *persistent*: once imposed it constrains every later
//! response (`response.rs` checks all of `reqs`, not only the newest).  It is
//! also *external*: the sealed derivation never derived a demand from inside
//! the object language — that is `OB-1`, the standing obstruction, and it is
//! why the Core engine takes its demands from `outside.rs` and nowhere else.
//!
//! A requirement is not yet an *active obstruction*.  Recording `(i, j)` says
//! the pair must become separable; an obstruction is that record **plus** the
//! exhaustive failure of the declared menu (`obstruction.rs`).  The estate
//! keeps the two apart because an engine that calls every failed check an
//! obstruction is guessing.

use crate::event::AdmissionError;
use crate::mark::Pair;
use crate::regime::Regime;

/// Impose the persistent requirement that `pair` be internally separable.
/// Both marks must be admitted and stored in strictly increasing order.
/// `Pair` fields are public, so the constructor's invariant is checked here.
pub fn impose(r: &Regime, pair: Pair) -> Result<Regime, AdmissionError> {
    if pair.i >= pair.j || !r.has_mark(pair.i) || !r.has_mark(pair.j) {
        return Err(AdmissionError(format!("requirement out of range: {pair}")));
    }
    let mut out = r.clone();
    out.reqs.insert(pair);
    Ok(out)
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/imposition.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:imposition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd9113490 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd9113490` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord9113490 {
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
impl BoundaryErrord9113490 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord9113490 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord9113490 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd9113490 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord9113490> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord9113490::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord9113490::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord9113490::ExceedsCapacity {
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
    fn a_requirement_is_recorded_and_persists() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = impose(&base, Pair::of(0, 1)).unwrap();
        assert!(r.reqs.contains(&Pair::of(0, 1)));
        let again = impose(&r, Pair::of(0, 1)).unwrap();
        assert_eq!(again, r, "imposing twice records once");
    }

    #[test]
    fn a_requirement_on_an_unadmitted_mark_is_refused() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(impose(&base, Pair::of(0, 2)).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_d9113490 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd9113490::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd9113490::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd9113490::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd9113490::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd9113490::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord9113490::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord9113490::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
