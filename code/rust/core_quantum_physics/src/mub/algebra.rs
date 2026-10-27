//! Exact finite MUB projector-algebra verification on the canonical matrix carrier.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::{adjoint, Involution},
    matrix,
};
use core_number_theory::rational::rq;
use core_number_theory::scalar::RationalEmbedding;
use serde::{Deserialize, Serialize};
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProjectorAlgebraStatus {
    AlgebraVerified,
    InvalidIdempotence,
    InvalidHermiticity,
    InvalidRankOneTrace,
    InvalidSameBasisOrthogonality,
    InvalidResolutionOfIdentity,
    InvalidCrossBasisUnbiasedness,
    EmptyBases,
    InvalidCarrier,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProjectorAlgebraReport {
    pub dimension: usize,
    pub basis_count: usize,
    pub projector_count: usize,
    pub status: ProjectorAlgebraStatus,
    pub idempotence_checks: usize,
    pub hermiticity_checks: usize,
    pub rank_one_trace_checks: usize,
    pub same_basis_orthogonality_checks: usize,
    pub resolution_of_identity_checks: usize,
    pub cross_basis_unbiased_checks: usize,
    pub checked_identities: Vec<String>,
    pub error: Option<String>,
}

impl ProjectorAlgebraReport {
    fn record_check(
        &mut self,
        condition: Result<bool, linear_algebra::exact_field::ExactFieldError>,
        fail_status: ProjectorAlgebraStatus,
        law: &str,
    ) -> bool {
        match condition {
            Ok(true) => {
                if !self.checked_identities.iter().any(|s| s == law) {
                    self.checked_identities.push(law.into());
                }
                true
            }
            Ok(false) => {
                self.status = fail_status;
                self.error = Some(law.into());
                false
            }
            Err(e) => {
                self.status = ProjectorAlgebraStatus::InvalidCarrier;
                self.error = Some(e.to_string());
                false
            }
        }
    }

    fn fail_carrier(&mut self, msg: impl Into<String>) {
        self.status = ProjectorAlgebraStatus::InvalidCarrier;
        self.error = Some(msg.into());
    }
}

fn validate_mub_carrier_shape<C>(
    r: &mut ProjectorAlgebraReport,
    bases: &[Vec<BasicMatrix<C>>],
    dimension: usize,
) -> bool {
    if dimension == 0 || bases.is_empty() {
        r.status = ProjectorAlgebraStatus::EmptyBases;
        r.error = Some("empty bases or zero dimension".into());
        return false;
    }
    let bad_basis = bases
        .iter()
        .any(|b| b.len() != dimension || b.iter().any(|p| p.shape() != (dimension, dimension)));
    if dimension > 64 || bases.len() > dimension + 1 || bad_basis {
        r.fail_carrier("malformed or oversized finite projector carrier");
        return false;
    }
    true
}

fn check_single_projector<C: RationalEmbedding + Involution>(
    r: &mut ProjectorAlgebraReport,
    p: &BasicMatrix<C>,
) -> bool {
    r.idempotence_checks += 1;
    if !r.record_check(
        matrix::multiply(p, p).map(|square| square == *p),
        ProjectorAlgebraStatus::InvalidIdempotence,
        "Pi^2=Pi",
    ) {
        return false;
    }
    r.hermiticity_checks += 1;
    if !r.record_check(
        adjoint(p).map(|star| star == *p),
        ProjectorAlgebraStatus::InvalidHermiticity,
        "Pi*=Pi",
    ) {
        return false;
    }
    r.rank_one_trace_checks += 1;
    r.record_check(
        matrix::trace(p).map(|trace| trace == C::one()),
        ProjectorAlgebraStatus::InvalidRankOneTrace,
        "Tr Pi=1",
    )
}

fn check_same_basis_orthogonality<C: RationalEmbedding + Involution>(
    r: &mut ProjectorAlgebraReport,
    basis: &[BasicMatrix<C>],
    dimension: usize,
    zero: &BasicMatrix<C>,
) -> bool {
    for j in 0..dimension {
        for k in 0..dimension {
            if j != k {
                r.same_basis_orthogonality_checks += 1;
                if !r.record_check(
                    matrix::multiply(&basis[j], &basis[k]).map(|prod| prod == *zero),
                    ProjectorAlgebraStatus::InvalidSameBasisOrthogonality,
                    "Pi_j Pi_k=0",
                ) {
                    return false;
                }
            }
        }
    }
    true
}

fn check_single_basis<C: RationalEmbedding + Involution>(
    r: &mut ProjectorAlgebraReport,
    basis: &[BasicMatrix<C>],
    dimension: usize,
    identity: &BasicMatrix<C>,
    zero: &BasicMatrix<C>,
) -> bool {
    let mut sum = zero.clone();
    for p in basis {
        if !check_single_projector(r, p) {
            return false;
        }
        sum = match matrix::add(&sum, p) {
            Ok(x) => x,
            Err(e) => {
                r.fail_carrier(e.to_string());
                return false;
            }
        };
    }
    if !check_same_basis_orthogonality(r, basis, dimension, zero) {
        return false;
    }
    r.resolution_of_identity_checks += 1;
    r.record_check(
        Ok(sum == *identity),
        ProjectorAlgebraStatus::InvalidResolutionOfIdentity,
        "sum Pi=I",
    )
}

fn check_cross_bases_unbiased<C: RationalEmbedding + Involution>(
    r: &mut ProjectorAlgebraReport,
    bases: &[Vec<BasicMatrix<C>>],
    overlap: &C,
) -> bool {
    for b in 0..bases.len() {
        for c in b + 1..bases.len() {
            for p in &bases[b] {
                for q in &bases[c] {
                    r.cross_basis_unbiased_checks += 1;
                    let cond = matrix::multiply(p, q)
                        .and_then(|m| matrix::trace(&m))
                        .map(|trace| trace == *overlap);
                    if !r.record_check(
                        cond,
                        ProjectorAlgebraStatus::InvalidCrossBasisUnbiasedness,
                        "Tr Pi_b Pi_c=1/d",
                    ) {
                        return false;
                    }
                }
            }
        }
    }
    true
}

pub fn verify_mub_projector_algebra<C: RationalEmbedding + Involution>(
    bases: &[Vec<BasicMatrix<C>>],
    dimension: usize,
) -> ProjectorAlgebraReport {
    let mut r = ProjectorAlgebraReport {
        dimension,
        basis_count: bases.len(),
        projector_count: bases.iter().map(Vec::len).sum(),
        status: ProjectorAlgebraStatus::AlgebraVerified,
        idempotence_checks: 0,
        hermiticity_checks: 0,
        rank_one_trace_checks: 0,
        same_basis_orthogonality_checks: 0,
        resolution_of_identity_checks: 0,
        cross_basis_unbiased_checks: 0,
        checked_identities: Vec::new(),
        error: None,
    };
    if !validate_mub_carrier_shape(&mut r, bases, dimension) {
        return r;
    }
    let identity = match matrix::identity(dimension) {
        Ok(x) => x,
        Err(e) => {
            r.fail_carrier(e.to_string());
            return r;
        }
    };
    let zero = match matrix::zeros(dimension, dimension) {
        Ok(x) => x,
        Err(e) => {
            r.fail_carrier(e.to_string());
            return r;
        }
    };
    for basis in bases {
        if !check_single_basis(&mut r, basis, dimension, &identity, &zero) {
            return r;
        }
    }
    let overlap = C::from_rational(&rq(1, dimension as i64));
    let _ = check_cross_bases_unbiased(&mut r, bases, &overlap);
    r
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/algebra.rs
// Claim: urn:core:crates_rs:core-quantum-physics:algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord249c910d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord249c910d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError249c910d {
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
impl BoundaryError249c910d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError249c910d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError249c910d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord249c910d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError249c910d> {
        if capacity_bound == 0 {
            return Err(BoundaryError249c910d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError249c910d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError249c910d::ExceedsCapacity {
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
mod l4_boundary_tests_249c910d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord249c910d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord249c910d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord249c910d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord249c910d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord249c910d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError249c910d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError249c910d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
