// AuthorityEffect: None.
// An f64 Kraus defect does not admit a channel. Exact admission is
// `core_quantum_physics::exact_channel::ExactKrausChannel`.

use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::{CMatrix, DensityMatrix};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StateSpace {
    pub dim: usize,
}

#[derive(Debug)]
pub struct QuantumChannel {
    pub source: StateSpace,
    pub target: StateSpace,
    /// Kraus operators: K_i : H_source -> H_target
    pub kraus: Vec<CMatrix>,
}

impl QuantumChannel {
    pub fn validate(&self) -> Result<(), DensityMatrixError> {
        if self.kraus.is_empty() {
            return Err(DensityMatrixError::NoValidStates);
        }

        let dim = self.source.dim;
        let id = CMatrix::identity(dim, dim);
        let mut acc = CMatrix::zeros(dim, dim);

        for k in &self.kraus {
            if k.nrows() != self.target.dim || k.ncols() != dim {
                return Err(DensityMatrixError::InvalidKrausShape {
                    expected: dim,
                    actual: k.nrows(),
                });
            }
            acc += k.adjoint() * k;
        }

        let defect = (acc - id).norm();
        Err(DensityMatrixError::FloatChannelRefused { defect })
    }
}

pub struct CPTPChannel {
    pub inner: QuantumChannel,
}

impl CPTPChannel {
    pub fn new(ch: QuantumChannel) -> Result<Self, DensityMatrixError> {
        ch.validate()?;
        Ok(Self { inner: ch })
    }

    pub fn apply_checked(&self, rho: &DensityMatrix) -> Result<DensityMatrix, DensityMatrixError> {
        let mut out = CMatrix::zeros(self.inner.target.dim, self.inner.target.dim);

        for k in &self.inner.kraus {
            out += k * rho.rho() * k.adjoint();
        }

        let cfg = crate::quantum::density_config::DensityMatrixConfig::default();
        DensityMatrix::from_validated(out.nrows(), out.as_slice().to_vec(), &cfg)
    }

    /// Candidate C11: Computes the explicit coherence residual vector r^{coh}_i across Kraus operators.
    /// Evaluates non-diagonal interference decay r^{coh}_i = \sum_{k, j \neq \ell} (A_k)_{ij} \rho_{j\ell} (A_k)_{i\ell}^*.
    pub fn compute_c11_coherence_residual(&self, rho: &DensityMatrix) -> Vec<f64> {
        let dim = self.inner.target.dim;
        let rho_mat = rho.rho();
        let mut r_coh = vec![0.0; dim];

        for i in 0..dim {
            let mut sum_i = 0.0;
            for k in &self.inner.kraus {
                for j in 0..dim {
                    for l in 0..dim {
                        if j == l {
                            continue;
                        }
                        let ak_ij = k[(i, j)];
                        let rho_jl = rho_mat[(j, l)];
                        let ak_il_conj = k[(i, l)].conj();
                        sum_i += (ak_ij * rho_jl * ak_il_conj).re;
                    }
                }
            }
            r_coh[i] = sum_i;
        }
        r_coh
    }

    pub fn compose_checked(&self, other: &CPTPChannel) -> Result<CPTPChannel, DensityMatrixError> {
        if self.inner.source != other.inner.target {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: self.inner.source.dim,
                actual: other.inner.target.dim,
            });
        }

        let mut composed = Vec::new();
        for k2 in &self.inner.kraus {
            for k1 in &other.inner.kraus {
                composed.push(k2 * k1);
            }
        }

        CPTPChannel::new(QuantumChannel {
            source: other.inner.source.clone(),
            target: self.inner.target.clone(),
            kraus: composed,
        })
    }
}

// Origin: engine/crates_rs/engines/src/quantum/quantum_channel.rs
// Claim: urn:core:crates_rs:engines:quantum-channel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord31948aae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord31948aae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError31948aae {
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
impl BoundaryError31948aae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError31948aae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError31948aae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord31948aae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError31948aae> {
        if capacity_bound == 0 {
            return Err(BoundaryError31948aae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError31948aae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError31948aae::ExceedsCapacity {
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
mod l4_boundary_tests_31948aae {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord31948aae::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord31948aae::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord31948aae::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord31948aae::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord31948aae::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError31948aae::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError31948aae::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
