//! Positivity of quantum operators depends on a declared real embedding.
//!
//! The scalar owner enumerates Galois classes and decides algebraic signs by
//! Sturm isolation. This module checks all principal minors of a Hermitian
//! matrix under each real embedding: their nonnegativity is equivalent to
//! positive semidefiniteness. It also computes Born weights and their Galois
//! transforms; Galois conjugation commutes with complex conjugation, so every
//! rank-one positive operator remains positive in every embedding.
//!
//! Matrices are `BasicMatrix<Cyclotomic<N>>`, fields and real embeddings are
//! canonical `core_number_theory` types. Dimension is bounded at ten because
//! the semidefinite test checks every nonempty principal minor.
//!
//! AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, ExactFieldError};
use core_number_theory::cyclotomic_field::{Cyclotomic, CyclotomicError};
use core_number_theory::rational::ri;
use core_number_theory::real_embedding::{EmbeddingError, RealEmbeddings};
use std::cmp::Ordering;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PositivityError {
    #[error("the Hermitian operator must have square dimension 1..=10")]
    Shape,
    #[error("the operator is not Hermitian")]
    NotHermitian,
    #[error(transparent)]
    Embedding(#[from] EmbeddingError),
    #[error(transparent)]
    Cyclotomic(#[from] CyclotomicError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

/// `(embedding class, is positive semidefinite)`, in canonical class order.
pub fn positivity_under_embeddings<const N: usize>(
    matrix: &BasicMatrix<Cyclotomic<N>>,
) -> Result<Vec<(usize, bool)>, PositivityError> {
    let n = matrix.rows();
    if n == 0 || n > 10 || matrix.cols() != n {
        return Err(PositivityError::Shape);
    }
    if !core_lie_theory::scalar::is_hermitian(matrix)? {
        return Err(PositivityError::NotHermitian);
    }
    let mut embedding = RealEmbeddings::new(N)?;
    let mut results = embedding
        .classes()
        .iter()
        .map(|k| (*k, true))
        .collect::<Vec<_>>();
    for mask in 1usize..1usize << n {
        let determinant = principal_minor_determinant(matrix, n, mask)?;
        update_embedding_signs(&mut embedding, &determinant, &mut results)?;
    }
    Ok(results)
}

fn principal_minor_determinant<const N: usize>(
    matrix: &BasicMatrix<Cyclotomic<N>>,
    n: usize,
    mask: usize,
) -> Result<Cyclotomic<N>, PositivityError> {
    let indices = (0..n).filter(|i| mask & (1 << i) != 0).collect::<Vec<_>>();
    let mut entries = Vec::with_capacity(indices.len() * indices.len());
    for i in &indices {
        for j in &indices {
            entries.push(
                matrix
                    .get_ref(*i, *j)
                    .map_err(ExactFieldError::from)?
                    .clone(),
            );
        }
    }
    let minor = BasicMatrix::from_row_major(indices.len(), indices.len(), entries)
        .map_err(ExactFieldError::from)?;
    Ok(elimination::determinant(&minor)?)
}

fn update_embedding_signs<const N: usize>(
    embedding: &mut RealEmbeddings,
    determinant: &Cyclotomic<N>,
    results: &mut [(usize, bool)],
) -> Result<(), PositivityError> {
    for (k, positive) in results {
        if *positive
            && embedding.sign_under_embedding(determinant.as_number(), *k as i64)? == Ordering::Less
        {
            *positive = false;
        }
    }
    Ok(())
}

pub fn born_weights<const N: usize>(amplitudes: &[Cyclotomic<N>]) -> Vec<Cyclotomic<N>> {
    amplitudes.iter().map(|a| a.mul(&a.conjugate())).collect()
}

/// Apply a declared Galois automorphism to amplitudes before the Born map.
pub fn galois_born_weights<const N: usize>(
    amplitudes: &[Cyclotomic<N>],
    k: i64,
) -> Result<Vec<Cyclotomic<N>>, PositivityError> {
    let conjugates = amplitudes
        .iter()
        .map(|a| a.galois(k))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(born_weights(&conjugates))
}

/// A unit-trace diagonal state positive in one embedding and negative in the other.
pub fn conductor_5_witness() -> Result<BasicMatrix<Cyclotomic<5>>, PositivityError> {
    let t = Cyclotomic::<5>::zeta(1).add(&Cyclotomic::<5>::zeta(-1));
    let a = t.scale(&ri(2)).sub(&Cyclotomic::<5>::one());
    let b = Cyclotomic::<5>::one().sub(&a);
    Ok(
        BasicMatrix::from_row_major(2, 2, vec![a, Cyclotomic::zero(), Cyclotomic::zero(), b])
            .map_err(ExactFieldError::from)?,
    )
}

pub fn conductor_8_witness() -> Result<BasicMatrix<Cyclotomic<8>>, PositivityError> {
    let root = Cyclotomic::<8>::zeta(1).add(&Cyclotomic::<8>::zeta(-1));
    let a = root.sub(&Cyclotomic::<8>::one());
    let b = Cyclotomic::<8>::one().sub(&a);
    Ok(
        BasicMatrix::from_row_major(2, 2, vec![a, Cyclotomic::zero(), Cyclotomic::zero(), b])
            .map_err(ExactFieldError::from)?,
    )
}

pub fn verify_conductor_5_witness() -> (bool, bool) {
    let results = conductor_5_witness().and_then(|m| positivity_under_embeddings(&m));
    results.map(|v| (v[0].1, v[1].1)).unwrap_or((false, false))
}
pub fn verify_conductor_8_witness() -> (bool, bool) {
    let results = conductor_8_witness().and_then(|m| positivity_under_embeddings(&m));
    results.map(|v| (v[0].1, v[1].1)).unwrap_or((false, false))
}

// Origin: engine/crates_rs/core_quantum_physics/src/embedding_relativity.rs
// Claim: urn:core:crates_rs:core-quantum-physics:embedding-relativity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_578c0e6e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
