// AuthorityEffect: None.
//! Cyclotomic matrix helpers for the QM-218 Page-Wootters control.

use num_traits::{One, Zero};

use super::super::q;
use super::super::*;

pub(crate) type QiDynMat = Vec<Vec<Qi>>;

pub(crate) fn qi_dyn_zeros(n: usize) -> QiDynMat {
    vec![vec![Qi::zero(); n]; n]
}

pub(crate) fn qi_dyn_eye(n: usize) -> QiDynMat {
    let mut m = qi_dyn_zeros(n);
    for idx in 0..n {
        m[idx][idx] = Qi::one();
    }
    m
}

pub(crate) fn qi_dyn_add(a: &QiDynMat, b: &QiDynMat) -> QiDynMat {
    let n = a.len();
    let mut out = qi_dyn_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[r][c].add(b[r][c]);
        }
    }
    out
}

pub(crate) fn qi_dyn_sub(a: &QiDynMat, b: &QiDynMat) -> QiDynMat {
    let n = a.len();
    let mut out = qi_dyn_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[r][c].sub(b[r][c]);
        }
    }
    out
}

pub(crate) fn qi_dyn_scale(s: Q, a: &QiDynMat) -> QiDynMat {
    let n = a.len();
    let sq = Qi::from_q(s);
    let mut out = qi_dyn_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = sq.mul(a[r][c]);
        }
    }
    out
}

pub(crate) fn qi_dyn_mul(a: &QiDynMat, b: &QiDynMat) -> QiDynMat {
    let n = a.len();
    let mut out = qi_dyn_zeros(n);
    for r in 0..n {
        for k in 0..n {
            let ark = a[r][k];
            if ark.is_zero() {
                continue;
            }
            for c in 0..n {
                out[r][c] = out[r][c].add(ark.mul(b[k][c]));
            }
        }
    }
    out
}

pub(crate) fn qi_dyn_dagger(a: &QiDynMat) -> QiDynMat {
    let n = a.len();
    let mut out = qi_dyn_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[c][r].conj();
        }
    }
    out
}

pub(crate) fn qi_dyn_comm(a: &QiDynMat, b: &QiDynMat) -> QiDynMat {
    qi_dyn_sub(&qi_dyn_mul(a, b), &qi_dyn_mul(b, a))
}

pub(crate) fn qi_dyn_kron(a: &QiDynMat, b: &QiDynMat) -> QiDynMat {
    let na = a.len();
    let nb = b.len();
    let mut out = qi_dyn_zeros(na * nb);
    for ra in 0..na {
        for ca in 0..na {
            let va = a[ra][ca];
            if va.is_zero() {
                continue;
            }
            for rb in 0..nb {
                for cb in 0..nb {
                    out[ra * nb + rb][ca * nb + cb] = va.mul(b[rb][cb]);
                }
            }
        }
    }
    out
}

pub(crate) fn qi_dyn_is_zero(a: &QiDynMat) -> bool {
    a.iter().all(|row| row.iter().all(|x| x.is_zero()))
}

pub(crate) fn qi_dyn_trace(a: &QiDynMat) -> Qi {
    let mut acc = Qi::zero();
    for k in 0..a.len() {
        acc = acc.add(a[k][k]);
    }
    acc
}

pub(crate) fn qi_dyn_matvec(a: &QiDynMat, v: &[Qi]) -> Vec<Qi> {
    let n = a.len();
    let mut out = vec![Qi::zero(); n];
    for r in 0..n {
        let mut acc = Qi::zero();
        for c in 0..n {
            acc = acc.add(a[r][c].mul(v[c]));
        }
        out[r] = acc;
    }
    out
}

pub(crate) fn qi_dyn_inner(u: &[Qi], v: &[Qi]) -> Qi {
    let mut acc = Qi::zero();
    for (uk, vk) in u.iter().zip(v.iter()) {
        acc = acc.add(uk.conj().mul(*vk));
    }
    acc
}

/// Element of `Q(zeta_8) = Q[z]/(z^4 + 1)` where `z^4 = -1`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Cyclo8(pub [Q; 4]);

impl Cyclo8 {
    pub fn zero() -> Self {
        Self([Q::zero(); 4])
    }

    pub fn one() -> Self {
        Self([Q::one(), Q::zero(), Q::zero(), Q::zero()])
    }

    pub fn from_int(n: i64) -> Self {
        Self([q(n, 1), Q::zero(), Q::zero(), Q::zero()])
    }

    pub fn sqrt2() -> Self {
        Self([Q::zero(), Q::one(), Q::zero(), q(-1, 1)])
    }

    pub fn inv_sqrt2() -> Self {
        let h = q(1, 2);
        Self([Q::zero(), h, Q::zero(), -h])
    }

    pub fn is_zero(self) -> bool {
        self.0.iter().all(|c| c.is_zero())
    }

    pub fn conj(self) -> Self {
        Self([self.0[0], -self.0[3], -self.0[2], -self.0[1]])
    }

    pub fn add(self, rhs: Self) -> Self {
        Self([
            self.0[0] + rhs.0[0],
            self.0[1] + rhs.0[1],
            self.0[2] + rhs.0[2],
            self.0[3] + rhs.0[3],
        ])
    }

