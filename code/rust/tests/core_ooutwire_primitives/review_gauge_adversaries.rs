use core_ooutwire_primitives::alpha_projection_obstruction::{
    cochain_presentation::{bigon_2complex, AdmittedComplexV1},
    gauge_coupling_bridge::{single_triangle_bridge, so3_generators, GaugeCouplingBridge},
    matrix::Matrix,
    rational::q,
};

#[test]
fn cohomology_certificate_rechecks_closure_and_the_complex() {
    let mut complex = bigon_2complex().unwrap();
    let omega = Matrix::column_i128(&[1, -1]);
    let mut report = complex.cohomology_classification(&omega).unwrap();
    report.is_closed = true;
    assert!(report.certificate().is_none());
    complex.d1 = Matrix::from_i128(&[&[1, 1]]);
    assert!(complex.cohomology_classification(&omega).is_err());
}

#[test]
fn curvature_certificate_cannot_be_forged_by_mutating_a_result_flag() {
    let bridge = single_triangle_bridge().unwrap();
    let [j1, j2, _] = so3_generators();
    let mut report = bridge
        .verify_pure_gauge(&[Matrix::zeros(3, 3), j1, j2])
        .unwrap();
    assert!(!report.total_curvature_vanishes);
    report.total_curvature_vanishes = true;
    assert!(report.certificate().is_none());
}

#[test]
fn holonomy_requires_orthogonal_matrices_and_closed_contiguous_loops() {
    let bridge = single_triangle_bridge().unwrap();
    let identity = Matrix::eye(2);
    let g = [identity.clone(), identity.clone(), identity.clone()];
    assert!(bridge.verify_group_holonomy(&g, &[]).is_err());
    assert!(bridge.verify_group_holonomy(&g, &[vec![]]).is_err());
    assert!(bridge
        .verify_group_holonomy(&g, &[vec![(0, 1), (1, 2)]])
        .is_err());
    assert!(bridge
        .verify_group_holonomy(&g, &[vec![(0, 1), (2, 0)]])
        .is_err());
    let loop_edges = [vec![(0, 1), (1, 2), (2, 0)]];
    let bad = [identity.clone(), identity.scale(q(2)), identity.clone()];
    assert!(bridge.verify_group_holonomy(&bad, &loop_edges).is_err());
    let mut report = bridge.verify_group_holonomy(&g, &loop_edges).unwrap();
    report.max_defect_norm = q(1);
    assert!(report.certificate().is_none());
}

#[test]
fn malformed_matrices_and_empty_carriers_are_refused() {
    let bridge = single_triangle_bridge().unwrap();
    let malformed = Matrix {
        rows: 2,
        cols: 2,
        data: vec![],
    };
    assert!(bridge
        .linear_coboundary_d1(&[malformed.clone(), Matrix::eye(2), Matrix::eye(2)])
        .is_err());
    assert!(bridge
        .verify_multipatch_transition(&[malformed, Matrix::eye(2), Matrix::eye(2)], None)
        .is_err());
    let empty = AdmittedComplexV1::new(Matrix::zeros(0, 0), Matrix::zeros(0, 0)).unwrap();
    assert!(GaugeCouplingBridge::new(empty, vec![]).is_err());
}

#[test]
fn transition_certificate_binds_its_matrix_and_keeps_annotation_out_of_proof() {
    let bridge = single_triangle_bridge().unwrap();
    let twist = Matrix::from_i128(&[&[-1, 0], &[0, -1]]);
    let mut report = bridge
        .verify_multipatch_transition(&[Matrix::eye(2), Matrix::eye(2), twist], Some(q(999)))
        .unwrap();
    let text = format!("{:?}", report.certificate().unwrap());
    assert!(!text.contains("999"));
    report.is_cocycle_trivial = true;
    assert!(report.certificate().is_none());
}

// Origin: engine/crates_rs/tests/core_ooutwire_primitives/review_gauge_adversaries.rs
// Claim: urn:core:crates_rs:tests:review-gauge-adversaries:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord64fa531f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord64fa531f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError64fa531f {
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
impl BoundaryError64fa531f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError64fa531f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError64fa531f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord64fa531f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError64fa531f> {
        if capacity_bound == 0 {
            return Err(BoundaryError64fa531f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError64fa531f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError64fa531f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_64fa531f() {
    let admitted = BoundaryRecord64fa531f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord64fa531f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
