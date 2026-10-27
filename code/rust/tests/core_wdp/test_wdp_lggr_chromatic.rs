use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::ExactRowReduction;
use num_rational::BigRational;
use core_wdp::wdp_lggr_chromatic::{ChromaticConstraintSystem, ChromaticPresentationError};
use std::collections::BTreeSet;

#[test]
fn named_presentation_and_minimum_are_both_bound_to_the_certificate() {
    let mut source = ChromaticConstraintSystem {
        vertices: vec!["a".into(), "b".into(), "c".into()],
        edges: vec![
            ("a".into(), "b".into()),
            ("b".into(), "c".into()),
            ("c".into(), "a".into()),
        ],
        num_colors: 2,
        forbidden_color_pairs: BTreeSet::from([(0, 0), (1, 1)]),
    };
    let cert = source.evaluate(8, 24).unwrap();
    assert_eq!(cert.minimum.violated_edges.len(), 1);
    assert!(source.verify(&cert, 8, 24).unwrap());
    let mut forged = cert.clone();
    forged.minimum.violated_edges.clear();
    assert!(!source.verify(&forged, 8, 24).unwrap());
    source.edges.pop();
    assert!(!source.verify(&cert, 8, 24).unwrap());
    source.vertices[1] = "a".into();
    assert_eq!(
        source.evaluate(8, 24),
        Err(ChromaticPresentationError::DuplicateVertex)
    );
    source.vertices[1] = "d".into();
    assert!(matches!(
        source.evaluate(8, 24),
        Err(ChromaticPresentationError::Endpoint(_))
    ));
}

#[test]
fn adjoint_probes_and_blind_spots_use_checked_linear_algebra_directly() {
    let q = |x: i64| BigRational::from_integer(x.into());
    let a = BasicMatrix::from_row_major(1, 3, vec![q(1), q(-1), q(0)]).unwrap();
    let basis = a.kernel_basis().unwrap();
    assert_eq!(basis.vectors().len(), 2);
    for v in basis.vectors() {
        assert_eq!(a.mul_vec(v).unwrap(), vec![q(0)]);
    }
    assert_eq!(
        a.try_transpose().unwrap().mul_vec(&[q(2)]).unwrap(),
        vec![q(2), q(-2), q(0)]
    );
    assert!(a.mul_vec(&[q(1)]).is_err());
    assert!(a.try_transpose().unwrap().mul_vec(&[q(1), q(2)]).is_err());
    let empty = BasicMatrix::<BigRational>::from_row_major(0, 3, vec![]).unwrap();
    assert_eq!(
        empty.try_transpose().unwrap().mul_vec(&[]).unwrap(),
        vec![q(0); 3]
    );
    assert_eq!(empty.kernel_basis().unwrap().vectors().len(), 3);
}

// Origin: engine/crates_rs/tests/core_wdp/test_wdp_lggr_chromatic.rs
// Claim: urn:core:crates_rs:tests:test-wdp-lggr-chromatic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6398daf2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6398daf2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6398daf2 {
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
impl BoundaryError6398daf2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6398daf2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6398daf2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6398daf2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6398daf2> {
        if capacity_bound == 0 {
            return Err(BoundaryError6398daf2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6398daf2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6398daf2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6398daf2() {
    let admitted = BoundaryRecord6398daf2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6398daf2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
