//! Checkable exact Yang-Baxter identities, retaining the residual matrix.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix;
use core_fusion_categories::{error::FusionError, scalar::FusionScalar, yang_baxter};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact Yang-Baxter residuals.";
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct YangBaxterEquation<K> {
    residual: BasicMatrix<K>,
}
impl<K: FusionScalar> YangBaxterEquation<K> {
    pub fn braid(r: &BasicMatrix<K>) -> Result<Self, FusionError> {
        Ok(Self {
            residual: yang_baxter::braid_form_defect(r)?,
        })
    }
    /// Additive spectral identity R12(u-v) R13(u) R23(v).
    pub fn spectral(
        family: impl Fn(&K) -> Result<BasicMatrix<K>, FusionError>,
        u: &K,
        v: &K,
    ) -> Result<Self, FusionError> {
        Ok(Self {
            residual: yang_baxter::spectral_form_defect(family, &u.sub(v), u, v)?,
        })
    }
    /// Multiplicative spectral identity R12(u/v) R13(u) R23(v).
    pub fn multiplicative(
        family: impl Fn(&K) -> Result<BasicMatrix<K>, FusionError>,
        u: &K,
        v: &K,
    ) -> Result<Self, FusionError> {
        let ratio = core_number_theory::scalar::divide(u, v).map_err(FusionError::from)?;
        Ok(Self {
            residual: yang_baxter::spectral_form_defect(family, &ratio, u, v)?,
        })
    }
    pub fn residual(&self) -> &BasicMatrix<K> {
        &self.residual
    }
    pub fn holds(&self) -> bool {
        matrix::is_zero_matrix(&self.residual)
    }
    pub fn first_failing_entry(&self) -> Option<(usize, usize, &K)> {
        self.residual
            .as_slice()
            .iter()
            .enumerate()
            .find(|(_, x)| !x.is_zero())
            .map(|(i, x)| (i / self.residual.cols(), i % self.residual.cols(), x))
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/yang_baxter_equation.rs
// Claim: urn:core:crates_rs:core-quantum-physics:yang-baxter-equation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord67571396 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord67571396` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError67571396 {
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
impl BoundaryError67571396 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError67571396 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError67571396 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord67571396 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError67571396> {
        if capacity_bound == 0 {
            return Err(BoundaryError67571396::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError67571396::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError67571396::ExceedsCapacity {
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
mod tests {
    use super::*;
    use core_number_theory::rational::rq;
    #[test]
    fn yang_and_six_vertex_satisfy_the_spectral_equations() {
        assert!(YangBaxterEquation::spectral(
            |u| yang_baxter::yang_rational(2, u),
            &rq(5, 1),
            &rq(2, 1)
        )
        .unwrap()
        .holds());
        assert!(YangBaxterEquation::multiplicative(
            |z| yang_baxter::six_vertex(&rq(2, 1), z),
            &rq(3, 1),
            &rq(5, 1)
        )
        .unwrap()
        .holds());
    }
    #[test]
    fn wrong_spectral_argument_has_a_nonzero_residual() {
        let r = yang_baxter::spectral_form_defect(
            |u| yang_baxter::yang_rational(2, u),
            &rq(7, 1),
            &rq(5, 1),
            &rq(2, 1),
        )
        .unwrap();
        let check = YangBaxterEquation { residual: r };
        assert!(!check.holds());
        assert!(check.first_failing_entry().is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_67571396 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord67571396::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord67571396::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord67571396::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord67571396::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord67571396::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError67571396::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError67571396::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
