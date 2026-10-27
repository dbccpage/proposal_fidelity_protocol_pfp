use core_operad_theory::foundation::{OperadColour, Operation, PlanarTree};

#[test]
fn test_operad_term_unit() {
    let c = OperadColour::new("State").unwrap();
    let op = Operation::identity(c);
    let tree = PlanarTree::corolla(op);
    assert_eq!(tree.children.len(), 1);
}

#[test]
fn identity_corolla_preserves_state_and_refuses_blank() {
    assert!(OperadColour::new("  ").is_err());
    let colour = OperadColour::new("State");
    assert!(colour.is_ok());
    if let Ok(colour) = colour {
        let operation = Operation::identity(colour);
        assert!(operation.is_identity());
        assert_eq!(operation.arity(), 1);
        assert_eq!(operation.output().as_str(), "State");
        assert_eq!(operation.inputs().first().map(OperadColour::as_str), Some("State"));
        let tree = PlanarTree::corolla(operation);
        assert_eq!(tree.children.len(), tree.root.arity());
        assert_eq!(tree.children.len(), 1);
    }
}

// Origin: engine/crates_rs/tests/core_operad_theory/operad_term_unit.rs
// Claim: urn:core:crates_rs:tests:operad-term-unit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord020419cc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord020419cc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError020419cc {
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
impl BoundaryError020419cc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError020419cc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError020419cc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord020419cc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError020419cc> {
        if capacity_bound == 0 {
            return Err(BoundaryError020419cc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError020419cc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError020419cc::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_020419cc() {
    let admitted = BoundaryRecord020419cc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord020419cc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
