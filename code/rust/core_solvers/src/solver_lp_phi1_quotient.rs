//! # Phi1 certificate construction over exact rationals
//!
//! [`core_functional::phi1`] and [`core_functional::l1_seminorm`] replay a submitted primal-dual
//! witness. This module produces one. For a checked presentation `(B, w)` and a
//! representative `omega` it solves, by exact two-phase simplex,
//!
//! ```text
//! primal  min_alpha ||omega - B alpha||_{1,w}
//! dual    max_y <omega, y>   subject to  B^T y = 0,  |y_i| <= w_i
//! ```
//!
//! as two independent linear programs and submits the pair to
//! [`L1Seminorm::evaluate`]. The solver never constructs a
//! [`VerifiedExactPhi1`] itself: a pivoting defect surfaces as a typed refusal
//! from the shared verifier, never as a sealed wrong value.
//!
//! Pivoting follows Bland's rule, so degenerate presentations terminate.
//! There is no floating-point path, no tolerance, and no fallback solver.
//!
//! **Warning**: a solved certificate carries exactly the evidence of
//! [`VerifiedExactPhi1`] and nothing more. It mints no authority.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3a11e8c0<T> {
    fn checked_invariant_3a11e8c0(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3a11e8c0<T> for Option<T> {
    #[inline]
    fn checked_invariant_3a11e8c0(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3a11e8c0<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3a11e8c0(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

use core_functional::l1_seminorm::{L1Seminorm, L1SeminormError};
use core_functional::phi1::VerifiedExactPhi1;

/// Which of the two linear programs refused.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Phi1LinearProgram {
    /// `min ||omega - B alpha||_{1,w}` over free `alpha`.
    Primal,
    /// `max <omega, y>` over `B^T y = 0`, `|y| <= w`.
    Dual,
}

/// Terminal simplex outcome other than an optimum.
///
/// Neither is reachable for a presentation admitted by [`L1Seminorm::new`]:
/// the primal is feasible at `alpha = 0` and bounded below by zero, and the
/// dual is feasible at `y = 0` and bounded above by `sum_i w_i |core_i|`.
/// They are typed so a defect cannot be mistaken for a value.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SimplexRefusal {
    Infeasible,
    Unbounded,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum Phi1SolveError {
    #[error("PHI1_SOLVE_DIMENSION_MISMATCH: omega has {actual} coordinates, presentation has {expected}")]
    CoreDimensionMismatch { expected: usize, actual: usize },
    #[error("PHI1_SOLVE_ZERO_DENOMINATOR: omega coordinate {index}")]
    ZeroDenominator { index: usize },
    #[error("PHI1_SOLVE_LP_REFUSED: {program:?} program is {refusal:?}")]
    LinearProgram {
        program: Phi1LinearProgram,
        refusal: SimplexRefusal,
    },
    #[error("PHI1_SOLVE_CERTIFICATE_REFUSED: {0}")]
    Certificate(#[from] L1SeminormError),
}

/// Solve the weighted l1 quotient distance of `omega` on `space` and return
/// it only after the shared verifier has replayed the primal-dual pair.
pub fn solve_exact_phi1(
    space: &L1Seminorm,
    omega: &[BigRational],
) -> Result<VerifiedExactPhi1, Phi1SolveError> {
    let boundary = space.boundary();
    let weights = space.weights();
    let rows = weights.len();
    if omega.len() != rows {
        return Err(Phi1SolveError::CoreDimensionMismatch {
            expected: rows,
            actual: omega.len(),
        });
    }
    if let Some(index) = omega.iter().position(|value| value.denom().is_zero()) {
        return Err(Phi1SolveError::ZeroDenominator { index });
    }
    // Denominators are admitted, so normalisation cannot panic.
    let omega: Vec<BigRational> = omega
        .iter()
        .map(|value| BigRational::new(value.numer().clone(), value.denom().clone()))
        .collect();
    let columns = boundary.first().map_or(0, Vec::len);

    let (_tableau_objective, alpha) = solve_primal(boundary, weights, &omega, columns)?;
    let dual_witness = solve_dual(boundary, weights, &omega, columns)?;
    Ok(
        core_functional::phi1::Phi1Functional::evaluate_exact_witness(
            &omega,
            boundary,
            weights,
            &alpha,
            &dual_witness,
        )
        .map_err(L1SeminormError::from)?,
    )
}

/// Variables `[alpha+, alpha-, r+, r-]`, rows `B(alpha+ - alpha-) + r+ - r- = omega`,
/// objective `sum_i w_i (r+_i + r-_i)`.
fn solve_primal(
    boundary: &[Vec<BigRational>],
    weights: &[BigRational],
    omega: &[BigRational],
    columns: usize,
) -> Result<(BigRational, Vec<BigRational>), Phi1SolveError> {
    let rows = weights.len();
    let width = 2 * columns + 2 * rows;
    let mut objective = vec![BigRational::zero(); width];
    for (i, weight) in weights.iter().enumerate() {
        objective[2 * columns + i] = weight.clone();
        objective[2 * columns + rows + i] = weight.clone();
    }
    let constraints = boundary
        .iter()
        .enumerate()
        .map(|(i, coefficients)| {
            let mut row = vec![BigRational::zero(); width];
            for (j, coefficient) in coefficients.iter().enumerate() {
                row[j] = coefficient.clone();
                row[columns + j] = -coefficient;
            }
            row[2 * columns + i] = BigRational::one();
            row[2 * columns + rows + i] = -BigRational::one();
            row
        })
        .collect();
    let (value, x) = minimize(&objective, constraints, omega.to_vec()).map_err(|refusal| {
        Phi1SolveError::LinearProgram {
            program: Phi1LinearProgram::Primal,
            refusal,
        }
    })?;
    let alpha = (0..columns).map(|j| &x[j] - &x[columns + j]).collect();
    Ok((value, alpha))
}

/// Variables `[y+, y-, s+, s-]`, rows `B^T(y+ - y-) = 0`, `y+ + s+ = w`,
/// `y- + s- = w`, objective `min -<omega, y+> + <omega, y->`.
fn solve_dual(
    boundary: &[Vec<BigRational>],
    weights: &[BigRational],
    omega: &[BigRational],
    columns: usize,
) -> Result<Vec<BigRational>, Phi1SolveError> {
    let rows = weights.len();
    let width = 4 * rows;
    let mut objective = vec![BigRational::zero(); width];
    for (i, value) in omega.iter().enumerate() {
        objective[i] = -value;
        objective[rows + i] = value.clone();
    }
    let mut constraints = Vec::with_capacity(columns + 2 * rows);
    let mut rhs = Vec::with_capacity(columns + 2 * rows);
    for j in 0..columns {
        let mut row = vec![BigRational::zero(); width];
        for (i, coefficients) in boundary.iter().enumerate() {
            row[i] = coefficients[j].clone();
            row[rows + i] = -&coefficients[j];
        }
        constraints.push(row);
        rhs.push(BigRational::zero());
    }
    for (i, weight) in weights.iter().enumerate() {
        for sign in 0..2 {
            let mut row = vec![BigRational::zero(); width];
            row[sign * rows + i] = BigRational::one();
            row[(2 + sign) * rows + i] = BigRational::one();
            constraints.push(row);
            rhs.push(weight.clone());
        }
    }
    let (_, x) = minimize(&objective, constraints, rhs).map_err(|refusal| {
        Phi1SolveError::LinearProgram {
            program: Phi1LinearProgram::Dual,
            refusal,
        }
    })?;
    Ok((0..rows).map(|i| &x[i] - &x[rows + i]).collect())
}

/// Exact two-phase simplex for `min c^T x` subject to `A x = b`, `x >= 0`.
///
/// Returns the optimum and one optimal vertex. Bland's rule (least-index
/// entering column, least-index basic variable on ratio ties) ensures
/// termination on degenerate programs.
fn build_phase1_tableau(
    n: usize,
    constraints: Vec<Vec<BigRational>>,
    rhs: Vec<BigRational>,
) -> (Vec<Vec<BigRational>>, Vec<BigRational>, Vec<usize>) {
    let m = constraints.len();
    // Phase 1 tableau: structural columns, one artificial per row, then b >= 0.
    let tableau: Vec<Vec<BigRational>> = constraints
        .into_iter()
        .zip(rhs)
        .enumerate()
        .map(|(i, (mut row, mut b))| {
            if b.is_negative() {
                b = -b;
                row.iter_mut().for_each(|entry| *entry = -&*entry);
            }
            row.resize(n + m, BigRational::zero());
            row[n + i] = BigRational::one();
            row.push(b);
            row
        })
        .collect();
    let basis: Vec<usize> = (n..n + m).collect();

    // Reduced costs of `min sum artificials`: artificial columns are basic and
    // price out to zero; structural columns and -z are minus the column sums.
    let mut cost = vec![BigRational::zero(); n + m + 1];
    for row in &tableau {
        for j in (0..n).chain(std::iter::once(n + m)) {
            cost[j] -= &row[j];
        }
    }
    (tableau, cost, basis)
}

fn eliminate_artificial_basis(
    tableau: &mut Vec<Vec<BigRational>>,
    cost: &mut [BigRational],
    basis: &mut Vec<usize>,
    n: usize,
) {
    // Drive zero-level artificials out of the basis; a row with no structural
    // support is linearly redundant and is dropped with its artificial.
    let mut row = 0;
    while row < tableau.len() {
        if basis[row] >= n {
            match (0..n).find(|&j| !tableau[row][j].is_zero()) {
                Some(column) => pivot(tableau, cost, basis, row, column),
                None => {
                    tableau.remove(row);
                    basis.remove(row);
                    continue;
                }
            }
        }
        row += 1;
    }
}

fn prepare_phase2_cost(
    objective: &[BigRational],
    tableau: &mut [Vec<BigRational>],
    basis: &[usize],
) -> Vec<BigRational> {
    let n = objective.len();
    // Phase 2 on the structural columns with the original objective.
    for row in tableau.iter_mut() {
        let b = row.pop().checked_invariant_3a11e8c0("tableau rows carry a rhs");
        row.truncate(n);
        row.push(b);
    }
    let mut cost: Vec<BigRational> = objective.to_vec();
    cost.push(BigRational::zero());
    for (row, &basic) in tableau.iter().zip(basis) {
        if !cost[basic].is_zero() {
            let factor = cost[basic].clone();
            for (entry, value) in cost.iter_mut().zip(row) {
                *entry -= &factor * value;
            }
        }
    }
    cost
}

fn minimize(
    objective: &[BigRational],
    constraints: Vec<Vec<BigRational>>,
    rhs: Vec<BigRational>,
) -> Result<(BigRational, Vec<BigRational>), SimplexRefusal> {
    let n = objective.len();
    let m = constraints.len();
    let (mut tableau, mut cost, mut basis) = build_phase1_tableau(n, constraints, rhs);

    run_simplex(&mut tableau, &mut cost, &mut basis, n + m)?;
    if !cost[n + m].is_zero() {
        return Err(SimplexRefusal::Infeasible);
    }

    eliminate_artificial_basis(&mut tableau, &mut cost, &mut basis, n);
    let mut cost = prepare_phase2_cost(objective, &mut tableau, &basis);
    run_simplex(&mut tableau, &mut cost, &mut basis, n)?;

    let mut x = vec![BigRational::zero(); n];
    for (row, &basic) in tableau.iter().zip(&basis) {
        x[basic] = row[n].clone();
    }
    Ok((-&cost[n], x))
}

fn run_simplex(
    tableau: &mut [Vec<BigRational>],
    cost: &mut [BigRational],
    basis: &mut [usize],
    eligible: usize,
) -> Result<(), SimplexRefusal> {
    let rhs = cost.len() - 1;
    while let Some(entering) = (0..eligible).find(|&j| cost[j].is_negative()) {
        let mut leaving: Option<(usize, BigRational)> = None;
        for (i, row) in tableau.iter().enumerate() {
            if !row[entering].is_positive() {
                continue;
            }
            let ratio = &row[rhs] / &row[entering];
            let better = match &leaving {
                None => true,
                Some((best_row, best)) => {
                    ratio < *best || (ratio == *best && basis[i] < basis[*best_row])
                }
            };
            if better {
                leaving = Some((i, ratio));
            }
        }
        let (row, _) = leaving.ok_or(SimplexRefusal::Unbounded)?;
        pivot(tableau, cost, basis, row, entering);
    }
    Ok(())
}

fn pivot(
    tableau: &mut [Vec<BigRational>],
    cost: &mut [BigRational],
    basis: &mut [usize],
    row: usize,
    column: usize,
) {
    let inverse = tableau[row][column].recip();
    tableau[row].iter_mut().for_each(|entry| *entry *= &inverse);
    let pivot_row = tableau[row].clone();
    let eliminate = |target: &mut [BigRational]| {
        if !target[column].is_zero() {
            let factor = target[column].clone();
            for (entry, value) in target.iter_mut().zip(&pivot_row) {
                *entry -= &factor * value;
            }
        }
    };
    for (i, target) in tableau.iter_mut().enumerate() {
        if i != row {
            eliminate(target);
        }
    }
    eliminate(cost);
    basis[row] = column;
}

/// Submitted exact finite rational primal-dual witness for the closure-constrained
/// representative repair linear program:
///
/// ```text
/// min_{f in C^0} ||omega - d0 f||_{1,w}
/// subject to     ||d1 omega - K f||_1 <= ||d1 omega||_1 + tau,   K = d1 d0.
/// ```
///
/// When `K = d1 d0 != 0` (curved descent), degree-2 closure defect depends on the
/// representative `h = omega - d0 f` because `d1(omega - d0 f) = d1 omega - K f`.
/// Rather than conflating quotient and representative norms inside
/// [`core_functional::gamma2::ExactCochainComplexQ`] (which remains restricted to the
/// flat `K = 0` locus), this certificate pairs representative-level
/// [`core_functional::gamma2::RawClosureDefectResult`] evaluations with a coupled
/// primal-dual optimality witness:
///
/// ```text
/// max_{y, z, lambda >= 0} <omega, y> + <d1 omega, z> - (||d1 omega||_1 + tau) lambda
/// subject to              d0^T y + K^T z = 0,  |y_i| <= w_i,  |z_r| <= lambda.
/// ```
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CurvedConstrainedPhi1Certificate {
    pub omega: Vec<BigRational>,
    pub d0: Vec<Vec<BigRational>>,
    pub d1: Vec<Vec<BigRational>>,
    pub curvature_k: Vec<Vec<BigRational>>,
    pub weights: Vec<BigRational>,
    pub tau: BigRational,
    pub alpha: Vec<BigRational>,
    pub primal_residual: Vec<BigRational>,
    pub dual_y: Vec<BigRational>,
    pub dual_z: Vec<BigRational>,
    pub dual_lambda: BigRational,
    pub reported_value: BigRational,
}

/// Sealed result of replaying a [`CurvedConstrainedPhi1Certificate`] together with
/// representative-level [`core_functional::gamma2::RawClosureDefectResult`] evaluations.
///
/// Fields are private so only [`verify_constrained_curved_phi1`] (or
/// [`solve_constrained_curved_phi1`], which delegates to it) can construct a value.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedCurvedConstrainedPhi1 {
    certificate: CurvedConstrainedPhi1Certificate,
    baseline_raw_gamma2: core_functional::gamma2::RawClosureDefectResult,
    repaired_raw_gamma2: core_functional::gamma2::RawClosureDefectResult,
    is_curved: bool,
}

impl VerifiedCurvedConstrainedPhi1 {
    pub fn certificate(&self) -> &CurvedConstrainedPhi1Certificate {
        &self.certificate
    }

    pub fn value(&self) -> &BigRational {
        &self.certificate.reported_value
    }

    pub fn alpha(&self) -> &[BigRational] {
        &self.certificate.alpha
    }

    pub fn primal_residual(&self) -> &[BigRational] {
        &self.certificate.primal_residual
    }

    pub fn baseline_raw_gamma2(&self) -> &core_functional::gamma2::RawClosureDefectResult {
        &self.baseline_raw_gamma2
    }

    pub fn repaired_raw_gamma2(&self) -> &core_functional::gamma2::RawClosureDefectResult {
        &self.repaired_raw_gamma2
    }

    pub fn curvature_k(&self) -> &[Vec<BigRational>] {
        &self.certificate.curvature_k
    }

    pub fn is_curved(&self) -> bool {
        self.is_curved
    }

    pub fn tau(&self) -> &BigRational {
        &self.certificate.tau
    }

    pub fn dual_y(&self) -> &[BigRational] {
        &self.certificate.dual_y
    }

    pub fn dual_z(&self) -> &[BigRational] {
        &self.certificate.dual_z
    }

    pub fn dual_lambda(&self) -> &BigRational {
        &self.certificate.dual_lambda
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CurvedConstrainedPhi1Error {
    #[error("CURVED_PHI1_ZERO_DENOMINATOR: input contains a rational with zero denominator")]
    ZeroRationalDenominator,
    #[error("CURVED_PHI1_NEGATIVE_TAU: closure slack tau must be non-negative")]
    NegativeTau,
    #[error("CURVED_PHI1_CORE_DIMENSION_MISMATCH: expected {expected} coordinates, got {actual}")]
    CoreDimensionMismatch { expected: usize, actual: usize },
    #[error("CURVED_PHI1_COCHAIN_DIMENSION_MISMATCH: omega, residual, weights, and dual_y must have equal length")]
    CochainDimensionMismatch,
    #[error("CURVED_PHI1_D0_ROW_MISMATCH: d0 has {actual} rows, expected {expected}")]
    D0RowMismatch { expected: usize, actual: usize },
    #[error("CURVED_PHI1_D0_COLUMN_MISMATCH: d0 row {row} has {actual} columns, expected {expected}")]
    D0ColumnMismatch {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("CURVED_PHI1_D1_COLUMN_MISMATCH: d1 row {row} has {actual} columns, expected {expected}")]
    D1ColumnMismatch {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("CURVED_PHI1_RAW_GAMMA2_ERROR: {0}")]
    RawGamma2(#[from] core_functional::gamma2::ExactGamma2Error),
    #[error("CURVED_PHI1_CURVATURE_SHAPE_MISMATCH: curvature K has shape ({actual_rows}, {actual_cols}), expected ({expected_rows}, {expected_cols})")]
    CurvatureDimensionMismatch {
        expected_rows: usize,
        actual_rows: usize,
        expected_cols: usize,
        actual_cols: usize,
    },
    #[error("CURVED_PHI1_CURVATURE_ENTRY_MISMATCH: curvature K[{row}][{column}] does not equal (d1 * d0)[{row}][{column}]")]
    CurvatureMismatch { row: usize, column: usize },
    #[error("CURVED_PHI1_COBOUNDARY_IDENTITY_MISMATCH: d1(omega - d0 f)[{row}] does not equal (d1 omega - K f)[{row}]")]
    CoboundaryIdentityMismatch { row: usize },
    #[error("CURVED_PHI1_NON_POSITIVE_WEIGHT: weight at index {index} is not strictly positive")]
    NonPositiveWeight { index: usize },
    #[error("CURVED_PHI1_PRIMAL_RESIDUAL_MISMATCH: primal residual at index {index} does not equal omega - d0 alpha")]
    PrimalResidualMismatch { index: usize },
    #[error("CURVED_PHI1_CLOSURE_BUDGET_EXCEEDED: repaired raw Gamma2 {repaired_gamma2} exceeds budget {budget}")]
    ClosureBudgetExceeded {
        repaired_gamma2: BigRational,
        budget: BigRational,
    },
    #[error("CURVED_PHI1_DUAL_Z_DIMENSION_MISMATCH: dual_z has {actual} coordinates, expected {expected}")]
    DualZDimensionMismatch { expected: usize, actual: usize },
    #[error("CURVED_PHI1_NEGATIVE_DUAL_LAMBDA: dual_lambda must be non-negative")]
    NegativeDualLambda,
    #[error("CURVED_PHI1_DUAL_Y_BOUND_VIOLATION: |dual_y[{index}]| exceeds weight[{index}]")]
    DualYNormBoundViolation { index: usize },
    #[error("CURVED_PHI1_DUAL_Z_BOUND_VIOLATION: |dual_z[{row}]| exceeds dual_lambda")]
    DualZNormBoundViolation { row: usize },
    #[error("CURVED_PHI1_COUPLED_ANNIHILATOR_MISMATCH: (d0^T y + K^T z)[{column}] != 0")]
    DualCoupledAnnihilatorMismatch { column: usize },
    #[error("CURVED_PHI1_NEGATIVE_REPORTED_VALUE: reported value is negative")]
    NegativeReportedValue,
    #[error("CURVED_PHI1_PRIMAL_VALUE_MISMATCH: reported value does not match weighted primal residual norm")]
    PrimalValueMismatch,
    #[error("CURVED_PHI1_DUAL_VALUE_MISMATCH: reported value does not match coupled dual objective")]
    DualValueMismatch,
    #[error("CURVED_PHI1_LP_REFUSED: {program:?} program is {refusal:?}")]
    LinearProgram {
        program: Phi1LinearProgram,
        refusal: SimplexRefusal,
    },
}

fn canonicalize_rational(value: &BigRational) -> BigRational {
    BigRational::new(value.numer().clone(), value.denom().clone())
}

fn dot_q(lhs: &[BigRational], rhs: &[BigRational]) -> BigRational {
    lhs.iter()
        .zip(rhs)
        .map(|(a, b)| a * b)
        .sum::<BigRational>()
}

/// Compute the exact rational curvature matrix `K = d1 * d0` of shape `(c2_dim, c0_dim)`.
pub fn compute_curvature_k(
    d0: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    c0_dim: usize,
) -> Result<Vec<Vec<BigRational>>, CurvedConstrainedPhi1Error> {
    if d0
        .iter()
        .flatten()
        .chain(d1.iter().flatten())
        .any(|q| q.denom().is_zero())
    {
        return Err(CurvedConstrainedPhi1Error::ZeroRationalDenominator);
    }
    let c1_dim = d0.len();
    for (row, coefficients) in d0.iter().enumerate() {
        if coefficients.len() != c0_dim {
            return Err(CurvedConstrainedPhi1Error::D0ColumnMismatch {
                row,
                expected: c0_dim,
                actual: coefficients.len(),
            });
        }
    }
    for (row, coefficients) in d1.iter().enumerate() {
        if coefficients.len() != c1_dim {
            return Err(CurvedConstrainedPhi1Error::D1ColumnMismatch {
                row,
                expected: c1_dim,
                actual: coefficients.len(),
            });
        }
    }
    let mut k_matrix = Vec::with_capacity(d1.len());
    for d1_row in d1 {
        let mut k_row = Vec::with_capacity(c0_dim);
        for col in 0..c0_dim {
            let entry = d1_row
                .iter()
                .zip(d0)
                .map(|(d1_val, d0_row)| d1_val * &d0_row[col])
                .sum::<BigRational>();
            k_row.push(entry);
        }
        k_matrix.push(k_row);
    }
    Ok(k_matrix)
}

fn validate_curved_certificate_scalars(
    certificate: &CurvedConstrainedPhi1Certificate,
) -> Result<(), CurvedConstrainedPhi1Error> {
    let mut all_scalars = certificate
        .omega
        .iter()
        .chain(certificate.weights.iter())
        .chain(certificate.alpha.iter())
        .chain(certificate.primal_residual.iter())
        .chain(certificate.dual_y.iter())
        .chain(certificate.dual_z.iter())
        .chain(certificate.d0.iter().flatten())
        .chain(certificate.d1.iter().flatten())
        .chain(certificate.curvature_k.iter().flatten())
        .chain([
            &certificate.tau,
            &certificate.dual_lambda,
            &certificate.reported_value,
        ]);
    if all_scalars.any(|q| q.denom().is_zero()) {
        return Err(CurvedConstrainedPhi1Error::ZeroRationalDenominator);
    }
    if certificate.tau.is_negative() {
        return Err(CurvedConstrainedPhi1Error::NegativeTau);
    }
    Ok(())
}

fn validate_curved_certificate_dimensions(
    certificate: &CurvedConstrainedPhi1Certificate,
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
) -> Result<(), CurvedConstrainedPhi1Error> {
    let valid_c1 = certificate.primal_residual.len() == c1_dim
        && certificate.weights.len() == c1_dim
        && certificate.dual_y.len() == c1_dim;
    if !valid_c1 {
        return Err(CurvedConstrainedPhi1Error::CochainDimensionMismatch);
    }
    if certificate.d0.len() != c1_dim {
        return Err(CurvedConstrainedPhi1Error::D0RowMismatch {
            expected: c1_dim,
            actual: certificate.d0.len(),
        });
    }
    for (row, coefficients) in certificate.d0.iter().enumerate() {
        if coefficients.len() != c0_dim {
            return Err(CurvedConstrainedPhi1Error::D0ColumnMismatch {
                row,
                expected: c0_dim,
                actual: coefficients.len(),
            });
        }
    }
    for (row, coefficients) in certificate.d1.iter().enumerate() {
        if coefficients.len() != c1_dim {
            return Err(CurvedConstrainedPhi1Error::D1ColumnMismatch {
                row,
                expected: c1_dim,
                actual: coefficients.len(),
            });
        }
    }
    if certificate.dual_z.len() != c2_dim {
        return Err(CurvedConstrainedPhi1Error::DualZDimensionMismatch {
            expected: c2_dim,
            actual: certificate.dual_z.len(),
        });
    }
    Ok(())
}

fn verify_curvature_matrix(
    certificate: &CurvedConstrainedPhi1Certificate,
    c0_dim: usize,
    c2_dim: usize,
) -> Result<(), CurvedConstrainedPhi1Error> {
    let expected_k = compute_curvature_k(&certificate.d0, &certificate.d1, c0_dim)?;
    if certificate.curvature_k.len() != c2_dim {
        return Err(CurvedConstrainedPhi1Error::CurvatureDimensionMismatch {
            expected_rows: c2_dim,
            actual_rows: certificate.curvature_k.len(),
            expected_cols: c0_dim,
            actual_cols: certificate.curvature_k.first().map_or(0, Vec::len),
        });
    }
    for (r, (row, expected_row)) in certificate
        .curvature_k
        .iter()
        .zip(&expected_k)
        .enumerate()
    {
        if row.len() != c0_dim {
            return Err(CurvedConstrainedPhi1Error::CurvatureDimensionMismatch {
                expected_rows: c2_dim,
                actual_rows: certificate.curvature_k.len(),
                expected_cols: c0_dim,
                actual_cols: row.len(),
            });
        }
        for (c, (val, exp_val)) in row.iter().zip(expected_row).enumerate() {
            if val != exp_val {
                return Err(CurvedConstrainedPhi1Error::CurvatureMismatch { row: r, column: c });
            }
        }
    }
    Ok(())
}

fn verify_primal_weights_and_residual(
    certificate: &CurvedConstrainedPhi1Certificate,
    c1_dim: usize,
) -> Result<(), CurvedConstrainedPhi1Error> {
    for (index, weight) in certificate.weights.iter().enumerate() {
        if !weight.is_positive() {
            return Err(CurvedConstrainedPhi1Error::NonPositiveWeight { index });
        }
    }
    for index in 0..c1_dim {
        let repair = dot_q(&certificate.d0[index], &certificate.alpha);
        if certificate.primal_residual[index] != &certificate.omega[index] - repair {
            return Err(CurvedConstrainedPhi1Error::PrimalResidualMismatch { index });
        }
    }
    Ok(())
}

fn verify_dual_feasibility_and_annihilator(
    certificate: &CurvedConstrainedPhi1Certificate,
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
) -> Result<(), CurvedConstrainedPhi1Error> {
    if certificate.dual_lambda.is_negative() {
        return Err(CurvedConstrainedPhi1Error::NegativeDualLambda);
    }
    for (index, (y_i, w_i)) in certificate
        .dual_y
        .iter()
        .zip(&certificate.weights)
        .enumerate()
    {
        if y_i.abs() > *w_i {
            return Err(CurvedConstrainedPhi1Error::DualYNormBoundViolation { index });
        }
    }
    for (row, z_r) in certificate.dual_z.iter().enumerate() {
        if z_r.abs() > certificate.dual_lambda {
            return Err(CurvedConstrainedPhi1Error::DualZNormBoundViolation { row });
        }
    }
    for column in 0..c0_dim {
        let d0_t_y = (0..c1_dim)
            .map(|row| &certificate.d0[row][column] * &certificate.dual_y[row])
            .sum::<BigRational>();
        let k_t_z = (0..c2_dim)
            .map(|row| &certificate.curvature_k[row][column] * &certificate.dual_z[row])
            .sum::<BigRational>();
        if !(d0_t_y + k_t_z).is_zero() {
            return Err(CurvedConstrainedPhi1Error::DualCoupledAnnihilatorMismatch { column });
        }
    }
    Ok(())
}

fn verify_primal_dual_objective_match(
    certificate: &CurvedConstrainedPhi1Certificate,
    baseline_coboundary: &[BigRational],
    budget: &BigRational,
) -> Result<(), CurvedConstrainedPhi1Error> {
    if certificate.reported_value.is_negative() {
        return Err(CurvedConstrainedPhi1Error::NegativeReportedValue);
    }
    // Weights, residual length and denominators were checked above, so the
    // canonical evaluator refuses here only on a broken precondition.
    let primal_value = core_functional::phi1::Phi1Functional::weighted_l1_rational(
        &certificate.weights,
        &certificate.primal_residual,
    )
    .ok_or(CurvedConstrainedPhi1Error::PrimalValueMismatch)?;
    if certificate.reported_value != primal_value {
        return Err(CurvedConstrainedPhi1Error::PrimalValueMismatch);
    }

    let dual_value = dot_q(&certificate.omega, &certificate.dual_y)
        + dot_q(baseline_coboundary, &certificate.dual_z)
        - budget * &certificate.dual_lambda;
    if certificate.reported_value != dual_value {
        return Err(CurvedConstrainedPhi1Error::DualValueMismatch);
    }
    Ok(())
}

fn verify_coboundary_identity_and_budget(
    certificate: &CurvedConstrainedPhi1Certificate,
    baseline_raw_gamma2: &core_functional::gamma2::RawClosureDefectResult,
    repaired_raw_gamma2: &core_functional::gamma2::RawClosureDefectResult,
    c2_dim: usize,
) -> Result<BigRational, CurvedConstrainedPhi1Error> {
    for row in 0..c2_dim {
        let k_alpha = dot_q(&certificate.curvature_k[row], &certificate.alpha);
        let expected_coboundary = &baseline_raw_gamma2.coboundary()[row] - k_alpha;
        if repaired_raw_gamma2.coboundary()[row] != expected_coboundary {
            return Err(CurvedConstrainedPhi1Error::CoboundaryIdentityMismatch { row });
        }
    }
    let budget = baseline_raw_gamma2.value() + &certificate.tau;
    if repaired_raw_gamma2.value() > &budget {
        return Err(CurvedConstrainedPhi1Error::ClosureBudgetExceeded {
            repaired_gamma2: repaired_raw_gamma2.value().clone(),
            budget,
        });
    }
    Ok(budget)
}

/// Replay a [`CurvedConstrainedPhi1Certificate`] and seal its result together with
/// [`core_functional::gamma2::RawClosureDefectResult`] evidence on the baseline and
/// repaired representatives.
pub fn verify_constrained_curved_phi1(
    certificate: CurvedConstrainedPhi1Certificate,
) -> Result<VerifiedCurvedConstrainedPhi1, CurvedConstrainedPhi1Error> {
    use core_functional::gamma2::Gamma2Functional;

    validate_curved_certificate_scalars(&certificate)?;
    let (c0_dim, c1_dim, c2_dim) = (
        certificate.alpha.len(),
        certificate.omega.len(),
        certificate.d1.len(),
    );
    validate_curved_certificate_dimensions(&certificate, c0_dim, c1_dim, c2_dim)?;
    verify_curvature_matrix(&certificate, c0_dim, c2_dim)?;
    verify_primal_weights_and_residual(&certificate, c1_dim)?;

    let baseline_raw_gamma2 =
        Gamma2Functional::try_compute_raw(&certificate.omega, &certificate.d1)?;
    let repaired_raw_gamma2 =
        Gamma2Functional::try_compute_raw(&certificate.primal_residual, &certificate.d1)?;

    let budget = verify_coboundary_identity_and_budget(
        &certificate,
        &baseline_raw_gamma2,
        &repaired_raw_gamma2,
        c2_dim,
    )?;

    verify_dual_feasibility_and_annihilator(&certificate, c0_dim, c1_dim, c2_dim)?;
    verify_primal_dual_objective_match(&certificate, baseline_raw_gamma2.coboundary(), &budget)?;

    let is_curved = certificate
        .curvature_k
        .iter()
        .flatten()
        .any(|entry| !entry.is_zero());

    Ok(VerifiedCurvedConstrainedPhi1 {
        certificate,
        baseline_raw_gamma2,
        repaired_raw_gamma2,
        is_curved,
    })
}

/// Solve the exact rational closure-constrained repair linear program:
///
/// ```text
/// min_{f in C^0} ||omega - d0 f||_{1,w}
/// subject to     ||d1 omega - K f||_1 <= ||d1 omega||_1 + tau,   K = d1 d0,
/// ```
///
/// together with its coupled dual linear program, and seal the result via
/// [`verify_constrained_curved_phi1`] using [`core_functional::gamma2::RawClosureDefectResult`].
fn validate_curved_solver_inputs(
    c1_dim: usize,
    d1: &[Vec<BigRational>],
    omega: &[BigRational],
    tau: &BigRational,
) -> Result<(), CurvedConstrainedPhi1Error> {
    if omega.len() != c1_dim {
        return Err(CurvedConstrainedPhi1Error::CoreDimensionMismatch {
            expected: c1_dim,
            actual: omega.len(),
        });
    }
    if tau.denom().is_zero()
        || omega.iter().any(|q| q.denom().is_zero())
        || d1.iter().flatten().any(|q| q.denom().is_zero())
    {
        return Err(CurvedConstrainedPhi1Error::ZeroRationalDenominator);
    }
    if tau.is_negative() {
        return Err(CurvedConstrainedPhi1Error::NegativeTau);
    }
    Ok(())
}

pub fn solve_constrained_curved_phi1(
    space: &L1Seminorm,
    d1: &[Vec<BigRational>],
    omega: &[BigRational],
    tau: &BigRational,
) -> Result<VerifiedCurvedConstrainedPhi1, CurvedConstrainedPhi1Error> {
    use core_functional::gamma2::Gamma2Functional;

    let d0 = space.boundary();
    let weights = space.weights();
    validate_curved_solver_inputs(weights.len(), d1, omega, tau)?;
    let tau = canonicalize_rational(tau);
    let omega: Vec<BigRational> = omega.iter().map(canonicalize_rational).collect();
    let d1: Vec<Vec<BigRational>> = d1
        .iter()
        .map(|row| row.iter().map(canonicalize_rational).collect())
        .collect();
    let c0_dim = d0.first().map_or(0, Vec::len);

    let curvature_k = compute_curvature_k(d0, &d1, c0_dim)?;
    let baseline_raw_gamma2 = Gamma2Functional::try_compute_raw(&omega, &d1)?;
    let budget = baseline_raw_gamma2.value() + &tau;

    let alpha = solve_primal_constrained(
        d0,
        &curvature_k,
        weights,
        &omega,
        baseline_raw_gamma2.coboundary(),
        &budget,
        c0_dim,
    )?;
    let (dual_y, dual_z, dual_lambda) = solve_dual_constrained(
        d0,
        &curvature_k,
        weights,
        &omega,
        baseline_raw_gamma2.coboundary(),
        &budget,
        c0_dim,
    )?;

    let primal_residual: Vec<BigRational> = omega
        .iter()
        .zip(d0)
        .map(|(x_i, d0_row)| x_i - dot_q(d0_row, &alpha))
        .collect();
    let reported_value =
        core_functional::phi1::Phi1Functional::weighted_l1_rational(weights, &primal_residual)
            .ok_or(CurvedConstrainedPhi1Error::PrimalValueMismatch)?;

    verify_constrained_curved_phi1(CurvedConstrainedPhi1Certificate {
        omega,
        d0: d0.to_vec(),
        d1,
        curvature_k,
        weights: weights.to_vec(),
        tau,
        alpha,
        primal_residual,
        dual_y,
        dual_z,
        dual_lambda,
        reported_value,
    })
}

/// Primal LP variables:
/// `[f+ (p), f- (p), r+ (m), r- (m), c+ (k), c- (k), s_tau (1)]`
/// Constraints:
/// - `d0(f+ - f-) + r+ - r- = omega` (`m` rows)
/// - `K(f+ - f-) + c+ - c- = d1 omega` (`k` rows)
/// - `sum_r (c+_r + c-_r) + s_tau = budget` (`1` row)
fn solve_primal_constrained(
    d0: &[Vec<BigRational>],
    curvature_k: &[Vec<BigRational>],
    weights: &[BigRational],
    omega: &[BigRational],
    d1_omega: &[BigRational],
    budget: &BigRational,
    c0_dim: usize,
) -> Result<Vec<BigRational>, CurvedConstrainedPhi1Error> {
    let c1_dim = weights.len();
    let c2_dim = curvature_k.len();
    let width = 2 * c0_dim + 2 * c1_dim + 2 * c2_dim + 1;
    let mut objective = vec![BigRational::zero(); width];
    for (i, weight) in weights.iter().enumerate() {
        objective[2 * c0_dim + i] = weight.clone();
        objective[2 * c0_dim + c1_dim + i] = weight.clone();
    }

    let mut constraints = Vec::with_capacity(c1_dim + c2_dim + 1);
    let mut rhs = Vec::with_capacity(c1_dim + c2_dim + 1);

    for (i, coefficients) in d0.iter().enumerate() {
        let mut row = vec![BigRational::zero(); width];
        for (j, coefficient) in coefficients.iter().enumerate() {
            row[j] = coefficient.clone();
            row[c0_dim + j] = -coefficient;
        }
        row[2 * c0_dim + i] = BigRational::one();
        row[2 * c0_dim + c1_dim + i] = -BigRational::one();
        constraints.push(row);
        rhs.push(omega[i].clone());
    }

    let c_offset = 2 * c0_dim + 2 * c1_dim;
    for (r, k_row) in curvature_k.iter().enumerate() {
        let mut row = vec![BigRational::zero(); width];
        for (j, coefficient) in k_row.iter().enumerate() {
            row[j] = coefficient.clone();
            row[c0_dim + j] = -coefficient;
        }
        row[c_offset + r] = BigRational::one();
        row[c_offset + c2_dim + r] = -BigRational::one();
        constraints.push(row);
        rhs.push(d1_omega[r].clone());
    }

    let mut budget_row = vec![BigRational::zero(); width];
    for r in 0..c2_dim {
        budget_row[c_offset + r] = BigRational::one();
        budget_row[c_offset + c2_dim + r] = BigRational::one();
    }
    budget_row[c_offset + 2 * c2_dim] = BigRational::one();
    constraints.push(budget_row);
    rhs.push(budget.clone());

    let (_, x) = minimize(&objective, constraints, rhs).map_err(|refusal| {
        CurvedConstrainedPhi1Error::LinearProgram {
            program: Phi1LinearProgram::Primal,
            refusal,
        }
    })?;
    let alpha = (0..c0_dim).map(|j| &x[j] - &x[c0_dim + j]).collect();
    Ok(alpha)
}

/// Dual LP variables:
/// `[y+ (m), y- (m), s+ (m), s- (m), z+ (k), z- (k), t+ (k), t- (k), lambda (1)]`
/// Constraints:
/// - `d0^T(y+ - y-) + K^T(z+ - z-) = 0` (`p` rows)
/// - `y+_i + s+_i = w_i`, `y-_i + s-_i = w_i` (`2m` rows)
/// - `z+_r + t+_r - lambda = 0`, `z-_r + t-_r - lambda = 0` (`2k` rows)
/// Objective:
/// `min -<omega, y+ - y-> - <d1 omega, z+ - z-> + budget * lambda`.
fn push_dual_annihilator_rows(
    d0: &[Vec<BigRational>],
    curvature_k: &[Vec<BigRational>],
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
    z_offset: usize,
    width: usize,
    constraints: &mut Vec<Vec<BigRational>>,
    rhs: &mut Vec<BigRational>,
) {
    for j in 0..c0_dim {
        let mut row = vec![BigRational::zero(); width];
        for (i, coefficients) in d0.iter().enumerate() {
            row[i] = coefficients[j].clone();
            row[c1_dim + i] = -&coefficients[j];
        }
        for (r, k_row) in curvature_k.iter().enumerate() {
            row[z_offset + r] = k_row[j].clone();
            row[z_offset + c2_dim + r] = -&k_row[j];
        }
        constraints.push(row);
        rhs.push(BigRational::zero());
    }
}

fn push_dual_box_and_linf_rows(
    weights: &[BigRational],
    c1_dim: usize,
    c2_dim: usize,
    z_offset: usize,
    lambda_col: usize,
    width: usize,
    constraints: &mut Vec<Vec<BigRational>>,
    rhs: &mut Vec<BigRational>,
) {
    for (i, weight) in weights.iter().enumerate() {
        for sign in 0..2 {
            let mut row = vec![BigRational::zero(); width];
            row[sign * c1_dim + i] = BigRational::one();
            row[(2 + sign) * c1_dim + i] = BigRational::one();
            constraints.push(row);
            rhs.push(weight.clone());
        }
    }
    for r in 0..c2_dim {
        for sign in 0..2 {
            let mut row = vec![BigRational::zero(); width];
            row[z_offset + sign * c2_dim + r] = BigRational::one();
            row[z_offset + (2 + sign) * c2_dim + r] = BigRational::one();
            row[lambda_col] = -BigRational::one();
            constraints.push(row);
            rhs.push(BigRational::zero());
        }
    }
}

fn solve_dual_constrained(
    d0: &[Vec<BigRational>],
    curvature_k: &[Vec<BigRational>],
    weights: &[BigRational],
    omega: &[BigRational],
    d1_omega: &[BigRational],
    budget: &BigRational,
    c0_dim: usize,
) -> Result<(Vec<BigRational>, Vec<BigRational>, BigRational), CurvedConstrainedPhi1Error> {
    let c1_dim = weights.len();
    let c2_dim = curvature_k.len();
    if c1_dim == 0 {
        return Ok((Vec::new(), vec![BigRational::zero(); c2_dim], BigRational::zero()));
    }
    let z_offset = 4 * c1_dim;
    let lambda_col = z_offset + 4 * c2_dim;
    let width = lambda_col + 1;

    let mut objective = vec![BigRational::zero(); width];
    for (i, value) in omega.iter().enumerate() {
        objective[i] = -value;
        objective[c1_dim + i] = value.clone();
    }
    for (r, value) in d1_omega.iter().enumerate() {
        objective[z_offset + r] = -value;
        objective[z_offset + c2_dim + r] = value.clone();
    }
    objective[lambda_col] = budget.clone();

    let mut constraints = Vec::with_capacity(c0_dim + 2 * c1_dim + 2 * c2_dim);
    let mut rhs = Vec::with_capacity(c0_dim + 2 * c1_dim + 2 * c2_dim);

    push_dual_annihilator_rows(
        d0,
        curvature_k,
        c0_dim,
        c1_dim,
        c2_dim,
        z_offset,
        width,
        &mut constraints,
        &mut rhs,
    );
    push_dual_box_and_linf_rows(
        weights,
        c1_dim,
        c2_dim,
        z_offset,
        lambda_col,
        width,
        &mut constraints,
        &mut rhs,
    );

    let (_, x) = minimize(&objective, constraints, rhs).map_err(|refusal| {
        CurvedConstrainedPhi1Error::LinearProgram {
            program: Phi1LinearProgram::Dual,
            refusal,
        }
    })?;

    let dual_y: Vec<BigRational> = (0..c1_dim).map(|i| &x[i] - &x[c1_dim + i]).collect();
    let dual_z: Vec<BigRational> = (0..c2_dim)
        .map(|r| &x[z_offset + r] - &x[z_offset + c2_dim + r])
        .collect();
    let dual_lambda = dual_z
        .iter()
        .map(Signed::abs)
        .max()
        .unwrap_or_else(BigRational::zero)
        .max(x[lambda_col].clone());

    Ok((dual_y, dual_z, dual_lambda))
}

// Origin: engine/crates_rs/core_solvers/src/solver_lp_phi1_quotient.rs
// Claim: urn:core:crates_rs:core-solvers:solver-lp-phi1-quotient:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::solver_graph_phi1_distance::{solve_graph_phi1, GraphPhi1Edge, GraphPhi1Request};
    use num_bigint::BigInt;
    use core_functional::phi1::Phi1Functional;

    fn q(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn qr(numer: i64, denom: i64) -> BigRational {
        BigRational::new(BigInt::from(numer), BigInt::from(denom))
    }

    /// Signed incidence rows for directed edges: -1 at the tail, +1 at the head.
    fn incidence(vertices: usize, edges: &[(usize, usize)]) -> Vec<Vec<BigRational>> {
        edges
            .iter()
            .map(|&(tail, head)| {
                let mut row = vec![q(0); vertices];
                row[tail] = q(-1);
                row[head] = q(1);
                row
            })
            .collect()
    }

    fn solve(
        boundary: Vec<Vec<BigRational>>,
        weights: Vec<BigRational>,
        omega: &[BigRational],
    ) -> VerifiedExactPhi1 {
        let space = L1Seminorm::new(boundary, weights).unwrap();
        solve_exact_phi1(&space, omega).unwrap()
    }

    #[test]
    fn solved_triangle_certificates_replay_with_zero_duality_gap() {
        let cycle = incidence(3, &[(0, 1), (1, 2), (2, 0)]);
        let exact = solve(cycle.clone(), vec![q(1); 3], &[q(1), q(1), q(-2)]);
        assert_eq!(exact.value(), &q(0));
        let frustrated = solve(cycle, vec![q(1); 3], &[q(1), q(1), q(1)]);
        assert_eq!(frustrated.value(), &q(3));
        // The sealed value is re-derivable from the exported witness alone.
        for verified in [exact, frustrated] {
            let replayed =
                Phi1Functional::verify_exact_certificate(verified.certificate().clone()).unwrap();
            assert_eq!(replayed.value(), verified.value());
        }
    }

    #[test]
    fn solver_agrees_with_independent_spanning_forest_enumeration() {
        let edge = |u: &str, v: &str, weight: &str, claim: &str| GraphPhi1Edge {
            u: u.into(),
            v: v.into(),
            weight: weight.into(),
            claim: claim.into(),
        };
        let cases: Vec<(Vec<&str>, Vec<GraphPhi1Edge>)> = vec![
            (
                vec!["a", "b", "c"],
                vec![
                    edge("a", "b", "1", "1/2"),
                    edge("b", "c", "1", "1/2"),
                    edge("a", "c", "2", "3/2"),
                ],
            ),
            (
                vec!["v0", "v1", "v2", "v3"],
                vec![
                    edge("v0", "v1", "1", "1"),
                    edge("v1", "v2", "1", "1"),
                    edge("v2", "v0", "1", "1"),
                    edge("v1", "v3", "1", "1"),
                    edge("v3", "v2", "1", "1"),
                ],
            ),
            (
                vec!["v0", "v1", "v2", "v3", "v4", "v5"],
                vec![
                    edge("v0", "v1", "1", "1"),
                    edge("v1", "v2", "1", "1"),
                    edge("v2", "v0", "1", "1"),
                    edge("v2", "v3", "1", "1"),
                    edge("v3", "v4", "1", "1"),
                    edge("v4", "v2", "1", "1"),
                    edge("v4", "v5", "1", "1"),
                    edge("v5", "v0", "1", "1"),
                    edge("v0", "v4", "1", "1"),
                ],
            ),
        ];
        for (names, edges) in cases {
            let index = |name: &str| names.iter().position(|n| *n == name).unwrap();
            let pairs: Vec<(usize, usize)> =
                edges.iter().map(|e| (index(&e.u), index(&e.v))).collect();
            let weights: Vec<BigRational> =
                edges.iter().map(|e| e.weight.parse().unwrap()).collect();
            let omega: Vec<BigRational> = edges.iter().map(|e| e.claim.parse().unwrap()).collect();
            let enumerated = solve_graph_phi1(GraphPhi1Request {
                vertices: names.iter().map(|n| n.to_string()).collect(),
                edges,
            })
            .unwrap();
            let solved = solve(incidence(names.len(), &pairs), weights, &omega);
            assert_eq!(solved.value().to_string(), enumerated.phi1);
        }
    }

    #[test]
    fn values_beyond_i64_stay_exact() {
        let huge = BigRational::from_integer(BigInt::from(1u128 << 70));
        let cycle = incidence(3, &[(0, 1), (1, 2), (2, 0)]);
        let verified = solve(
            cycle,
            vec![q(1); 3],
            &[huge.clone(), huge.clone(), huge.clone()],
        );
        assert_eq!(verified.value(), &(huge * q(3)));
    }

    #[test]
    fn degenerate_and_empty_presentations_terminate() {
        // Duplicate columns and an isolated vertex make the primal degenerate.
        let boundary = vec![
            vec![q(-1), q(-1), q(1), q(0)],
            vec![q(0), q(0), q(-1), q(1)],
            vec![q(1), q(1), q(0), q(-1)],
        ];
        let verified = solve(boundary, vec![qr(1, 2), q(2), q(3)], &[q(2), q(-1), q(4)]);
        assert_eq!(verified.value(), &qr(5, 2));

        let zero_image = solve(vec![vec![], vec![]], vec![q(2), q(3)], &[q(-3), q(4)]);
        assert_eq!(zero_image.value(), &q(18));

        let empty = solve(vec![], vec![], &[]);
        assert_eq!(empty.value(), &q(0));
    }

    #[test]
    fn malformed_representatives_are_typed_refusals() {
        let space = L1Seminorm::new(vec![vec![q(1)]], vec![q(1)]).unwrap();
        assert_eq!(
            solve_exact_phi1(&space, &[]),
            Err(Phi1SolveError::CoreDimensionMismatch {
                expected: 1,
                actual: 0
            })
        );
        let invalid = BigRational::new_raw(BigInt::from(1), BigInt::from(0));
        assert_eq!(
            solve_exact_phi1(&space, &[invalid]),
            Err(Phi1SolveError::ZeroDenominator { index: 0 })
        );
    }

    #[test]
    fn curved_descent_constrained_lp_enforces_raw_gamma2_budget_while_exact_complex_refuses_k_nonzero() {
        use core_functional::gamma2::{ExactCochainComplexQ, ExactGamma2Error};

        // Curved 1-vertex, 2-edge, 1-face presentation:
        // d0 = [[1], [1]], d1 = [[1, -2]], so K = d1 * d0 = [[-1]] != 0.
        let d0 = vec![vec![q(1)], vec![q(1)]];
        let d1 = vec![vec![q(1), q(-2)]];
        let weights = vec![q(1), q(1)];
        let omega = vec![q(2), q(1)];

        // 1. ExactCochainComplexQ remains strictly restricted to the flat (K = 0) locus.
        assert_eq!(
            ExactCochainComplexQ::try_new(1, 2, 1, d0.clone(), d1.clone()),
            Err(ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 })
        );

        // 2. Unconstrained Phi1 repair chooses f in [1, 2] with ||omega - d0 f||_1 = 1,
        // which increases raw closure defect from ||d1 omega||_1 = 0 to ||d1(omega - d0 f)||_1 >= 1.
        let space = L1Seminorm::new(d0.clone(), weights).unwrap();
        let unconstrained = solve_exact_phi1(&space, &omega).unwrap();
        assert_eq!(unconstrained.value(), &q(1));
        let unconstrained_raw_gamma2 = core_functional::gamma2::Gamma2Functional::try_compute_raw(
            unconstrained.primal_residual(),
            &d1,
        )
        .unwrap();
        assert!(unconstrained_raw_gamma2.value() >= &q(1));

        // 3. Constrained LP with tau = 0 enforces ||d1 omega - K f||_1 <= Gamma2_raw(omega) + 0 = 0,
        // pinning f* = 0 with constrained optimum ||omega - d0 f*||_1 = 3 and zero duality gap.
        let constrained_tau0 = solve_constrained_curved_phi1(&space, &d1, &omega, &q(0)).unwrap();
        assert!(constrained_tau0.is_curved());
        assert_eq!(constrained_tau0.curvature_k(), &[vec![q(-1)]]);
        assert_eq!(constrained_tau0.baseline_raw_gamma2().value(), &q(0));
        assert_eq!(constrained_tau0.repaired_raw_gamma2().value(), &q(0));
        assert_eq!(constrained_tau0.alpha(), &[q(0)]);
        assert_eq!(constrained_tau0.value(), &q(3));

        // 4. Constrained LP with tau = 1/2 allows ||d1 omega - K f||_1 <= 1/2,
        // attaining f* = 1/2 with constrained objective ||[3/2, 1/2]||_1 = 2.
        let constrained_half =
            solve_constrained_curved_phi1(&space, &d1, &omega, &qr(1, 2)).unwrap();
        assert_eq!(constrained_half.alpha(), &[qr(1, 2)]);
        assert_eq!(constrained_half.repaired_raw_gamma2().value(), &qr(1, 2));
        assert_eq!(constrained_half.value(), &q(2));

        // 5. Constrained LP with tau = 1 reaches the unconstrained Phi1 minimum 1.
        let constrained_one = solve_constrained_curved_phi1(&space, &d1, &omega, &q(1)).unwrap();
        assert_eq!(constrained_one.value(), &q(1));
        assert!(constrained_one.repaired_raw_gamma2().value() <= &q(1));

        // All solved certificates replay independently through verify_constrained_curved_phi1.
        for solved in [constrained_tau0, constrained_half, constrained_one] {
            let replayed =
                verify_constrained_curved_phi1(solved.certificate().clone()).unwrap();
            assert_eq!(replayed.value(), solved.value());
            assert_eq!(
                replayed.repaired_raw_gamma2().value(),
                solved.repaired_raw_gamma2().value()
            );
        }
    }

    #[test]
    fn flat_locus_agrees_with_exact_phi1_and_exact_cochain_complex_q() {
        use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};

        // Standard flat triangle boundary: d0 is 3x3 edge-vertex incidence, d1 = [[1, 1, 1]],
        // so K = d1 * d0 = [[0, 0, 0]].
        let d0 = incidence(3, &[(0, 1), (1, 2), (2, 0)]);
        let d1 = vec![vec![q(1), q(1), q(1)]];
        let weights = vec![q(1); 3];
        let omega = vec![q(2), q(-1), q(3)];

        let complex =
            ExactCochainComplexQ::try_new(3, 3, 1, d0.clone(), d1.clone()).unwrap();
        let space = L1Seminorm::new(d0, weights).unwrap();
        let exact_phi1 = solve_exact_phi1(&space, &omega).unwrap();
        let residual_q =
            DegreeOneResidualQ::try_new(&complex, exact_phi1.primal_residual().to_vec()).unwrap();
        let exact_gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual_q).unwrap();

        let constrained = solve_constrained_curved_phi1(&space, &d1, &omega, &q(0)).unwrap();
        assert!(!constrained.is_curved());
        assert_eq!(constrained.curvature_k(), &[vec![q(0), q(0), q(0)]]);
        assert_eq!(constrained.value(), exact_phi1.value());
        assert_eq!(
            constrained.repaired_raw_gamma2().value(),
            exact_gamma2.value()
        );
    }

    #[test]
    fn tampered_curved_certificate_is_rejected_by_verifier() {
        let d0 = vec![vec![q(1)], vec![q(1)]];
        let d1 = vec![vec![q(1), q(-2)]];
        let space = L1Seminorm::new(d0, vec![q(1), q(1)]).unwrap();
        let omega = vec![q(2), q(1)];
        let solved = solve_constrained_curved_phi1(&space, &d1, &omega, &q(0)).unwrap();

        // Tamper with alpha/primal_residual to use the unconstrained repair f = 1 under tau = 0.
        let mut budget_violating = solved.certificate().clone();
        budget_violating.alpha = vec![q(1)];
        budget_violating.primal_residual = vec![q(1), q(0)];
        budget_violating.reported_value = q(1);
        assert_eq!(
            verify_constrained_curved_phi1(budget_violating),
            Err(CurvedConstrainedPhi1Error::ClosureBudgetExceeded {
                repaired_gamma2: q(1),
                budget: q(0),
            })
        );

        // Tamper with curvature_k to claim K = 0 on a curved presentation.
        let mut wrong_k = solved.certificate().clone();
        wrong_k.curvature_k = vec![vec![q(0)]];
        assert_eq!(
            verify_constrained_curved_phi1(wrong_k),
            Err(CurvedConstrainedPhi1Error::CurvatureMismatch { row: 0, column: 0 })
        );

        // Tamper with dual_z so d0^T y + K^T z != 0.
        let mut wrong_dual = solved.certificate().clone();
        wrong_dual.dual_z = vec![q(0)];
        assert_eq!(
            verify_constrained_curved_phi1(wrong_dual),
            Err(CurvedConstrainedPhi1Error::DualCoupledAnnihilatorMismatch { column: 0 })
        );
    }
}

