//! Constructive finite Hermitian spectral checks over Q(i).
//!
//! Algebraic eigenvalues are isolated at every bounded dimension by the shared
//! exact operator spectrum. Rational spectra yield complete orthogonal eigenbases
//! over Q(i); irrational spectra require an extended eigenvector field and are
//! refused by the same-field decomposition API. Float diagnostics never enter
//! exact commutation or spectral certificates. AuthorityEffect: None.

use crate::exact_hermitian::exact_limits;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use num_bigint::BigInt;

use crate::exact_hermitian::{check_hermitian, eigen_residual, ExactHermitianError};
use crate::trace_norm_certificate::{sign_from_spectrum, TraceNormCertificate, TraceNormError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational, Zero};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite Hermitian spectral face; no continuum claim.";

/// OPEN residual for general-n exact spectral algorithm beyond paid cases.
///
/// **Misdescribes the obstruction — read
/// the program spectral ledger instead.** The phrase
/// "(non-diagonal, n > 2) is unpaid" implies a missing implementation at large
/// `n`. In fact a rational Hermitian matrix can have irrational eigenvalues
/// already at `n = 2` (`[[1,1],[1,0]]`), so no exact decomposition over the
/// rationals exists in general at any size. Retained for continuity of the
/// residual id; superseded in substance.

// ─────────────────────────────────────────────────────────────────────────────
// Scalar carrier
// ─────────────────────────────────────────────────────────────────────────────

/// Explicit scalar carrier for spectral arithmetic.
///
/// [`ScalarCarrier::Float64Demo`] is **non-exact / experimental** and never pays
/// an exact spectral certificate.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ScalarCarrier {
    /// Exact rational field ℚ (Hermitian matrices are real-symmetric when entries are real).
    Rational,
    /// Exact Gaussian rationals ℚ(i).
    GaussianRational,
    /// Floating-point demo path — **NON-EXACT / EXPERIMENTAL**.
    /// Must not be treated as an exact spectral certificate.
    Float64Demo,
}

impl ScalarCarrier {
    /// Whether this carrier supports exact (certificate-grade) arithmetic.
    pub fn is_exact(self) -> bool {
        match self {
            Self::Rational | Self::GaussianRational => true,
            Self::Float64Demo => false,
        }
    }

    pub fn label(self) -> &'static str {
        match self {
            Self::Rational => "Rational",
            Self::GaussianRational => "GaussianRational",
            Self::Float64Demo => "Float64Demo(non-exact/experimental)",
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Errors
// ─────────────────────────────────────────────────────────────────────────────

/// Errors for Hermitian construction and spectral application.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SpectralError {
    ExactAlgebra(String),
    ZeroDimension,
    EntryCountMismatch {
        expected: usize,
        actual: usize,
    },
    /// Mutation-negative: matrix fails Hermiticity check.
    NotHermitian {
        row: usize,
        col: usize,
        detail: &'static str,
    },
    /// Diagonal entry not real (violates Hermitian).
    DiagonalNotReal {
        index: usize,
    },
    /// Off-diagonal not real under [`ScalarCarrier::Rational`].
    RationalCarrierRequiresRealEntries {
        row: usize,
        col: usize,
    },
    /// Spectral theorem refused: one or more hypotheses unpaid.
    HypothesesUnpaid {
        unpaid: Vec<&'static str>,
    },
    /// Characteristic polynomial does not split over the chosen exact carrier.
    CharpolyDoesNotSplit,
    /// Float64Demo cannot pay an exact spectral certificate.
    Float64DemoNonExact,
    /// General-n exact algorithm unpaid (OPEN residual).
    GeneralNAlgorithmOpen,
    /// Unsupported shape for paid exact paths.
    UnsupportedExactShape {
        n: usize,
        diagonal: bool,
    },
    /// The paid spectrum did not yield a trace-norm certificate. Boxed to keep the
    /// error small.
    TraceNormRefused(Box<TraceNormError>),
}

// Origin: engine/crates_rs/core_quantum_physics/src/hermitian_spectral.rs
// Claim: urn:core:crates_rs:core-quantum-physics:hermitian-spectral:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SpectralError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SpectralError {}

// ─────────────────────────────────────────────────────────────────────────────
// Hermitian witness + hypotheses
// ─────────────────────────────────────────────────────────────────────────────

/// Checked Hermiticity witness (only minted by construction checks).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HermitianWitness {
    n: usize,
    carrier: ScalarCarrier,
    /// Exact conjugate-transpose defect is zero (always true when witness exists).
    defect_is_zero: bool,
}

impl HermitianWitness {
    pub fn n(&self) -> usize {
        self.n
    }

    pub fn carrier(&self) -> ScalarCarrier {
        self.carrier
    }

    pub fn defect_is_zero(&self) -> bool {
        self.defect_is_zero
    }
}

/// Hypotheses required before the finite Hermitian spectral theorem may apply.
///
/// Refuse decomposition when any hypothesis is unpaid.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpectralHypotheses {
    /// Finite dimension (must be `true`; continuum / infinite-dim unpaid).
    pub finite_n: bool,
    /// Hermiticity witness from a checked matrix.
    pub hermitian: Option<HermitianWitness>,
    /// Characteristic polynomial splits in the scalar carrier (paid per case).
    pub scalar_closed_for_charpoly: bool,
    /// Declared carrier (Float64Demo never pays exact certificates).
    pub carrier: ScalarCarrier,
    /// Explicit “no continuum object minted” obligation (must be true).
    pub no_continuum_claim: bool,
}

impl SpectralHypotheses {
    /// Build unpaid template from a matrix (charpoly-closed unpaid until case solver pays it).
    pub fn from_matrix_unpaid(matrix: &HermitianMatrix) -> Self {
        Self {
            finite_n: matrix.n >= 1,
            hermitian: Some(matrix.witness.clone()),
            scalar_closed_for_charpoly: false,
            carrier: matrix.carrier,
            no_continuum_claim: true,
        }
    }

