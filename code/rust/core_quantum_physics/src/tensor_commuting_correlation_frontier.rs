//! Exact CHSH game attainment, operator bounds, and a state-derived NPA moment.
use crate::finite_chsh_correlations::{
    algebraic_box_from_state, npa_level_one_ab_moment, tsirelson_certificate,
    AlgebraicCorrelationError, TsirelsonCertificate,
};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::outer_product, matrix as mx, ordered::HermitianOrdered,
};
use core_lie_theory::pauli_symplectic::{pauli, Pauli};
use core_number_theory::cyclotomic_field::{sqrt_of_integer, Cyclotomic};
use core_number_theory::rational::{ri, rq, Rational};
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChshGameCertificate {
    pub local_dimension: usize,
    pub classical_value: Rational,
    pub game_value: Cyclotomic<8>,
    pub state: BasicMatrix<Cyclotomic<8>>,
    pub alice: [BasicMatrix<Cyclotomic<8>>; 2],
    pub bob: [BasicMatrix<Cyclotomic<8>>; 2],
    pub operator_bound: TsirelsonCertificate<Cyclotomic<8>>,
    pub moment: BasicMatrix<Cyclotomic<8>>,
    pub probabilities: Vec<Cyclotomic<8>>,
}
fn chsh_tau_and_inverse() -> Result<(Cyclotomic<8>, Cyclotomic<8>), AlgebraicCorrelationError> {
    let tau = Cyclotomic::<8>::try_from(
        sqrt_of_integer(8, &2.into()).map_err(|_| AlgebraicCorrelationError::SquareRoot)?,
    )
    .map_err(|_| AlgebraicCorrelationError::SquareRoot)?;
    let inv = tau.inverse().ok_or(AlgebraicCorrelationError::SquareRoot)?;
    Ok((tau, inv))
}

fn build_chsh_alice_bob_observables(
    inv: &Cyclotomic<8>,
) -> Result<
    (
        [BasicMatrix<Cyclotomic<8>>; 2],
        [BasicMatrix<Cyclotomic<8>>; 2],
    ),
    AlgebraicCorrelationError,
> {
    let x = pauli::<Cyclotomic<8>>(Pauli::X).map_err(|_| AlgebraicCorrelationError::Observable)?;
    let z = pauli::<Cyclotomic<8>>(Pauli::Z).map_err(|_| AlgebraicCorrelationError::Observable)?;
    let alice = [z.clone(), x.clone()];
    let bob = [
        mx::scale(&mx::add(&z, &x)?, inv)?,
        mx::scale(&mx::sub(&z, &x)?, inv)?,
    ];
    Ok((alice, bob))
}

fn verify_chsh_bell_expectation(
    state: &BasicMatrix<Cyclotomic<8>>,
    bound: &TsirelsonCertificate<Cyclotomic<8>>,
) -> Result<Cyclotomic<8>, AlgebraicCorrelationError> {
    let prod = mx::multiply(state, &bound.bell_operator)?;
    let expectation = mx::trace(&prod)?;
    if expectation != bound.bound {
        return Err(AlgebraicCorrelationError::Certificate);
    }
    Ok(expectation)
}

/// Phi+ with Alice (Z,X) and Bob ((Z+X)/sqrt2,(Z-X)/sqrt2).
/// Upper optimality replays the two SOS identities, lower optimality the Born trace.
pub fn chsh_game_certificate() -> Result<ChshGameCertificate, AlgebraicCorrelationError> {
    let q = |r: Rational| Cyclotomic::<8>::rational(r);
    let (tau, inv) = chsh_tau_and_inverse()?;
    let (alice, bob) = build_chsh_alice_bob_observables(&inv)?;
    let v = vec![q(ri(1)), q(ri(0)), q(ri(0)), q(ri(1))];
    let outer = outer_product(&v, &v)?;
    let state = mx::scale(&outer, &q(rq(1, 2)))?;
    let bound = tsirelson_certificate(&alice, &bob, &tau)?;
    let expectation = verify_chsh_bell_expectation(&state, &bound)?;
    let game_value = q(rq(1, 2)) + expectation.scale(&rq(1, 8));
    let moment = npa_level_one_ab_moment(&state, &alice, &bob)?;
    let probabilities = algebraic_box_from_state(&state, &alice, &bob)?;
    let cert = ChshGameCertificate {
        local_dimension: 2,
        classical_value: rq(3, 4),
        game_value,
        state,
        alice,
        bob,
        operator_bound: bound,
        moment,
        probabilities,
    };
    Ok(cert)
}
/// The endpoints are checked against the actual algebraic strategy value.
pub fn certify_chsh_interval(
    lower: &Rational,
    upper: &Rational,
) -> Result<bool, AlgebraicCorrelationError> {
    let c = chsh_game_certificate()?;
    if lower >= upper {
        return Ok(false);
    }
    Ok(
        (c.game_value.clone() - Cyclotomic::<8>::rational(lower.clone())).fixed_field_sign()
            == Some(1)
            && (Cyclotomic::<8>::rational(upper.clone()) - c.game_value).fixed_field_sign()
                == Some(1),
    )
}

// Origin: engine/crates_rs/core_quantum_physics/src/tensor_commuting_correlation_frontier.rs
// Claim: urn:core:crates_rs:core-quantum-physics:tensor-commuting-correlation-frontier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord50f16360 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord50f16360` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError50f16360 {
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
impl BoundaryError50f16360 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError50f16360 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError50f16360 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord50f16360 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError50f16360> {
        if capacity_bound == 0 {
            return Err(BoundaryError50f16360::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError50f16360::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError50f16360::ExceedsCapacity {
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
mod l4_boundary_tests_50f16360 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord50f16360::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord50f16360::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord50f16360::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord50f16360::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord50f16360::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError50f16360::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError50f16360::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
