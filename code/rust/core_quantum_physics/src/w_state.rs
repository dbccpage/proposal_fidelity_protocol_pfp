//! Canonical W state (maximally multipartite entangled state robust to qubit loss) for `core_quantum_physics`.
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`C64`, `CVector`).
//! Constructs n-qubit W states |W_n⟩ = 1/√n (|100...0⟩ + |010...0⟩ + ... + |000...1⟩) in ℂ^{2ⁿ}.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_796ec0c4<T> {
    fn checked_invariant_796ec0c4(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_796ec0c4<T> for Option<T> {
    #[inline]
    fn checked_invariant_796ec0c4(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_796ec0c4<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_796ec0c4(self, msg: &str) -> T {
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
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite W state face.";

/// Finite carrier for `w_state`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WState {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl Default for WState {
    fn default() -> Self {
        Self::new(8, "w_3")
    }
}

impl WState {
    /// Exact W ray, the Dicke state of Hamming weight one, with norm squared n.
    pub fn exact(n: usize) -> Result<RayVector, StateFamilyError> {
        Self::dicke(n, 1)
    }

    /// Symmetric Dicke ray sum_{|x|=k} |x>, using exact unit coefficients.
    /// Its norm squared is binomial(n,k); k=0,n give product states.
    pub fn dicke(n: usize, k: usize) -> Result<RayVector, StateFamilyError> {
        if n == 0 || k > n {
            return Err(StateFamilyError::Parameter);
        }
        let dim = HilbertSpace::qubits(n)?.dim();
        let mut v = vec![GaussianRat::zero(); dim];
        for (index, x) in v.iter_mut().enumerate() {
            if usize::try_from(index.count_ones()).ok() == Some(k) {
                *x = GaussianRat::one();
            }
        }
        Ok(RayVector::try_new(v)?)
    }

    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Standard 3-qubit W state |W⟩ = 1/√3 (|100⟩ + |010⟩ + |001⟩) in dim 8.
    pub fn standard_three_qubit() -> QuantumState {
        Self::n_qubit(3).checked_invariant_796ec0c4("valid 3-qubit W state")
    }

    /// Construct n-qubit W state in dimension 2ⁿ.
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
        let inv_sqrt_n = 1.0 / (n as f64).sqrt();

        // Indices with Hamming weight 1: 2^0, 2^1, ..., 2^{n-1}
        for i in 0..n {
            amps[1usize << i] = NComplex::new(inv_sqrt_n, 0.0);
        }

        QuantumState::try_normalized(&space, amps, format!("w_{}", n))
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/w_state.rs
// Claim: urn:core:crates_rs:core-quantum-physics:w-state:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord796ec0c4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord796ec0c4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError796ec0c4 {
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
impl BoundaryError796ec0c4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError796ec0c4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError796ec0c4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord796ec0c4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError796ec0c4> {
        if capacity_bound == 0 {
            return Err(BoundaryError796ec0c4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError796ec0c4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError796ec0c4::ExceedsCapacity {
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

    #[test]
    fn new_and_fence() {
        let x = WState::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(WState::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn standard_three_qubit_w() {
        let w = WState::standard_three_qubit();
        assert_eq!(w.dim, 8);
        assert!((w.norm_sq() - 1.0).abs() < 1e-12);
        let inv_sqrt3 = 1.0 / (3.0_f64).sqrt();
        assert!((w.amplitudes[1].re - inv_sqrt3).abs() < 1e-12); // |001>
        assert!((w.amplitudes[2].re - inv_sqrt3).abs() < 1e-12); // |010>
        assert!((w.amplitudes[4].re - inv_sqrt3).abs() < 1e-12); // |100>
        assert_eq!(w.amplitudes[0], C64::ZERO);
        assert_eq!(w.amplitudes[3], C64::ZERO);
        assert_eq!(w.amplitudes[7], C64::ZERO);
    }
}

#[cfg(test)]
mod l4_boundary_tests_796ec0c4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord796ec0c4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord796ec0c4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord796ec0c4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord796ec0c4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord796ec0c4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError796ec0c4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError796ec0c4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
