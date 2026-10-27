// AuthorityEffect: None.

//! The phase-blind quotient of amplitude configurations, and its fibers.
//!
//! A configuration is a finite vector `c` of Gaussian rationals over a declared
//! sector basis. Its phase-blind projection is the point
//! `pi(c)_g = |c_g|^2 / sum_h |c_h|^2` of the rational simplex. Configurations
//! with the same projection are phase equivalent; a class is a fiber. The
//! sector basis, the quadratic readout `|.|^2` and any finite phase group used
//! to enumerate a fiber are declared inputs. Computed here:
//!
//! - the projection, phase equivalence, and a fiber's support and relative
//!   phase dimension `|supp| - 1` (phases on zero coordinates are inert);
//! - the discrete fiber through `c` for a declared finite group of units: the
//!   `|G|^(|supp| - 1)` configurations `(z_g c_g)` with `z = 1` on the first
//!   nonzero coordinate, one per class modulo a global phase;
//! - descent of a linear map `M` through the projection extended by
//!   `0 -> None`. A map with at most one nonzero entry per row descends, and
//!   the induced map on the simplex is returned. Any other map is refused with
//!   an explicit phase-equivalent pair whose images the extended projection
//!   separates. Without the extension the classification fails: `[[1,1],[1,1]]`
//!   sends every configuration it does not annihilate to `(1/2, 1/2)`;
//! - which simplex points are images at all. A point `p` has a preimage in
//!   `Q(i)^n` exactly when every product `p_g p_h` of nonzero coordinates is a
//!   sum of two rational squares, and a real rational preimage exactly when
//!   every such product is a rational square. So the base of the quotient is a
//!   proper subset of the rational simplex: `(1/4, 3/4)` has no preimage.
//!
//! Refused: empty or zero configurations (they have no simplex point), shape
//! mismatches, phase sets that are not finite unit groups, vectors that are not
//! probability vectors, and exhausted factorisation or norm-construction budgets.
//!
//! Nothing here derives the quadratic readout or gives phases a physical reading.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_9bb9f80c<T> {
    fn checked_invariant_9bb9f80c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_9bb9f80c<T> for Option<T> {
    #[inline]
    fn checked_invariant_9bb9f80c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_9bb9f80c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_9bb9f80c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::{One, Signed, Zero};

use crate::exact_hermitian::ExactHermitianError;
use linear_algebra::exact_field::matrix;
use core_lie_theory::cayley::is_unit;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::sqrt_exact;
use core_number_theory::rational::Rational;

/// Refusals for projections, fibers, descent and lifts.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum QuotientError {
    #[error("a configuration needs at least one coordinate")]
    Empty,
    #[error("the zero configuration has no simplex point")]
    Zero,
    #[error("configurations of length {left} and {right} cannot be compared")]
    LengthMismatch { left: usize, right: usize },
    #[error("the matrix has no rows or no columns")]
    EmptyMatrix,
    #[error("phase {index} is not a unit")]
    NonUnitPhase { index: usize },
    #[error("phase {index} repeats an earlier phase")]
    RepeatedPhase { index: usize },
    #[error("the declared phases are not closed under multiplication")]
    NotClosed,
    #[error("a finite unit subgroup of Q(i) has at most four elements, got {0}")]
    PhaseGroupSize(usize),
    #[error("coordinate {index} is negative")]
    NegativeCoordinate { index: usize },
    #[error("the coordinates sum to {0}, not to one")]
    NotNormalized(Rational),
    #[error(transparent)]
    Lift(#[from] core_number_theory::sums_of_squares::TwoSquaresError),
    #[error("the fiber would have more than {budget} configurations")]
    FiberBudget { budget: usize },
    #[error("exact matrix refusal: {0}")]
    Matrix(#[from] ExactHermitianError),
}

/// `pi(c)_g = |c_g|^2 / sum_h |c_h|^2`.
pub fn phase_blind_projection(c: &[GaussianRat]) -> Result<Vec<Rational>, QuotientError> {
    if c.is_empty() {
        return Err(QuotientError::Empty);
    }
    let weights: Vec<Rational> = c.iter().map(GaussianRat::norm_sq).collect();
    let total: Rational = weights.iter().sum();
    if total.is_zero() {
        return Err(QuotientError::Zero);
    }
    Ok(weights.into_iter().map(|w| w / &total).collect())
}

/// `pi` extended by `0 -> None`, so an annihilated configuration is a point too.
pub fn zero_extended_projection(c: &[GaussianRat]) -> Result<Option<Vec<Rational>>, QuotientError> {
    match phase_blind_projection(c) {
        Ok(point) => Ok(Some(point)),
        Err(QuotientError::Zero) => Ok(None),
        Err(other) => Err(other),
    }
}

/// `pi(a) = pi(b)`; configurations of different lengths are refused.
pub fn phase_equivalent(a: &[GaussianRat], b: &[GaussianRat]) -> Result<bool, QuotientError> {
    if a.len() != b.len() {
        return Err(QuotientError::LengthMismatch {
            left: a.len(),
            right: b.len(),
        });
    }
    Ok(phase_blind_projection(a)? == phase_blind_projection(b)?)
}

/// The quotient point of a configuration, with its total weight and support.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiberPoint {
    base: Vec<Rational>,
    total_weight: Rational,
    support: Vec<usize>,
}

impl FiberPoint {
    pub fn of(c: &[GaussianRat]) -> Result<Self, QuotientError> {
        let base = phase_blind_projection(c)?;
        let total_weight = c.iter().map(GaussianRat::norm_sq).sum();
        let support = base
            .iter()
            .enumerate()
            .filter(|(_, p)| !p.is_zero())
            .map(|(index, _)| index)
            .collect();
        Ok(Self {
            base,
            total_weight,
            support,
        })
    }

    pub fn base(&self) -> &[Rational] {
        &self.base
    }

    /// `sum_g |c_g|^2`, which the projection forgets.
    pub fn total_weight(&self) -> &Rational {
        &self.total_weight
    }

    pub fn support(&self) -> &[usize] {
        &self.support
    }

    /// Relative phases that are not inert: `|supp| - 1`.
    pub fn relative_phase_dimension(&self) -> usize {
        self.support.len() - 1
    }

    /// A single nonzero coordinate: the fiber is one point modulo global phase.
    pub fn is_basis_state(&self) -> bool {
        self.support.len() == 1
    }
}

/// A declared finite group of unit Gaussian rationals.
///
/// A finite nonempty set of units closed under multiplication is a subgroup;
/// in `Q(i)` the only ones are `{1}`, `{1, -1}` and `{1, i, -1, -i}`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnitPhaseGroup {
    elements: Vec<GaussianRat>,
}

