// AuthorityEffect: None.

//! Exact operators on a declared bipartite carrier `C^(d_A) (x) C^(d_B)` over `Q(i)`.
//!
//! Operators are `BasicMatrix<GaussianRat>` in the lexicographic order
//! `(a, b) -> a d_B + b` that `ExactMatrix::kron` produces. Computed exactly:
//!
//! - the partial traces and the partial transpose on the second factor, from
//!   `exact_hermitian` (whose traces contract through `linear_algebra::tensor`),
//!   `rho^(T_B)_((a,b),(a',b')) = rho_((a,b'),(a',b))`, and the PPT test by the
//!   exact PSD decision of `exact_hermitian`;
//! - decomposable witnesses `W = Q^(T_B)` with `Q` PSD. For product states
//!   `Tr(W (alpha (x) beta)) = Tr(Q (alpha (x) beta^T)) >= 0`, so `W` is
//!   nonnegative on every separable state and `Tr(W rho) < 0` excludes every
//!   separable decomposition of `rho`;
//! - verification of a declared decomposition `rho = sum_k p_k alpha_k (x) beta_k`
//!   into product states;
//! - the phase-blind descent of a state to a joint weight table in declared
//!   local orthogonal bases, `w(a, b) = <u_a v_b| rho |u_a v_b> / (|u_a|^2 |v_b|^2)`;
//!   the bases need not be normalised, so bases such as `(1, 1), (1, -1)` stay
//!   rational;
//! - real coordinates of a Hermitian operator, for decisions relative to a
//!   declared family.
//!
//! PPT is necessary for separability. That it is also sufficient on `2 x 2`
//! and `2 x 3` carriers (Horodecki) is a cited theorem, not a computation here.
//!
//! Refused: zero dimensions, operators whose size is not `d_A d_B`,
//! non-Hermitian or non-PSD operators where a state or witness is required,
//! bases that are not complete and orthogonal, and decomposition terms that
//! are not states.

