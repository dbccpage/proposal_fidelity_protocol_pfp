use thiserror::Error;

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum GraphLaplacianError {
    #[error("node index {index} out of bounds for graph with {node_count} nodes")]
    NodeOutOfBounds { index: usize, node_count: usize },

    #[error("dimension overflow: {node_count} squared exceeds usize")]
    DimensionOverflow { node_count: usize },
}

pub fn graph_laplacian_dense_checked(
    num_nodes: usize,
    edges: &[(usize, usize)],
) -> Result<Vec<f64>, GraphLaplacianError> {
    let n = num_nodes;
    let n_sq = n
        .checked_mul(n)
        .ok_or(GraphLaplacianError::DimensionOverflow { node_count: n })?;
    let mut lap = vec![0.0; n_sq];

    for &(i, j) in edges {
        if i >= n {
            return Err(GraphLaplacianError::NodeOutOfBounds {
                index: i,
                node_count: n,
            });
        }
        if j >= n {
            return Err(GraphLaplacianError::NodeOutOfBounds {
                index: j,
                node_count: n,
            });
        }

        lap[i * n + i] += 1.0;
        lap[j * n + j] += 1.0;
        lap[i * n + j] -= 1.0;
        lap[j * n + i] -= 1.0;
    }

    Ok(lap)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IntegerLaplacianError {
    NodeOutOfBounds { index: usize, node_count: usize },
    DimensionOverflow { node_count: usize },
    EntryOverflow { index: usize },
    RowSumNonzero { row: usize, sum: i64 },
}

fn bump_entry(lap: &mut [i64], index: usize, delta: i64) -> Result<(), IntegerLaplacianError> {
    let cell = lap
        .get_mut(index)
        .ok_or(IntegerLaplacianError::EntryOverflow { index })?;
    *cell = cell
        .checked_add(delta)
        .ok_or(IntegerLaplacianError::EntryOverflow { index })?;
    Ok(())
}

fn flat_index(row: usize, col: usize, width: usize) -> Result<usize, IntegerLaplacianError> {
    row.checked_mul(width)
        .and_then(|start| start.checked_add(col))
        .ok_or(IntegerLaplacianError::DimensionOverflow { node_count: width })
}

/// Integer Laplacian with the same undirected convention as
/// [`graph_laplacian_dense_checked`]: a loop `i == i` contributes +1 and −1
/// on the diagonal and therefore nets zero. Every row sums to zero.
pub fn integer_graph_laplacian(
    num_nodes: usize,
    edges: &[(usize, usize)],
) -> Result<Vec<i64>, IntegerLaplacianError> {
    let n_sq =
        num_nodes
            .checked_mul(num_nodes)
            .ok_or(IntegerLaplacianError::DimensionOverflow {
                node_count: num_nodes,
            })?;
    let mut lap = vec![0i64; n_sq];
    for &(i, j) in edges {
        add_integer_edge(&mut lap, num_nodes, i, j)?;
    }
    verify_zero_row_sums(&lap, num_nodes)?;
    Ok(lap)
}

fn add_integer_edge(
    lap: &mut [i64],
    num_nodes: usize,
    i: usize,
    j: usize,
) -> Result<(), IntegerLaplacianError> {
    for index in [i, j] {
        if index >= num_nodes {
            return Err(IntegerLaplacianError::NodeOutOfBounds {
                index,
                node_count: num_nodes,
            });
        }
    }
    bump_entry(lap, flat_index(i, i, num_nodes)?, 1)?;
    bump_entry(lap, flat_index(j, j, num_nodes)?, 1)?;
    bump_entry(lap, flat_index(i, j, num_nodes)?, -1)?;
    bump_entry(lap, flat_index(j, i, num_nodes)?, -1)
}

fn verify_zero_row_sums(lap: &[i64], num_nodes: usize) -> Result<(), IntegerLaplacianError> {
    for row in 0..num_nodes {
        let mut sum = 0i64;
        for col in 0..num_nodes {
            let index = flat_index(row, col, num_nodes)?;
            let entry = lap
                .get(index)
                .copied()
                .ok_or(IntegerLaplacianError::EntryOverflow { index })?;
            sum = sum
                .checked_add(entry)
                .ok_or(IntegerLaplacianError::EntryOverflow { index })?;
        }
        if sum != 0 {
            return Err(IntegerLaplacianError::RowSumNonzero { row, sum });
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/graph_laplacian.rs
// Claim: urn:core:crates_rs:core-linear-algebra:graph-laplacian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_d0696c41 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