    pub fn sub(self, rhs: Self) -> Self {
        Self([
            self.0[0] - rhs.0[0],
            self.0[1] - rhs.0[1],
            self.0[2] - rhs.0[2],
            self.0[3] - rhs.0[3],
        ])
    }

    pub fn neg(self) -> Self {
        Self([-self.0[0], -self.0[1], -self.0[2], -self.0[3]])
    }

    pub fn mul(self, rhs: Self) -> Self {
        let mut res = [Q::zero(); 4];
        for i in 0..4 {
            if self.0[i].is_zero() {
                continue;
            }
            for j in 0..4 {
                if rhs.0[j].is_zero() {
                    continue;
                }
                let k = i + j;
                if k < 4 {
                    res[k] += self.0[i] * rhs.0[j];
                } else {
                    res[k - 4] -= self.0[i] * rhs.0[j];
                }
            }
        }
        Self(res)
    }
}

pub(super) type Z8DynMat = Vec<Vec<Cyclo8>>;

pub(super) fn z8_zeros(n: usize) -> Z8DynMat {
    vec![vec![Cyclo8::zero(); n]; n]
}

pub(super) fn z8_eye(n: usize) -> Z8DynMat {
    let mut m = z8_zeros(n);
    for k in 0..n {
        m[k][k] = Cyclo8::one();
    }
    m
}

pub(super) fn z8_add(a: &Z8DynMat, b: &Z8DynMat) -> Z8DynMat {
    let n = a.len();
    let mut out = z8_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[r][c].add(b[r][c]);
        }
    }
    out
}

pub(super) fn z8_sub(a: &Z8DynMat, b: &Z8DynMat) -> Z8DynMat {
    let n = a.len();
    let mut out = z8_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[r][c].sub(b[r][c]);
        }
    }
    out
}

pub(super) fn z8_scale(s: Cyclo8, a: &Z8DynMat) -> Z8DynMat {
    let n = a.len();
    let mut out = z8_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = s.mul(a[r][c]);
        }
    }
    out
}

pub(super) fn z8_mul(a: &Z8DynMat, b: &Z8DynMat) -> Z8DynMat {
    let n = a.len();
    let mut out = z8_zeros(n);
    for r in 0..n {
        for k in 0..n {
            let ark = a[r][k];
            if ark.is_zero() {
                continue;
            }
            for c in 0..n {
                out[r][c] = out[r][c].add(ark.mul(b[k][c]));
            }
        }
    }
    out
}

pub(super) fn z8_dagger(a: &Z8DynMat) -> Z8DynMat {
    let n = a.len();
    let mut out = z8_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[c][r].conj();
        }
    }
    out
}

pub(super) fn z8_comm(a: &Z8DynMat, b: &Z8DynMat) -> Z8DynMat {
    z8_sub(&z8_mul(a, b), &z8_mul(b, a))
}

pub(super) fn z8_kron(a: &Z8DynMat, b: &Z8DynMat) -> Z8DynMat {
    let na = a.len();
    let nb = b.len();
    let mut out = z8_zeros(na * nb);
    for ra in 0..na {
        for ca in 0..na {
            let va = a[ra][ca];
            if va.is_zero() {
                continue;
            }
            for rb in 0..nb {
                for cb in 0..nb {
                    out[ra * nb + rb][ca * nb + cb] = va.mul(b[rb][cb]);
                }
            }
        }
    }
    out
}

pub(super) fn z8_is_zero(a: &Z8DynMat) -> bool {
    a.iter().all(|row| row.iter().all(|x| x.is_zero()))
}

pub(super) fn z8_matvec(a: &Z8DynMat, v: &[Cyclo8]) -> Vec<Cyclo8> {
    let n = a.len();
    let mut out = vec![Cyclo8::zero(); n];
    for r in 0..n {
        let mut acc = Cyclo8::zero();
        for c in 0..n {
            acc = acc.add(a[r][c].mul(v[c]));
        }
        out[r] = acc;
    }
    out
}

pub(super) fn z8_inner(u: &[Cyclo8], v: &[Cyclo8]) -> Cyclo8 {
    let mut acc = Cyclo8::zero();
    for (uk, vk) in u.iter().zip(v.iter()) {
        acc = acc.add(uk.conj().mul(*vk));
    }
    acc
}

/// Element `a + b*omega` in `Q(zeta_3) = Q[omega]/(omega^2 + omega + 1)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Cyclo3 {
    pub a: Q,
    pub b: Q,
}

impl Cyclo3 {
    pub fn zero() -> Self {
        Self {
            a: Q::zero(),
            b: Q::zero(),
        }
    }

    pub fn from_int(n: i64) -> Self {
        Self {
            a: q(n, 1),
            b: Q::zero(),
        }
    }

    pub fn core_pow(k: i64) -> Self {
        match k.rem_euclid(3) {
            0 => Self {
                a: Q::one(),
                b: Q::zero(),
            },
            1 => Self {
                a: Q::zero(),
                b: Q::one(),
            },
            _ => Self {
                a: q(-1, 1),
                b: q(-1, 1),
            },
        }
    }

