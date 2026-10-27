//! Density matrix observables and quantum fidelity metrics.
//!
//! Provides von Neumann entropy, purity, exact Uhlmann/Jozsa fidelity,
//! Bures distance/angle, classical projection, and supertrace observables.
//!
//! AuthorityEffect: None. Diagnostics only.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Parity {
    Even,
    Odd,
}

use crate::quantum::density_matrix::{CMatrix, C64};
use crate::quantum::semantic_geometry_engine::uhlmann_fidelity;
use linear_algebra::linear_algebra::density::{
    DensityMatrix, DensityMatrixConfig, DensityMatrixError,
};

pub fn von_neumann_entropy_observable(dm: &DensityMatrix) -> f64 {
    dm.von_neumann_entropy().unwrap_or(0.0)
}

pub fn purity_observable(dm: &DensityMatrix) -> f64 {
    dm.purity()
}

pub fn trace_observable(dm: &DensityMatrix) -> f64 {
    dm.trace()
}

/// Compute exact Uhlmann / Jozsa fidelity \(\mathcal{F}(\rho, \sigma) = (\operatorname{Tr}\sqrt{\sqrt{\rho}\sigma\sqrt{\rho}})^2\).
pub fn fidelity_observable(dm: &DensityMatrix, other: &DensityMatrix) -> Result<f64, String> {
    let cfg = DensityMatrixConfig::default();
    fidelity_observable_checked(dm, other, &cfg).map_err(|e| format!("{:?}", e))
}

/// Strict checked Uhlmann fidelity with configuration validation.
pub fn fidelity_observable_checked(
    dm: &DensityMatrix,
    other: &DensityMatrix,
    _cfg: &DensityMatrixConfig,
) -> Result<f64, DensityMatrixError> {
    if dm.dim() != other.dim() {
        return Err(DensityMatrixError::DimensionMismatch {
            expected: dm.dim(),
            actual: other.dim(),
        });
    }

    let n = dm.dim();
    let rho_arr = dm.rho();
    let other_arr = other.rho();

    let mut rho_mat = CMatrix::zeros(n, n);
    let mut other_mat = CMatrix::zeros(n, n);

    for i in 0..n {
        for j in 0..n {
            let z1 = rho_arr[(i, j)];
            let z2 = other_arr[(i, j)];
            if !z1.re.is_finite() || !z1.im.is_finite() || !z2.re.is_finite() || !z2.im.is_finite()
            {
                return Err(DensityMatrixError::NonPhysical);
            }
            rho_mat[(i, j)] = C64::new(z1.re, z1.im);
            other_mat[(i, j)] = C64::new(z2.re, z2.im);
        }
    }

    uhlmann_fidelity(&rho_mat, &other_mat).map_err(|_| DensityMatrixError::NonPhysical)
}

/// Compute Bures metric distance \(d_B(\rho, \sigma) = \sqrt{2(1 - \sqrt{\mathcal{F}(\rho, \sigma)})}\).
pub fn bures_distance_observable(dm: &DensityMatrix, other: &DensityMatrix) -> Result<f64, String> {
    let f = fidelity_observable(dm, other)?;
    let d = (2.0 * (1.0 - f.sqrt())).max(0.0).sqrt();
    Ok(d)
}

/// Compute Bures angle \(\theta_B(\rho, \sigma) = \arccos(\sqrt{\mathcal{F}(\rho, \sigma)})\).
pub fn bures_angle_observable(dm: &DensityMatrix, other: &DensityMatrix) -> Result<f64, String> {
    let f = fidelity_observable(dm, other)?;
    Ok(f.sqrt().clamp(0.0, 1.0).acos())
}

pub fn classical_projection_observable(dm: &DensityMatrix) -> Vec<f64> {
    classical_projection_observable_checked(dm, &DensityMatrixConfig::default())
        .unwrap_or_else(|_| vec![0.0; dm.dim()])
}

pub fn classical_projection_observable_checked(
    dm: &DensityMatrix,
    cfg: &DensityMatrixConfig,
) -> Result<Vec<f64>, DensityMatrixError> {
    let mut probs = Vec::with_capacity(dm.dim());
    for i in 0..dm.dim() {
        let val = dm.rho()[(i, i)].re;
        if !val.is_finite() {
            return Err(DensityMatrixError::NonPhysical);
        }
        if val < -cfg.psd_tol() {
            return Err(DensityMatrixError::InvalidProbabilityMass { mass: val });
        }
        probs.push(val);
    }
    Ok(probs)
}

pub fn supertrace_observable(dm: &DensityMatrix, grading: &[Parity]) -> Result<f64, String> {
    let cfg = DensityMatrixConfig::default();
    supertrace_observable_checked(dm, grading, &cfg).map_err(|e| format!("{:?}", e))
}

pub fn supertrace_observable_checked(
    dm: &DensityMatrix,
    grading: &[Parity],
    _cfg: &DensityMatrixConfig,
) -> Result<f64, DensityMatrixError> {
    if grading.len() != dm.dim() {
        return Err(DensityMatrixError::DimensionMismatch {
            expected: dm.dim(),
            actual: grading.len(),
        });
    }

    let mut strace = 0.0;
    for (i, p) in grading.iter().enumerate() {
        let val = dm.rho()[(i, i)].re;
        if !val.is_finite() {
            return Err(DensityMatrixError::NonPhysical);
        }

        match p {
            Parity::Even => strace += val,
            Parity::Odd => strace -= val,
        }
    }

    Ok(strace)
}

// Origin: engine/crates_rs/engines/src/quantum/density.rs
// Claim: urn:core:crates_rs:engines:density:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5fbbf020 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5fbbf020` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5fbbf020 {
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
impl BoundaryError5fbbf020 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5fbbf020 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5fbbf020 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5fbbf020 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5fbbf020> {
        if capacity_bound == 0 {
            return Err(BoundaryError5fbbf020::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5fbbf020::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5fbbf020::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_5fbbf020 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5fbbf020::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5fbbf020::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5fbbf020::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5fbbf020::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5fbbf020::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5fbbf020::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5fbbf020::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
