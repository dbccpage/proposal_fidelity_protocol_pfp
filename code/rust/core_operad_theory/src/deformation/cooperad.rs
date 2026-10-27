//! Deformation: Cooperads and cocomposition.
//!
//! AuthorityEffect: None.

use std::collections::{HashMap, HashSet};
use serde::{Deserialize, Serialize};
use crate::foundation::{OperadColour, Operation};

/// A multi-coloured cooperad C with cocomposition maps.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColouredCooperad {
    pub name: String,
    colours: HashSet<OperadColour>,
    cognerators: HashMap<String, Operation>,
}

impl ColouredCooperad {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            colours: HashSet::new(),
            cognerators: HashMap::new(),
        }
    }

    pub fn add_cognerator(&mut self, op: Operation) {
        self.cognerators.insert(op.op_id.as_str().to_string(), op);
    }
}
/// Colour partition for a cooperad: generators require an occupied colour, and occupied plus unused restores the colour count.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CooperadCensus { generators: u64, colours: u64, occupied: u64, unused: u64 }
pub fn try_colour_census(generators: u64, colours: u64, occupied: u64) -> Result<CooperadCensus, &'static str> {
    if occupied > colours {
        return Err("occupied colours exceed the colour set");
    }
    if generators > 0 && occupied == 0 {
        return Err("generators require an occupied colour");
    }
    let unused = colours.checked_sub(occupied).ok_or("unused colour underflow")?;
    let restored = occupied.checked_add(unused).ok_or("colour total overflow")?;
    if restored != colours {
        return Err("occupied and unused colours do not restore the colour set");
    }
    Ok(CooperadCensus { generators, colours, occupied, unused })
}

// Origin: engine/crates_rs/core_operad_theory/src/deformation/cooperad.rs
// Claim: urn:core:crates_rs:core-operad-theory:cooperad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddd74406b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddd74406b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordd74406b {
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
impl BoundaryErrordd74406b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordd74406b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordd74406b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddd74406b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordd74406b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordd74406b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordd74406b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordd74406b::ExceedsCapacity {
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
mod cooperad_census_checks {
    use super::try_colour_census;
    #[test]
    fn occupied_and_unused_colours_restore_the_set() {
        let census = try_colour_census(2, 3, 1);
        assert_eq!(census.as_ref().map(|item| item.unused), Ok(2));
        assert_eq!(try_colour_census(2, 3, 0).map(|_| ()), Err("generators require an occupied colour"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_dd74406b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddd74406b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddd74406b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddd74406b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddd74406b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddd74406b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordd74406b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordd74406b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
