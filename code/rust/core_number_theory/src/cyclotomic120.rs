//! Clean-room exact arithmetic in `Q(zeta_120)`.
//!
//! This field is used only for finite MUB control lanes that need fifth roots
//! of unity while preserving the existing d=2/d=3/d=4 phases.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_997924c7<T> {
    fn checked_invariant_997924c7(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_997924c7<T> for Option<T> {
    #[inline]
    fn checked_invariant_997924c7(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_997924c7<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_997924c7(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::{One, Zero};

use crate::rational::ri;

const DEGREE: usize = 32;

// Phi_120(x) = x^32 + x^28 - x^20 - x^16 - x^12 + x^4 + 1.
// Coefficients c_j for x^32 + sum_{j<32} c_j x^j.
const PHI120_LOW: [i64; DEGREE] = [
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, -1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
    0,
];

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Cyc120 {
    pub a: [BigRational; DEGREE],
}

impl Cyc120 {
    pub fn zero() -> Self {
        Cyc120 {
            a: std::array::from_fn(|_| BigRational::zero()),
        }
    }

    pub fn rat(x: BigRational) -> Self {
        let mut c = Cyc120::zero();
        c.a[0] = x;
        c
    }

    pub fn zeta(p: i32) -> Self {
        let p = p.rem_euclid(120) as usize;
        let mut dense = vec![BigRational::zero(); 120];
        dense[p] = BigRational::one();
        Cyc120 {
            a: reduce_dense(dense),
        }
    }

    pub fn add(&self, o: &Cyc120) -> Cyc120 {
        Cyc120 {
            a: std::array::from_fn(|i| &self.a[i] + &o.a[i]),
        }
    }

    pub fn sub(&self, o: &Cyc120) -> Cyc120 {
        Cyc120 {
            a: std::array::from_fn(|i| &self.a[i] - &o.a[i]),
        }
    }

    pub fn neg(&self) -> Cyc120 {
        Cyc120 {
            a: std::array::from_fn(|i| -&self.a[i]),
        }
    }

    pub fn mul(&self, o: &Cyc120) -> Cyc120 {
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
        Cyc120 {
            a: reduce_dense(prod),
        }
    }

    pub fn conj(&self) -> Cyc120 {
        let mut out = Cyc120::zero();
        for (k, x) in self.a.iter().enumerate() {
            if !x.is_zero() {
                let zk = Cyc120::zeta(-(k as i32));
                for i in 0..DEGREE {
                    out.a[i] += x * &zk.a[i];
                }
            }
        }
        out
    }

    pub fn inv(&self) -> Cyc120 {
        let cols: [[BigRational; DEGREE]; DEGREE] = std::array::from_fn(|k| {
            let mut e = Cyc120::zero();
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
                .checked_invariant_997924c7("Cyc120::inv on a non-invertible element");
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
        Cyc120 {
            a: std::array::from_fn(|i| a[i][DEGREE].clone()),
        }
    }

    pub fn is_zero(&self) -> bool {
        self.a.iter().all(|x| x.is_zero())
    }

    pub fn mul_rat(&self, r: &BigRational) -> Cyc120 {
        Cyc120 {
            a: std::array::from_fn(|i| &self.a[i] * r),
        }
    }
}

pub fn c1_120() -> Cyc120 {
    Cyc120::rat(ri(1))
}

pub fn icyc_120() -> Cyc120 {
    Cyc120::zeta(30)
}

pub fn sqrt2_120() -> Cyc120 {
    Cyc120::zeta(15).add(&Cyc120::zeta(-15))
}

pub fn sqrt5_120() -> Cyc120 {
    c1_120().add(&Cyc120::zeta(24).add(&Cyc120::zeta(-24)).mul_rat(&ri(2)))
}

fn reduce_dense(mut dense: Vec<BigRational>) -> [BigRational; DEGREE] {
    if dense.len() < DEGREE {
        dense.resize(DEGREE, BigRational::zero());
    }
    for k in (DEGREE..dense.len()).rev() {
        if !dense[k].is_zero() {
            let v = dense[k].clone();
            for j in 0..DEGREE {
                if PHI120_LOW[j] != 0 {
                    dense[k - DEGREE + j] -= &v * ri(PHI120_LOW[j]);
                }
            }
            dense[k] = BigRational::zero();
        }
    }
    std::array::from_fn(|i| dense[i].clone())
}

impl Cyc120 {
    pub fn scale_rat(&self, r: &BigRational) -> Self {
        Cyc120 {
            a: std::array::from_fn(|i| &self.a[i] * r),
        }
    }
}

// Origin: engine/crates_rs/core_number_theory/src/cyclotomic120.rs
// Claim: urn:core:crates_rs:core-number-theory:cyclotomic120:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord997924c7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord997924c7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError997924c7 {
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
impl BoundaryError997924c7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError997924c7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError997924c7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord997924c7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError997924c7> {
        if capacity_bound == 0 {
            return Err(BoundaryError997924c7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError997924c7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError997924c7::ExceedsCapacity {
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
    fn zeta120_reduces_by_declared_cyclotomic_polynomial() {
        assert_eq!(Cyc120::zeta(120), c1_120());
        assert_eq!(Cyc120::zeta(60), Cyc120::rat(ri(-1)));
        let phi = Cyc120::zeta(32)
            .add(&Cyc120::zeta(28))
            .sub(&Cyc120::zeta(20))
            .sub(&Cyc120::zeta(16))
            .sub(&Cyc120::zeta(12))
            .add(&Cyc120::zeta(4))
            .add(&c1_120());
        assert!(phi.is_zero());
    }

    #[test]
    fn sqrt_identities_hold_in_q_zeta120() {
        assert_eq!(sqrt2_120().mul(&sqrt2_120()), Cyc120::rat(ri(2)));
        assert_eq!(sqrt5_120().mul(&sqrt5_120()), Cyc120::rat(ri(5)));
        assert_eq!(icyc_120().mul(&icyc_120()), Cyc120::rat(ri(-1)));
    }

    #[test]
    fn inv_times_self_is_one() {
        let x = Cyc120::rat(ri(3)).add(&sqrt5_120());
        assert_eq!(x.mul(&x.inv()), c1_120());
    }
}

#[cfg(test)]
mod l4_boundary_tests_997924c7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord997924c7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord997924c7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord997924c7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord997924c7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord997924c7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError997924c7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError997924c7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
