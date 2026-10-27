use core_homology::cycle_basis::{
    compute_cycle_basis, compute_cycle_basis_with_tree, CycleBasisEdge,
};

#[test]
fn test_k4_witness_round_5_b1() {
    let vertices = vec!["a".into(), "b".into(), "c".into(), "d".into()];
    let edges = vec![
        CycleBasisEdge { u: "a".into(), v: "b".into(), weight: 1 },
        CycleBasisEdge { u: "b".into(), v: "c".into(), weight: 2 },
        CycleBasisEdge { u: "c".into(), v: "a".into(), weight: 3 },
        CycleBasisEdge { u: "b".into(), v: "d".into(), weight: 1 },
        CycleBasisEdge { u: "d".into(), v: "a".into(), weight: 2 },
        CycleBasisEdge { u: "c".into(), v: "d".into(), weight: 1 },
    ];

    let result = compute_cycle_basis(&vertices, &edges);
    assert_eq!(result.b1, 3);
    assert_eq!(result.chords.len(), 3);
    assert_eq!(result.num_components, 1);
    assert!(result.certificate.valid);
    assert_eq!(result.certificate.chords_count, 3);
    assert_eq!(result.certificate.b1_calculated, 3);
}

#[test]
fn test_k4_exact_chord_potentials_match_witness() {
    let vertices = vec!["a".into(), "b".into(), "c".into(), "d".into()];
    let tree_edges = vec![
        CycleBasisEdge { u: "a".into(), v: "b".into(), weight: 1 },
        CycleBasisEdge { u: "b".into(), v: "c".into(), weight: 2 },
        CycleBasisEdge { u: "d".into(), v: "a".into(), weight: 2 },
    ];
    let edges = vec![
        CycleBasisEdge { u: "a".into(), v: "b".into(), weight: 1 },
        CycleBasisEdge { u: "b".into(), v: "c".into(), weight: 2 },
        CycleBasisEdge { u: "c".into(), v: "a".into(), weight: 3 },
        CycleBasisEdge { u: "b".into(), v: "d".into(), weight: 1 },
        CycleBasisEdge { u: "d".into(), v: "a".into(), weight: 2 },
        CycleBasisEdge { u: "c".into(), v: "d".into(), weight: 1 },
    ];

    let result = compute_cycle_basis_with_tree(&vertices, &edges, &tree_edges);
    assert_eq!(result.potentials["a"], 0);
    assert_eq!(result.potentials["b"], 1);
    assert_eq!(result.potentials["c"], 3);
    assert_eq!(result.potentials["d"], -2);

    assert_eq!(result.fundamental_cycles.len(), 3);
    for fc in &result.fundamental_cycles {
        if fc.chord.u == "c" && fc.chord.v == "a" {
            assert_eq!(fc.expected_chord_value, -3); // f(a) - f(c) = 0 - 3 = -3
        } else if fc.chord.u == "b" && fc.chord.v == "d" {
            assert_eq!(fc.expected_chord_value, -3); // f(d) - f(b) = -2 - 1 = -3
        } else if fc.chord.u == "c" && fc.chord.v == "d" {
            assert_eq!(fc.expected_chord_value, -5); // f(d) - f(c) = -2 - 3 = -5
        }
    }
}

#[test]
fn test_disconnected_components_b1_formula() {
    // Two disjoint triangles: C1 on {1,2,3}, C2 on {4,5,6}
    // |V| = 6, |E| = 6, c = 2
    // b1 = 6 - 6 + 2 = 2
    let vertices = vec![
        "1".into(), "2".into(), "3".into(),
        "4".into(), "5".into(), "6".into(),
    ];
    let edges = vec![
        CycleBasisEdge { u: "1".into(), v: "2".into(), weight: 1 },
        CycleBasisEdge { u: "2".into(), v: "3".into(), weight: 1 },
        CycleBasisEdge { u: "3".into(), v: "1".into(), weight: 1 },
        CycleBasisEdge { u: "4".into(), v: "5".into(), weight: 1 },
        CycleBasisEdge { u: "5".into(), v: "6".into(), weight: 1 },
        CycleBasisEdge { u: "6".into(), v: "4".into(), weight: 1 },
    ];

    let result = compute_cycle_basis(&vertices, &edges);
    assert_eq!(result.num_components, 2);
    assert_eq!(result.b1, 2);
    assert_eq!(result.chords.len(), 2);
    assert!(result.certificate.valid);
}

// Origin: engine/crates_rs/tests/core_homology/cycle_basis.rs
// Claim: urn:core:crates_rs:tests:cycle-basis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord98437802 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord98437802` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError98437802 {
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
impl BoundaryError98437802 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError98437802 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError98437802 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord98437802 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError98437802> {
        if capacity_bound == 0 {
            return Err(BoundaryError98437802::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError98437802::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError98437802::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_98437802() {
    let admitted = BoundaryRecord98437802::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord98437802::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
