//! Finite unital star-subalgebras of matrices over Q(i), with exact closure,
//! commutants and centers. No continuum operator algebra is represented.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::exact_hermitian::{self, gi};
use linear_algebra::backend::basic_matrix::OperationLimits;
use linear_algebra::exact_field::{commutant, involution, matrix};
use linear_algebra::{backend::basic_matrix::BasicMatrix, exact_field::elimination};
use core_number_theory::cyclotomic::GaussianRat;
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite operator algebras.";
pub const MAX_ALGEBRA_HILBERT_DIMENSION: usize = 16;
pub const MAX_ALGEBRA_CANDIDATES: usize = 1 << 18;
const LIMITS: OperationLimits = OperationLimits {
    max_elements: 1 << 20,
    max_scalar_ops: 1 << 28,
};
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AlgebraError {
    #[error(transparent)]
    ExactAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("Hilbert dimension must be in 1..=16")]
    Dimension,
    #[error("operator does not act on the declared carrier")]
    Shape,
    #[error("algebra closure exhausted the budget {limit}")]
    Budget { limit: usize },
    #[error("exact matrix operation refused: {0}")]
    Matrix(String),
}
fn matrix_error(e: impl std::fmt::Display) -> AlgebraError {
    AlgebraError::Matrix(e.to_string())
}
/// Closed, linearly independent basis, with the identity included.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalOperatorAlgebra {
    hilbert_dim: usize,
    basis: Vec<BasicMatrix<GaussianRat>>,
}
fn basis_matrix(
    basis: &[BasicMatrix<GaussianRat>],
    columns: usize,
) -> Result<BasicMatrix<GaussianRat>, AlgebraError> {
    BasicMatrix::from_row_major(
        basis.len(),
        columns,
        basis
            .iter()
            .flat_map(|b| b.as_slice().iter().cloned())
            .collect(),
    )
    .map_err(matrix_error)
}
fn independent(
    basis: &[BasicMatrix<GaussianRat>],
    candidate: &BasicMatrix<GaussianRat>,
) -> Result<bool, AlgebraError> {
    let mut rows = basis.to_vec();
    rows.push(candidate.clone());
    Ok(
        elimination::rank_with_limits(&basis_matrix(&rows, candidate.as_slice().len())?, LIMITS)
            .map_err(matrix_error)?
            > basis.len(),
    )
}
fn validate_generator_inputs(
    hilbert_dim: usize,
    generators: &[BasicMatrix<GaussianRat>],
    budget: usize,
) -> Result<usize, AlgebraError> {
    if !(1..=MAX_ALGEBRA_HILBERT_DIMENSION).contains(&hilbert_dim) {
        return Err(AlgebraError::Dimension);
    }
    let budget = budget.min(MAX_ALGEBRA_CANDIDATES);
    if generators.len() > budget {
        return Err(AlgebraError::Budget { limit: budget });
    }
    for g in generators {
        if exact_hermitian::square_dim(g).map_err(matrix_error)? != hilbert_dim {
            return Err(AlgebraError::Shape);
        }
    }
    Ok(budget)
}

fn insert_candidate_with_budget(
    basis: &mut Vec<BasicMatrix<GaussianRat>>,
    used: &mut usize,
    budget: usize,
    candidate: BasicMatrix<GaussianRat>,
) -> Result<(), AlgebraError> {
    if *used >= budget {
        return Err(AlgebraError::Budget { limit: budget });
    }
    *used += 1;
    if independent(basis, &candidate)? {
        basis.push(candidate);
    }
    Ok(())
}

fn close_algebra_basis(
    basis: &mut Vec<BasicMatrix<GaussianRat>>,
    used: &mut usize,
    budget: usize,
) -> Result<(), AlgebraError> {
    let mut cursor = 0;
    while cursor < basis.len() {
        let a = basis[cursor].clone();
        insert_candidate_with_budget(basis, used, budget, involution::adjoint(&a)?)?;
        let count = basis.len();
        for j in 0..count {
            let b = basis[j].clone();
            insert_candidate_with_budget(basis, used, budget, matrix::multiply(&a, &b)?)?;
            insert_candidate_with_budget(basis, used, budget, matrix::multiply(&b, &a)?)?;
        }
        cursor += 1;
    }
    Ok(())
}

