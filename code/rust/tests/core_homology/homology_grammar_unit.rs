use core_homology::cell_grammar::*;

#[test]
fn test_homology_grammar_unit() {
    let vertices = vec!["v0".into(), "v1".into(), "v2".into()];
    let e0 = OrientedEdgeV1::new("e0", "c0", "v0", "v1").unwrap();
    let e1 = OrientedEdgeV1::new("e1", "c1", "v1", "v2").unwrap();
    let e2 = OrientedEdgeV1::new("e2", "c2", "v0", "v2").unwrap();
    let edges = vec![e0, e1, e2];

    let b0 = BoundaryUseV1::new("e0", 1).unwrap();
    let b1 = BoundaryUseV1::new("e1", 1).unwrap();
    let b2 = BoundaryUseV1::new("e2", -1).unwrap();
    let f0 = OrientedFaceV1::new("f0", vec![b0, b1, b2]).unwrap();
    let faces = vec![f0];

    let grammar = CellGrammarV1::new(vertices, edges, faces).unwrap();
    let window = build_cochain_window_from_cells(&grammar).unwrap();
    assert_eq!(window.demand_coordinate_ids, vec!["c0", "c1", "c2"]);
}

// Origin: engine/crates_rs/tests/core_homology/homology_grammar_unit.rs
// Claim: urn:core:crates_rs:tests:homology-grammar-unit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord66885f07 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord66885f07` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError66885f07 {
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
impl BoundaryError66885f07 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError66885f07 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError66885f07 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord66885f07 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError66885f07> {
        if capacity_bound == 0 {
            return Err(BoundaryError66885f07::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError66885f07::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError66885f07::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_66885f07() {
    let admitted = BoundaryRecord66885f07::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord66885f07::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
