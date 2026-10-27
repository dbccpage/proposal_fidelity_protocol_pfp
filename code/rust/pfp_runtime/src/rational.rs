//! Exact rational certificates: LP duality and the L¹ quotient distance.
//!
//! Two adapters from merge spec sections 4.2–4.4, both exact over ℚ. No
//! floating point appears anywhere; `BigRational` is used precisely so that
//! "the objectives are equal" is a decision rather than a tolerance.
//!
//! The discipline both adapters share: **the host verifies a candidate, it does
//! not search for one.** A model proposes `(p, y)` or `(x, u)`; this code
//! checks feasibility and the exact equality that makes the pair a proof. The
//! words "dual witness" certify nothing on their own.
//!
//! AuthorityEffect: None.

use num_traits::{One, Signed, Zero};
use core_functional::phi1::ExactPhi1CertificateError;
use core_functional::residual::Residual;
use core_functional::{ExactPhi1Certificate, Phi1Functional};
use core_kernel::{parse_exact, to_canonical_string, Exact, ExactError};
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum RationalError {
    #[error("dimension mismatch: expected {expected}, got {actual}")]
    Dimension { expected: usize, actual: usize },

    #[error("matrix rows are ragged")]
    Ragged,

    #[error("matrix is not square: {rows} x {cols}")]
    NotSquare { rows: usize, cols: usize },

    #[error("matrix is not symmetric")]
    NotSymmetric,

    #[error("linear algebra error: {0}")]
    LinearAlgebra(String),

    #[error(transparent)]
    NotExact(#[from] ExactError),
}

// ---------------------------------------------------------------------------
// L¹ quotient distance
// ---------------------------------------------------------------------------

/// A rational linear map, dense and row-major.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RationalMatrixWire", into = "RationalMatrixWire")]
#[serde(deny_unknown_fields)]
pub struct RationalMatrix {
    rows: usize,
    cols: usize,
    data: Vec<Exact>,
}

/// Checked wire representation for a rational matrix.
///
/// Each entry is a rational string and rows are nested, so dimensions are
/// derived from data rather than repeated as independently forgeable fields.
/// Deserialization passes through [`RationalMatrix::from_rows`].
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct RationalMatrixWire {
    rows: Vec<Vec<String>>,
}

impl TryFrom<RationalMatrixWire> for RationalMatrix {
    type Error = RationalError;

    fn try_from(wire: RationalMatrixWire) -> Result<Self, Self::Error> {
        let rows = wire
            .rows
            .into_iter()
            .map(|row| {
                row.into_iter()
                    .map(|value| parse_exact(&value))
                    .collect::<Result<Vec<_>, _>>()
            })
            .collect::<Result<Vec<_>, _>>()?;
        Self::from_rows(&rows)
    }
}

impl From<RationalMatrix> for RationalMatrixWire {
    fn from(matrix: RationalMatrix) -> Self {
        let rows = (0..matrix.rows)
            .map(|row| {
                (0..matrix.cols)
                    .map(|col| to_canonical_string(matrix.get(row, col)))
                    .collect()
            })
            .collect();
        Self { rows }
    }
}

impl RationalMatrix {
    pub fn from_rows(rows: &[Vec<Exact>]) -> Result<Self, RationalError> {
        let row_count = rows.len();
        let col_count = rows.first().map(Vec::len).unwrap_or(0);
        if rows.iter().any(|row| row.len() != col_count) {
            return Err(RationalError::Ragged);
        }
        Ok(Self {
            rows: row_count,
            cols: col_count,
            data: rows.iter().flatten().cloned().collect(),
        })
    }

    pub fn rows(&self) -> usize {
        self.rows
    }

    pub fn cols(&self) -> usize {
        self.cols
    }

    pub fn get(&self, row: usize, col: usize) -> &Exact {
        &self.data[row * self.cols + col]
    }

    /// `self · vector`.
    pub fn apply(&self, vector: &[Exact]) -> Result<Vec<Exact>, RationalError> {
        if vector.len() != self.cols {
            return Err(RationalError::Dimension {
                expected: self.cols,
                actual: vector.len(),
            });
        }
        Ok((0..self.rows)
            .map(|r| (0..self.cols).fold(Exact::zero(), |acc, c| acc + self.get(r, c) * &vector[c]))
            .collect())
    }

    /// `selfᵀ · vector`.
    pub fn apply_transpose(&self, vector: &[Exact]) -> Result<Vec<Exact>, RationalError> {
        if vector.len() != self.rows {
            return Err(RationalError::Dimension {
                expected: self.rows,
                actual: vector.len(),
            });
        }
        Ok((0..self.cols)
            .map(|c| (0..self.rows).fold(Exact::zero(), |acc, r| acc + self.get(r, c) * &vector[r]))
            .collect())
    }

    pub fn is_square(&self) -> bool {
        self.rows == self.cols
    }

    pub fn is_symmetric(&self) -> bool {
        if !self.is_square() {
            return false;
        }
        for i in 0..self.rows {
            for j in (i + 1)..self.cols {
                if self.get(i, j) != self.get(j, i) {
                    return false;
                }
            }
        }
        true
    }

    /// Exact determinant via Bareiss fraction-free elimination from `linear_algebra`.
    pub fn determinant(&self) -> Result<Exact, RationalError> {
        if !self.is_square() {
            return Err(RationalError::NotSquare {
                rows: self.rows,
                cols: self.cols,
            });
        }
        let n = self.rows;
        if n == 0 {
            return Ok(Exact::one());
        }

        use num_bigint::BigInt;
        use num_integer::Integer;

        let mut int_matrix: Vec<Vec<BigInt>> = Vec::with_capacity(n);
        let mut total_denom_scale = BigInt::from(1);

        for r in 0..n {
            let mut row_lcm = BigInt::from(1);
            for c in 0..n {
                let entry = self.get(r, c);
                row_lcm = row_lcm.lcm(entry.denom());
            }
            let mut row_ints = Vec::with_capacity(n);
            for c in 0..n {
                let entry = self.get(r, c);
                let factor = &row_lcm / entry.denom();
                row_ints.push(entry.numer() * factor);
            }
            int_matrix.push(row_ints);
            total_denom_scale *= row_lcm;
        }

        let int_det = linear_algebra::determinant::bareiss_determinant(&int_matrix)
            .map_err(|e| RationalError::LinearAlgebra(e.to_string()))?;

        Ok(Exact::new(int_det, total_denom_scale))
    }

    /// Sylvester's criterion: exact positive definiteness via LDLT pivots from `linear_algebra`.
    pub fn is_positive_definite(&self) -> Result<bool, RationalError> {
        if !self.is_square() {
            return Err(RationalError::NotSquare {
                rows: self.rows,
                cols: self.cols,
            });
        }
        if !self.is_symmetric() {
            return Err(RationalError::NotSymmetric);
        }
        let mut rows: Vec<Vec<Exact>> = Vec::with_capacity(self.rows);
        for r in 0..self.rows {
            let mut row = Vec::with_capacity(self.cols);
            for c in 0..self.cols {
                row.push(self.get(r, c).clone());
            }
            rows.push(row);
        }
        match linear_algebra::exact_ldlt::ldlt_pivots_strictly_positive_rational(&rows) {
            Ok(_) => Ok(true),
            Err(_) => Ok(false),
        }
    }

    /// Exact LDLT decomposition pivots from `linear_algebra`.
    pub fn ldlt_pivots(&self) -> Result<Vec<Exact>, RationalError> {
        if !self.is_square() {
            return Err(RationalError::NotSquare {
                rows: self.rows,
                cols: self.cols,
            });
        }
        if !self.is_symmetric() {
            return Err(RationalError::NotSymmetric);
        }
        let mut rows: Vec<Vec<Exact>> = Vec::with_capacity(self.rows);
        for r in 0..self.rows {
            let mut row = Vec::with_capacity(self.cols);
            for c in 0..self.cols {
                row.push(self.get(r, c).clone());
            }
            rows.push(row);
        }
        let (_, pivots, _) = linear_algebra::exact_ldlt::ldlt_decomposition_rational(&rows)
            .map_err(RationalError::LinearAlgebra)?;
        Ok(pivots)
    }

    /// Leading principal minors: det(m[0..k, 0..k]) for k in 1..=n.
    pub fn leading_minors(&self) -> Result<Vec<Exact>, RationalError> {
        if !self.is_square() {
            return Err(RationalError::NotSquare {
                rows: self.rows,
                cols: self.cols,
            });
        }
        let mut minors = Vec::with_capacity(self.rows);
        for k in 1..=self.rows {
            let sub_rows: Vec<Vec<Exact>> = (0..k)
                .map(|r| (0..k).map(|c| self.get(r, c).clone()).collect())
                .collect();
            let sub = RationalMatrix::from_rows(&sub_rows)?;
            minors.push(sub.determinant()?);
        }
        Ok(minors)
    }

    /// Exact rank via `linear_algebra` ExactRowReduction over BigRational.
    pub fn rank(&self) -> Result<usize, RationalError> {
        if self.rows == 0 || self.cols == 0 {
            return Ok(0);
        }
        use linear_algebra::backend::basic_matrix::BasicMatrix;
        use linear_algebra::linear_algebra::image_kernel::ExactRowReduction;

        let bm = BasicMatrix::from_row_major(self.rows, self.cols, self.data.clone())
            .map_err(|e| RationalError::LinearAlgebra(format!("{e:?}")))?;
        ExactRowReduction::<Exact>::rank(&bm)
            .map_err(|e| RationalError::LinearAlgebra(format!("{e:?}")))
    }

    fn multiply_square_matrix(&self, rhs: &[Vec<Exact>]) -> Vec<Vec<Exact>> {
        let n = self.rows;
        let mut prod = vec![vec![Exact::zero(); n]; n];
        for i in 0..n {
            for j in 0..n {
                let mut sum = Exact::zero();
                for t in 0..n {
                    sum += self.get(i, t) * &rhs[t][j];
                }
                prod[i][j] = sum;
            }
        }
        prod
    }

    fn add_scaled_identity(prod: &[Vec<Exact>], scalar: &Exact) -> Vec<Vec<Exact>> {
        let n = prod.len();
        let mut mk = vec![vec![Exact::zero(); n]; n];
        for i in 0..n {
            for j in 0..n {
                mk[i][j] = if i == j {
                    &prod[i][j] + scalar
                } else {
                    prod[i][j].clone()
                };
            }
        }
        mk
    }

    fn matrix_trace(mat: &[Vec<Exact>]) -> Exact {
        let mut tr = Exact::zero();
        for (i, row) in mat.iter().enumerate() {
            tr += &row[i];
        }
        tr
    }

    /// Exact characteristic polynomial coefficients via Faddeev-LeVerrier over BigRational.
    pub fn char_poly(&self) -> Result<Vec<Exact>, RationalError> {
        if !self.is_square() {
            return Err(RationalError::NotSquare {
                rows: self.rows,
                cols: self.cols,
            });
        }
        let n = self.rows;
        let mut coeffs = vec![Exact::zero(); n + 1];
        coeffs[n] = Exact::one();
        let mut mk = vec![vec![Exact::zero(); n]; n];
        let mut ck = Exact::one();

        for k in 1..=n {
            // M_k = A * M_{k-1} + c_{n-k+1} * I
            let prod = self.multiply_square_matrix(&mk);
            mk = Self::add_scaled_identity(&prod, &ck);
            let am = self.multiply_square_matrix(&mk);
            let tr = Self::matrix_trace(&am);
            ck = -(&tr / Exact::from(num_bigint::BigInt::from(k)));
            coeffs[n - k] = ck.clone();
        }
        Ok(coeffs)
    }
}

pub fn inner(left: &[Exact], right: &[Exact]) -> Result<Exact, RationalError> {
    if left.len() != right.len() {
        return Err(RationalError::Dimension {
            expected: left.len(),
            actual: right.len(),
        });
    }
    Ok(left
        .iter()
        .zip(right)
        .fold(Exact::zero(), |acc, (a, b)| acc + a * b))
}

/// Why an L¹ quotient certificate was refused.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum L1Refusal {
    /// `Bᵀy ≠ 0`, so `y` is not in the annihilator of the image.
    DualNotAnnihilating { residual: Vec<Exact> },
    /// `‖y‖_∞ > 1`.
    DualNotBounded { max_abs: Exact },
    /// `⟨y, ω⟩ ≠ ‖ω − Bp‖₁`: the pair does not close the gap.
    ObjectivesDiffer { primal_l1: Exact, dual_value: Exact },
}