impl LocalOperatorAlgebra {
    pub fn from_generators(
        hilbert_dim: usize,
        generators: &[BasicMatrix<GaussianRat>],
        budget: usize,
    ) -> Result<Self, AlgebraError> {
        let budget = validate_generator_inputs(hilbert_dim, generators, budget)?;
        let mut basis = vec![matrix::identity(hilbert_dim)?];
        let mut used = 0;
        for g in generators {
            insert_candidate_with_budget(&mut basis, &mut used, budget, g.clone())?;
        }
        close_algebra_basis(&mut basis, &mut used, budget)?;
        Ok(Self { hilbert_dim, basis })
    }
    pub fn hilbert_dimension(&self) -> usize {
        self.hilbert_dim
    }
    pub fn dimension(&self) -> usize {
        self.basis.len()
    }
    pub fn basis(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.basis
    }
    pub fn contains(&self, op: &BasicMatrix<GaussianRat>) -> Result<bool, AlgebraError> {
        if exact_hermitian::square_dim(op).map_err(matrix_error)? != self.hilbert_dim {
            return Err(AlgebraError::Shape);
        }
        Ok(!independent(&self.basis, op)?)
    }
    pub fn is_subalgebra_of(&self, other: &Self) -> Result<bool, AlgebraError> {
        if self.hilbert_dim != other.hilbert_dim {
            return Err(AlgebraError::Shape);
        }
        for a in &self.basis {
            if !other.contains(a)? {
                return Ok(false);
            }
        }
        Ok(true)
    }
    pub fn same_algebra(&self, other: &Self) -> Result<bool, AlgebraError> {
        Ok(self.dimension() == other.dimension() && self.is_subalgebra_of(other)?)
    }
    pub fn commutes_with(&self, other: &Self) -> Result<bool, AlgebraError> {
        if self.hilbert_dim != other.hilbert_dim {
            return Err(AlgebraError::Shape);
        }
        for a in &self.basis {
            for b in &other.basis {
                if !matrix::is_zero_matrix(&matrix::commutator(a, b)?) {
                    return Ok(false);
                }
            }
        }
        Ok(true)
    }
    /// Kernel of the simultaneous commutator maps [A_k,X].
    pub fn commutant(&self) -> Result<Self, AlgebraError> {
        Ok(Self {
            hilbert_dim: self.hilbert_dim,
            basis: commutant::commutant_basis_with_limits(self.hilbert_dim, &self.basis, LIMITS)?,
        })
    }
    /// Compute central linear combinations of the algebra's basis; individual
    /// commuting basis elements alone would miss a general center.
    pub fn center(&self) -> Result<Self, AlgebraError> {
        let map = self.build_commutator_map()?;
        let vectors = elimination::kernel_basis_with_limits(&map, LIMITS)?;
        let basis = vectors
            .iter()
            .map(|v| self.combine_basis_with_coefficients(v))
            .collect::<Result<Vec<_>, _>>()?;
        Ok(Self {
            hilbert_dim: self.hilbert_dim,
            basis,
        })
    }

    fn build_commutator_map(&self) -> Result<BasicMatrix<GaussianRat>, AlgebraError> {
        let n = self.hilbert_dim;
        let columns = self.dimension();
        // Preflight canonical dense storage before any commutator materialization.
        let mut map = matrix::zeros_with_limits(columns * n * n, columns, LIMITS)?;
        for (index, a) in self.basis.iter().enumerate() {
            let commutators: Vec<BasicMatrix<GaussianRat>> = self
                .basis
                .iter()
                .map(|b| matrix::commutator(a, b))
                .collect::<Result<Vec<_>, _>>()?;
            for entry in 0..n * n {
                for (column, c) in commutators.iter().enumerate() {
                    map.set(index * n * n + entry, column, c.as_slice()[entry].clone())?;
                }
            }
        }
        Ok(map)
    }

