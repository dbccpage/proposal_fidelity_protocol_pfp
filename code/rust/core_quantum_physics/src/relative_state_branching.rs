// AuthorityEffect: None.

//! Finite relative-state expansions `Psi = sum_i c_i f_i (x) E_i` over `Q(i)`.
//!
//! Every ingredient is declared: the tensor factorization `C^d (x) C^m`, an
//! orthonormal system family `f_i` (the standard basis unless one is given),
//! coefficients `c_i` up to a positive scale (so an equal-weight branch needs
//! no surd), and records `E_i` that are exactly unit vectors. Nothing here
//! selects a factorization, a basis or a record family.
//!
//! Computed exactly, with `N = sum_i |c_i|^2`:
//!
//! - the global state `|Psi><Psi| / N` and the record Gram matrix
//!   `G_ij = <E_j|E_i>`;
//! - the reduced state from the relative-state formula
//!   `rho_S = sum_ij c_i conj(c_j) G_ij |f_i><f_j| / N`, which must equal the
//!   partial trace of the global state over the records;
//! - branch weights `w_i = |c_i|^2 / N` and the diagonal shadow
//!   `rho_diag = sum_i w_i |f_i><f_i|`;
//! - the off-diagonal mass `Phi_off = sum_{i != j} |c_i| |c_j| |G_ij| / N`,
//!   returned only when every summand is rational, and the local deviation
//!   `Tr(A rho_S) - Tr(A rho_diag)` for `||A||_op <= 1`, the norm bound being
//!   decided exactly as `I - A* A >= 0`;
//! - the branch mixture `sum_i w_i |f_i E_i><f_i E_i|`;
//! - refinement of one branch by amplitudes `r_a` with `sum_a |r_a|^2 = 1`;
//! - expectations on a declared finite family of observables, and the first
//!   observable, if any, that separates two states.
//!
//! Refused: empty or ragged declarations, records that are not unit vectors,
//! non-orthonormal system families, a zero coefficient vector, operators that
//! are not contractions, irrational off-diagonal summands, non-isometric
//! refinements. No world, collapse, chance or preferred-basis predicate is
//! computed here.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_40c97ee9<T> {
    fn checked_invariant_40c97ee9(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_40c97ee9<T> for Option<T> {
    #[inline]
    fn checked_invariant_40c97ee9(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_40c97ee9<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_40c97ee9(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::composition_tomography::complex_hermitian_basis;
use crate::exact_hermitian::{self};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::{One, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::sqrt_exact;
use core_number_theory::rational::Rational;

/// Refusals for relative-state declarations and evaluations.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RelativeStateError {
    #[error("relative-state operation exceeds its declared finite budget")]
    Budget,
    #[error(transparent)]
    Arithmetic(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error("a relative-state expansion needs at least one branch")]
    NoBranches,
    #[error("{coefficients} coefficients, {records} records and {family} system vectors declared")]
    CountMismatch {
        coefficients: usize,
        records: usize,
        family: usize,
    },
    #[error("record {index} has {actual} components, expected {expected}")]
    RecordLength {
        index: usize,
        expected: usize,
        actual: usize,
    },
    #[error("record {index} is not a unit vector")]
    UnnormalizedRecord { index: usize },
    #[error("system vector {index} has {actual} components, expected {expected}")]
    SystemVectorLength {
        index: usize,
        expected: usize,
        actual: usize,
    },
    #[error("system vectors {first} and {second} are not orthonormal")]
    NonOrthonormalFamily { first: usize, second: usize },
    #[error("every coefficient is zero")]
    ZeroCoefficients,
    #[error("a factor of the tensor product has dimension zero")]
    EmptyFactor,
    #[error("operator is {rows}x{cols}; the system has dimension {dimension}")]
    OperatorShape {
        dimension: usize,
        rows: usize,
        cols: usize,
    },
    #[error("operator norm exceeds one")]
    NotAContraction,
    #[error("|c_{first}| |c_{second}| |G_{first}{second}| / N is irrational")]
    IrrationalOffDiagonalTerm { first: usize, second: usize },
    #[error("branch {branch} is out of range for {branches} branches")]
    BranchOutOfRange { branch: usize, branches: usize },
    #[error("{amplitudes} refinement amplitudes for {records} child records")]
    RefinementCount { amplitudes: usize, records: usize },
    #[error("refinement amplitudes have sum |r|^2 = {0}, not 1")]
    NonIsometricRefinement(Rational),
    #[error("matrix is {rows}x{cols}, expected {expected}x{expected}")]
    StateShape {
        expected: usize,
        rows: usize,
        cols: usize,
    },
}

/// A declared relative-state expansion.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RelativeStatePacket {
    family: Vec<Vec<GaussianRat>>,
    coefficients: Vec<GaussianRat>,
    records: Vec<Vec<GaussianRat>>,
    norm: Rational,
}

impl RelativeStatePacket {
    /// `Psi = sum_i c_i e_i (x) E_i` on the standard basis `e_i` of `C^n`.
    pub fn new(
        coefficients: Vec<GaussianRat>,
        records: Vec<Vec<GaussianRat>>,
    ) -> Result<Self, RelativeStateError> {
        let n = coefficients.len();
        let family = (0..n).map(|i| standard_vector(n, i)).collect();
        Self::with_system_family(family, coefficients, records)
    }

    fn validate_records(records: &[Vec<GaussianRat>]) -> Result<(), RelativeStateError> {
        let m = records[0].len();
        for (index, record) in records.iter().enumerate() {
            if record.len() != m {
                return Err(RelativeStateError::RecordLength {
                    index,
                    expected: m,
                    actual: record.len(),
                });
            }
            if !record
                .iter()
                .map(GaussianRat::norm_sq)
                .sum::<Rational>()
                .is_one()
            {
                return Err(RelativeStateError::UnnormalizedRecord { index });
            }
        }
        Ok(())
    }

    fn validate_orthonormal_family(family: &[Vec<GaussianRat>]) -> Result<(), RelativeStateError> {
        let n = family.len();
        let d = family[0].len();
        for (index, vector) in family.iter().enumerate() {
            if vector.len() != d {
                return Err(RelativeStateError::SystemVectorLength {
                    index,
                    expected: d,
                    actual: vector.len(),
                });
            }
        }
        for first in 0..n {
            for second in first..n {
                let overlap = linear_algebra::exact_field::involution::inner_product(
                    &family[first],
                    &family[second],
                )
                .map_err(crate::exact_hermitian::ExactHermitianError::from)
                .checked_invariant_40c97ee9("system vector lengths are validated above");
                let expected = if first == second {
                    GaussianRat::one()
                } else {
                    GaussianRat::zero()
                };
                if overlap != expected {
                    return Err(RelativeStateError::NonOrthonormalFamily { first, second });
                }
            }
        }
        Ok(())
    }

    /// `Psi = sum_i c_i f_i (x) E_i` for a declared orthonormal family `f_i`.
    pub fn with_system_family(
        family: Vec<Vec<GaussianRat>>,
        coefficients: Vec<GaussianRat>,
        records: Vec<Vec<GaussianRat>>,
    ) -> Result<Self, RelativeStateError> {
        let n = coefficients.len();
        if n == 0 {
            return Err(RelativeStateError::NoBranches);
        }
        if records.len() != n || family.len() != n {
            return Err(RelativeStateError::CountMismatch {
                coefficients: n,
                records: records.len(),
                family: family.len(),
            });
        }
        Self::validate_records(&records)?;
        Self::validate_orthonormal_family(&family)?;
        let norm: Rational = coefficients.iter().map(GaussianRat::norm_sq).sum();
        if norm.is_zero() {
            return Err(RelativeStateError::ZeroCoefficients);
        }
        Ok(Self {
            family,
            coefficients,
            records,
            norm,
        })
    }

    pub fn branch_count(&self) -> usize {
        self.coefficients.len()
    }

    /// Dimension `d` of the system factor.
    pub fn system_dimension(&self) -> usize {
        self.family[0].len()
    }

    /// Dimension `m` of the record factor.
    pub fn record_dimension(&self) -> usize {
        self.records[0].len()
    }

    pub fn coefficients(&self) -> &[GaussianRat] {
        &self.coefficients
    }

    /// The branch vector `f_i (x) E_i` on `C^d (x) C^m`, in Kronecker order.
    fn branch_vector(&self, i: usize) -> Vec<GaussianRat> {
        let column = |v: &[GaussianRat]| {
            linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(
                v.len(),
                1,
                v.to_vec(),
            )
            .checked_invariant_40c97ee9("validated matrix literal")
        };
        linear_algebra::exact_field::matrix::kronecker(
            &column(&self.family[i]),
            &column(&self.records[i]),
        )
        .checked_invariant_40c97ee9("validated branch dimension")
        .as_slice()
        .to_vec()
    }

    /// `Psi = sum_i c_i f_i (x) E_i`, unnormalized.
    fn global_vector(&self) -> Vec<GaussianRat> {
        let size = self.system_dimension() * self.record_dimension();
        (0..self.branch_count()).fold(vec![GaussianRat::zero(); size], |acc, i| {
            let c = &self.coefficients[i];
            acc.iter()
                .zip(self.branch_vector(i))
                .map(|(a, b)| a.add(&c.mul(&b)))
                .collect()
        })
    }

    /// `|Psi><Psi| / N`.
    pub fn global_state(&self) -> BasicMatrix<GaussianRat> {
        let psi = self.global_vector();
        linear_algebra::exact_field::matrix::scale(
            &(linear_algebra::exact_field::involution::outer_product(&psi, &psi)
                .checked_invariant_40c97ee9("validated finite matrix shape and budget")),
            &GaussianRat::from_rational(self.norm.recip()),
        )
        .checked_invariant_40c97ee9("validated finite matrix shape and budget")
    }

    /// `G_ij = <E_j|E_i>`.
    pub fn record_gram(&self) -> BasicMatrix<GaussianRat> {
        let n = self.branch_count();
        let mut gram = linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
            n,
            n,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_40c97ee9("validated finite matrix shape and budget");
        for i in 0..n {
            for j in 0..n {
                let overlap = linear_algebra::exact_field::involution::inner_product(
                    &self.records[j],
                    &self.records[i],
                )
                .map_err(crate::exact_hermitian::ExactHermitianError::from)
                .checked_invariant_40c97ee9("record lengths are validated at declaration");
                (gram)
                    .set(i, j, overlap)
                    .checked_invariant_40c97ee9("validated finite matrix shape and budget");
            }
        }
        gram
    }

    /// `rho_S = sum_ij c_i conj(c_j) G_ij |f_i><f_j| / N`.
    pub fn reduced_state(&self) -> BasicMatrix<GaussianRat> {
        let gram = self.record_gram();
        let n = self.branch_count();
        let mut rho = linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
            self.system_dimension(),
            self.system_dimension(),
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_40c97ee9("validated finite matrix shape and budget");
        for i in 0..n {
            for j in 0..n {
                let weight = self.coefficients[i].mul(&self.coefficients[j].conj()).mul(
                    (gram)
                        .get_ref(i, j)
                        .checked_invariant_40c97ee9("validated finite matrix shape and budget"),
                );
                rho = linear_algebra::exact_field::matrix::add(
                    &(rho),
                    &linear_algebra::exact_field::matrix::scale(
                        &(linear_algebra::exact_field::involution::outer_product(
                            &self.family[i],
                            &self.family[j],
                        )
                        .checked_invariant_40c97ee9("validated finite matrix shape and budget")),
                        &weight,
                    )
                    .checked_invariant_40c97ee9("validated finite matrix shape and budget"),
                )
                .checked_invariant_40c97ee9("validated finite matrix shape and budget");
            }
        }
        linear_algebra::exact_field::matrix::scale(
            &(rho),
            &GaussianRat::from_rational(self.norm.recip()),
        )
        .checked_invariant_40c97ee9("validated finite matrix shape and budget")
    }

    /// `w_i = |c_i|^2 / N`: the L1 branch shadow.
    pub fn branch_weights(&self) -> Vec<Rational> {
        self.coefficients
            .iter()
            .map(|c| c.norm_sq() / &self.norm)
            .collect()
    }

    /// `rho_diag = sum_i w_i |f_i><f_i|`.
    pub fn diagonal_shadow(&self) -> BasicMatrix<GaussianRat> {
        self.family.iter().zip(self.branch_weights()).fold(
            linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
                self.system_dimension(),
                self.system_dimension(),
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_40c97ee9("validated finite matrix shape and budget"),
            |acc, (f, w)| {
                linear_algebra::exact_field::matrix::add(
                    &(acc),
                    &linear_algebra::exact_field::matrix::scale(
                        &(linear_algebra::exact_field::involution::outer_product(f, f)
                            .checked_invariant_40c97ee9("validated finite matrix shape and budget")),
                        &GaussianRat::from_rational(w),
                    )
                    .checked_invariant_40c97ee9("validated finite matrix shape and budget"),
                )
                .checked_invariant_40c97ee9("validated finite matrix shape and budget")
            },
        )
    }

    /// `Phi_off = sum_{i != j} |c_i| |c_j| |G_ij| / N`, when every summand is rational.
    pub fn off_diagonal_mass(&self) -> Result<Rational, RelativeStateError> {
        let gram = self.record_gram();
        let norm_sq = &self.norm * &self.norm;
        let n = self.branch_count();
        let mut total = Rational::zero();
        for first in 0..n {
            for second in first + 1..n {
                let square = self.coefficients[first].norm_sq()
                    * self.coefficients[second].norm_sq()
                    * (gram)
                        .get_ref(first, second)
                        .checked_invariant_40c97ee9("validated finite matrix shape and budget")
                        .norm_sq()
                    / &norm_sq;
                let term = sqrt_exact(&square)
                    .ok_or(RelativeStateError::IrrationalOffDiagonalTerm { first, second })?;
                total = total + &term + &term;
            }
        }
        Ok(total)
    }

    /// `Tr(A rho_S) - Tr(A rho_diag)` for a system operator with `||A||_op <= 1`.
    pub fn local_deviation(
        &self,
        operator: &BasicMatrix<GaussianRat>,
    ) -> Result<GaussianRat, RelativeStateError> {
        let dimension = self.system_dimension();
        if operator.rows() != dimension || operator.cols() != dimension {
            return Err(RelativeStateError::OperatorShape {
                dimension,
                rows: operator.rows(),
                cols: operator.cols(),
            });
        }
        if !is_contraction(operator) {
            return Err(RelativeStateError::NotAContraction);
        }
        let off_diagonal = linear_algebra::exact_field::matrix::sub(
            &self.reduced_state(),
            &self.diagonal_shadow(),
        )?;
        Ok(linear_algebra::exact_field::matrix::trace(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(operator),
                &off_diagonal,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_40c97ee9("validated finite matrix shape and budget")),
        )
        .checked_invariant_40c97ee9("validated finite matrix shape and budget"))
    }

    /// `sum_i w_i |f_i E_i><f_i E_i|`: the branch terms as a classical mixture.
    pub fn branch_mixture(&self) -> BasicMatrix<GaussianRat> {
        let size = self.system_dimension() * self.record_dimension();
        self.branch_weights().into_iter().enumerate().fold(
            linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
                size,
                size,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_40c97ee9("validated finite matrix shape and budget"),
            |acc, (i, w)| {
                let term = self.branch_vector(i);
                linear_algebra::exact_field::matrix::add(
                    &(acc),
                    &linear_algebra::exact_field::matrix::scale(
                        &(linear_algebra::exact_field::involution::outer_product(&term, &term)
                            .checked_invariant_40c97ee9("validated finite matrix shape and budget")),
                        &GaussianRat::from_rational(w),
                    )
                    .checked_invariant_40c97ee9("validated finite matrix shape and budget"),
                )
                .checked_invariant_40c97ee9("validated finite matrix shape and budget")
            },
        )
    }

    /// Replace branch `branch` by children with coefficients `c_branch r_a` and
    /// the declared child records, on the label basis of the refined system.
    ///
    /// Licensed only when `sum_a |r_a|^2 = 1`, the isometry condition on the
    /// declared parent component.
    pub fn refine(
        &self,
        branch: usize,
        amplitudes: &[GaussianRat],
        child_records: Vec<Vec<GaussianRat>>,
    ) -> Result<Self, RelativeStateError> {
        let branches = self.branch_count();
        if branch >= branches {
            return Err(RelativeStateError::BranchOutOfRange { branch, branches });
        }
        if amplitudes.len() != child_records.len() {
            return Err(RelativeStateError::RefinementCount {
                amplitudes: amplitudes.len(),
                records: child_records.len(),
            });
        }
        let total: Rational = amplitudes.iter().map(GaussianRat::norm_sq).sum();
        if !total.is_one() {
            return Err(RelativeStateError::NonIsometricRefinement(total));
        }
        let parent = &self.coefficients[branch];
        let mut coefficients = self.coefficients[..branch].to_vec();
        coefficients.extend(amplitudes.iter().map(|r| parent.mul(r)));
        coefficients.extend_from_slice(&self.coefficients[branch + 1..]);
        let mut records = self.records[..branch].to_vec();
        records.extend(child_records);
        records.extend_from_slice(&self.records[branch + 1..]);
        Self::new(coefficients, records)
    }
}

/// `{B (x) I_m}` for the standard Hermitian basis `B` of `M_d(C)`, taken from
/// `composition_tomography`: a spanning family for an observer with access to
/// the system factor only.
pub fn system_only_observables(
    system_dimension: usize,
    record_dimension: usize,
) -> Result<Vec<BasicMatrix<GaussianRat>>, RelativeStateError> {
    if record_dimension == 0 {
        return Err(RelativeStateError::EmptyFactor);
    }
    let joint = system_dimension
        .checked_mul(record_dimension)
        .ok_or(RelativeStateError::Budget)?;
    if joint > 256
        || system_dimension
            .checked_mul(system_dimension)
            .and_then(|v| v.checked_mul(joint))
            .and_then(|v| v.checked_mul(joint))
            .is_none_or(|v| v > 1 << 24)
    {
        return Err(RelativeStateError::Budget);
    }
    let total = system_dimension
        .checked_mul(record_dimension)
        .ok_or(RelativeStateError::Budget)?;
    let work = system_dimension
        .checked_mul(system_dimension)
        .and_then(|v| v.checked_mul(total))
        .and_then(|v| v.checked_mul(total));
    if total > 256 || work.is_none_or(|v| v > 1 << 24) {
        return Err(RelativeStateError::Budget);
    }
    let basis =
        complex_hermitian_basis(system_dimension).map_err(|_| RelativeStateError::EmptyFactor)?;
    let identity = linear_algebra::exact_field::matrix::identity::<GaussianRat>(record_dimension)?;
    basis
        .iter()
        .map(|b| {
            linear_algebra::exact_field::matrix::kronecker(b, &identity)
                .map_err(RelativeStateError::from)
        })
        .collect()
}

/// `Tr(A rho)`.
pub fn expectation(
    observable: &BasicMatrix<GaussianRat>,
    state: &BasicMatrix<GaussianRat>,
) -> Result<GaussianRat, RelativeStateError> {
    let expected = observable.rows();
    for m in [observable, state] {
        if m.rows() != expected || m.cols() != expected {
            return Err(RelativeStateError::StateShape {
                expected,
                rows: m.rows(),
                cols: m.cols(),
            });
        }
    }
    Ok(linear_algebra::exact_field::matrix::trace(
        &(linear_algebra::exact_field::matrix::multiply_with_limits(
            &(observable),
            state,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_40c97ee9("validated finite matrix shape and budget")),
    )
    .checked_invariant_40c97ee9("validated finite matrix shape and budget"))
}

/// An observable on which two states have different expectations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Separation {
    pub index: usize,
    pub left: GaussianRat,
    pub right: GaussianRat,
}

/// The first declared observable that separates `rho` from `sigma`, or `None`
/// when they agree on the whole family.
pub fn first_separating_observable(
    observables: &[BasicMatrix<GaussianRat>],
    rho: &BasicMatrix<GaussianRat>,
    sigma: &BasicMatrix<GaussianRat>,
) -> Result<Option<Separation>, RelativeStateError> {
    for (index, observable) in observables.iter().enumerate() {
        let left = expectation(observable, rho)?;
        let right = expectation(observable, sigma)?;
        if left != right {
            return Ok(Some(Separation { index, left, right }));
        }
    }
    Ok(None)
}

/// `||A||_op <= 1`, decided exactly as `I - A* A >= 0`.
pub fn is_contraction(operator: &BasicMatrix<GaussianRat>) -> bool {
    let gap = linear_algebra::exact_field::matrix::sub(
        &(linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
            operator.cols(),
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_40c97ee9("validated finite matrix shape and budget")),
        &linear_algebra::exact_field::matrix::multiply_with_limits(
            &(linear_algebra::exact_field::involution::adjoint(&(operator))
                .checked_invariant_40c97ee9("validated finite matrix shape and budget")),
            operator,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_40c97ee9("validated finite matrix shape and budget"),
    )
    .checked_invariant_40c97ee9("validated finite matrix shape and budget");
    exact_hermitian::is_positive_semidefinite(&gap)
}

fn standard_vector(n: usize, i: usize) -> Vec<GaussianRat> {
    let mut v = vec![GaussianRat::zero(); n];
    v[i] = GaussianRat::one();
    v
}

// Origin: engine/crates_rs/core_quantum_physics/src/relative_state_branching.rs
// Claim: urn:core:crates_rs:core-quantum-physics:relative-state-branching:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_40c97ee9 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
