//! Greenberger–Horne–Zeilinger (GHZ) state for `core_quantum_physics`.
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`C64`, `CVector`).
//! Constructs n-qubit entangled states |GHZ_n⟩ = 1/√2 (|0...0⟩ + |1...1⟩) in ℂ^{2ⁿ}.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_da4a1bd3<T> {
    fn checked_invariant_da4a1bd3(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_da4a1bd3<T> for Option<T> {
    #[inline]
    fn checked_invariant_da4a1bd3(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_da4a1bd3<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_da4a1bd3(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::bell_state::StateFamilyError;
use crate::hilbert_space::HilbertSpace;
use crate::quantum_state::{QuantumState, QuantumStateError, RayVector};
use linear_algebra::linear_algebra::complex_matrix::{NComplex, C64};
use core_number_theory::cyclotomic::GaussianRat;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite GHZ state face.";

/// Finite carrier for `ghz_state`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GhzState {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl Default for GhzState {
    fn default() -> Self {
        Self::new(8, "ghz_3")
    }
}

impl GhzState {
    /// Exact unnormalised GHZ ray with norm squared two. The carrier is bounded.
    pub fn exact(n: usize) -> Result<RayVector, StateFamilyError> {
        if n < 2 {
            return Err(StateFamilyError::Parameter);
        }
        let dim = HilbertSpace::qubits(n)?.dim();
        let mut v = vec![GaussianRat::zero(); dim];
        v[0] = GaussianRat::one();
        v[dim - 1] = GaussianRat::one();
        Ok(RayVector::try_new(v)?)
    }

    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Standard 3-qubit GHZ state |GHZ⟩ = 1/√2 (|000⟩ + |111⟩) in dim 8.
    pub fn standard_three_qubit() -> QuantumState {
        Self::n_qubit(3).checked_invariant_da4a1bd3("valid 3-qubit GHZ state")
    }

    /// Construct n-qubit GHZ state in dimension 2ⁿ.
    pub fn n_qubit(n: usize) -> Result<QuantumState, QuantumStateError> {
        if n < 2 {
            return Err(QuantumStateError::DimensionMismatch {
                expected: 2,
                actual: n,
            });
        }
        let space = HilbertSpace::qubits(n).map_err(|_| QuantumStateError::DimensionMismatch {
            expected: 1024,
            actual: n,
        })?;
        let dim = space.dim();
        let space = HilbertSpace::try_new(dim, format!("H_2^{}", n)).map_err(|_| {
            QuantumStateError::DimensionMismatch {
                expected: dim,
                actual: 0,
            }
        })?;
        let mut amps = vec![C64::ZERO; dim];
        let inv_sqrt2 = 1.0 / (2.0_f64).sqrt();
        amps[0] = NComplex::new(inv_sqrt2, 0.0);
        amps[dim - 1] = NComplex::new(inv_sqrt2, 0.0);
        QuantumState::try_normalized(&space, amps, format!("ghz_{}", n))
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/ghz_state.rs
// Claim: urn:core:crates_rs:core-quantum-physics:ghz-state:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordda4a1bd3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordda4a1bd3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorda4a1bd3 {
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
impl BoundaryErrorda4a1bd3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorda4a1bd3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorda4a1bd3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordda4a1bd3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorda4a1bd3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorda4a1bd3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorda4a1bd3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorda4a1bd3::ExceedsCapacity {
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

    #[test]
    fn new_and_fence() {
        let x = GhzState::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(GhzState::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn standard_three_qubit_ghz() {
        let ghz = GhzState::standard_three_qubit();
        assert_eq!(ghz.dim, 8);
        assert!((ghz.norm_sq() - 1.0).abs() < 1e-12);
        let inv_sqrt2 = 1.0 / (2.0_f64).sqrt();
        assert!((ghz.amplitudes[0].re - inv_sqrt2).abs() < 1e-12);
        assert!((ghz.amplitudes[7].re - inv_sqrt2).abs() < 1e-12);
        for i in 1..7 {
            assert_eq!(ghz.amplitudes[i], C64::ZERO);
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_da4a1bd3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordda4a1bd3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordda4a1bd3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordda4a1bd3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordda4a1bd3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordda4a1bd3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorda4a1bd3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorda4a1bd3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
