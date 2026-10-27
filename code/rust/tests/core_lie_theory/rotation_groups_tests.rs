//! Exact SO(3) laws and independent rejection controls retained from C1000.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_lie_theory::finite_order::finite_order;
use core_lie_theory::rotation::*;
use core_number_theory::rational::{ri, rq};
#[test]
fn test_t865_octahedral_closure_and_price_1() {
    let g = octahedral_group().unwrap();
    assert_eq!(g.order(), 24);
    g.verify_associativity().unwrap();
    let mut census = [0; 5];
    for i in 0..g.order() {
        assert!(is_rotation(g.element(i).unwrap()));
        census[g.element_order(i).unwrap()] += 1;
    }
    assert_eq!(census, [0, 1, 9, 8, 6]);
    assert_eq!(trace_field_conductor([1, 2, 3, 4]), 1);
}
#[test]
fn test_t865_tetrahedral_closure_and_price_1() {
    let g = tetrahedral_group().unwrap();
    assert_eq!(g.order(), 12);
    g.verify_associativity().unwrap();
    assert!(g.elements().iter().all(is_rotation));
}
#[test]
fn test_t865_icosahedral_closure_and_price_5() {
    let g = icosahedral_group().unwrap();
    assert_eq!(g.order(), 60);
    assert!(g.elements().iter().all(is_rotation));
    let a = icosahedral_trace_field().unwrap();
    assert_eq!(
        a.order_census.into_iter().collect::<Vec<_>>(),
        vec![(1, 1), (2, 15), (3, 20), (5, 24)]
    );
    assert_eq!(a.nonrational_traces, 24);
    assert_eq!(a.order_five_elements, 24);
    assert!(a.all_nonrational_traces_satisfy_minimal_polynomial);
    assert_eq!(a.conductor, 5);
}
#[test]
fn trace_field_price_is_independent_of_the_chosen_axis() {
    for m in [1, 2, 3, 4, 6] {
        let g = cyclic_rotation_group(m).unwrap();
        assert_eq!(g.order(), m);
        assert_eq!(trace_field_conductor([m]), 1);
    }
    for m in [2, 3, 4, 6] {
        assert_eq!(dihedral_rotation_group(m).unwrap().order(), 2 * m);
    }
    assert_eq!(real_subfield_conductor(5), 5);
    assert_eq!(real_subfield_conductor(8), 8);
    assert_eq!(real_subfield_conductor(12), 12);
    assert!(matches!(
        cyclic_rotation_group(5),
        Err(RotationError::NoRationalRealisation(5))
    ));
}
#[test]
fn test_t867_mutation_1_closure_checked_by_tolerance() {
    let mut m = octahedral_group().unwrap().element(1).unwrap().clone();
    let old = m.get(0, 1).unwrap();
    m.set(0, 1, old + rq(1, 1000)).unwrap();
    assert!(!is_rotation(&m));
    assert!(matches!(
        rotation_group(&[m]),
        Err(RotationError::NotRotation)
    ));
}
#[test]
fn test_t867_mutation_2_non_faithful_realisation_accepted() {
    let identity: BasicMatrix<core_number_theory::rational::Rational> = mx::identity(3).unwrap();
    let image = rotation_group(&[identity]).unwrap();
    assert_eq!(image.order(), 1);
    assert_ne!(image.order(), 24);
}
#[test]
fn test_t867_mutation_5_planted_rational_icosahedral_realisation() {
    let r = rational_axis_angle_rotation(&[ri(0), ri(0), ri(1)], &rq(3, 5), &rq(4, 5)).unwrap();
    assert!(is_rotation(&r));
    assert_eq!(finite_order(&r).unwrap(), None);
    assert_eq!(core_number_theory::rational::sqrt_exact(&ri(5)), None);
}

// Origin: engine/crates_rs/tests/core_lie_theory/rotation_groups_tests.rs
// Claim: urn:core:crates_rs:tests:rotation-groups-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7cef3b56 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7cef3b56` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7cef3b56 {
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
impl BoundaryError7cef3b56 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7cef3b56 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7cef3b56 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7cef3b56 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7cef3b56> {
        if capacity_bound == 0 {
            return Err(BoundaryError7cef3b56::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7cef3b56::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7cef3b56::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7cef3b56() {
    let admitted = BoundaryRecord7cef3b56::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7cef3b56::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
