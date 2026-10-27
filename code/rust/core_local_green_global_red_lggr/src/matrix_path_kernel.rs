// Executable finite evidence; AuthorityEffect: None.
//! Exact two-dimensional matrix path kernels and declared overlap/trace checks.
//!
//! Grounded in FOC-012 ("Local Green, Global Red Foundational Series"):
//! - LGGR I (Evaluated Path Kernels): Path composition K(P) = T_{e_m} ... T_{e_1}. Canonical 3-cycle: Local Green !=> Global Green.
//! - LGGR II (Organizational Gluing): Covering sieves U = {U_i} and Cech gluing defect Delta_{glue}(s) = ||delta^0 s||_1.
//! - LGGR III (CODA_GTLA Traces): Game-Theoretic Trace Verification contracting evaluation residuals under finite budgets.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3ae276a2<T> {
    fn checked_invariant_3ae276a2(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3ae276a2<T> for Option<T> {
    #[inline]
    fn checked_invariant_3ae276a2(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3ae276a2<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3ae276a2(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Serialize};

use core_holonomy::matrix::ExactMatrix;
use core_homology::finite_directed_graph::{DirectedGraphBuilder, TheoremProvenance};

/// Typed malformed-presentation and native-owner refusals.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MatrixPathError {
    #[error("Invalid input: {detail}")]
    InvalidInput { detail: String },
    #[error("Graph carrier refusal: {0}")]
    GraphCarrier(#[from] core_homology::finite_directed_graph::NamedEdgeResolutionError),
    #[error("Holonomy refusal: {0}")]
    Holonomy(#[from] core_holonomy::HolonomyError),
}

/// Evaluation status for local edges and global cycles.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvaluationColor {
    Green,
    Red,
}

/// 2x2 BigRational Matrix for transition and path evaluation kernels.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RationalMatrix2x2 {
    pub m00: BigRational,
    pub m01: BigRational,
    pub m10: BigRational,
    pub m11: BigRational,
}

impl RationalMatrix2x2 {
    pub fn identity() -> Self {
        Self {
            m00: BigRational::one(),
            m01: BigRational::zero(),
            m10: BigRational::zero(),
            m11: BigRational::one(),
        }
    }

    pub fn new(m00: BigRational, m01: BigRational, m10: BigRational, m11: BigRational) -> Self {
        Self { m00, m01, m10, m11 }
    }

    fn to_native(&self) -> Result<ExactMatrix<BigRational>, MatrixPathError> {
        let values = [&self.m00, &self.m01, &self.m10, &self.m11];
        if values.iter().any(|q| q.denom().is_zero()) {
            return Err(MatrixPathError::InvalidInput {
                detail: "matrix entry has zero rational denominator".into(),
            });
        }
        Ok(ExactMatrix::try_new(
            2,
            2,
            values.iter().map(|q| q.reduced()).collect(),
        )?)
    }

    fn from_native(matrix: &ExactMatrix<BigRational>) -> Self {
        Self {
            m00: matrix.get(0, 0).clone(),
            m01: matrix.get(0, 1).clone(),
            m10: matrix.get(1, 0).clone(),
            m11: matrix.get(1, 1).clone(),
        }
    }

    /// Product arithmetic is owned by the exact holonomy matrix backend.
    pub fn multiply(&self, other: &Self) -> Result<Self, MatrixPathError> {
        Ok(Self::from_native(
            &self.to_native()?.matmul(&other.to_native()?)?,
        ))
    }

    pub fn determinant(&self) -> Result<BigRational, MatrixPathError> {
        Ok(self.to_native()?.determinant()?)
    }

    /// L1 matrix norm: max absolute column sum.
    pub fn l1_norm(&self) -> Result<BigRational, MatrixPathError> {
        let native = self.to_native()?;
        let rows = (0..2)
            .map(|i| (0..2).map(|j| native.get(i, j).clone()).collect())
            .collect::<Vec<_>>();
        core_functional::residual_splitting::weighted_l1_operator_norm(
            &rows,
            &[BigRational::one(), BigRational::one()],
        )
        .map_err(|error| MatrixPathError::InvalidInput {
            detail: error.to_string(),
        })
    }

    /// Deviation from identity: ||M - I||_1.
    pub fn deviation_from_identity(&self) -> Result<BigRational, MatrixPathError> {
        let native = self.to_native()?;
        let diff = Self {
            m00: native.get(0, 0) - BigRational::one(),
            m01: native.get(0, 1).clone(),
            m10: native.get(1, 0).clone(),
            m11: native.get(1, 1) - BigRational::one(),
        };
        diff.l1_norm()
    }
}

/// Evaluated Path Kernel system over a directed graph.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvaluatedPathKernelGraph {
    pub vertices: Vec<String>,
    pub edges: Vec<(String, String)>,
    pub transition_matrices: Vec<RationalMatrix2x2>,
}

impl EvaluatedPathKernelGraph {
    pub fn new(
        vertices: Vec<String>,
        edges: Vec<(String, String)>,
        transitions: Vec<RationalMatrix2x2>,
    ) -> Result<Self, MatrixPathError> {
        let graph = Self {
            vertices,
            edges,
            transition_matrices: transitions,
        };
        graph.validate()?;
        Ok(graph)
    }

    fn validate(&self) -> Result<(), MatrixPathError> {
        if self.edges.len() != self.transition_matrices.len() {
            return Err(MatrixPathError::InvalidInput {
                detail: "each declared edge needs exactly one transition matrix".into(),
            });
        }
        DirectedGraphBuilder::from_named(
            self.vertices.clone(),
            &self.edges,
            TheoremProvenance {
                verification_source: "core_epk::matrix_path_kernel".into(),
            },
        )?;
        for matrix in &self.transition_matrices {
            matrix.to_native()?;
        }
        Ok(())
    }

    fn check_threshold(value: BigRational, name: &str) -> Result<BigRational, MatrixPathError> {
        if value.denom().is_zero() {
            return Err(MatrixPathError::InvalidInput {
                detail: format!("{name} has zero denominator"),
            });
        }
        let value = value.reduced();
        if value.is_negative() {
            return Err(MatrixPathError::InvalidInput {
                detail: format!("{name} must be nonnegative"),
            });
        }
        Ok(value)
    }

    /// Checked declared edge walk, in full, with no malformed steps omitted.
    /// Products T_last...T_first delegate to the native exact matrix owner.
    pub fn evaluate_path(
        &self,
        edge_indices: &[usize],
    ) -> Result<RationalMatrix2x2, MatrixPathError> {
        self.validate()?;
        if edge_indices.iter().any(|&i| i >= self.edges.len()) {
            return Err(MatrixPathError::InvalidInput {
                detail: "path edge index outside declared graph".into(),
            });
        }
        for pair in edge_indices.windows(2) {
            if self.edges[pair[0]].1 != self.edges[pair[1]].0 {
                return Err(MatrixPathError::InvalidInput {
                    detail: "path edges are not composable".into(),
                });
            }
        }
        let mut kernel = RationalMatrix2x2::identity();
        for &i in edge_indices {
            kernel = self.transition_matrices[i].multiply(&kernel)?;
        }
        Ok(kernel)
    }

    pub fn check_local_green(
        &self,
        edge_threshold: BigRational,
    ) -> Result<(bool, Vec<EvaluationColor>), MatrixPathError> {
        self.validate()?;
        let threshold = Self::check_threshold(edge_threshold, "edge threshold")?;
        let mut colors = Vec::with_capacity(self.edges.len());
        for transition in &self.transition_matrices {
            colors.push(
                if transition.determinant()? > BigRational::zero()
                    && transition.deviation_from_identity()? <= threshold
                {
                    EvaluationColor::Green
                } else {
                    EvaluationColor::Red
                },
            );
        }
        Ok((colors.iter().all(|c| *c == EvaluationColor::Green), colors))
    }

    pub fn check_global_cycle(
        &self,
        cycle_edges: &[usize],
        cycle_threshold: BigRational,
    ) -> Result<(bool, RationalMatrix2x2), MatrixPathError> {
        let threshold = Self::check_threshold(cycle_threshold, "cycle threshold")?;
        let product = self.evaluate_path(cycle_edges)?;
        let (Some(&first), Some(&last)) = (cycle_edges.first(), cycle_edges.last()) else {
            return Err(MatrixPathError::InvalidInput {
                detail: "a cycle needs a declared nonempty closed edge walk".into(),
            });
        };
        if self.edges[first].0 != self.edges[last].1 {
            return Err(MatrixPathError::InvalidInput {
                detail: "declared cycle edge walk is open".into(),
            });
        }
        Ok((product.deviation_from_identity()? <= threshold, product))
    }

    /// Sum matrix differences on the caller's declared comparisons. Zero means
    /// agreement on precisely those pairs; no coverage, transport, Cech H1 or
    /// global gluing property follows from an arbitrary comparison list.
    pub fn compute_cech_gluing_defect(
        &self,
        patch_evaluations: &[RationalMatrix2x2],
        overlaps: &[(usize, usize)],
    ) -> Result<(BigRational, bool), MatrixPathError> {
        self.validate()?;
        let canonical_patches: Vec<_> = patch_evaluations
            .iter()
            .map(|patch| {
                patch
                    .to_native()
                    .map(|native| RationalMatrix2x2::from_native(&native))
            })
            .collect::<Result<_, _>>()?;
        if overlaps
            .iter()
            .any(|&(i, j)| i >= patch_evaluations.len() || j >= patch_evaluations.len())
        {
            return Err(MatrixPathError::InvalidInput {
                detail: "overlap comparison index outside declared patches".into(),
            });
        }
        let mut total = BigRational::zero();
        for &(i, j) in overlaps {
            let left = &canonical_patches[i];
            let right = &canonical_patches[j];
            let difference = RationalMatrix2x2::new(
                &left.m00 - &right.m00,
                &left.m01 - &right.m01,
                &left.m10 - &right.m10,
                &left.m11 - &right.m11,
            );
            total += difference.l1_norm()?;
        }
        let vanishes = total.is_zero();
        Ok((total, vanishes))
    }

    /// Check the declared exact nonnegative residual sequence: every positive
    /// residual strictly decreases; zero is absorbing. This is a conditional
    /// sequence check, not recomputation of residuals from an actual graph run.
    pub fn verify_coda_gtla_trace(&self, residual_sequence: &[BigRational]) -> bool {
        if residual_sequence.is_empty() || residual_sequence.iter().any(|q| q.denom().is_zero()) {
            return false;
        }
        let values: Vec<_> = residual_sequence.iter().map(|q| q.reduced()).collect();
        if values.iter().any(|q| q.is_negative()) {
            return false;
        }
        values.windows(2).all(|pair| {
            if pair[0].is_zero() {
                pair[1].is_zero()
            } else {
                pair[1] < pair[0]
            }
        })
    }
}

/// Generates the canonical 3-cycle LGGR counterexample: Local Green !=> Global Green.
pub fn generate_canonical_lggr_counterexample() -> (EvaluatedPathKernelGraph, Vec<usize>) {
    let vertices = vec!["v0".to_string(), "v1".to_string(), "v2".to_string()];
    let edges = vec![
        ("v0".to_string(), "v1".to_string()),
        ("v1".to_string(), "v2".to_string()),
        ("v2".to_string(), "v0".to_string()),
    ];

    // Three upper-triangular shears each with ||T - I|| = 1/2 (Local Green <= 1/2)
    // T1 = [[1, 1/2], [0, 1]]
    // T2 = [[1, 0], [1/2, 1]]
    // T3 = [[1, 1/2], [0, 1]]
    let half = || BigRational::new(BigInt::from(1), BigInt::from(2));
    let t1 = RationalMatrix2x2::new(
        BigRational::one(),
        half(),
        BigRational::zero(),
        BigRational::one(),
    );
    let t2 = RationalMatrix2x2::new(
        BigRational::one(),
        BigRational::zero(),
        half(),
        BigRational::one(),
    );
    let t3 = RationalMatrix2x2::new(
        BigRational::one(),
        half(),
        BigRational::zero(),
        BigRational::one(),
    );

    let graph = EvaluatedPathKernelGraph::new(vertices, edges, vec![t1, t2, t3])
        .checked_invariant_3ae276a2("declared LGGR fixture is a checked graph");
    let cycle = vec![0, 1, 2];
    (graph, cycle)
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/matrix_path_kernel.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:matrix-path-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_homology::scalar::{q, qr};

    #[test]
    fn test_canonical_lggr_counterexample() {
        let (graph, cycle) = generate_canonical_lggr_counterexample();
        let (local_green, colors) = graph.check_local_green(qr(1, 2)).unwrap();
        assert!(local_green);
        assert_eq!(
            colors,
            vec![
                EvaluationColor::Green,
                EvaluationColor::Green,
                EvaluationColor::Green
            ]
        );

        let (global_green, cycle_prod) = graph.check_global_cycle(&cycle, qr(1, 10)).unwrap();
        assert!(!global_green); // Global Red!
        assert!(!cycle_prod.deviation_from_identity().unwrap().is_zero());
    }

    #[test]
    fn test_coda_gtla_trace_contractivity() {
        let graph = EvaluatedPathKernelGraph::new(vec![], vec![], vec![]).unwrap();
        let valid_trace = vec![q(1), qr(1, 2), qr(1, 4), q(0)];
        assert!(graph.verify_coda_gtla_trace(&valid_trace));

        let non_contractive = vec![
            q(1),
            qr(1, 2),
            qr(3, 4), // increased!
        ];
        assert!(!graph.verify_coda_gtla_trace(&non_contractive));
    }
    #[test]
    fn malformed_walks_cycles_and_budgets_refuse() {
        let (mut graph, _) = generate_canonical_lggr_counterexample();
        assert!(graph.evaluate_path(&[0, 2]).is_err());
        assert!(graph.evaluate_path(&[99]).is_err());
        assert!(graph.check_global_cycle(&[0, 1], q(0)).is_err());
        assert!(graph.check_global_cycle(&[], q(0)).is_err());
        assert!(graph.check_local_green(q(-1)).is_err());
        assert!(graph
            .compute_cech_gluing_defect(&[RationalMatrix2x2::identity()], &[(0, 1)])
            .is_err());
        graph.edges[0].0 = "outside".into();
        assert!(graph.evaluate_path(&[0]).is_err());
    }
    #[test]
    fn nonnegative_trace_has_absorbing_zero_and_no_vacuous_empty_run() {
        let graph = EvaluatedPathKernelGraph::new(vec![], vec![], vec![]).unwrap();
        assert!(!graph.verify_coda_gtla_trace(&[q(0), q(1)]));
        assert!(!graph.verify_coda_gtla_trace(&[q(-1), q(-2)]));
        assert!(!graph.verify_coda_gtla_trace(&[]));
        assert!(graph.verify_coda_gtla_trace(&[q(1), q(0), q(0)]));
        let invalid = BigRational::new_raw(BigInt::from(1), BigInt::from(0));
        assert!(!graph.verify_coda_gtla_trace(&[invalid]));
    }
}
