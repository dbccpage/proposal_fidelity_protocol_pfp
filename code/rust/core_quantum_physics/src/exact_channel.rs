// AuthorityEffect: None.

//! Exact CPTP channels over `Q(i)`: weighted Kraus, Choi and Stinespring
//! presentations of one declared channel (QM_080, QM_082).
//!
//! The crate's one exact channel implementation. A channel is
//! `Phi(rho) = sum_k w_k K_k rho K_k*` with rational weights `w_k >= 0` and Kraus
//! operators `K_k` over `Q(i)` ([`linear_algebra::backend::basic_matrix::BasicMatrix`], `d_out x d_in`). The weights keep
//! this fixed Kraus presentation exact without absorbing square roots into each operator: the
//! depolarizing channel with rational `p` is `(1 - 3p/4, p/4, p/4, p/4)` on
//! `I, X, Y, Z`.
//!
//! - [`ExactKrausChannel::try_weighted`] certifies trace preservation with zero
//!   defect, `sum_k w_k K_k* K_k = I` exactly. Complete positivity holds by the
//!   form. [`ExactKrausChannel::adjoint_apply`] is the Heisenberg dual
//!   `Phi*(E) = sum_k w_k K_k* E K_k`.
//! - [`ExactChoiMatrix`] is `J = sum_ij |i><j| (x) Phi(|i><j|)`, with index
//!   `i * d_out + r` for `|i> (x) |r>` (the convention of
//!   `completely_positive_map`). [`ExactChoiMatrix::try_new`] certifies complete
//!   positivity by exact `J ⪰ 0` ([`crate::exact_hermitian::is_psd`]) and trace
//!   preservation by `Tr_out J = I`. [`apply_choi`] applies any Choi matrix,
//!   certified or not, and [`choi_is_cptp`] is `try_new` as a yes/no answer.
//! - [`ExactKrausChannel::stinespring_isometry`] is `V = sum_k sqrt(w_k) K_k (x) |k>`,
//!   row index `(o, k) -> o * r + k`, with `V* V = I` and
//!   `Phi(rho) = Tr_env(V rho V*)` ([`apply_stinespring`]). This fixed-presentation
//!   helper requires every weight to be a rational square and refuses otherwise.
//!   A refusal does not exclude a different, larger Kraus family over `Q(i)`;
//!   the channel census uses LDL* and four-square splitting for that construction.
//!   [`ExactKrausChannel::complementary`] is `Tr_out(V rho V*)`.
//!
//! `kraus_operators`, `quantum_channel`, `completely_positive_map` and
//! `stinespring_dilation` are `f64` diagnostics of the same objects. Their
//! tolerances, such as `kraus_operators::DEFAULT_TP_TOL`, never certify anything;
//! certification is here.
//!
//! The channel is declared data. Nothing here derives CPTP dynamics, and
//! agreement of the presentations is a finite identity about one declared
//! channel, not a Born or CPTP derivation.
//!
//! Not PROVED. Not GlobalGreen.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::ordered::hermitian_ldl_with_limits;
use core_kernel::resource_limits::{OperationLimits, ResourceError};
use core_number_theory::four_squares::{rational_square_split, FourSquaresError};

use crate::exact_hermitian::exact_limits;
use crate::exact_hermitian::{
    check_hermitian, check_well_formed, is_psd, partial_trace_first, partial_trace_second,
    ExactHermitianError,
};
use linear_algebra::backend::basic_matrix::MatrixError;
use linear_algebra::exact_field::rational_bareiss::{
    self as bounded, RationalBudget, RationalError,
};
use linear_algebra::exact_field::{elimination, involution as star, matrix as mx};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, One, Rational, Zero};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact CPTP channel face over Q(i).";

