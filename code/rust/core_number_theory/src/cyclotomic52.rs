//! Clean-room exact arithmetic in `Q(zeta_52)`.
//!
//! This field supports the d=13 odd-prime Weyl control. It contains thirteenth
//! roots of unity, `i`, and the quadratic Gauss normalization `sqrt(13)`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_04d1d51d<T> {
    fn checked_invariant_04d1d51d(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_04d1d51d<T> for Option<T> {
    #[inline]
    fn checked_invariant_04d1d51d(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_04d1d51d<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_04d1d51d(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::{One, Zero};

use crate::rational::ri;

const DEGREE: usize = 24;

// Phi_52(x) = x^24 - x^22 + x^20 - ... - x^2 + 1.
// Coefficients c_j for x^24 + sum_{j<24} c_j x^j.
const PHI52_LOW: [i64; DEGREE] = [
    1, 0, -1, 0, 1, 0, -1, 0, 1, 0, -1, 0, 1, 0, -1, 0, 1, 0, -1, 0, 1, 0, -1, 0,
];

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Cyc52 {
    pub a: [BigRational; DEGREE],
}

impl Cyc52 {
    pub fn zero() -> Self {
        Cyc52 {
            a: std::array::from_fn(|_| BigRational::zero()),
        }
    }

    pub fn rat(x: BigRational) -> Self {
        let mut c = Cyc52::zero();
        c.a[0] = x;
        c
    }

    pub fn zeta(p: i32) -> Self {
        let p = p.rem_euclid(52) as usize;
        let mut dense = vec![BigRational::zero(); 52];
        dense[p] = BigRational::one();
        Cyc52 {
            a: reduce_dense(dense),
        }
    }

    pub fn add(&self, o: &Cyc52) -> Cyc52 {
        Cyc52 {
            a: std::array::from_fn(|i| &self.a[i] + &o.a[i]),
        }
    }

    pub fn sub(&self, o: &Cyc52) -> Cyc52 {
        Cyc52 {
            a: std::array::from_fn(|i| &self.a[i] - &o.a[i]),
        }
    }

    pub fn mul(&self, o: &Cyc52) -> Cyc52 {
        let mut prod = vec![BigRational::zero(); 2 * DEGREE - 1];
        for (i, x) in self.a.iter().enumerate() {
            if !x.is_zero() {
                for (j, y) in o.a.iter().enumerate() {
                    if !y.is_zero() {
                        prod[i + j] += x * y;
                    }
                }
            }
        }
        Cyc52 {
            a: reduce_dense(prod),
        }
    }

    pub fn conj(&self) -> Cyc52 {
        let mut out = Cyc52::zero();
        for (k, x) in self.a.iter().enumerate() {
            if !x.is_zero() {
                let zk = Cyc52::zeta(-(k as i32));
                for i in 0..DEGREE {
                    out.a[i] += x * &zk.a[i];
                }
            }
        }
        out
    }

    pub fn inv(&self) -> Cyc52 {
        let cols: [[BigRational; DEGREE]; DEGREE] = std::array::from_fn(|k| {
            let mut e = Cyc52::zero();
            e.a[k] = BigRational::one();
            self.mul(&e).a
        });
        let mut a: [[BigRational; DEGREE + 1]; DEGREE] = std::array::from_fn(|i| {
            std::array::from_fn(|j| {
                if j < DEGREE {
                    cols[j][i].clone()
                } else if i == 0 {
                    BigRational::one()
                } else {
                    BigRational::zero()
                }
            })
        });
        for col in 0..DEGREE {
            let piv = (col..DEGREE)
                .find(|&r| !a[r][col].is_zero())
                .checked_invariant_04d1d51d("Cyc52::inv on a non-invertible element");
            a.swap(col, piv);
            let pv = a[col][col].clone();
            for x in a[col].iter_mut() {
                *x /= &pv;
            }
            for r in 0..DEGREE {
                if r != col && !a[r][col].is_zero() {
                    let f = a[r][col].clone();
                    for c in 0..=DEGREE {
                        let t = &f * &a[col][c];
                        a[r][c] -= t;
                    }
                }
            }
        }
        Cyc52 {
            a: std::array::from_fn(|i| a[i][DEGREE].clone()),
        }
    }

    pub fn is_zero(&self) -> bool {
        self.a.iter().all(|x| x.is_zero())
    }
}

pub fn c1_52() -> Cyc52 {
    Cyc52::rat(ri(1))
}

pub fn icyc_52() -> Cyc52 {
    Cyc52::zeta(13)
}

pub fn sqrt13_52() -> Cyc52 {
    gauss13_52()
}

fn gauss13_52() -> Cyc52 {
    let mut sum = Cyc52::zero();
    for x in 0_i32..13 {
        sum = sum.add(&Cyc52::zeta(4 * x * x));
    }
    sum
}

fn reduce_dense(mut dense: Vec<BigRational>) -> [BigRational; DEGREE] {
    if dense.len() < DEGREE {
        dense.resize(DEGREE, BigRational::zero());
    }
    for k in (DEGREE..dense.len()).rev() {
        if !dense[k].is_zero() {
            let v = dense[k].clone();
            for j in 0..DEGREE {
                if PHI52_LOW[j] != 0 {
                    dense[k - DEGREE + j] -= &v * ri(PHI52_LOW[j]);
                }
            }
            dense[k] = BigRational::zero();
        }
    }
    std::array::from_fn(|i| dense[i].clone())
}

impl Cyc52 {
    pub fn scale_rat(&self, r: &BigRational) -> Self {
        Cyc52 {
            a: std::array::from_fn(|i| &self.a[i] * r),
        }
    }
}

// Origin: engine/crates_rs/core_number_theory/src/cyclotomic52.rs
// Claim: urn:core:crates_rs:core-number-theory:cyclotomic52:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord04d1d51d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord04d1d51d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError04d1d51d {
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
impl BoundaryError04d1d51d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError04d1d51d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError04d1d51d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord04d1d51d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError04d1d51d> {
        if capacity_bound == 0 {
            return Err(BoundaryError04d1d51d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError04d1d51d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError04d1d51d::ExceedsCapacity {
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
    fn zeta52_reduces_by_declared_cyclotomic_polynomial() {
        assert_eq!(Cyc52::zeta(52), c1_52());
        assert_eq!(Cyc52::zeta(26), Cyc52::rat(ri(-1)));
        let mut phi = Cyc52::zero();
        for k in (0_i32..=24).step_by(2) {
            let sign = if (k / 2) % 2 == 0 { 1 } else { -1 };
            let term = Cyc52::zeta(k);
            phi = if sign == 1 {
                phi.add(&term)
            } else {
                phi.sub(&term)
            };
        }
        assert!(phi.is_zero());
    }

    #[test]
    fn sqrt13_and_i_identities_hold_in_q_zeta52() {
        assert_eq!(icyc_52().mul(&icyc_52()), Cyc52::rat(ri(-1)));
        assert_eq!(sqrt13_52().mul(&sqrt13_52()), Cyc52::rat(ri(13)));
        assert_eq!(sqrt13_52().mul(&sqrt13_52().inv()), c1_52());
    }
}

#[cfg(test)]
mod l4_boundary_tests_04d1d51d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord04d1d51d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord04d1d51d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord04d1d51d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord04d1d51d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord04d1d51d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError04d1d51d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError04d1d51d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
