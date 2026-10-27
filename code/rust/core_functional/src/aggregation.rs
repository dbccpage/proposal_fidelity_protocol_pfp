//! Exact finite graph aggregation under an explicitly declared partition.
//!
//! This is an observed comparison, not a universal monotonicity theorem.
//! Averaging may increase edge defect. Fine values, edges and every edge defect
//! remain available; collapsed edges and surviving multiplicities are explicit.
//! These diagnostics are not primary obstruction values, scores, workload
//! verdicts or authority. Ingress byte/bit limits belong to the owning host.

use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AggregationError {
    #[error("AGGREGATION_ZERO_BLOCK_SIZE")]
    ZeroBlockSize,
    #[error("AGGREGATION_LEFTOVER_VERTICES: {vertices} by {block_size}")]
    LeftoverVertices { vertices: usize, block_size: usize },
    #[error("AGGREGATION_VALUE_COUNT: expected {expected}, got {actual}")]
    ValueCount { expected: usize, actual: usize },
    #[error("AGGREGATION_EDGE_ENDPOINT: edge {edge}, endpoint {endpoint}, vertices {vertices}")]
    EdgeEndpoint {
        edge: usize,
        endpoint: usize,
        vertices: usize,
    },
    #[error("AGGREGATION_BLOCK_LABEL: vertex {vertex}, label {label}, vertices {vertices}")]
    BlockLabel {
        vertex: usize,
        label: usize,
        vertices: usize,
    },
    #[error("AGGREGATION_MISSING_BLOCK: {block}")]
    MissingBlock { block: usize },
    #[error("AGGREGATION_ZERO_DENOMINATOR: vertex {vertex}")]
    ZeroDenominator { vertex: usize },
    #[error("AGGREGATION_GRID_SHAPE_OVERFLOW")]
    GridShapeOverflow,
    #[error("AGGREGATION_GRID_EMPTY_AXIS: {rows} by {columns}")]
    GridEmptyAxis { rows: usize, columns: usize },
    #[error("AGGREGATION_GRID_LEFTOVER: {rows} by {columns}, block {block_size}")]
    GridLeftover {
        rows: usize,
        columns: usize,
        block_size: usize,
    },
}

/// Pure comparison of these two exact scalars, not an acceptance decision.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum DefectComparison {
    Decreased,
    Unchanged,
    Increased,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum GridBoundary {
    Open,
    Periodic,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum AggregationAuthorityEffect {
    None,
}

/// Preserve the declared construction, even when resulting values coincide.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum AggregationOrigin {
    PartitionedGraph,
    ContiguousBlocks {
        block_size: usize,
    },
    Grid {
        rows: usize,
        columns: usize,
        block_size: usize,
        boundary: GridBoundary,
    },
}

/// Immutable declared fine multigraph and onto, densely labelled partition.
/// Parallel edges and orientation are retained; self loops are legitimate.
///
/// ~~~compile_fail
/// use core_functional::aggregation::AggregationMonotonicity;
/// let forged: AggregationMonotonicity = serde_json::from_str("{}").unwrap();
/// ~~~
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct AggregationMonotonicity {
    origin: AggregationOrigin,
    fine_edges: Vec<[usize; 2]>,
    partition: Vec<usize>,
    block_sizes: Vec<usize>,
}

/// A surviving edge is traceable to its original edge, including multiplicity.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CoarseEdge {
    fine_edge_index: usize,
    endpoints: [usize; 2],
}

impl CoarseEdge {
    pub fn fine_edge_index(&self) -> usize {
        self.fine_edge_index
    }
    pub fn endpoints(&self) -> [usize; 2] {
        self.endpoints
    }
}

/// Exact calculation retaining both the fine evidence and the lossy projection.
/// No public constructor, deserializer or authority-promotion API.
///
/// ~~~compile_fail
/// use core_functional::aggregation::AggregationEvidence;
/// let forged: AggregationEvidence = serde_json::from_str("{}").unwrap();
/// ~~~
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct AggregationEvidence {
    authority_effect: AggregationAuthorityEffect,
    presentation: AggregationMonotonicity,
    fine_values: Vec<BigRational>,
    fine_edge_defects: Vec<BigRational>,
    coarse_values: Vec<BigRational>,
    coarse_edges: Vec<CoarseEdge>,
    coarse_edge_defects: Vec<BigRational>,
    collapsed_edge_indices: Vec<usize>,
    fine_defect: BigRational,
    coarse_defect: BigRational,
    comparison: DefectComparison,
}

