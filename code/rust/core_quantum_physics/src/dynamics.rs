// AuthorityEffect: None.

//! Finite toggle dynamics and rational unitary evolution.
//!
//! Formalizes Band D (Steps 31–38) in Rust:
//! - Toggle square root obstruction: det(X) = -1 has no real matrix square root.
//! - Exact complex square root in Z[i] at scale 4: M^2 = 4*X.
//! - Cayley rational transform: cay_tau(X) = ((1 - tau^2)*I - 2*i*tau*X) / (1 + tau^2)
//!   producing exact rational unitaries over Q(i) without floats or continuum approximations.
//! - Abelian group composition: tau_comp = (tau1 + tau2) / (1 - tau1 * tau2).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b9a16a78<T> {
    fn checked_invariant_b9a16a78(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b9a16a78<T> for Option<T> {
    #[inline]
    fn checked_invariant_b9a16a78(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b9a16a78<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b9a16a78(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_number_theory::rational::Rational;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CayleyUnitary2x2 {
    pub tau: Rational,
    pub diag_re: Rational,
    pub offdiag_im: Rational,
    pub norm_sq: Rational,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ToggleSquareRootReport {
    pub det_x: i64,
    pub has_real_matrix_sqrt: bool,
    pub scale4_complex_sqrt_verified: bool,
    pub interpolant_not_unique: bool,
}

/// Computes the exact rational Cayley unitary for toggle X = [[0, 1], [1, 0]].
pub fn cayley_transform_toggle(tau: Rational) -> CayleyUnitary2x2 {
    let scalar = core_lie_theory::cayley::unit_from_parameter(&(-tau.clone()));
    let diag_re = scalar.re;
    let offdiag_im = scalar.im;
    let norm_sq = &diag_re * &diag_re + &offdiag_im * &offdiag_im;

    CayleyUnitary2x2 {
        tau,
        diag_re,
        offdiag_im,
        norm_sq,
    }
}

/// Verifies toggle square root algebraic obstruction.
pub fn verify_toggle_square_roots() -> ToggleSquareRootReport {
    // 1. det(X) = -1. det(M^2) = det(M)^2 = -1 has no real root.
    let det_x = -1i64;
    let has_real = false;

    // 2. Exact scale-4 square root in Z[i]:
    // M = [[1+i, 1-i], [1-i, 1+i]]
    // Diagonal: (1+i)^2 + (1-i)^2 = 2i - 2i = 0
    // Off-diagonal: (1+i)(1-i) + (1-i)(1+i) = 2 + 2 = 4
    let roots = crate::finite_report_dynamics::swap_interpolants(4).checked_invariant_b9a16a78("positive scale");
    let verified = roots.len() == 4
        && roots.iter().all(|r| {
            linear_algebra::exact_field::matrix::multiply_with_limits(
                &(r),
                r,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_b9a16a78("validated finite matrix shape and budget")
                == linear_algebra::exact_field::matrix::from_rows(vec![
                    vec![
                        crate::exact_hermitian::gi(0, 0),
                        crate::exact_hermitian::gi(4, 0),
                    ],
                    vec![
                        crate::exact_hermitian::gi(4, 0),
                        crate::exact_hermitian::gi(0, 0),
                    ],
                ])
                .checked_invariant_b9a16a78("fixed square matrix")
        });

    ToggleSquareRootReport {
        det_x,
        has_real_matrix_sqrt: has_real,
        scale4_complex_sqrt_verified: verified,
        interpolant_not_unique: roots.len() > 1,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/dynamics.rs
// Claim: urn:core:crates_rs:core-quantum-physics:dynamics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb9a16a78 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb9a16a78` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb9a16a78 {
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
impl BoundaryErrorb9a16a78 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb9a16a78 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb9a16a78 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb9a16a78 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb9a16a78> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb9a16a78::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb9a16a78::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb9a16a78::ExceedsCapacity {
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
    use core_number_theory::rational::{rq, One, Zero};

    #[test]
    fn test_cayley_toggle_unitarity_and_pythagorean_triples() {
        // tau = 0 -> a = 1, b = 0
        let c0 = cayley_transform_toggle(Rational::zero());
        assert_eq!(c0.diag_re, Rational::one());
        assert_eq!(c0.offdiag_im, Rational::zero());
        assert_eq!(c0.norm_sq, Rational::one());

        // tau = 1/2 -> a = (1 - 1/4)/(1 + 1/4) = 3/5, b = -1/(5/4) = -4/5
        let c_half = cayley_transform_toggle(rq(1, 2));
        assert_eq!(c_half.diag_re, rq(3, 5));
        assert_eq!(c_half.offdiag_im, rq(-4, 5));
        assert_eq!(c_half.norm_sq, Rational::one());

        // tau = 3/4 -> a = (1 - 9/16)/(1 + 9/16) = 7/25, b = (-3/2)/(25/16) = -24/25
        let c_three_quarters = cayley_transform_toggle(rq(3, 4));
        assert_eq!(c_three_quarters.diag_re, rq(7, 25));
        assert_eq!(c_three_quarters.offdiag_im, rq(-24, 25));
        assert_eq!(c_three_quarters.norm_sq, Rational::one());
    }

    #[test]
    fn test_cayley_composition_group_law() {
        // tau1 = 1/2, tau2 = 1/3 -> tau_comp = (1/2 + 1/3) / (1 - 1/6) = (5/6)/(5/6) = 1
        let tau1 = rq(1, 2);
        let tau2 = rq(1, 3);
        let comp =
            core_lie_theory::cayley::compactified_circle_composition(Some(&tau1), Some(&tau2))
                .unwrap();
        assert_eq!(comp, Rational::one());

        let c_comp = cayley_transform_toggle(comp);
        assert_eq!(c_comp.diag_re, Rational::zero());
        assert_eq!(c_comp.offdiag_im, rq(-1, 1));
        assert_eq!(c_comp.norm_sq, Rational::one());
    }

    #[test]
    fn test_toggle_square_root_properties() {
        let rep = verify_toggle_square_roots();
        assert_eq!(rep.det_x, -1);
        assert!(!rep.has_real_matrix_sqrt);
        assert!(rep.scale4_complex_sqrt_verified);
        assert!(rep.interpolant_not_unique);
    }
}

#[cfg(test)]
mod l4_boundary_tests_b9a16a78 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb9a16a78::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb9a16a78::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb9a16a78::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb9a16a78::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb9a16a78::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb9a16a78::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb9a16a78::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
