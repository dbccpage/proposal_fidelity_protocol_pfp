// AuthorityEffect: None.

//! Four sign-valued windows, joint assignments, pairwise boxes, and the finite CHSH bound.
//!
//! Windows `a_0, a_1` (first coordinate) and `b_0, b_1` (second) each read
//! `+1` or `-1`. A joint assignment fixes all four. A pairwise box declares,
//! for each window pair `(x, y)`, a nonnegative table `p(a, b | x, y)` summing
//! to one. Computed exactly:
//!
//! - the CHSH value `a_0 b_0 + a_0 b_1 + a_1 b_0 - a_1 b_1` of each of the 16
//!   joint assignments;
//! - the box of pairwise marginals of a joint table (nonnegative weights on
//!   the 16 assignments with positive total), and for any box the correlators
//!   `E(x, y) = sum_(a,b) a b p(a, b | x, y)` and
//!   `S = E(0,0) + E(0,1) + E(1,0) - E(1,1)`;
//! - no-signalling: the marginal of `a` in window `x` does not depend on `y`,
//!   and the marginal of `b` in window `y` does not depend on `x`;
//! - the joint assignments compatible with the support of all four tables;
//! - joint extension, decided by `declared_family_separability` against the 16
//!   marginal vectors of the joint assignments: either weights on the
//!   assignments that reproduce the box (a joint table), or a separating
//!   functional. The CHSH functional `phi = -S` with threshold `-2` is one
//!   declared witness;
//! - the box of a declared bipartite state and declared `+-1`-valued
//!   observables, `p(a, b | x, y) = Tr(rho (P_a^x (x) Q_b^y))`, where
//!   `P_(+-)^x = (I +- A_x) / 2` and `Q_(+-)^y = (I +- B_y) / 2`.
//!
//! The bound `|S| <= 2` concerns jointly tabled boxes only. No bound is derived
//! for boxes without a joint table; the Tsirelson value is not derived.
//! Refused: coordinate vectors of the wrong length, negative entries, contexts
//! that do not sum to one, joint tables with zero total, window indices other
//! than 0 and 1, observables that are not Hermitian involutions, and states
//! that are not Hermitian PSD of trace one.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_e81b223f<T> {
    fn checked_invariant_e81b223f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_e81b223f<T> for Option<T> {
    #[inline]
    fn checked_invariant_e81b223f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_e81b223f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_e81b223f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_hermitian::{self};
use num_traits::{One, Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

use core_finite_probability::joint_table::{JointTable, WeightTableError};
use core_solvers::solver_convex_finite_hull::{
    decide_membership, ConvexHullError, DeclaredFamily, MembershipCertificate, SeparatingWitness,
};

/// Number of coordinates of a pairwise box: four contexts, four outcomes each.
pub const BOX_COORDINATES: usize = 16;

const SIGNS: [i8; 2] = [1, -1];

/// Refusals for boxes, joint tables and state-derived correlations.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CorrelationError {
    #[error("{actual} entries given, expected {BOX_COORDINATES}")]
    Length { actual: usize },
    #[error("entry {index} is negative")]
    Negative { index: usize },
    #[error("entry {index} has a nonpositive rational denominator")]
    InvalidDenominator { index: usize },
    #[error("context ({x}, {y}) sums to {sum}, not one")]
    ContextNotNormalized { x: usize, y: usize, sum: Rational },
    #[error("the joint table has zero total")]
    ZeroTotal,
    #[error("({x}, {y}) is not a window pair")]
    WindowOutOfRange { x: usize, y: usize },
    #[error("observable {index} is not a nonempty square Hermitian matrix")]
    ObservableNotHermitian { index: usize },
    #[error("observable {index} does not square to the identity")]
    NotInvolution { index: usize },
    #[error("the state is not Hermitian PSD of trace one on the observables' carrier")]
    NotAState,
    #[error("table refusal: {0}")]
    Table(#[from] WeightTableError),
}

fn outcome_index(sign: i8) -> usize {
    usize::from(sign != 1)
}

fn coordinate(x: usize, y: usize, a: i8, b: i8) -> usize {
    4 * (2 * x + y) + 2 * outcome_index(a) + outcome_index(b)
}

fn check_window(x: usize, y: usize) -> Result<(), CorrelationError> {
    if x > 1 || y > 1 {
        return Err(CorrelationError::WindowOutOfRange { x, y });
    }
    Ok(())
}

/// Values of the four windows `a_0, a_1, b_0, b_1`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct JointAssignment {
    pub a: [i8; 2],
    pub b: [i8; 2],
}

impl JointAssignment {
    /// The 16 joint assignments; in assignment `s`, bit `i` set means `-1` for
    /// window `a_0, a_1, b_0, b_1` in that order.
    pub fn all() -> Vec<Self> {
        (0..16u8)
            .map(|s| {
                let sign = |bit: u8| if (s >> bit) & 1 == 0 { 1 } else { -1 };
                Self {
                    a: [sign(0), sign(1)],
                    b: [sign(2), sign(3)],
                }
            })
            .collect()
    }

    /// `a_0 b_0 + a_0 b_1 + a_1 b_0 - a_1 b_1`.
    pub fn chsh(&self) -> i64 {
        let [a0, a1] = self.a.map(i64::from);
        let [b0, b1] = self.b.map(i64::from);
        a0 * b0 + a0 * b1 + a1 * b0 - a1 * b1
    }

    fn marginal_coordinates(&self) -> Vec<Rational> {
        let mut v = vec![Rational::zero(); BOX_COORDINATES];
        for (x, &a) in self.a.iter().enumerate() {
            for (y, &b) in self.b.iter().enumerate() {
                v[coordinate(x, y, a, b)] = Rational::one();
            }
        }
        v
    }
}

/// The 16 marginal vectors of the joint assignments, as a declared family.
pub fn deterministic_family() -> DeclaredFamily {
    use core_finite_probability::local_deterministic::{binary_local_vertices, LocalVertexLimits};
    let contexts = vec![vec![2, 0], vec![3, 0], vec![2, 1], vec![3, 1]];
    let vertices = binary_local_vertices(
        4,
        &contexts,
        LocalVertexLimits {
            assignments: 16,
            coordinates: 16,
            entries: 256,
        },
    )
    .checked_invariant_e81b223f("fixed four-window local carrier");
    DeclaredFamily::new(vertices).checked_invariant_e81b223f("fixed local vertices share their coordinates")
}

/// `phi = -S` in box coordinates, with threshold `-2`.
pub fn chsh_witness() -> SeparatingWitness {
    let mut phi = vec![Rational::zero(); BOX_COORDINATES];
    for x in 0..2 {
        for y in 0..2 {
            let s: i64 = if (x, y) == (1, 1) { -1 } else { 1 };
            for a in SIGNS {
                for b in SIGNS {
                    phi[coordinate(x, y, a, b)] = ri(-s * i64::from(a) * i64::from(b));
                }
            }
        }
    }
    SeparatingWitness::new(phi, ri(-2))
}

/// Four declared outcome tables, one per window pair.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PairwiseBox {
    probabilities: Vec<Rational>,
}