impl AggregationEvidence {
    pub fn authority_effect(&self) -> AggregationAuthorityEffect {
        self.authority_effect
    }
    pub fn presentation(&self) -> &AggregationMonotonicity {
        &self.presentation
    }
    pub fn fine_values(&self) -> &[BigRational] {
        &self.fine_values
    }
    pub fn fine_edge_defects(&self) -> &[BigRational] {
        &self.fine_edge_defects
    }
    pub fn coarse_values(&self) -> &[BigRational] {
        &self.coarse_values
    }
    pub fn coarse_edges(&self) -> &[CoarseEdge] {
        &self.coarse_edges
    }
    pub fn coarse_edge_defects(&self) -> &[BigRational] {
        &self.coarse_edge_defects
    }
    pub fn collapsed_edge_indices(&self) -> &[usize] {
        &self.collapsed_edge_indices
    }
    pub fn fine_defect(&self) -> &BigRational {
        &self.fine_defect
    }
    pub fn coarse_defect(&self) -> &BigRational {
        &self.coarse_defect
    }
    pub fn comparison(&self) -> DefectComparison {
        self.comparison
    }
}

impl AggregationMonotonicity {
    pub fn new(
        fine_edges: Vec<[usize; 2]>,
        partition: Vec<usize>,
    ) -> Result<Self, AggregationError> {
        let vertices = partition.len();
        // Bound every label by stored vertices before allocating by the label.
        for (vertex, &label) in partition.iter().enumerate() {
            if label >= vertices {
                return Err(AggregationError::BlockLabel {
                    vertex,
                    label,
                    vertices,
                });
            }
        }
        for (edge, endpoints) in fine_edges.iter().enumerate() {
            for &endpoint in endpoints {
                if endpoint >= vertices {
                    return Err(AggregationError::EdgeEndpoint {
                        edge,
                        endpoint,
                        vertices,
                    });
                }
            }
        }
        let blocks = partition.iter().max().map_or(0, |label| label + 1);
        let mut block_sizes = vec![0; blocks];
        for &label in &partition {
            block_sizes[label] += 1;
        }
        for (block, &size) in block_sizes.iter().enumerate() {
            if size == 0 {
                return Err(AggregationError::MissingBlock { block });
            }
        }
        Ok(Self {
            origin: AggregationOrigin::PartitionedGraph,
            fine_edges,
            partition,
            block_sizes,
        })
    }

    pub fn fine_edges(&self) -> &[[usize; 2]] {
        &self.fine_edges
    }

    pub fn origin(&self) -> &AggregationOrigin {
        &self.origin
    }
    pub fn partition(&self) -> &[usize] {
        &self.partition
    }

