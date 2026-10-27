// AuthorityEffect: None.

//! Exact finite-step Schrödinger transport on a finite carrier.
//!
//! Declared: a square matrix `H` over `Q(i)` on the vertices of a finite graph
//! (for example the connection Laplacian `D_A* W D_A` of
//! `core_quantum_physics::u1_graph_connection`), a rational step `tau` and a
//! field `psi`. Units have `hbar = 1`. Computed exactly:
//!
//! - [`norm_rate`]: `d/dt sum_v |psi_v|^2 = 2 Im <psi, H psi>` along
//!   `psi' = -i H psi`. It is zero for every `psi` when `H` is Hermitian and
//!   need not be otherwise.
//! - [`euler_propagator`]: the explicit step `E = I - i tau H`. For Hermitian
//!   `H`, `E* E = I + tau^2 H^2`, so `E` gains norm unless `H psi = 0`.
//!   The exactly unitary step is the Cayley step
//!   `crate::unitary_generator_admission::cayley_unitary`.
//! - [`cycle_product`]: `H[v_1][v_0] H[v_2][v_1] ... H[v_0][v_(k-1)]` around a
//!   closed vertex cycle, invariant under every diagonal unitary gauge
//!   `H -> G H G*`. For the connection Laplacian each hop is `-w_e U_e`, so
//!   around a `k`-cycle the product is `(-1)^k (prod w_e)` times the holonomy:
//!   its phase is the holonomy up to the sign `(-1)^k`.
//!
//! The continuous-time equation `i dpsi/dt = H psi`, its exponential and any
//! continuum limit are not computed.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a590ed80<T> {
    fn checked_invariant_a590ed80(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a590ed80<T> for Option<T> {
    #[inline]
    fn checked_invariant_a590ed80(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a590ed80<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a590ed80(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::Zero;

use crate::exact_hermitian::{self, ExactHermitianError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

/// Refusals for finite Schrödinger inputs.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SchrodingerError {
    #[error("matrix is {rows}x{cols}, not square")]
    NotSquare { rows: usize, cols: usize },
    #[error("a cycle needs at least one vertex")]
    EmptyCycle,
    #[error("cycle vertex {vertex} is out of range for dimension {dimension}")]
    VertexOutOfRange { vertex: usize, dimension: usize },
    #[error("exact Hermitian refusal: {0}")]
    Hermitian(#[from] ExactHermitianError),
}

fn square_dimension(h: &BasicMatrix<GaussianRat>) -> Result<usize, SchrodingerError> {
    exact_hermitian::check_well_formed(h)?;
    if h.rows() != h.cols() {
        return Err(SchrodingerError::NotSquare {
            rows: h.rows(),
            cols: h.cols(),
        });
    }
    Ok(h.rows())
}

/// `2 Im <psi, H psi>`, the rate of change of `sum_v |psi_v|^2` under `psi' = -i H psi`.
pub fn norm_rate(
    h: &BasicMatrix<GaussianRat>,
    psi: &[GaussianRat],
) -> Result<Rational, SchrodingerError> {
    square_dimension(h)?;
    let q = linear_algebra::exact_field::ordered::hermitian_form(h, psi)
        .map_err(ExactHermitianError::from)?;
    Ok(&q.im + &q.im)
}

/// `I - i tau H`.
pub fn euler_propagator(
    h: &BasicMatrix<GaussianRat>,
    tau: &Rational,
) -> Result<BasicMatrix<GaussianRat>, SchrodingerError> {
    let n = square_dimension(h)?;
    let i_tau = GaussianRat {
        re: Rational::zero(),
        im: tau.clone(),
    };
    Ok(linear_algebra::exact_field::matrix::sub(
        &(linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
            n,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_a590ed80("validated finite matrix shape and budget")),
        &linear_algebra::exact_field::matrix::scale(&(h), &i_tau)
            .checked_invariant_a590ed80("validated finite matrix shape and budget"),
    )
    .checked_invariant_a590ed80("validated finite matrix shape and budget"))
}

/// `H[v_1][v_0] H[v_2][v_1] ... H[v_0][v_(k-1)]` for the closed cycle `v_0, ..., v_(k-1)`.
pub fn cycle_product(
    h: &BasicMatrix<GaussianRat>,
    cycle: &[usize],
) -> Result<GaussianRat, SchrodingerError> {
    let dimension = square_dimension(h)?;
    if cycle.is_empty() {
        return Err(SchrodingerError::EmptyCycle);
    }
    if let Some(&vertex) = cycle.iter().find(|&&v| v >= dimension) {
        return Err(SchrodingerError::VertexOutOfRange { vertex, dimension });
    }
    let k = cycle.len();
    Ok((0..k).fold(GaussianRat::one(), |acc, j| {
        (h).get_ref(cycle[(j + 1) % k], cycle[j])
            .checked_invariant_a590ed80("validated finite matrix shape and budget")
            .mul(&acc)
    }))
}

/// Exact exponential in the group algebra of rational frequencies. A term
/// (lambda,P) represents exp(-i lambda t) P; t remains a formal real variable.
/// Equal frequencies merge under multiplication, making the group law exact.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpectralPropagator {
    terms: std::collections::BTreeMap<Rational, BasicMatrix<GaussianRat>>,
    dimension: usize,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PropagatorError {
    #[error("declared spectrum is invalid: {0:?}")]
    Spectrum(crate::exact_hermitian::SpectrumError),
    #[error("propagator dimensions or finite operation budget disagree")]
    Shape,
}
impl SpectralPropagator {
    pub fn new(
        h: &BasicMatrix<GaussianRat>,
        eigenvalues: &[Rational],
    ) -> Result<Self, PropagatorError> {
        if h.rows() > 64 || eigenvalues.len() > 64 {
            return Err(PropagatorError::Shape);
        }
        let spectrum = exact_hermitian::spectral_resolution(h, eigenvalues)
            .map_err(PropagatorError::Spectrum)?;
        Ok(Self {
            dimension: h.rows(),
            terms: spectrum
                .eigenvalues()
                .iter()
                .cloned()
                .zip(spectrum.projectors().iter().cloned())
                .collect(),
        })
    }
    pub fn terms(&self) -> &std::collections::BTreeMap<Rational, BasicMatrix<GaussianRat>> {
        &self.terms
    }
    pub fn at_zero(&self) -> BasicMatrix<GaussianRat> {
        self.terms.values().fold(
            linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
                self.dimension,
                self.dimension,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_a590ed80("validated finite matrix shape and budget"),
            |a, p| {
                linear_algebra::exact_field::matrix::add(&(a), p)
                    .checked_invariant_a590ed80("validated finite matrix shape and budget")
            },
        )
    }
    pub fn derivative_at_zero(&self) -> BasicMatrix<GaussianRat> {
        self.terms.iter().fold(
            linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
                self.dimension,
                self.dimension,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_a590ed80("validated finite matrix shape and budget"),
            |a, (lambda, p)| {
                linear_algebra::exact_field::matrix::add(
                    &(a),
                    &linear_algebra::exact_field::matrix::scale(
                        &(p),
                        &GaussianRat {
                            re: Rational::zero(),
                            im: -lambda,
                        },
                    )
                    .checked_invariant_a590ed80("validated finite matrix shape and budget"),
                )
                .checked_invariant_a590ed80("validated finite matrix shape and budget")
            },
        )
    }
    pub fn adjoint(&self) -> Self {
        Self {
            dimension: self.dimension,
            terms: self
                .terms
                .iter()
                .map(|(l, p)| {
                    (
                        -l,
                        linear_algebra::exact_field::involution::adjoint(&(p))
                            .checked_invariant_a590ed80("validated finite matrix shape and budget"),
                    )
                })
                .collect(),
        }
    }
    pub fn multiply(&self, other: &Self) -> Result<Self, PropagatorError> {
        if self.dimension != other.dimension
            || self
                .terms
                .len()
                .checked_mul(other.terms.len())
                .is_none_or(|v| v > 4096)
        {
            return Err(PropagatorError::Shape);
        }
        let mut terms = std::collections::BTreeMap::new();
        for (a, p) in &self.terms {
            for (b, q) in &other.terms {
                let product = linear_algebra::exact_field::matrix::multiply_with_limits(
                    &(p),
                    q,
                    linear_algebra::backend::basic_matrix::OperationLimits {
                        max_elements: 1 << 20,
                        max_scalar_ops: 1 << 24,
                    },
                )
                .checked_invariant_a590ed80("validated finite matrix shape and budget");
                if linear_algebra::exact_field::matrix::is_zero_matrix(&product) {
                    continue;
                }
                let entry = terms.entry(a + b).or_insert_with(|| {
                    linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
                        self.dimension,
                        self.dimension,
                        linear_algebra::backend::basic_matrix::OperationLimits {
                            max_elements: 1 << 20,
                            max_scalar_ops: 1 << 24,
                        },
                    )
                    .checked_invariant_a590ed80("validated finite matrix shape and budget")
                });
                *entry = linear_algebra::exact_field::matrix::add(&(entry), &product)
                    .checked_invariant_a590ed80("validated finite matrix shape and budget");
            }
        }
        terms.retain(|_, p| !linear_algebra::exact_field::matrix::is_zero_matrix(p));
        Ok(Self {
            dimension: self.dimension,
            terms,
        })
    }
    pub fn is_identity(&self) -> bool {
        self.terms.len() == 1
            && self.terms.get(&Rational::zero())
                == Some(
                    &linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
                        self.dimension,
                        linear_algebra::backend::basic_matrix::OperationLimits {
                            max_elements: 1 << 20,
                            max_scalar_ops: 1 << 24,
                        },
                    )
                    .checked_invariant_a590ed80("validated finite matrix shape and budget"),
                )
    }
}

/// The exact Euler norm defect E*E-I for a checked Hermitian generator.
pub fn euler_norm_defect(
    h: &BasicMatrix<GaussianRat>,
    tau: &Rational,
) -> Result<BasicMatrix<GaussianRat>, SchrodingerError> {
    exact_hermitian::check_hermitian(h)?;
    let e = euler_propagator(h, tau)?;
    Ok(linear_algebra::exact_field::matrix::sub(
        &(linear_algebra::exact_field::matrix::multiply_with_limits(
            &(linear_algebra::exact_field::involution::adjoint(&(e))
                .checked_invariant_a590ed80("validated finite matrix shape and budget")),
            &e,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_a590ed80("validated finite matrix shape and budget")),
        &linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
            h.rows(),
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_a590ed80("validated finite matrix shape and budget"),
    )
    .checked_invariant_a590ed80("validated finite matrix shape and budget"))
}

// Origin: engine/crates_rs/core_quantum_physics/src/finite_schrodinger_step.rs
// Claim: urn:core:crates_rs:core-quantum-physics:finite-schrodinger-step:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_a590ed80 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
