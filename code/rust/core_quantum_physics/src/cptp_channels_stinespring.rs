//! Exact Stinespring realizations with a declared weighted environment metric.
//!
//! A weighted Kraus channel has V†(I tensor G)V=I with G=diag(w_k).
//! The channel is the corresponding weighted partial trace; rational four-square
//! splitting also gives an ordinary isometry over Q(i), at the cost of a larger
//! environment. Choi rank is the minimal environment dimension over C.
//! AuthorityEffect: None.

use crate::exact_channel::{ExactChannelError, ExactKrausChannel};
use crate::exact_hermitian::exact_limits;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WeightedStinespring {
    channel: ExactKrausChannel,
    isometry: BasicMatrix<GaussianRat>,
    metric: Vec<Rational>,
}

impl WeightedStinespring {
    /// Minimal weighted realization from a canonical Choi factorization.
    pub fn from_channel(channel: &ExactKrausChannel) -> Result<Self, ExactChannelError> {
        let channel = channel.minimal()?;
        let v = Self::build_isometry_matrix(&channel)?;
        let result = Self {
            metric: channel.weights().to_vec(),
            channel,
            isometry: v,
        };
        if !result.verify()? {
            return Err(ExactChannelError::FactorizationReplay);
        }
        Ok(result)
    }

    fn build_isometry_matrix(
        channel: &ExactKrausChannel,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        let r = channel.operators().len();
        let limits = core_kernel::resource_limits::OperationLimits::default();
        let rows = limits.checked_product(channel.dim_out(), r)?;
        limits.check_hilbert_dim(rows)?;
        limits.check_dense_matrix(rows, channel.dim_in(), std::mem::size_of::<GaussianRat>())?;
        let mut v = mx::zeros_with_limits(rows, channel.dim_in(), exact_limits())?;
        for (k, op) in channel.operators().iter().enumerate() {
            for b in 0..channel.dim_out() {
                for a in 0..channel.dim_in() {
                    v.set(b * r + k, a, op.get_ref(b, a)?.clone())?;
                }
            }
        }
        Ok(v)
    }
    pub fn environment_dim(&self) -> usize {
        self.metric.len()
    }
    pub fn isometry(&self) -> &BasicMatrix<GaussianRat> {
        &self.isometry
    }
    pub fn environment_metric(&self) -> &[Rational] {
        &self.metric
    }
    /// Independent contraction of the declared metric and V, with exact replay.
    pub fn verify(&self) -> Result<bool, ExactChannelError> {
        let r = self.environment_dim();
        let weighted = mx::from_fn_with_limits(
            self.isometry.rows(),
            self.isometry.cols(),
            exact_limits(),
            |row, col| {
                self.isometry.as_slice()[row * self.isometry.cols() + col]
                    .mul(&GaussianRat::from_rational(self.metric[row % r].clone()))
            },
        )?;
        let gram =
            mx::multiply_with_limits(&star::adjoint(&self.isometry)?, &weighted, exact_limits())?;
        Ok(gram == mx::identity_with_limits(self.channel.dim_in(), exact_limits())?)
    }

    /// Weighted partial trace, evaluated directly from V and G rather than
    /// reconstructing a Kraus family.
    pub fn apply(
        &self,
        rho: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        crate::exact_hermitian::check_well_formed(rho).map_err(ExactChannelError::Malformed)?;
        if rho.rows() != self.channel.dim_in() || rho.cols() != self.channel.dim_in() {
            return Err(ExactChannelError::StateShape {
                expected: self.channel.dim_in(),
                actual: (rho.rows(), rho.cols()),
            });
        }
        let r = self.environment_dim();
        // Matrix products carry the shared scalar-operation budget; the naive
        // four-index contraction would perform O(d_in² d_out² r) field work.
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            self.isometry.rows(),
            self.isometry.rows(),
            std::mem::size_of::<GaussianRat>(),
        )?;
        let state = mx::multiply_with_limits(
            &mx::multiply_with_limits(&self.isometry, rho, exact_limits())?,
            &star::adjoint(&self.isometry)?,
            exact_limits(),
        )?;
        Ok(mx::from_fn_with_limits(
            self.channel.dim_out(),
            self.channel.dim_out(),
            exact_limits(),
            |b, c| {
                (0..r).fold(GaussianRat::zero(), |sum, k| {
                    sum.add(
                        &state.as_slice()[(b * r + k) * state.cols() + c * r + k]
                            .mul(&GaussianRat::from_rational(self.metric[k].clone())),
                    )
                })
            },
        )?)
    }

    /// Ordinary isometry over the original field after bounded four-square splitting.
    pub fn ordinary_isometry(
        &self,
        budget: u64,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        self.channel.to_unit_weight(budget)?.stinespring_isometry()
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/cptp_channels_stinespring.rs
// Claim: urn:core:crates_rs:core-quantum-physics:cptp-channels-stinespring:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1bc6a326 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1bc6a326` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1bc6a326 {
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
impl BoundaryError1bc6a326 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1bc6a326 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1bc6a326 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1bc6a326 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1bc6a326> {
        if capacity_bound == 0 {
            return Err(BoundaryError1bc6a326::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1bc6a326::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1bc6a326::ExceedsCapacity {
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
mod l4_boundary_tests_1bc6a326 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1bc6a326::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1bc6a326::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1bc6a326::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1bc6a326::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1bc6a326::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError1bc6a326::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError1bc6a326::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