impl PairwiseBox {
    /// Declare a box from its 16 coordinates. Context `(x, y)` occupies the
    /// four entries from `4 (2x + y)`, with outcomes `(+,+), (+,-), (-,+), (-,-)`.
    pub fn new(probabilities: Vec<Rational>) -> Result<Self, CorrelationError> {
        if probabilities.len() != BOX_COORDINATES {
            return Err(CorrelationError::Length {
                actual: probabilities.len(),
            });
        }
        if let Some(index) = probabilities.iter().position(|p| !p.denom().is_positive()) {
            return Err(CorrelationError::InvalidDenominator { index });
        }
        if let Some(index) = probabilities.iter().position(Signed::is_negative) {
            return Err(CorrelationError::Negative { index });
        }
        for x in 0..2 {
            for y in 0..2 {
                let start = 4 * (2 * x + y);
                let sum: Rational = probabilities[start..start + 4].iter().sum();
                if !sum.is_one() {
                    return Err(CorrelationError::ContextNotNormalized { x, y, sum });
                }
            }
        }
        Ok(Self { probabilities })
    }

    /// The box of pairwise marginals of a joint table on the 16 assignments.
    pub fn from_joint_table(weights: &[Rational]) -> Result<Self, CorrelationError> {
        if weights.len() != BOX_COORDINATES {
            return Err(CorrelationError::Length {
                actual: weights.len(),
            });
        }
        if let Some(index) = weights.iter().position(|w| !w.denom().is_positive()) {
            return Err(CorrelationError::InvalidDenominator { index });
        }
        if let Some(index) = weights.iter().position(Signed::is_negative) {
            return Err(CorrelationError::Negative { index });
        }
        let total: Rational = weights.iter().sum();
        if total.is_zero() {
            return Err(CorrelationError::ZeroTotal);
        }
        let mut probabilities = vec![Rational::zero(); BOX_COORDINATES];
        for (w, s) in weights.iter().zip(JointAssignment::all()) {
            for (acc, m) in probabilities.iter_mut().zip(s.marginal_coordinates()) {
                *acc += w * m / &total;
            }
        }
        Self::new(probabilities)
    }

    /// `p(a, b | x, y) = Tr(rho (P_a^x (x) Q_b^y))` for declared observables and state.
    pub fn from_state(
        rho: &BasicMatrix<GaussianRat>,
        alice: [&BasicMatrix<GaussianRat>; 2],
        bob: [&BasicMatrix<GaussianRat>; 2],
    ) -> Result<Self, CorrelationError> {
        let (d_a, d_b) = (alice[0].rows(), bob[0].rows());
        for (index, observable) in alice.iter().chain(bob.iter()).enumerate() {
            check_observable(observable, if index < 2 { d_a } else { d_b }, index)?;
        }
        let a = [alice[0].clone(), alice[1].clone()];
        let b = [bob[0].clone(), bob[1].clone()];
        let field_values =
            algebraic_box_from_state(rho, &a, &b).map_err(|_| CorrelationError::NotAState)?;
        let probabilities = field_values.into_iter().map(|p| p.re).collect();
        Self::new(probabilities)
    }

    pub fn coordinates(&self) -> &[Rational] {
        &self.probabilities
    }

    fn p(&self, x: usize, y: usize, a: i8, b: i8) -> &Rational {
        &self.probabilities[coordinate(x, y, a, b)]
    }

