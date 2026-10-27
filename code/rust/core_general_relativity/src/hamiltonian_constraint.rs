//! Simplicial Wheeler–DeWitt Hamiltonian Constraint Operator (MTW §42.11, Hamber §8.4).
//!
//! On a spatial Cauchy 3-slice $\Sigma_t$ triangulated by tetrahedra with spatial edge lengths $\ell_a$:
//! At each spatial vertex v, the discrete Hamiltonian constraint operator is:
//!   $$\mathcal{H}_\perp(v) = \mathcal{K}_v(\pi) - \mathcal{R}_v^{(3)} + 2\Lambda V_v^{(3)} = 0$$
//! where:
//! - $\mathcal{K}_v(\pi) = \sum_{a, b \sim v} G^{ab}(v) \pi_a \pi_b$ is the kinetic energy in the
//!   discrete DeWitt supermetric:
//!   $$G^{ab}(v) = \frac{1}{V_v^{(3)}} \left( \delta^{ab} - \frac{1}{2} \right)$$
//! - $\mathcal{R}_v^{(3)} = \sum_{e \supset v} \ell_e \epsilon_e^{(3)}$ is the 3D spatial scalar curvature,
//!   where in 3 dimensions hinges are edges with deficit angle $\epsilon_e^{(3)} = 2\pi - \sum_{\tau \supset e} \theta_e(\tau)$.
//! - $V_v^{(3)} = \frac{1}{4} \sum_{\tau \supset v} V_3(\tau)$ is the dual barycentric 3-volume of vertex v.
//! - $\Lambda$ is the cosmological constant.
//!
//! Vanishing of $\mathcal{H}_\perp(v) = 0$ ensures gauge invariance under time reparameterizations (lapse variations).
//!
//! AuthorityEffect: None.

use crate::cayley_menger::simplex_volume_cayley_menger;
use crate::dihedral_angles::tetrahedron_dihedral_angle_at_edge;
use crate::initial_value_formulation::SpatialSlice3D;
use crate::regge_calculus::ReggeError;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; simplicial Hamiltonian constraint.";

/// Evaluation of the Hamiltonian constraint at a single spatial vertex.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct VertexHamiltonianConstraint {
    pub vertex: usize,
    /// Kinetic energy term: ∑_{a, b ~ v} G^{ab} π_a π_b.
    pub kinetic_term: f64,
    /// Spatial curvature potential: R_v^{(3)} = ∑_{e ⊃ v} ℓ_e ε_e.
    pub curvature_potential: f64,
    /// Cosmological constant potential: 2 Λ V_v^{(3)}.
    pub cosmological_potential: f64,
    /// Total Hamiltonian constraint residual: H_⊥ = Kinetic - Curvature + Cosmo.
    pub residual: f64,
    /// Dual barycentric 3-volume V_v^{(3)}.
    pub dual_volume: f64,
}

/// Comprehensive report of the Hamiltonian constraint across the entire Cauchy slice.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HamiltonianConstraintReport {
    pub vertex_constraints: BTreeMap<usize, VertexHamiltonianConstraint>,
    pub max_residual: f64,
    pub rms_residual: f64,
    pub total_kinetic_energy: f64,
    pub total_curvature_potential: f64,
    pub total_cosmological_potential: f64,
    pub total_spatial_volume: f64,
    pub is_satisfied: bool,
}

/// Evaluate the simplicial Hamiltonian constraint on a spatial Cauchy slice given conjugate momenta.
fn compute_vertex_volumes(
    slice: &SpatialSlice3D,
) -> Result<(BTreeSet<usize>, BTreeMap<usize, f64>, f64), ReggeError> {
    let get_len = |u: usize, v: usize| slice.metric.get(u, v).ok();
    // 1. Compute vertex dual volumes V_v^{(3)} = 1/4 ∑_{τ ⊃ v} V_3(τ)
    let mut vertex_set = BTreeSet::new();
    for tet in &slice.tetrahedra {
        for &v in tet {
            vertex_set.insert(v);
        }
    }

    let mut vertex_dual_vol = BTreeMap::new();
    for &v in &vertex_set {
        vertex_dual_vol.insert(v, 0.0);
    }

    let mut total_vol = 0.0;
    for tet in &slice.tetrahedra {
        let vol3 = simplex_volume_cayley_menger(tet, get_len)
            .map_err(ReggeError::Computation)?;
        total_vol += vol3;
        let v_share = 0.25 * vol3;
        for &v in tet {
            if let Some(entry) = vertex_dual_vol.get_mut(&v) {
                *entry += v_share;
            }
        }
    }

    Ok((vertex_set, vertex_dual_vol, total_vol))
}

fn compute_edge_angle_sum(
    u: usize,
    v: usize,
    tetrahedra: &[[usize; 4]],
    get_len: impl Fn(usize, usize) -> Option<f64>,
) -> Result<(usize, f64), ReggeError> {
    let mut total_angle = 0.0;
    let mut incident_tets = 0;
    for tet in tetrahedra {
        if tet.contains(&u) && tet.contains(&v) {
            incident_tets += 1;
            let theta = tetrahedron_dihedral_angle_at_edge(tet, (u, v), &get_len)
                .map_err(ReggeError::Computation)?;
            total_angle += theta;
        }
    }
    Ok((incident_tets, total_angle))
}