    pub fn compute(&self, values: &[BigRational]) -> Result<AggregationEvidence, AggregationError> {
        if values.len() != self.partition.len() {
            return Err(AggregationError::ValueCount {
                expected: self.partition.len(),
                actual: values.len(),
            });
        }
        for (vertex, value) in values.iter().enumerate() {
            if value.denom().is_zero() {
                return Err(AggregationError::ZeroDenominator { vertex });
            }
        }
        let fine_values: Vec<_> = values
            .iter()
            .map(|v| BigRational::new(v.numer().clone(), v.denom().clone()))
            .collect();
        let mut coarse_values = vec![BigRational::zero(); self.block_sizes.len()];
        for (value, &block) in fine_values.iter().zip(&self.partition) {
            coarse_values[block] += value;
        }
        for (value, &size) in coarse_values.iter_mut().zip(&self.block_sizes) {
            *value /= BigRational::from_integer(size.into());
        }
        let fine_edge_defects: Vec<_> = self
            .fine_edges
            .iter()
            .map(|[a, b]| (&fine_values[*b] - &fine_values[*a]).abs())
            .collect();
        let mut coarse_edges = Vec::new();
        let mut coarse_edge_defects = Vec::new();
        let mut collapsed_edge_indices = Vec::new();
        for (fine_edge_index, &[a, b]) in self.fine_edges.iter().enumerate() {
            let endpoints = [self.partition[a], self.partition[b]];
            if endpoints[0] == endpoints[1] {
                collapsed_edge_indices.push(fine_edge_index);
            } else {
                coarse_edge_defects
                    .push((&coarse_values[endpoints[1]] - &coarse_values[endpoints[0]]).abs());
                coarse_edges.push(CoarseEdge {
                    fine_edge_index,
                    endpoints,
                });
            }
        }
        let fine_defect: BigRational = fine_edge_defects.iter().cloned().sum();
        let coarse_defect: BigRational = coarse_edge_defects.iter().cloned().sum();
        let comparison = match coarse_defect.cmp(&fine_defect) {
            std::cmp::Ordering::Less => DefectComparison::Decreased,
            std::cmp::Ordering::Equal => DefectComparison::Unchanged,
            std::cmp::Ordering::Greater => DefectComparison::Increased,
        };
        Ok(AggregationEvidence {
            authority_effect: AggregationAuthorityEffect::None,
            presentation: self.clone(),
            fine_values,
            fine_edge_defects,
            coarse_values,
            coarse_edges,
            coarse_edge_defects,
            collapsed_edge_indices,
            fine_defect,
            coarse_defect,
            comparison,
        })
    }

    /// Contiguous equal-size blocks; preserve the actual supplied multigraph.
    pub fn blocks_1d(
        values: &[BigRational],
        edges: &[[usize; 2]],
        block_size: usize,
    ) -> Result<AggregationEvidence, AggregationError> {
        if block_size == 0 {
            return Err(AggregationError::ZeroBlockSize);
        }
        if !values.len().is_multiple_of(block_size) {
            return Err(AggregationError::LeftoverVertices {
                vertices: values.len(),
                block_size,
            });
        }
        let partition = (0..values.len())
            .map(|vertex| vertex / block_size)
            .collect();
        let mut presentation = Self::new(edges.to_vec(), partition)?;
        presentation.origin = AggregationOrigin::ContiguousBlocks { block_size };
        presentation.compute(values)
    }

    fn build_grid_partition_and_edges(
        rows: usize,
        columns: usize,
        block_size: usize,
        boundary: GridBoundary,
    ) -> (Vec<usize>, Vec<[usize; 2]>) {
        let coarse_columns = columns / block_size;
        let mut partition = Vec::new();
        let mut edges = Vec::new();
        for row in 0..rows {
            for column in 0..columns {
                let here = row * columns + column;
                partition.push((row / block_size) * coarse_columns + column / block_size);
                if column + 1 < columns {
                    edges.push([here, here + 1]);
                } else if boundary == GridBoundary::Periodic {
                    edges.push([here, row * columns]);
                }
                if row + 1 < rows {
                    edges.push([here, here + columns]);
                } else if boundary == GridBoundary::Periodic {
                    edges.push([here, column]);
                }
            }
        }
        (partition, edges)
    }

    /// Row-major square block averaging on a declared fine grid. The coarse
    /// graph is its quotient MULTIGRAPH, not an invented simple coarse grid.
    /// For periodic boundaries each fine cell contributes one right and one
    /// down edge, including loops when a dimension is one.
    pub fn grid_2d(
        values: &[BigRational],
        rows: usize,
        columns: usize,
        block_size: usize,
        boundary: GridBoundary,
    ) -> Result<AggregationEvidence, AggregationError> {
        if block_size == 0 {
            return Err(AggregationError::ZeroBlockSize);
        }
        // Only 0 x 0 is the admitted empty grid. Refusing a lone empty axis
        // avoids iterating unstored rows in shapes such as a million by zero.
        if (rows == 0) != (columns == 0) {
            return Err(AggregationError::GridEmptyAxis { rows, columns });
        }
        let vertices = rows
            .checked_mul(columns)
            .ok_or(AggregationError::GridShapeOverflow)?;
        if values.len() != vertices {
            return Err(AggregationError::ValueCount {
                expected: vertices,
                actual: values.len(),
            });
        }
        if !rows.is_multiple_of(block_size) || !columns.is_multiple_of(block_size) {
            return Err(AggregationError::GridLeftover {
                rows,
                columns,
                block_size,
            });
        }
        let (partition, edges) =
            Self::build_grid_partition_and_edges(rows, columns, block_size, boundary);
        let mut presentation = Self::new(edges, partition)?;
        presentation.origin = AggregationOrigin::Grid {
            rows,
            columns,
            block_size,
            boundary,
        };
        presentation.compute(values)
    }
}

