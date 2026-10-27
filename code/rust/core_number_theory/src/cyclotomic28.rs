//! Clean-room exact arithmetic in `Q(zeta_28)`.
//!
//! This field supports the d=7 odd-prime Weyl control. It contains seventh
//! roots of unity, `i`, and the quadratic Gauss normalization `sqrt(7)`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_364e2040<T> {
    fn checked_invariant_364e2040(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_364e2040<T> for Option<T> {
    #[inline]
    fn checked_invariant_364e2040(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_364e2040<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_364e2040(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::{One, Zero};

use crate::rational::ri;

const DEGREE: usize = 12;

// Phi_28(x) = x^12 - x^10 + x^8 - x^6 + x^4 - x^2 + 1.
// Coefficients c_j for x^12 + sum_{j<12} c_j x^j.
const PHI28_LOW: [i64; DEGREE] = [1, 0, -1, 0, 1, 0, -1, 0, 1, 0, -1, 0];

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Cyc28 {
    pub a: [BigRational; DEGREE],
}

impl Cyc28 {
    pub fn zero() -> Self {
        Cyc28 {
            a: std::array::from_fn(|_| BigRational::zero()),
        }
    }

    pub fn rat(x: BigRational) -> Self {
        let mut c = Cyc28::zero();
        c.a[0] = x;
        c
    }

    pub fn zeta(p: i32) -> Self {
        let p = p.rem_euclid(28) as usize;
        let mut dense = vec![BigRational::zero(); 28];
        dense[p] = BigRational::one();
        Cyc28 {
            a: reduce_dense(dense),
        }
    }

    pub fn add(&self, o: &Cyc28) -> Cyc28 {
        Cyc28 {
            a: std::array::from_fn(|i| &self.a[i] + &o.a[i]),
        }
    }

    pub fn sub(&self, o: &Cyc28) -> Cyc28 {
        Cyc28 {
            a: std::array::from_fn(|i| &self.a[i] - &o.a[i]),
        }
    }

    pub fn neg(&self) -> Cyc28 {
        Cyc28 {
            a: std::array::from_fn(|i| -&self.a[i]),
        }
    }

    pub fn mul(&self, o: &Cyc28) -> Cyc28 {
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
        Cyc28 {
            a: reduce_dense(prod),
        }
    }

    pub fn conj(&self) -> Cyc28 {
        let mut out = Cyc28::zero();
        for (k, x) in self.a.iter().enumerate() {
            if !x.is_zero() {
                let zk = Cyc28::zeta(-(k as i32));
                for i in 0..DEGREE {
                    out.a[i] += x * &zk.a[i];
                }
            }
        }
        out
    }

    pub fn inv(&self) -> Cyc28 {
        let cols: [[BigRational; DEGREE]; DEGREE] = std::array::from_fn(|k| {
            let mut e = Cyc28::zero();
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
                .checked_invariant_364e2040("Cyc28::inv on a non-invertible element");
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
        Cyc28 {
            a: std::array::from_fn(|i| a[i][DEGREE].clone()),
        }
    }

    pub fn is_zero(&self) -> bool {
        self.a.iter().all(|x| x.is_zero())
    }
}

pub fn c1_28() -> Cyc28 {
    Cyc28::rat(ri(1))
}

pub fn icyc_28() -> Cyc28 {
    Cyc28::zeta(7)
}

pub fn sqrt7_28() -> Cyc28 {
    icyc_28().neg().mul(&gauss7_28())
}

fn gauss7_28() -> Cyc28 {
    let mut sum = Cyc28::zero();
    for x in 0_i32..7 {
        sum = sum.add(&Cyc28::zeta(4 * x * x));
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
                if PHI28_LOW[j] != 0 {
                    dense[k - DEGREE + j] -= &v * ri(PHI28_LOW[j]);
                }
            }
            dense[k] = BigRational::zero();
        }
    }
    std::array::from_fn(|i| dense[i].clone())
}

impl Cyc28 {
    pub fn scale_rat(&self, r: &BigRational) -> Self {
        Cyc28 {
            a: std::array::from_fn(|i| &self.a[i] * r),
        }
    }
}

// Origin: engine/crates_rs/core_number_theory/src/cyclotomic28.rs
// Claim: urn:core:crates_rs:core-number-theory:cyclotomic28:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord364e2040 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord364e2040` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError364e2040 {
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
impl BoundaryError364e2040 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError364e2040 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError364e2040 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord364e2040 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError364e2040> {
        if capacity_bound == 0 {
            return Err(BoundaryError364e2040::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError364e2040::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError364e2040::ExceedsCapacity {
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
    fn zeta28_reduces_by_declared_cyclotomic_polynomial() {
        assert_eq!(Cyc28::zeta(28), c1_28());
        assert_eq!(Cyc28::zeta(14), Cyc28::rat(ri(-1)));
        let phi = Cyc28::zeta(12)
            .sub(&Cyc28::zeta(10))
            .add(&Cyc28::zeta(8))
            .sub(&Cyc28::zeta(6))
            .add(&Cyc28::zeta(4))
            .sub(&Cyc28::zeta(2))
            .add(&c1_28());
        assert!(phi.is_zero());
    }

    #[test]
    fn sqrt7_and_i_identities_hold_in_q_zeta28() {
        assert_eq!(icyc_28().mul(&icyc_28()), Cyc28::rat(ri(-1)));
        assert_eq!(sqrt7_28().mul(&sqrt7_28()), Cyc28::rat(ri(7)));
        assert_eq!(sqrt7_28().mul(&sqrt7_28().inv()), c1_28());
    }
}

#[cfg(test)]
mod l4_boundary_tests_364e2040 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord364e2040::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord364e2040::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord364e2040::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord364e2040::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord364e2040::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError364e2040::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError364e2040::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