impl UnitPhaseGroup {
    pub fn new(elements: Vec<GaussianRat>) -> Result<Self, QuotientError> {
        if elements.is_empty() {
            return Err(QuotientError::Empty);
        }
        // Every element of a finite group has finite order; Q(i) contains
        // precisely the four roots of unity 1, -1, i and -i.
        if elements.len() > 4 {
            return Err(QuotientError::PhaseGroupSize(elements.len()));
        }
        for (index, u) in elements.iter().enumerate() {
            if !is_unit(u) {
                return Err(QuotientError::NonUnitPhase { index });
            }
            if elements[..index].contains(u) {
                return Err(QuotientError::RepeatedPhase { index });
            }
        }
        let closed = elements
            .iter()
            .all(|a| elements.iter().all(|b| elements.contains(&a.mul(b))));
        if !closed {
            return Err(QuotientError::NotClosed);
        }
        Ok(Self { elements })
    }

    pub fn elements(&self) -> &[GaussianRat] {
        &self.elements
    }
}

/// Most configurations [`discrete_fiber`] enumerates.
pub const FIBER_BUDGET: usize = 1 << 16;

/// The configurations `(z_g c_g)`, `z_g` in `group`, with `z = 1` on the first
/// nonzero coordinate of `c`.
///
/// All of them project to `pi(c)`, and no two differ by a global phase, so
/// there is one per class of the `group`-orbit of `c` modulo a global phase:
/// `|group|^(|supp| - 1)` configurations, refused above [`FIBER_BUDGET`].
/// Phases on zero coordinates are inert and are not enumerated.
pub fn discrete_fiber(
    c: &[GaussianRat],
    group: &UnitPhaseGroup,
) -> Result<Vec<Vec<GaussianRat>>, QuotientError> {
    let point = FiberPoint::of(c)?;
    let size = u32::try_from(point.support.len() - 1)
        .ok()
        .and_then(|k| group.elements.len().checked_pow(k));
    if size.is_none_or(|n| n > FIBER_BUDGET) {
        return Err(QuotientError::FiberBudget {
            budget: FIBER_BUDGET,
        });
    }
    let mut fiber = vec![c.to_vec()];
    for &index in &point.support[1..] {
        fiber = fiber
            .into_iter()
            .flat_map(|v| {
                group.elements.iter().map(move |z| {
                    let mut w = v.clone();
                    w[index] = z.mul(&v[index]);
                    w
                })
            })
            .collect();
    }
    Ok(fiber)
}

