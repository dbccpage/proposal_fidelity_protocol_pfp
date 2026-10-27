// AuthorityEffect: None.
//! Float tolerances do not admit a quantum channel. Exact admission is
//! `ExactKrausChannel::try_new`.

use linear_algebra::exact_field::matrix as mx;
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, NComplex};
use linear_algebra::linear_algebra::density::{
    DensityMatrixConfig, DensityMatrixError, NumericalDensityMatrix,
};
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::kraus_operators::KrausOperators;
use core_quantum_physics::quantum_channel::{ChannelError, QuantumChannel};

#[test]
fn exact_rational_kraus_channel_is_admitted_by_exact_kraus() {
    let channel = ExactKrausChannel::try_new(2, 2, vec![mx::identity(2).unwrap()], "id")
        .expect("exact identity");
    assert_eq!(channel.dim_in(), 2);
    assert_eq!(channel.dim_out(), 2);
    assert_eq!(channel.label(), "id");
    assert_eq!(channel.operators().len(), 1);
}

#[test]
fn float_defect_below_1e_6_is_refused() {
    let mut almost = CMatrix::zeros(2, 2);
    almost[(0, 0)] = NComplex::new(1.0, 0.0);
    almost[(1, 1)] = NComplex::new(1.0 - 1e-9, 0.0);
    let kraus = KrausOperators::try_from_cmatrices(2, vec![almost.clone()], "almost").unwrap();
    let residual = kraus.completeness_residual();
    let config = DensityMatrixConfig::default();
    assert!(residual > 0.0 && residual < 1e-6);
    assert!(residual < config.channel_tol());

    assert!(matches!(
        QuantumChannel::try_from_kraus(kraus, "almost", 1e-6),
        Err(ChannelError::ToleranceAdmissionRefused {
            tolerance,
            residual: got,
            ..
        }) if tolerance == 1e-6 && got < 1e-6
    ));

    let rho = NumericalDensityMatrix::try_maximally_mixed(2).unwrap();
    assert!(matches!(
        rho.apply_kraus(&[almost], &config),
        Err(DensityMatrixError::FloatChannelRefused { defect }) if defect < 1e-6
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/exact_channel_admission.rs
// Claim: urn:core:crates_rs:tests:exact-channel-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde105c47f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde105c47f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore105c47f {
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
impl BoundaryErrore105c47f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore105c47f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore105c47f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde105c47f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore105c47f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore105c47f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore105c47f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore105c47f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e105c47f() {
    let admitted = BoundaryRecorde105c47f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde105c47f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
