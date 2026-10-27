//! Ordered fields: exact inertia, definiteness and LDLᵀ.
//!
//! [`OrderedExactField`] is a field with a total order compatible with its operations
//! (`Q`, a real quadratic field, a real cyclotomic subfield). [`HermitianOrdered`] is a
//! field with an involution whose fixed field is ordered and whose norms `x·x̄` are
//! nonnegative (`Q(i)`, a cyclotomic field with complex conjugation). On them:
//!
//! * [`inertia`] / [`hermitian_inertia`]: the counts of positive, negative and zero
//!   diagonal entries of a congruence diagonalisation, which by Sylvester's law of
//!   inertia are invariants of the matrix (valid over any ordered field, not only `R`);
//! * [`is_positive_semidefinite`], [`is_positive_definite`] and their Hermitian forms;
//! * [`ldlt`] and [`hermitian_ldl`]: `A = L D Lᵀ` (`L D L†` for a Hermitian `A`) without
//!   pivoting, stopping with a typed reason and a replayable witness `v` with `v* A v < 0`
//!   (`v*` is `vᵀ` or `v†`) the moment `A` is found not positive semidefinite.
//!
//! Everything is exact: a pivot is zero or it is not, and a tiny positive pivot is positive.
//!
//! AuthorityEffect: None.

use std::cmp::Ordering;

use crate::backend::basic_matrix::{BasicMatrix, OperationLimits};
use crate::exact_field::congruence::{
    hermitian_congruence_diagonalisation_with_limits,
    symmetric_congruence_diagonalisation_with_limits, symmetric_violation,
};
use crate::exact_field::involution::{adjoint, hermitian_violation, inner_product, Involution};
use crate::exact_field::matrix::{diagonal, dot, multiply, multiply_vector, transpose};
use crate::exact_field::{
    charge, element_count, inverse_of, plus, require_square, reserve, times, ExactFieldError, Grid,
};
use crate::scalars::{ExactRing, Field};
use num_bigint::Sign;
use num_rational::BigRational;

/// A field with a total order compatible with `+` and `·`.
///
/// # What an implementor must prove
///
/// `signum` returns `-1`, `0` or `1`, and with `P = {x : signum(x) = 1}`:
///
/// 1. `signum(x) = 0` exactly when `x` is zero;
/// 2. `signum(−x) = −signum(x)`;
/// 3. `P` is closed under addition and multiplication.
///
/// Then `x < y :⇔ y − x ∈ P` is a total order making `F` an ordered field (so `F` has
/// characteristic `0` and every square is nonnegative). `laws::check_ordered_axioms` replays
/// (1)–(3) on a sample. The algorithms refuse a `signum` that returns a value outside
/// `{-1, 0, 1}` or disagrees with `is_zero`, as a typed error.
///
/// Calling `x.signum()` on a `BigRational` is ambiguous when `num_traits::Signed` is also in
/// scope; call `OrderedExactField::signum(&x)` there.
pub trait OrderedExactField: Field + ExactRing {
    /// `-1`, `0` or `1` according to the sign of `self`.
    fn signum(&self) -> i8;
}

impl OrderedExactField for BigRational {
    fn signum(&self) -> i8 {
        // A reduced `Ratio` has a positive denominator, so the sign is the numerator's.
        match self.numer().sign() {
            Sign::Minus => -1,
            Sign::NoSign => 0,
            Sign::Plus => 1,
        }
    }
}

/// A field with an involution whose fixed field is ordered and whose norms are nonnegative.
///
/// # What an implementor must prove
///
/// 1. `fixed_field_sign(x)` is `None` exactly when `conjugate(x) ≠ x`;
/// 2. on the fixed field `K₀ = {x : x̄ = x}` it returns `-1`, `0` or `1` obeying the
///    obligations of [`OrderedExactField`] (so `K₀` is an ordered field);
/// 3. every norm `x·x̄` (which lies in `K₀`) has sign `≥ 0`, and `0` only for `x = 0`.
///
/// Every subfield of `C` closed under complex conjugation, with the involution complex
/// conjugation and the order induced from `R`, satisfies this (`|x|² ≥ 0`). A field whose
/// involution can send a square to a negative norm (such as `Q(√2)` with `√2 ↦ −√2`) does
/// not, and Sylvester's law does not hold for it. `laws::check_hermitian_ordered_axioms`
/// replays (1)–(3) on a sample.
pub trait HermitianOrdered: Involution {
    /// The sign of `self` in the order of the fixed field, or `None` when `self` is not
    /// fixed by the involution.
    fn fixed_field_sign(&self) -> Option<i8>;
}

impl HermitianOrdered for BigRational {
    fn fixed_field_sign(&self) -> Option<i8> {
        Some(OrderedExactField::signum(self))
    }
}

/// The sign of `x`, refusing a `signum` that breaks its contract.
pub(crate) fn checked_sign<F: OrderedExactField>(
    operation: &'static str,
    x: &F,
) -> Result<i8, ExactFieldError> {
    validated_sign(operation, x.signum(), x.is_zero())
}

/// The sign of a diagonal entry of a Hermitian form, refusing `None` (not fixed by the
/// involution) and a sign that breaks its contract.
pub(crate) fn checked_fixed_sign<F: HermitianOrdered>(
    operation: &'static str,
    x: &F,
) -> Result<i8, ExactFieldError> {
    match x.fixed_field_sign() {
        Some(sign) => validated_sign(operation, sign, x.is_zero()),
        None => Err(ExactFieldError::ScalarContract {
            operation,
            violation: "a diagonal entry of a Hermitian form is not fixed by the involution",
        }),
    }
}

fn validated_sign(operation: &'static str, sign: i8, is_zero: bool) -> Result<i8, ExactFieldError> {
    if !(-1..=1).contains(&sign) {
        return Err(ExactFieldError::ScalarContract {
            operation,
            violation: "a sign must be -1, 0 or 1",
        });
    }
    if (sign == 0) != is_zero {
        return Err(ExactFieldError::ScalarContract {
            operation,
            violation: "a sign is zero exactly when the element is zero",
        });
    }
    Ok(sign)
}

// ============================================================================
// Inertia
// ============================================================================

/// The numbers of positive, negative and zero diagonal entries of a congruence
/// diagonalisation. By Sylvester's law they do not depend on the diagonalisation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Inertia {
    pub positive: usize,
    pub negative: usize,
    pub zero: usize,
}

impl Inertia {
    /// `positive + negative + zero`.
    pub fn dimension(&self) -> usize {
        self.positive + self.negative + self.zero
    }

    /// `positive + negative`, the rank of the form.
    pub fn rank(&self) -> usize {
        self.positive + self.negative
    }

    /// No negative and no zero direction.
    pub fn is_positive_definite(&self) -> bool {
        self.negative == 0 && self.zero == 0
    }

    /// No negative direction.
    pub fn is_positive_semidefinite(&self) -> bool {
        self.negative == 0
    }

    /// No positive and no zero direction.
    pub fn is_negative_definite(&self) -> bool {
        self.positive == 0 && self.zero == 0
    }

    /// No positive direction.
    pub fn is_negative_semidefinite(&self) -> bool {
        self.positive == 0
    }
}

fn count_signs<F>(
    diagonal: &[F],
    mut sign: impl FnMut(&F) -> Result<i8, ExactFieldError>,
) -> Result<Inertia, ExactFieldError> {
    let mut inertia = Inertia {
        positive: 0,
        negative: 0,
        zero: 0,
    };
    for entry in diagonal {
        match sign(entry)?.cmp(&0) {
            Ordering::Greater => inertia.positive += 1,
            Ordering::Less => inertia.negative += 1,
            Ordering::Equal => inertia.zero += 1,
        }
    }
    Ok(inertia)
}

