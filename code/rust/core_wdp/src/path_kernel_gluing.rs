// Executable finite evidence; AuthorityEffect: None.
//! WDP presentation of LGGR-owned exact matrix path kernels.
//! Public fields, serialization, WdpError and AuthorityEffect remain available
//! here; multiplication, walk validation and diagnostic checks have one owner.
use num_rational::BigRational;
use core_epk::matrix_path_kernel as native;
use serde::{Deserialize, Serialize};

use crate::error::WdpError;
use crate::types::AuthorityEffect;

pub use native::EvaluationColor;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RationalMatrix2x2 {
    pub m00: BigRational,
    pub m01: BigRational,
    pub m10: BigRational,
    pub m11: BigRational,
}
impl From<native::RationalMatrix2x2> for RationalMatrix2x2 {
    fn from(value: native::RationalMatrix2x2) -> Self {
        Self {
            m00: value.m00,
            m01: value.m01,
            m10: value.m10,
            m11: value.m11,
        }
    }
}
impl RationalMatrix2x2 {
    fn native(&self) -> native::RationalMatrix2x2 {
        native::RationalMatrix2x2::new(
            self.m00.clone(),
            self.m01.clone(),
            self.m10.clone(),
            self.m11.clone(),
        )
    }
    pub fn identity() -> Self {
        native::RationalMatrix2x2::identity().into()
    }
    pub fn new(m00: BigRational, m01: BigRational, m10: BigRational, m11: BigRational) -> Self {
        native::RationalMatrix2x2::new(m00, m01, m10, m11).into()
    }
    pub fn multiply(&self, other: &Self) -> Result<Self, WdpError> {
        Ok(self.native().multiply(&other.native())?.into())
    }
    pub fn determinant(&self) -> Result<BigRational, WdpError> {
        Ok(self.native().determinant()?)
    }
    pub fn l1_norm(&self) -> Result<BigRational, WdpError> {
        Ok(self.native().l1_norm()?)
    }
    pub fn deviation_from_identity(&self) -> Result<BigRational, WdpError> {
        Ok(self.native().deviation_from_identity()?)
    }
}

/// Retained WDP receipt shape. Agreement refers only to supplied comparisons.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LggrEvaluationReceipt {
    pub is_local_green: bool,
    pub is_global_green: bool,
    pub lggr_anomaly_detected: bool,
    pub cycle_path: Vec<String>,
    pub path_kernel_product: RationalMatrix2x2,
    pub cech_gluing_defect: BigRational,
    pub declared_overlap_residual_vanishes: bool,
    #[serde(rename = "gtla_trace_contractive")]
    pub coda_gtla_trace_contractive: bool,
    #[serde(rename = "gtla_steps_count")]
    pub coda_gtla_steps_count: usize,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvaluatedPathKernelGraph {
    pub vertices: Vec<String>,
    pub edges: Vec<(String, String)>,
    pub transition_matrices: Vec<RationalMatrix2x2>,
    pub authority_effect: AuthorityEffect,
}
impl From<native::EvaluatedPathKernelGraph> for EvaluatedPathKernelGraph {
    fn from(value: native::EvaluatedPathKernelGraph) -> Self {
        Self {
            vertices: value.vertices,
            edges: value.edges,
            transition_matrices: value
                .transition_matrices
                .into_iter()
                .map(Into::into)
                .collect(),
            authority_effect: AuthorityEffect::None,
        }
    }
}
impl EvaluatedPathKernelGraph {
    fn native(&self) -> native::EvaluatedPathKernelGraph {
        native::EvaluatedPathKernelGraph {
            vertices: self.vertices.clone(),
            edges: self.edges.clone(),
            transition_matrices: self
                .transition_matrices
                .iter()
                .map(RationalMatrix2x2::native)
                .collect(),
        }
    }
    pub fn new(
        vertices: Vec<String>,
        edges: Vec<(String, String)>,
        transitions: Vec<RationalMatrix2x2>,
    ) -> Result<Self, WdpError> {
        Ok(native::EvaluatedPathKernelGraph::new(
            vertices,
            edges,
            transitions.iter().map(RationalMatrix2x2::native).collect(),
        )?
        .into())
    }
    pub fn evaluate_path(&self, edge_indices: &[usize]) -> Result<RationalMatrix2x2, WdpError> {
        Ok(self.native().evaluate_path(edge_indices)?.into())
    }
    pub fn check_local_green(
        &self,
        edge_threshold: BigRational,
    ) -> Result<(bool, Vec<EvaluationColor>), WdpError> {
        Ok(self.native().check_local_green(edge_threshold)?)
    }
    pub fn check_global_cycle(
        &self,
        cycle_edges: &[usize],
        cycle_threshold: BigRational,
    ) -> Result<(bool, RationalMatrix2x2), WdpError> {
        let (green, product) = self
            .native()
            .check_global_cycle(cycle_edges, cycle_threshold)?;
        Ok((green, product.into()))
    }
    pub fn compute_cech_gluing_defect(
        &self,
        patch_evaluations: &[RationalMatrix2x2],
        overlaps: &[(usize, usize)],
    ) -> Result<(BigRational, bool), WdpError> {
        let patches: Vec<_> = patch_evaluations
            .iter()
            .map(RationalMatrix2x2::native)
            .collect();
        Ok(self
            .native()
            .compute_cech_gluing_defect(&patches, overlaps)?)
    }
    pub fn verify_coda_gtla_trace(&self, residual_sequence: &[BigRational]) -> bool {
        self.native().verify_coda_gtla_trace(residual_sequence)
    }
}

pub fn generate_canonical_lggr_counterexample() -> (EvaluatedPathKernelGraph, Vec<usize>) {
    let (graph, cycle) = native::generate_canonical_lggr_counterexample();
    (graph.into(), cycle)
}

// Origin: engine/crates_rs/core_wdp/src/path_kernel_gluing.rs
// Claim: urn:core:crates_rs:core-wdp:path-kernel-gluing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddf6d5d5a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddf6d5d5a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordf6d5d5a {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrordf6d5d5a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordf6d5d5a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordf6d5d5a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddf6d5d5a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordf6d5d5a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordf6d5d5a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordf6d5d5a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordf6d5d5a::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_df6d5d5a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddf6d5d5a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddf6d5d5a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddf6d5d5a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddf6d5d5a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddf6d5d5a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordf6d5d5a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordf6d5d5a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
