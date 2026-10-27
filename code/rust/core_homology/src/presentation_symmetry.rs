//! Exact automorphisms of finite graph and cochain presentations.
//! Model obstructions carry no Genesis scale-forcing authority.

use std::collections::BTreeSet;

use crate::cochain_complex::{CochainComplex, TheoremProvenance};
use crate::finite_directed_graph::FiniteDirectedGraph;
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::{One, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SymmetryError {
    #[error("empty presentations do not supply symmetry evidence")]
    Empty,
    #[error("map must be a bijection of the exact declared carrier with signs +/-1")]
    Bijection,
    #[error("graph adjacency is not preserved")]
    Adjacency,
    #[error("cochain law or shape is invalid: {0}")]
    Complex(String),
    #[error("coboundary or difference operator does not intertwine the proposed symmetry")]
    Intertwining,
}

/// Column i maps to signs[i] times basis element image[i].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignedPermutation {
    pub image: Vec<usize>,
    pub signs: Vec<i8>,
}

impl SignedPermutation {
    pub fn validate(&self, dimension: usize) -> Result<(), SymmetryError> {
        if self.image.len() != dimension
            || self.signs.len() != dimension
            || self.image.iter().copied().collect::<BTreeSet<_>>() != (0..dimension).collect()
            || self.signs.iter().any(|s| *s != 1 && *s != -1)
        {
            return Err(SymmetryError::Bijection);
        }
        Ok(())
    }
}

fn intertwines(
    matrix: &BasicMatrix<Q>,
    source: &SignedPermutation,
    target: &SignedPermutation,
) -> Result<(), SymmetryError> {
    source.validate(matrix.cols())?;
    target.validate(matrix.rows())?;
    for row in 0..matrix.rows() {
        for col in 0..matrix.cols() {
            let sign =
                Q::from_integer((source.signs[col] as i64 * target.signs[row] as i64).into());
            let entry = matrix
                .get_ref(row, col)
                .map_err(|e| SymmetryError::Complex(e.to_string()))?;
            let moved = matrix
                .get_ref(target.image[row], source.image[col])
                .map_err(|e| SymmetryError::Complex(e.to_string()))?;
            if moved != &(&sign * entry) {
                return Err(SymmetryError::Intertwining);
            }
        }
    }
    Ok(())
}

/// Revalidate the public complex data, then verify P_(i+1) d_i = d_i P_i.
/// Consequently cocycles and coboundaries are preserved, inducing an H^i automorphism.
pub fn verify_cochain_symmetry(
    complex: &CochainComplex,
    maps: &[SignedPermutation; 3],
) -> Result<(), SymmetryError> {
    if complex.c0_dim == 0 {
        return Err(SymmetryError::Empty);
    }
    let provenance = TheoremProvenance::new("exact symmetry checker: d1*d0 recomputed".into())
        .map_err(|e| SymmetryError::Complex(e.to_string()))?;
    CochainComplex::new(
        complex.c0_dim,
        complex.c1_dim,
        complex.c2_dim,
        complex.d0.matrix.clone(),
        complex.d1.matrix.clone(),
        provenance,
    )
    .map_err(|e| SymmetryError::Complex(e.to_string()))?;
    intertwines(&complex.d0.matrix, &maps[0], &maps[1])?;
    intertwines(&complex.d1.matrix, &maps[1], &maps[2])
}

/// A square difference operator is observable-equivariant exactly when DP = PD.
pub fn verify_difference_symmetry(
    operator: &BasicMatrix<Q>,
    map: &SignedPermutation,
) -> Result<(), SymmetryError> {
    if operator.rows() == 0 {
        return Err(SymmetryError::Empty);
    }
    if operator.rows() != operator.cols() {
        return Err(SymmetryError::Intertwining);
    }
    intertwines(operator, map, map)
}

/// Graph automorphisms induce an incidence-cochain symmetry and preserve D^T D.
pub fn verify_graph_symmetry(
    graph: &FiniteDirectedGraph,
    image: &[usize],
) -> Result<Vec<usize>, SymmetryError> {
    let n = graph.num_nodes();
    if n == 0 {
        return Err(SymmetryError::Empty);
    }
    let vertices = SignedPermutation {
        image: image.to_vec(),
        signs: vec![1; n],
    };
    vertices.validate(n)?;
    let edges = graph.edges();
    let mut edge_image = Vec::new();
    for &(a, b) in edges {
        edge_image.push(
            edges
                .iter()
                .position(|e| *e == (image[a], image[b]))
                .ok_or(SymmetryError::Adjacency)?,
        );
    }
    let incidence = BasicMatrix::try_from_fn(edges.len(), n, |row, col| {
        if edges[row].0 == col {
            -Q::one()
        } else if edges[row].1 == col {
            Q::one()
        } else {
            Q::zero()
        }
    })
    .map_err(|e| SymmetryError::Complex(e.to_string()))?;
    let edge_map = SignedPermutation {
        image: edge_image.clone(),
        signs: vec![1; edges.len()],
    };
    intertwines(&incidence, &vertices, &edge_map)?;
    Ok(edge_image)
}

// Origin: engine/crates_rs/core_homology/src/presentation_symmetry.rs
// Claim: urn:core:crates_rs:core-homology:presentation-symmetry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn directed_cycle_rotation_and_duplicate_near_miss() {
        let graph = crate::finite_directed_graph::DirectedGraphBuilder::from_anonymous(
            3,
            vec![(0, 1), (1, 2), (2, 0)],
            crate::finite_directed_graph::TheoremProvenance {
                verification_source: "three-cycle presentation".into(),
            },
        )
        .unwrap();
        assert_eq!(
            verify_graph_symmetry(&graph, &[1, 2, 0]).unwrap(),
            vec![1, 2, 0]
        );
        assert_eq!(
            verify_graph_symmetry(&graph, &[0, 0, 2]),
            Err(SymmetryError::Bijection)
        );
        assert_eq!(
            verify_graph_symmetry(&graph, &[1, 0, 2]),
            Err(SymmetryError::Adjacency)
        );
    }

    #[test]
    fn signed_cochain_maps_preserve_laws_but_arbitrary_maps_do_not() {
        let d0 = BasicMatrix::from_row_major(1, 2, vec![-Q::one(), Q::one()]).unwrap();
        let complex = CochainComplex::new(
            2,
            1,
            0,
            d0,
            BasicMatrix::zero(0, 1).unwrap(),
            TheoremProvenance::new("incidence of one edge".into()).unwrap(),
        )
        .unwrap();
        let maps = [
            SignedPermutation {
                image: vec![1, 0],
                signs: vec![1, 1],
            },
            SignedPermutation {
                image: vec![0],
                signs: vec![-1],
            },
            SignedPermutation {
                image: vec![],
                signs: vec![],
            },
        ];
        verify_cochain_symmetry(&complex, &maps).unwrap();
        let mut bad = maps.clone();
        bad[1].signs[0] = 1;
        assert_eq!(
            verify_cochain_symmetry(&complex, &bad),
            Err(SymmetryError::Intertwining)
        );
        let laplacian =
            BasicMatrix::from_row_major(2, 2, vec![Q::one(), -Q::one(), -Q::one(), Q::one()])
                .unwrap();
        verify_difference_symmetry(&laplacian, &maps[0]).unwrap();
        let diagonal = BasicMatrix::from_row_major(
            2,
            2,
            vec![Q::one(), Q::zero(), Q::zero(), Q::from_integer(2.into())],
        )
        .unwrap();
        assert_eq!(
            verify_difference_symmetry(&diagonal, &maps[0]),
            Err(SymmetryError::Intertwining)
        );
    }
}