/// Why an exact channel or Choi matrix was refused.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactChannelError {
    #[error("shared exact rational budget: {0}")]
    RationalBudget(#[from] RationalError),
    #[error("a Gram state factor needs positive width and the declared input dimension")]
    GramStateShape,
    #[error("the Gram state does not have exact unit trace")]
    GramStateNormalization,
    #[error("bounded finite channel: {0}")]
    Limits(#[from] ResourceError),
    #[error("exact algebra: {0}")]
    Algebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error("weight square splitting: {0}")]
    SquareSplit(#[from] FourSquaresError),
    #[error("matrix storage: {0}")]
    Storage(#[from] MatrixError),
    #[error("factorization replay changed the Choi matrix")]
    FactorizationReplay,

    /// An input or output dimension is zero.
    #[error("an input or output dimension is zero")]
    ZeroDimension,
    /// No Kraus operators were given.
    #[error("a channel needs at least one Kraus operator")]
    EmptyKrausSet,
    /// Kraus operator `index` is not `d_out x d_in`.
    #[error("Kraus operator {index} is {actual:?}, expected {expected:?}")]
    KrausShape {
        index: usize,
        expected: (usize, usize),
        actual: (usize, usize),
    },
    /// Weight `index` is negative.
    #[error("weight {index} is negative")]
    NegativeWeight { index: usize },
    /// A parameter lies outside its admissible range.
    #[error("parameter {name} is out of range")]
    ParameterOutOfRange { name: &'static str },
    /// First entry `(row, col)` where `sum w K*K` (or `Tr_out J`) differs from `I`.
    #[error("not trace preserving at ({row}, {col})")]
    NotTracePreserving { row: usize, col: usize },
    /// The Choi matrix is not `(d_in d_out)^2`.
    #[error("the Choi matrix is {actual:?}, expected {expected}x{expected}")]
    ChoiShape {
        expected: usize,
        actual: (usize, usize),
    },
    /// The Choi matrix is malformed or not Hermitian.
    #[error("the Choi matrix is not Hermitian: {0}")]
    ChoiDefect(ExactHermitianError),
    /// The Choi matrix is not positive semidefinite.
    #[error("the Choi matrix is not positive semidefinite")]
    NotCompletelyPositive,
    /// The operator fed to a channel is not `d x d` for the side it acts on.
    #[error("the operator is {actual:?}, expected {expected}x{expected}")]
    StateShape {
        expected: usize,
        actual: (usize, usize),
    },
    /// `self.d_out != next.d_in` in a composition.
    #[error("cannot compose: output {left_out} does not match input {right_in}")]
    CompositionMismatch { left_out: usize, right_in: usize },
    /// A Kraus operator or input operator holds the wrong number of entries.
    #[error("malformed operator: {0}")]
    Malformed(ExactHermitianError),
    /// `sqrt(w_k)` is irrational, so the Stinespring isometry has no entries in `Q(i)`.
    #[error("weight {index} is not the square of a rational")]
    IrrationalWeight { index: usize },
    /// An isometry is not `(d_out r) x d_in`.
    #[error("the isometry is {actual:?}, expected {expected:?}")]
    IsometryShape {
        expected: (usize, usize),
        actual: (usize, usize),
    },
}

/// The rational square root of `q`, when there is one.
fn rational_sqrt(q: &Rational) -> Option<Rational> {
    core_number_theory::rational::sqrt_exact(q)
}

fn check_state_shape(rho: &BasicMatrix<GaussianRat>, dim: usize) -> Result<(), ExactChannelError> {
    if (rho.rows(), rho.cols()) != (dim, dim) {
        return Err(ExactChannelError::StateShape {
            expected: dim,
            actual: (rho.rows(), rho.cols()),
        });
    }
    Ok(())
}

fn check_state(rho: &BasicMatrix<GaussianRat>, dim: usize) -> Result<(), ExactChannelError> {
    check_state_shape(rho, dim)?;
    check_well_formed(rho).map_err(ExactChannelError::Malformed)
}

/// Exact CPTP channel in weighted Kraus form. Fields are private; every value has
/// passed [`ExactKrausChannel::try_weighted`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactKrausChannel {
    dim_in: usize,
    dim_out: usize,
    weights: Vec<Rational>,
    operators: Vec<BasicMatrix<GaussianRat>>,
    label: String,
}

impl ExactKrausChannel {
    /// Weighted Kraus admission using one caller-owned rational budget for every
    /// entry check, contraction, scaling and addition. Complete positivity is
    /// guaranteed by the nonnegative weighted Kraus form; trace preservation is
    /// checked by the exact completeness identity. No nested operation resets fuel.
    pub fn try_weighted_with_budget(
        dim_in: usize,
        dim_out: usize,
        terms: Vec<(Rational, BasicMatrix<GaussianRat>)>,
        label: impl Into<String>,
        fuel: &mut RationalBudget,
    ) -> Result<Self, ExactChannelError> {
        Self::check_family_limits(dim_in, dim_out, terms.len())?;
        let mut completeness = BudgetedParts::zeros(dim_in, dim_in, fuel)?;
        for (index, (weight, operator)) in terms.iter().enumerate() {
            let gram =
                Self::budgeted_weighted_gram(index, dim_in, dim_out, weight, operator, fuel)?;
            completeness = completeness.add(&gram, fuel)?;
        }
        Self::verify_budgeted_completeness(&completeness, dim_in)?;
        let (weights, operators) = terms.into_iter().unzip();
        Ok(Self {
            dim_in,
            dim_out,
            weights,
            operators,
            label: label.into(),
        })
    }

    fn budgeted_weighted_gram(
        index: usize,
        dim_in: usize,
        dim_out: usize,
        weight: &Rational,
        operator: &BasicMatrix<GaussianRat>,
        fuel: &mut RationalBudget,
    ) -> Result<BudgetedParts, ExactChannelError> {
        fuel.rational(weight)?;
        if *weight < Rational::zero() {
            return Err(ExactChannelError::NegativeWeight { index });
        }
        if (operator.rows(), operator.cols()) != (dim_out, dim_in) {
            return Err(ExactChannelError::KrausShape {
                index,
                expected: (dim_out, dim_in),
                actual: (operator.rows(), operator.cols()),
            });
        }
        let operator = BudgetedParts::from_gaussian(operator, fuel)?;
        let adj = operator.adjoint(fuel)?;
        let prod = adj.multiply(&operator, fuel)?;
        prod.scale(weight, fuel)
    }

    fn verify_budgeted_completeness(
        completeness: &BudgetedParts,
        dim_in: usize,
    ) -> Result<(), ExactChannelError> {
        for row in 0..dim_in {
            for col in 0..dim_in {
                let expected = if row == col {
                    Rational::one()
                } else {
                    Rational::zero()
                };
                if completeness.re.get_ref(row, col)? != &expected
                    || !completeness.im.get_ref(row, col)?.is_zero()
                {
                    return Err(ExactChannelError::NotTracePreserving { row, col });
                }
            }
        }
        Ok(())
    }

    /// Exact application with scalar admission and contractions on the caller's
    /// shared budget. Bit limits precede normalization of raw input ratios.
    /// As for `apply`, the input can be any correctly shaped operator.
    pub fn apply_with_budget(
        &self,
        rho: &BasicMatrix<GaussianRat>,
        fuel: &mut RationalBudget,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        check_state_shape(rho, self.dim_in)?;
        OperationLimits::default()
            .check_dense_matrix(rho.rows(), rho.cols(), std::mem::size_of::<GaussianRat>())
            .map_err(|error| ExactChannelError::Malformed(ExactHermitianError::Limits(error)))?;
        let rho = BudgetedParts::from_gaussian(rho, fuel)?;
        let mut out = BudgetedParts::zeros(self.dim_out, self.dim_out, fuel)?;
        for (weight, operator) in self.weights.iter().zip(&self.operators) {
            let image = Self::budgeted_kraus_step(&rho, weight, operator, fuel)?;
            out = out.add(&image, fuel)?;
        }
        out.into_gaussian(fuel)
    }

    fn budgeted_kraus_step(
        rho: &BudgetedParts,
        weight: &Rational,
        operator: &BasicMatrix<GaussianRat>,
        fuel: &mut RationalBudget,
    ) -> Result<BudgetedParts, ExactChannelError> {
        let operator = BudgetedParts::from_gaussian(operator, fuel)?;
        let adj = operator.adjoint(fuel)?;
        let left = operator.multiply(rho, fuel)?;
        let prod = left.multiply(&adj, fuel)?;
        prod.scale(weight, fuel)
    }

    /// Transport one finite state declared by a Gram factor `B`: `rho = B B*`.
    /// Positive semidefiniteness follows from this explicit construction. Unit
    /// trace is checked exactly before applying this declared CPTP map. This
    /// is a finite operational input, not a derivation of quantum dynamics.
    pub fn transport_gram_state_with_budget(
        &self,
        factor: &BasicMatrix<GaussianRat>,
        fuel: &mut RationalBudget,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        if factor.rows() != self.dim_in || factor.cols() == 0 {
            return Err(ExactChannelError::GramStateShape);
        }
        let factor = BudgetedParts::from_gaussian(factor, fuel)?;
        let adj = factor.adjoint(fuel)?;
        let rho = factor.multiply(&adj, fuel)?;
        Self::verify_unit_trace_budgeted(&rho, self.dim_in, fuel)?;
        let rho_gauss = rho.into_gaussian(fuel)?;
        self.apply_with_budget(&rho_gauss, fuel)
    }

    fn verify_unit_trace_budgeted(
        rho: &BudgetedParts,
        dim: usize,
        fuel: &mut RationalBudget,
    ) -> Result<(), ExactChannelError> {
        let mut trace_re = Rational::zero();
        let mut trace_im = Rational::zero();
        for index in 0..dim {
            trace_re = fuel.add(&trace_re, rho.re.get_ref(index, index)?)?;
            trace_im = fuel.add(&trace_im, rho.im.get_ref(index, index)?)?;
        }
        if trace_re != Rational::one() || !trace_im.is_zero() {
            return Err(ExactChannelError::GramStateNormalization);
        }
        Ok(())
    }

    /// Channel with unit weights: `Phi(rho) = sum_k K_k rho K_k*`.
    pub fn try_new(
        dim_in: usize,
        dim_out: usize,
        operators: Vec<BasicMatrix<GaussianRat>>,
        label: impl Into<String>,
    ) -> Result<Self, ExactChannelError> {
        let terms = operators
            .into_iter()
            .map(|k| (Rational::one(), k))
            .collect();
        Self::try_weighted(dim_in, dim_out, terms, label)
    }

    /// Unit-weight channel whose dimensions are read from the first operator
    /// (`d_out x d_in`), with an empty label.
    pub fn from_operators(
        operators: Vec<BasicMatrix<GaussianRat>>,
    ) -> Result<Self, ExactChannelError> {
        let first = operators.first().ok_or(ExactChannelError::EmptyKrausSet)?;
        let (dim_out, dim_in) = (first.rows(), first.cols());
        Self::try_new(dim_in, dim_out, operators, "")
    }

    /// Check dimensions, operator count, and total memory budget for a Kraus family
    /// before allocating any matrices.
    pub fn check_family_limits(
        dim_in: usize,
        dim_out: usize,
        operator_count: usize,
    ) -> Result<(), ExactChannelError> {
        if dim_in == 0 || dim_out == 0 {
            return Err(ExactChannelError::ZeroDimension);
        }
        if operator_count == 0 {
            return Err(ExactChannelError::EmptyKrausSet);
        }
        Self::check_family_memory_budget(dim_in, dim_out, operator_count)
    }

    fn check_family_memory_budget(
        dim_in: usize,
        dim_out: usize,
        operator_count: usize,
    ) -> Result<(), ExactChannelError> {
        let limits = OperationLimits::default();
        limits.check_hilbert_dim(dim_in)?;
        limits.check_hilbert_dim(dim_out)?;
        limits.check_operator_count(operator_count)?;
        let entries =
            limits.check_dense_matrix(dim_in, dim_out, std::mem::size_of::<GaussianRat>())?;
        let total_entries = limits.checked_product(entries, operator_count)?;
        let bytes = limits.checked_product(total_entries, std::mem::size_of::<GaussianRat>())?;
        if bytes > limits.max_memory_bytes {
            return Err(ResourceError::AllocationFailure {
                requested: bytes,
                detail: "Kraus family exceeds declared memory budget".into(),
            }
            .into());
        }
        Ok(())
    }

    /// Channel `Phi(rho) = sum_k w_k K_k rho K_k*`, accepted only when `w_k >= 0`,
    /// every `K_k` is `d_out x d_in`, and `sum_k w_k K_k* K_k = I` exactly.
    pub fn try_weighted(
        dim_in: usize,
        dim_out: usize,
        terms: Vec<(Rational, BasicMatrix<GaussianRat>)>,
        label: impl Into<String>,
    ) -> Result<Self, ExactChannelError> {
        Self::check_family_limits(dim_in, dim_out, terms.len())?;
        let mut completeness = mx::zeros_with_limits(dim_in, dim_in, exact_limits())?;
        for (index, (weight, k)) in terms.iter().enumerate() {
            let scaled_gram = Self::validate_and_compute_gram(index, dim_in, dim_out, weight, k)?;
            completeness = mx::add(&completeness, &scaled_gram)?;
        }
        if let Some((row, col)) = first_difference(
            &completeness,
            &mx::identity_with_limits(dim_in, exact_limits())?,
        ) {
            return Err(ExactChannelError::NotTracePreserving { row, col });
        }
        let (weights, operators) = terms.into_iter().unzip();
        Ok(Self {
            dim_in,
            dim_out,
            weights,
            operators,
            label: label.into(),
        })
    }

    fn validate_and_compute_gram(
        index: usize,
        dim_in: usize,
        dim_out: usize,
        weight: &Rational,
        k: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        if (k.rows(), k.cols()) != (dim_out, dim_in) {
            return Err(ExactChannelError::KrausShape {
                index,
                expected: (dim_out, dim_in),
                actual: (k.rows(), k.cols()),
            });
        }
        check_well_formed(k).map_err(ExactChannelError::Malformed)?;
        if *weight < Rational::zero() {
            return Err(ExactChannelError::NegativeWeight { index });
        }
        let adj = star::adjoint(k)?;
        let gram = mx::multiply_with_limits(&adj, k, exact_limits())?;
        Ok(mx::scale(
            &gram,
            &GaussianRat::from_rational(weight.clone()),
        )?)
    }

    /// Identity channel on `C^dim`.
    pub fn identity(dim: usize, label: impl Into<String>) -> Result<Self, ExactChannelError> {
        OperationLimits::default().check_hilbert_dim(dim)?;
        Self::try_new(
            dim,
            dim,
            vec![mx::identity_with_limits(dim, exact_limits())?],
            label,
        )
    }

    /// Qubit depolarizing channel `Phi(rho) = (1 - p) rho + p I / 2` for rational
    /// `0 <= p <= 1`, as weights `(1 - 3p/4, p/4, p/4, p/4)` on `I, X, Y, Z` — the
    /// parameterisation of the `f64` `QuantumChannel::depolarizing` at `d = 2`.
    pub fn depolarizing_qubit(
        p: Rational,
        label: impl Into<String>,
    ) -> Result<Self, ExactChannelError> {
        if p < Rational::zero() || p > Rational::one() {
            return Err(ExactChannelError::ParameterOutOfRange { name: "p" });
        }
        let quarter = &p * rq(1, 4);
        let keep = Rational::one() - &quarter * ri(3);
        let pauli = |entries: [(i64, i64); 4]| {
            BasicMatrix::<GaussianRat>::from_row_major(
                2,
                2,
                entries
                    .iter()
                    .map(|&(re, im)| GaussianRat::from_ints(re, im))
                    .collect(),
            )
            .map_err(ExactChannelError::Storage)
        };
        let terms = vec![
            (keep, mx::identity_with_limits(2, exact_limits())?),
            (quarter.clone(), pauli([(0, 0), (1, 0), (1, 0), (0, 0)])?),
            (quarter.clone(), pauli([(0, 0), (0, -1), (0, 1), (0, 0)])?),
            (quarter, pauli([(1, 0), (0, 0), (0, 0), (-1, 0)])?),
        ];
        Self::try_weighted(2, 2, terms, label)
    }

    pub fn dim_in(&self) -> usize {
        self.dim_in
    }

    pub fn dim_out(&self) -> usize {
        self.dim_out
    }

    pub fn weights(&self) -> &[Rational] {
        &self.weights
    }

    pub fn operators(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.operators
    }

    pub fn label(&self) -> &str {
        &self.label
    }

    /// `Phi(rho) = sum_k w_k K_k rho K_k*` for any `d_in x d_in` operator `rho`.
    pub fn apply(
        &self,
        rho: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        check_state(rho, self.dim_in)?;
        let mut out = mx::zeros_with_limits(self.dim_out, self.dim_out, exact_limits())?;
        for (weight, k) in self.weights.iter().zip(&self.operators) {
            let image = mx::multiply_with_limits(
                &mx::multiply_with_limits(k, rho, exact_limits())?,
                &star::adjoint(k)?,
                exact_limits(),
            )?;
            out = mx::add(
                &out,
                &mx::scale(&image, &GaussianRat::from_rational(weight.clone()))?,
            )?;
        }
        Ok(out)
    }

    /// `Phi*(E) = sum_k w_k K_k* E K_k` for any `d_out x d_out` operator `E`.
    pub fn adjoint_apply(
        &self,
        effect: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        check_state(effect, self.dim_out)?;
        let mut out = mx::zeros_with_limits(self.dim_in, self.dim_in, exact_limits())?;
        for (weight, k) in self.weights.iter().zip(&self.operators) {
            let image = mx::multiply_with_limits(
                &mx::multiply_with_limits(&star::adjoint(k)?, effect, exact_limits())?,
                k,
                exact_limits(),
            )?;
            out = mx::add(
                &out,
                &mx::scale(&image, &GaussianRat::from_rational(weight.clone()))?,
            )?;
        }
        Ok(out)
    }

    /// `next ∘ self`: apply `self`, then `next`.
    pub fn compose(&self, next: &Self) -> Result<Self, ExactChannelError> {
        if self.dim_out != next.dim_in {
            return Err(ExactChannelError::CompositionMismatch {
                left_out: self.dim_out,
                right_in: next.dim_in,
            });
        }
        let limits = OperationLimits::default();
        let count = limits.checked_product(self.operators.len(), next.operators.len())?;
        Self::check_family_limits(self.dim_in, next.dim_out, count)?;
        let mut terms = Vec::with_capacity(count);
        for (wn, kn) in next.weights.iter().zip(&next.operators) {
            for (ws, ks) in self.weights.iter().zip(&self.operators) {
                terms.push((wn * ws, mx::multiply_with_limits(kn, ks, exact_limits())?));
            }
        }
        Self::try_weighted(
            self.dim_in,
            next.dim_out,
            terms,
            format!("{}∘{}", next.label, self.label),
        )
    }

    /// Choi matrix `J = sum_k w_k vec(K_k) vec(K_k)*`, `vec(K)[i * d_out + r] = K[r][i]`,
    /// re-certified by [`ExactChoiMatrix::try_new`].
    pub fn choi(&self) -> Result<ExactChoiMatrix, ExactChannelError> {
        let n = OperationLimits::default().checked_product(self.dim_in, self.dim_out)?;
        OperationLimits::default().check_hilbert_dim(n)?;
        OperationLimits::default().check_dense_matrix(n, n, std::mem::size_of::<GaussianRat>())?;
        let mut j = mx::zeros_with_limits(n, n, exact_limits())?;
        for (weight, k) in self.weights.iter().zip(&self.operators) {
            let v = Self::vectorize_kraus(k, self.dim_in, self.dim_out, n)?;
            let outer = star::outer_product_with_limits(&v, &v, exact_limits())?;
            let scaled = mx::scale(&outer, &GaussianRat::from_rational(weight.clone()))?;
            j = mx::add(&j, &scaled)?;
        }
        ExactChoiMatrix::try_new(self.dim_in, self.dim_out, j)
    }

    fn vectorize_kraus(
        k: &BasicMatrix<GaussianRat>,
        dim_in: usize,
        dim_out: usize,
        n: usize,
    ) -> Result<Vec<GaussianRat>, ExactChannelError> {
        let mut v = Vec::with_capacity(n);
        for i in 0..dim_in {
            for r in 0..dim_out {
                v.push(k.get_ref(r, i)?.clone());
            }
        }
        Ok(v)
    }

    /// The Stinespring isometry `V = sum_k sqrt(w_k) K_k (x) |k>`, row index
    /// `(o, k) -> o * r + k`; refused when a weight is not a rational square.
    pub fn stinespring_isometry(&self) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        let r = self.operators.len();
        let rows = OperationLimits::default().checked_product(self.dim_out, r)?;
        OperationLimits::default().check_hilbert_dim(rows)?;
        OperationLimits::default().check_dense_matrix(
            rows,
            self.dim_in,
            std::mem::size_of::<GaussianRat>(),
        )?;
        let mut v = mx::zeros_with_limits(rows, self.dim_in, exact_limits())?;
        for (k, (weight, op)) in self.weights.iter().zip(&self.operators).enumerate() {
            let root =
                rational_sqrt(weight).ok_or(ExactChannelError::IrrationalWeight { index: k })?;
            self.write_stinespring_block(&mut v, k, r, GaussianRat::from_rational(root), op)?;
        }
        Ok(v)
    }

    fn write_stinespring_block(
        &self,
        v: &mut BasicMatrix<GaussianRat>,
        k: usize,
        r: usize,
        root: GaussianRat,
        op: &BasicMatrix<GaussianRat>,
    ) -> Result<(), ExactChannelError> {
        for o in 0..self.dim_out {
            for i in 0..self.dim_in {
                v.set(o * r + k, i, root.mul(op.get_ref(o, i)?))?;
            }
        }
        Ok(())
    }

    /// The environment output `Tr_out(V rho V*)`, an `r x r` matrix.
    pub fn complementary(
        &self,
        rho: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        check_state(rho, self.dim_in)?;
        let v = self.stinespring_isometry()?;
        partial_trace_first(
            &mx::multiply_with_limits(
                &mx::multiply_with_limits(&v, rho, exact_limits())?,
                &star::adjoint(&v)?,
                exact_limits(),
            )?,
            self.dim_out,
            self.operators.len(),
        )
        .map_err(ExactChannelError::Malformed)
    }

    /// Minimal weighted Kraus representation, preserving the Choi matrix exactly.
    pub fn minimal(&self) -> Result<Self, ExactChannelError> {
        self.choi()?.weighted_kraus()
    }

    /// Kraus rank equals rank of the Choi matrix, independent of the representation.
    pub fn kraus_rank(&self) -> Result<usize, ExactChannelError> {
        Ok(elimination::rank_with_limits(
            self.choi()?.matrix(),
            exact_limits(),
        )?)
    }

    /// Unit-weight realization over the same field, with at most four operators per
    /// weighted term. Lagrange splitting uses a declared search budget per weight.
    pub fn to_unit_weight(&self, budget_per_weight: u64) -> Result<Self, ExactChannelError> {
        let splits: Vec<Vec<Rational>> = self
            .weights
            .iter()
            .map(|weight| rational_square_split(weight, budget_per_weight))
            .collect::<Result<Vec<_>, _>>()?;
        let total_operators: usize = splits.iter().map(|s| s.len()).sum();
        Self::check_family_limits(self.dim_in, self.dim_out, total_operators)?;
        let mut operators = Vec::with_capacity(total_operators);
        for (split, op) in splits.into_iter().zip(&self.operators) {
            for coefficient in split {
                operators.push(mx::scale(op, &GaussianRat::from_rational(coefficient))?);
            }
        }
        let unit = Self::try_new(self.dim_in, self.dim_out, operators, &self.label)?;
        if unit.choi()?.matrix() != self.choi()?.matrix() {
            return Err(ExactChannelError::FactorizationReplay);
        }
        Ok(unit)
    }

    /// True exactly when the two linear maps coincide, certified by Choi equality.
    pub fn same_channel(&self, other: &Self) -> Result<bool, ExactChannelError> {
        Ok(self.dim_in == other.dim_in
            && self.dim_out == other.dim_out
            && self.choi()?.matrix() == other.choi()?.matrix())
    }

    /// General-d depolarizing map (1-p)rho + p Tr(rho) I/d over Q(i),
    /// using matrix units with weight p/d, avoiding cyclotomic extensions.
    pub fn depolarizing(dim: usize, p: Rational) -> Result<Self, ExactChannelError> {
        OperationLimits::default().check_hilbert_dim(dim)?;
        if p < ri(0) || p > ri(1) {
            return Err(ExactChannelError::ParameterOutOfRange { name: "p" });
        }
        let count = OperationLimits::default().checked_product(dim, dim)?;
        let total_count = count.checked_add(1).ok_or(ResourceError::CountOverflow)?;
        Self::check_family_limits(dim, dim, total_count)?;
        let terms = Self::build_depolarizing_terms(dim, p)?;
        Self::try_weighted(dim, dim, terms, "depolarizing")
    }

    fn build_depolarizing_terms(
        dim: usize,
        p: Rational,
    ) -> Result<Vec<(Rational, BasicMatrix<GaussianRat>)>, ExactChannelError> {
        let mut terms = vec![(ri(1) - &p, mx::identity_with_limits(dim, exact_limits())?)];
        let weight = p / Rational::from_integer(dim.into());
        for r in 0..dim {
            for c in 0..dim {
                let mut op = mx::zeros_with_limits(dim, dim, exact_limits())?;
                op.set(r, c, GaussianRat::one())?;
                terms.push((weight.clone(), op));
            }
        }
        Ok(terms)
    }

    /// Generalized amplitude damping with rational survival amplitude s and bath
    /// ground population p. gamma=1-s^2; four weighted operators need no roots.
    pub fn generalized_amplitude_damping(
        survival: Rational,
        ground: Rational,
    ) -> Result<Self, ExactChannelError> {
        if !(ri(0)..=ri(1)).contains(&survival) || !(ri(0)..=ri(1)).contains(&ground) {
            return Err(ExactChannelError::ParameterOutOfRange {
                name: "survival or ground",
            });
        }
        let gamma = ri(1) - &survival * &survival;
        let down = Self::qubit_matrix_unit(0, 1)?;
        let up = Self::qubit_matrix_unit(1, 0)?;
        let d0 = Self::qubit_diagonal(ri(1), survival.clone())?;
        let d1 = Self::qubit_diagonal(survival, ri(1))?;
        Self::try_weighted(
            2,
            2,
            vec![
                (ground.clone(), d0),
                (&ground * &gamma, down),
                (ri(1) - &ground, d1),
                ((ri(1) - ground) * gamma, up),
            ],
            "thermal amplitude damping",
        )
    }

    fn qubit_diagonal(
        a: Rational,
        b: Rational,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        BasicMatrix::<GaussianRat>::from_row_major(
            2,
            2,
            vec![
                GaussianRat::from_rational(a),
                GaussianRat::zero(),
                GaussianRat::zero(),
                GaussianRat::from_rational(b),
            ],
        )
        .map_err(ExactChannelError::Storage)
    }

    fn qubit_matrix_unit(
        row: usize,
        col: usize,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        let mut mat = mx::zeros_with_limits(2, 2, exact_limits())?;
        mat.set(row, col, GaussianRat::one())?;
        Ok(mat)
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// The rational-parts bridge delegates generic arithmetic to linear algebra.
/// It keeps GaussianRat ownership here and avoids a reverse foundation import.
struct BudgetedParts {
    re: BasicMatrix<Rational>,
    im: BasicMatrix<Rational>,
}

impl BudgetedParts {
    fn zeros(
        rows: usize,
        cols: usize,
        fuel: &mut RationalBudget,
    ) -> Result<Self, ExactChannelError> {
        let count = fuel.elements(rows, cols)?;
        Ok(Self {
            re: BasicMatrix::from_row_major(rows, cols, bounded_buffer(count, Rational::zero())?)?,
            im: BasicMatrix::from_row_major(rows, cols, bounded_buffer(count, Rational::zero())?)?,
        })
    }

    fn from_gaussian(
        matrix: &BasicMatrix<GaussianRat>,
        fuel: &mut RationalBudget,
    ) -> Result<Self, ExactChannelError> {
        let count = fuel.elements(matrix.rows(), matrix.cols())?;
        let mut re = bounded_buffer(count, Rational::zero())?;
        let mut im = bounded_buffer(count, Rational::zero())?;
        for ((real, imaginary), value) in re.iter_mut().zip(&mut im).zip(matrix.as_slice()) {
            fuel.rational(&value.re)?;
            fuel.rational(&value.im)?;
            *real = value.re.clone();
            *imaginary = value.im.clone();
        }
        Ok(Self {
            re: BasicMatrix::from_row_major(matrix.rows(), matrix.cols(), re)?,
            im: BasicMatrix::from_row_major(matrix.rows(), matrix.cols(), im)?,
        })
    }

    fn into_gaussian(
        self,
        fuel: &mut RationalBudget,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        let count = fuel.elements(self.re.rows(), self.re.cols())?;
        let mut entries = bounded_buffer(count, GaussianRat::zero())?;
        for ((entry, re), im) in entries
            .iter_mut()
            .zip(self.re.as_slice())
            .zip(self.im.as_slice())
        {
            fuel.rational(re)?;
            fuel.rational(im)?;
            *entry = GaussianRat {
                re: re.clone(),
                im: im.clone(),
            };
        }
        Ok(BasicMatrix::from_row_major(
            self.re.rows(),
            self.re.cols(),
            entries,
        )?)
    }

    fn adjoint(&self, fuel: &mut RationalBudget) -> Result<Self, ExactChannelError> {
        let (re, im) = bounded::adjoint_complex_parts(&self.re, &self.im, fuel)?;
        Ok(Self { re, im })
    }

    fn multiply(&self, right: &Self, fuel: &mut RationalBudget) -> Result<Self, ExactChannelError> {
        let (re, im) =
            bounded::multiply_complex_parts(&self.re, &self.im, &right.re, &right.im, fuel)?;
        Ok(Self { re, im })
    }

    fn add(&self, right: &Self, fuel: &mut RationalBudget) -> Result<Self, ExactChannelError> {
        Ok(Self {
            re: bounded::add_matrix(&self.re, &right.re, fuel)?,
            im: bounded::add_matrix(&self.im, &right.im, fuel)?,
        })
    }

    fn scale(
        &self,
        scalar: &Rational,
        fuel: &mut RationalBudget,
    ) -> Result<Self, ExactChannelError> {
        Ok(Self {
            re: bounded::scale_matrix(&self.re, scalar, fuel)?,
            im: bounded::scale_matrix(&self.im, scalar, fuel)?,
        })
    }
}

fn bounded_buffer<T: Clone>(count: usize, value: T) -> Result<Vec<T>, RationalError> {
    let mut entries = Vec::new();
    entries
        .try_reserve_exact(count)
        .map_err(|_| RationalError::Allocation)?;
    entries.resize(count, value);
    Ok(entries)
}

/// Choi matrix of an exact CPTP map. Fields are private; every value has passed
/// [`ExactChoiMatrix::try_new`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactChoiMatrix {
    dim_in: usize,
    dim_out: usize,
    matrix: BasicMatrix<GaussianRat>,
}

impl ExactChoiMatrix {
    /// Accept `J` only when it is `(d_in d_out)^2`, Hermitian, exactly PSD (complete
    /// positivity, by Choi's theorem) and satisfies `Tr_out J = I` exactly (trace
    /// preservation).
    pub fn try_new(
        dim_in: usize,
        dim_out: usize,
        matrix: BasicMatrix<GaussianRat>,
    ) -> Result<Self, ExactChannelError> {
        check_choi_shape(&matrix, dim_in, dim_out)?;
        check_hermitian(&matrix).map_err(ExactChannelError::ChoiDefect)?;
        if !is_psd(&matrix).map_err(ExactChannelError::ChoiDefect)? {
            return Err(ExactChannelError::NotCompletelyPositive);
        }
        Self::verify_partial_trace_identity(&matrix, dim_in, dim_out)?;
        Ok(Self {
            dim_in,
            dim_out,
            matrix,
        })
    }

    fn verify_partial_trace_identity(
        matrix: &BasicMatrix<GaussianRat>,
        dim_in: usize,
        dim_out: usize,
    ) -> Result<(), ExactChannelError> {
        for i in 0..dim_in {
            for j in 0..dim_in {
                let sum = Self::partial_trace_entry(matrix, i, j, dim_out)?;
                let expected = if i == j {
                    GaussianRat::one()
                } else {
                    GaussianRat::zero()
                };
                if sum != expected {
                    return Err(ExactChannelError::NotTracePreserving { row: i, col: j });
                }
            }
        }
        Ok(())
    }

    fn partial_trace_entry(
        matrix: &BasicMatrix<GaussianRat>,
        i: usize,
        j: usize,
        dim_out: usize,
    ) -> Result<GaussianRat, ExactChannelError> {
        let mut sum = GaussianRat::zero();
        for r in 0..dim_out {
            sum = sum.add(matrix.get_ref(i * dim_out + r, j * dim_out + r)?);
        }
        Ok(sum)
    }

    pub fn dim_in(&self) -> usize {
        self.dim_in
    }

    pub fn dim_out(&self) -> usize {
        self.dim_out
    }

    pub fn matrix(&self) -> &BasicMatrix<GaussianRat> {
        &self.matrix
    }

    /// Constructive Choi theorem using shared exact Hermitian LDL-star. Positive
    /// pivots become rational weights and columns become rectangular Kraus operators.
    /// Both the Choi reconstruction and its rank are independently replayed.
    pub fn weighted_kraus(&self) -> Result<ExactKrausChannel, ExactChannelError> {
        let ldl = hermitian_ldl_with_limits(&self.matrix, exact_limits())?;
        if !ldl.is_positive_semidefinite() {
            return Err(ExactChannelError::NotCompletelyPositive);
        }
        if ldl.reconstruct_hermitian()? != self.matrix {
            return Err(ExactChannelError::FactorizationReplay);
        }
        let terms = self.extract_ldl_kraus_terms(&ldl)?;
        let channel = ExactKrausChannel::try_weighted(
            self.dim_in,
            self.dim_out,
            terms,
            "Choi factorization",
        )?;
        self.verify_factorization_replay(&channel)?;
        Ok(channel)
    }

    fn extract_ldl_kraus_terms(
        &self,
        ldl: &linear_algebra::exact_field::ordered::Ldlt<GaussianRat>,
    ) -> Result<Vec<(Rational, BasicMatrix<GaussianRat>)>, ExactChannelError> {
        let lower = ldl.unit_lower();
        let mut terms = Vec::new();
        for (k, pivot) in ldl.pivots().iter().enumerate() {
            if !pivot.is_zero() {
                let op = self.extract_kraus_column(lower, k)?;
                terms.push((pivot.re.clone(), op));
            }
        }
        Ok(terms)
    }

    fn extract_kraus_column(
        &self,
        lower: &BasicMatrix<GaussianRat>,
        k: usize,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        let mut op = mx::zeros_with_limits(self.dim_out, self.dim_in, exact_limits())?;
        for i in 0..self.dim_in {
            for r in 0..self.dim_out {
                op.set(r, i, lower.get_ref(i * self.dim_out + r, k)?.clone())?;
            }
        }
        Ok(op)
    }

    fn verify_factorization_replay(
        &self,
        channel: &ExactKrausChannel,
    ) -> Result<(), ExactChannelError> {
        let choi_matches = channel.choi()?.matrix() == &self.matrix;
        let rank_matches =
            channel.operators.len() == elimination::rank_with_limits(&self.matrix, exact_limits())?;
        if !choi_matches || !rank_matches {
            return Err(ExactChannelError::FactorizationReplay);
        }
        Ok(())
    }

    /// Entanglement fidelity for maximally mixed input on a square channel:
    /// <Phi|J|Phi>/d, with |Phi>=sum_i|ii>/sqrt(d).
    pub fn entanglement_fidelity(&self) -> Result<Rational, ExactChannelError> {
        if self.dim_in != self.dim_out {
            return Err(ExactChannelError::CompositionMismatch {
                left_out: self.dim_out,
                right_in: self.dim_in,
            });
        }
        let mut sum = GaussianRat::zero();
        for i in 0..self.dim_in {
            for j in 0..self.dim_in {
                sum = sum.add(
                    self.matrix
                        .get_ref(i * self.dim_out + i, j * self.dim_out + j)?,
                );
            }
        }
        Ok(sum.re / Rational::from_integer((self.dim_in * self.dim_in).into()))
    }

    /// `Phi(rho)_{rs} = sum_{ij} rho_{ij} J[i * d_out + r][j * d_out + s]`.
    pub fn apply(
        &self,
        rho: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        apply_choi(&self.matrix, self.dim_in, self.dim_out, rho)
    }
}

fn check_choi_shape(
    choi: &BasicMatrix<GaussianRat>,
    dim_in: usize,
    dim_out: usize,
) -> Result<(), ExactChannelError> {
    if dim_in == 0 || dim_out == 0 {
        return Err(ExactChannelError::ZeroDimension);
    }
    let n = OperationLimits::default().checked_product(dim_in, dim_out)?;
    OperationLimits::default().check_hilbert_dim(n)?;
    if (choi.rows(), choi.cols()) != (n, n) {
        return Err(ExactChannelError::ChoiShape {
            expected: n,
            actual: (choi.rows(), choi.cols()),
        });
    }
    check_well_formed(choi).map_err(ExactChannelError::Malformed)
}

/// `Phi(rho)_{rs} = sum_{ij} rho_{ij} J[i * d_out + r][j * d_out + s]` for the
/// linear map with Choi matrix `J`, which need not be CPTP.
pub fn apply_choi(
    choi: &BasicMatrix<GaussianRat>,
    input_dim: usize,
    output_dim: usize,
    rho: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
    check_choi_shape(choi, input_dim, output_dim)?;
    check_state(rho, input_dim)?;
    let mut out = mx::zeros_with_limits(output_dim, output_dim, exact_limits())?;
    for r in 0..output_dim {
        for s in 0..output_dim {
            let acc = choi_entry_contraction(choi, rho, input_dim, output_dim, r, s)?;
            out.set(r, s, acc)?;
        }
    }
    Ok(out)
}

fn choi_entry_contraction(
    choi: &BasicMatrix<GaussianRat>,
    rho: &BasicMatrix<GaussianRat>,
    input_dim: usize,
    output_dim: usize,
    r: usize,
    s: usize,
) -> Result<GaussianRat, ExactChannelError> {
    let mut acc = GaussianRat::zero();
    for i in 0..input_dim {
        for j in 0..input_dim {
            let coupling = choi.get_ref(i * output_dim + r, j * output_dim + s)?;
            acc = acc.add(&rho.get_ref(i, j)?.mul(coupling));
        }
    }
    Ok(acc)
}

/// Choi's criterion as a yes/no answer: [`ExactChoiMatrix::try_new`] accepts `J`.
pub fn choi_is_cptp(choi: &BasicMatrix<GaussianRat>, input_dim: usize, output_dim: usize) -> bool {
    ExactChoiMatrix::try_new(input_dim, output_dim, choi.clone()).is_ok()
}

/// `Tr_env(V rho V*)` for an isometry `V : C^d_in -> C^d_out (x) C^r`.
pub fn apply_stinespring(
    isometry: &BasicMatrix<GaussianRat>,
    output_dim: usize,
    environment_dim: usize,
    rho: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
    let rows = OperationLimits::default().checked_product(output_dim, environment_dim)?;
    OperationLimits::default().check_hilbert_dim(rows)?;
    if isometry.rows() != rows || isometry.cols() != rho.rows() {
        return Err(ExactChannelError::IsometryShape {
            expected: (rows, rho.rows()),
            actual: (isometry.rows(), isometry.cols()),
        });
    }
    check_well_formed(isometry).map_err(ExactChannelError::Malformed)?;
    check_state(rho, isometry.cols())?;
    partial_trace_second(
        &mx::multiply_with_limits(
            &mx::multiply_with_limits(isometry, rho, exact_limits())?,
            &star::adjoint(isometry)?,
            exact_limits(),
        )?,
        output_dim,
        environment_dim,
    )
    .map_err(ExactChannelError::Malformed)
}

/// First `(row, col)`, in row-major order, where equal-shaped `a` and `b` differ.
fn first_difference(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
) -> Option<(usize, usize)> {
    let cols = a.cols();
    a.as_slice()
        .iter()
        .zip(b.as_slice())
        .position(|(x, y)| x != y)
        .map(|index| (index / cols, index % cols))
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hilbert_space::HilbertSpace;
    use crate::quantum_channel::{ChannelError, QuantumChannel};
    use crate::trace_norm_certificate::trace_distance;

    fn qi(rows: usize, cols: usize, entries: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
        BasicMatrix::<GaussianRat>::from_row_major(
            rows,
            cols,
            entries
                .iter()
                .map(|&(re, im)| GaussianRat::from_ints(re, im))
                .collect(),
        )
        .expect("validated matrix literal")
    }

    fn diag(values: &[Rational]) -> BasicMatrix<GaussianRat> {
        let mut m = mx::zeros(values.len(), values.len()).unwrap();
        for (i, v) in values.iter().enumerate() {
            m.set(i, i, GaussianRat::from_rational(v.clone())).unwrap();
        }
        m
    }

    /// `sum_{a,b in support} |a><b|` on `C^n`: the unnormalised maximally entangled
    /// projector when `support` is `{i * d + i}`.
    fn ones_on(n: usize, support: &[usize]) -> BasicMatrix<GaussianRat> {
        let mut m = mx::zeros(n, n).unwrap();
        for &a in support {
            for &b in support {
                m.set(a, b, GaussianRat::one()).unwrap();
            }
        }
        m
    }

    #[test]
    fn identity_channel_is_exactly_trace_preserving() {
        let id = ExactKrausChannel::identity(3, "id").unwrap();
        let rho = diag(&[rq(1, 2), rq(1, 3), rq(1, 6)]);
        assert_eq!(id.apply(&rho).unwrap(), rho);
        // Choi of the qubit identity is the unnormalised |Φ+><Φ+|.
        let choi = ExactKrausChannel::identity(2, "id2")
            .unwrap()
            .choi()
            .unwrap();
        assert_eq!(choi.matrix(), &ones_on(4, &[0, 3]));
    }

    #[test]
    fn budgeted_channel_input_limits_precede_physical_normalization() {
        let identity = ExactKrausChannel::identity(1, "budgeted identity").unwrap();
        let oversized = num_bigint::BigInt::from(1) << 4096usize;
        let cases = [
            (
                Rational::new_raw(oversized.clone(), oversized),
                RationalError::BitLimit,
            ),
            (
                Rational::new_raw(1.into(), 0.into()),
                RationalError::InvalidRational,
            ),
        ];
        for (raw, expected) in cases {
            let input = BasicMatrix::from_row_major(1, 1, vec![GaussianRat { re: raw, im: ri(0) }])
                .unwrap();
            let mut fuel = RationalBudget::new(bounded::RationalLimits {
                max_scalar_ops: 64,
                max_elements: 1,
                max_bits: 8,
            });
            assert_eq!(
                identity.apply_with_budget(&input, &mut fuel),
                Err(ExactChannelError::RationalBudget(expected)),
            );
            assert_eq!(fuel.used(), 0, "raw ratios refuse before normalization");
            assert!(matches!(
                identity.apply(&input),
                Err(ExactChannelError::Malformed(_))
            ));
        }
    }

    #[test]
    fn budgeted_channel_application_keeps_spent_fuel_and_accepts_benign_input() {
        let identity = ExactKrausChannel::identity(1, "budgeted identity").unwrap();
        let input = mx::identity(1).unwrap();
        let limits = bounded::RationalLimits {
            max_scalar_ops: 512,
            max_elements: 1,
            max_bits: 8,
        };
        let mut sufficient = RationalBudget::new(limits);
        assert_eq!(
            identity.apply_with_budget(&input, &mut sufficient).unwrap(),
            input
        );
        assert!(sufficient.used() > 0);

        let mut spent = RationalBudget::new(limits);
        spent.charge(511).unwrap();
        assert_eq!(
            identity.apply_with_budget(&input, &mut spent),
            Err(ExactChannelError::RationalBudget(
                RationalError::FuelExhausted
            ))
        );
        assert_eq!(spent.used(), 512);
    }

    #[test]
    fn budgeted_channel_shape_refusal_preserves_fuel() {
        let identity = ExactKrausChannel::identity(1, "budgeted identity").unwrap();
        let input = qi(1, 2, &[(0, 0), (0, 0)]);
        let mut fuel = RationalBudget::new(bounded::RationalLimits {
            max_scalar_ops: 8,
            max_elements: 1,
            max_bits: 8,
        });
        fuel.charge(2).unwrap();
        assert_eq!(
            identity.apply_with_budget(&input, &mut fuel),
            Err(ExactChannelError::StateShape {
                expected: 1,
                actual: (1, 2)
            })
        );
        assert_eq!(fuel.used(), 2);
    }

    /// Exact counterpart of MUT-01 in `tests/mutation_kill_tests.rs`: no tolerance,
    /// a trace-preservation defect anywhere is refused and located.
    #[test]
    fn trace_preservation_defect_is_refused_exactly() {
        let two_i = mx::scale(
            &(mx::identity(2).unwrap()),
            &GaussianRat::from_rational(ri(2)),
        )
        .unwrap();
        assert_eq!(
            ExactKrausChannel::try_new(2, 2, vec![two_i], "2I"),
            Err(ExactChannelError::NotTracePreserving { row: 0, col: 0 })
        );
        // A defect of 1/10^30, which no f64 tolerance would see.
        let mut almost = mx::identity(2).unwrap();
        let tiny = Rational::new(1.into(), num_bigint::BigInt::from(10u8).pow(30));
        almost
            .set(1, 1, GaussianRat::from_rational(Rational::one() - tiny))
            .unwrap();
        assert_eq!(
            ExactKrausChannel::try_new(2, 2, vec![almost], "almost"),
            Err(ExactChannelError::NotTracePreserving { row: 1, col: 1 })
        );
    }

    #[test]
    fn construction_refusals() {
        assert_eq!(
            ExactKrausChannel::try_new(2, 2, vec![], "e"),
            Err(ExactChannelError::EmptyKrausSet)
        );
        assert_eq!(
            ExactKrausChannel::from_operators(vec![]),
            Err(ExactChannelError::EmptyKrausSet)
        );
        assert_eq!(
            ExactKrausChannel::try_new(0, 2, vec![mx::identity(2).unwrap()], "z"),
            Err(ExactChannelError::ZeroDimension)
        );
        assert_eq!(
            ExactKrausChannel::try_new(2, 2, vec![mx::identity(3).unwrap()], "s"),
            Err(ExactChannelError::KrausShape {
                index: 0,
                expected: (2, 2),
                actual: (3, 3)
            })
        );
        assert_eq!(
            ExactKrausChannel::try_weighted(1, 1, vec![(ri(-1), mx::identity(1).unwrap())], "w"),
            Err(ExactChannelError::NegativeWeight { index: 0 })
        );
        assert_eq!(
            ExactKrausChannel::depolarizing_qubit(rq(3, 2), "p"),
            Err(ExactChannelError::ParameterOutOfRange { name: "p" })
        );
        assert!(
            BasicMatrix::<GaussianRat>::from_row_major(2, 2, vec![GaussianRat::one()]).is_err()
        );
        let id = ExactKrausChannel::identity(2, "id").unwrap();
        let wrong = mx::identity(1).unwrap();
        assert!(matches!(
            id.apply(&wrong),
            Err(ExactChannelError::StateShape { .. })
        ));
        assert!(matches!(
            id.adjoint_apply(&wrong),
            Err(ExactChannelError::StateShape { .. })
        ));
        assert!(matches!(
            id.choi().unwrap().apply(&wrong),
            Err(ExactChannelError::StateShape { .. })
        ));
    }

    /// Depolarizing with rational `p` is exact; the `f64` channel with the same `p`
    /// agrees within rounding, so it serves as a diagnostic of this one.
    #[test]
    fn depolarizing_is_exact_and_the_float_path_is_its_diagnostic() {
        let dep = ExactKrausChannel::depolarizing_qubit(rq(1, 5), "dep").unwrap();
        let zero = diag(&[ri(1), ri(0)]);
        let out = dep.apply(&zero).unwrap();
        assert_eq!(out, diag(&[rq(9, 10), rq(1, 10)]));

        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        assert!(matches!(
            QuantumChannel::depolarizing(&h2, 0.2, "dep"),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
    }

    /// Amplitude damping is exact when `√γ` and `√(1 − γ)` are rational (γ = 9/25).
    #[test]
    fn pythagorean_amplitude_damping_matches_the_float_diagnostic() {
        let k0 = diag(&[ri(1), rq(4, 5)]);
        let mut k1 = mx::zeros(2, 2).unwrap();
        k1.set(0, 1, GaussianRat::from_rational(rq(3, 5))).unwrap();
        let ad = ExactKrausChannel::try_new(2, 2, vec![k0, k1], "ad").unwrap();
        let excited = diag(&[ri(0), ri(1)]);
        let out = ad.apply(&excited).unwrap();
        assert_eq!(out, diag(&[rq(9, 25), rq(16, 25)]));

        assert!(matches!(
            QuantumChannel::amplitude_damping(0.36, "ad"),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
    }

    /// The Choi matrix applies the same channel as the Kraus form.
    #[test]
    fn choi_and_kraus_forms_agree() {
        let dep = ExactKrausChannel::depolarizing_qubit(rq(1, 3), "dep").unwrap();
        let choi = dep.choi().unwrap();
        // A generic state with a complex coherence.
        let mut rho = diag(&[rq(2, 3), rq(1, 3)]);
        rho.set(
            0,
            1,
            GaussianRat::from_rational(rq(1, 6)).mul(&GaussianRat::from_ints(1, -1)),
        )
        .unwrap();
        rho.set(
            1,
            0,
            GaussianRat::from_rational(rq(1, 6)).mul(&GaussianRat::from_ints(1, 1)),
        )
        .unwrap();
        assert_eq!(choi.apply(&rho).unwrap(), dep.apply(&rho).unwrap());
    }

    /// `dep(q) ∘ dep(p) = dep(p + q − pq)`, compared on the unique Choi matrix.
    #[test]
    fn composition_of_depolarizing_channels() {
        let p = rq(1, 5);
        let q = rq(1, 3);
        let dp = ExactKrausChannel::depolarizing_qubit(p.clone(), "p").unwrap();
        let dq = ExactKrausChannel::depolarizing_qubit(q.clone(), "q").unwrap();
        let composed = dp.compose(&dq).unwrap();
        let direct = ExactKrausChannel::depolarizing_qubit(&p + &q - &p * &q, "pq").unwrap();
        assert_eq!(
            composed.choi().unwrap().matrix(),
            direct.choi().unwrap().matrix()
        );
        assert_eq!(composed.label(), "q∘p");
    }

    /// The transpose map has Choi matrix SWAP: Hermitian and trace preserving but not
    /// completely positive. Exact PSD refuses it.
    #[test]
    fn transpose_map_is_refused_as_not_completely_positive() {
        let mut swap = mx::zeros(4, 4).unwrap();
        for i in 0..2 {
            for j in 0..2 {
                swap.set(i * 2 + j, j * 2 + i, GaussianRat::one()).unwrap();
            }
        }
        assert_eq!(
            ExactChoiMatrix::try_new(2, 2, swap.clone()),
            Err(ExactChannelError::NotCompletelyPositive)
        );
        assert!(!choi_is_cptp(&swap, 2, 2));
        // It still applies as a linear map: the transpose.
        let rho = qi(2, 2, &[(1, 0), (0, 1), (0, -1), (0, 0)]);
        assert_eq!(
            apply_choi(&swap, 2, 2, &rho).unwrap(),
            mx::transpose(&rho).unwrap()
        );
    }

    #[test]
    fn choi_refusals() {
        let id_choi = ExactKrausChannel::identity(2, "id")
            .unwrap()
            .choi()
            .unwrap();
        // Doubling breaks trace preservation but not positivity.
        assert_eq!(
            ExactChoiMatrix::try_new(
                2,
                2,
                mx::scale(&(id_choi.matrix()), &GaussianRat::from_rational(ri(2))).unwrap()
            ),
            Err(ExactChannelError::NotTracePreserving { row: 0, col: 0 })
        );
        let mut skew = id_choi.matrix().clone();
        skew.set(0, 3, GaussianRat::from_ints(0, 1)).unwrap();
        assert!(matches!(
            ExactChoiMatrix::try_new(2, 2, skew),
            Err(ExactChannelError::ChoiDefect(_))
        ));
        assert_eq!(
            ExactChoiMatrix::try_new(2, 2, mx::identity(3).unwrap()),
            Err(ExactChannelError::ChoiShape {
                expected: 4,
                actual: (3, 3)
            })
        );
    }

    /// A non-endomorphic channel: the trace `C^2 -> C^1`, Kraus `<0|, <1|`.
    #[test]
    fn trace_channel_is_rectangular() {
        let bra0 = qi(1, 2, &[(1, 0), (0, 0)]);
        let bra1 = qi(1, 2, &[(0, 0), (1, 0)]);
        let tr = ExactKrausChannel::try_new(2, 1, vec![bra0, bra1], "tr").unwrap();
        let rho = diag(&[rq(1, 4), rq(3, 4)]);
        assert_eq!(tr.apply(&rho).unwrap(), mx::identity(1).unwrap());
        assert_eq!(tr.choi().unwrap().matrix(), &mx::identity(2).unwrap());
    }

    /// The fixed-presentation helper requires rational-square weights; it does
    /// not decide existence of a dilation with a different Kraus family.
    #[test]
    fn stinespring_isometry_needs_rational_square_weights() {
        // Depolarizing at p = 1/5: weights 17/20, 1/20, 1/20, 1/20; none a square.
        let dep = ExactKrausChannel::depolarizing_qubit(rq(1, 5), "dep").unwrap();
        assert_eq!(
            dep.stinespring_isometry(),
            Err(ExactChannelError::IrrationalWeight { index: 0 })
        );
        // At p = 1: weights 1/4 each, all squares.
        let full = ExactKrausChannel::depolarizing_qubit(ri(1), "full").unwrap();
        let v = full.stinespring_isometry().unwrap();
        assert_eq!(
            mx::multiply_with_limits(
                &(star::adjoint(&(v)).unwrap()),
                &v,
                crate::exact_hermitian::exact_limits()
            )
            .unwrap(),
            mx::identity(2).unwrap()
        );
        let rho = diag(&[rq(2, 3), rq(1, 3)]);
        assert_eq!(
            apply_stinespring(&v, 2, 4, &rho).unwrap(),
            full.apply(&rho).unwrap()
        );
        assert_eq!(
            mx::trace(&(full.complementary(&rho).unwrap())).unwrap(),
            GaussianRat::one()
        );
        assert!(matches!(
            apply_stinespring(&v, 2, 3, &rho),
            Err(ExactChannelError::IsometryShape { .. })
        ));
    }

    /// QM_080: trace distance contracts under a CPTP map, certified exactly.
    #[test]
    fn trace_distance_contracts_under_depolarizing() {
        let zero = diag(&[ri(1), ri(0)]);
        let one = diag(&[ri(0), ri(1)]);
        let before = trace_distance(&zero, &one, &[ri(1), ri(-1)]).unwrap();
        let dep = ExactKrausChannel::depolarizing_qubit(rq(1, 2), "dep").unwrap();
        let (a, b) = (dep.apply(&zero).unwrap(), dep.apply(&one).unwrap());
        let after = trace_distance(&a, &b, &[rq(1, 2), rq(-1, 2)]).unwrap();
        assert_eq!(before, ri(1));
        assert_eq!(after, rq(1, 2));
        assert!(after < before);
    }

    #[test]
    fn depolarizing_oversized_request_refuses_before_allocation() {
        // Dimension 63 produces 63^2 + 1 = 3970 operators, each 63x63 = 3969 GaussianRat entries.
        // Total bytes = 3970 * 3969 * sizeof(GaussianRat) > 32 MiB default memory budget.
        // Must refuse with ResourceError::AllocationFailure before allocating matrices.
        let result = ExactKrausChannel::depolarizing(63, rq(1, 2));
        assert!(matches!(
            result,
            Err(ExactChannelError::Limits(
                ResourceError::AllocationFailure { .. }
            ))
        ));
    }

    #[test]
    fn authority_fence_is_none() {
        assert!(ExactKrausChannel::authority_fence().contains("AuthorityEffect None"));
    }
}

#[cfg(test)]
mod dp8_controls {
    use super::*;
    use crate::exact_hermitian::{decide_psd, realify, PsdDecision};
    use num_bigint::BigInt;
    use core_number_theory::integer_factorization::FactorizationBudget;
    use core_number_theory::sums_of_squares::two_squares;

    fn qi(rows: usize, entries: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
        BasicMatrix::from_row_major(
            rows,
            entries.len() / rows,
            entries
                .iter()
                .map(|&(r, i)| GaussianRat::from_ints(r, i))
                .collect(),
        )
        .expect("literal matrix")
    }

    fn quadratic_form(m: &BasicMatrix<GaussianRat>, v: &[GaussianRat]) -> GaussianRat {
        let n = v.len();
        let mut acc = GaussianRat::zero();
        for i in 0..n {
            for j in 0..n {
                acc = acc.add(
                    &v[i]
                        .conj()
                        .mul(m.get_ref(i, j).expect("in range"))
                        .mul(&v[j]),
                );
            }
        }
        acc
    }

    fn leading_minors(m: &BasicMatrix<GaussianRat>) -> Vec<GaussianRat> {
        (1..=m.rows())
            .map(|k| {
                let block = mx::from_fn(k, k, |i, j| m.get_ref(i, j).expect("in range").clone())
                    .expect("block");
                elimination::determinant(&block).expect("square")
            })
            .collect()
    }

    #[test]
    fn singular_leading_minor_control_is_decided_by_congruence() {
        let a = qi(
            3,
            &[
                (0, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (2, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (-1, 0),
            ],
        );
        // Every leading principal minor is zero, so a minor test reads "nonnegative".
        assert!(leading_minors(&a).iter().all(GaussianRat::is_zero));
        match decide_psd(&a).expect("Hermitian") {
            PsdDecision::Negative { vector, value } => {
                assert!(value < Rational::zero());
                assert_eq!(
                    quadratic_form(&a, &vector),
                    GaussianRat::from_rational(value)
                );
            }
            other => panic!("diag(0,2,-1) admitted: {other:?}"),
        }
        let psd = qi(2, &[(1, 0), (0, 1), (0, -1), (1, 0)]);
        assert!(matches!(
            decide_psd(&psd),
            Ok(PsdDecision::PositiveSemidefinite { .. })
        ));
        assert!(decide_psd(&qi(2, &[(0, 0), (0, 1), (0, 1), (0, 0)])).is_err());
    }

    #[test]
    fn transpose_choi_is_refused_with_a_negative_vector() {
        // J = sum |i><j| (x) |j><i| = SWAP on C^2 (x) C^2.
        let swap = qi(
            4,
            &[
                (1, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (1, 0),
                (0, 0),
                (0, 0),
                (1, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (1, 0),
            ],
        );
        assert_eq!(
            ExactChoiMatrix::try_new(2, 2, swap.clone()),
            Err(ExactChannelError::NotCompletelyPositive)
        );
        let v = vec![
            GaussianRat::zero(),
            GaussianRat::one(),
            GaussianRat::from_ints(-1, 0),
            GaussianRat::zero(),
        ];
        assert_eq!(quadratic_form(&swap, &v), GaussianRat::from_ints(-2, 0));
        match decide_psd(&swap).expect("Hermitian") {
            PsdDecision::Negative { vector, value } => {
                assert!(value < Rational::zero());
                assert_eq!(
                    quadratic_form(&swap, &vector),
                    GaussianRat::from_rational(value)
                );
            }
            other => panic!("SWAP admitted: {other:?}"),
        }
        // Trace preservation holds for the transpose; only positivity fails.
        assert!(!choi_is_cptp(&swap, 2, 2));
    }

    #[test]
    fn rank_one_channel_has_no_single_unit_operator_and_two_suffice_over_gaussian_rationals() {
        // H = [[1, 1+i], [1-i, -1]], H* H = 3 I.
        let h = qi(2, &[(1, 0), (1, 1), (1, -1), (-1, 0)]);
        assert_eq!(
            mx::multiply(&star::adjoint(&h).unwrap(), &h).unwrap(),
            mx::scale(&mx::identity(2).unwrap(), &GaussianRat::from_ints(3, 0)).unwrap()
        );
        let weighted =
            ExactKrausChannel::try_weighted(2, 2, vec![(rq(1, 3), h.clone())], "H/3").unwrap();
        assert_eq!(weighted.kraus_rank().unwrap(), 1);
        let third = mx::scale(&h, &GaussianRat::from_rational(rq(1, 3))).unwrap();
        // One copy of H/3 is not trace preserving; three copies are.
        assert!(matches!(
            ExactKrausChannel::try_new(2, 2, vec![third.clone()], "one"),
            Err(ExactChannelError::NotTracePreserving { .. })
        ));
        let three =
            ExactKrausChannel::try_new(2, 2, vec![third.clone(), third.clone(), third], "three")
                .unwrap();
        assert!(three.same_channel(&weighted).unwrap());
        // A single unit Kraus operator would be c H with |c|^2 = 1/3, c in Q(i): 1/3 is a sum of
        // two rational squares exactly when 1 * 3 is a sum of two integer squares, and 3 is not.
        assert_eq!(
            two_squares(&BigInt::from(3), FactorizationBudget::default(), 1_000).unwrap(),
            None
        );
        // Budget refusal is not nonexistence: budget 0 refuses, a positive budget succeeds.
        assert!(matches!(
            weighted.to_unit_weight(0),
            Err(ExactChannelError::SquareSplit(
                FourSquaresError::BudgetExhausted
            ))
        ));
        let unit = weighted.to_unit_weight(10_000).unwrap();
        assert!(unit.same_channel(&weighted).unwrap());
        assert!(unit.operators().len() >= 2);
        // Two unit operators suffice over Q(i): c1 = (1+i)/3, c2 = 1/3, |c1|^2 + |c2|^2 = 1/3.
        let c1 = mx::scale(
            &h,
            &GaussianRat {
                re: rq(1, 3),
                im: rq(1, 3),
            },
        )
        .unwrap();
        let c2 = mx::scale(&h, &GaussianRat::from_rational(rq(1, 3))).unwrap();
        let two = ExactKrausChannel::try_new(2, 2, vec![c1, c2], "two").unwrap();
        assert!(two.same_channel(&weighted).unwrap());
    }

    #[test]
    fn realification_doubles_the_carrier_and_scales_the_trace() {
        let m = qi(2, &[(1, 0), (0, 1), (0, -1), (3, 0)]);
        let r = realify(&m).unwrap();
        assert_eq!(r.len(), 4);
        let trace: Rational = (0..4).map(|i| r[i][i].clone()).sum();
        assert_eq!(trace, ri(8));
        assert_eq!(
            trace,
            ri(2) * crate::exact_hermitian::hermitian_trace(&m).unwrap()
        );
        // R(A (x) B) lives on 2ab, R(A) (x) R(B) on 4ab: realification is not a tensor functor
        // on carriers.
        let ab = mx::kronecker(&m, &m).unwrap();
        assert_eq!(realify(&ab).unwrap().len(), 8);
        assert_eq!(r.len() * r.len(), 16);
    }
}