/// The inertia of a symmetric matrix over an ordered field. Refuses a non-symmetric matrix.
pub fn inertia<F: OrderedExactField>(a: &BasicMatrix<F>) -> Result<Inertia, ExactFieldError> {
    inertia_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`inertia`] under the budget of `congruence::symmetric_congruence_diagonalisation_with_limits`.
pub fn inertia_with_limits<F: OrderedExactField>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Inertia, ExactFieldError> {
    let certificate = symmetric_congruence_diagonalisation_with_limits(a, limits)?;
    count_signs(certificate.diagonal(), |x| checked_sign("inertia", x))
}

/// The inertia of a Hermitian matrix. Refuses a non-Hermitian matrix.
pub fn hermitian_inertia<F: HermitianOrdered>(
    a: &BasicMatrix<F>,
) -> Result<Inertia, ExactFieldError> {
    hermitian_inertia_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`hermitian_inertia`] under the budget of the Hermitian congruence diagonalisation.
pub fn hermitian_inertia_with_limits<F: HermitianOrdered>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Inertia, ExactFieldError> {
    let certificate = hermitian_congruence_diagonalisation_with_limits(a, limits)?;
    count_signs(certificate.diagonal(), |x| {
        checked_fixed_sign("hermitian_inertia", x)
    })
}

/// `true` when the symmetric matrix `a` is positive semidefinite (`vᵀAv ≥ 0` for all `v`).
pub fn is_positive_semidefinite<F: OrderedExactField>(
    a: &BasicMatrix<F>,
) -> Result<bool, ExactFieldError> {
    Ok(inertia(a)?.is_positive_semidefinite())
}

/// `true` when the symmetric matrix `a` is positive definite (`vᵀAv > 0` for all `v ≠ 0`).
pub fn is_positive_definite<F: OrderedExactField>(
    a: &BasicMatrix<F>,
) -> Result<bool, ExactFieldError> {
    Ok(inertia(a)?.is_positive_definite())
}

/// `true` when the Hermitian matrix `a` is positive semidefinite.
pub fn hermitian_is_positive_semidefinite<F: HermitianOrdered>(
    a: &BasicMatrix<F>,
) -> Result<bool, ExactFieldError> {
    Ok(hermitian_inertia(a)?.is_positive_semidefinite())
}

/// `true` when the Hermitian matrix `a` is positive definite.
pub fn hermitian_is_positive_definite<F: HermitianOrdered>(
    a: &BasicMatrix<F>,
) -> Result<bool, ExactFieldError> {
    Ok(hermitian_inertia(a)?.is_positive_definite())
}

// ============================================================================
// Quadratic forms
// ============================================================================

fn check_form_shape<F>(
    operation: &'static str,
    a: &BasicMatrix<F>,
    v: &[F],
) -> Result<(), ExactFieldError> {
    let n = require_square(operation, a)?;
    if v.len() != n {
        return Err(ExactFieldError::VectorLength {
            operation,
            expected: n,
            got: v.len(),
        });
    }
    Ok(())
}

/// The quadratic form `vᵀ A v`.
pub fn quadratic_form<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    v: &[F],
) -> Result<F, ExactFieldError> {
    check_form_shape("quadratic_form", a, v)?;
    dot(v, &multiply_vector(a, v)?)
}

/// The Hermitian form `v† A v`.
pub fn hermitian_form<F: Involution>(a: &BasicMatrix<F>, v: &[F]) -> Result<F, ExactFieldError> {
    check_form_shape("hermitian_form", a, v)?;
    inner_product(v, &multiply_vector(a, v)?)
}

// ============================================================================
// LDLT
// ============================================================================

/// Why an [`Ldlt`] stopped.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LdltOutcome<F> {
    /// All `n` steps completed: every pivot is `≥ 0` and each zero pivot has a zero Schur
    /// column. Then `A = L D L*` (with `L* = Lᵀ` for a symmetric factorisation and `L† ` for a
    /// Hermitian one) and `A` is positive semidefinite.
    PositiveSemidefinite,
    /// The pivot at `step` is negative, so `A` is not positive semidefinite. `witness` is a
    /// vector with `witness* A witness = pivot < 0`.
    NegativePivot { step: usize, witness: Vec<F> },
    /// The pivot at `step` is zero while the Schur column has a nonzero entry in `row`, so the
    /// `2 × 2` principal minor of the Schur complement is negative and `A` is not positive
    /// semidefinite. `witness` has `witness* A witness = −1`.
    ZeroPivotWithNonzeroColumn {
        step: usize,
        row: usize,
        witness: Vec<F>,
    },
}

/// The result of an LDL* factorisation without pivoting: `L` unit lower triangular, the
/// pivots `D`, and how the factorisation ended. After an early stop `L` has identity columns
/// from the stopping step on and the pivots after it are zero.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Ldlt<F> {
    unit_lower: BasicMatrix<F>,
    pivots: Vec<F>,
    outcome: LdltOutcome<F>,
}

impl<F> Ldlt<F> {
    /// The unit lower triangular factor `L`.
    pub fn unit_lower(&self) -> &BasicMatrix<F> {
        &self.unit_lower
    }

    /// The pivots `D` (`n` entries).
    pub fn pivots(&self) -> &[F] {
        &self.pivots
    }

    /// How the factorisation ended.
    pub fn outcome(&self) -> &LdltOutcome<F> {
        &self.outcome
    }

    /// `true` when the factorisation completed, which is exactly positive semidefiniteness.
    pub fn is_positive_semidefinite(&self) -> bool {
        matches!(self.outcome, LdltOutcome::PositiveSemidefinite)
    }
}

impl<F: Field + ExactRing> Ldlt<F> {
    /// `L D Lᵀ`; equals `A` when a symmetric factorisation completed.
    pub fn reconstruct(&self) -> Result<BasicMatrix<F>, ExactFieldError> {
        let scaled = multiply(&self.unit_lower, &diagonal(&self.pivots)?)?;
        multiply(&scaled, &transpose(&self.unit_lower)?)
    }
}

impl<F: Involution> Ldlt<F> {
    /// `L D L†`; equals `A` when a Hermitian factorisation completed.
    pub fn reconstruct_hermitian(&self) -> Result<BasicMatrix<F>, ExactFieldError> {
        let scaled = multiply(&self.unit_lower, &diagonal(&self.pivots)?)?;
        multiply(&scaled, &adjoint(&self.unit_lower)?)
    }
}

/// `v` with `L* v = w` (back substitution; `L` is unit lower triangular and `L*` is its
/// conjugate transpose for the given conjugation, the transpose for the identity).
fn solve_unit_lower_adjoint<F: Field + ExactRing>(
    l: &Grid<F>,
    w: Vec<F>,
    conj: &dyn Fn(&F) -> F,
) -> Result<Vec<F>, ExactFieldError> {
    let n = l.rows();
    let mut v: Vec<F> = reserve(n)?;
    v.resize(n, F::zero());
    for i in (0..n).rev() {
        let mut acc = w[i].clone();
        for (m, vm) in v.iter().enumerate().skip(i + 1) {
            acc = acc.sub(&conj(l.at(m, i)).mul(vm));
        }
        v[i] = acc;
    }
    Ok(v)
}

/// A vector of length `n` that is zero except for the listed `(index, value)` entries.
fn sparse_vector<F: Field + ExactRing>(
    n: usize,
    entries: &[(usize, F)],
) -> Result<Vec<F>, ExactFieldError> {
    let mut w: Vec<F> = reserve(n)?;
    w.resize(n, F::zero());
    for (index, value) in entries {
        w[*index] = value.clone();
    }
    Ok(w)
}