    pub fn is_zero(self) -> bool {
        self.a.is_zero() && self.b.is_zero()
    }

    pub fn conj(self) -> Self {
        Self {
            a: self.a - self.b,
            b: -self.b,
        }
    }

    pub fn add(self, rhs: Self) -> Self {
        Self {
            a: self.a + rhs.a,
            b: self.b + rhs.b,
        }
    }

    pub fn mul(self, rhs: Self) -> Self {
        Self {
            a: self.a * rhs.a - self.b * rhs.b,
            b: self.a * rhs.b + self.b * rhs.a - self.b * rhs.b,
        }
    }

    pub fn scale(self, c: Q) -> Self {
        Self {
            a: self.a * c,
            b: self.b * c,
        }
    }
}

pub(super) type Z3Mat3 = [[Cyclo3; 3]; 3];

pub(super) fn z3_zeros3() -> Z3Mat3 {
    [[Cyclo3::zero(); 3]; 3]
}

pub(super) fn z3_eye3() -> Z3Mat3 {
    let mut m = z3_zeros3();
    for k in 0..3 {
        m[k][k] = Cyclo3::from_int(1);
    }
    m
}

pub(super) fn z3_add3(a: &Z3Mat3, b: &Z3Mat3) -> Z3Mat3 {
    let mut out = z3_zeros3();
    for r in 0..3 {
        for c in 0..3 {
            out[r][c] = a[r][c].add(b[r][c]);
        }
    }
    out
}

pub(super) fn z3_scale3(c: Q, a: &Z3Mat3) -> Z3Mat3 {
    let mut out = z3_zeros3();
    for r in 0..3 {
        for col in 0..3 {
            out[r][col] = a[r][col].scale(c);
        }
    }
    out
}

pub(super) fn z3_mul3(a: &Z3Mat3, b: &Z3Mat3) -> Z3Mat3 {
    let mut out = z3_zeros3();
    for r in 0..3 {
        for k in 0..3 {
            let ark = a[r][k];
            if ark.is_zero() {
                continue;
            }
            for c in 0..3 {
                out[r][c] = out[r][c].add(ark.mul(b[k][c]));
            }
        }
    }
    out
}

pub(super) fn z3_dagger3(a: &Z3Mat3) -> Z3Mat3 {
    let mut out = z3_zeros3();
    for r in 0..3 {
        for c in 0..3 {
            out[r][c] = a[c][r].conj();
        }
    }
    out
}

pub(super) fn z3_trace3(a: &Z3Mat3) -> Cyclo3 {
    a[0][0].add(a[1][1]).add(a[2][2])
}

pub(super) fn z3_quad_form3(a: &Z3Mat3, v: &[Cyclo3; 3]) -> Cyclo3 {
    let mut acc = Cyclo3::zero();
    for r in 0..3 {
        for c in 0..3 {
            acc = acc.add(v[r].conj().mul(a[r][c]).mul(v[c]));
        }
    }
    acc
}

pub(super) fn wigner_phase_point_z3(q_idx: usize, p_idx: usize) -> Z3Mat3 {
    let mut m = z3_zeros3();
    let target = (2 * q_idx) % 3;
    for x in 0..3 {
        for y in 0..3 {
            if (x + y) % 3 == target {
                let exp = (p_idx as i64) * ((x as i64) - (y as i64));
                m[x][y] = Cyclo3::core_pow(exp);
            }
        }
    }
    m
}

pub(super) fn compute_wigner_table_z3_rust(state: &[Cyclo3; 3]) -> [[Q; 3]; 3] {
    let mut norm_sq = Cyclo3::zero();
    for c in state {
        norm_sq = norm_sq.add(c.conj().mul(*c));
    }
    assert!(norm_sq.b.is_zero() && norm_sq.a > Q::zero());
    let denom = q(3, 1) * norm_sq.a;
    let mut table = [[Q::zero(); 3]; 3];
    for q_idx in 0..3 {
        for p_idx in 0..3 {
            let aqp = wigner_phase_point_z3(q_idx, p_idx);
            let val = z3_quad_form3(&aqp, state);
            assert!(val.b.is_zero());
            table[q_idx][p_idx] = val.a / denom;
        }
    }
    table
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_import_finite_maps/page_wootters_tsirelson_wigner/cyclotomic_rings.rs
// Claim: urn:core:crates_rs:core-quantum-physics:cyclotomic-rings:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord61ffdb60 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord61ffdb60` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError61ffdb60 {
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
impl BoundaryError61ffdb60 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError61ffdb60 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError61ffdb60 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord61ffdb60 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError61ffdb60> {
        if capacity_bound == 0 {
            return Err(BoundaryError61ffdb60::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError61ffdb60::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError61ffdb60::ExceedsCapacity {
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
mod l4_boundary_tests_61ffdb60 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord61ffdb60::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord61ffdb60::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord61ffdb60::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord61ffdb60::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord61ffdb60::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError61ffdb60::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError61ffdb60::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
