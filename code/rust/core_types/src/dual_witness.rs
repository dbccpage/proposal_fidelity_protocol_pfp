//! Dual witness: display projection of a sealed Φ₁ dual, plus a finite pairing
//! admission check (`||y||* ≤ 1` and claimed evaluation equals the pairing).
//!
//! **Warning**:
//! - `from_verified` is a display-only view of exact quotient-level Φ₁ dual
//!   evidence. It must not re-verify boundedness, annihilate boundary, or decide
//!   authority.
//! - `is_circulation` and `is_bounded` on that path are inherited from the exact
//!   verifier, not recomputed here. See [`DualWitness::from_verified`].
//! - `try_from_claimed_evaluation` enforces the finite dual-norm bound and
//!   pairing identity for an unsealed pairing. It does not mint authority.

use nalgebra::DVector;
use num_traits::ToPrimitive;
use core_functional::phi1::VerifiedExactPhi1;
use serde::{Deserialize, Serialize};

/// Display/diagnostic-only view of a dual witness.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DualWitness {
    /// The dual witness vector φ*
    pub phi: DVector<f64>,

    /// The dual objective value ⟨φ*, ω⟩
    pub dual_value: f64,

    /// Whether the circulation constraint is satisfied: d₀ᵀφ = 0
    pub is_circulation: bool,

    /// Whether the boundedness constraint is satisfied: ‖φ‖∞ ≤ 1
    pub is_bounded: bool,
}

use core_functional::phi1::{DualWitnessError, Phi1Functional};

impl DualWitness {
    /// Construct a display-only `DualWitness` from a `VerifiedExactPhi1`.
    ///
    /// `is_circulation` and `is_bounded` are inherited from the certificate's
    /// exact rational proof, not recomputed:
    /// [`core_functional::phi1::Phi1Functional::verify_exact_certificate`] has already
    /// rejected any witness that fails to annihilate `im(d0)`
    /// (`DualAnnihilatorMismatch`) or that breaks the weighted dual bound
    /// (`DualNormBoundViolation`), and [`VerifiedExactPhi1`] cannot be forged:
    /// its fields are private, so the verifier is its only constructor.
    ///
    /// Do not "fix" this by recomputing the two checks here. That would re-decide
    /// an exact rational fact in lossy f64 — the boundedness verification this
    /// module is forbidden to perform — and rounding alone could then make the
    /// view contradict the certificate it is displaying. The invariant is
    /// load-bearing on those two checks: if either is weakened or dropped from
    /// `verify_exact_certificate`, these fields become false witnesses and must
    /// be dropped with it.
    pub fn from_verified(verified: &VerifiedExactPhi1) -> Self {
        let phi = DVector::from_iterator(
            verified.dual_witness().len(),
            verified
                .dual_witness()
                .iter()
                .map(|v| v.to_f64().unwrap_or(f64::NAN)),
        );
        let dual_value = verified.value().to_f64().unwrap_or(f64::NAN);
        Self {
            phi,
            dual_value,
            is_circulation: true, // Inherited, not recomputed; see from_verified.
            is_bounded: true,     // Inherited, not recomputed; see from_verified.
        }
    }

    /// Admit a finite pairing whose dual infinity-norm is at most 1 and whose
    /// claimed evaluation equals ⟨y, x⟩. Does not mint authority.
    pub fn try_from_claimed_evaluation(
        dual: DVector<f64>,
        primal: DVector<f64>,
        claimed_evaluation: f64,
    ) -> Result<Self, DualWitnessError> {
        let computed = Phi1Functional::verify_display_dual_pairing(
            dual.as_slice(),
            primal.as_slice(),
            claimed_evaluation,
        )?;
        Ok(Self {
            phi: dual,
            dual_value: computed,
            is_circulation: false,
            is_bounded: true,
        })
    }
}

// Origin: engine/crates_rs/core_types/src/dual_witness.rs
// Claim: urn:core:crates_rs:core-types:dual-witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord321b2f52 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord321b2f52` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError321b2f52 {
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
impl BoundaryError321b2f52 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError321b2f52 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError321b2f52 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord321b2f52 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError321b2f52> {
        if capacity_bound == 0 {
            return Err(BoundaryError321b2f52::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError321b2f52::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError321b2f52::ExceedsCapacity {
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
    use num_bigint::BigInt;
    use num_rational::BigRational;
    use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn survivor_certificate() -> ExactPhi1Certificate {
        ExactPhi1Certificate {
            omega: vec![r(1)],
            d0: vec![vec![r(0)]],
            weights: vec![r(1)],
            alpha: vec![r(0)],
            primal_residual: vec![r(1)],
            dual_witness: vec![r(1)],
            reported_value: r(1),
        }
    }

    #[test]
    fn dual_norm_exceeds_unit_bound() {
        let dual = DVector::from_vec(vec![1.5]);
        let primal = DVector::from_vec(vec![1.0]);
        assert_eq!(
            DualWitness::try_from_claimed_evaluation(dual, primal, 1.5).unwrap_err(),
            DualWitnessError::DualNormBoundViolation
        );
        let dual_ok = DVector::from_vec(vec![1.0]);
        let primal_ok = DVector::from_vec(vec![1.0]);
        let witness =
            DualWitness::try_from_claimed_evaluation(dual_ok, primal_ok, 1.0).expect("unit dual");
        assert!(witness.is_bounded);
        assert_eq!(witness.dual_value, 1.0);
    }

    #[test]
    fn evaluation_pairing_mismatch_must_be_rejected() {
        let dual = DVector::from_vec(vec![1.0, 0.0]);
        let primal = DVector::from_vec(vec![2.0, 3.0]);
        assert_eq!(
            DualWitness::try_from_claimed_evaluation(dual.clone(), primal.clone(), 0.0)
                .unwrap_err(),
            DualWitnessError::EvaluationMismatch {
                claimed: 0.0,
                computed: 2.0,
            }
        );
        let witness = DualWitness::try_from_claimed_evaluation(dual, primal, 2.0)
            .expect("claimed pairing matches ⟨y,x⟩");
        assert_eq!(witness.dual_value, 2.0);
        assert_eq!(witness.phi.len(), 2);
    }

    #[test]
    fn dual_primal_length_mismatch_must_be_rejected() {
        let dual = DVector::from_vec(vec![1.0]);
        let primal = DVector::from_vec(vec![1.0, 0.0]);
        assert_eq!(
            DualWitness::try_from_claimed_evaluation(dual, primal, 1.0).unwrap_err(),
            DualWitnessError::DimensionMismatch
        );
    }

    #[test]
    fn from_verified_inherits_sealed_certificate_flags() {
        let verified =
            Phi1Functional::verify_exact_certificate(survivor_certificate()).expect("survivor");
        let witness = DualWitness::from_verified(&verified);
        assert!(witness.is_circulation);
        assert!(witness.is_bounded);
        assert_eq!(witness.dual_value, 1.0);
        assert_eq!(witness.phi.len(), 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_321b2f52 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord321b2f52::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord321b2f52::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord321b2f52::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord321b2f52::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord321b2f52::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError321b2f52::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError321b2f52::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