    fn combine_basis_with_coefficients(
        &self,
        v: &[GaussianRat],
    ) -> Result<BasicMatrix<GaussianRat>, AlgebraError> {
        let n = self.hilbert_dim;
        let mut a = matrix::zeros(n, n)?;
        for (coefficient, b) in v.iter().zip(&self.basis) {
            a = matrix::add(&a, &matrix::scale(b, coefficient)?)?;
        }
        Ok(a)
    }
    pub fn is_factor(&self) -> Result<bool, AlgebraError> {
        Ok(self.center()?.dimension() == 1)
    }
    /// Tensor-local qubit observables generated by X and Z on the selected sites.
    pub fn pauli_support(qubits: usize, sites: &[usize]) -> Result<Self, AlgebraError> {
        if qubits > 4 || sites.iter().any(|&s| s >= qubits) {
            return Err(AlgebraError::Dimension);
        }
        let dimension = 1usize << qubits;
        let mut generators = Vec::new();
        for &site in sites {
            let bit = 1usize << (qubits - site - 1);
            let mut x = matrix::zeros(dimension, dimension)?;
            let mut z = matrix::zeros(dimension, dimension)?;
            for column in 0..dimension {
                x.set(column ^ bit, column, gi(1, 0))?;
                z.set(
                    column,
                    column,
                    gi(if column & bit == 0 { 1 } else { -1 }, 0),
                )?;
            }
            generators.extend([x, z]);
        }
        Self::from_generators(dimension, &generators, 1 << 18)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/local_operator_algebra.rs
// Claim: urn:core:crates_rs:core-quantum-physics:local-operator-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::majorana_fock_algebra::FockCarrier;
    #[test]
    fn oversized_algebra_constraint_packets_refuse_before_dense_materialization() {
        let n = MAX_ALGEBRA_HILBERT_DIMENSION;
        let basis = (0..n * n)
            .map(|entry| {
                matrix::from_fn(n, n, |r, c| gi(i64::from(r * n + c == entry), 0)).unwrap()
            })
            .collect();
        let algebra = LocalOperatorAlgebra {
            hilbert_dim: n,
            basis,
        };
        for outcome in [algebra.commutant(), algebra.center()] {
            assert!(matches!(outcome,
                Err(AlgebraError::ExactAlgebra(linear_algebra::exact_field::ExactFieldError::Matrix(
                    linear_algebra::backend::basic_matrix::MatrixError::AllocationLimitExceeded { .. }
                )))
            ));
        }
        assert_eq!(
            LocalOperatorAlgebra::from_generators(2, &[], usize::MAX)
                .unwrap()
                .dimension(),
            1
        );
    }
    #[test]
    fn even_fermion_algebra_has_dimension_eight_and_two_dimensional_center() {
        let f = FockCarrier::new(2).unwrap();
        let g = f.majoranas();
        let products: Vec<_> = (0..4)
            .flat_map(|i| {
                let g = &g;
                (i + 1..4).map(move |j| matrix::multiply(&g[i], &g[j]).unwrap())
            })
            .collect();
        let algebra = LocalOperatorAlgebra::from_generators(4, &products, 4096).unwrap();
        assert_eq!(algebra.dimension(), 8);
        assert_eq!(algebra.center().unwrap().dimension(), 2);
        assert_eq!(algebra.commutant().unwrap().dimension(), 2);
        assert!(algebra.contains(&f.parity()).unwrap());
    }
    #[test]
    fn pauli_local_algebra_commutant_is_the_complement_region() {
        let local = LocalOperatorAlgebra::pauli_support(3, &[0]).unwrap();
        let complement = LocalOperatorAlgebra::pauli_support(3, &[1, 2]).unwrap();
        assert_eq!(local.dimension(), 4);
        assert_eq!(complement.dimension(), 16);
        assert!(local
            .commutant()
            .unwrap()
            .same_algebra(&complement)
            .unwrap());
        assert!(local.is_factor().unwrap());
        assert!(matches!(
            LocalOperatorAlgebra::from_generators(2, &[], 0),
            Err(AlgebraError::Budget { .. })
        ));
    }
}