    /// `E(x, y) = sum_(a,b) a b p(a, b | x, y)`.
    pub fn correlator(&self, x: usize, y: usize) -> Result<Rational, CorrelationError> {
        check_window(x, y)?;
        Ok(self.p(x, y, 1, 1) - self.p(x, y, 1, -1) - self.p(x, y, -1, 1) + self.p(x, y, -1, -1))
    }

    /// `S = E(0,0) + E(0,1) + E(1,0) - E(1,1)`.
    pub fn chsh(&self) -> Rational {
        let e = |x, y| self.correlator(x, y).checked_invariant_e81b223f("windows are 0 and 1");
        e(0, 0) + e(0, 1) + e(1, 0) - e(1, 1)
    }

    /// Each window's outcome marginal is independent of the other side's window.
    pub fn is_no_signalling(&self) -> bool {
        let alice = |x: usize, y: usize, a: i8| self.p(x, y, a, 1) + self.p(x, y, a, -1);
        let bob = |x: usize, y: usize, b: i8| self.p(x, y, 1, b) + self.p(x, y, -1, b);
        (0..2).all(|w| {
            SIGNS
                .iter()
                .all(|&s| alice(w, 0, s) == alice(w, 1, s) && bob(0, w, s) == bob(1, w, s))
        })
    }

    /// The outcome table of window pair `(x, y)`, rows `a = +1, -1`, columns `b = +1, -1`.
    pub fn context_table(&self, x: usize, y: usize) -> Result<JointTable, CorrelationError> {
        check_window(x, y)?;
        let rows = SIGNS
            .iter()
            .map(|&a| SIGNS.iter().map(|&b| self.p(x, y, a, b).clone()).collect())
            .collect();
        Ok(JointTable::new(rows)?)
    }

    /// Joint assignments whose four restrictions all have positive probability.
    ///
    /// A joint table reproducing the box can only weight these assignments, so
    /// an empty list excludes every joint table.
    pub fn support_compatible_assignments(&self) -> Vec<JointAssignment> {
        JointAssignment::all()
            .into_iter()
            .filter(|s| (0..2).all(|x| (0..2).all(|y| self.p(x, y, s.a[x], s.b[y]).is_positive())))
            .collect()
    }

    /// Decide whether some joint table on the 16 assignments reproduces the box.
    pub fn joint_extension(&self) -> Result<MembershipCertificate, ConvexHullError> {
        decide_membership(&deterministic_family(), &self.probabilities)
    }
}

fn check_observable(
    observable: &BasicMatrix<GaussianRat>,
    dimension: usize,
    index: usize,
) -> Result<(), CorrelationError> {
    if observable.rows() == 0
        || observable.rows() != dimension
        || observable.cols() != dimension
        || !exact_hermitian::is_hermitian(observable)
    {
        return Err(CorrelationError::ObservableNotHermitian { index });
    }
    if field_matrix::multiply(observable, observable)
        .and_then(|m| field_matrix::is_identity_matrix(&m))
        != Ok(true)
    {
        return Err(CorrelationError::NotInvolution { index });
    }
    Ok(())
}

/// Typed refusals of the algebraic CHSH operator and state certificates.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AlgebraicCorrelationError {
    #[error(transparent)]
    Matrix(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error("nonzero local dimensions up to 16 and joint dimension up to 64 are supported")]
    Carrier,
    #[error("every declared observable must be a Hermitian involution on its local factor")]
    Observable,
    #[error("the declared scalar is not the positive square root of two")]
    SquareRoot,
    #[error("the declared density is not a positive Hermitian trace-one state")]
    State,
    #[error("the independently replayed operator certificate failed")]
    Certificate,
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::adjoint,
    matrix as field_matrix,
    ordered::{hermitian_inertia, HermitianOrdered},
};

fn check_single_party_observables<F: HermitianOrdered>(
    family: &[BasicMatrix<F>; 2],
    d: usize,
) -> Result<(), AlgebraicCorrelationError> {
    let id = field_matrix::identity(d)?;
    for o in family {
        if o.shape() != (d, d) || adjoint(o)? != *o || field_matrix::multiply(o, o)? != id {
            return Err(AlgebraicCorrelationError::Observable);
        }
    }
    Ok(())
}

fn check_algebraic_observables<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
) -> Result<(usize, usize), AlgebraicCorrelationError> {
    let da = a[0].rows();
    let db = b[0].rows();
    let bad_dim = da == 0 || db == 0 || da > 16 || db > 16;
    if bad_dim || da.checked_mul(db).is_none_or(|d| d > 64) {
        return Err(AlgebraicCorrelationError::Carrier);
    }
    check_single_party_observables(a, da)?;
    check_single_party_observables(b, db)?;
    Ok((da, db))
}

/// A0 tensor (B0+B1) + A1 tensor (B0-B1), on the checked tensor carrier.
pub fn chsh_operator<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
) -> Result<BasicMatrix<F>, AlgebraicCorrelationError> {
    check_algebraic_observables(a, b)?;
    Ok(field_matrix::add(
        &field_matrix::kronecker(&a[0], &field_matrix::add(&b[0], &b[1])?)?,
        &field_matrix::kronecker(&a[1], &field_matrix::sub(&b[0], &b[1])?)?,
    )?)
}