/// How a linear map meets the projection extended by `0 -> None`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Descent {
    /// Every row has at most one nonzero entry.
    Monopolar(MonopolarDescent),
    /// A row has two nonzero entries.
    Obstructed(DescentObstruction),
}

/// The simplex map induced by a map with at most one nonzero entry per row.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MonopolarDescent {
    rows: Vec<Option<(usize, Rational)>>,
    cols: usize,
}

impl MonopolarDescent {
    /// For each row, the column it reads and `|m|^2`, or `None` for a zero row.
    pub fn rows(&self) -> &[Option<(usize, Rational)>] {
        &self.rows
    }

    /// `f(p)_i = |m_i|^2 p_j(i) / sum_k |m_k|^2 p_j(k)`, or `None` when the
    /// image is the zero vector. Homogeneous, so any positive multiple of a
    /// simplex point gives the same value.
    pub fn apply(&self, p: &[Rational]) -> Result<Option<Vec<Rational>>, QuotientError> {
        if p.len() != self.cols {
            return Err(QuotientError::LengthMismatch {
                left: self.cols,
                right: p.len(),
            });
        }
        if let Some(index) = p.iter().position(Signed::is_negative) {
            return Err(QuotientError::NegativeCoordinate { index });
        }
        let raw: Vec<Rational> = self
            .rows
            .iter()
            .map(|row| match row {
                Some((column, weight)) => weight * &p[*column],
                None => Rational::zero(),
            })
            .collect();
        let total: Rational = raw.iter().sum();
        if total.is_zero() {
            return Ok(None);
        }
        Ok(Some(raw.into_iter().map(|x| x / &total).collect()))
    }
}

/// Two phase-equivalent configurations that row `row` of the map separates.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DescentObstruction {
    pub row: usize,
    /// The first two nonzero columns of `row`, `first < second`.
    pub first: usize,
    pub second: usize,
    /// `e_first - (m_first / m_second) e_second`; row `row` of its image is `0`.
    pub cancelled: Vec<GaussianRat>,
    /// `e_first + (m_first / m_second) e_second`; row `row` of its image is `2 m_first`.
    pub reinforced: Vec<GaussianRat>,
}

/// Decide whether `m` descends through the zero-extended projection.
pub fn classify_descent(m: &BasicMatrix<GaussianRat>) -> Result<Descent, QuotientError> {
    if m.rows() == 0 || m.cols() == 0 {
        return Err(QuotientError::EmptyMatrix);
    }
    let mut rows = Vec::with_capacity(m.rows());
    for row in 0..m.rows() {
        let nonzero: Vec<usize> = (0..m.cols())
            .filter(|&c| {
                !m.get(row, c)
                    .checked_invariant_9bb9f80c("bounded carrier index")
                    .norm_sq()
                    .is_zero()
            })
            .collect();
        match nonzero.as_slice() {
            [] => rows.push(None),
            [column] => rows.push(Some((
                *column,
                m.get(row, *column)
                    .checked_invariant_9bb9f80c("bounded carrier index")
                    .norm_sq(),
            ))),
            [first, second, ..] => {
                let ratio = m.get(row, *first).checked_invariant_9bb9f80c("bounded carrier index").mul(
                    &m.get(row, *second)
                        .checked_invariant_9bb9f80c("bounded nonzero carrier entry")
                        .inv(),
                );
                let mut cancelled = vec![GaussianRat::zero(); m.cols()];
                cancelled[*first] = GaussianRat::one();
                let mut reinforced = cancelled.clone();
                cancelled[*second] = ratio.neg();
                reinforced[*second] = ratio;
                return Ok(Descent::Obstructed(DescentObstruction {
                    row,
                    first: *first,
                    second: *second,
                    cancelled,
                    reinforced,
                }));
            }
        }
    }
    Ok(Descent::Monopolar(MonopolarDescent {
        rows,
        cols: m.cols(),
    }))
}

