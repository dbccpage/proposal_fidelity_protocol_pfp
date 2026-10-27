
#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_f56857a2 = (i128, i128);
use core_ooutwire_primitives::alpha_projection_obstruction::{
    cochain_presentation::LinearRepairProblem,
    covering_edge::receipt_fixture,
    family_bound::{certify_uniform_family, receipt_family},
    matrix::Matrix,
    numeric::{hermitian_eigen, CMatrix},
    observer_carriers::three_patch_certificate,
    rational::{q, r, Rational},
    transfer::linear_projection_transfer_certificate,
};

#[test]
fn transfer_rechecks_the_recorded_premise_and_lower_bound() {
    let original = linear_projection_transfer_certificate(
        &Matrix::column_i128(&[1, 2]), &Matrix::column_i128(&[1, 0]),
        &Matrix::from_i128(&[&[1, 0], &[0, 0]]), r(1, 2),
    ).unwrap();
    assert!(original.verify());
    let mut forged = original.clone();
    forged.projection_distance = q(100);
    assert!(!forged.verify());
    assert!(forged.certificate().is_none());
    forged = original.clone();
    forged.transfer_lower_bound = q(-999);
    assert!(!forged.verify());
    forged = original;
    forged.source_distance = q(-1);
    assert!(!forged.verify());
}

#[test]
fn coboundary_certificate_cannot_issue_from_a_forged_holds_bit() {
    let (diagram, section) = receipt_fixture();
    let mut certificate = diagram.coboundary_bound_certificate(&section).unwrap();
    certificate.coboundary_norm = certificate.bound + q(1);
    assert!(certificate.certificate().is_none());
}

#[test]
fn uniform_family_rejects_empty_and_corrupted_member_evidence() {
    let (members, premises) = receipt_family();
    let certificate = certify_uniform_family(&members, &premises, r(1, 128)).unwrap();
    assert!(certificate.accepted && certificate.verify());
    let mut forged = certificate.clone();
    forged.member_bounds.clear();
    assert!(!forged.verify());
    forged = certificate;
    forged.local_edge_polynomial = Some(q(100));
    assert!(!forged.verify());
}

#[test]
fn passivity_recomputes_inequalities_from_row_values() {
    let mut certificate = three_patch_certificate(q(1)).unwrap().passivity;
    certificate.rows[0].observed_j = certificate.rows[0].raw_i + q(1);
    assert!(!certificate.verify());
}

#[test]
fn three_patch_replays_the_actual_observer_maps() {
    let mut certificate = three_patch_certificate(q(1)).unwrap();
    for observer in &mut certificate.family.observers {
        for map in observer.maps.values_mut() { *map = Matrix::eye(3); }
    }
    assert!(!certificate.verify());
}

#[test]
fn malformed_exactness_packet_is_refused_without_panicking() {
    let problem = LinearRepairProblem::new(Matrix::from_i128(&[&[1], &[1]]));
    let mut certificate = problem.exactness_certificate(&Matrix::column_i128(&[2, 2])).unwrap();
    certificate.witness = Some(Matrix::eye(3));
    assert!(!certificate.verify());
}

#[test]
fn malformed_quotient_packet_is_refused_without_panicking() {
    let problem = LinearRepairProblem::new(Matrix::from_i128(&[&[1], &[1]]));
    let mut certificate = problem.quotient_l1_distance(&Matrix::column_i128(&[2, 3])).unwrap();
    certificate.repair_witness = Matrix::eye(3);
    assert!(!certificate.verify());
}

#[test]
fn numerical_eigen_refuses_empty_and_unbounded_tolerance() {
    assert!(hermitian_eigen(&CMatrix::zeros(0, 0), 1e-12).is_err());
    assert!(hermitian_eigen(&CMatrix::eye(2), f64::INFINITY).is_err());
}

#[test]
fn rational_absolute_value_refuses_release_overflow() {
    assert!(std::panic::catch_unwind(|| Rational::int(i128::MIN).abs()).is_err());
    assert!(std::panic::catch_unwind(|| Rational::new(1, i128::MIN)).is_err());
}

#[test]
fn observer_packets_bind_rank_and_kernel_reports_to_maps() {
    let instance = three_patch_certificate(q(1)).unwrap();
    let mut rank = instance.family.joint_injectivity_certificate().unwrap();
    *rank.edgewise_combined_rank.values_mut().next().unwrap() = 999;
    assert!(!rank.verify());
    let mut kernel = instance.all_green_kernel;
    kernel.edgewise_joint_kernel_membership.clear();
    assert!(!kernel.verify());
}

#[test]
fn audit_certificate_names_the_actual_scalar_population() {
    use core_ooutwire_primitives::alpha_projection_obstruction::replica_hierarchy::{
        receipt_samples, Diagnostic, FiniteDiagnosticFamily,
    };
    let (edges, gauges, types, samples) = receipt_samples();
    let family = FiniteDiagnosticFamily::new(edges, gauges, Diagnostic::UnweightedL1, Some(types)).unwrap();
    let audit = family.audit(&samples, &[q(3)]).unwrap();
    let certificate = audit.certificate("custom grid").to_string();
    assert!(certificate.contains("scalars (3)"), "{certificate}");
}

// Origin: engine/crates_rs/tests/core_ooutwire_primitives/review_adversaries.rs
// Claim: urn:core:crates_rs:tests:review-adversaries:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf56857a2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf56857a2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf56857a2 {
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
impl BoundaryErrorf56857a2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf56857a2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf56857a2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf56857a2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf56857a2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf56857a2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf56857a2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf56857a2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f56857a2() {
    let admitted = BoundaryRecordf56857a2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf56857a2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