/// Replay B_CHSH^2 = 4 I - [A0,A1] tensor [B0,B1]. No extremal value is declared.
pub fn verify_chsh_square_identity<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
) -> Result<bool, AlgebraicCorrelationError> {
    let bell = chsh_operator(a, b)?;
    let four = F::one().add(&F::one()).add(&F::one()).add(&F::one());
    let rhs = field_matrix::sub(
        &field_matrix::scale(&field_matrix::identity(bell.rows())?, &four)?,
        &field_matrix::kronecker(
            &field_matrix::commutator(&a[0], &a[1])?,
            &field_matrix::commutator(&b[0], &b[1])?,
        )?,
    )?;
    Ok(field_matrix::multiply(&bell, &bell)? == rhs)
}

/// Sum-of-squares proof of both operator inequalities -2 sqrt(2) I <= B <= 2 sqrt(2) I.
/// The factors are Hermitian and their squares have nonnegative quadratic forms.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TsirelsonCertificate<F> {
    pub bell_operator: BasicMatrix<F>,
    pub bound: F,
    pub upper_factors: [BasicMatrix<F>; 2],
    pub lower_factors: [BasicMatrix<F>; 2],
}

fn build_scaled_kronecker<F: HermitianOrdered>(
    left: &BasicMatrix<F>,
    right: &BasicMatrix<F>,
    scale: &F,
) -> Result<BasicMatrix<F>, AlgebraicCorrelationError> {
    let k = field_matrix::kronecker(left, right)?;
    Ok(field_matrix::scale(&k, scale)?)
}

fn build_tsirelson_local_operators<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
    da: usize,
    db: usize,
    inv: &F,
) -> Result<([BasicMatrix<F>; 2], [BasicMatrix<F>; 2]), AlgebraicCorrelationError> {
    let ia = field_matrix::identity(da)?;
    let ib = field_matrix::identity(db)?;
    let local_a = [
        field_matrix::kronecker(&a[0], &ib)?,
        field_matrix::kronecker(&a[1], &ib)?,
    ];
    let b_plus = field_matrix::add(&b[0], &b[1])?;
    let b_minus = field_matrix::sub(&b[0], &b[1])?;
    let local_b = [
        build_scaled_kronecker(&ia, &b_plus, inv)?,
        build_scaled_kronecker(&ia, &b_minus, inv)?,
    ];
    Ok((local_a, local_b))
}

fn validate_positive_sqrt_two<F: HermitianOrdered>(
    sqrt_two: &F,
) -> Result<(F, F), AlgebraicCorrelationError> {
    let two = F::one().add(&F::one());
    if sqrt_two.mul(sqrt_two) != two || sqrt_two.fixed_field_sign() != Some(1) {
        return Err(AlgebraicCorrelationError::SquareRoot);
    }
    let inv = sqrt_two
        .try_inv()
        .ok_or(AlgebraicCorrelationError::SquareRoot)?;
    Ok((two, inv))
}

pub fn tsirelson_certificate<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
    sqrt_two: &F,
) -> Result<TsirelsonCertificate<F>, AlgebraicCorrelationError> {
    let (da, db) = check_algebraic_observables(a, b)?;
    let (two, inv) = validate_positive_sqrt_two(sqrt_two)?;
    let (local_a, local_b) = build_tsirelson_local_operators(a, b, da, db, &inv)?;
    let cert = build_tsirelson_cert_struct(a, b, &two.mul(sqrt_two), &local_a, &local_b)?;
    if !verify_tsirelson_certificate(a, b, sqrt_two, &cert)? {
        return Err(AlgebraicCorrelationError::Certificate);
    }
    Ok(cert)
}

fn build_tsirelson_cert_struct<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
    bound: &F,
    local_a: &[BasicMatrix<F>; 2],
    local_b: &[BasicMatrix<F>; 2],
) -> Result<TsirelsonCertificate<F>, AlgebraicCorrelationError> {
    Ok(TsirelsonCertificate {
        bell_operator: chsh_operator(a, b)?,
        bound: bound.clone(),
        upper_factors: [
            field_matrix::sub(&local_a[0], &local_b[0])?,
            field_matrix::sub(&local_a[1], &local_b[1])?,
        ],
        lower_factors: [
            field_matrix::add(&local_a[0], &local_b[0])?,
            field_matrix::add(&local_a[1], &local_b[1])?,
        ],
    })
}

fn verify_sos_factor_pair<F: HermitianOrdered>(
    factors: &[BasicMatrix<F>; 2],
    gap: &BasicMatrix<F>,
    shape: (usize, usize),
    inv: &F,
) -> Result<bool, AlgebraicCorrelationError> {
    if factors.iter().any(|x| x.shape() != shape) {
        return Ok(false);
    }
    let mut sum = field_matrix::zeros(shape.0, shape.1)?;
    for x in factors {
        if adjoint(x)? != *x {
            return Ok(false);
        }
        sum = field_matrix::add(&sum, &field_matrix::multiply(&adjoint(x)?, x)?)?;
    }
    Ok(field_matrix::scale(&sum, inv)? == *gap)
}