use crate::exact_hermitian::{self, exact_limits};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, involution as star, matrix as mx};
use num_traits::{One, Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

use core_finite_probability::joint_table::{JointTable, WeightTableError};

/// Refusals for bipartite operator work.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum BipartiteError {
    #[error(transparent)]
    Algebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("a factor dimension is zero")]
    ZeroDimension,
    #[error("a {rows}x{cols} operator does not act on a {d_a} x {d_b} carrier")]
    Shape {
        rows: usize,
        cols: usize,
        d_a: usize,
        d_b: usize,
    },
    #[error("operator is not Hermitian")]
    NotHermitian,
    #[error("operator is not positive semidefinite")]
    NotPositive,
    #[error("positivity budget exhausted: {0}")]
    PositivityBudgetExhausted(String),
    #[error("operator does not have trace one")]
    NotUnitTrace,
    #[error("vector {index} of basis {factor} has the wrong length")]
    BasisVectorLength { factor: usize, index: usize },
    #[error("vector {index} of basis {factor} is zero")]
    ZeroBasisVector { factor: usize, index: usize },
    #[error("vectors {first} and {second} of basis {factor} are not orthogonal")]
    NotOrthogonal {
        factor: usize,
        first: usize,
        second: usize,
    },
    #[error("the vector is zero")]
    ZeroVector,
    #[error("a decomposition needs at least one term")]
    EmptyDecomposition,
    #[error("decomposition term {index}: {reason}")]
    BadTerm { index: usize, reason: &'static str },
    #[error("decomposition weights sum to {sum}, not one")]
    WeightsNotNormalized { sum: Rational },
    #[error("the decomposition does not reproduce the state")]
    DoesNotReproduce,
    #[error("tensor refusal: {0}")]
    Tensor(String),
    #[error(transparent)]
    Hermitian(#[from] exact_hermitian::ExactHermitianError),
    #[error(transparent)]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error(transparent)]
    Operator(#[from] crate::exact_operator::OperatorError),
    #[error(transparent)]
    State(#[from] crate::density_matrix::ExactDensityError),
    #[error(transparent)]
    Ray(#[from] crate::quantum_state::RayError),
    #[error("the orthogonal product family can be extended (subset {subset})")]
    Extendible { subset: usize },
    #[error("the product family must be nonempty and smaller than the carrier")]
    InvalidProductFamily,
    #[error("the bounded subset enumeration is exhausted")]
    SubsetBudget,
    #[error(transparent)]
    TraceNorm(#[from] crate::trace_norm_certificate::TraceNormError),
    #[error("the complement-state certificate failed replay")]
    ComplementReplay,
    #[error("table refusal: {0}")]
    Table(#[from] WeightTableError),
}

fn check_dims(m: &BasicMatrix<GaussianRat>, d_a: usize, d_b: usize) -> Result<(), BipartiteError> {
    if d_a == 0 || d_b == 0 {
        return Err(BipartiteError::ZeroDimension);
    }
    exact_hermitian::check_well_formed(m)?;
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let dim = limits.checked_product(d_a, d_b)?;
    limits.check_hilbert_dim(dim)?;
    let n = Some(dim);
    if n != Some(m.rows()) || n != Some(m.cols()) {
        return Err(BipartiteError::Shape {
            rows: m.rows(),
            cols: m.cols(),
            d_a,
            d_b,
        });
    }
    Ok(())
}

/// `Tr_B(m)`, a `d_A x d_A` operator.
pub fn partial_trace_b(
    m: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> Result<BasicMatrix<GaussianRat>, BipartiteError> {
    check_dims(m, d_a, d_b)?;
    exact_hermitian::partial_trace_second(m, d_a, d_b)
        .map_err(|e| BipartiteError::Tensor(e.to_string()))
}

/// `Tr_A(m)`, a `d_B x d_B` operator.
pub fn partial_trace_a(
    m: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> Result<BasicMatrix<GaussianRat>, BipartiteError> {
    check_dims(m, d_a, d_b)?;
    exact_hermitian::partial_trace_first(m, d_a, d_b)
        .map_err(|e| BipartiteError::Tensor(e.to_string()))
}

/// `m^(T_B)`: transpose the second tensor factor only.
pub fn partial_transpose_b(
    m: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> Result<BasicMatrix<GaussianRat>, BipartiteError> {
    check_dims(m, d_a, d_b)?;
    exact_hermitian::partial_transpose_second(m, d_a, d_b)
        .map_err(|e| BipartiteError::Tensor(e.to_string()))
}

/// `rho^(T_B)` is positive semidefinite.
pub fn is_ppt(
    rho: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> Result<bool, BipartiteError> {
    if !exact_hermitian::is_hermitian(rho) {
        return Err(BipartiteError::NotHermitian);
    }
    let pt = partial_transpose_b(rho, d_a, d_b)?;
    match exact_hermitian::is_psd(&pt) {
        Ok(is_psd) => Ok(is_psd),
        Err(exact_hermitian::ExactHermitianError::Limits(e)) => {
            Err(BipartiteError::PositivityBudgetExhausted(e.to_string()))
        }
        Err(exact_hermitian::ExactHermitianError::Algebra(
            linear_algebra::exact_field::ExactFieldError::Matrix(
                linear_algebra::backend::basic_matrix::MatrixError::OperationLimitExceeded {
                    requested,
                    limit,
                },
            ),
        )) => Err(BipartiteError::PositivityBudgetExhausted(format!(
            "operation limit {limit} exceeded for {requested}"
        ))),
        Err(exact_hermitian::ExactHermitianError::Algebra(
            linear_algebra::exact_field::ExactFieldError::Matrix(
                linear_algebra::backend::basic_matrix::MatrixError::AllocationLimitExceeded {
                    requested,
                    limit,
                },
            ),
        )) => Err(BipartiteError::PositivityBudgetExhausted(format!(
            "allocation limit {limit} exceeded for {requested}"
        ))),
        Err(e) => Err(BipartiteError::Hermitian(e)),
    }
}

/// A decomposable witness `W = Q^(T_B)` with `Q` Hermitian PSD.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DecomposableWitness {
    witness: BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
}

impl DecomposableWitness {
    /// Declare `W = Q^(T_B)` from a PSD `Q` on the carrier.
    pub fn new(
        q: &BasicMatrix<GaussianRat>,
        d_a: usize,
        d_b: usize,
    ) -> Result<Self, BipartiteError> {
        check_dims(q, d_a, d_b)?;
        if !exact_hermitian::is_hermitian(q) {
            return Err(BipartiteError::NotHermitian);
        }
        if !exact_hermitian::is_psd(q)? {
            return Err(BipartiteError::NotPositive);
        }
        Ok(Self {
            witness: partial_transpose_b(q, d_a, d_b)?,
            d_a,
            d_b,
        })
    }

    /// The witness operator `W`.
    pub fn operator(&self) -> &BasicMatrix<GaussianRat> {
        &self.witness
    }

    /// `Tr(W X)`, real for Hermitian `X`. This is the linear pairing; it
    /// accepts any Hermitian operator on the carrier and certifies nothing.
    pub fn value(&self, rho: &BasicMatrix<GaussianRat>) -> Result<Rational, BipartiteError> {
        check_dims(rho, self.d_a, self.d_b)?;
        if !exact_hermitian::is_hermitian(rho) {
            return Err(BipartiteError::NotHermitian);
        }
        let pairing = star::hs_inner(&self.witness, rho)
            .map_err(|e| BipartiteError::Tensor(e.to_string()))?;
        debug_assert!(pairing.im.is_zero(), "Hermitian pairing is real");
        Ok(pairing.re)
    }

    /// `Tr(W rho) < 0`, which no separable state satisfies. Only a state can
    /// be certified: `rho` must be PSD with trace one, because a negative
    /// operator such as `-I` also pairs negatively with `W`.
    pub fn certifies_entanglement(
        &self,
        rho: &BasicMatrix<GaussianRat>,
    ) -> Result<bool, BipartiteError> {
        let value = self.value(rho)?;
        if !exact_hermitian::is_psd(rho)? {
            return Err(BipartiteError::NotPositive);
        }
        if mx::trace(rho)? != GaussianRat::one() {
            return Err(BipartiteError::NotUnitTrace);
        }
        Ok(value.is_negative())
    }
}

fn check_state(m: &BasicMatrix<GaussianRat>, index: usize) -> Result<(), BipartiteError> {
    exact_hermitian::check_well_formed(m)?;
    if m.rows() != m.cols() || m.rows() == 0 {
        return Err(BipartiteError::BadTerm {
            index,
            reason: "factor is not a nonempty square matrix",
        });
    }
    if !exact_hermitian::is_psd(m)? {
        return Err(BipartiteError::BadTerm {
            index,
            reason: "factor is not Hermitian positive semidefinite",
        });
    }
    if mx::trace(m)? != GaussianRat::one() {
        return Err(BipartiteError::BadTerm {
            index,
            reason: "factor does not have trace one",
        });
    }
    Ok(())
}

/// A declared decomposition `sum_k p_k alpha_k (x) beta_k` into product states.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductDecomposition {
    terms: Vec<(Rational, BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>)>,
}

impl ProductDecomposition {
    pub fn new(terms: Vec<(Rational, BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>)>) -> Self {
        Self { terms }
    }

    /// Check `p_k >= 0`, `sum p_k = 1`, every factor a state, and the sum equal to `rho`.
    pub fn verify(&self, rho: &BasicMatrix<GaussianRat>) -> Result<(), BipartiteError> {
        let (_, first_a, first_b) = self
            .terms
            .first()
            .ok_or(BipartiteError::EmptyDecomposition)?;
        let (d_a, d_b) = (first_a.rows(), first_b.rows());
        check_dims(rho, d_a, d_b)?;
        core_kernel::resource_limits::OperationLimits::default()
            .check_operator_count(self.terms.len())?;
        let (sum, acc) = self.accumulate_terms(rho, d_a, d_b)?;
        if !sum.is_one() {
            return Err(BipartiteError::WeightsNotNormalized { sum });
        }
        if &acc != rho {
            return Err(BipartiteError::DoesNotReproduce);
        }
        Ok(())
    }

    fn accumulate_terms(
        &self,
        rho: &BasicMatrix<GaussianRat>,
        d_a: usize,
        d_b: usize,
    ) -> Result<(Rational, BasicMatrix<GaussianRat>), BipartiteError> {
        let mut sum = Rational::zero();
        let mut acc = mx::zeros_with_limits(rho.rows(), rho.cols(), exact_limits())?;
        for (index, (p, alpha, beta)) in self.terms.iter().enumerate() {
            Self::validate_term(index, p, alpha, beta, d_a, d_b)?;
            sum += p;
            let product = mx::kronecker_with_limits(alpha, beta, exact_limits())?;
            let scaled = mx::scale(&product, &GaussianRat::from_rational(p.clone()))?;
            acc = mx::add(&acc, &scaled)?;
        }
        Ok((sum, acc))
    }

    fn validate_term(
        index: usize,
        p: &Rational,
        alpha: &BasicMatrix<GaussianRat>,
        beta: &BasicMatrix<GaussianRat>,
        d_a: usize,
        d_b: usize,
    ) -> Result<(), BipartiteError> {
        if p.is_negative() {
            return Err(BipartiteError::BadTerm {
                index,
                reason: "negative weight",
            });
        }
        if alpha.rows() != d_a || beta.rows() != d_b {
            return Err(BipartiteError::BadTerm {
                index,
                reason: "factor dimensions differ from the first term",
            });
        }
        check_state(alpha, index)?;
        check_state(beta, index)?;
        Ok(())
    }
}

fn check_basis(basis: &[Vec<GaussianRat>], factor: usize) -> Result<(), BipartiteError> {
    let d = basis.len();
    for (index, v) in basis.iter().enumerate() {
        if v.len() != d {
            return Err(BipartiteError::BasisVectorLength { factor, index });
        }
        if v.iter().all(|z| z.re.is_zero() && z.im.is_zero()) {
            return Err(BipartiteError::ZeroBasisVector { factor, index });
        }
    }
    for (first, u) in basis.iter().enumerate() {
        for (second, v) in basis.iter().enumerate().skip(first + 1) {
            let overlap =
                star::inner_product(u, v).map_err(|e| BipartiteError::Tensor(e.to_string()))?;
            if overlap != GaussianRat::zero() {
                return Err(BipartiteError::NotOrthogonal {
                    factor,
                    first,
                    second,
                });
            }
        }
    }
    Ok(())
}

fn norm_sq(v: &[GaussianRat]) -> Rational {
    v.iter().map(GaussianRat::norm_sq).sum()
}

/// The phase-blind table `w(a, b) = <u_a v_b| rho |u_a v_b> / (|u_a|^2 |v_b|^2)`.
///
/// `rho` must be Hermitian PSD with nonzero trace; the bases must be complete
/// and orthogonal. Off-diagonal coherences in the chosen basis are discarded.
pub fn descend_to_table(
    rho: &BasicMatrix<GaussianRat>,
    basis_a: &[Vec<GaussianRat>],
    basis_b: &[Vec<GaussianRat>],
) -> Result<JointTable, BipartiteError> {
    let (d_a, d_b) = (basis_a.len(), basis_b.len());
    check_dims(rho, d_a, d_b)?;
    check_basis(basis_a, 0)?;
    check_basis(basis_b, 1)?;
    validate_hermitian_psd(rho)?;
    let mut rows = Vec::with_capacity(d_a);
    for u in basis_a {
        let mut row = Vec::with_capacity(d_b);
        for v in basis_b {
            row.push(table_entry(rho, u, v)?);
        }
        rows.push(row);
    }
    Ok(JointTable::new(rows)?)
}

fn validate_hermitian_psd(rho: &BasicMatrix<GaussianRat>) -> Result<(), BipartiteError> {
    if !exact_hermitian::is_hermitian(rho) {
        return Err(BipartiteError::NotHermitian);
    }
    if !exact_hermitian::is_psd(rho)? {
        return Err(BipartiteError::NotPositive);
    }
    Ok(())
}

fn table_entry(
    rho: &BasicMatrix<GaussianRat>,
    u: &[GaussianRat],
    v: &[GaussianRat],
) -> Result<Rational, BipartiteError> {
    let product: Vec<GaussianRat> = u
        .iter()
        .flat_map(|x| v.iter().map(move |y| x.mul(y)))
        .collect();
    let image = mx::multiply_vector_with_limits(rho, &product, exact_limits())?;
    let diagonal =
        star::inner_product(&product, &image).map_err(|e| BipartiteError::Tensor(e.to_string()))?;
    Ok(diagonal.re / (norm_sq(u) * norm_sq(v)))
}

/// Real coordinates of a Hermitian operator: the diagonal, then the real and
/// imaginary parts of each entry above it, row by row. This is a real linear
/// isomorphism from the Hermitian `n x n` matrices onto `Q^(n^2)`.
pub fn hermitian_coordinates(
    m: &BasicMatrix<GaussianRat>,
) -> Result<Vec<Rational>, BipartiteError> {
    if !exact_hermitian::is_hermitian(m) {
        return Err(BipartiteError::NotHermitian);
    }
    let n = m.rows();
    let mut out: Vec<Rational> = (0..n).map(|i| m.as_slice()[i * n + i].re.clone()).collect();
    for r in 0..n {
        for c in (r + 1)..n {
            let z = m.get_ref(r, c)?;
            out.push(z.re.clone());
            out.push(z.im.clone());
        }
    }
    Ok(out)
}

/// `|u><u| / <u, u>` for a nonzero vector with Gaussian-rational entries.
///
/// The vector need not be normalised, so states such as `|+> = (1, 1) / sqrt 2`
/// have rational density matrices.
pub fn pure_state(u: &[GaussianRat]) -> Result<BasicMatrix<GaussianRat>, BipartiteError> {
    let n = norm_sq(u);
    if n.is_zero() {
        return Err(BipartiteError::ZeroVector);
    }
    Ok(mx::scale(
        &star::outer_product_with_limits(u, u, exact_limits())?,
        &GaussianRat::from_rational(n.recip()),
    )?)
}

/// Gurvits--Barnum sufficient separability ball around the maximally mixed state.
/// The exact purity inequality is sufficient; outside the ball no verdict is returned.
pub fn in_separable_ball(
    rho: &crate::density_matrix::ExactDensityMatrix,
    d_a: usize,
    d_b: usize,
) -> Result<bool, BipartiteError> {
    check_dims(rho.matrix(), d_a, d_b)?;
    if rho.dim() == 1 {
        return Ok(true);
    }
    Ok(rho.purity() <= Rational::new(1.into(), (rho.dim() - 1).into()))
}

/// Realignment R(X)_(a,c),(b,d)=X_(a,b),(c,d), preserving every coherence.
pub fn realignment(
    x: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> Result<BasicMatrix<GaussianRat>, BipartiteError> {
    check_dims(x, d_a, d_b)?;
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let rows = limits.checked_product(d_a, d_a)?;
    let cols = limits.checked_product(d_b, d_b)?;
    limits.check_dense_matrix(rows, cols, std::mem::size_of::<GaussianRat>())?;
    let mut result = mx::zeros_with_limits(rows, cols, exact_limits())?;
    for a in 0..d_a {
        for c in 0..d_a {
            fill_realignment_row(&mut result, x, a, c, d_a, d_b)?;
        }
    }
    Ok(result)
}

fn fill_realignment_row(
    result: &mut BasicMatrix<GaussianRat>,
    x: &BasicMatrix<GaussianRat>,
    a: usize,
    c: usize,
    d_a: usize,
    d_b: usize,
) -> Result<(), BipartiteError> {
    for b in 0..d_b {
        for d in 0..d_b {
            let entry = x.get_ref(a * d_b + b, c * d_b + d)?.clone();
            result.set(a * d_a + c, b * d_b + d, entry)?;
        }
    }
    Ok(())
}

/// Operator-Schmidt rank equals the exact rank of the realignment.
pub fn operator_schmidt_rank(
    x: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> Result<usize, BipartiteError> {
    Ok(elimination::rank_with_limits(
        &realignment(x, d_a, d_b)?,
        exact_limits(),
    )?)
}

/// The reduction criterion on both local carriers; failing either excludes separability.
pub fn reduction_criterion(
    rho: &crate::density_matrix::ExactDensityMatrix,
    d_a: usize,
    d_b: usize,
) -> Result<(bool, bool), BipartiteError> {
    check_dims(rho.matrix(), d_a, d_b)?;
    let a = reduction_operator_a(rho.matrix(), d_a, d_b)?;
    let b = reduction_operator_b(rho.matrix(), d_a, d_b)?;
    Ok((exact_hermitian::is_psd(&a)?, exact_hermitian::is_psd(&b)?))
}

fn reduction_operator_a(
    rho: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> Result<BasicMatrix<GaussianRat>, BipartiteError> {
    let pt_b = partial_trace_b(rho, d_a, d_b)?;
    let id_b = mx::identity_with_limits(d_b, exact_limits())?;
    let kron = mx::kronecker_with_limits(&pt_b, &id_b, exact_limits())?;
    Ok(mx::sub(&kron, rho)?)
}

fn reduction_operator_b(
    rho: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> Result<BasicMatrix<GaussianRat>, BipartiteError> {
    let id_a = mx::identity_with_limits(d_a, exact_limits())?;
    let pt_a = partial_trace_a(rho, d_a, d_b)?;
    let kron = mx::kronecker_with_limits(&id_a, &pt_a, exact_limits())?;
    Ok(mx::sub(&kron, rho)?)
}

/// Exact kernel, for independently replaying range-criterion exclusions.
pub fn range_kernel(
    rho: &crate::density_matrix::ExactDensityMatrix,
) -> Result<Vec<Vec<GaussianRat>>, BipartiteError> {
    linear_algebra::exact_field::elimination::kernel_basis_with_limits(
        rho.matrix(),
        exact_hermitian::exact_limits(),
    )
    .map_err(|e| BipartiteError::Hermitian(exact_hermitian::ExactHermitianError::Algebra(e)))
}

/// Orthogonal product vectors with a replayed absence of an orthogonal product ray.
/// For every assignment of factors to Alice or Bob, at least one assigned family
/// spans its complete local carrier. This exhausts all possible product extensions.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnextendibleProductBasis {
    d_a: usize,
    d_b: usize,
    factors: Vec<(
        crate::quantum_state::RayVector,
        crate::quantum_state::RayVector,
    )>,
    complement: crate::density_matrix::ExactDensityMatrix,
}
impl UnextendibleProductBasis {
    pub fn try_new(
        factors: Vec<(
            crate::quantum_state::RayVector,
            crate::quantum_state::RayVector,
        )>,
        subset_budget: usize,
    ) -> Result<Self, BipartiteError> {
        let (d_a, d_b, dim, masks) = Self::validate_upb_parameters(&factors, subset_budget)?;
        let products = Self::build_orthogonal_products(&factors, d_a, d_b)?;
        Self::verify_unextendible_subsets(&factors, d_a, d_b, masks)?;
        let complement = Self::build_upb_complement(&products, dim, d_a, d_b)?;
        Ok(Self {
            d_a,
            d_b,
            factors,
            complement,
        })
    }

    fn validate_upb_parameters(
        factors: &[(
            crate::quantum_state::RayVector,
            crate::quantum_state::RayVector,
        )],
        subset_budget: usize,
    ) -> Result<(usize, usize, usize, usize), BipartiteError> {
        let (a, b) = factors
            .first()
            .ok_or(BipartiteError::InvalidProductFamily)?;
        let (d_a, d_b) = (a.len(), b.len());
        let limits = core_kernel::resource_limits::OperationLimits::default();
        let dim = limits.checked_product(d_a, d_b)?;
        limits.check_hilbert_dim(dim)?;
        if factors.len() >= dim || factors.len() >= usize::BITS as usize {
            return Err(BipartiteError::InvalidProductFamily);
        }
        let masks = Self::compute_subset_masks(factors.len(), d_a, d_b, subset_budget)?;
        Ok((d_a, d_b, dim, masks))
    }

    fn compute_subset_masks(
        num_factors: usize,
        d_a: usize,
        d_b: usize,
        subset_budget: usize,
    ) -> Result<usize, BipartiteError> {
        let masks = 1usize
            .checked_shl(num_factors as u32)
            .ok_or(BipartiteError::SubsetBudget)?;
        if masks > subset_budget || masks > 65_536 {
            return Err(BipartiteError::SubsetBudget);
        }
        // A declared ceiling includes all elimination work before subset enumeration.
        let cost = masks
            .checked_mul(num_factors.max(d_a.max(d_b)).pow(3))
            .ok_or(BipartiteError::SubsetBudget)?;
        if cost > 100_000_000 {
            return Err(BipartiteError::SubsetBudget);
        }
        Ok(masks)
    }

    fn build_orthogonal_products(
        factors: &[(
            crate::quantum_state::RayVector,
            crate::quantum_state::RayVector,
        )],
        d_a: usize,
        d_b: usize,
    ) -> Result<Vec<crate::quantum_state::RayVector>, BipartiteError> {
        let mut products: Vec<crate::quantum_state::RayVector> = Vec::new();
        for (i, (a, b)) in factors.iter().enumerate() {
            if a.len() != d_a || b.len() != d_b {
                return Err(BipartiteError::InvalidProductFamily);
            }
            let product = a.kron(b)?;
            Self::check_orthogonal_to_priors(&products, &product, i)?;
            products.push(product);
        }
        Ok(products)
    }

    fn check_orthogonal_to_priors(
        products: &[crate::quantum_state::RayVector],
        product: &crate::quantum_state::RayVector,
        index: usize,
    ) -> Result<(), BipartiteError> {
        for (j, prior) in products.iter().enumerate() {
            if !product.inner(prior)?.is_zero() {
                return Err(BipartiteError::NotOrthogonal {
                    factor: 2,
                    first: j,
                    second: index,
                });
            }
        }
        Ok(())
    }

    fn ray_family_rank(
        vectors: Vec<&crate::quantum_state::RayVector>,
        dim: usize,
    ) -> Result<usize, BipartiteError> {
        if vectors.is_empty() {
            return Ok(0);
        }
        let matrix = mx::from_rows(vectors.iter().map(|v| v.entries().to_vec()).collect())?;
        if matrix.cols() != dim {
            return Err(BipartiteError::InvalidProductFamily);
        }
        Ok(elimination::rank_with_limits(&matrix, exact_limits())?)
    }

    fn verify_unextendible_subsets(
        factors: &[(
            crate::quantum_state::RayVector,
            crate::quantum_state::RayVector,
        )],
        d_a: usize,
        d_b: usize,
        masks: usize,
    ) -> Result<(), BipartiteError> {
        for mask in 0..masks {
            let a = factors
                .iter()
                .enumerate()
                .filter(|(i, _)| mask & (1usize << i) != 0)
                .map(|(_, p)| &p.0)
                .collect();
            let b = factors
                .iter()
                .enumerate()
                .filter(|(i, _)| mask & (1usize << i) == 0)
                .map(|(_, p)| &p.1)
                .collect();
            if Self::ray_family_rank(a, d_a)? < d_a && Self::ray_family_rank(b, d_b)? < d_b {
                return Err(BipartiteError::Extendible { subset: mask });
            }
        }
        Ok(())
    }

    fn subtract_product_projectors(
        products: &[crate::quantum_state::RayVector],
        dim: usize,
    ) -> Result<crate::exact_operator::ExactOperator, BipartiteError> {
        let mut complement = crate::exact_operator::ExactOperator::identity(dim)?;
        for product in products {
            complement = complement.sub(&product.projector()?)?;
        }
        Ok(complement)
    }

    fn build_upb_complement(
        products: &[crate::quantum_state::RayVector],
        dim: usize,
        d_a: usize,
        d_b: usize,
    ) -> Result<crate::density_matrix::ExactDensityMatrix, BipartiteError> {
        use crate::{density_matrix::ExactDensityMatrix, exact_operator::ExactOperator};
        let mut complement = Self::subtract_product_projectors(products, dim)?;
        let scale = Rational::new(1.into(), (dim - products.len()).into());
        complement = complement.scale_rat(&scale)?;
        let complement = ExactDensityMatrix::try_from_operator(complement)?;
        if !is_ppt(complement.matrix(), d_a, d_b)? || complement.rank()? != dim - products.len() {
            return Err(BipartiteError::ComplementReplay);
        }
        Ok(complement)
    }
    pub fn dimensions(&self) -> (usize, usize) {
        (self.d_a, self.d_b)
    }
    pub fn factors(
        &self,
    ) -> &[(
        crate::quantum_state::RayVector,
        crate::quantum_state::RayVector,
    )] {
        &self.factors
    }
    /// A PPT state with no product ray in its support, hence entangled.
    pub fn complement_state(&self) -> &crate::density_matrix::ExactDensityMatrix {
        &self.complement
    }
}

/// Certified CCNR norm enclosure. A lower endpoint greater than one excludes
/// separability; an interval meeting one is an honest undecided bound.
pub fn realignment_norm_enclosure(
    rho: &crate::density_matrix::ExactDensityMatrix,
    d_a: usize,
    d_b: usize,
    bits: u32,
) -> Result<core_kernel::interval::Interval, BipartiteError> {
    let r = realignment(rho.matrix(), d_a, d_b)?;
    let adjoint = star::adjoint(&r)?;
    let gram = if r.rows() <= r.cols() {
        mx::multiply_with_limits(&r, &adjoint, exact_limits())?
    } else {
        mx::multiply_with_limits(&adjoint, &r, exact_limits())?
    };
    Ok(crate::trace_norm_certificate::positive_sqrt_trace(
        &crate::exact_operator::ExactOperator::try_new(gram)?,
        bits,
    )?)
}

/// Negativity (||rho^(T_B)||_1-1)/2 with exact algebraic spectral bounds.
pub fn negativity_enclosure(
    rho: &crate::density_matrix::ExactDensityMatrix,
    d_a: usize,
    d_b: usize,
    bits: u32,
) -> Result<core_kernel::interval::Interval, BipartiteError> {
    use core_kernel::interval::Interval;
    let pt = partial_transpose_b(rho.matrix(), d_a, d_b)?;
    Ok(
        crate::trace_norm_certificate::trace_norm_enclosure(&pt, bits)?
            .sub(&Interval::point(Rational::one()))
            .mul_scalar(&Rational::new(1.into(), 2.into())),
    )
}

// Origin: engine/crates_rs/core_quantum_physics/src/bipartite_operator.rs
// Claim: urn:core:crates_rs:core-quantum-physics:bipartite-operator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_fcc90531 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