// Origin: engine/crates_rs/core_functional/src/aggregation.rs
// Claim: urn:core:crates_rs:core-functional:aggregation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }

    #[test]
    fn collapsed_edges_preserve_fine_evidence_and_do_not_invent_a_chain() {
        let values = vec![q(0), q(2), q(10), q(12)];
        let result = AggregationMonotonicity::blocks_1d(&values, &[[0, 1], [2, 3]], 2).unwrap();
        assert_eq!(result.coarse_values(), &[q(1), q(11)]);
        assert_eq!(result.fine_edge_defects(), &[q(2), q(2)]);
        assert_eq!(result.fine_defect(), &q(4));
        assert_eq!(result.coarse_defect(), &q(0));
        assert!(result.coarse_edges().is_empty());
        assert_eq!(result.collapsed_edge_indices(), &[0, 1]);
        assert_eq!(result.comparison(), DefectComparison::Decreased);
        assert_eq!(result.fine_values(), values.as_slice());
    }

    #[test]
    fn arbitrary_averaging_has_a_decisive_monotonicity_counterexample() {
        // Supplied edge 0->2 has zero fine defect. The unrelated vertex 1
        // changes its block average, producing coarse defect five.
        let result =
            AggregationMonotonicity::blocks_1d(&[q(0), q(10), q(0), q(0)], &[[0, 2]], 2).unwrap();
        assert_eq!(result.fine_defect(), &q(0));
        assert_eq!(result.coarse_values(), &[q(5), q(0)]);
        assert_eq!(result.coarse_defect(), &q(5));
        assert_eq!(result.comparison(), DefectComparison::Increased);
        assert_eq!(result.coarse_edges()[0].fine_edge_index(), 0);
        assert_eq!(result.coarse_edges()[0].endpoints(), [0, 1]);
    }

    #[test]
    fn parallel_reversed_and_self_loop_edges_retain_their_actual_multiplicity() {
        let result =
            AggregationMonotonicity::blocks_1d(&[q(1), q(4)], &[[0, 1], [0, 1], [1, 0], [0, 0]], 1)
                .unwrap();
        assert_eq!(result.fine_edge_defects(), &[q(3), q(3), q(3), q(0)]);
        assert_eq!(result.coarse_edge_defects(), &[q(3), q(3), q(3)]);
        assert_eq!(result.fine_defect(), &q(9));
        assert_eq!(result.coarse_defect(), &q(9));
        assert_eq!(result.comparison(), DefectComparison::Unchanged);
        assert_eq!(result.collapsed_edge_indices(), &[3]);
        assert_eq!(
            result
                .coarse_edges()
                .iter()
                .map(CoarseEdge::fine_edge_index)
                .collect::<Vec<_>>(),
            vec![0, 1, 2]
        );
        assert_eq!(result.coarse_edges()[2].endpoints(), [1, 0]);
    }

    #[test]
    fn noncontiguous_unequal_blocks_use_the_declared_partition_and_exact_averages() {
        let presentation =
            AggregationMonotonicity::new(vec![[0, 1], [1, 2]], vec![1, 0, 1]).unwrap();
        let result = presentation.compute(&[q(1), q(7), q(2)]).unwrap();
        assert_eq!(
            result.coarse_values(),
            &[q(7), BigRational::new(3.into(), 2.into())]
        );
        assert_eq!(result.fine_defect(), &q(11));
        assert_eq!(result.coarse_defect(), &q(11));
        assert_eq!(result.comparison(), DefectComparison::Unchanged);
        assert_eq!(result.presentation(), &presentation);
        assert_eq!(presentation.partition(), &[1, 0, 1]);
        assert_eq!(presentation.fine_edges(), &[[0, 1], [1, 2]]);
    }

    #[test]
    fn invalid_labels_and_edge_endpoints_are_typed_refusals_before_indexing() {
        // The small invalid label comes first so a guard-bypass mutation fails
        // before it can reach the large sentinel's allocation-sensitive path.
        for label in [1, usize::MAX] {
            assert_eq!(
                AggregationMonotonicity::new(vec![], vec![label]),
                Err(AggregationError::BlockLabel {
                    vertex: 0,
                    label,
                    vertices: 1
                })
            );
        }
        assert_eq!(
            AggregationMonotonicity::new(vec![], vec![1, 1]),
            Err(AggregationError::MissingBlock { block: 0 })
        );
        for edge in [[0, 2], [2, 0]] {
            assert_eq!(
                AggregationMonotonicity::new(vec![edge], vec![0, 1]),
                Err(AggregationError::EdgeEndpoint {
                    edge: 0,
                    endpoint: 2,
                    vertices: 2
                })
            );
        }
        assert_eq!(
            AggregationMonotonicity::new(vec![[0, 0]], vec![]),
            Err(AggregationError::EdgeEndpoint {
                edge: 0,
                endpoint: 0,
                vertices: 0
            })
        );
    }

    #[test]
    fn missing_extra_and_invalid_rational_values_cannot_enter_even_edgeless_results() {
        let p = AggregationMonotonicity::new(vec![], vec![0]).unwrap();
        for values in [vec![], vec![q(0), q(1)]] {
            assert_eq!(
                p.compute(&values),
                Err(AggregationError::ValueCount {
                    expected: 1,
                    actual: values.len()
                })
            );
        }
        assert_eq!(
            p.compute(&[BigRational::new_raw(1.into(), 0.into())]),
            Err(AggregationError::ZeroDenominator { vertex: 0 })
        );
    }

    #[test]
    fn block_sizes_leftovers_grid_shapes_and_overflow_are_distinct_refusals() {
        assert_eq!(
            AggregationMonotonicity::blocks_1d(&[q(1)], &[], 0),
            Err(AggregationError::ZeroBlockSize)
        );
        assert_eq!(
            AggregationMonotonicity::blocks_1d(&[q(1)], &[], 2),
            Err(AggregationError::LeftoverVertices {
                vertices: 1,
                block_size: 2
            })
        );
        assert_eq!(
            AggregationMonotonicity::grid_2d(&[], 0, 0, 0, GridBoundary::Open),
            Err(AggregationError::ZeroBlockSize)
        );
        assert_eq!(
            AggregationMonotonicity::grid_2d(&[], usize::MAX, 2, 1, GridBoundary::Open),
            Err(AggregationError::GridShapeOverflow)
        );
        assert_eq!(
            AggregationMonotonicity::grid_2d(&[q(1)], 2, 2, 1, GridBoundary::Open),
            Err(AggregationError::ValueCount {
                expected: 4,
                actual: 1
            })
        );
        assert_eq!(
            AggregationMonotonicity::grid_2d(&[q(1), q(1), q(1)], 1, 3, 2, GridBoundary::Open),
            Err(AggregationError::GridLeftover {
                rows: 1,
                columns: 3,
                block_size: 2
            })
        );
    }

    #[test]
    fn grid_open_and_periodic_boundaries_are_explicit_not_inferred() {
        let values = [q(0), q(1), q(2), q(3)];
        let open = AggregationMonotonicity::grid_2d(&values, 2, 2, 1, GridBoundary::Open).unwrap();
        let periodic =
            AggregationMonotonicity::grid_2d(&values, 2, 2, 1, GridBoundary::Periodic).unwrap();
        assert_eq!(open.presentation().fine_edges().len(), 4);
        assert_eq!(periodic.presentation().fine_edges().len(), 8);
        assert_eq!(open.fine_defect(), &q(6));
        assert_eq!(periodic.fine_defect(), &q(12));
        assert_eq!(open.coarse_defect(), open.fine_defect());
        assert_eq!(periodic.coarse_defect(), periodic.fine_defect());
    }

    #[test]
    fn grid_block_projection_keeps_crossing_parallel_edges_and_collapsed_edge_ledger() {
        let values: Vec<_> = (0..8).map(q).collect();
        let result =
            AggregationMonotonicity::grid_2d(&values, 2, 4, 2, GridBoundary::Open).unwrap();
        assert_eq!(
            result.coarse_values(),
            &[
                BigRational::new(5.into(), 2.into()),
                BigRational::new(9.into(), 2.into())
            ]
        );
        assert_eq!(result.presentation().fine_edges().len(), 10);
        assert_eq!(result.coarse_edges().len(), 2);
        assert_eq!(result.collapsed_edge_indices().len(), 8);
        assert_eq!(result.fine_defect(), &q(22));
        assert_eq!(result.coarse_defect(), &q(4));
        assert_eq!(result.comparison(), DefectComparison::Decreased);
        assert!(result
            .coarse_edges()
            .iter()
            .all(|edge| edge.endpoints() == [0, 1]));
    }

    #[test]
    fn signed_unreduced_input_is_canonical_immutable_and_has_no_terminal_claim() {
        let raw = BigRational::new_raw((-2).into(), (-4).into());
        let input = vec![raw, q(-1)];
        let before = serde_json::to_vec(&input).unwrap();
        let p = AggregationMonotonicity::new(vec![[0, 1]], vec![0, 1]).unwrap();
        let snapshot = p.clone();
        let first = p.compute(&input).unwrap();
        let second = p.compute(&input).unwrap();
        assert_eq!(first, second);
        assert_eq!(p, snapshot);
        assert_eq!(serde_json::to_vec(&input).unwrap(), before);
        assert_eq!(first.fine_values()[0].numer(), &1.into());
        assert_eq!(first.fine_values()[0].denom(), &2.into());
        assert_eq!(first.fine_defect(), &BigRational::new(3.into(), 2.into()));
        let wire = serde_json::to_value(&first).unwrap();
        assert_eq!(first.authority_effect(), AggregationAuthorityEffect::None);
        assert_eq!(wire["authority_effect"], "None");
        for absent in [
            "accepted",
            "monotone_theorem",
            "license",
            "terminal_status",
            "FactOnly",
        ] {
            assert!(wire.get(absent).is_none(), "{absent}");
        }
    }

    #[test]
    fn empty_graph_and_singleton_periodic_loops_are_explicit_degenerate_data() {
        let empty = AggregationMonotonicity::blocks_1d(&[], &[], 1).unwrap();
        assert!(empty.fine_values().is_empty() && empty.coarse_edges().is_empty());
        assert_eq!(empty.fine_defect(), &q(0));
        assert_eq!(empty.comparison(), DefectComparison::Unchanged);
        let singleton =
            AggregationMonotonicity::grid_2d(&[q(9)], 1, 1, 1, GridBoundary::Periodic).unwrap();
        assert_eq!(singleton.presentation().fine_edges(), &[[0, 0], [0, 0]]);
        assert_eq!(singleton.collapsed_edge_indices(), &[0, 1]);
        assert_eq!(singleton.fine_defect(), &q(0));
        assert_eq!(singleton.coarse_values(), &[q(9)]);
    }

    #[test]
    fn empty_axis_refusal_and_grid_origin_do_not_disappear_in_zero_evidence() {
        for (rows, columns) in [(1_000_000, 0), (0, 1_000_000)] {
            assert_eq!(
                AggregationMonotonicity::grid_2d(&[], rows, columns, 1, GridBoundary::Open),
                Err(AggregationError::GridEmptyAxis { rows, columns })
            );
        }
        let zero = AggregationMonotonicity::grid_2d(&[], 0, 0, 1, GridBoundary::Open).unwrap();
        assert_eq!(
            zero.presentation().origin(),
            &AggregationOrigin::Grid {
                rows: 0,
                columns: 0,
                block_size: 1,
                boundary: GridBoundary::Open
            }
        );
        let line = AggregationMonotonicity::blocks_1d(&[], &[], 1).unwrap();
        assert_eq!(
            line.presentation().origin(),
            &AggregationOrigin::ContiguousBlocks { block_size: 1 }
        );
        assert_eq!(line.coarse_defect(), zero.coarse_defect());
        assert_ne!(line.presentation(), zero.presentation());
        assert_eq!(
            AggregationMonotonicity::new(vec![], vec![])
                .unwrap()
                .origin(),
            &AggregationOrigin::PartitionedGraph
        );
    }
}