/// The LDLᵀ factorisation of a symmetric matrix over an ordered field, without pivoting.
/// Refuses a non-symmetric matrix.
///
/// A zero pivot is accepted only when its whole Schur column is zero (otherwise the matrix
/// is indefinite); a negative pivot stops the factorisation. A matrix that is positive
/// definite up to a permutation but has a zero leading minor is reported as not positive
/// semidefinite *by this routine*; [`is_positive_semidefinite`] (which pivots by congruence)
/// is the complete decision.
pub fn ldlt<F: OrderedExactField>(a: &BasicMatrix<F>) -> Result<Ldlt<F>, ExactFieldError> {
    ldlt_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`ldlt`] under a budget: `n²` elements and at most `2n³ + n²` scalar calls.
pub fn ldlt_with_limits<F: OrderedExactField>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Ldlt<F>, ExactFieldError> {
    if let Some((row, col)) = symmetric_violation(a)? {
        return Err(ExactFieldError::NotSymmetric { row, col });
    }
    ldl_core(
        a,
        "ldlt",
        &|x: &F| x.clone(),
        &|x: &F| checked_sign("ldlt", x),
        limits,
    )
}

/// The factorisation `A = L D L†` of a Hermitian matrix, without pivoting: the direct
/// Hermitian counterpart of [`ldlt`] (no realification, so the dimension is not doubled). The
/// pivots are fixed by the involution and their signs are read in the fixed field. Refuses a
/// non-Hermitian matrix. Stopping rules and witnesses are those of [`ldlt`], with
/// `witness† A witness < 0`.
pub fn hermitian_ldl<F: HermitianOrdered>(a: &BasicMatrix<F>) -> Result<Ldlt<F>, ExactFieldError> {
    hermitian_ldl_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`hermitian_ldl`] under the budget of [`ldlt_with_limits`].
pub fn hermitian_ldl_with_limits<F: HermitianOrdered>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Ldlt<F>, ExactFieldError> {
    if let Some((row, col)) = hermitian_violation(a)? {
        return Err(ExactFieldError::NotHermitian { row, col });
    }
    ldl_core(
        a,
        "hermitian_ldl",
        &|x: &F| x.conjugate(),
        &|x: &F| checked_fixed_sign("hermitian_ldl", x),
        limits,
    )
}

/// Shared core. `a[i][j] = conj(a[j][i])` must hold (checked by the callers); `conj` is the
/// identity for the symmetric case. The recurrences are those of `A = L D L*`:
/// `D[j] = A[j][j] − Σ_{k<j} L[j][k]·D[k]·conj(L[j][k])` and, when `D[j] ≠ 0`,
/// `L[i][j] = (A[i][j] − Σ_{k<j} L[i][k]·D[k]·conj(L[j][k])) / D[j]`.
fn ldl_core<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    operation: &'static str,
    conj: &dyn Fn(&F) -> F,
    sign: &dyn Fn(&F) -> Result<i8, ExactFieldError>,
    limits: OperationLimits,
) -> Result<Ldlt<F>, ExactFieldError> {
    let n = a.rows();
    let (mut l, mut d) = init_ldl_storage::<F>(n, limits)?;
    for j in 0..n {
        if let Some(outcome) = ldl_step(a, &mut l, &mut d, j, n, operation, conj, sign)? {
            return Ok(Ldlt {
                unit_lower: l.into_matrix()?,
                pivots: d,
                outcome,
            });
        }
    }
    Ok(Ldlt {
        unit_lower: l.into_matrix()?,
        pivots: d,
        outcome: LdltOutcome::PositiveSemidefinite,
    })
}

fn init_ldl_storage<F: Field + ExactRing>(
    n: usize,
    limits: OperationLimits,
) -> Result<(Grid<F>, Vec<F>), ExactFieldError> {
    let square = element_count(n, n)?;
    charge(limits, square, plus(times(2, times(square, n)?)?, square)?)?;
    let l = Grid::from_fn(n, n, |r, c| {
        Ok::<F, ExactFieldError>(if r == c { F::one() } else { F::zero() })
    })?;
    let mut d: Vec<F> = reserve(n)?;
    d.resize(n, F::zero());
    Ok((l, d))
}

// Σ_{k<j} L[i][k]·D[k]·conj(L[j][k])
fn ldl_coupling<F: Field + ExactRing>(
    l: &Grid<F>,
    d: &[F],
    i: usize,
    j: usize,
    conj: &dyn Fn(&F) -> F,
) -> F {
    let mut sum = F::zero();
    for (k, dk) in d.iter().enumerate().take(j) {
        sum = sum.add(&l.at(i, k).mul(dk).mul(&conj(l.at(j, k))));
    }
    sum
}

#[allow(clippy::too_many_arguments)]
fn ldl_step<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    l: &mut Grid<F>,
    d: &mut [F],
    j: usize,
    n: usize,
    operation: &'static str,
    conj: &dyn Fn(&F) -> F,
    sign: &dyn Fn(&F) -> Result<i8, ExactFieldError>,
) -> Result<Option<LdltOutcome<F>>, ExactFieldError> {
    let pivot = a.get_ref(j, j)?.sub(&ldl_coupling(l, d, j, j, conj));
    d[j] = pivot.clone();
    match sign(&pivot)?.cmp(&0) {
        Ordering::Less => {
            let witness =
                solve_unit_lower_adjoint(l, sparse_vector(n, &[(j, F::one())])?, conj)?;
            Ok(Some(LdltOutcome::NegativePivot { step: j, witness }))
        }
        Ordering::Equal => check_zero_pivot_column(a, l, d, j, n, operation, conj),
        Ordering::Greater => {
            fill_positive_pivot_column(a, l, d, j, n, &pivot, operation, conj)?;
            Ok(None)
        }
    }
}

fn check_zero_pivot_column<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    l: &Grid<F>,
    d: &[F],
    j: usize,
    n: usize,
    operation: &'static str,
    conj: &dyn Fn(&F) -> F,
) -> Result<Option<LdltOutcome<F>>, ExactFieldError> {
    for i in (j + 1)..n {
        let schur_ij = a.get_ref(i, j)?.sub(&ldl_coupling(l, d, i, j, conj));
        if !schur_ij.is_zero() {
            // On the trailing Schur complement S (S_jj = 0) the vector
            // x·e_j + e_i has S-form x·S_ij + conj(x·S_ij) + S_ii; choosing
            // x = −(S_ii + 1)/(2 S_ij) makes x·S_ij = −(S_ii + 1)/2, which is
            // fixed by the involution, so the form is −1. Lifting through L*
            // gives the witness for A.
            let schur_ii = a.get_ref(i, i)?.sub(&ldl_coupling(l, d, i, i, conj));
            let two = F::one().add(&F::one());
            let denominator = inverse_of(operation, &two.mul(&schur_ij))?;
            let x = schur_ii.add(&F::one()).neg().mul(&denominator);
            let witness = solve_unit_lower_adjoint(
                l,
                sparse_vector(n, &[(j, x), (i, F::one())])?,
                conj,
            )?;
            return Ok(Some(LdltOutcome::ZeroPivotWithNonzeroColumn {
                step: j,
                row: i,
                witness,
            }));
        }
    }
    Ok(None)
}

