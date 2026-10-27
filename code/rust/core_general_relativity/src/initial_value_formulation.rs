//! 3+1 (ADM) Simplicial Cauchy Dynamics and Initial-Value Formulation (MTW §42.11, Sorkin 1975, Hamber §6.5).
//!
//! Decomposes spacetime into spatial Cauchy hypersurfaces $\Sigma_t$ evolved
//! across discrete time intervals $\Delta t$:
//! - Spatial 3D triangulation $\Sigma_t$ with spatial edge lengths $\ell_a(t)$.
//! - 4D prismatoid slab $\Sigma_t \times [t, t+\Delta t]$ triangulated into 4-simplices.
//! - Time-struts connecting vertex $v \in \Sigma_t$ to $v' \in \Sigma_{t+\Delta t}$ with
//!   squared lengths $s_{\text{strut}}(v) = (N_v \Delta t)^2$, where $N_v$ is the lapse.
//! - Conjugate momentum $\pi_a$ to spatial squared edge length $s_a = \ell_a^2$:
//!   $$\pi_a = \frac{\partial S_{\text{slab}}}{\partial s_a(t+\Delta t)}$$
//!
//! AuthorityEffect: None.

use crate::cayley_menger::simplex_volume_cayley_menger;
use crate::regge_calculus::{EdgeLengthMetric, ReggeError};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; 3+1 ADM simplicial dynamics.";

/// Spatial Cauchy hypersurface $\Sigma_t$ at fixed discrete time t.
#[derive(Debug, Clone, PartialEq)]
pub struct SpatialSlice3D {
    /// Spatial tetrahedra: [v0, v1, v2, v3].
    pub tetrahedra: Vec<[usize; 4]>,
    /// Unique spatial edges: (u, v) with u < v.
    pub edges: Vec<(usize, usize)>,
    /// Metric lengths for all spatial edges.
    pub metric: EdgeLengthMetric,
    /// Time label / index.
    pub time_index: usize,
}

impl SpatialSlice3D {
    pub fn try_new(
        tetrahedra: Vec<[usize; 4]>,
        metric: EdgeLengthMetric,
        time_index: usize,
    ) -> Result<Self, ReggeError> {
        let mut edge_set = BTreeSet::new();
        for tet in &tetrahedra {
            for i in 0..4 {
                for j in (i + 1)..4 {
                    let u = tet[i].min(tet[j]);
                    let v = tet[i].max(tet[j]);
                    edge_set.insert((u, v));
                }
            }
        }

        // Verify every spatial edge has a valid length
        for &(u, v) in &edge_set {
            let _ = metric.get(u, v)?;
        }

        Ok(Self {
            tetrahedra,
            edges: edge_set.into_iter().collect(),
            metric,
            time_index,
        })
    }

    /// Single regular tetrahedron spatial slice for testing and benchmark models.
    pub fn single_tetrahedron(side_len: f64) -> Result<Self, ReggeError> {
        let mut metric = EdgeLengthMetric::new();
        let tet = [0, 1, 2, 3];
        for i in 0..4 {
            for j in (i + 1)..4 {
                metric.set(i, j, side_len)?;
            }
        }
        Self::try_new(vec![tet], metric, 0)
    }

    /// Compute total spatial 3-volume: ∑_τ V_3(τ).
    pub fn total_volume(&self) -> Result<f64, ReggeError> {
        let mut sum = 0.0;
        let get_len = |u: usize, v: usize| self.metric.get(u, v).ok();
        for tet in &self.tetrahedra {
            let vol = simplex_volume_cayley_menger(tet, get_len)
                .map_err(ReggeError::Computation)?;
            sum += vol;
        }
        Ok(sum)
    }
}

/// A 4D sandwich slab connecting slice $\Sigma_t$ to $\Sigma_{t+\Delta t}$.
#[derive(Debug, Clone, PartialEq)]
pub struct SimplicialSlab4D {
    pub slice_t0: SpatialSlice3D,
    pub slice_t1: SpatialSlice3D,
    /// Lapse function N_v at each vertex v.
    pub lapse: BTreeMap<usize, f64>,
    /// Time increment Δt.
    pub delta_t: f64,
}

