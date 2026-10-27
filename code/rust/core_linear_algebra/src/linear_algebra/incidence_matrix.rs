use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use nalgebra::DMatrix;
use thiserror::Error;

/// Errors for oriented incidence matrix construction.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum IncidenceMatrixError {
    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),

    #[error("edge index out of bounds at edge {edge_index}: ({source_node}, {target_node}), num_nodes={num_nodes}")]
    EdgeIndexOutOfBounds {
        edge_index: usize,
        source_node: usize,
        target_node: usize,
        num_nodes: usize,
    },

    #[error("self-loop at edge {edge_index}: node={node}")]
    SelfLoop { edge_index: usize, node: usize },
}

/// Constructs the oriented edge-node incidence matrix.
///
/// Convention:
/// - rows are edges;
/// - columns are nodes;
/// - for edge `(source, target)`, entry `(edge, source) = -1`;
/// - entry `(edge, target) = +1`.
///
/// This treats the edge orientation as supplied by `edges`.
pub fn incidence_matrix(
    num_nodes: usize,
    edges: &[(usize, usize)],
) -> Result<BasicMatrix<i64>, IncidenceMatrixError> {
    let mut matrix =
        BasicMatrix::zero(edges.len(), num_nodes).map_err(IncidenceMatrixError::Matrix)?;

    for (row, &(source, target)) in edges.iter().enumerate() {
        if source >= num_nodes || target >= num_nodes {
            return Err(IncidenceMatrixError::EdgeIndexOutOfBounds {
                edge_index: row,
                source_node: source,
                target_node: target,
                num_nodes,
            });
        }

        if source == target {
            return Err(IncidenceMatrixError::SelfLoop {
                edge_index: row,
                node: source,
            });
        }

        matrix
            .set(row, source, -1)
            .map_err(IncidenceMatrixError::Matrix)?;
        matrix
            .set(row, target, 1)
            .map_err(IncidenceMatrixError::Matrix)?;
    }

    Ok(matrix)
}

/// Constructs the oriented incidence matrix as a `nalgebra::DMatrix`.
pub fn incidence_matrix_dmatrix(
    num_nodes: usize,
    edges: &[(usize, usize)],
) -> Result<DMatrix<i64>, IncidenceMatrixError> {
    let bm = incidence_matrix(num_nodes, edges)?;

    let mut data = Vec::with_capacity(bm.rows() * bm.cols());
    for c in 0..bm.cols() {
        for r in 0..bm.rows() {
            // DMatrix::from_column_slice expects column-major order, so we iterate cols then rows
            data.push(bm.get(r, c).map_err(IncidenceMatrixError::Matrix)?);
        }
    }

    Ok(DMatrix::from_column_slice(bm.rows(), bm.cols(), &data))
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/incidence_matrix.rs
// Claim: urn:core:crates_rs:core-linear-algebra:incidence-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_graph_returns_0_by_n_matrix() {
        let bm = incidence_matrix(3, &[]).unwrap();
        assert_eq!(bm.rows(), 0);
        assert_eq!(bm.cols(), 3);
    }

    #[test]
    fn single_edge_has_minus_one_plus_one() {
        let bm = incidence_matrix(2, &[(0, 1)]).unwrap();
        assert_eq!(bm.rows(), 1);
        assert_eq!(bm.cols(), 2);
        assert_eq!(bm.get(0, 0).unwrap(), -1);
        assert_eq!(bm.get(0, 1).unwrap(), 1);
    }

    #[test]
    fn invalid_source_rejected() {
        let err = incidence_matrix(2, &[(2, 0)]).unwrap_err();
        assert!(matches!(
            err,
            IncidenceMatrixError::EdgeIndexOutOfBounds { .. }
        ));
    }

    #[test]
    fn invalid_target_rejected() {
        let err = incidence_matrix(2, &[(0, 3)]).unwrap_err();
        assert!(matches!(
            err,
            IncidenceMatrixError::EdgeIndexOutOfBounds { .. }
        ));
    }

    #[test]
    fn self_loop_rejected_if_forbidden() {
        let err = incidence_matrix(2, &[(1, 1)]).unwrap_err();
        assert!(matches!(err, IncidenceMatrixError::SelfLoop { .. }));
    }

    #[test]
    fn dmatrix_matches_basic_matrix() {
        let num_nodes = 3;
        let edges = vec![(0, 1), (1, 2)];
        let bm = incidence_matrix(num_nodes, &edges).unwrap();
        let dm = incidence_matrix_dmatrix(num_nodes, &edges).unwrap();

        for r in 0..bm.rows() {
            for c in 0..bm.cols() {
                assert_eq!(bm.get(r, c).unwrap(), dm[(r, c)]);
            }
        }
    }
}