pub fn verify_tsirelson_certificate<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
    sqrt_two: &F,
    cert: &TsirelsonCertificate<F>,
) -> Result<bool, AlgebraicCorrelationError> {
    let bell = chsh_operator(a, b)?;
    let two = F::one().add(&F::one());
    let valid_sqrt = sqrt_two.mul(sqrt_two) == two && sqrt_two.fixed_field_sign() == Some(1);
    if !valid_sqrt || cert.bell_operator != bell || cert.bound != two.mul(sqrt_two) {
        return Ok(false);
    }
    let inv = sqrt_two
        .try_inv()
        .ok_or(AlgebraicCorrelationError::SquareRoot)?;
    verify_tsirelson_sos_bounds(&bell, cert, &inv)
}

fn verify_tsirelson_sos_bounds<F: HermitianOrdered>(
    bell: &BasicMatrix<F>,
    cert: &TsirelsonCertificate<F>,
    inv: &F,
) -> Result<bool, AlgebraicCorrelationError> {
    let bound_identity = field_matrix::scale(&field_matrix::identity(bell.rows())?, &cert.bound)?;
    let upper_gap = field_matrix::sub(&bound_identity, bell)?;
    let lower_gap = field_matrix::add(&bound_identity, bell)?;
    if !verify_sos_factor_pair(&cert.upper_factors, &upper_gap, bell.shape(), inv)? {
        return Ok(false);
    }
    verify_sos_factor_pair(&cert.lower_factors, &lower_gap, bell.shape(), inv)
}

fn check_algebraic_state<F: HermitianOrdered>(
    rho: &BasicMatrix<F>,
    dimension: usize,
) -> Result<(), AlgebraicCorrelationError> {
    if rho.shape() != (dimension, dimension)
        || field_matrix::trace(rho)? != F::one()
        || !hermitian_inertia(rho)?.is_positive_semidefinite()
    {
        return Err(AlgebraicCorrelationError::State);
    }
    Ok(())
}

fn local_projector<F: HermitianOrdered>(
    id: &BasicMatrix<F>,
    op: &BasicMatrix<F>,
    half: &F,
    sign: i8,
) -> Result<BasicMatrix<F>, AlgebraicCorrelationError> {
    let factor = if sign == 1 { F::one() } else { F::one().neg() };
    let shifted = field_matrix::add(id, &field_matrix::scale(op, &factor)?)?;
    Ok(field_matrix::scale(&shifted, half)?)
}

fn compute_window_probability<F: HermitianOrdered>(
    rho: &BasicMatrix<F>,
    ax: &BasicMatrix<F>,
    by: &BasicMatrix<F>,
    ia: &BasicMatrix<F>,
    ib: &BasicMatrix<F>,
    half: &F,
    sa: i8,
    sb: i8,
) -> Result<F, AlgebraicCorrelationError> {
    let pa = local_projector(ia, ax, half, sa)?;
    let pb = local_projector(ib, by, half, sb)?;
    let prod = field_matrix::multiply(rho, &field_matrix::kronecker(&pa, &pb)?)?;
    let p = field_matrix::trace(&prod)?;
    if !matches!(p.fixed_field_sign(), Some(0 | 1)) {
        return Err(AlgebraicCorrelationError::Certificate);
    }
    Ok(p)
}

fn verify_window_normalizations<F: HermitianOrdered>(
    probabilities: &[F],
) -> Result<(), AlgebraicCorrelationError> {
    for x in 0..2 {
        for y in 0..2 {
            let sum = probabilities[4 * (2 * x + y)..4 * (2 * x + y) + 4]
                .iter()
                .fold(F::zero(), |s, p| s.add(p));
            if sum != F::one() {
                return Err(AlgebraicCorrelationError::Certificate);
            }
        }
    }
    Ok(())
}

/// The 16 probabilities of the four binary windows, measured in any exact ordered
/// number field. Admission checks the state and local Hermitian involutions.
pub fn algebraic_box_from_state<F: HermitianOrdered>(
    rho: &BasicMatrix<F>,
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
) -> Result<Vec<F>, AlgebraicCorrelationError> {
    let (da, db) = check_algebraic_observables(a, b)?;
    check_algebraic_state(rho, da * db)?;
    let half = F::one()
        .add(&F::one())
        .try_inv()
        .ok_or(AlgebraicCorrelationError::Certificate)?;
    let probabilities = evaluate_all_window_probabilities(rho, a, b, da, db, &half)?;
    verify_window_normalizations(&probabilities)?;
    Ok(probabilities)
}

fn evaluate_all_window_probabilities<F: HermitianOrdered>(
    rho: &BasicMatrix<F>,
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
    da: usize,
    db: usize,
    half: &F,
) -> Result<Vec<F>, AlgebraicCorrelationError> {
    let ia = field_matrix::identity(da)?;
    let ib = field_matrix::identity(db)?;
    let mut probabilities = vec![F::zero(); 16];
    for x in 0..2 {
        for y in 0..2 {
            for (sa, sb) in [(1i8, 1i8), (1, -1), (-1, 1), (-1, -1)] {
                probabilities[coordinate(x, y, sa, sb)] =
                    compute_window_probability(rho, &a[x], &b[y], &ia, &ib, half, sa, sb)?;
            }
        }
    }
    Ok(probabilities)
}

fn build_npa_words<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
    da: usize,
    db: usize,
) -> Result<Vec<BasicMatrix<F>>, AlgebraicCorrelationError> {
    let (aa, bb) = build_lifted_alice_bob_operators(a, b, da, db)?;
    let mut words = vec![
        field_matrix::identity(da * db)?,
        aa[0].clone(),
        aa[1].clone(),
        bb[0].clone(),
        bb[1].clone(),
    ];
    for x in &aa {
        for y in &bb {
            words.push(field_matrix::multiply(x, y)?);
        }
    }
    Ok(words)
}