/// The verified result of an L¹ quotient-distance certificate.
///
/// This type is output-only. Its two result fields are not enough to replay
/// the certificate conditions: verification also needs `B`, `omega`, `p`, and
/// `y`. Consequently it deliberately does not implement `Deserialize`; an
/// input must carry those objects and pass through [`verify_l1_certificate`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(into = "L1CertificateWire")]
pub struct L1Certificate {
    /// `ω − Bp`, kept as a vector alongside its norm.
    residual: Residual,
    /// `⟨y, ω⟩`, equal to the residual's L¹ norm when the certificate holds.
    dual_value: Exact,
}

impl L1Certificate {
    pub fn residual(&self) -> &Residual {
        &self.residual
    }

    pub fn dual_value(&self) -> &Exact {
        &self.dual_value
    }
}

#[derive(Serialize)]
struct L1CertificateWire {
    residual: Residual,
    dual_value: String,
}

impl From<L1Certificate> for L1CertificateWire {
    fn from(certificate: L1Certificate) -> Self {
        Self {
            residual: certificate.residual,
            dual_value: to_canonical_string(&certificate.dual_value),
        }
    }
}

/// Verify `Φ(ω) = min_p ‖ω − Bp‖₁ = max{⟨y,ω⟩ : Bᵀy = 0, ‖y‖_∞ ≤ 1}`.
///
/// Checks all three conditions from merge spec section 4.3 in order and returns
/// the offending quantity on refusal, so a caller learns which condition failed
/// rather than just that something did.
pub fn verify_l1_certificate(
    b: &RationalMatrix,
    omega: &[Exact],
    p: &[Exact],
    y: &[Exact],
) -> Result<Result<L1Certificate, L1Refusal>, RationalError> {
    let image = b.apply(p)?;
    if image.len() != omega.len() {
        return Err(RationalError::Dimension {
            expected: omega.len(),
            actual: image.len(),
        });
    }
    let residual_entries: Vec<Exact> = omega
        .iter()
        .zip(&image)
        .map(|(weight, image_entry)| weight - image_entry)
        .collect();
    let residual = Residual::new(residual_entries.clone());
    let annihilated = b.apply_transpose(y)?;
    let weights = vec![Exact::one(); omega.len()];
    let boundary: Vec<Vec<Exact>> = (0..b.rows())
        .map(|row| {
            (0..b.cols())
                .map(|column| b.get(row, column).clone())
                .collect()
        })
        .collect();
    let reported = residual.l1().clone();
    let replay = ExactPhi1Certificate {
        omega: omega.to_vec(),
        d0: boundary,
        weights,
        alpha: p.to_vec(),
        primal_residual: residual_entries,
        dual_witness: y.to_vec(),
        reported_value: reported.clone(),
    };
    match Phi1Functional::verify_exact_certificate(replay) {
        Ok(_) => Ok(Ok(L1Certificate {
            residual,
            dual_value: reported,
        })),
        Err(ExactPhi1CertificateError::DualAnnihilatorMismatch { .. }) => {
            Ok(Err(L1Refusal::DualNotAnnihilating {
                residual: annihilated,
            }))
        }
        Err(ExactPhi1CertificateError::DualNormBoundViolation { .. }) => {
            let max_abs = y.iter().map(Signed::abs).fold(Exact::zero(), |acc, value| {
                if value > acc {
                    value
                } else {
                    acc
                }
            });
            Ok(Err(L1Refusal::DualNotBounded { max_abs }))
        }
        Err(ExactPhi1CertificateError::DualValueMismatch)
        | Err(ExactPhi1CertificateError::PrimalValueMismatch) => {
            let dual_value = inner(y, omega)?;
            Ok(Err(L1Refusal::ObjectivesDiffer {
                primal_l1: residual.l1().clone(),
                dual_value,
            }))
        }
        Err(error) => Err(RationalError::LinearAlgebra(error.to_string())),
    }
}

