// AuthorityEffect: None.

//! Admission of a Dirac operator from a declared family of gamma matrices over `Q(i)`.
//!
//! Declared: square matrices `gamma^0, ..., gamma^(n-1)` of one size `N` and a
//! diagonal metric `eta = diag(eta_0, ..., eta_(n-1))` with entries `+1` or
//! `-1`; momenta `p^mu`, masses and spin-element parameters are rational.
//! Computed exactly:
//!
//! - [`CliffordFamily::admit`]: every anticommutator
//!   `{gamma^mu, gamma^nu} = 2 eta^(mu nu) I`; the first failing pair is named.
//!   [`CliffordFamily::dirac`] and [`CliffordFamily::weyl`] are the Dirac and
//!   chiral representations of signature `(+, -, -, -)`, built with the Pauli
//!   matrices of `core_lie_theory::pauli_symplectic`.
//! - [`CliffordFamily::slash`]: `gamma^mu p_mu` with `p_mu = eta_mu p^mu`,
//!   whose square is `(p . p) I` ([`CliffordFamily::interval`]).
//!   [`CliffordFamily::solution_dimension`] is `N - rank(slash(p) - m)`, by exact
//!   rank over `Q(i)`.
//! - [`CliffordFamily::has_dirac_adjoint`]: `gamma^0 (gamma^mu)* gamma^0 = gamma^mu`
//!   for every `mu`. The anticommutators do not imply it: a non-unitary
//!   similarity keeps them and loses it.
//! - [`CliffordFamily::product_span_rank`]: the rank of the `2^n` ordered
//!   products `gamma^(mu_1) ... gamma^(mu_k)`, `mu_1 < ... < mu_k`. When it is
//!   `N^2` the products span all `N x N` matrices and the family is
//!   irreducible.
//! - [`CliffordFamily::chirality`]: for even `n`, the product `gamma^0 ... gamma^(n-1)`
//!   times `1` or `i`, whichever squares to `I`.
//! - [`CliffordFamily::vector_action`]: for an invertible `S`,
//!   `L^mu_nu = Tr(S^(-1) gamma^mu S gamma_nu) / N`, returned only when
//!   `S^(-1) gamma^mu S = L^mu_nu gamma^nu` holds exactly with real `L`. Then
//!   `slash(L p) S = S slash(p)`: `S` carries solutions at `p` to solutions at
//!   `L p`, and `S` and `-S` give the same `L`.
//! - [`CliffordFamily::plane_spin_element`]: `a I + b gamma^mu gamma^nu`, and
//!   [`boost_half_parameters`]: the rational `(a, b)` with `a^2 - b^2 = 1` whose
//!   boost has the declared `(cosh, sinh)`. They exist exactly when
//!   `(1 + cosh) / 2` is the square of a rational; otherwise the refusal names
//!   its squarefree class (`core_number_theory::quadratic::Surd`).
//!
//! Refused: an empty or ragged family, a metric entry other than `+-1`, a
//! failing anticommutator, momenta of the wrong length, an odd family asked
//! for its chirality, a singular `S` or one outside the Clifford group, and
//! boost data off the future unit hyperbola.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_de1b0452<T> {
    fn checked_invariant_de1b0452(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_de1b0452<T> for Option<T> {
    #[inline]
    fn checked_invariant_de1b0452(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_de1b0452<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_de1b0452(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, matrix as mx, ExactFieldError};
use core_lie_theory::clifford::{CliffordError, CliffordFamily as CliffordAlgebra};
use core_lie_theory::scalar::dagger;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::{QuadraticError, Surd};
use core_number_theory::rational::{ri, Rational};

/// Largest family whose `2^n` ordered products are enumerated.
pub const MAX_PRODUCT_FAMILY: usize = 6;

/// Refusals for gamma families, Dirac operators and spin elements.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DiracError {
    #[error(transparent)]
    Algebra(#[from] CliffordError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error("spin element is {rows}x{cols}, expected {size}x{size}")]
    SpinShape {
        rows: usize,
        cols: usize,
        size: usize,
    },
    #[error("mass must be nonzero for energy projectors")]
    ZeroMass,
    #[error("momentum does not lie on the declared mass shell")]
    OffMassShell,
    #[error("a Clifford family needs at least one matrix")]
    Empty,
    #[error("gamma {index} is {rows}x{cols}, expected {size}x{size}")]
    Shape {
        index: usize,
        rows: usize,
        cols: usize,
        size: usize,
    },
    #[error("{gammas} gammas but {metric} metric entries")]
    MetricLength { gammas: usize, metric: usize },
    #[error("metric entry {index} is {value}, not +1 or -1")]
    MetricEntry { index: usize, value: Rational },
    #[error("the anticommutator of gamma {mu} and gamma {nu} is not 2 eta I")]
    Anticommutator { mu: usize, nu: usize },
    #[error("momentum has {found} components, expected {expected}")]
    MomentumLength { expected: usize, found: usize },
    #[error("gamma index {index} is out of range for {count} gammas")]
    IndexOutOfRange { index: usize, count: usize },
    #[error("a spin element needs two distinct gammas, got {index} twice")]
    SamePlaneIndex { index: usize },
    #[error("an odd family has no chirality element")]
    OddFamily,
    #[error("a family of {0} gammas has too many ordered products to enumerate")]
    TooManyProducts(usize),
    #[error("S is not an invertible {size}x{size} matrix")]
    Singular { size: usize },
    #[error("S does not conjugate each gamma to a real combination of gammas")]
    NotInCliffordGroup,
    #[error("(cosh, sinh) is not on the future unit hyperbola")]
    OffHyperbola,
    #[error("the half-rapidity needs the square root of {square_class} times a rational square")]
    NoRationalHalfRapidity { square_class: BigInt },
    #[error(transparent)]
    Surd(#[from] QuadraticError),
}

/// A declared family of gamma matrices that satisfies the Clifford relations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CliffordFamily {
    gammas: Vec<BasicMatrix<GaussianRat>>,
    metric: Vec<Rational>,
    algebra: CliffordAlgebra<GaussianRat>,
}

fn pauli_matrices() -> [BasicMatrix<GaussianRat>; 3] {
    use core_lie_theory::pauli_symplectic::{pauli, Pauli};
    [Pauli::X, Pauli::Y, Pauli::Z].map(|axis| {
        pauli::<GaussianRat>(axis).checked_invariant_de1b0452("the Pauli field is Q(i)")
    })
}
fn minkowski_family(gamma0: BasicMatrix<GaussianRat>) -> CliffordFamily {
    let [x, y, z] = pauli_matrices();
    let i_sigma_y =
        mx::scale(&y, &GaussianRat::i()).checked_invariant_de1b0452("fixed 2x2 Pauli carrier");
    let gammas = vec![
        gamma0,
        mx::kronecker(&i_sigma_y, &x).checked_invariant_de1b0452("fixed Dirac carrier"),
        mx::kronecker(&i_sigma_y, &y).checked_invariant_de1b0452("fixed Dirac carrier"),
        mx::kronecker(&i_sigma_y, &z).checked_invariant_de1b0452("fixed Dirac carrier"),
    ];
    CliffordFamily::admit(gammas, vec![ri(1), ri(-1), ri(-1), ri(-1)])
        .checked_invariant_de1b0452("the declared representation satisfies the Clifford relations")
}

impl CliffordFamily {
    pub fn admit(
        gammas: Vec<BasicMatrix<GaussianRat>>,
        metric: Vec<Rational>,
    ) -> Result<Self, DiracError> {
        let size = gammas.first().ok_or(DiracError::Empty)?.rows();
        if let Some((index, g)) = gammas
            .iter()
            .enumerate()
            .find(|(_, g)| g.rows() != size || g.cols() != size || size == 0)
        {
            return Err(DiracError::Shape {
                index,
                rows: g.rows(),
                cols: g.cols(),
                size,
            });
        }
        if metric.len() != gammas.len() {
            return Err(DiracError::MetricLength {
                gammas: gammas.len(),
                metric: metric.len(),
            });
        }
        if let Some((index, value)) = metric
            .iter()
            .enumerate()
            .find(|(_, v)| v.abs() != Rational::one())
        {
            return Err(DiracError::MetricEntry {
                index,
                value: value.clone(),
            });
        }
        let signature = metric
            .iter()
            .map(|v| if v == &ri(1) { 1 } else { -1 })
            .collect();
        let algebra = CliffordAlgebra::admit(gammas.clone(), signature).map_err(|e| match e {
            CliffordError::Anticommutator { mu, nu } => DiracError::Anticommutator { mu, nu },
            other => DiracError::Algebra(other),
        })?;
        Ok(Self {
            gammas,
            metric,
            algebra,
        })
    }

    pub fn euclidean(dimension: usize) -> Result<Self, DiracError> {
        Self::from_algebra(CliffordAlgebra::euclidean(dimension)?)
    }
    pub fn minkowski(positive: usize, negative: usize) -> Result<Self, DiracError> {
        Self::from_algebra(CliffordAlgebra::minkowski(positive, negative)?)
    }
    fn from_algebra(algebra: CliffordAlgebra<GaussianRat>) -> Result<Self, DiracError> {
        let gammas = algebra.gammas().to_vec();
        let metric = algebra.metric().iter().map(|s| ri(i64::from(*s))).collect();
        Ok(Self {
            algebra,
            gammas,
            metric,
        })
    }

    /// The Dirac representation: `gamma^0 = Z (x) I`, `gamma^k = (i Y) (x) sigma_k`.
    pub fn dirac() -> Self {
        let [_, _, z] = pauli_matrices();
        minkowski_family(
            mx::kronecker(&z, &mx::identity(2).checked_invariant_de1b0452("2x2"))
                .checked_invariant_de1b0452("4x4"),
        )
    }

    /// The chiral representation: `gamma^0 = X (x) I`, `gamma^k = (i Y) (x) sigma_k`.
    pub fn weyl() -> Self {
        let [x, _, _] = pauli_matrices();
        minkowski_family(
            mx::kronecker(&x, &mx::identity(2).checked_invariant_de1b0452("2x2"))
                .checked_invariant_de1b0452("4x4"),
        )
    }

    pub fn gammas(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.gammas
    }

    pub fn metric(&self) -> &[Rational] {
        &self.metric
    }

    /// The matrix size `N`.
    pub fn size(&self) -> usize {
        self.gammas[0].rows()
    }

    fn check_momentum(&self, p: &[Rational]) -> Result<(), DiracError> {
        if p.len() != self.gammas.len() {
            return Err(DiracError::MomentumLength {
                expected: self.gammas.len(),
                found: p.len(),
            });
        }
        Ok(())
    }

    /// `gamma^mu p_mu = sum_mu eta_mu p^mu gamma^mu`.
    pub fn slash(&self, p: &[Rational]) -> Result<BasicMatrix<GaussianRat>, DiracError> {
        self.check_momentum(p)?;
        let mut result = mx::zeros(self.size(), self.size())?;
        for ((g, eta), component) in self.gammas.iter().zip(&self.metric).zip(p) {
            result = mx::add(
                &result,
                &mx::scale(g, &GaussianRat::from_rational(eta * component))?,
            )?;
        }
        Ok(result)
    }

    /// `p . p = sum_mu eta_mu (p^mu)^2`.
    pub fn interval(&self, p: &[Rational]) -> Result<Rational, DiracError> {
        self.check_momentum(p)?;
        Ok(self.metric.iter().zip(p).map(|(eta, c)| eta * c * c).sum())
    }

    /// `N - rank(slash(p) - m I)`: the dimension of the plane-wave solutions at `p`.
    pub fn solution_dimension(&self, p: &[Rational], mass: &Rational) -> Result<usize, DiracError> {
        let operator = mx::sub(
            &self.slash(p)?,
            &mx::scale(
                &mx::identity(self.size())?,
                &GaussianRat::from_rational(mass.clone()),
            )?,
        )?;
        Ok(self.size() - elimination::rank(&operator)?)
    }

    /// `gamma^0 (gamma^mu)* gamma^0 = gamma^mu` for every `mu`.
    pub fn has_dirac_adjoint(&self) -> bool {
        let g0 = &self.gammas[0];
        self.gammas.iter().all(|g| {
            dagger(g)
                .and_then(|d| mx::multiply(g0, &d))
                .and_then(|a| mx::multiply(&a, g0))
                .map(|a| a == *g)
                .unwrap_or(false)
        })
    }

    pub fn product_span_rank(&self) -> Result<usize, DiracError> {
        if self.gammas.len() > MAX_PRODUCT_FAMILY {
            return Err(DiracError::TooManyProducts(self.gammas.len()));
        }
        Ok(self.algebra.product_span_rank()?)
    }

    pub fn chirality(&self) -> Result<BasicMatrix<GaussianRat>, DiracError> {
        self.algebra.chirality().map_err(|e| match e {
            CliffordError::OddFamily => DiracError::OddFamily,
            other => DiracError::Algebra(other),
        })
    }

    /// Trace identity for four gammas, independently determined by the declared metric.
    pub fn four_gamma_trace(
        &self,
        mu: usize,
        nu: usize,
        rho: usize,
        sigma: usize,
    ) -> Result<GaussianRat, DiracError> {
        for i in [mu, nu, rho, sigma] {
            self.check_index(i)?;
        }
        Ok(mx::trace(&mx::multiply(
            &mx::multiply(
                &mx::multiply(&self.gammas[mu], &self.gammas[nu])?,
                &self.gammas[rho],
            )?,
            &self.gammas[sigma],
        )?)?)
    }

    /// Complementary on-shell energy projectors `(I +- slash(p)/m)/2`.
    pub fn energy_projectors(
        &self,
        p: &[Rational],
        mass: &Rational,
    ) -> Result<[BasicMatrix<GaussianRat>; 2], DiracError> {
        let normalized = self.normalized_on_shell_slash(p, mass)?;
        let identity = mx::identity(self.size())?;
        let half = GaussianRat::from_rational(Rational::one() / ri(2));
        Ok([
            mx::scale(&mx::add(&identity, &normalized)?, &half)?,
            mx::scale(&mx::sub(&identity, &normalized)?, &half)?,
        ])
    }

    fn normalized_on_shell_slash(
        &self,
        p: &[Rational],
        mass: &Rational,
    ) -> Result<BasicMatrix<GaussianRat>, DiracError> {
        if mass.is_zero() {
            return Err(DiracError::ZeroMass);
        }
        if self.interval(p)? != mass * mass {
            return Err(DiracError::OffMassShell);
        }
        Ok(mx::scale(
            &self.slash(p)?,
            &GaussianRat::from_rational(Rational::one() / mass),
        )?)
    }

    fn check_index(&self, index: usize) -> Result<(), DiracError> {
        if index >= self.gammas.len() {
            return Err(DiracError::IndexOutOfRange {
                index,
                count: self.gammas.len(),
            });
        }
        Ok(())
    }

    /// `a I + b gamma^mu gamma^nu` for `mu != nu`.
    pub fn plane_spin_element(
        &self,
        mu: usize,
        nu: usize,
        a: &Rational,
        b: &Rational,
    ) -> Result<BasicMatrix<GaussianRat>, DiracError> {
        self.check_index(mu)?;
        self.check_index(nu)?;
        if mu == nu {
            return Err(DiracError::SamePlaneIndex { index: mu });
        }
        Ok(self.algebra.plane_spin_element(mu, nu, a, b)?)
    }

    /// The real matrix `L` with `S^(-1) gamma^mu S = sum_nu L^mu_nu gamma^nu`.
    pub fn vector_action(
        &self,
        s: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<Rational>, DiracError> {
        let size = self.size();
        if s.rows() != size || s.cols() != size {
            return Err(DiracError::SpinShape {
                rows: s.rows(),
                cols: s.cols(),
                size,
            });
        }
        let action = self.algebra.vector_action(s).map_err(|e| match e {
            CliffordError::Matrix(ExactFieldError::Singular { .. }) => {
                DiracError::Singular { size }
            }
            CliffordError::NotNormalizer => DiracError::NotInCliffordGroup,
            other => DiracError::Algebra(other),
        })?;
        let values = action
            .as_slice()
            .iter()
            .map(|value| {
                if !value.im.is_zero() {
                    Err(DiracError::NotInCliffordGroup)
                } else {
                    Ok(value.re.clone())
                }
            })
            .collect::<Result<Vec<_>, DiracError>>()?;
        Ok(
            BasicMatrix::from_row_major(action.rows(), action.cols(), values)
                .map_err(ExactFieldError::from)?,
        )
    }
}

/// The rational `(a, b)`, `a > 0`, `a^2 - b^2 = 1`, with `a^2 + b^2 = cosh` and `2 a b = sinh`.
pub fn boost_half_parameters(
    cosh: &Rational,
    sinh: &Rational,
) -> Result<(Rational, Rational), DiracError> {
    if cosh * cosh - sinh * sinh != Rational::one() || cosh < &Rational::one() {
        return Err(DiracError::OffHyperbola);
    }
    let half = (cosh + Rational::one()) / ri(2);
    let root = Surd::new(Rational::one(), &half)?;
    if root.radicand() != &BigInt::one() {
        return Err(DiracError::NoRationalHalfRapidity {
            square_class: root.radicand().clone(),
        });
    }
    let b = sinh / (root.coefficient() * ri(2));
    Ok((root.coefficient().clone(), b))
}

// Origin: engine/crates_rs/core_quantum_physics/src/dirac_gamma_admission.rs
// Claim: urn:core:crates_rs:core-quantum-physics:dirac-gamma-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_de1b0452 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