fn build_lifted_alice_bob_operators<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
    da: usize,
    db: usize,
) -> Result<([BasicMatrix<F>; 2], [BasicMatrix<F>; 2]), AlgebraicCorrelationError> {
    let ia = field_matrix::identity(da)?;
    let ib = field_matrix::identity(db)?;
    let aa = [
        field_matrix::kronecker(&a[0], &ib)?,
        field_matrix::kronecker(&a[1], &ib)?,
    ];
    let bb = [
        field_matrix::kronecker(&ia, &b[0])?,
        field_matrix::kronecker(&ia, &b[1])?,
    ];
    Ok((aa, bb))
}

fn compute_npa_gram_entries<F: HermitianOrdered>(
    rho: &BasicMatrix<F>,
    words: &[BasicMatrix<F>],
) -> Result<Vec<F>, AlgebraicCorrelationError> {
    let mut data = Vec::with_capacity(81);
    for x in words {
        for y in words {
            data.push(field_matrix::trace(&field_matrix::multiply(
                rho,
                &field_matrix::multiply(&adjoint(x)?, y)?,
            )?)?);
        }
    }
    Ok(data)
}

/// A state-derived NPA 1+AB moment matrix. PSD is checked exactly and the matrix
/// is the Gram form Tr(rho W_i^* W_j), W=(1,A0,A1,B0,B1,A0B0,A0B1,A1B0,A1B1).
/// The reverse inference from a finite PSD relaxation to a quantum model is absent.
pub fn npa_level_one_ab_moment<F: HermitianOrdered>(
    rho: &BasicMatrix<F>,
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
) -> Result<BasicMatrix<F>, AlgebraicCorrelationError> {
    let (da, db) = check_algebraic_observables(a, b)?;
    let d = da * db;
    check_algebraic_state(rho, d)?;
    let words = build_npa_words(a, b, da, db)?;
    let data = compute_npa_gram_entries(rho, &words)?;
    let gram =
        BasicMatrix::from_row_major(9, 9, data).map_err(|_| AlgebraicCorrelationError::Carrier)?;
    if !hermitian_inertia(&gram)?.is_positive_semidefinite()
        || (0..9).any(|i| gram.as_slice()[9 * i + i] != F::one())
    {
        return Err(AlgebraicCorrelationError::Certificate);
    }
    Ok(gram)
}

/// Typed refusals of the single-carrier commuting-operator Bell admission.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CommutingBellError {
    #[error(transparent)]
    Matrix(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error("the carrier is empty or larger than 64")]
    EmptyCarrier,
    #[error("observable {party}{index} is not a square operator on the declared carrier")]
    ShapeMismatch { party: char, index: usize },
    #[error("observable {party}{index} is not Hermitian")]
    ObservableNotHermitian { party: char, index: usize },
    #[error("observable {party}{index} does not square to the identity")]
    ObservableNotInvolution { party: char, index: usize },
    #[error("A{x} and B{y} do not commute")]
    CrossPartyNotCommuting { x: usize, y: usize },
    #[error("the state is not a positive Hermitian trace-one operator on the carrier")]
    InvalidState,
    #[error("the Bell value is not fixed by the involution, so it has no order sign")]
    UnsupportedAlgebraicField,
}

/// The CHSH value of a commuting-operator strategy on one carrier, with its order sign.
/// `square == value * value`; the sign is read from the ordered fixed field, never from
/// the square.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChshValueCertificate<F> {
    pub bell_operator: BasicMatrix<F>,
    pub value: F,
    pub square: F,
    pub sign: i8,
}

/// Which extreme `S^2 = 8` is attained, once the order sign is read.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ChshExtreme {
    PositiveTsirelson,
    NegativeTsirelson,
}

impl<F: HermitianOrdered> ChshValueCertificate<F> {
    /// `Some` exactly when `S^2 = 8`; the sign then separates `2 sqrt 2` from `-2 sqrt 2`.
    pub fn extreme(&self) -> Option<ChshExtreme> {
        let eight = (0..8).fold(F::zero(), |s, _| s.add(&F::one()));
        if self.square != eight {
            return None;
        }
        match self.sign {
            1 => Some(ChshExtreme::PositiveTsirelson),
            -1 => Some(ChshExtreme::NegativeTsirelson),
            _ => None,
        }
    }
}

/// Lifts a tensor-carrier strategy to one carrier: `A_x (x) I` and `I (x) B_y`.
pub fn tensor_embedding<F: HermitianOrdered>(
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
) -> Result<([BasicMatrix<F>; 2], [BasicMatrix<F>; 2]), CommutingBellError> {
    let (da, db) = (a[0].rows(), b[0].rows());
    if da == 0 || db == 0 {
        return Err(CommutingBellError::EmptyCarrier);
    }
    let ia = field_matrix::identity(da)?;
    let ib = field_matrix::identity(db)?;
    Ok((
        [field_matrix::kronecker(&a[0], &ib)?, field_matrix::kronecker(&a[1], &ib)?],
        [field_matrix::kronecker(&ia, &b[0])?, field_matrix::kronecker(&ia, &b[1])?],
    ))
}