// ---------------------------------------------------------------------------
// Linear programming duality
// ---------------------------------------------------------------------------

/// `max cᵀx  s.t.  Ax ≤ b, x ≥ 0`, with the dual `min bᵀu  s.t.  Aᵀu ≥ c, u ≥ 0`.
#[derive(Debug, Clone)]
pub struct StandardLp {
    pub a: RationalMatrix,
    pub b: Vec<Exact>,
    pub c: Vec<Exact>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LpRefusal {
    PrimalInfeasible {
        detail: String,
    },
    DualInfeasible {
        detail: String,
    },
    /// Both feasible but the objectives differ, so optimality is unproven. Weak
    /// duality still bounds the answer, and the gap is reported.
    DualityGap {
        primal: Exact,
        dual: Exact,
    },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LpCertificate {
    pub primal_objective: Exact,
    pub dual_objective: Exact,
}

fn check_primal_feasibility(
    lp: &StandardLp,
    x: &[Exact],
) -> Result<Option<LpRefusal>, RationalError> {
    if let Some(index) = x.iter().position(Signed::is_negative) {
        return Ok(Some(LpRefusal::PrimalInfeasible {
            detail: format!("x[{index}] is negative"),
        }));
    }
    let ax = lp.a.apply(x)?;
    for (index, (lhs, rhs)) in ax.iter().zip(&lp.b).enumerate() {
        if lhs > rhs {
            return Ok(Some(LpRefusal::PrimalInfeasible {
                detail: format!("constraint {index} violated"),
            }));
        }
    }
    Ok(None)
}

fn check_dual_feasibility(
    lp: &StandardLp,
    u: &[Exact],
) -> Result<Option<LpRefusal>, RationalError> {
    if let Some(index) = u.iter().position(Signed::is_negative) {
        return Ok(Some(LpRefusal::DualInfeasible {
            detail: format!("u[{index}] is negative"),
        }));
    }
    let atu = lp.a.apply_transpose(u)?;
    for (index, (lhs, rhs)) in atu.iter().zip(&lp.c).enumerate() {
        if lhs < rhs {
            return Ok(Some(LpRefusal::DualInfeasible {
                detail: format!("dual constraint {index} violated"),
            }));
        }
    }
    Ok(None)
}

/// Verify a primal/dual pair establishes optimality.
///
/// Feasibility of both plus exact equality of objectives is the proof; strong
/// duality then says no better primal exists. This checks a candidate pair, it
/// does not solve the program.
pub fn verify_lp_certificate(
    lp: &StandardLp,
    x: &[Exact],
    u: &[Exact],
) -> Result<Result<LpCertificate, LpRefusal>, RationalError> {
    if x.len() != lp.c.len() {
        return Err(RationalError::Dimension {
            expected: lp.c.len(),
            actual: x.len(),
        });
    }
    if u.len() != lp.b.len() {
        return Err(RationalError::Dimension {
            expected: lp.b.len(),
            actual: u.len(),
        });
    }

    if let Some(refusal) = check_primal_feasibility(lp, x)? {
        return Ok(Err(refusal));
    }
    if let Some(refusal) = check_dual_feasibility(lp, u)? {
        return Ok(Err(refusal));
    }

    let primal_objective = inner(&lp.c, x)?;
    let dual_objective = inner(&lp.b, u)?;
    if primal_objective != dual_objective {
        return Ok(Err(LpRefusal::DualityGap {
            primal: primal_objective,
            dual: dual_objective,
        }));
    }

    Ok(Ok(LpCertificate {
        primal_objective,
        dual_objective,
    }))
}

// Origin: engine/crates_rs/pfp_runtime/src/rational.rs
// Claim: urn:core:crates_rs:pfp-runtime:rational:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_kernel::{exact, integer};

    fn v(values: &[i64]) -> Vec<Exact> {
        values.iter().map(|value| integer(*value)).collect()
    }

    /// The acceptance fixture from merge spec section 4.4.
    ///
    /// max 3x + 2y  s.t.  x+y ≤ 4, x ≤ 2, y ≤ 3, x,y ≥ 0.
    /// Primal (2,2) = 10; dual (2,1,0) = 10.
    fn fixture_lp() -> StandardLp {
        StandardLp {
            a: RationalMatrix::from_rows(&[v(&[1, 1]), v(&[1, 0]), v(&[0, 1])]).unwrap(),
            b: v(&[4, 2, 3]),
            c: v(&[3, 2]),
        }
    }

    #[test]
    fn the_declared_optimum_certifies_at_exactly_ten() {
        let lp = fixture_lp();
        let certificate = verify_lp_certificate(&lp, &v(&[2, 2]), &v(&[2, 1, 0]))
            .unwrap()
            .expect("the fixture pair must certify");
        assert_eq!(certificate.primal_objective, integer(10));
        assert_eq!(certificate.dual_objective, integer(10));
    }

    #[test]
    fn a_feasible_but_suboptimal_primal_leaves_a_reported_gap() {
        let lp = fixture_lp();
        let refusal = verify_lp_certificate(&lp, &v(&[2, 1]), &v(&[2, 1, 0]))
            .unwrap()
            .unwrap_err();
        assert_eq!(
            refusal,
            LpRefusal::DualityGap {
                primal: integer(8),
                dual: integer(10)
            }
        );
    }

    #[test]
    fn an_infeasible_primal_is_refused_before_the_objective_is_compared() {
        let lp = fixture_lp();
        // x = 3 violates x ≤ 2.
        let refusal = verify_lp_certificate(&lp, &v(&[3, 1]), &v(&[2, 1, 0]))
            .unwrap()
            .unwrap_err();
        assert!(matches!(refusal, LpRefusal::PrimalInfeasible { .. }));
    }

    #[test]
    fn negativity_is_refused_on_both_sides() {
        let lp = fixture_lp();
        assert!(matches!(
            verify_lp_certificate(&lp, &v(&[-1, 0]), &v(&[2, 1, 0]))
                .unwrap()
                .unwrap_err(),
            LpRefusal::PrimalInfeasible { .. }
        ));
        assert!(matches!(
            verify_lp_certificate(&lp, &v(&[2, 2]), &v(&[-1, 1, 0]))
                .unwrap()
                .unwrap_err(),
            LpRefusal::DualInfeasible { .. }
        ));
    }

    #[test]
    fn an_infeasible_dual_is_refused() {
        let lp = fixture_lp();
        // u = 0 gives Aᵀu = 0, which fails Aᵀu ≥ c.
        let refusal = verify_lp_certificate(&lp, &v(&[2, 2]), &v(&[0, 0, 0]))
            .unwrap()
            .unwrap_err();
        assert!(matches!(refusal, LpRefusal::DualInfeasible { .. }));
    }

    #[test]
    fn exactness_holds_where_floating_point_would_not() {
        // 1/3 + 1/3 + 1/3 == 1 exactly.
        let third = exact(1, 3);
        let total = &third + &third + &third;
        assert_eq!(total, Exact::one());
    }

    #[test]
    fn exact_parser_refuses_noncanonical_aliases() {
        for text in ["0/1", "01", "+0", "1/1", "2/2", "1/-2", "-0"] {
            assert!(parse_exact(text).is_err(), "{text} must be refused");
        }
    }

    #[test]
    fn the_residual_vector_survives_alongside_its_norm() {
        // Acceptance criterion 12: the vector is not collapsed into the scalar.
        let residual = Residual::new(v(&[1, -2, 0]));
        assert_eq!(residual.l1(), &integer(3));
        assert_eq!(residual.vector(), v(&[1, -2, 0]).as_slice());
        assert!(!residual.is_zero());
    }

    #[test]
    fn an_exact_repair_certifies_with_a_zero_residual() {
        // B = identity on ℚ², ω = Bp, so the residual vanishes and y = 0 pairs to 0.
        let b = RationalMatrix::from_rows(&[v(&[1, 0]), v(&[0, 1])]).unwrap();
        let certificate = verify_l1_certificate(&b, &v(&[3, 5]), &v(&[3, 5]), &v(&[0, 0]))
            .unwrap()
            .expect("zero residual with the zero dual must certify");
        assert!(certificate.residual.is_zero());
        assert_eq!(certificate.dual_value, Exact::zero());
    }

    #[test]
    fn a_dual_outside_the_annihilator_is_refused() {
        let b = RationalMatrix::from_rows(&[v(&[1, 0]), v(&[0, 1])]).unwrap();
        let refusal = verify_l1_certificate(&b, &v(&[3, 5]), &v(&[0, 0]), &v(&[1, 0]))
            .unwrap()
            .unwrap_err();
        assert!(matches!(refusal, L1Refusal::DualNotAnnihilating { .. }));
    }

    #[test]
    fn a_dual_exceeding_the_infinity_norm_is_refused() {
        // B maps ℚ¹ into the diagonal of ℚ², so y = (t, -t) annihilates Bᵀ.
        let b = RationalMatrix::from_rows(&[v(&[1]), v(&[1])]).unwrap();
        let refusal = verify_l1_certificate(&b, &v(&[1, 0]), &v(&[0]), &v(&[2, -2]))
            .unwrap()
            .unwrap_err();
        match refusal {
            L1Refusal::DualNotBounded { max_abs } => assert_eq!(max_abs, integer(2)),
            other => panic!("expected an infinity-norm refusal, got {other:?}"),
        }
    }

    #[test]
    fn a_quotient_distance_certifies_against_the_diagonal() {
        // ω = (1,0) has L¹ distance 1 from the diagonal span{(1,1)}, attained at
        // p = 1/2 with residual (1/2, -1/2), and y = (1,-1) is admissible with
        // ⟨y,ω⟩ = 1.
        let b = RationalMatrix::from_rows(&[v(&[1]), v(&[1])]).unwrap();
        let certificate = verify_l1_certificate(&b, &v(&[1, 0]), &[exact(1, 2)], &v(&[1, -1]))
            .unwrap()
            .expect("the pair must certify");
        assert_eq!(certificate.residual.l1(), &Exact::one());
        assert_eq!(
            certificate.residual.vector(),
            [exact(1, 2), exact(-1, 2)].as_slice()
        );
        assert_eq!(certificate.dual_value, Exact::one());
    }

    #[test]
    fn a_non_optimal_primal_breaks_the_equality() {
        let b = RationalMatrix::from_rows(&[v(&[1]), v(&[1])]).unwrap();
        // p = 0 leaves residual (1,0) with L¹ = 1... which still equals ⟨y,ω⟩ = 1.
        // Use p = 2 instead: residual (-1,-2), L¹ = 3 ≠ 1.
        let refusal = verify_l1_certificate(&b, &v(&[1, 0]), &v(&[2]), &v(&[1, -1]))
            .unwrap()
            .unwrap_err();
        match refusal {
            L1Refusal::ObjectivesDiffer {
                primal_l1,
                dual_value,
            } => {
                assert_eq!(primal_l1, integer(3));
                assert_eq!(dual_value, Exact::one());
            }
            other => panic!("expected an objective mismatch, got {other:?}"),
        }
    }

    #[test]
    fn dimension_mismatches_are_errors_not_panics() {
        let b = RationalMatrix::from_rows(&[v(&[1, 0]), v(&[0, 1])]).unwrap();
        assert!(b.apply(&v(&[1])).is_err());
        assert!(inner(&v(&[1]), &v(&[1, 2])).is_err());
    }

    #[test]
    fn rational_matrix_round_trips_as_exact_strings() {
        let matrix = RationalMatrix::from_rows(&[
            vec![exact(1, 3), exact(-5, 2)],
            vec![integer(7), Exact::zero()],
        ])
        .unwrap();
        let wire = serde_json::to_value(&matrix).expect("matrix serializes");
        assert_eq!(
            wire,
            serde_json::json!({"rows": [["1/3", "-5/2"], ["7", "0"]]})
        );
        let round_trip: RationalMatrix =
            serde_json::from_value(wire).expect("exact matrix round trips");
        assert_eq!(round_trip, matrix);
    }

    #[test]
    fn rational_matrix_wire_refuses_numbers_ragged_rows_and_unknown_fields() {
        assert!(
            serde_json::from_value::<RationalMatrix>(serde_json::json!({"rows": [[0.5]]})).is_err()
        );
        assert!(serde_json::from_value::<RationalMatrix>(
            serde_json::json!({"rows": [["1"], ["1", "2"]]})
        )
        .is_err());
        assert!(serde_json::from_value::<RationalMatrix>(
            serde_json::json!({"rows": [["1"]], "ignored": true})
        )
        .is_err());
    }

    #[test]
    fn l1_certificate_serializes_without_floating_point() {
        let certificate = L1Certificate {
            residual: Residual::new(vec![exact(1, 2), exact(-1, 2)]),
            dual_value: Exact::one(),
        };
        let wire = serde_json::to_value(&certificate).expect("certificate serializes");
        assert_eq!(
            wire,
            serde_json::json!({
                "residual": {"vector": ["1/2", "-1/2"], "l1": "1"},
                "dual_value": "1"
            })
        );
    }

    #[test]
    fn l1_certificate_cannot_be_deserialized_without_its_witnesses() {
        // The result does not carry B, omega, p, or y, so no input conversion
        // can establish the conditions checked by verify_l1_certificate. The
        // fence is the absent derive, as for packets::RoundRecord.
        let source = include_str!("rational.rs");
        let marker = "pub struct L1Certificate {";
        let start = source.find(marker).expect("L1Certificate is defined here");
        let attribute_start = source[..start]
            .rfind("#[")
            .expect("L1Certificate carries an attribute");
        let mut attached_start = attribute_start;
        while let Some(previous) = source[..attached_start].rfind("#[") {
            let between = &source[previous..attached_start];
            let Some(close) = between.rfind(']') else {
                break;
            };
            if !between[close + 1..].trim().is_empty() {
                break;
            }
            attached_start = previous;
        }
        let attached_attributes = &source[attached_start..start];
        assert!(
            attached_attributes.contains("Serialize"),
            "a verified certificate must still serialize"
        );
        assert!(
            !attached_attributes.contains("Deserialize"),
            "L1Certificate derives Deserialize ({attached_attributes:?}), but its wire result omits the \
             instance and witnesses required to verify the certificate"
        );
    }

    #[test]
    fn the_rational_implementation_admits_no_floating_point_type() {
        let source = include_str!("rational.rs");
        let implementation = source
            .split("#[cfg(test)]")
            .next()
            .expect("the module must have a non-test half");
        assert!(
            implementation.len() > 1_000,
            "the split found no implementation; the marker moved"
        );
        for banned in ["f64", "f32"] {
            assert!(
                !implementation.contains(banned),
                "the rational implementation must admit no {banned}"
            );
        }
    }
}