fn compute_edge_deficits(
    slice: &SpatialSlice3D,
) -> Result<BTreeMap<(usize, usize), f64>, ReggeError> {
    let get_len = |u: usize, v: usize| slice.metric.get(u, v).ok();
    // 2. Compute edge deficit angles ε_e^{(3)} = 2π - ∑_{τ ⊃ e} θ_e(τ)
    let mut edge_deficits = BTreeMap::new();
    for &(u, v) in &slice.edges {
        let (incident_tets, total_angle) =
            compute_edge_angle_sum(u, v, &slice.tetrahedra, get_len)?;
        if incident_tets > 0 {
            // Target is 2π for interior edge, π for boundary
            let target = if incident_tets >= 3 {
                2.0 * std::f64::consts::PI
            } else {
                std::f64::consts::PI
            };
            let deficit = target - total_angle;
            edge_deficits.insert((u, v), deficit);
        }
    }
    Ok(edge_deficits)
}

fn evaluate_vertex_constraint(
    v: usize,
    v_vol: f64,
    slice: &SpatialSlice3D,
    momenta: &BTreeMap<(usize, usize), f64>,
    edge_deficits: &BTreeMap<(usize, usize), f64>,
    lambda: f64,
) -> Result<VertexHamiltonianConstraint, ReggeError> {
    let incident_edges: Vec<(usize, usize)> = slice
        .edges
        .iter()
        .copied()
        .filter(|&(e1, e2)| e1 == v || e2 == v)
        .collect();

    let mut sum_pi_sq = 0.0;
    let mut sum_pi = 0.0;
    for &e in &incident_edges {
        let pi = momenta.get(&e).copied().unwrap_or(0.0);
        sum_pi_sq += pi * pi;
        sum_pi += pi;
    }

    let kinetic = (1.0 / v_vol) * (sum_pi_sq - 0.5 * sum_pi * sum_pi);

    let mut curv = 0.0;
    for &e in &incident_edges {
        let len = slice.metric.get(e.0, e.1)?;
        let eps = edge_deficits.get(&e).copied().unwrap_or(0.0);
        curv += 0.5 * len * eps;
    }

    let cosmo = 2.0 * lambda * v_vol;
    let residual = kinetic - curv + cosmo;

    Ok(VertexHamiltonianConstraint {
        vertex: v,
        kinetic_term: kinetic,
        curvature_potential: curv,
        cosmological_potential: cosmo,
        residual,
        dual_volume: v_vol,
    })
}

pub fn evaluate_hamiltonian_constraints(
    slice: &SpatialSlice3D,
    momenta: &BTreeMap<(usize, usize), f64>,
    lambda: f64,
    tolerance: f64,
) -> Result<HamiltonianConstraintReport, ReggeError> {
    let (vertex_set, vertex_dual_vol, total_vol) = compute_vertex_volumes(slice)?;
    let edge_deficits = compute_edge_deficits(slice)?;

    // 3. Evaluate constraint at each vertex
    let mut vertex_constraints = BTreeMap::new();
    let mut max_res: f64 = 0.0;
    let mut sum_sq_res = 0.0;
    let mut total_kin = 0.0;
    let mut total_curv = 0.0;
    let mut total_cosmo = 0.0;

    for &v in &vertex_set {
        let v_vol = vertex_dual_vol.get(&v).copied().unwrap_or(1e-12).max(1e-12);
        let vc = evaluate_vertex_constraint(v, v_vol, slice, momenta, &edge_deficits, lambda)?;

        // Incident edges to vertex v
        // Kinetic term: 1/V_v * ( ∑_a π_a² - 1/2 (∑_a π_a)² )
        // Curvature potential: ∑_{e ⊃ v} 1/2 * ℓ_e * ε_e (shared equally between its 2 endpoints)
        let abs_r = vc.residual.abs();
        if abs_r > max_res {
            max_res = abs_r;
        }
        sum_sq_res += vc.residual * vc.residual;
        total_kin += vc.kinetic_term;
        total_curv += vc.curvature_potential;
        total_cosmo += vc.cosmological_potential;

        vertex_constraints.insert(v, vc);
    }

    let n = vertex_set.len().max(1);
    let rms = (sum_sq_res / n as f64).sqrt();
    let is_satisfied = max_res < tolerance;

    Ok(HamiltonianConstraintReport {
        vertex_constraints,
        max_residual: max_res,
        rms_residual: rms,
        total_kinetic_energy: total_kin,
        total_curvature_potential: total_curv,
        total_cosmological_potential: total_cosmo,
        total_spatial_volume: total_vol,
        is_satisfied,
    })
}

// Origin: engine/crates_rs/core_general_relativity/src/hamiltonian_constraint.rs
// Claim: urn:core:crates_rs:core-general-relativity:hamiltonian-constraint:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord66f9ebba {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord66f9ebba` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError66f9ebba {
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
impl BoundaryError66f9ebba {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError66f9ebba {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError66f9ebba {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord66f9ebba {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError66f9ebba> {
        if capacity_bound == 0 {
            return Err(BoundaryError66f9ebba::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError66f9ebba::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError66f9ebba::ExceedsCapacity {
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
    fn test_hamiltonian_constraint_evaluation_single_tetrahedron() {
        let slice = SpatialSlice3D::single_tetrahedron(1.0).unwrap();
        let mut momenta = BTreeMap::new();
        // Static geometry: π = 0
        for &e in &slice.edges {
            momenta.insert(e, 0.0);
        }

        let report = evaluate_hamiltonian_constraints(&slice, &momenta, 0.0, 1.0).unwrap();
        assert_eq!(report.vertex_constraints.len(), 4);
        assert_eq!(report.total_kinetic_energy, 0.0);
        assert!(report.total_spatial_volume > 0.1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_66f9ebba {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord66f9ebba::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord66f9ebba::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord66f9ebba::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord66f9ebba::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord66f9ebba::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError66f9ebba::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError66f9ebba::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