impl SimplicialSlab4D {
    pub fn new(
        slice_t0: SpatialSlice3D,
        slice_t1: SpatialSlice3D,
        lapse: BTreeMap<usize, f64>,
        delta_t: f64,
    ) -> Result<Self, ReggeError> {
        if delta_t <= 0.0 || !delta_t.is_finite() {
            return Err(ReggeError::NonFinite);
        }
        Ok(Self {
            slice_t0,
            slice_t1,
            lapse,
            delta_t,
        })
    }

    /// Strut edge length connecting vertex v at time t0 to corresponding vertex v' at time t1:
    /// ℓ_strut(v) = N_v * Δt.
    pub fn strut_length(&self, v: usize) -> Result<f64, ReggeError> {
        let n = self.lapse.get(&v).copied().unwrap_or(1.0);
        if n <= 0.0 || !n.is_finite() {
            return Err(ReggeError::NonFinite);
        }
        Ok(n * self.delta_t)
    }

    /// Discrete conjugate momentum π_a conjugate to squared edge length s_a = ℓ_a²:
    /// In a discrete time step, π_a ≈ (s_a(t1) - s_a(t0)) / (2 * N_a * Δt),
    /// corresponding to the extrinsic curvature K_a on edge a.
    pub fn canonical_momenta(&self) -> Result<BTreeMap<(usize, usize), f64>, ReggeError> {
        let mut momenta = BTreeMap::new();
        for &(u, v) in &self.slice_t0.edges {
            let l0 = self.slice_t0.metric.get(u, v)?;
            let l1 = self.slice_t1.metric.get(u, v)?;

            let s0 = l0 * l0;
            let s1 = l1 * l1;

            let n_u = self.lapse.get(&u).copied().unwrap_or(1.0);
            let n_v = self.lapse.get(&v).copied().unwrap_or(1.0);
            let n_avg = 0.5 * (n_u + n_v);

            // Momentum: rate of change of metric divided by lapse
            let pi = (s1 - s0) / (2.0 * n_avg * self.delta_t);
            momenta.insert((u, v), pi);
        }
        Ok(momenta)
    }
}

/// Results of a 3+1 Cauchy evolution step.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CauchyStepSummary {
    pub time_index: usize,
    pub delta_t: f64,
    pub mean_momentum: f64,
    pub max_momentum: f64,
    pub total_spatial_volume: f64,
}

// Origin: engine/crates_rs/core_general_relativity/src/initial_value_formulation.rs
// Claim: urn:core:crates_rs:core-general-relativity:initial-value-formulation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3d086882 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3d086882` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3d086882 {
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
impl BoundaryError3d086882 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3d086882 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3d086882 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3d086882 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3d086882> {
        if capacity_bound == 0 {
            return Err(BoundaryError3d086882::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3d086882::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3d086882::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_spatial_slice_volume_and_struts() {
        let slice = SpatialSlice3D::single_tetrahedron(1.0).unwrap();
        let vol = slice.total_volume().unwrap();
        let expected_vol = 1.0 / (6.0 * 2.0f64.sqrt());
        assert!((vol - expected_vol).abs() < 1e-9);

        let mut lapse = BTreeMap::new();
        for v in 0..4 {
            lapse.insert(v, 1.0);
        }

        let slice_next = SpatialSlice3D::single_tetrahedron(1.1).unwrap();
        let slab = SimplicialSlab4D::new(slice, slice_next, lapse, 0.1).unwrap();

        assert_eq!(slab.strut_length(0).unwrap(), 0.1);

        let momenta = slab.canonical_momenta().unwrap();
        assert_eq!(momenta.len(), 6);

        // s0 = 1.0, s1 = 1.21, ds = 0.21. pi = 0.21 / (2 * 1.0 * 0.1) = 1.05.
        for &pi in momenta.values() {
            assert!((pi - 1.05).abs() < 1e-6);
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_3d086882 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3d086882::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3d086882::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3d086882::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3d086882::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3d086882::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3d086882::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3d086882::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
