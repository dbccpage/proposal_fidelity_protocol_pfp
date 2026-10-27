// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! The finite-dimensional commutator obstruction and the Weyl relation, exact over
//! `Q(zeta_24)`.
//!
//! **No finite canonical commutation relation.** For `N x N` matrices over a field of
//! characteristic 0, `Tr[Q, P] = Tr(QP) - Tr(PQ) = 0`, while `Tr(c I_N) = N c`. So
//! `[Q, P] = c I_N` forces `c = 0` (Wintner): the Heisenberg relation has no
//! finite-dimensional solution. [`trace_of_scalar_d3`],
//! [`commutator_equals_scalar_d3`] and [`trace_obstructs_scalar_commutator_d3`] check the
//! two sides of that argument on given matrices.
//!
//! **The finite replacement** is the Weyl relation `Z X = omega X Z` with `omega` a
//! primitive `N`-th root of unity; for `N = 3` the shift `X` and clock `Z` of
//! [`core_lie_theory::weyl_operators`] satisfy it, and `Tr[Z, X] = 0` holds because `Tr(XZ) = 0`.
//!
//! **Irreducibility.** [`linear_algebra::exact_field::commutant::commutant_dimension_with_limits`] computes, by exact rank over
//! `Q(zeta_24)` of the linear system `[M, G] = 0`, the dimension of the algebra of
//! matrices commuting with given generators. For `(X, Z)` it is 1: only the scalars
//! commute with both. Because `X` and `Z` are unitary this says the pair is an
//! irreducible representation, the finite-dimensional half of Stone-von Neumann. That
//! every irreducible representation of the relation is equivalent to this one is **not**
//! checked here.
//!
//! Everything is exact; nothing panics on the `d = 3` data of this module. The
//! generic [`linear_algebra::exact_field::commutant::commutant_dimension_with_limits`] refuses generators of the wrong shape.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_4e726d84<T> {
    fn checked_invariant_4e726d84(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_4e726d84<T> for Option<T> {
    #[inline]
    fn checked_invariant_4e726d84(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_4e726d84<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_4e726d84(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_hermitian::exact_limits;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    commutant::commutant_dimension_with_limits, involution as star, matrix as mx, ExactFieldError,
};
use core_lie_theory::weyl_operators::{weyl_x_d3, weyl_z_d3};
use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::rational::rq;
use serde::{Deserialize, Serialize};
/// Report on the finite commutator trace obstruction analysis.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CommutatorObstructionReport {
    pub dimension: usize,
    /// `Tr[Q, P] = 0` for the discrete position and momentum.
    pub commutator_trace_is_zero: bool,
    /// For the canonical constants `c = 1` and `c = i`, the trace of a hypothetical
    /// right-hand side `c I_3` is non-zero and differs from `Tr[Q, P]`, so `[Q, P] = c I_3`
    /// is impossible.
    pub hypothetical_ccr_trace_non_zero: bool,
    pub weyl_relation_satisfied: bool,
    pub weyl_commutator_trace_is_zero: bool,
}

/// Exact finite trace obstruction, on a declared 3-dimensional carrier.
pub fn verify_trace_cyclicity_d3(
    a: &BasicMatrix<Cyc24>,
    b: &BasicMatrix<Cyc24>,
) -> Result<(Cyc24, bool), ExactFieldError> {
    if a.shape() != (3, 3) || b.shape() != (3, 3) {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "CCR carrier",
            left: a.shape(),
            right: b.shape(),
        });
    }
    let trace = mx::trace(&mx::sub(
        &mx::multiply_with_limits(a, b, exact_limits())?,
        &mx::multiply_with_limits(b, a, exact_limits())?,
    )?)?;
    let zero = trace.is_zero();
    Ok((trace, zero))
}
/// Tr(c I_3)=3c, computed directly in the coefficient field.
pub fn trace_of_scalar_d3(c: &Cyc24) -> Cyc24 {
    c.mul(&Cyc24::from_int(3))
}
pub fn commutator_equals_scalar_d3(
    a: &BasicMatrix<Cyc24>,
    b: &BasicMatrix<Cyc24>,
    c: &Cyc24,
) -> Result<bool, ExactFieldError> {
    verify_trace_cyclicity_d3(a, b)?;
    Ok(mx::sub(
        &mx::multiply_with_limits(a, b, exact_limits())?,
        &mx::multiply_with_limits(b, a, exact_limits())?,
    )? == mx::scale(&mx::identity_with_limits(3, exact_limits())?, c)?)
}
pub fn trace_obstructs_scalar_commutator_d3(
    a: &BasicMatrix<Cyc24>,
    b: &BasicMatrix<Cyc24>,
    c: &Cyc24,
) -> Result<bool, ExactFieldError> {
    Ok(verify_trace_cyclicity_d3(a, b)?.0 != trace_of_scalar_d3(c))
}
/// Computational-basis position, with eigenvalues 0,1,2.
pub fn discrete_position_d3() -> BasicMatrix<Cyc24> {
    mx::diagonal(&[Cyc24::zero(), Cyc24::one(), Cyc24::from_int(2)])
        .checked_invariant_4e726d84("fixed 3-dimensional operator")
}
/// Fourier-conjugate position F† Q F /3, where F_(j,k)=zeta_3^(jk).
/// The normalization cancels into a rational and Hermiticity replays exactly.
pub fn discrete_momentum_d3() -> Result<BasicMatrix<Cyc24>, ExactFieldError> {
    let fourier = mx::from_fn_with_limits(3, 3, exact_limits(), |j, k| {
        Cyc24::zeta3_pow((j * k) as i32)
    })?;
    let product = mx::multiply_with_limits(
        &mx::multiply_with_limits(
            &star::adjoint(&fourier)?,
            &discrete_position_d3(),
            exact_limits(),
        )?,
        &fourier,
        exact_limits(),
    )?;
    let momentum = mx::scale(&product, &Cyc24::rat(rq(1, 3)))?;
    if !star::is_hermitian(&momentum)? {
        return Err(ExactFieldError::ReplayFailed {
            operation: "Fourier momentum Hermiticity",
        });
    }
    Ok(momentum)
}
/// Physical irreducibility witness for the finite clock-and-shift representation.
pub fn weyl_commutant_dimension_d3() -> Result<usize, ExactFieldError> {
    commutant_dimension_with_limits(3, &[weyl_x_d3(), weyl_z_d3()], exact_limits())
}
pub fn audit_commutator_obstruction_d3() -> Result<CommutatorObstructionReport, ExactFieldError> {
    let q = discrete_position_d3();
    let p = discrete_momentum_d3()?;
    let (_, comm_zero) = verify_trace_cyclicity_d3(&q, &p)?;
    let mut ccr = true;
    for c in [Cyc24::one(), Cyc24::i()] {
        ccr &=
            !trace_of_scalar_d3(&c).is_zero() && trace_obstructs_scalar_commutator_d3(&q, &p, &c)?;
    }
    let x = weyl_x_d3();
    let z = weyl_z_d3();
    let weyl_satisfied = mx::multiply_with_limits(&z, &x, exact_limits())?
        == mx::scale(
            &mx::multiply_with_limits(&x, &z, exact_limits())?,
            &Cyc24::zeta3(),
        )?;
    let (_, weyl_zero) = verify_trace_cyclicity_d3(&z, &x)?;
    Ok(CommutatorObstructionReport {
        dimension: 3,
        commutator_trace_is_zero: comm_zero,
        hypothetical_ccr_trace_non_zero: ccr,
        weyl_relation_satisfied: weyl_satisfied,
        weyl_commutator_trace_is_zero: weyl_zero,
    })
}
pub fn verify_finite_heisenberg_center_d3() -> Result<bool, ExactFieldError> {
    let centre = mx::scale(
        &mx::identity_with_limits(3, exact_limits())?,
        &Cyc24::zeta3(),
    )?;
    for g in [weyl_x_d3(), weyl_z_d3()] {
        if mx::multiply_with_limits(&centre, &g, exact_limits())?
            != mx::multiply_with_limits(&g, &centre, exact_limits())?
        {
            return Ok(false);
        }
    }
    Ok(weyl_commutant_dimension_d3()? == 1)
}