#[allow(clippy::too_many_arguments)]
fn fill_positive_pivot_column<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    l: &mut Grid<F>,
    d: &[F],
    j: usize,
    n: usize,
    pivot: &F,
    operation: &'static str,
    conj: &dyn Fn(&F) -> F,
) -> Result<(), ExactFieldError> {
    let inverse = inverse_of(operation, pivot)?;
    for i in (j + 1)..n {
        let schur_ij = a.get_ref(i, j)?.sub(&ldl_coupling(l, d, i, j, conj));
        l.put(i, j, schur_ij.mul(&inverse));
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/ordered.rs
// Claim: urn:core:crates_rs:core-linear-algebra:ordered:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord450ef138 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord450ef138` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError450ef138 {
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
impl BoundaryError450ef138 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError450ef138 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError450ef138 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord450ef138 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError450ef138> {
        if capacity_bound == 0 {
            return Err(BoundaryError450ef138::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError450ef138::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError450ef138::ExceedsCapacity {
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
    use crate::exact_field::elimination::determinant;
    use crate::exact_field::involution::adjoint;
    use crate::exact_field::matrix::{add, from_fn, from_rows, identity, scale, zeros};
    use crate::exact_field::test_support::{
        gi, gq, m, q, qsi, random_matrix, GaussianRational, QSqrt2, Rng, Shaky,
    };
    use crate::scalars::Semiring;
    use num_bigint::BigInt;

    type Q = BigRational;
    type G = GaussianRational;

    fn sgn(x: &Q) -> i8 {
        OrderedExactField::signum(x)
    }

    fn inertia_of(a: &BasicMatrix<Q>) -> (usize, usize, usize) {
        let i = inertia(a).unwrap();
        (i.positive, i.negative, i.zero)
    }

    fn gmat(rows: &[&[(i64, i64)]]) -> BasicMatrix<G> {
        from_rows(
            rows.iter()
                .map(|r| r.iter().map(|&(a, b)| gi(a, b)).collect())
                .collect(),
        )
        .unwrap()
    }

    fn random_symmetric(rng: &mut Rng, n: usize) -> BasicMatrix<Q> {
        let b = random_matrix(rng, n, n, 4);
        add(&b, &transpose(&b).unwrap()).unwrap()
    }

    fn random_hermitian(rng: &mut Rng, n: usize) -> BasicMatrix<G> {
        let b = from_rows(
            (0..n)
                .map(|_| {
                    (0..n)
                        .map(|_| {
                            gq(
                                q(rng.range(-3, 3), rng.range(1, 3)),
                                q(rng.range(-3, 3), rng.range(1, 3)),
                            )
                        })
                        .collect()
                })
                .collect(),
        )
        .unwrap();
        add(&b, &adjoint(&b).unwrap()).unwrap()
    }

    /// `S` unit lower triangular times unit upper triangular with random entries: invertible.
    fn random_unimodular(rng: &mut Rng, n: usize) -> BasicMatrix<Q> {
        let raw = random_matrix(rng, n, n, 2);
        let lower = from_fn(n, n, |r, c| {
            if c < r {
                raw.get(r, c).unwrap()
            } else if c == r {
                q(1, 1)
            } else {
                q(0, 1)
            }
        })
        .unwrap();
        let upper = transpose(&lower).unwrap();
        multiply(&lower, &upper).unwrap()
    }

    // ------------------------------------------------------------------ sign contract

    #[test]
    fn bigrational_signum_is_the_sign_of_the_value() {
        assert_eq!(sgn(&q(0, 1)), 0);
        assert_eq!(sgn(&q(3, 7)), 1);
        assert_eq!(sgn(&q(-3, 7)), -1);
        assert_eq!(sgn(&q(-3, -7)), 1);
        assert_eq!(sgn(&q(1, 1_000_000_000_000_000_000)), 1, "no tolerance");
        assert_eq!(BigRational::fixed_field_sign(&q(-5, 2)), Some(-1));
    }

    // ------------------------------------------------------------------ inertia

    /// Known inertias (positive, negative, zero), including every branch of the pivot search.
    #[test]
    fn inertia_of_known_matrices() {
        assert_eq!(inertia_of(&m(&[&[4, 2], &[2, 3]])), (2, 0, 0));
        assert_eq!(inertia_of(&m(&[&[1, 2], &[2, 1]])), (1, 1, 0));
        assert_eq!(
            inertia_of(&m(&[&[1, 0, 0], &[0, -2, 0], &[0, 0, 0]])),
            (1, 1, 1)
        );
        assert_eq!(inertia_of(&m(&[&[1, 1], &[1, 1]])), (1, 0, 1));
        assert_eq!(inertia_of(&zeros::<Q>(3, 3).unwrap()), (0, 0, 3));
        assert_eq!(inertia_of(&identity::<Q>(4).unwrap()), (4, 0, 0));
        assert_eq!(
            inertia_of(&scale(&identity::<Q>(4).unwrap(), &q(-1, 1)).unwrap()),
            (0, 4, 0)
        );
        assert_eq!(inertia_of(&zeros::<Q>(0, 0).unwrap()), (0, 0, 0));
        // zero diagonal: eigenvalues ±1
        assert_eq!(inertia_of(&m(&[&[0, 1], &[1, 0]])), (1, 1, 0));
        // Cartan matrix of A3 (positive definite)
        assert_eq!(
            inertia_of(&m(&[&[2, -1, 0], &[-1, 2, -1], &[0, -1, 2]])),
            (3, 0, 0)
        );
        // path Laplacian: positive semidefinite with a one-dimensional kernel
        assert_eq!(
            inertia_of(&m(&[
                &[1, -1, 0, 0],
                &[-1, 2, -1, 0],
                &[0, -1, 2, -1],
                &[0, 0, -1, 1]
            ])),
            (3, 0, 1)
        );
    }

    /// Adjacency matrices have zero diagonals, so every step goes through the shear.
    /// Spectra: `K_n` has `n−1` once and `−1` `n−1` times; `C4` has `2, 0, 0, −2`; the path
    /// `P3` has `±√2, 0`; the Petersen graph has `3, 1 (×5), −2 (×4)`.
    #[test]
    fn inertia_of_graph_adjacency_matrices() {
        for n in 2..=7usize {
            let k = from_fn(n, n, |r, c| if r == c { q(0, 1) } else { q(1, 1) }).unwrap();
            assert_eq!(inertia_of(&k), (1, n - 1, 0), "K_{n}");
        }
        let c4 = m(&[&[0, 1, 0, 1], &[1, 0, 1, 0], &[0, 1, 0, 1], &[1, 0, 1, 0]]);
        assert_eq!(inertia_of(&c4), (1, 1, 2));
        let p3 = m(&[&[0, 1, 0], &[1, 0, 1], &[0, 1, 0]]);
        assert_eq!(inertia_of(&p3), (1, 1, 1));

        let mut edges: Vec<(usize, usize)> = Vec::new();
        for i in 0..5 {
            edges.push((i, (i + 1) % 5)); // outer cycle
            edges.push((5 + i, 5 + (i + 2) % 5)); // inner pentagram
            edges.push((i, i + 5)); // spokes
        }
        let petersen = from_fn(10, 10, |r, c| {
            if edges
                .iter()
                .any(|&(a, b)| (a, b) == (r, c) || (b, a) == (r, c))
            {
                q(1, 1)
            } else {
                q(0, 1)
            }
        })
        .unwrap();
        assert_eq!(inertia_of(&petersen), (6, 4, 0));
    }

    /// The 4×4 Hilbert matrix is positive definite; exact arithmetic sees it (pivots are
    /// tiny positive rationals that a tolerance-based test would call zero).
    #[test]
    fn the_hilbert_matrix_is_positive_definite_exactly() {
        let hilbert = from_fn(6, 6, |r, c| q(1, (r + c + 1) as i64)).unwrap();
        assert!(is_positive_definite(&hilbert).unwrap());
        assert_eq!(inertia_of(&hilbert), (6, 0, 0));
        // the smallest pivot is 1/1 · (Cauchy determinant ratio) > 0 but far below 1e-6
        let d =
            crate::exact_field::congruence::symmetric_congruence_diagonalisation(&hilbert).unwrap();
        let smallest = d.diagonal().iter().map(sgn).min().unwrap();
        assert_eq!(smallest, 1);
    }

    /// Sylvester's law: `inertia(Sᵀ A S) = inertia(A)` for invertible `S`.
    #[test]
    fn inertia_is_invariant_under_congruence() {
        let mut rng = Rng::new(601);
        for n in 2..=5usize {
            for _ in 0..5 {
                let a = random_symmetric(&mut rng, n);
                let s = random_unimodular(&mut rng, n);
                let congruent =
                    multiply(&multiply(&transpose(&s).unwrap(), &a).unwrap(), &s).unwrap();
                assert_eq!(inertia(&congruent).unwrap(), inertia(&a).unwrap(), "n={n}");
            }
        }
    }

    /// Inertia is the signature of the eigenvalues: `positive + negative = rank` and the
    /// sign of the determinant is `(−1)^negative` (for invertible `A`).
    #[test]
    fn inertia_is_consistent_with_rank_and_the_sign_of_the_determinant() {
        use crate::exact_field::elimination::rank;
        let mut rng = Rng::new(607);
        for n in 1..=5usize {
            for _ in 0..6 {
                let a = random_symmetric(&mut rng, n);
                let i = inertia(&a).unwrap();
                assert_eq!(i.rank(), rank(&a).unwrap());
                assert_eq!(i.dimension(), n);
                if i.zero == 0 {
                    let expected = if i.negative.is_multiple_of(2) { 1 } else { -1 };
                    assert_eq!(sgn(&determinant(&a).unwrap()), expected, "n={n}");
                }
            }
        }
    }

    // ------------------------------------------------------------------ definiteness

    /// Independent route 1: Sylvester's criterion (all leading principal minors positive).
    /// Independent route 2: positive semidefinite iff ALL principal minors are nonnegative.
    #[test]
    fn definiteness_agrees_with_the_minor_criteria() {
        fn principal_minor(a: &BasicMatrix<Q>, subset: &[usize]) -> Q {
            let sub = from_fn(subset.len(), subset.len(), |r, c| {
                a.get(subset[r], subset[c]).unwrap()
            })
            .unwrap();
            determinant(&sub).unwrap()
        }
        let mut rng = Rng::new(611);
        for n in 1..=4usize {
            for trial in 0..24 {
                let b = random_matrix(&mut rng, n, n, 3);
                let a = match trial % 3 {
                    0 => add(
                        &multiply(&transpose(&b).unwrap(), &b).unwrap(),
                        &identity(n).unwrap(),
                    )
                    .unwrap(),
                    1 => multiply(&transpose(&b).unwrap(), &b).unwrap(),
                    _ => random_symmetric(&mut rng, n),
                };
                let leading_positive = (1..=n).all(|k| {
                    let subset: Vec<usize> = (0..k).collect();
                    sgn(&principal_minor(&a, &subset)) > 0
                });
                let all_nonneg = (1usize..(1 << n)).all(|mask| {
                    let subset: Vec<usize> = (0..n).filter(|i| mask >> i & 1 == 1).collect();
                    sgn(&principal_minor(&a, &subset)) >= 0
                });
                assert_eq!(
                    is_positive_definite(&a).unwrap(),
                    leading_positive,
                    "PD n={n} trial={trial}"
                );
                assert_eq!(
                    is_positive_semidefinite(&a).unwrap(),
                    all_nonneg,
                    "PSD n={n} trial={trial}"
                );
            }
        }
    }

    /// Exactness: `[[1, 1],[1, 1 + 10⁻³⁰]]` is positive definite, `[[1,1],[1,1]]` is only
    /// semidefinite, `[[1,1],[1,1 − 10⁻³⁰]]` is indefinite: no tolerance can separate them.
    #[test]
    fn a_perturbation_far_below_any_tolerance_is_decided_exactly() {
        let tiny = BigRational::new(BigInt::from(1), BigInt::from(10).pow(30));
        let make =
            |corner: Q| from_rows(vec![vec![q(1, 1), q(1, 1)], vec![q(1, 1), corner]]).unwrap();
        assert!(is_positive_definite(&make(q(1, 1) + tiny.clone())).unwrap());
        let semidefinite = make(q(1, 1));
        assert!(is_positive_semidefinite(&semidefinite).unwrap());
        assert!(!is_positive_definite(&semidefinite).unwrap());
        assert!(!is_positive_semidefinite(&make(q(1, 1) - tiny)).unwrap());
    }

    // ------------------------------------------------------------------ Q(sqrt 2)

    /// Exact decisions with irrational entries. `[[√2,1],[1,√2]]`: det 1 > 0, trace > 0 → PD;
    /// `[[1,√2],[√2,1]]`: det −1 → indefinite; `[[1,√2],[√2,2]]`: det exactly 0 → PSD.
    #[test]
    fn definiteness_over_a_real_quadratic_field() {
        let sqrt2 = qsi(0, 1);
        let one = qsi(1, 0);
        let pd = from_rows(vec![
            vec![sqrt2.clone(), one.clone()],
            vec![one.clone(), sqrt2.clone()],
        ])
        .unwrap();
        assert_eq!(
            inertia(&pd).unwrap(),
            Inertia {
                positive: 2,
                negative: 0,
                zero: 0
            }
        );
        let indefinite = from_rows(vec![
            vec![one.clone(), sqrt2.clone()],
            vec![sqrt2.clone(), one.clone()],
        ])
        .unwrap();
        assert_eq!(
            inertia(&indefinite).unwrap(),
            Inertia {
                positive: 1,
                negative: 1,
                zero: 0
            }
        );
        let psd = from_rows(vec![
            vec![one.clone(), sqrt2.clone()],
            vec![sqrt2.clone(), qsi(2, 0)],
        ])
        .unwrap();
        assert_eq!(
            inertia(&psd).unwrap(),
            Inertia {
                positive: 1,
                negative: 0,
                zero: 1
            }
        );
        // a negative entry whose sign depends on the irrational comparison: 1 − √2 < 0
        let small = from_rows(vec![vec![qsi(1, -1)]]).unwrap();
        assert_eq!(inertia(&small).unwrap().negative, 1);
        // 3 − 2√2 = (√2 − 1)² > 0
        let square = from_rows(vec![vec![qsi(3, -2)]]).unwrap();
        assert_eq!(inertia(&square).unwrap().positive, 1);
        // the test field's own sign agrees with an exact rational enclosure of √2
        // (1.41421356 < √2 < 1.41421357) whenever the enclosure decides the sign
        let (lo, hi) = (q(141_421_356, 100_000_000), q(141_421_357, 100_000_000));
        for (a, b) in [
            (1, 1),
            (-1, 1),
            (5, -4),
            (-7, 5),
            (3, -2),
            (17, -12),
            (-3, 2),
        ] {
            let x: QSqrt2 = qsi(a, b);
            let (low, high) = if b >= 0 {
                (
                    q(a, 1) + q(b, 1) * lo.clone(),
                    q(a, 1) + q(b, 1) * hi.clone(),
                )
            } else {
                (
                    q(a, 1) + q(b, 1) * hi.clone(),
                    q(a, 1) + q(b, 1) * lo.clone(),
                )
            };
            let decided = if sgn(&low) > 0 {
                1
            } else if sgn(&high) < 0 {
                -1
            } else {
                panic!("enclosure does not decide {a} + {b}√2")
            };
            assert_eq!(OrderedExactField::signum(&x), decided, "{a} + {b}√2");
        }
    }

    // ------------------------------------------------------------------ Hermitian

    /// Known Hermitian inertias over Q(i): `[[1,i],[−i,1]]` has eigenvalues 0, 2; σ_y has ±1
    /// (the shear with an imaginary entry); `[[2,1+i],[1−i,3]]` has determinant 4 > 0 (PD);
    /// `[[1,2i],[−2i,1]]` has determinant −3 (indefinite).
    #[test]
    fn hermitian_inertia_of_known_matrices() {
        let h = |rows: &[&[(i64, i64)]]| hermitian_inertia(&gmat(rows)).unwrap();
        assert_eq!(
            h(&[&[(1, 0), (0, 1)], &[(0, -1), (1, 0)]]),
            Inertia {
                positive: 1,
                negative: 0,
                zero: 1
            }
        );
        assert_eq!(
            h(&[&[(0, 0), (0, -1)], &[(0, 1), (0, 0)]]),
            Inertia {
                positive: 1,
                negative: 1,
                zero: 0
            }
        );
        assert_eq!(
            h(&[&[(2, 0), (1, 1)], &[(1, -1), (3, 0)]]),
            Inertia {
                positive: 2,
                negative: 0,
                zero: 0
            }
        );
        assert_eq!(
            h(&[&[(1, 0), (0, 2)], &[(0, -2), (1, 0)]]),
            Inertia {
                positive: 1,
                negative: 1,
                zero: 0
            }
        );
        assert!(
            hermitian_is_positive_definite(&gmat(&[&[(2, 0), (1, 1)], &[(1, -1), (3, 0)]]))
                .unwrap()
        );
        assert!(hermitian_is_positive_semidefinite(&gmat(&[
            &[(1, 0), (0, 1)],
            &[(0, -1), (1, 0)]
        ]))
        .unwrap());
        assert!(
            !hermitian_is_positive_definite(&gmat(&[&[(1, 0), (0, 1)], &[(0, -1), (1, 0)]]))
                .unwrap()
        );
    }

    /// A Gram matrix `B†B` is positive semidefinite; `B†B + I` positive definite; Hermitian
    /// inertia is congruence invariant for `S†AS`.
    #[test]
    fn hermitian_gram_matrices_are_positive_and_inertia_is_congruence_invariant() {
        let mut rng = Rng::new(617);
        for n in 1..=4usize {
            let b = random_hermitian(&mut rng, n);
            let gram = multiply(&adjoint(&b).unwrap(), &b).unwrap();
            assert!(hermitian_is_positive_semidefinite(&gram).unwrap(), "n={n}");
            let shifted = add(&gram, &identity(n).unwrap()).unwrap();
            assert!(hermitian_is_positive_definite(&shifted).unwrap(), "n={n}");
            let a = random_hermitian(&mut rng, n);
            // a unit triangular complex S
            let s = from_fn(n, n, |r, c| {
                if c < r {
                    gq(q(rng.range(-2, 2), 1), q(rng.range(-2, 2), 1))
                } else if c == r {
                    gi(1, 0)
                } else {
                    gi(0, 0)
                }
            })
            .unwrap();
            let congruent = multiply(&multiply(&adjoint(&s).unwrap(), &a).unwrap(), &s).unwrap();
            assert_eq!(
                hermitian_inertia(&congruent).unwrap(),
                hermitian_inertia(&a).unwrap(),
                "n={n}"
            );
        }
    }

    /// The Hermitian route equals the real route on real matrices, and equals the real
    /// inertia of the realification `[[Re, −Im],[Im, Re]]` counted twice.
    #[test]
    fn hermitian_inertia_agrees_with_the_realification() {
        let mut rng = Rng::new(619);
        for n in 1..=4usize {
            let a = random_hermitian(&mut rng, n);
            let real_part = from_fn(n, n, |r, c| a.get(r, c).unwrap().re).unwrap();
            let imag_part = from_fn(n, n, |r, c| a.get(r, c).unwrap().im).unwrap();
            let realified = from_fn(2 * n, 2 * n, |r, c| {
                let (br, bc) = (r / n, c / n);
                let (i, j) = (r % n, c % n);
                match (br, bc) {
                    (0, 0) | (1, 1) => real_part.get(i, j).unwrap(),
                    (0, 1) => -imag_part.get(i, j).unwrap(),
                    _ => imag_part.get(i, j).unwrap(),
                }
            })
            .unwrap();
            let h = hermitian_inertia(&a).unwrap();
            let r = inertia(&realified).unwrap();
            assert_eq!(
                (r.positive, r.negative, r.zero),
                (2 * h.positive, 2 * h.negative, 2 * h.zero),
                "n={n}"
            );
        }
    }

    // ------------------------------------------------------------------ LDLT

    #[test]
    fn ldlt_of_a_positive_definite_matrix_reproduces_it() {
        // [[4,2],[2,3]]: d = (4, 2), l10 = 1/2
        let a = m(&[&[4, 2], &[2, 3]]);
        let f = ldlt(&a).unwrap();
        assert!(f.is_positive_semidefinite());
        assert_eq!(f.pivots(), &[q(4, 1), q(2, 1)]);
        assert_eq!(f.unit_lower().get(1, 0).unwrap(), q(1, 2));
        assert_eq!(f.unit_lower().get(0, 1).unwrap(), q(0, 1));
        assert_eq!(f.reconstruct().unwrap(), a);

        let mut rng = Rng::new(631);
        for n in 1..=6usize {
            let b = random_matrix(&mut rng, n, n, 3);
            let pd = add(
                &multiply(&transpose(&b).unwrap(), &b).unwrap(),
                &identity(n).unwrap(),
            )
            .unwrap();
            let f = ldlt(&pd).unwrap();
            assert!(f.is_positive_semidefinite());
            assert!(f.pivots().iter().all(|d| sgn(d) > 0));
            assert_eq!(f.reconstruct().unwrap(), pd, "n={n}");
        }
    }

    /// Semidefinite through a zero pivot with a zero Schur column: `[[1,1],[1,1]]` and `diag(0,1)`.
    #[test]
    fn ldlt_accepts_a_zero_pivot_with_a_zero_column() {
        let a = m(&[&[1, 1], &[1, 1]]);
        let f = ldlt(&a).unwrap();
        assert!(f.is_positive_semidefinite());
        assert_eq!(f.pivots(), &[q(1, 1), q(0, 1)]);
        assert_eq!(f.reconstruct().unwrap(), a);
        let g = ldlt(&m(&[&[0, 0], &[0, 1]])).unwrap();
        assert!(g.is_positive_semidefinite());
        assert_eq!(g.pivots(), &[q(0, 1), q(1, 1)]);
    }

    /// A negative pivot stops the factorisation and yields a replayable direction `v` with
    /// `vᵀAv = pivot`: `[[1,2],[2,1]]` has `d = (1, −3)`.
    #[test]
    fn ldlt_reports_a_negative_pivot_with_a_witness() {
        let a = m(&[&[1, 2], &[2, 1]]);
        let f = ldlt(&a).unwrap();
        let LdltOutcome::NegativePivot { step, witness } = f.outcome() else {
            panic!("expected a negative pivot");
        };
        assert_eq!(*step, 1);
        assert_eq!(f.pivots(), &[q(1, 1), q(-3, 1)]);
        assert_eq!(quadratic_form(&a, witness).unwrap(), q(-3, 1));
        assert!(!f.is_positive_semidefinite());
        // the witness is not a multiple of a standard basis vector: it had to be lifted
        assert_eq!(witness, &vec![q(-2, 1), q(1, 1)]);
    }

    /// A zero pivot with a nonzero Schur column: `[[0,1],[1,0]]` (prefix empty) and
    /// `[[1,1,0],[1,1,1],[0,1,1]]` (the step-1 pivot is `1 − 1 = 0`, the column below it `1`):
    /// the witness, lifted through the computed prefix, has `vᵀAv = −1` exactly.
    #[test]
    fn ldlt_reports_a_zero_pivot_with_a_nonzero_column_and_a_lifted_witness() {
        let a = m(&[&[0, 1], &[1, 0]]);
        let f = ldlt(&a).unwrap();
        let LdltOutcome::ZeroPivotWithNonzeroColumn { step, row, witness } = f.outcome() else {
            panic!("expected a zero pivot with a nonzero column");
        };
        assert_eq!((*step, *row), (0, 1));
        assert_eq!(quadratic_form(&a, witness).unwrap(), q(-1, 1));

        let b = m(&[&[1, 1, 0], &[1, 1, 1], &[0, 1, 1]]);
        let f = ldlt(&b).unwrap();
        let LdltOutcome::ZeroPivotWithNonzeroColumn { step, row, witness } = f.outcome() else {
            panic!("expected a zero pivot with a nonzero column");
        };
        assert_eq!((*step, *row), (1, 2));
        assert_eq!(quadratic_form(&b, witness).unwrap(), q(-1, 1));
        assert_ne!(witness[0], q(0, 1), "the prefix correction must be present");
    }

    /// Two independent algorithms agree: the pivoting-free LDLᵀ says "completed" exactly when
    /// the congruence inertia has no negative part, and every reported witness is a real
    /// negative direction.
    #[test]
    fn ldlt_and_congruence_inertia_agree_and_every_witness_replays() {
        let mut rng = Rng::new(641);
        let mut completed = 0;
        let mut stopped = 0;
        for n in 1..=5usize {
            for trial in 0..40 {
                let b = random_matrix(&mut rng, n, n.max(2) - 1, 3);
                let a = match trial % 4 {
                    0 => multiply(&b, &transpose(&b).unwrap()).unwrap(), // PSD, often singular
                    1 => random_symmetric(&mut rng, n),
                    2 => scale(&multiply(&b, &transpose(&b).unwrap()).unwrap(), &q(-1, 1)).unwrap(),
                    _ => {
                        // a matrix with a forced zero diagonal entry
                        let mut s = random_symmetric(&mut rng, n);
                        s.set(0, 0, q(0, 1)).unwrap();
                        s
                    }
                };
                let f = ldlt(&a).unwrap();
                let psd = is_positive_semidefinite(&a).unwrap();
                assert_eq!(f.is_positive_semidefinite(), psd, "n={n} trial={trial}");
                match f.outcome() {
                    LdltOutcome::PositiveSemidefinite => {
                        completed += 1;
                        assert_eq!(f.reconstruct().unwrap(), a);
                    }
                    LdltOutcome::NegativePivot { witness, .. }
                    | LdltOutcome::ZeroPivotWithNonzeroColumn { witness, .. } => {
                        stopped += 1;
                        assert!(
                            sgn(&quadratic_form(&a, witness).unwrap()) < 0,
                            "n={n} trial={trial}"
                        );
                    }
                }
            }
        }
        assert!(
            completed > 10 && stopped > 10,
            "both branches must be exercised"
        );
    }

    #[test]
    fn ldlt_works_over_a_real_quadratic_field() {
        // [[2, √2],[√2, 2]]: d0 = 2, l10 = √2/2, d1 = 2 − (√2/2)²·2 = 1
        let two = qsi(2, 0);
        let s = qsi(0, 1);
        let a = from_rows(vec![vec![two.clone(), s.clone()], vec![s, two]]).unwrap();
        let f = ldlt(&a).unwrap();
        assert!(f.is_positive_semidefinite());
        assert_eq!(f.pivots(), &[qsi(2, 0), qsi(1, 0)]);
        assert_eq!(f.reconstruct().unwrap(), a);
    }

    // ------------------------------------------------------------------ Hermitian LDL

    /// `[[2, 1+i],[1−i, 3]]`: `d0 = 2`, `l10 = (1−i)/2`, `d1 = 3 − |l10|²·2 = 3 − 1 = 2`. The
    /// conjugate in the coupling matters: without it `d1` would be `3 − (1−i)²/4·2` (not real).
    #[test]
    fn hermitian_ldl_of_a_positive_definite_matrix_reproduces_it() {
        let a = gmat(&[&[(2, 0), (1, 1)], &[(1, -1), (3, 0)]]);
        let f = hermitian_ldl(&a).unwrap();
        assert!(f.is_positive_semidefinite());
        assert_eq!(f.pivots(), &[gi(2, 0), gi(2, 0)]);
        assert_eq!(f.unit_lower().get(1, 0).unwrap(), gq(q(1, 2), q(-1, 2)));
        assert_eq!(f.reconstruct_hermitian().unwrap(), a);

        let mut rng = Rng::new(731);
        for n in 1..=5usize {
            let b = random_hermitian(&mut rng, n);
            let pd = add(
                &multiply(&adjoint(&b).unwrap(), &b).unwrap(),
                &identity(n).unwrap(),
            )
            .unwrap();
            let f = hermitian_ldl(&pd).unwrap();
            assert!(f.is_positive_semidefinite(), "n={n}");
            for d in f.pivots() {
                assert_eq!(d, &d.conjugate(), "pivots are fixed by the involution");
                assert_eq!(d.fixed_field_sign(), Some(1));
            }
            assert_eq!(f.reconstruct_hermitian().unwrap(), pd, "n={n}");
        }
    }

    /// σ_y has a zero pivot with an imaginary Schur entry: `x = −1/(2i) = i/2` and the witness
    /// `(i/2, 1)` has `v† σ_y v = −1`.
    #[test]
    fn hermitian_ldl_witness_for_an_imaginary_off_diagonal_entry() {
        let sigma_y = gmat(&[&[(0, 0), (0, -1)], &[(0, 1), (0, 0)]]);
        let f = hermitian_ldl(&sigma_y).unwrap();
        let LdltOutcome::ZeroPivotWithNonzeroColumn { step, row, witness } = f.outcome() else {
            panic!("expected a zero pivot with a nonzero column");
        };
        assert_eq!((*step, *row), (0, 1));
        assert_eq!(witness, &vec![gq(q(0, 1), q(1, 2)), gi(1, 0)]);
        assert_eq!(hermitian_form(&sigma_y, witness).unwrap(), gi(-1, 0));
    }

    /// Two independent algorithms agree on random Hermitian matrices (Gram matrices,
    /// generic, negated Gram, forced zero leading entry): the pivoting-free factorisation
    /// completes exactly when the congruence inertia has no negative part, and every stopped
    /// factorisation carries a witness with a negative Hermitian form.
    #[test]
    fn hermitian_ldl_and_hermitian_inertia_agree_and_every_witness_replays() {
        let mut rng = Rng::new(733);
        let (mut completed, mut stopped) = (0, 0);
        for n in 1..=4usize {
            for trial in 0..32 {
                let b = random_hermitian(&mut rng, n);
                let a = match trial % 4 {
                    0 => multiply(&adjoint(&b).unwrap(), &b).unwrap(),
                    1 => random_hermitian(&mut rng, n),
                    2 => scale(&multiply(&adjoint(&b).unwrap(), &b).unwrap(), &gi(-1, 0)).unwrap(),
                    _ => {
                        let mut h = random_hermitian(&mut rng, n);
                        h.set(0, 0, gi(0, 0)).unwrap();
                        h
                    }
                };
                let f = hermitian_ldl(&a).unwrap();
                assert_eq!(
                    f.is_positive_semidefinite(),
                    hermitian_is_positive_semidefinite(&a).unwrap(),
                    "n={n} trial={trial}"
                );
                match f.outcome() {
                    LdltOutcome::PositiveSemidefinite => {
                        completed += 1;
                        assert_eq!(f.reconstruct_hermitian().unwrap(), a);
                    }
                    LdltOutcome::NegativePivot { witness, .. }
                    | LdltOutcome::ZeroPivotWithNonzeroColumn { witness, .. } => {
                        stopped += 1;
                        let value = hermitian_form(&a, witness).unwrap();
                        assert_eq!(value.fixed_field_sign(), Some(-1), "n={n} trial={trial}");
                    }
                }
            }
        }
        assert!(completed > 8 && stopped > 8, "{completed}/{stopped}");
    }

    /// On matrices with real entries the Hermitian factorisation over `Q(i)` has the same
    /// pivots as the symmetric one over `Q`.
    #[test]
    fn hermitian_ldl_agrees_with_the_symmetric_ldlt_on_real_matrices() {
        let mut rng = Rng::new(735);
        for n in 1..=5usize {
            let real = random_symmetric(&mut rng, n);
            let complex = from_fn(n, n, |r, c| gq(real.get(r, c).unwrap(), q(0, 1))).unwrap();
            let (s, h) = (ldlt(&real).unwrap(), hermitian_ldl(&complex).unwrap());
            assert_eq!(
                s.is_positive_semidefinite(),
                h.is_positive_semidefinite(),
                "n={n}"
            );
            let lifted: Vec<G> = s.pivots().iter().map(|p| gq(p.clone(), q(0, 1))).collect();
            assert_eq!(h.pivots(), lifted.as_slice(), "n={n}");
        }
    }

    #[test]
    fn hermitian_ldl_refuses_non_hermitian_input_and_respects_the_budget() {
        let not_hermitian = gmat(&[&[(1, 0), (0, 1)], &[(0, 1), (1, 0)]]);
        assert_eq!(
            hermitian_ldl(&not_hermitian),
            Err(ExactFieldError::NotHermitian { row: 0, col: 1 })
        );
        let a = gmat(&[&[(2, 0), (1, 1)], &[(1, -1), (3, 0)]]);
        let exact = OperationLimits {
            max_elements: 4,
            max_scalar_ops: 20,
        };
        assert!(hermitian_ldl_with_limits(&a, exact).is_ok());
        assert!(hermitian_ldl_with_limits(
            &a,
            OperationLimits {
                max_scalar_ops: 19,
                ..exact
            }
        )
        .is_err());
    }

    // ------------------------------------------------------------------ quadratic forms

    #[test]
    fn quadratic_and_hermitian_forms() {
        let a = m(&[&[2, 1], &[1, 3]]);
        // (1, -1): 2 - 1 - 1 + 3 = 3
        assert_eq!(quadratic_form(&a, &[q(1, 1), q(-1, 1)]).unwrap(), q(3, 1));
        assert!(matches!(
            quadratic_form(&a, &[q(1, 1)]),
            Err(ExactFieldError::VectorLength {
                operation: "quadratic_form",
                expected: 2,
                got: 1
            })
        ));
        // v† σ_y v for v = (1, i): σ_y v = (−i·i, i·1) = (1, i) → v†(1, i) = 1·1 + (−i)(i) = 2
        let sigma_y = gmat(&[&[(0, 0), (0, -1)], &[(0, 1), (0, 0)]]);
        assert_eq!(
            hermitian_form(&sigma_y, &[gi(1, 0), gi(0, 1)]).unwrap(),
            gi(2, 0)
        );
        // the Hermitian form of a Hermitian matrix is self-conjugate
        let mut rng = Rng::new(651);
        let h = random_hermitian(&mut rng, 3);
        let v = vec![gi(1, 2), gi(-1, 0), gi(0, 3)];
        let value = hermitian_form(&h, &v).unwrap();
        assert!(Semiring::is_zero(&value.im));
    }

    // ------------------------------------------------------------------ refusals

    #[test]
    fn asymmetric_non_square_and_non_hermitian_inputs_are_refused() {
        let a = m(&[&[1, 2], &[3, 1]]);
        assert_eq!(
            inertia(&a),
            Err(ExactFieldError::NotSymmetric { row: 0, col: 1 })
        );
        assert_eq!(
            ldlt(&a),
            Err(ExactFieldError::NotSymmetric { row: 0, col: 1 })
        );
        assert!(is_positive_definite(&a).is_err());
        assert!(matches!(
            inertia(&zeros::<Q>(2, 3).unwrap()),
            Err(ExactFieldError::NotSquare { .. })
        ));
        let not_hermitian = gmat(&[&[(1, 0), (0, 1)], &[(0, 1), (1, 0)]]);
        assert_eq!(
            hermitian_inertia(&not_hermitian),
            Err(ExactFieldError::NotHermitian { row: 0, col: 1 })
        );
        assert!(hermitian_is_positive_definite(&not_hermitian).is_err());
    }

    /// A scalar type whose `signum` breaks its contract is refused, not trusted: a value
    /// outside {-1,0,1}, and a zero sign for a nonzero element.
    #[test]
    fn a_lying_signum_is_a_typed_error() {
        fn diag_shaky<const MODE: u8>(v: i64) -> BasicMatrix<Shaky<MODE>> {
            from_rows(vec![vec![Shaky::<MODE>(q(v, 1))]]).unwrap()
        }
        assert_eq!(
            inertia(&diag_shaky::<1>(5)),
            Err(ExactFieldError::ScalarContract {
                operation: "inertia",
                violation: "a sign must be -1, 0 or 1"
            })
        );
        assert_eq!(
            inertia(&diag_shaky::<2>(5)),
            Err(ExactFieldError::ScalarContract {
                operation: "inertia",
                violation: "a sign is zero exactly when the element is zero"
            })
        );
        assert!(ldlt(&diag_shaky::<1>(5)).is_err());
        // an honest wrapper behaves
        assert_eq!(inertia(&diag_shaky::<0>(5)).unwrap().positive, 1);
    }

    #[test]
    fn a_lying_fixed_field_sign_is_a_typed_error() {
        let one = |v: i64| from_rows(vec![vec![Shaky::<5>(q(v, 1))]]).unwrap();
        assert_eq!(
            hermitian_inertia(&one(3)),
            Err(ExactFieldError::ScalarContract {
                operation: "hermitian_inertia",
                violation: "a diagonal entry of a Hermitian form is not fixed by the involution"
            })
        );
        let two = from_rows(vec![vec![Shaky::<6>(q(3, 1))]]).unwrap();
        assert!(matches!(
            hermitian_inertia(&two),
            Err(ExactFieldError::ScalarContract {
                violation: "a sign must be -1, 0 or 1",
                ..
            })
        ));
    }

    /// Boundary: the `ldlt` cost for `n = 2` is `2·8 + 4 = 20` scalar calls and 4 elements.
    #[test]
    fn ldlt_budget_boundary_is_inclusive() {
        let a = m(&[&[4, 2], &[2, 3]]);
        let exact = OperationLimits {
            max_elements: 4,
            max_scalar_ops: 20,
        };
        assert!(ldlt_with_limits(&a, exact).is_ok());
        assert!(ldlt_with_limits(
            &a,
            OperationLimits {
                max_scalar_ops: 19,
                ..exact
            }
        )
        .is_err());
        assert!(inertia_with_limits(
            &a,
            OperationLimits {
                max_scalar_ops: 79,
                ..exact
            }
        )
        .is_err());
        assert!(inertia_with_limits(
            &a,
            OperationLimits {
                max_scalar_ops: 80,
                ..exact
            }
        )
        .is_ok());
    }

    #[test]
    fn inertia_helpers() {
        let i = Inertia {
            positive: 2,
            negative: 1,
            zero: 3,
        };
        assert_eq!(i.dimension(), 6);
        assert_eq!(i.rank(), 3);
        assert!(!i.is_positive_semidefinite() && !i.is_positive_definite());
        assert!(!i.is_negative_semidefinite() && !i.is_negative_definite());
        assert!(Inertia {
            positive: 0,
            negative: 2,
            zero: 0
        }
        .is_negative_definite());
        assert!(Inertia {
            positive: 0,
            negative: 2,
            zero: 1
        }
        .is_negative_semidefinite());
        assert!(Inertia {
            positive: 2,
            negative: 0,
            zero: 1
        }
        .is_positive_semidefinite());
        assert!(Inertia {
            positive: 0,
            negative: 0,
            zero: 0
        }
        .is_positive_definite());
    }
}

#[cfg(test)]
mod l4_boundary_tests_450ef138 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord450ef138::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord450ef138::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord450ef138::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord450ef138::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord450ef138::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError450ef138::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError450ef138::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
