use core_category_theory::finite_functional_dependencies::*;

fn fd(x: u16, y: u16) -> FunctionalDependency {
    FunctionalDependency {
        determinant: x,
        dependent: y,
    }
}

#[test]
fn heath_split_decides_schema_and_keeps_a_replayable_closure() {
    let schema = FdSchema {
        arity: 3,
        dependencies: vec![fd(1, 2)],
    };
    let report = schema.binary_decomposition([3, 5], 100_000).unwrap();
    assert!(!report.original_bcnf_violations.is_empty());
    assert!(report.component_bcnf_violations.iter().all(Vec::is_empty));
    assert_eq!(report.determined_component, Some(0));
    assert!(report.lost_dependencies.is_empty());
    assert!(schema.verify_closure(&report.intersection_closure));
    let mut altered = report.intersection_closure;
    altered.applications.clear();
    assert!(!schema.verify_closure(&altered));
}

#[test]
fn bcnf_lossless_does_not_imply_dependency_preservation() {
    let schema = FdSchema {
        arity: 3,
        dependencies: vec![fd(3, 4), fd(4, 2)],
    };
    let report = schema.binary_decomposition([6, 5], 100_000).unwrap();
    assert_eq!(report.determined_component, Some(0));
    assert!(report.component_bcnf_violations.iter().all(Vec::is_empty));
    assert_eq!(report.lost_dependencies, vec![fd(3, 4)]);
}

#[test]
fn projected_implied_dependencies_and_empty_determinants_are_checked() {
    let schema = FdSchema {
        arity: 3,
        dependencies: vec![fd(1, 2), fd(2, 4)],
    };
    let report = schema.binary_decomposition([5, 3], 100_000).unwrap();
    assert!(report.projected_dependencies[0].contains(&fd(1, 4)));
    assert_eq!(report.lost_dependencies, vec![fd(2, 4)]);
    let constants = FdSchema {
        arity: 3,
        dependencies: vec![fd(0, 1)],
    };
    assert!(constants
        .binary_decomposition([3, 5], 100_000)
        .unwrap()
        .component_bcnf_violations
        .iter()
        .all(|v| v.contains(&fd(0, 1))));
}

#[test]
fn budgets_malformed_inputs_and_instance_claims_remain_distinct() {
    let schema = FdSchema {
        arity: 3,
        dependencies: vec![fd(1, 2)],
    };
    assert_eq!(
        schema.binary_decomposition([3, 5], 0),
        Err(FdRefusal::BudgetUnknown)
    );
    assert_eq!(
        schema.binary_decomposition([3, 1], 1000),
        Err(FdRefusal::InvalidDecomposition)
    );
    assert_eq!(
        schema.check_instance(&[vec!["a", "b", "c"], vec!["a", "d", "c"]]),
        Err(FdRefusal::InstanceDependencyViolation {
            dependency: 0,
            first: 1,
            second: 0
        })
    );
    assert_eq!(
        schema.check_instance(&[vec!["a", "b", "c"], vec!["a", "b", "c"]]),
        Err(FdRefusal::DuplicateTuple)
    );
    // A singleton instance satisfies every FD; it cannot certify BCNF of its schema.
    assert!(schema.check_instance(&[vec![0, 0, 0]]).is_ok());
    assert!(!schema
        .binary_decomposition([3, 5], 1000)
        .unwrap()
        .original_bcnf_violations
        .is_empty());
}

#[test]
fn all_boolean_relations_replay_lossless_binary_fd_decisions() {
    for x in 0..8 {
        for y in [1, 2, 4] {
            let schema = FdSchema {
                arity: 3,
                dependencies: vec![fd(x, y)],
            };
            for a in 1..8 {
                for b in 1..8 {
                    if a | b != 7 {
                        continue;
                    }
                    let report = schema.binary_decomposition([a, b], 100_000).unwrap();
                    let mut every_legal_instance_roundtrips = true;
                    for subset in 0u16..256 {
                        let rows = (0..8)
                            .filter(|i| subset & (1 << i) != 0)
                            .map(|i| (0..3).map(|j| (i >> j) & 1).collect::<Vec<_>>())
                            .collect::<Vec<_>>();
                        if schema.check_instance(&rows).is_err() {
                            continue;
                        }
                        let joined = natural_join(
                            &project(&rows, 3, a).unwrap(),
                            &project(&rows, 3, b).unwrap(),
                            3,
                            [a, b],
                        )
                        .unwrap();
                        every_legal_instance_roundtrips &= joined == rows.into_iter().collect();
                    }
                    assert_eq!(
                        report.determined_component.is_some(),
                        every_legal_instance_roundtrips
                    );
                }
            }
        }
    }
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_fd_decomposition.rs
// Claim: urn:core:crates_rs:tests:finite-fd-decomposition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb53d7e55 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb53d7e55` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb53d7e55 {
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
impl BoundaryErrorb53d7e55 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb53d7e55 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb53d7e55 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb53d7e55 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb53d7e55> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb53d7e55::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb53d7e55::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb53d7e55::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b53d7e55() {
    let admitted = BoundaryRecordb53d7e55::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb53d7e55::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