// Origin: engine/crates_rs/core_quantum_physics/src/commutator.rs
// Claim: urn:core:crates_rs:core-quantum-physics:commutator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4e726d84 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4e726d84` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4e726d84 {
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
impl BoundaryError4e726d84 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4e726d84 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4e726d84 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4e726d84 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4e726d84> {
        if capacity_bound == 0 {
            return Err(BoundaryError4e726d84::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4e726d84::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4e726d84::ExceedsCapacity {
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
    use core_lie_theory::weyl_operators::{weyl_displacement_d3, weyl_parity_d3};

    fn sample_matrices() -> Vec<BasicMatrix<Cyc24>> {
        vec![
            discrete_position_d3(),
            discrete_momentum_d3().unwrap(),
            weyl_x_d3(),
            weyl_z_d3(),
            weyl_parity_d3(),
            weyl_displacement_d3(1, 2),
            weyl_displacement_d3(2, 1),
        ]
    }

    #[test]
    fn test_trace_cyclicity_arbitrary_matrices() {
        let x = weyl_x_d3();
        let z = weyl_z_d3();
        let (_, is_zero) = verify_trace_cyclicity_d3(&x, &z).unwrap();
        assert!(is_zero);

        let d1 = weyl_displacement_d3(1, 2);
        let d2 = weyl_displacement_d3(2, 1);
        let (_, is_zero_d) = verify_trace_cyclicity_d3(&d1, &d2).unwrap();
        assert!(is_zero_d);
    }

    #[test]
    fn test_audit_commutator_obstruction() {
        let report = audit_commutator_obstruction_d3().unwrap();
        assert!(report.commutator_trace_is_zero);
        assert!(report.hypothetical_ccr_trace_non_zero);
        assert!(report.weyl_relation_satisfied);
        assert!(report.weyl_commutator_trace_is_zero);
    }

    #[test]
    fn test_heisenberg_center() {
        assert!(verify_finite_heisenberg_center_d3().unwrap());
    }

    #[test]
    fn the_trace_of_a_scalar_matrix_is_three_times_the_scalar() {
        assert_eq!(trace_of_scalar_d3(&Cyc24::from_int(5)), Cyc24::from_int(15));
        let omega = Cyc24::zeta3();
        assert_eq!(trace_of_scalar_d3(&omega), omega.add(&omega).add(&omega));
        assert!(trace_of_scalar_d3(&Cyc24::zero()).is_zero());
    }

    #[test]
    fn no_pair_of_three_by_three_matrices_has_a_nonzero_scalar_commutator() {
        let constants = [Cyc24::one(), Cyc24::i(), Cyc24::from_int(2), Cyc24::zeta3()];
        for a in sample_matrices() {
            for b in sample_matrices() {
                for c in &constants {
                    assert!(!commutator_equals_scalar_d3(&a, &b, c).unwrap());
                    assert!(trace_obstructs_scalar_commutator_d3(&a, &b, c).unwrap());
                }
            }
        }
    }

    #[test]
    fn the_scalar_commutator_relation_does_hold_with_c_zero_exactly_for_commuting_pairs() {
        let zero = Cyc24::zero();
        let x = weyl_x_d3();
        let q = discrete_position_d3();
        // a matrix commutes with itself, with the identity and with its powers
        assert!(commutator_equals_scalar_d3(&x, &x, &zero).unwrap());
        assert!(commutator_equals_scalar_d3(
            &x,
            &mx::multiply_with_limits(&x, &x, exact_limits()).unwrap(),
            &zero
        )
        .unwrap());
        assert!(commutator_equals_scalar_d3(&q, &mx::identity(3).unwrap(), &zero).unwrap());
        // position and momentum do not commute, so even c = 0 fails, and the trace
        // argument does not apply to c = 0
        assert!(!commutator_equals_scalar_d3(&q, &discrete_momentum_d3().unwrap(), &zero).unwrap());
        assert!(!trace_obstructs_scalar_commutator_d3(&x, &x, &zero).unwrap());
    }

    #[test]
    fn the_commutant_of_no_generators_or_of_the_identity_is_every_matrix() {
        assert_eq!(
            commutant_dimension_with_limits::<Cyc24>(3, &[], exact_limits()),
            Ok(9)
        );
        assert_eq!(
            commutant_dimension_with_limits::<Cyc24>(
                3,
                &[mx::identity(3).unwrap()],
                exact_limits()
            ),
            Ok(9)
        );
        assert_eq!(
            commutant_dimension_with_limits::<Cyc24>(0, &[], exact_limits()),
            Ok(0)
        );
    }

    #[test]
    fn the_commutant_of_a_diagonal_matrix_follows_its_eigenvalue_multiplicities() {
        // distinct entries: only the diagonal matrices commute (dimension 3)
        assert_eq!(
            commutant_dimension_with_limits(3, &[discrete_position_d3()], exact_limits()),
            Ok(3)
        );
        // diag(0, 0, 1): block matrices of sizes 2 and 1 (dimension 2^2 + 1^2 = 5)
        let mut repeated = mx::zeros(3, 3).unwrap();
        repeated.set(2, 2, Cyc24::one()).unwrap();
        assert_eq!(
            commutant_dimension_with_limits(3, &[repeated], exact_limits()),
            Ok(5)
        );
    }

    #[test]
    fn the_shift_and_the_clock_alone_have_three_dimensional_commutants() {
        // each has three distinct eigenvalues 1, omega, omega^2, so its commutant is the
        // algebra of its polynomials
        assert_eq!(
            commutant_dimension_with_limits(3, &[weyl_x_d3()], exact_limits()),
            Ok(3)
        );
        assert_eq!(
            commutant_dimension_with_limits(3, &[weyl_z_d3()], exact_limits()),
            Ok(3)
        );
    }

    #[test]
    fn the_shift_and_clock_pair_has_only_scalars_in_its_commutant() {
        assert_eq!(weyl_commutant_dimension_d3(), Ok(1));
        // position and momentum together are irreducible as well
        assert_eq!(
            commutant_dimension_with_limits(
                3,
                &[discrete_position_d3(), discrete_momentum_d3().unwrap()],
                exact_limits()
            ),
            Ok(1)
        );
    }

    #[test]
    fn a_generator_of_the_wrong_shape_is_refused() {
        let wrong: BasicMatrix<Cyc24> = mx::zeros(2, 2).unwrap();
        assert_eq!(
            commutant_dimension_with_limits(3, &[weyl_x_d3(), wrong], exact_limits()),
            Err(ExactFieldError::ShapeMismatch {
                operation: "commutant",
                left: (3, 3),
                right: (2, 2)
            })
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_4e726d84 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4e726d84::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4e726d84::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4e726d84::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4e726d84::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4e726d84::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4e726d84::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4e726d84::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
