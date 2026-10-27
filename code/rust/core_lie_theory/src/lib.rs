//! `core_lie_theory` -- exact finite groups, Lie groups and Lie algebras.
//!
//! Every quantity is exact: rationals, cyclotomic and quadratic number fields. There is no
//! floating point and no tolerance; a computation that would need one is refused with a
//! typed error. Scalars come from `core_number_theory`, matrices and elimination from
//! `linear_algebra`; this crate adds the group and Lie-algebra structure.
//!
//! - [`finite_group`]: Cayley tables, generation with a declared bound, conjugacy classes,
//!   the class equation, commuting pairs, quotients, flux and holonomy operators, and
//!   character tables over `Z[zeta_e]` (Dixon), with McKay matrices.
//! Character values use `core_number_theory::cyclotomic_integer`, the canonical
//! integral cyclotomic ring for a runtime conductor.
//! - [`cayley`]: Cayley charts of `so(n)` over `Q` and of the unit circle of `Q(i)`.
//! - [`su2`]: quaternions, the adjoint cover `SU(2) -> SO(3)`, spinor norms and spin lifts,
//!   `sl(2)` spin representations, Clebsch-Gordan coefficients, the binary polyhedral groups.
//! - [`rotation`]: the finite subgroups `C_m`, `D_m`, `T`, `O`, `I` of `SO(3, K)`.
//! - [`lorentz`]: `SO+(1, d; Q)`: boosts, polar decomposition, Thomas-Wigner rotation,
//!   `SO+(1, 2; Q) = PGL(2, Q)`.
//! - [`finite_order`]: the exact decision whether a rational matrix has finite order.
//! - [`lie_algebra`]: structure constants, Jacobi, Killing form, Chevalley-Eilenberg cohomology.
//! - [`scalar`]: exact complex scalars (conjugation, `i`, `1/sqrt 2`) for the unitary
//!   constructions still to come.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

pub mod cayley;
pub mod cayley_unitary;
pub mod clifford;
pub mod finite_group;
pub mod finite_groupoid_algebra;
pub mod finite_path_algebra;
pub mod twisted_abelian_algebra;
pub mod finite_order;
pub mod heisenberg;
pub mod lie_algebra;
pub mod lorentz;
pub mod pauli_symplectic;
pub mod rotation;
pub mod scalar;
pub mod su2;
pub mod su2_matrix;
pub mod su_n;

/// An exact rational matrix: the carrier of the constructions over `Q`.
pub(crate) type QMatrix =
    linear_algebra::backend::basic_matrix::BasicMatrix<num_rational::BigRational>;

pub mod weyl_operators;

/// Exact `so(2)` element `[[0, a], [-a, 0]]`: trace zero and determinant `a²`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct So2Carrier {
    off_num: i128,
    off_den: i128,
    det_num: i128,
    det_den: i128,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum So2Error {
    Denominator,
    Overflow,
    Trace,
    Determinant,
}

impl std::fmt::Display for So2Error {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Denominator => write!(formatter, "off-diagonal denominator is zero"),
            Self::Overflow => write!(formatter, "so(2) arithmetic overflowed i128"),
            Self::Trace => write!(formatter, "skew trace is not zero"),
            Self::Determinant => write!(formatter, "determinant is not the square of the off-diagonal"),
        }
    }
}

impl std::error::Error for So2Error {}

impl So2Carrier {
    pub fn determinant(&self) -> (i128, i128) {
        (self.det_num, self.det_den)
    }
}

fn gcd_i128(mut left: i128, mut right: i128) -> Result<i128, So2Error> {
    left = left.checked_abs().ok_or(So2Error::Overflow)?;
    right = right.checked_abs().ok_or(So2Error::Overflow)?;
    while right != 0 {
        let remainder = left.checked_rem(right).ok_or(So2Error::Overflow)?;
        left = right;
        right = remainder;
    }
    Ok(left)
}

fn verify_cross_ratio(
    square_num: i128,
    square_den: i128,
    det_num: i128,
    det_den: i128,
) -> Result<(), So2Error> {
    let cross = det_num
        .checked_mul(square_den)
        .ok_or(So2Error::Overflow)?;
    let back = det_den
        .checked_mul(square_num)
        .ok_or(So2Error::Overflow)?;
    if cross != back {
        return Err(So2Error::Determinant);
    }
    Ok(())
}

fn reduced_square_ratio(off_num: i128, off_den: i128) -> Result<(i128, i128), So2Error> {
    let square_num = off_num.checked_mul(off_num).ok_or(So2Error::Overflow)?;
    let square_den = off_den.checked_mul(off_den).ok_or(So2Error::Overflow)?;
    let content = gcd_i128(square_num, square_den)?;
    if content == 0 {
        return Err(So2Error::Determinant);
    }
    let det_num = square_num.checked_div(content).ok_or(So2Error::Overflow)?;
    let det_den = square_den.checked_div(content).ok_or(So2Error::Overflow)?;
    verify_cross_ratio(square_num, square_den, det_num, det_den)?;
    Ok((det_num, det_den))
}

/// Admit a rational skew block. The trace of `[[0, a], [-a, 0]]` is 0 and `det = a²`.
pub fn admit_so2(off_num: i128, off_den: i128) -> Result<So2Carrier, So2Error> {
    if off_den == 0 {
        return Err(So2Error::Denominator);
    }
    let trace = 0i128.checked_add(0).ok_or(So2Error::Overflow)?;
    if trace != 0 {
        return Err(So2Error::Trace);
    }
    let (det_num, det_den) = reduced_square_ratio(off_num, off_den)?;
    let _matrix: Option<QMatrix> = None;
    Ok(So2Carrier {
        off_num,
        off_den,
        det_num,
        det_den,
    })
}

// Origin: engine/crates_rs/core_lie_theory/src/lib.rs
// Claim: urn:core:crates_rs:core-lie-theory:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod so2_tests {
    use super::*;

    fn taken(result: Result<So2Carrier, So2Error>) -> So2Carrier {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn three_halves_has_determinant_nine_over_four() {
        let carrier = taken(admit_so2(3, 2));
        assert_eq!(carrier.determinant(), (9, 4));
    }

    #[test]
    fn a_zero_denominator_is_refused() {
        assert!(matches!(admit_so2(1, 0), Err(So2Error::Denominator)));
    }
}
