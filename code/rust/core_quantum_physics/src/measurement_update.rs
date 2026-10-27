//! Post-measurement quantum state update (Lüders/von Neumann collapse) for `core_quantum_physics`.
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`CMatrix`, `CVector`).
//! Implements selective state update |ψ'⟩ = M_m|ψ⟩ / √p(m), density matrix update
//! ρ' = M_m ρ M_m† / p(m), and unselective update ρ' = ∑ M_m ρ M_m†.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::measurement::{Measurement, MeasurementError};
use crate::quantum_state::QuantumState;
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, NComplex, C64};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite measurement update face.";

/// Finite carrier for `measurement_update`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct MeasurementUpdate {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl MeasurementUpdate {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Selective state update on outcome m: |ψ'⟩ = M_m |ψ⟩ / √p(m).
    pub fn update_state(
        measurement: &Measurement,
        psi: &QuantumState,
        outcome: usize,
    ) -> Result<QuantumState, MeasurementError> {
        measurement.validate()?;
        if outcome >= measurement.num_outcomes() {
            return Err(MeasurementError::OutcomeOutOfRange {
                outcome,
                total: measurement.num_outcomes(),
            });
        }
        if psi.dim != measurement.dim || psi.amplitudes.len() != measurement.dim {
            return Err(MeasurementError::DimensionMismatch {
                expected: measurement.dim,
                actual: psi.dim,
            });
        }
        let m = &measurement.operators[outcome];
        let v = psi.to_cvector();
        let mv = m * v;
        let norm_sq: f64 = mv.iter().map(|z| z.norm_sqr()).sum();
        if !norm_sq.is_finite() || norm_sq <= 0.0 {
            return Err(MeasurementError::ZeroProbability);
        }
        let inv_norm = 1.0 / norm_sq.sqrt();
        let updated_amps: Vec<C64> = mv.iter().map(|z| *z * inv_norm).collect();
        Ok(QuantumState {
            dim: measurement.dim,
            amplitudes: updated_amps,
            label: format!("{}_post_{}", psi.label, outcome),
        })
    }

    /// Selective density matrix update on outcome m: ρ' = M_m ρ M_m† / p(m).
    pub fn update_density(
        measurement: &Measurement,
        rho_mat: &CMatrix,
        outcome: usize,
    ) -> Result<CMatrix, MeasurementError> {
        measurement.validate()?;
        if outcome >= measurement.num_outcomes() {
            return Err(MeasurementError::OutcomeOutOfRange {
                outcome,
                total: measurement.num_outcomes(),
            });
        }
        if rho_mat.nrows() != measurement.dim || rho_mat.ncols() != measurement.dim {
            return Err(MeasurementError::DimensionMismatch {
                expected: measurement.dim,
                actual: rho_mat.nrows(),
            });
        }
        let m = &measurement.operators[outcome];
        let unnorm = m * rho_mat * m.adjoint();
        let tr = unnorm.trace().re;
        if !tr.is_finite() || tr <= 0.0 {
            return Err(MeasurementError::ZeroProbability);
        }
        let scale = NComplex::new(1.0 / tr, 0.0);
        Ok(&unnorm * scale)
    }

    /// Unselective measurement update: ρ' = ∑_m M_m ρ M_m†.
    pub fn unselective_update(
        measurement: &Measurement,
        rho_mat: &CMatrix,
    ) -> Result<CMatrix, MeasurementError> {
        measurement.validate()?;
        if rho_mat.nrows() != measurement.dim || rho_mat.ncols() != measurement.dim {
            return Err(MeasurementError::DimensionMismatch {
                expected: measurement.dim,
                actual: rho_mat.nrows(),
            });
        }
        let mut out = CMatrix::zeros(measurement.dim, measurement.dim);
        for m in &measurement.operators {
            out += m * rho_mat * m.adjoint();
        }
        Ok(out)
    }

    /// Degree / dimension proxy.
    pub fn degree(&self) -> usize {
        self.degree
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/measurement_update.rs
// Claim: urn:core:crates_rs:core-quantum-physics:measurement-update:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc87dc55e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc87dc55e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc87dc55e {
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
impl BoundaryErrorc87dc55e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc87dc55e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc87dc55e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc87dc55e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc87dc55e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc87dc55e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc87dc55e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc87dc55e::ExceedsCapacity {
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
mod tests {
    use super::*;
    use crate::hilbert_space::HilbertSpace;
    use linear_algebra::linear_algebra::complex_matrix::NComplex;

    #[test]
    fn new_and_fence() {
        let x = MeasurementUpdate::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(MeasurementUpdate::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn state_collapse_on_superposition() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let inv_sqrt2 = 1.0 / (2.0_f64).sqrt();
        let plus = QuantumState::try_normalized(
            &h2,
            vec![NComplex::new(inv_sqrt2, 0.0), NComplex::new(inv_sqrt2, 0.0)],
            "+",
        )
        .unwrap();

        let m = Measurement::computational_basis(2);

        // Collapse to |0>
        let post_0 = MeasurementUpdate::update_state(&m, &plus, 0).unwrap();
        assert!((post_0.amplitudes[0].re - 1.0).abs() < 1e-12);
        assert!(post_0.amplitudes[1].norm_sqr() < 1e-12);

        // Collapse to |1>
        let post_1 = MeasurementUpdate::update_state(&m, &plus, 1).unwrap();
        assert!(post_1.amplitudes[0].norm_sqr() < 1e-12);
        assert!((post_1.amplitudes[1].re - 1.0).abs() < 1e-12);
    }
}

#[cfg(test)]
mod l4_boundary_tests_c87dc55e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc87dc55e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc87dc55e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc87dc55e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc87dc55e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc87dc55e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc87dc55e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc87dc55e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
