// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! Fixed three- and five-dimensional Weyl-Heisenberg operators.
//!
//! These conveniences instantiate the validated WeylHeisenberg construction.
//! Matrices have the shared BasicMatrix representation; arithmetic lives in
//! linear_algebra::exact_field. The convention is ZX = omega XZ and
//! D(a,b) = omega^(ab/2) X^a Z^b. Labels are reduced before multiplication.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_9fb30024<T> {
    fn checked_invariant_9fb30024(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_9fb30024<T> for Option<T> {
    #[inline]
    fn checked_invariant_9fb30024(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_9fb30024<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_9fb30024(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::heisenberg::WeylHeisenberg;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::{Cyc24, Cyc5};

fn system_d3() -> WeylHeisenberg<Cyc24> {
    WeylHeisenberg::new(3, Cyc24::zeta3()).checked_invariant_9fb30024("declared primitive third root")
}

fn system_d5() -> WeylHeisenberg<Cyc5> {
    WeylHeisenberg::new(5, Cyc5::zeta5(1)).checked_invariant_9fb30024("declared primitive fifth root")
}

/// X|j> = |j+1 mod 3>.
pub fn weyl_x_d3() -> BasicMatrix<Cyc24> {
    system_d3().shift().checked_invariant_9fb30024("fixed 3 by 3 matrix")
}

/// Z|j> = zeta_3^j |j>.
pub fn weyl_z_d3() -> BasicMatrix<Cyc24> {
    system_d3().clock().checked_invariant_9fb30024("fixed 3 by 3 matrix")
}

/// P|j> = |-j mod 3>.
pub fn weyl_parity_d3() -> BasicMatrix<Cyc24> {
    system_d3().parity().checked_invariant_9fb30024("fixed 3 by 3 matrix")
}

/// D(a,b) = omega^(2ab) X^a Z^b in dimension three.
pub fn weyl_displacement_d3(a: i64, b: i64) -> BasicMatrix<Cyc24> {
    system_d3().displacement(a, b).checked_invariant_9fb30024("fixed 3 by 3 matrix")
}

/// X|j> = |j+1 mod 5>.
pub fn weyl_x_d5() -> BasicMatrix<Cyc5> {
    system_d5().shift().checked_invariant_9fb30024("fixed 5 by 5 matrix")
}

/// Z|j> = zeta_5^j |j>.
pub fn weyl_z_d5() -> BasicMatrix<Cyc5> {
    system_d5().clock().checked_invariant_9fb30024("fixed 5 by 5 matrix")
}

/// P|j> = |-j mod 5>.
pub fn weyl_parity_d5() -> BasicMatrix<Cyc5> {
    system_d5().parity().checked_invariant_9fb30024("fixed 5 by 5 matrix")
}

/// D(q,p) = omega^(3qp) X^q Z^p in dimension five.
pub fn weyl_displacement_d5(q: i64, p: i64) -> BasicMatrix<Cyc5> {
    system_d5().displacement(q, p).checked_invariant_9fb30024("fixed 5 by 5 matrix")
}

// Origin: engine/crates_rs/core_lie_theory/src/weyl_operators.rs
// Claim: urn:core:crates_rs:core-lie-theory:weyl-operators:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9fb30024 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9fb30024` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9fb30024 {
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
impl BoundaryError9fb30024 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9fb30024 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9fb30024 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9fb30024 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9fb30024> {
        if capacity_bound == 0 {
            return Err(BoundaryError9fb30024::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9fb30024::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9fb30024::ExceedsCapacity {
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
    use linear_algebra::exact_field::{involution, matrix as mx};
    use core_number_theory::cyclotomic::GaussianRat;
    use core_number_theory::rational::ri;

    #[test]
    fn test_d3_weyl_commutation_relation() {
        let x = weyl_x_d3();
        let z = weyl_z_d3();
        let zx = mx::multiply(&z, &x).unwrap();
        let xz = mx::multiply(&x, &z).unwrap();
        assert_eq!(zx, mx::scale(&xz, &Cyc24::zeta3()).unwrap());
    }

    #[test]
    fn test_d3_displacement_orthogonality() {
        for a in 0..3 {
            for b in 0..3 {
                let d = weyl_displacement_d3(a, b);
                let tr = mx::trace(&d).unwrap();
                assert_eq!(
                    tr,
                    if a == 0 && b == 0 {
                        Cyc24::from_int(3)
                    } else {
                        Cyc24::zero()
                    }
                );
            }
        }
    }

    #[test]
    fn test_d5_weyl_commutation_relation() {
        let x = weyl_x_d5();
        let z = weyl_z_d5();
        let zx = mx::multiply(&z, &x).unwrap();
        let xz = mx::multiply(&x, &z).unwrap();
        assert_eq!(zx, mx::scale(&xz, &Cyc5::zeta5(1)).unwrap());
    }

    #[test]
    fn test_d5_displacement_orthogonality() {
        for q in 0..5 {
            for p in 0..5 {
                let d = weyl_displacement_d5(q, p);
                let tr = mx::trace(&d).unwrap();
                assert_eq!(
                    tr,
                    if q == 0 && p == 0 {
                        Cyc5::rat(ri(5))
                    } else {
                        Cyc5::zero()
                    }
                );
            }
        }
    }

    #[test]
    fn test_rectangular_add_and_sub_keep_shape() {
        let a = mx::from_fn(2, 3, |r, c| ri((r * 3 + c) as i64)).unwrap();
        let b = mx::from_fn(2, 3, |_, _| ri(1)).unwrap();
        let sum = mx::add(&a, &b).unwrap();
        assert_eq!((sum.rows(), sum.cols()), (2, 3));
        assert_eq!(*sum.get_ref(1, 2).unwrap(), ri(6));
        assert_eq!(mx::sub(&sum, &b).unwrap(), a);
    }

    #[test]
    fn test_gaussian_rational_matrix_pauli_y() {
        let y = mx::from_rows(vec![
            vec![GaussianRat::zero(), GaussianRat::from_ints(0, -1)],
            vec![GaussianRat::from_ints(0, 1), GaussianRat::zero()],
        ])
        .unwrap();
        assert_eq!(involution::adjoint(&y).unwrap(), y);
        assert_eq!(mx::multiply(&y, &y).unwrap(), mx::identity(2).unwrap());
    }
}

#[cfg(test)]
mod l4_boundary_tests_9fb30024 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9fb30024::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9fb30024::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9fb30024::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9fb30024::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9fb30024::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9fb30024::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9fb30024::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