/// Admits a commuting-operator CHSH strategy on a single carrier and returns its value.
///
/// Checked: every observable is a Hermitian involution of the carrier, every `A_x`
/// commutes with every `B_y`, and the state is Hermitian PSD of trace one. Same-party
/// observables are not required to commute (`A_0 = Z`, `A_1 = X` is admitted). The value
/// `S = Tr(rho (A0 B0 + A0 B1 + A1 B0 - A1 B1))` must lie in the ordered fixed field.
pub fn commuting_chsh_value<F: HermitianOrdered>(
    rho: &BasicMatrix<F>,
    a: &[BasicMatrix<F>; 2],
    b: &[BasicMatrix<F>; 2],
) -> Result<ChshValueCertificate<F>, CommutingBellError> {
    let d = rho.rows();
    if d == 0 || d > 64 {
        return Err(CommutingBellError::EmptyCarrier);
    }
    let id = field_matrix::identity(d)?;
    for (party, family) in [('A', a), ('B', b)] {
        for (index, o) in family.iter().enumerate() {
            if o.shape() != (d, d) {
                return Err(CommutingBellError::ShapeMismatch { party, index });
            }
            if adjoint(o)? != *o {
                return Err(CommutingBellError::ObservableNotHermitian { party, index });
            }
            if field_matrix::multiply(o, o)? != id {
                return Err(CommutingBellError::ObservableNotInvolution { party, index });
            }
        }
    }
    for (x, ax) in a.iter().enumerate() {
        for (y, by) in b.iter().enumerate() {
            if field_matrix::multiply(ax, by)? != field_matrix::multiply(by, ax)? {
                return Err(CommutingBellError::CrossPartyNotCommuting { x, y });
            }
        }
    }
    if rho.shape() != (d, d)
        || adjoint(rho)? != *rho
        || field_matrix::trace(rho)? != F::one()
        || !hermitian_inertia(rho)?.is_positive_semidefinite()
    {
        return Err(CommutingBellError::InvalidState);
    }
    let bell = field_matrix::sub(
        &field_matrix::add(
            &field_matrix::add(
                &field_matrix::multiply(&a[0], &b[0])?,
                &field_matrix::multiply(&a[0], &b[1])?,
            )?,
            &field_matrix::multiply(&a[1], &b[0])?,
        )?,
        &field_matrix::multiply(&a[1], &b[1])?,
    )?;
    let value = field_matrix::trace(&field_matrix::multiply(rho, &bell)?)?;
    let sign = value
        .fixed_field_sign()
        .ok_or(CommutingBellError::UnsupportedAlgebraicField)?;
    let square = value.mul(&value);
    Ok(ChshValueCertificate {
        bell_operator: bell,
        value,
        square,
        sign,
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/finite_chsh_correlations.rs
// Claim: urn:core:crates_rs:core-quantum-physics:finite-chsh-correlations:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod commuting_bell_tests {
    use super::*;
    use crate::tensor_commuting_correlation_frontier::chsh_game_certificate;
    use core_number_theory::cyclotomic_field::{sqrt_of_integer, Cyclotomic};

    fn g(rows: usize, entries: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
        BasicMatrix::from_row_major(
            rows,
            entries.len() / rows,
            entries.iter().map(|&(r, i)| GaussianRat::from_ints(r, i)).collect(),
        )
        .expect("literal matrix")
    }
    fn z() -> BasicMatrix<GaussianRat> {
        g(2, &[(1, 0), (0, 0), (0, 0), (-1, 0)])
    }
    fn x() -> BasicMatrix<GaussianRat> {
        g(2, &[(0, 0), (1, 0), (1, 0), (0, 0)])
    }

    #[test]
    fn raw_nonpositive_denominators_are_refused_before_box_arithmetic() {
        for (numerator, denominator) in [(0, 0), (1, 0), (-1, 0), (0, -1), (-1, -4)] {
            let raw = Rational::new_raw(numerator.into(), denominator.into());
            let mut probabilities = vec![Rational::new(1.into(), 4.into()); BOX_COORDINATES];
            probabilities[7] = raw;
            assert_eq!(
                PairwiseBox::new(probabilities.clone()),
                Err(CorrelationError::InvalidDenominator { index: 7 })
            );
            assert_eq!(
                PairwiseBox::from_joint_table(&probabilities),
                Err(CorrelationError::InvalidDenominator { index: 7 })
            );
        }
        let canonical = Rational::new((-1).into(), (-4).into());
        assert!(PairwiseBox::new(vec![canonical; BOX_COORDINATES]).is_ok());
    }

    #[test]
    fn embedded_optimal_strategy_has_positive_sign_and_negated_bob_has_negative_sign() {
        let game = chsh_game_certificate().expect("fixed strategy");
        let (a, b) = tensor_embedding(&game.alice, &game.bob).unwrap();
        // Same-party observables Z (x) I and X (x) I anticommute and are admitted.
        assert_ne!(
            field_matrix::multiply(&a[0], &a[1]).unwrap(),
            field_matrix::multiply(&a[1], &a[0]).unwrap()
        );
        let plus = commuting_chsh_value(&game.state, &a, &b).unwrap();
        assert_eq!(plus.sign, 1);
        assert_eq!(plus.extreme(), Some(ChshExtreme::PositiveTsirelson));
        let tau = Cyclotomic::<8>::try_from(sqrt_of_integer(8, &2.into()).unwrap()).unwrap();
        assert_eq!(plus.value, tau.add(&tau));
        let neg_b = [field_matrix::neg(&b[0]).unwrap(), field_matrix::neg(&b[1]).unwrap()];
        let minus = commuting_chsh_value(&game.state, &a, &neg_b).unwrap();
        // The square cannot tell the two strategies apart; the ordered sign does.
        assert_eq!(minus.square, plus.square);
        assert_eq!(minus.sign, -1);
        assert_eq!(minus.extreme(), Some(ChshExtreme::NegativeTsirelson));
    }

    #[test]
    fn gaussian_rationals_carry_no_square_root_of_two() {
        assert!(sqrt_of_integer(4, &2.into()).is_err());
        assert!(sqrt_of_integer(8, &2.into()).is_ok());
    }

    #[test]
    fn rational_product_strategy_is_admitted_and_not_extreme() {
        let i2 = field_matrix::identity::<GaussianRat>(2).unwrap();
        let (a, b) = tensor_embedding(&[z(), x()], &[z(), x()]).unwrap();
        let rho = field_matrix::kronecker(&g(2, &[(1, 0), (0, 0), (0, 0), (0, 0)]), &g(2, &[(1, 0), (0, 0), (0, 0), (0, 0)])).unwrap();
        let cert = commuting_chsh_value(&rho, &a, &b).unwrap();
        // <ZZ> + <ZX> + <XZ> - <XX> on |00> is 1 + 0 + 0 - 0.
        assert_eq!(cert.value, GaussianRat::from_ints(1, 0));
        assert_eq!(cert.extreme(), None);
        // Mutation: trace two is refused.
        let doubled = field_matrix::scale(&rho, &GaussianRat::from_ints(2, 0)).unwrap();
        assert_eq!(commuting_chsh_value(&doubled, &a, &b), Err(CommutingBellError::InvalidState));
        // Mutations of the observables.
        let not_hermitian = field_matrix::kronecker(&g(2, &[(1, 0), (1, 0), (0, 0), (-1, 0)]), &i2).unwrap();
        assert_eq!(
            commuting_chsh_value(&rho, &[not_hermitian, a[1].clone()], &b),
            Err(CommutingBellError::ObservableNotHermitian { party: 'A', index: 0 })
        );
        let doubled_z = field_matrix::scale(&b[0], &GaussianRat::from_ints(2, 0)).unwrap();
        assert_eq!(
            commuting_chsh_value(&rho, &a, &[doubled_z, b[1].clone()]),
            Err(CommutingBellError::ObservableNotInvolution { party: 'B', index: 0 })
        );
        assert_eq!(
            commuting_chsh_value(&rho, &[z(), a[1].clone()], &b),
            Err(CommutingBellError::ShapeMismatch { party: 'A', index: 0 })
        );
    }

    #[test]
    fn original_single_carrier_control_vanishes_and_corrected_one_is_refused() {
        // c1 control on one qubit: A0 = Z, A1 = X, B0 = Z, B1 = X.
        let bell = |a1: &BasicMatrix<GaussianRat>| {
            let a0b = field_matrix::multiply(&z(), &field_matrix::add(&z(), &x()).unwrap()).unwrap();
            let a1b = field_matrix::multiply(a1, &field_matrix::sub(&z(), &x()).unwrap()).unwrap();
            field_matrix::add(&a0b, &a1b).unwrap()
        };
        // A1 = X: Z(Z + X) + X(Z - X) = ZX + XZ = 0 since Z and X anticommute.
        let zero = field_matrix::zeros::<GaussianRat>(2, 2).unwrap();
        assert_eq!(bell(&x()), zero);
        // A1 = -X: 2I + ZX - XZ = 2I + 2ZX, which is not Hermitian.
        let corrected = bell(&field_matrix::neg(&x()).unwrap());
        assert_eq!(corrected, g(2, &[(2, 0), (2, 0), (-2, 0), (2, 0)]));
        assert_ne!(adjoint(&corrected).unwrap(), corrected);
        // On rho = (I + Y)/2 its trace is 2 + 2i: not a real expectation.
        let rho = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                GaussianRat { re: Rational::new(1.into(), 2.into()), im: Rational::zero() },
                GaussianRat { re: Rational::zero(), im: Rational::new((-1).into(), 2.into()) },
                GaussianRat { re: Rational::zero(), im: Rational::new(1.into(), 2.into()) },
                GaussianRat { re: Rational::new(1.into(), 2.into()), im: Rational::zero() },
            ],
        )
        .unwrap();
        assert_eq!(
            field_matrix::trace(&field_matrix::multiply(&rho, &corrected).unwrap()).unwrap(),
            GaussianRat::from_ints(2, 2)
        );
        // The admission refuses both controls before any value is formed: A0 = Z and B1 = X
        // do not commute on one carrier.
        let minus_x = field_matrix::neg(&x()).unwrap();
        for a1 in [x(), minus_x] {
            assert_eq!(
                commuting_chsh_value(&rho, &[z(), a1], &[z(), x()]),
                Err(CommutingBellError::CrossPartyNotCommuting { x: 0, y: 1 })
            );
        }
    }
}