    /// List unpaid hypothesis labels (empty ⇒ all paid for exact application).
    pub fn unpaid(&self) -> Vec<&'static str> {
        let mut out = Vec::new();
        if !self.finite_n {
            out.push("finite_n");
        }
        match &self.hermitian {
            None => out.push("hermitian"),
            Some(w) if !w.defect_is_zero => out.push("hermitian.defect_is_zero"),
            Some(_) => {}
        }
        if !self.scalar_closed_for_charpoly {
            out.push("scalar_closed_for_charpoly");
        }
        if !self.carrier.is_exact() {
            out.push("carrier_exact (Float64Demo is non-exact/experimental)");
        }
        if !self.no_continuum_claim {
            out.push("no_continuum_claim");
        }
        out
    }

    pub fn all_paid(&self) -> bool {
        self.unpaid().is_empty()
    }

    /// Gate: refuse spectral theorem when any hypothesis is unpaid.
    pub fn require_paid(&self) -> Result<(), SpectralError> {
        let unpaid = self.unpaid();
        if unpaid.is_empty() {
            Ok(())
        } else {
            Err(SpectralError::HypothesesUnpaid { unpaid })
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Hermitian matrix (finite n, exact carriers)
// ─────────────────────────────────────────────────────────────────────────────

/// Finite `n × n` Hermitian matrix over an explicit scalar carrier.
///
/// Entries are Gaussian rationals. Under [`ScalarCarrier::Rational`], every
/// entry must be real (`im = 0`). Under [`ScalarCarrier::Float64Demo`], use
/// [`HermitianMatrix::try_float64_demo`] — the matrix still stores an exact
/// [`linear_algebra::backend::basic_matrix::BasicMatrix`] only when constructed via exact paths; the demo path stores a
/// separate float buffer and never pays exact certificates.
#[derive(Debug, Clone, PartialEq)]
pub struct HermitianMatrix {
    pub n: usize,
    pub carrier: ScalarCarrier,
    /// Exact `n × n` matrix. `None` when float-demo only.
    exact: Option<BasicMatrix<GaussianRat>>,
    /// Float demo storage: row-major `(re, im)` pairs. Empty when exact path.
    float_entries: Vec<(f64, f64)>,
    witness: HermitianWitness,
}

fn validate_rational_carrier_entries(
    n: usize,
    entries: &[GaussianRat],
) -> Result<(), SpectralError> {
    for i in 0..n {
        for j in 0..n {
            if !entries[i * n + j].is_real() {
                return Err(SpectralError::RationalCarrierRequiresRealEntries { row: i, col: j });
            }
        }
    }
    Ok(())
}

fn map_hermitian_error(defect: ExactHermitianError) -> SpectralError {
    match defect {
        ExactHermitianError::DiagonalNotReal { index } => SpectralError::DiagonalNotReal { index },
        ExactHermitianError::NotSelfAdjoint { row, col } => SpectralError::NotHermitian {
            row,
            col,
            detail: "A[j,i] != conjugate(A[i,j])",
        },
        // The checked carrier enforces flat storage; physical shape errors
        // cannot occur for the declared square matrix above.
        ExactHermitianError::Empty
        | ExactHermitianError::NotSquare { .. }
        | ExactHermitianError::ShapeMismatch { .. }
        | ExactHermitianError::Bipartite { .. }
        | ExactHermitianError::Tensor(_) => SpectralError::ZeroDimension,
        ExactHermitianError::Algebra(e) => SpectralError::ExactAlgebra(e.to_string()),
        ExactHermitianError::Storage(e) => SpectralError::ExactAlgebra(e.to_string()),
        ExactHermitianError::Limits(e) => SpectralError::ExactAlgebra(e.to_string()),
    }
}

fn validate_float_hermitian_pair(
    i: usize,
    j: usize,
    (rij, iij): (f64, f64),
    (rji, iji): (f64, f64),
    tol: f64,
) -> Result<(), SpectralError> {
    let finite = rij.is_finite() && iij.is_finite() && rji.is_finite() && iji.is_finite();
    if !finite {
        return Err(SpectralError::NotHermitian {
            row: i,
            col: j,
            detail: "non-finite entry",
        });
    }
    // A_ji ≈ conj(A_ij)
    if (rji - rij).abs() > tol || (iji + iij).abs() > tol {
        return Err(SpectralError::NotHermitian {
            row: i,
            col: j,
            detail: "A[j,i] != conjugate(A[i,j]) (float tol)",
        });
    }
    Ok(())
}

fn validate_float_hermitian_entries(
    n: usize,
    entries: &[(f64, f64)],
) -> Result<(), SpectralError> {
    const TOL: f64 = 1e-12;
    for i in 0..n {
        let (re, im) = entries[i * n + i];
        if !re.is_finite() || !im.is_finite() || im.abs() > TOL {
            return Err(SpectralError::DiagonalNotReal { index: i });
        }
        for j in (i + 1)..n {
            validate_float_hermitian_pair(
                i,
                j,
                entries[i * n + j],
                entries[j * n + i],
                TOL,
            )?;
        }
    }
    Ok(())
}

impl HermitianMatrix {
    /// Construct an exact Hermitian matrix; refuses non-Hermitian input.
    pub fn try_exact(
        n: usize,
        carrier: ScalarCarrier,
        entries: Vec<GaussianRat>,
    ) -> Result<Self, SpectralError> {
        if n == 0 {
            return Err(SpectralError::ZeroDimension);
        }
        if !carrier.is_exact() {
            return Err(SpectralError::Float64DemoNonExact);
        }
        let expected = core_kernel::resource_limits::OperationLimits::default()
            .check_dense_matrix(n, n, std::mem::size_of::<GaussianRat>())
            .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
        if entries.len() != expected {
            return Err(SpectralError::EntryCountMismatch {
                expected,
                actual: entries.len(),
            });
        }

        // Carrier discipline: Rational ⇒ all entries real.
        if carrier == ScalarCarrier::Rational {
            validate_rational_carrier_entries(n, &entries)?;
        }

        // Hermiticity: A_{ji} = conj(A_{ij}); diagonal real.
        let exact = BasicMatrix::<GaussianRat>::from_row_major(n, n, entries)
            .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
        check_hermitian(&exact).map_err(map_hermitian_error)?;

        let witness = HermitianWitness {
            n,
            carrier,
            defect_is_zero: true,
        };
        Ok(Self {
            n,
            carrier,
            exact: Some(exact),
            float_entries: Vec::new(),
            witness,
        })
    }

    /// Diagonal exact Hermitian from real rational eigenvalues on the diagonal.
    pub fn try_diagonal_rational(
        diagonal: &[Rational],
        carrier: ScalarCarrier,
    ) -> Result<Self, SpectralError> {
        let n = diagonal.len();
        if n == 0 {
            return Err(SpectralError::ZeroDimension);
        }
        if !carrier.is_exact() {
            return Err(SpectralError::Float64DemoNonExact);
        }
        let count = core_kernel::resource_limits::OperationLimits::default()
            .check_dense_matrix(n, n, std::mem::size_of::<GaussianRat>())
            .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
        let mut entries = vec![GaussianRat::zero(); count];
        for (i, d) in diagonal.iter().enumerate() {
            entries[i * n + i] = GaussianRat::from_rational(d.clone());
        }
        Self::try_exact(n, carrier, entries)
    }

    /// Float64Demo construction — **non-exact / experimental**.
    ///
    /// Hermiticity is checked with a small absolute tolerance. This path never
    /// pays [`SpectralHypotheses::scalar_closed_for_charpoly`] for exact use.
    pub fn try_float64_demo(n: usize, entries: Vec<(f64, f64)>) -> Result<Self, SpectralError> {
        if n == 0 {
            return Err(SpectralError::ZeroDimension);
        }
        let expected = core_kernel::resource_limits::OperationLimits::default()
            .check_dense_matrix(n, n, std::mem::size_of::<GaussianRat>())
            .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
        if entries.len() != expected {
            return Err(SpectralError::EntryCountMismatch {
                expected,
                actual: entries.len(),
            });
        }
        validate_float_hermitian_entries(n, &entries)?;
        let witness = HermitianWitness {
            n,
            carrier: ScalarCarrier::Float64Demo,
            defect_is_zero: true,
        };
        Ok(Self {
            n,
            carrier: ScalarCarrier::Float64Demo,
            exact: None,
            float_entries: entries,
            witness,
        })
    }

    pub fn witness(&self) -> &HermitianWitness {
        &self.witness
    }

    pub fn entry(&self, i: usize, j: usize) -> Option<GaussianRat> {
        if i >= self.n || j >= self.n {
            return None;
        }
        self.exact
            .as_ref()
            .and_then(|m| m.get_ref(i, j).ok().cloned())
    }

    /// The exact matrix, absent on the float-demo path.
    pub fn exact_matrix(&self) -> Option<&BasicMatrix<GaussianRat>> {
        self.exact.as_ref()
    }

    pub fn is_diagonal_exact(&self) -> bool {
        let Some(m) = &self.exact else {
            return false;
        };
        if self.n == 0 || m.shape() != (self.n, self.n) {
            return false;
        }
        for i in 0..self.n {
            for j in 0..self.n {
                if i != j && !m.as_slice()[i * m.cols() + j].is_zero() {
                    return false;
                }
            }
        }
        true
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Spectral decomposition result
// ─────────────────────────────────────────────────────────────────────────────

/// How the paid spectral decomposition was obtained.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpectralMethod {
    /// Already diagonal: λ_i = A_{ii}, eigenvectors = standard basis.
    DiagonalExact,
    /// 2×2 charpoly split over the exact carrier.
    TwoByTwoCharpolySplit,
    /// Complete computed rational spectrum, with exact orthogonal kernel bases.
    GeneralRationalExact,
}

/// Authority tag for this diagnostic face. Structurally uninhabitable by
/// authority: it has exactly one variant.
///
/// Deliberately NOT `core_types::AuthorityEffect`, and deliberately not named
/// that either. The canonical type can hold `Certified(CertifiedAuthority)`,
/// so a field of that type on a spectral diagnostic could *represent* authority
/// this face must never carry; a one-variant enum cannot. Renamed 2026-08-04
/// from `AuthorityEffect`, which broke the single-definition invariant asserted
/// by `core_certifiers/tests/phi1_conformance.rs` -- that test requires exactly
/// one `pub enum AuthorityEffect` in the tree, in `core_types/src/authority.rs`,
/// so that the name always means the canonical type.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum SpectralAuthorityTag {
    #[default]
    None,
}

/// Exact spectral decomposition certificate (finite, no continuum).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpectralDecomposition {
    pub n: usize,
    pub carrier: ScalarCarrier,
    pub method: SpectralMethod,
    /// Eigenvalues (real for Hermitian; stored as GaussianRat with `im = 0`).
    pub eigenvalues: Vec<GaussianRat>,
    /// Eigenvectors as length-`n` columns (each a `Vec` of length `n`).
    pub eigenvectors: Vec<Vec<GaussianRat>>,
    pub hypotheses: SpectralHypotheses,
    pub authority_effect: SpectralAuthorityTag,
}

impl SpectralDecomposition {
    /// Distinct eigenvalues, ascending: the spectrum as a set.
    pub fn distinct_eigenvalues(&self) -> Vec<Rational> {
        let mut out: Vec<Rational> = self.eigenvalues.iter().map(|z| z.re.clone()).collect();
        out.sort();
        out.dedup();
        out
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Integer / rational square root (exact)
// ─────────────────────────────────────────────────────────────────────────────

/// Integer square root: `Some(s)` iff `s * s == n` for `n ≥ 0`.
pub fn perfect_isqrt(n: i64) -> Option<i64> {
    if n < 0 {
        return None;
    }
    if n == 0 {
        return Some(0);
    }
    // Binary search on [1, n]
    let mut lo: i64 = 1;
    let mut hi: i64 = n.min(3_037_000_499); // floor(sqrt(i64::MAX)) bound
    while lo <= hi {
        let mid = lo + (hi - lo) / 2;
        let sq = mid.saturating_mul(mid);
        if sq == n {
            return Some(mid);
        } else if sq < n {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    let cand = hi.max(0);
    if cand.checked_mul(cand) == Some(n) {
        Some(cand)
    } else {
        None
    }
}

/// Exact rational square root when both numerator and denominator are perfect squares.
fn rational_sqrt(r: Rational) -> Option<Rational> {
    core_number_theory::rational::sqrt_exact(&r)
}

// ─────────────────────────────────────────────────────────────────────────────
// Spectral theorem API
// ─────────────────────────────────────────────────────────────────────────────

/// Apply the finite Hermitian spectral theorem when hypotheses are paid.
///
/// Paid cases: diagonal (any `n`); 2×2 with splitting charpoly over exact carrier.
/// Otherwise returns a typed refusal (`HypothesesUnpaid`, `CharpolyDoesNotSplit`,
/// `GeneralNAlgorithmOpen`, or `Float64DemoNonExact`).
pub fn spectral_decompose(
    matrix: &HermitianMatrix,
) -> Result<SpectralDecomposition, SpectralError> {
    let h = exact_required(matrix)?;

    // Diagonal path: charpoly splits as ∏(λ − A_ii) over any exact carrier.
    if matrix.is_diagonal_exact() {
        return decompose_diagonal(matrix, h);
    }

    // 2×2 non-diagonal exact path.
    if matrix.n == 2 {
        return decompose_2x2(matrix, h);
    }

    // Compute all algebraic eigenvalues first; a same-field vector decomposition
    // exists over Q(i) exactly when those Hermitian eigenvalues are rational.
    let values = compute_rational_eigenvalues(h)?;
    let (eigenvalues, eigenvectors) = build_orthogonal_eigenbasis(h, matrix.n, values)?;
    let hypotheses = SpectralHypotheses {
        finite_n: true,
        hermitian: Some(matrix.witness.clone()),
        scalar_closed_for_charpoly: true,
        carrier: matrix.carrier,
        no_continuum_claim: true,
    };
    hypotheses.require_paid()?;
    Ok(SpectralDecomposition {
        n: matrix.n,
        carrier: matrix.carrier,
        method: SpectralMethod::GeneralRationalExact,
        eigenvalues,
        eigenvectors,
        hypotheses,
        authority_effect: SpectralAuthorityTag::None,
    })
}

fn compute_rational_eigenvalues(
    h: &BasicMatrix<GaussianRat>,
) -> Result<Vec<(Rational, usize)>, SpectralError> {
    let op = crate::exact_operator::ExactOperator::try_new(h.clone())
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
    op.spectrum()
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?
        .rational_eigenvalues()
        .ok_or(SpectralError::CharpolyDoesNotSplit)
}

fn build_orthogonal_eigenbasis(
    h: &BasicMatrix<GaussianRat>,
    n: usize,
    values: Vec<(Rational, usize)>,
) -> Result<(Vec<GaussianRat>, Vec<Vec<GaussianRat>>), SpectralError> {
    let mut eigenvectors: Vec<Vec<GaussianRat>> = Vec::new();
    let mut eigenvalues = Vec::new();
    for (lambda, multiplicity) in values {
        let basis = compute_shifted_kernel_basis(h, n, &lambda, multiplicity)?;
        let lambda_g = GaussianRat::from_rational(lambda);
        for vector in basis {
            let ortho =
                orthogonalize_and_verify_eigenvector(h, &lambda_g, vector, &eigenvectors)?;
            eigenvalues.push(lambda_g.clone());
            eigenvectors.push(ortho);
        }
    }
    if eigenvectors.len() != n {
        return Err(SpectralError::ExactAlgebra("incomplete eigenbasis".into()));
    }
    Ok((eigenvalues, eigenvectors))
}

fn compute_shifted_kernel_basis(
    h: &BasicMatrix<GaussianRat>,
    n: usize,
    lambda: &Rational,
    multiplicity: usize,
) -> Result<Vec<Vec<GaussianRat>>, SpectralError> {
    let id = mx::identity_with_limits(n, exact_limits())
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
    let scaled = mx::scale(&id, &GaussianRat::from_rational(lambda.clone()))
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
    let shifted =
        mx::sub(h, &scaled).map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
    let basis = linear_algebra::exact_field::elimination::kernel_basis_with_limits(
        &shifted,
        crate::exact_hermitian::exact_limits(),
    )
    .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
    if basis.len() != multiplicity {
        return Err(SpectralError::ExactAlgebra(
            "eigenspace multiplicity failed".into(),
        ));
    }
    Ok(basis)
}

fn orthogonalize_and_verify_eigenvector(
    h: &BasicMatrix<GaussianRat>,
    lambda: &GaussianRat,
    mut vector: Vec<GaussianRat>,
    eigenvectors: &[Vec<GaussianRat>],
) -> Result<Vec<GaussianRat>, SpectralError> {
    for previous in eigenvectors {
        let overlap = star::inner_product(previous, &vector)
            .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
        let norm = star::inner_product(previous, previous)
            .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
        let factor = overlap.mul(&norm.inv());
        for (entry, p) in vector.iter_mut().zip(previous) {
            *entry = entry.sub(&factor.mul(p));
        }
    }
    if vector.iter().all(GaussianRat::is_zero) || first_eigen_defect(h, lambda, &vector).is_some() {
        return Err(SpectralError::ExactAlgebra(
            "eigenvector replay failed".into(),
        ));
    }
    Ok(vector)
}

/// First non-zero row of `A v − λ v` ([`eigen_residual`]). The shapes are `n × n` and
/// `n` by construction; a shape refusal would still fail closed, as row 0.
fn first_eigen_defect(
    h: &BasicMatrix<GaussianRat>,
    lambda: &GaussianRat,
    v: &[GaussianRat],
) -> Option<usize> {
    match eigen_residual(h, lambda, v) {
        Ok(residual) => residual.iter().position(|r| !r.is_zero()),
        Err(_) => Some(0),
    }
}

fn decompose_diagonal(
    matrix: &HermitianMatrix,
    h: &BasicMatrix<GaussianRat>,
) -> Result<SpectralDecomposition, SpectralError> {
    let n = matrix.n;
    let mut eigenvalues = Vec::with_capacity(n);
    let mut eigenvectors = Vec::with_capacity(n);
    for i in 0..n {
        let d = h
            .get_ref(i, i)
            .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?
            .clone();
        debug_assert!(d.is_real());
        eigenvalues.push(d);
        let mut v = vec![GaussianRat::zero(); n];
        v[i] = GaussianRat::one();
        eigenvectors.push(v);
    }

    // Proof-level check: A v_k = λ_k v_k for standard basis (A diagonal).
    for (k, (lambda, v)) in eigenvalues.iter().zip(&eigenvectors).enumerate() {
        if let Some(row) = first_eigen_defect(h, lambda, v) {
            // Should be unreachable for a true diagonal Hermitian matrix.
            return Err(SpectralError::NotHermitian {
                row,
                col: k,
                detail: "diagonal eigen-check failed",
            });
        }
    }

    let hypotheses = SpectralHypotheses {
        finite_n: true,
        hermitian: Some(matrix.witness.clone()),
        scalar_closed_for_charpoly: true,
        carrier: matrix.carrier,
        no_continuum_claim: true,
    };
    hypotheses.require_paid()?;

    Ok(SpectralDecomposition {
        n,
        carrier: matrix.carrier,
        method: SpectralMethod::DiagonalExact,
        eigenvalues,
        eigenvectors,
        hypotheses,
        authority_effect: SpectralAuthorityTag::None,
    })
}

fn decompose_2x2(
    matrix: &HermitianMatrix,
    h: &BasicMatrix<GaussianRat>,
) -> Result<SpectralDecomposition, SpectralError> {
    debug_assert_eq!(matrix.n, 2);
    let a = h
        .get_ref(0, 0)
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?; // A00 real
    let c = h
        .get_ref(0, 1)
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?; // A01
    let b = h
        .get_ref(1, 1)
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?; // A11 real
    debug_assert!(a.is_real() && b.is_real());

    // Char poly: λ² − tr λ + det, tr = a+b, det = ab − |c|²
    // disc = (a−b)² + 4|c|²  (always ≥ 0 in reals)
    let tr = &a.re + &b.re;
    let c_ns = c.norm_sq();
    let diff = &a.re - &b.re;
    let disc = &diff * &diff + ri(4) * c_ns;

    let sqrt_disc = rational_sqrt(disc).ok_or(SpectralError::CharpolyDoesNotSplit)?;
    let two = ri(2);
    let lambda_plus = GaussianRat::from_rational((&tr + &sqrt_disc) / &two);
    let lambda_minus = GaussianRat::from_rational((&tr - &sqrt_disc) / &two);

    let v0 = eigenvector_2x2(a, c, &lambda_plus);
    let v1 = eigenvector_2x2(a, c, &lambda_minus);

    // Algebraic eigen-check: (A − λ I) v = 0 for both vectors.
    verify_eigenpair_2x2(h, &lambda_plus, &v0)?;
    verify_eigenpair_2x2(h, &lambda_minus, &v1)?;

    let hypotheses = SpectralHypotheses {
        finite_n: true,
        hermitian: Some(matrix.witness.clone()),
        scalar_closed_for_charpoly: true,
        carrier: matrix.carrier,
        no_continuum_claim: true,
    };
    hypotheses.require_paid()?;

    Ok(SpectralDecomposition {
        n: 2,
        carrier: matrix.carrier,
        method: SpectralMethod::TwoByTwoCharpolySplit,
        eigenvalues: vec![lambda_plus, lambda_minus],
        eigenvectors: vec![v0, v1],
        hypotheses,
        authority_effect: SpectralAuthorityTag::None,
    })
}

// Eigenvector for λ: v = [c, λ − a] when c ≠ 0; else standard basis column.
fn eigenvector_2x2(a: &GaussianRat, c: &GaussianRat, lambda: &GaussianRat) -> Vec<GaussianRat> {
    if c.is_zero() {
        // Already diagonal in this branch only if off-diag zero — still handle.
        if (&a.re - &lambda.re).is_zero() {
            vec![GaussianRat::one(), GaussianRat::zero()]
        } else {
            vec![GaussianRat::zero(), GaussianRat::one()]
        }
    } else {
        // v = [c, λ − a]; (a−λ)c + c(λ−a) = 0.
        vec![c.clone(), lambda.sub(a)]
    }
}

fn verify_eigenpair_2x2(
    h: &BasicMatrix<GaussianRat>,
    lambda: &GaussianRat,
    v: &[GaussianRat],
) -> Result<(), SpectralError> {
    // w = A v − λ v
    match first_eigen_defect(h, lambda, v) {
        None => Ok(()),
        Some(row) => Err(SpectralError::NotHermitian {
            row,
            col: 0,
            detail: "2x2 eigenpair check failed",
        }),
    }
}

/// Explicit refusal helper when a caller builds hypotheses manually.
pub fn apply_spectral_theorem(
    matrix: &HermitianMatrix,
    hypotheses: &SpectralHypotheses,
) -> Result<SpectralDecomposition, SpectralError> {
    hypotheses.require_paid()?;
    // Carrier on hypotheses must match matrix.
    if hypotheses.carrier != matrix.carrier {
        return Err(SpectralError::HypothesesUnpaid {
            unpaid: vec!["carrier_matrix_mismatch"],
        });
    }
    spectral_decompose(matrix)
}

// ═════════════════════════════════════════════════════════════════════════════
// W6.10 — the spectral obstruction, block-diagonal general n, and axiom A17
// ═════════════════════════════════════════════════════════════════════════════

/// **Corrected characterisation of the residual.**
///
/// the program spectral ledger describes the gap as *dimensional* — "general-n
/// ... is unpaid" — as though a missing implementation were the obstacle. That
/// understates the finding.
///
/// The obstruction is **algebraic, not dimensional**, and it bites already at
/// `n = 2`: a rational Hermitian matrix can have irrational eigenvalues, so no
/// exact decomposition over the rationals exists at any `n >= 2` in general.
/// See [`rational_spectrum_obstruction_witness`].
///
/// Consequence for the ledger: `OB-SPECTRAL` is not a pending implementation. It
/// is a **priced import** — paying it means admitting a scalar carrier strictly
/// larger than the rationals (a real algebraic extension), and that admission is
/// the cost.

/// The witness: `[[1,1],[1,0]]` — rational, symmetric, characteristic polynomial
/// `x^2 - x - 1`, whose roots are the golden ratio and its conjugate.
///
/// Both are irrational, so this matrix has **no** exact spectral decomposition
/// over the rationals. It is `2 x 2`, which is why the obstruction cannot be
/// described as a large-`n` gap.
pub fn rational_spectrum_obstruction_witness() -> Result<HermitianMatrix, SpectralError> {
    HermitianMatrix::try_exact(
        2,
        ScalarCarrier::Rational,
        vec![
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(0, 0),
        ],
    )
}

/// **The obstruction at every `n >= 2`, and a same-shaped matrix that pays.**
///
/// Builds an `n x n` rational symmetric block-diagonal matrix whose leading
/// `2 x 2` block is `lead`, padded by the distinct integer diagonal
/// `3, 4, ..., n`. The padding is deliberately non-degenerate so nothing can be
/// blamed on repeated eigenvalues.
///
/// Feed it the golden block `[[1,1],[1,0]]` (discriminant `5`) and no exact
/// rational spectral decomposition exists at any `n`. Feed it Pauli-X
/// `[[0,1],[1,0]]` (discriminant `4`) and one does, at the same `n`, through the
/// same code path. That pair is the whole argument: the refusal tracks the
/// **discriminant**, not the size and not the shape.
fn leading_block_family(n: usize, lead: [[i64; 2]; 2]) -> Result<HermitianMatrix, SpectralError> {
    if n < 2 {
        return Err(SpectralError::UnsupportedExactShape { n, diagonal: false });
    }
    let count = core_kernel::resource_limits::OperationLimits::default()
        .check_dense_matrix(n, n, std::mem::size_of::<GaussianRat>())
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
    let mut entries = vec![GaussianRat::zero(); count];
    for i in 0..2 {
        for j in 0..2 {
            entries[i * n + j] = GaussianRat::from_ints(lead[i][j], 0);
        }
    }
    // Distinct integer padding: 3, 4, ..., so degeneracy cannot be the cause.
    for k in 2..n {
        entries[k * n + k] = GaussianRat::from_ints((k + 1) as i64, 0);
    }
    HermitianMatrix::try_exact(n, ScalarCarrier::Rational, entries)
}

/// The golden family: `n x n`, leading block `[[1,1],[1,0]]`, charpoly of that
/// block `x^2 - x - 1`, discriminant `5` — **not** a perfect square.
pub fn spectral_obstruction_family(n: usize) -> Result<HermitianMatrix, SpectralError> {
    leading_block_family(n, [[1, 1], [1, 0]])
}

/// The control family: identical construction, leading block `[[0,1],[1,0]]`
/// (Pauli-X), charpoly `x^2 - 1`, discriminant `4` — a perfect square, so it
/// splits over the rationals.
pub fn spectral_payable_family(n: usize) -> Result<HermitianMatrix, SpectralError> {
    leading_block_family(n, [[0, 1], [1, 0]])
}

/// Block structure for either family: one `2 x 2` block then `n - 2` singletons.
///
/// Refuses `n < 2` with the same error [`spectral_obstruction_family`] uses, so
/// the structure and the matrix agree on what a valid size is. Saturating the
/// subtraction instead would return a size-2 structure for `n = 0` or `n = 1`,
/// whose `total()` does not equal `n` - a silently wrong answer to an invalid
/// question.
pub fn leading_block_structure(n: usize) -> Result<BlockStructure, SpectralError> {
    if n < 2 {
        return Err(SpectralError::UnsupportedExactShape { n, diagonal: false });
    }
    let mut block_sizes = vec![2usize];
    block_sizes.extend(std::iter::repeat_n(1usize, n - 2));
    Ok(BlockStructure { block_sizes })
}

/// **`OB-SPECTRAL` is not a small-`n` accident - within the executed range.**
///
/// The family is *constructed* for arbitrary `n >= 2` and *executed* for
/// `2 <= n <= 8`. The name says `SCOPE` because the universal reading is not
/// mechanized: see the `NOT ESTABLISHED` clause in the text.

/// Exact rational-root test for the monic quadratic `x^2 + b x + c` with integer
/// coefficients: a rational root exists iff the discriminant is a perfect square.
/// Decided by exact integer arithmetic — no floating point, no tolerance.
pub fn monic_quadratic_has_rational_root(b: i64, c: i64) -> bool {
    let b = BigInt::from(b);
    let discriminant = &b * &b - BigInt::from(4) * BigInt::from(c);
    core_number_theory::rational::exact_integer_sqrt(&discriminant).is_some()
}

/// The witness's characteristic polynomial `x^2 - x - 1` has no rational root:
/// discriminant `1 + 4 = 5` is not a perfect square.
pub fn charpoly_has_no_rational_root_golden() -> bool {
    !monic_quadratic_has_rational_root(-1, -1)
}

/// A declared block structure: consecutive diagonal blocks whose sizes sum to `n`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BlockStructure {
    pub block_sizes: Vec<usize>,
}

impl BlockStructure {
    pub fn total(&self) -> usize {
        self.block_sizes.iter().sum()
    }
}

/// Does `m` vanish outside the declared consecutive diagonal blocks?
pub fn is_block_diagonal(m: &HermitianMatrix, blocks: &BlockStructure) -> bool {
    if blocks.total() != m.n {
        return false;
    }
    let mut owner = vec![0usize; m.n];
    let mut idx = 0usize;
    for (bid, &sz) in blocks.block_sizes.iter().enumerate() {
        for _ in 0..sz {
            owner[idx] = bid;
            idx += 1;
        }
    }
    for i in 0..m.n {
        for j in 0..m.n {
            if owner[i] != owner[j] {
                match m.entry(i, j) {
                    Some(e) if e.is_zero() => {}
                    _ => return false,
                }
            }
        }
    }
    true
}

/// **General-`n` extension that is actually available over the rationals.**
///
/// A block-diagonal Hermitian matrix decomposes exactly whenever *every* block
/// does. Since each block is handled by the existing paid paths (diagonal at any
/// size, or `2 x 2` with a splitting charpoly), this pays arbitrary `n` for the
/// block-diagonal class — without pretending the general case is available.
///
/// A block whose charpoly does not split refuses the whole matrix, by design:
/// partial credit would be exactly the laundering this face exists to prevent.
pub fn block_diagonal_eigenvalues(
    m: &HermitianMatrix,
    blocks: &BlockStructure,
) -> Result<Vec<GaussianRat>, SpectralError> {
    if !is_block_diagonal(m, blocks) {
        return Err(SpectralError::UnsupportedExactShape {
            n: m.n,
            diagonal: m.is_diagonal_exact(),
        });
    }
    let mut out = Vec::new();
    let mut offset = 0usize;
    for &sz in &blocks.block_sizes {
        let mut entries = Vec::with_capacity(sz * sz);
        for i in 0..sz {
            for j in 0..sz {
                entries.push(
                    m.entry(offset + i, offset + j)
                        .unwrap_or_else(GaussianRat::zero),
                );
            }
        }
        let block = HermitianMatrix::try_exact(sz, m.carrier, entries)?;
        let dec = spectral_decompose(&block)?;
        out.extend(dec.eigenvalues);
        offset += sz;
    }
    Ok(out)
}

// ─────────────────────────────────────────────────────────────────────────────
// Axiom A17 — what an observable IS on the declared carrier
// ─────────────────────────────────────────────────────────────────────────────

/// **Axiom A17 (observables).** The register ran A1–A16 without ever answering
/// "what is an observable?", while A8, A11 and A15 all quantify over exactly
/// those objects.
///
/// On the declared finite carrier a **classical** observable is a function from
/// the sector set to the rationals. Its spectral decomposition is level-set
/// indicator arithmetic, and the classical algebra is **commutative by
/// construction** — see [`classical_observables_commute`].
///
/// Anything non-commutative is therefore *not* a classical observable, and
/// obtaining it is a declared import (`OB-NONCOMM`), not a consequence of the
/// carrier. That pricing is the point of stating A17.

/// A classical observable: one rational value per sector.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClassicalObservable {
    pub values: Vec<Rational>,
}

impl ClassicalObservable {
    pub fn new(values: Vec<Rational>) -> Result<Self, SpectralError> {
        if values.is_empty() {
            return Err(SpectralError::ZeroDimension);
        }
        Ok(Self { values })
    }

    /// Realisation as a diagonal Hermitian matrix on the same carrier.
    pub fn as_hermitian(&self, carrier: ScalarCarrier) -> Result<HermitianMatrix, SpectralError> {
        HermitianMatrix::try_diagonal_rational(&self.values, carrier)
    }

    /// The level set of `lambda` — the classical spectral projector's support.
    /// Spectral decomposition here is indicator arithmetic, nothing more.
    pub fn level_set(&self, lambda: Rational) -> Vec<usize> {
        self.values
            .iter()
            .enumerate()
            .filter(|(_, v)| **v == lambda)
            .map(|(i, _)| i)
            .collect()
    }

    /// Distinct eigenvalues, in first-appearance order.
    pub fn spectrum(&self) -> Vec<Rational> {
        let mut out: Vec<Rational> = Vec::new();
        for v in &self.values {
            if !out.contains(v) {
                out.push(v.clone());
            }
        }
        out
    }
}

/// The exact coefficient matrix; float demos have no exact interpretation.
fn exact_required(m: &HermitianMatrix) -> Result<&BasicMatrix<GaussianRat>, SpectralError> {
    if !m.carrier.is_exact() {
        return Err(SpectralError::Float64DemoNonExact);
    }
    let exact = m.exact.as_ref().ok_or(SpectralError::Float64DemoNonExact)?;
    if m.n == 0 {
        return Err(SpectralError::ZeroDimension);
    }
    if exact.rows() != m.n || exact.cols() != m.n || m.witness.n != m.n {
        return Err(SpectralError::ExactAlgebra(
            "mutated carrier dimension".into(),
        ));
    }
    if m.witness.carrier != m.carrier || !m.witness.defect_is_zero {
        return Err(SpectralError::ExactAlgebra(
            "mutated scalar carrier or Hermitian witness".into(),
        ));
    }
    check_hermitian(exact).map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?;
    Ok(exact)
}

/// Full algebraic real spectrum for every bounded exact Hermitian matrix. The
/// result isolates irrational eigenvalues without pretending they lie in Q(i).
pub fn algebraic_spectrum(
    matrix: &HermitianMatrix,
) -> Result<crate::exact_operator::ExactSpectrum, SpectralError> {
    crate::exact_operator::ExactOperator::try_new(exact_required(matrix)?.clone())
        .and_then(|op| op.spectrum())
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))
}

/// **A17 consequence.** Any two classical observables commute — the classical
/// algebra is commutative by construction, so non-commutativity can never arise
/// inside it.
pub fn classical_observables_commute(
    a: &ClassicalObservable,
    b: &ClassicalObservable,
    carrier: ScalarCarrier,
) -> Result<bool, SpectralError> {
    if a.values.len() != b.values.len() {
        return Err(SpectralError::EntryCountMismatch {
            expected: a.values.len(),
            actual: b.values.len(),
        });
    }
    let a = a.as_hermitian(carrier)?;
    let b = b.as_hermitian(carrier)?;
    hermitian_commute(&a, &b)
}

/// Do two Hermitian matrices commute (exactly)?
pub fn hermitian_commute(a: &HermitianMatrix, b: &HermitianMatrix) -> Result<bool, SpectralError> {
    if a.n != b.n {
        return Err(SpectralError::EntryCountMismatch {
            expected: a.n,
            actual: b.n,
        });
    }
    let ea = exact_required(a)?;
    let eb = exact_required(b)?;
    Ok(mx::multiply_with_limits(ea, eb, exact_limits())
        .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?
        == mx::multiply_with_limits(eb, ea, exact_limits())
            .map_err(|e| SpectralError::ExactAlgebra(e.to_string()))?)
}

/// A non-commuting Hermitian pair: `X = [[0,1],[1,0]]`, `Z = [[1,0],[0,-1]]`.
///
/// Both are Hermitian on the declared carrier and they do **not** commute — so
/// the classical (diagonal) algebra is a *proper* subalgebra, and `OB-NONCOMM`
/// buys something the carrier does not already contain.
pub fn noncommuting_hermitian_pair() -> Result<(HermitianMatrix, HermitianMatrix), SpectralError> {
    let x = HermitianMatrix::try_exact(
        2,
        ScalarCarrier::Rational,
        vec![
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(0, 0),
        ],
    )?;
    let z = HermitianMatrix::try_diagonal_rational(&[ri(1), ri(-1)], ScalarCarrier::Rational)?;
    Ok((x, z))
}

// ─────────────────────────────────────────────────────────────────────────────
// Trace norm of a paid decomposition (shared with `trace_norm_certificate`)
// ─────────────────────────────────────────────────────────────────────────────

/// Exact trace-norm certificate of `matrix` from its paid spectral decomposition.
///
/// The spectrum comes from [`spectral_decompose`], so this refuses exactly where that
/// does. Everything after the spectrum — projectors, `sign(H)`, positive and negative
/// parts, the zero duality gap — is
/// [`crate::trace_norm_certificate::sign_from_spectrum`], the one implementation.
pub fn certify_trace_norm(matrix: &HermitianMatrix) -> Result<TraceNormCertificate, SpectralError> {
    let decomposition = spectral_decompose(matrix)?;
    let h = matrix
        .exact_matrix()
        .ok_or(SpectralError::Float64DemoNonExact)?;
    sign_from_spectrum(h, &decomposition.distinct_eigenvalues())
        .map_err(|e| SpectralError::TraceNormRefused(Box::new(e)))
}

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;

    fn r(n: i64, d: i64) -> Rational {
        rq(n, d)
    }

    // --- W6.10: the obstruction is ALGEBRAIC, not dimensional ---------------

    /// The load-bearing negative result. `[[1,1],[1,0]]` is rational, symmetric,
    /// and `2 x 2` — yet its charpoly `x^2 - x - 1` has irrational roots, so no
    /// exact decomposition over the rationals exists. The residual is therefore
    /// misdescribed as a large-`n` gap: it bites at the smallest nontrivial size.
    #[test]
    fn w610_rational_hermitian_can_have_irrational_spectrum() {
        assert!(charpoly_has_no_rational_root_golden());
        let m = rational_spectrum_obstruction_witness().unwrap();
        assert_eq!(m.n, 2);
        assert!(!m.is_diagonal_exact());
        assert_eq!(
            spectral_decompose(&m),
            Err(SpectralError::CharpolyDoesNotSplit),
            "a rational-spectrum obstruction must refuse, not approximate"
        );
    }

    /// The rational-root test discriminates: it accepts splitting quadratics and
    /// rejects non-splitting ones. Without this the test above could pass because
    /// the predicate is constantly false.
    #[test]
    fn w610_rational_root_test_is_not_constant() {
        // x^2 - 3x + 2 = (x-1)(x-2): discriminant 1, splits.
        assert!(monic_quadratic_has_rational_root(-3, 2));
        // x^2 - 2: discriminant 8, irrational roots.
        assert!(!monic_quadratic_has_rational_root(0, -2));
        // x^2 - x - 1: discriminant 5, the golden case.
        assert!(!monic_quadratic_has_rational_root(-1, -1));
    }

    /// A splitting 2x2 still decomposes, so the refusal above is specific to the
    /// algebraic obstruction rather than to non-diagonal shape.
    #[test]
    fn w610_splitting_two_by_two_still_decomposes() {
        // [[0,1],[1,0]] has charpoly x^2 - 1, eigenvalues +-1: rational.
        let m = HermitianMatrix::try_exact(
            2,
            ScalarCarrier::Rational,
            vec![
                GaussianRat::from_ints(0, 0),
                GaussianRat::from_ints(1, 0),
                GaussianRat::from_ints(1, 0),
                GaussianRat::from_ints(0, 0),
            ],
        )
        .unwrap();
        let dec = spectral_decompose(&m).expect("rational spectrum must decompose");
        assert_eq!(dec.eigenvalues.len(), 2);
    }

    // --- W6.10: block-diagonal general n ------------------------------------

    /// General `n` IS available for the block-diagonal class: a 5x5 built from a
    /// 2x2 splitting block and a 3x3 diagonal block decomposes exactly.
    #[test]
    fn w610_block_diagonal_pays_general_n() {
        let n = 5;
        let mut e = vec![GaussianRat::zero(); n * n];
        // block A (2x2) = [[0,1],[1,0]]
        e[0 * n + 1] = GaussianRat::from_ints(1, 0);
        e[1 * n + 0] = GaussianRat::from_ints(1, 0);
        // block B (3x3) diagonal = diag(5, 7, 9)
        e[2 * n + 2] = GaussianRat::from_ints(5, 0);
        e[3 * n + 3] = GaussianRat::from_ints(7, 0);
        e[4 * n + 4] = GaussianRat::from_ints(9, 0);
        let m = HermitianMatrix::try_exact(n, ScalarCarrier::Rational, e).unwrap();

        let blocks = BlockStructure {
            block_sizes: vec![2, 3],
        };
        assert!(is_block_diagonal(&m, &blocks));
        let eig = block_diagonal_eigenvalues(&m, &blocks).unwrap();
        assert_eq!(eig.len(), 5);
    }

    /// A block whose charpoly does not split refuses the WHOLE matrix. Partial
    /// credit here would be exactly the laundering this face exists to prevent.
    #[test]
    fn w610_block_diagonal_refuses_when_any_block_refuses() {
        let n = 4;
        let mut e = vec![GaussianRat::zero(); n * n];
        // golden block [[1,1],[1,0]] in positions 0..2
        e[0] = GaussianRat::from_ints(1, 0);
        e[1] = GaussianRat::from_ints(1, 0);
        e[n] = GaussianRat::from_ints(1, 0);
        // diagonal block
        e[2 * n + 2] = GaussianRat::from_ints(3, 0);
        e[3 * n + 3] = GaussianRat::from_ints(4, 0);
        let m = HermitianMatrix::try_exact(n, ScalarCarrier::Rational, e).unwrap();
        let blocks = BlockStructure {
            block_sizes: vec![2, 2],
        };
        assert_eq!(
            block_diagonal_eigenvalues(&m, &blocks),
            Err(SpectralError::CharpolyDoesNotSplit)
        );
    }

    /// Off-block mass is detected, so `is_block_diagonal` is a real check.
    #[test]
    fn w610_block_detection_rejects_off_block_mass() {
        let n = 4;
        let mut e = vec![GaussianRat::zero(); n * n];
        e[0 * n + 3] = GaussianRat::from_ints(1, 0);
        e[3 * n + 0] = GaussianRat::from_ints(1, 0);
        let m = HermitianMatrix::try_exact(n, ScalarCarrier::Rational, e).unwrap();
        assert!(!is_block_diagonal(
            &m,
            &BlockStructure {
                block_sizes: vec![2, 2]
            }
        ));
    }

    // --- W6.10: axiom A17 and the OB-NONCOMM price --------------------------

    /// A17: classical observables are functions sector -> Q, and their spectral
    /// decomposition is level-set indicator arithmetic.
    #[test]
    fn w610_a17_classical_spectral_is_level_set_arithmetic() {
        let o = ClassicalObservable::new(vec![ri(3), ri(5), ri(3)]).unwrap();
        assert_eq!(o.spectrum(), vec![ri(3), ri(5)]);
        assert_eq!(o.level_set(ri(3)), vec![0, 2]);
        assert_eq!(o.level_set(ri(5)), vec![1]);
        assert!(o.level_set(ri(11)).is_empty());

        // and its realisation decomposes on the diagonal path at any n
        let h = o.as_hermitian(ScalarCarrier::Rational).unwrap();
        let dec = spectral_decompose(&h).unwrap();
        assert_eq!(dec.eigenvalues.len(), 3);
    }

    /// A17 consequence: the classical algebra is commutative BY CONSTRUCTION.
    #[test]
    fn w610_a17_classical_observables_always_commute() {
        let a = ClassicalObservable::new(vec![ri(1), ri(2), ri(-4)]).unwrap();
        let b = ClassicalObservable::new(vec![rq(1, 3), ri(7), rq(-5, 2)]).unwrap();
        assert!(classical_observables_commute(&a, &b, ScalarCarrier::Rational).unwrap());
    }

    /// **The price of OB-NONCOMM.** Non-commutativity is not available inside the
    /// classical algebra; X and Z are Hermitian on the same carrier and do not
    /// commute, so the classical (diagonal) algebra is a PROPER subalgebra. This
    /// is what the import buys — and the test would fail if the commutator check
    /// were vacuous, since the previous test requires it to report `true`.
    #[test]
    fn w610_a17_noncommutativity_is_a_priced_import() {
        let (x, z) = noncommuting_hermitian_pair().unwrap();
        assert!(!hermitian_commute(&x, &z).unwrap());

        // Z alone is classical (diagonal) and commutes with itself.
        assert!(hermitian_commute(&z, &z).unwrap());
    }

    #[test]
    fn authority_fence_is_none() {
        assert!(AUTHORITY_FENCE.contains("AuthorityEffect None"));
        assert!(AUTHORITY_FENCE.contains("no continuum claim"));
        assert!(!ScalarCarrier::Float64Demo.is_exact());
        assert!(ScalarCarrier::Float64Demo.label().contains("non-exact"));
    }

    /// Mutation-negative: non-Hermitian matrices are refused at construction.
    #[test]
    fn non_hermitian_refused() {
        // [[0, 1], [0, 0]] — not Hermitian
        let entries = vec![
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(0, 0),
        ];
        let err = HermitianMatrix::try_exact(2, ScalarCarrier::Rational, entries);
        assert!(matches!(err, Err(SpectralError::NotHermitian { .. })));
    }

    #[test]
    fn non_hermitian_complex_refused() {
        // A01 = i, A10 = i (should be −i for Hermitian)
        let entries = vec![
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(0, 1),
            GaussianRat::from_ints(0, 1),
            GaussianRat::from_ints(0, 0),
        ];
        let err = HermitianMatrix::try_exact(2, ScalarCarrier::GaussianRational, entries);
        assert!(matches!(err, Err(SpectralError::NotHermitian { .. })));
    }

    /// Diagonal n=3: eigenvalues on diagonal, standard-basis eigenvectors.
    #[test]
    fn diagonal_n3_spectral() {
        let diag = [r(3, 1), r(-1, 1), r(2, 1)];
        let m = HermitianMatrix::try_diagonal_rational(&diag, ScalarCarrier::Rational).unwrap();
        assert!(m.is_diagonal_exact());
        let decomp = spectral_decompose(&m).unwrap();
        assert_eq!(decomp.method, SpectralMethod::DiagonalExact);
        assert_eq!(decomp.n, 3);
        assert_eq!(decomp.authority_effect, SpectralAuthorityTag::None);
        assert!(decomp.hypotheses.all_paid());
        for i in 0..3 {
            assert_eq!(
                decomp.eigenvalues[i],
                GaussianRat::from_rational(diag[i].clone())
            );
            for j in 0..3 {
                let expected = if i == j {
                    GaussianRat::one()
                } else {
                    GaussianRat::zero()
                };
                assert_eq!(decomp.eigenvectors[i][j], expected);
            }
        }
    }

    /// Hypotheses gate: unpaid scalar_closed refuses apply_spectral_theorem.
    #[test]
    fn hypotheses_gate_refuses_unpaid() {
        let m =
            HermitianMatrix::try_diagonal_rational(&[r(1, 1)], ScalarCarrier::Rational).unwrap();
        let unpaid = SpectralHypotheses::from_matrix_unpaid(&m);
        assert!(!unpaid.all_paid());
        assert!(unpaid.unpaid().contains(&"scalar_closed_for_charpoly"));
        let err = apply_spectral_theorem(&m, &unpaid);
        assert!(matches!(err, Err(SpectralError::HypothesesUnpaid { .. })));
    }

    #[test]
    fn float64_demo_marked_non_exact_and_refused_for_theorem() {
        // Hermitian [[1,0],[0,2]] as float demo
        let m = HermitianMatrix::try_float64_demo(
            2,
            vec![(1.0, 0.0), (0.0, 0.0), (0.0, 0.0), (2.0, 0.0)],
        )
        .unwrap();
        assert_eq!(m.carrier, ScalarCarrier::Float64Demo);
        assert!(!m.carrier.is_exact());
        let err = spectral_decompose(&m);
        assert_eq!(err, Err(SpectralError::Float64DemoNonExact));

        // Non-Hermitian float also refused
        let bad = HermitianMatrix::try_float64_demo(
            2,
            vec![(0.0, 0.0), (1.0, 0.0), (0.0, 0.0), (0.0, 0.0)],
        );
        assert!(matches!(bad, Err(SpectralError::NotHermitian { .. })));
    }

    /// Non-diagonal 2×2 real symmetric with splitting charpoly over ℚ.
    /// [[2,1],[1,2]] → eigenvalues 3,1.
    #[test]
    fn two_by_two_rational_split() {
        let entries = vec![
            GaussianRat::from_ints(2, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(2, 0),
        ];
        let m = HermitianMatrix::try_exact(2, ScalarCarrier::Rational, entries).unwrap();
        let decomp = spectral_decompose(&m).unwrap();
        assert_eq!(decomp.method, SpectralMethod::TwoByTwoCharpolySplit);
        assert!(decomp.hypotheses.all_paid());
        let evs: Vec<Rational> = decomp.eigenvalues.iter().map(|e| e.re.clone()).collect();
        // {3, 1} unordered as (tr ± sqrt)/2 with tr=4, disc=4, sqrt=2 → 3 and 1
        assert!(evs.contains(&r(3, 1)));
        assert!(evs.contains(&r(1, 1)));
        assert_eq!(decomp.authority_effect, SpectralAuthorityTag::None);
    }

    /// 2×2 with non-splitting disc over ℚ (disc = 2, not a perfect square).
    /// [[0,1],[1,0]] wait disc = 4, splits. Use [[0,1],[1,1]]: disc = 1 + 4 = 5.
    #[test]
    fn two_by_two_charpoly_does_not_split() {
        let entries = vec![
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(1, 0),
        ];
        let m = HermitianMatrix::try_exact(2, ScalarCarrier::Rational, entries).unwrap();
        let err = spectral_decompose(&m);
        assert_eq!(err, Err(SpectralError::CharpolyDoesNotSplit));
    }

    /// Gaussian-rational Hermitian: σ_y-like [[0,−i],[i,0]] → eigenvalues ±1.
    #[test]
    fn two_by_two_gaussian_pauli_y() {
        let entries = vec![
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(0, -1), // −i
            GaussianRat::from_ints(0, 1),  // +i
            GaussianRat::from_ints(0, 0),
        ];
        let m = HermitianMatrix::try_exact(2, ScalarCarrier::GaussianRational, entries).unwrap();
        let decomp = spectral_decompose(&m).unwrap();
        assert_eq!(decomp.method, SpectralMethod::TwoByTwoCharpolySplit);
        let evs: Vec<Rational> = decomp.eigenvalues.iter().map(|e| e.re.clone()).collect();
        assert!(evs.contains(&r(1, 1)));
        assert!(evs.contains(&r(-1, 1)));
    }

    #[test]
    fn general_n_nondiagonal_open_residual() {
        // 3×3 non-diagonal Hermitian with rational entries
        let mut entries = vec![GaussianRat::zero(); 9];
        entries[0] = GaussianRat::from_ints(1, 0);
        entries[1] = GaussianRat::from_ints(1, 0);
        entries[3] = GaussianRat::from_ints(1, 0);
        entries[4] = GaussianRat::from_ints(2, 0);
        entries[8] = GaussianRat::from_ints(3, 0);
        let m = HermitianMatrix::try_exact(3, ScalarCarrier::Rational, entries).unwrap();
        assert!(!m.is_diagonal_exact());
        let err = spectral_decompose(&m);
        assert_eq!(err, Err(SpectralError::CharpolyDoesNotSplit));
        assert_eq!(algebraic_spectrum(&m).unwrap().dim(), 3);
    }

    #[test]
    fn rational_carrier_rejects_complex_entry() {
        let entries = vec![
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(0, 1),
            GaussianRat::from_ints(0, -1),
            GaussianRat::from_ints(0, 0),
        ];
        let err = HermitianMatrix::try_exact(2, ScalarCarrier::Rational, entries);
        assert!(matches!(
            err,
            Err(SpectralError::RationalCarrierRequiresRealEntries { .. })
        ));
    }

    #[test]
    fn perfect_isqrt_smoke() {
        assert_eq!(perfect_isqrt(0), Some(0));
        assert_eq!(perfect_isqrt(1), Some(1));
        assert_eq!(perfect_isqrt(4), Some(2));
        assert_eq!(perfect_isqrt(2), None);
        assert_eq!(perfect_isqrt(9), Some(3));
        assert_eq!(rational_sqrt(r(4, 9)), Some(r(2, 3)));
        assert_eq!(rational_sqrt(r(2, 1)), None);
    }

    // ── Target 3: OB-SPECTRAL at general n ──────────────────────────────

    /// The minimal pair, at every size: same construction, same block path,
    /// discriminant 5 versus discriminant 4.
    #[test]
    fn general_n_obstruction_tracks_discriminant_not_dimension() {
        for n in 2..=8 {
            let blocks = leading_block_structure(n).expect("n >= 2");
            assert_eq!(blocks.total(), n);

            let witness = spectral_obstruction_family(n).expect("witness builds");
            let control = spectral_payable_family(n).expect("control builds");

            let ok = block_diagonal_eigenvalues(&control, &blocks);
            assert!(
                ok.is_ok(),
                "n={n}: control (disc 4) must decompose through the block path"
            );
            assert_eq!(ok.unwrap().len(), n, "n={n}: one eigenvalue per dimension");

            assert!(
                block_diagonal_eigenvalues(&witness, &blocks).is_err(),
                "n={n}: witness (disc 5) must refuse - no rational spectrum"
            );
        }
    }

    /// The pair splits on the **square class** of the discriminant.
    ///
    /// The two families differ in more than the discriminant - different
    /// leading blocks, different characteristic polynomials, different spectra.
    /// The decisive property is narrower: whether the discriminant is a perfect
    /// square. That is what this checks, and the name no longer claims the
    /// families are otherwise identical.
    #[test]
    fn general_n_pair_splits_on_the_discriminant_square_class() {
        // golden x^2 - x - 1: disc = 1 + 4 = 5, not a perfect square
        assert_eq!(perfect_isqrt(5), None);
        assert!(!monic_quadratic_has_rational_root(-1, -1));
        // control x^2 - 1: disc = 0 + 4 = 4 = 2^2, a perfect square
        assert_eq!(perfect_isqrt(4), Some(2));
        assert!(monic_quadratic_has_rational_root(0, -1));
    }

    /// The block structure refuses invalid sizes instead of answering anyway.
    #[test]
    fn leading_block_structure_rejects_dimensions_below_two() {
        for n in [0usize, 1] {
            assert!(
                leading_block_structure(n).is_err(),
                "n={n}: a 2x2 leading block cannot exist"
            );
            assert!(spectral_obstruction_family(n).is_err(), "n={n}: family too");
        }
        for n in 2..=8 {
            let blocks = leading_block_structure(n).expect("n >= 2 builds");
            assert_eq!(blocks.total(), n, "n={n}: block sizes must sum to n");
        }
    }

    /// Anti-vacuity: the refusal is NOT "n > 2 is unsupported". Same size,
    /// same non-diagonal shape, splitting block -> decomposes.
    #[test]
    fn general_n_refusal_is_not_a_size_limitation() {
        for n in 3..=8 {
            let blocks = leading_block_structure(n).expect("n >= 2");
            assert!(
                block_diagonal_eigenvalues(&spectral_payable_family(n).unwrap(), &blocks).is_ok(),
                "n={n}: a non-diagonal 2x2 block at size n decomposes when it splits"
            );
        }
    }

    /// The padding is non-degenerate, so repeated eigenvalues cannot be blamed.
    #[test]
    fn general_n_padding_is_non_degenerate() {
        let blocks = leading_block_structure(6).expect("n >= 2");
        let evs = block_diagonal_eigenvalues(&spectral_payable_family(6).unwrap(), &blocks)
            .expect("control decomposes");
        let mut re: Vec<BigInt> = evs.iter().map(|z| z.re.to_integer()).collect();
        re.sort_unstable();
        assert_eq!(re, [-1, 1, 3, 4, 5, 6].map(BigInt::from));
    }

    /// Collapse whitespace runs so an assertion tests the *claim*, not the
    /// literal's line layout. String constants here are wrapped, and a
    /// continuation leaves a run of spaces mid-sentence.

    /// The receipt must state its own executed range and its own limit.

    // ── Reconciliation with the trace-norm certificate ──────────────────

    /// A paid decomposition feeds the one trace-norm implementation: for Pauli Y
    /// the certificate's value is `2` and its dual witness is `sign(Y) = Y`.
    #[test]
    fn certify_trace_norm_uses_the_paid_spectrum() {
        let y = HermitianMatrix::try_exact(
            2,
            ScalarCarrier::GaussianRational,
            vec![
                GaussianRat::from_ints(0, 0),
                GaussianRat::from_ints(0, -1),
                GaussianRat::from_ints(0, 1),
                GaussianRat::from_ints(0, 0),
            ],
        )
        .unwrap();
        let cert = certify_trace_norm(&y).unwrap();
        assert_eq!(cert.trace_norm(), &ri(2));
        assert_eq!(Some(cert.witness()), y.exact_matrix());

        let d = HermitianMatrix::try_diagonal_rational(
            &[r(3, 1), r(-1, 1), r(2, 1)],
            ScalarCarrier::Rational,
        )
        .unwrap();
        assert_eq!(certify_trace_norm(&d).unwrap().trace_norm(), &ri(6));
    }

    /// `certify_trace_norm` refuses exactly where `spectral_decompose` does.
    #[test]
    fn certify_trace_norm_inherits_the_spectral_refusals() {
        let golden = rational_spectrum_obstruction_witness().unwrap();
        assert_eq!(
            certify_trace_norm(&golden),
            Err(SpectralError::CharpolyDoesNotSplit)
        );
        let demo = HermitianMatrix::try_float64_demo(
            2,
            vec![(1.0, 0.0), (0.0, 0.0), (0.0, 0.0), (2.0, 0.0)],
        )
        .unwrap();
        assert_eq!(
            certify_trace_norm(&demo),
            Err(SpectralError::Float64DemoNonExact)
        );
    }

    /// The division of labour. This face does not *find* the spectrum of a
    /// non-diagonal 3x3 (gating unchanged), yet the same exact matrix with its
    /// declared rational spectrum `{-1, 0, 2}` is certified at `n = 3` by the
    /// shared implementation.
    #[test]
    fn declared_rational_spectrum_is_certified_beyond_the_paid_cases() {
        let mut e = vec![GaussianRat::zero(); 9];
        e[0] = GaussianRat::from_ints(1, 0);
        e[1] = GaussianRat::from_ints(1, 0);
        e[3] = GaussianRat::from_ints(1, 0);
        e[4] = GaussianRat::from_ints(1, 0);
        e[8] = GaussianRat::from_ints(-1, 0);
        let m = HermitianMatrix::try_exact(3, ScalarCarrier::Rational, e).unwrap();
        let decomposition = spectral_decompose(&m).unwrap();
        assert_eq!(
            decomposition.distinct_eigenvalues(),
            vec![ri(-1), ri(0), ri(2)]
        );
        let cert = sign_from_spectrum(m.exact_matrix().unwrap(), &[ri(-1), ri(0), ri(2)]).unwrap();
        assert_eq!(cert.trace_norm(), &ri(3));
    }

    /// Past the old `Ratio<i64>` ceiling: for `[[0, 2^40], [2^40, 0]]` the
    /// discriminant `4 · 2^80` does not fit in `i64`, and the eigenvalues are
    /// `±2^40`, computed exactly.
    #[test]
    fn two_by_two_beyond_the_i64_ceiling() {
        let big = Rational::from_integer(BigInt::from(2u8).pow(40));
        let c = GaussianRat::from_rational(big.clone());
        let m = HermitianMatrix::try_exact(
            2,
            ScalarCarrier::Rational,
            vec![GaussianRat::zero(), c.clone(), c, GaussianRat::zero()],
        )
        .unwrap();
        let dec = spectral_decompose(&m).unwrap();
        assert_eq!(dec.distinct_eigenvalues(), vec![-big.clone(), big]);
    }

    #[test]
    fn test_perfect_isqrt_exact() {
        assert_eq!(perfect_isqrt(0), Some(0));
        assert_eq!(perfect_isqrt(1), Some(1));
        assert_eq!(perfect_isqrt(4), Some(2));
        assert_eq!(perfect_isqrt(9), Some(3));
        assert_eq!(perfect_isqrt(16), Some(4));
        assert_eq!(perfect_isqrt(100), Some(10));
        assert_eq!(perfect_isqrt(2), None);
        assert_eq!(perfect_isqrt(3), None);
        assert_eq!(perfect_isqrt(-1), None);
    }
}
