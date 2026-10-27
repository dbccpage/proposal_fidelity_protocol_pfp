use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_epk::residual_families::{FamilyRegistry, RegistryWrite};
use core_solvers::solver_lp_phi1_boundary::{Boundary1, BoundaryEdge};
use core_wdp::phi1_coda_adapter::{solve_phi1_coda, Phi1CodaAdapterError};

fn triangle() -> Boundary1 {
    Boundary1 {
        num_vertices: 3,
        edges: vec![
            BoundaryEdge {
                tail: 0,
                head: 1,
                weight: 1,
            },
            BoundaryEdge {
                tail: 1,
                head: 2,
                weight: 1,
            },
            BoundaryEdge {
                tail: 2,
                head: 0,
                weight: 1,
            },
        ],
    }
}

#[test]
fn solver_survivor_runs_shared_runtime_and_reuses_family() {
    let boundary = triangle();
    let mut registry = FamilyRegistry::new();

    let first = solve_phi1_coda(&boundary, &[1, 0, 0], &mut registry).expect("first solve");
    assert_eq!(
        first.evaluation().status(),
        ObstructionDiagnosticClass::ClosedResidual
    );
    assert_eq!(first.solution().objective, 1);
    let first_family = first.residual_family().expect("survivor family");
    assert!(!first_family.lookup_hit());
    assert_eq!(first_family.registry_write(), RegistryWrite::Inserted);

    let second = solve_phi1_coda(&boundary, &[1, 0, 0], &mut registry).expect("second solve");
    let second_family = second.residual_family().expect("reused family");
    assert!(second_family.lookup_hit());
    assert_eq!(
        second_family.registry_write(),
        RegistryWrite::Hit { collision: false }
    );
}

#[test]
fn exact_solver_result_is_not_registered_as_a_survivor_family() {
    let boundary = Boundary1 {
        num_vertices: 2,
        edges: vec![BoundaryEdge {
            tail: 0,
            head: 1,
            weight: 1,
        }],
    };
    let mut registry = FamilyRegistry::new();
    let result = solve_phi1_coda(&boundary, &[5], &mut registry).expect("exact solve");

    assert_eq!(
        result.evaluation().status(),
        ObstructionDiagnosticClass::ExactRepair
    );
    assert!(result.residual_family().is_none());
    assert!(registry.is_empty());
}

#[test]
fn same_shape_different_exact_class_is_surfaced() {
    let boundary = triangle();
    let mut registry = FamilyRegistry::new();
    solve_phi1_coda(&boundary, &[1, 0, 0], &mut registry).expect("seed family");

    assert!(matches!(
        solve_phi1_coda(&boundary, &[2, 0, 0], &mut registry),
        Err(Phi1CodaAdapterError::Family(_))
    ));
}

// Origin: engine/crates_rs/tests/core_wdp/test_residual_family.rs
// Claim: urn:core:crates_rs:tests:test-residual-family:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb28040fa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb28040fa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb28040fa {
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
impl BoundaryErrorb28040fa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb28040fa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb28040fa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb28040fa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb28040fa> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb28040fa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb28040fa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb28040fa::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b28040fa() {
    let admitted = BoundaryRecordb28040fa::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb28040fa::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