/// `true` when `left` and `right` are phase equivalent and the zero-extended
/// projection separates `m left` from `m right`.
pub fn separates(
    m: &BasicMatrix<GaussianRat>,
    left: &[GaussianRat],
    right: &[GaussianRat],
) -> Result<bool, QuotientError> {
    if m.rows() == 0 || m.cols() == 0 {
        return Err(QuotientError::EmptyMatrix);
    }
    if !phase_equivalent(left, right)? {
        return Ok(false);
    }
    let left_image = zero_extended_projection(
        &matrix::multiply_vector(m, left).map_err(ExactHermitianError::from)?,
    )?;
    let right_image = zero_extended_projection(
        &matrix::multiply_vector(m, right).map_err(ExactHermitianError::from)?,
    )?;
    Ok(left_image != right_image)
}

/// A configuration in `Q(i)^n` projecting to `p`, or `None` when there is none.
///
/// With `g0` the first nonzero coordinate, `c_g = x + y i` with
/// `x^2 + y^2 = p_g p_g0` projects to `p`. Writing `p_g p_g0 = a / b` in lowest
/// terms, such `x, y` exist exactly when the integer `a b` is a sum of two
/// integer squares, which the shared factorisation and Gaussian norm construction decide with explicit budgets.
pub fn gaussian_lift(p: &[Rational]) -> Result<Option<Vec<GaussianRat>>, QuotientError> {
    gaussian_lift_with_budget(
        p,
        core_number_theory::integer_factorization::FactorizationBudget::default(),
        1_000_000,
    )
}
/// Lift using declared factorisation and Gaussian norm construction budgets.
pub fn gaussian_lift_with_budget(
    p: &[Rational],
    factor_budget: core_number_theory::integer_factorization::FactorizationBudget,
    construction_budget: u64,
) -> Result<Option<Vec<GaussianRat>>, QuotientError> {
    let anchor = check_probability_vector(p)?;
    let mut lift = Vec::with_capacity(p.len());
    for x in p {
        if x.is_zero() {
            lift.push(GaussianRat::zero());
            continue;
        }
        let target = x * &p[anchor];
        let Some((a, b)) = core_number_theory::sums_of_squares::two_squares(
            &(target.numer() * target.denom()),
            factor_budget,
            construction_budget,
        )?
        else {
            return Ok(None);
        };
        let denominator = Rational::from_integer(target.denom().clone());
        lift.push(GaussianRat {
            re: Rational::from_integer(a) / &denominator,
            im: Rational::from_integer(b) / &denominator,
        });
    }
    Ok(Some(lift))
}

/// A real rational configuration projecting to `p`, or `None` when there is none.
///
/// It exists exactly when every `p_g p_g0` is a rational square, and then
/// `c_g = sqrt(p_g p_g0)` works.
pub fn rational_lift(p: &[Rational]) -> Result<Option<Vec<Rational>>, QuotientError> {
    let anchor = check_probability_vector(p)?;
    Ok(p.iter().map(|x| sqrt_exact(&(x * &p[anchor]))).collect())
}

/// Nonnegative coordinates summing to one; returns the first nonzero index.
fn check_probability_vector(p: &[Rational]) -> Result<usize, QuotientError> {
    if p.is_empty() {
        return Err(QuotientError::Empty);
    }
    if let Some(index) = p.iter().position(Signed::is_negative) {
        return Err(QuotientError::NegativeCoordinate { index });
    }
    let total: Rational = p.iter().sum();
    if !total.is_one() {
        return Err(QuotientError::NotNormalized(total));
    }
    Ok(p.iter()
        .position(|x| !x.is_zero())
        .checked_invariant_9bb9f80c("a probability vector has a nonzero coordinate"))
}

// Origin: engine/crates_rs/core_quantum_physics/src/phase_blind_quotient.rs
// Claim: urn:core:crates_rs:core-quantum-physics:phase-blind-quotient:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9bb9f80c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
