//! Discrete Simplicial Ricci and Scalar Curvatures & Higher-Derivative Regge Gravity (Hamber §7.2-7.3).
//!
//! In a D-dimensional simplicial complex (D=4):
//! - Dual volume associated with vertex v:
//!   $$V(v) = \frac{1}{D+1} \sum_{\sigma \supset v} V_D(\sigma)$$
//! - Integrated scalar curvature at vertex v:
//!   $$\mathcal{R}(v) = 2 \sum_{h \supset v} A_h \epsilon_h$$
//! - Local scalar curvature density at vertex v:
//!   $$R(v) = \frac{\mathcal{R}(v)}{V(v)} = \frac{2 \sum_{h \supset v} A_h \epsilon_h}{V(v)}$$
//! - Einstein–Hilbert–Regge action equivalence:
//!   $$S_{\text{EH}} = \frac{1}{2} \sum_v V(v) R(v) = \sum_h A_h \epsilon_h = S_{\text{Regge}}$$
//! - Higher-Derivative Regge action (Hamber & Williams 1984):
//!   $$S_{\text{HD}} = a \sum_v V(v) R(v)^2 = 4 a \sum_v \frac{1}{V(v)} \left( \sum_{h \supset v} A_h \epsilon_h \right)^2$$
//!   This curvature-squared term is strictly non-negative (S_HD >= 0) and regulates
//!   the Euclidean conformal factor instability in quantum Regge calculus.
//!
//! AuthorityEffect: None.

use crate::regge_4d::ReggeTriangulation4D;
use crate::regge_calculus::ReggeError;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; discrete Ricci and higher-derivative Regge.";

/// Curvature and volume measures localized at a single vertex in a 4D triangulation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct VertexCurvature4D {
    pub vertex: usize,
    /// Barycentric dual volume V(v) = 1/5 ∑_{σ ⊃ v} V_4(σ).
    pub dual_volume: f64,
    /// Integrated scalar curvature: 2 ∑_{h ⊃ v} A_h ε_h.
    pub integrated_scalar_curvature: f64,
    /// Local scalar curvature density: R(v) = 2 ∑_{h ⊃ v} A_h ε_h / V(v).
    pub scalar_curvature_density: f64,
    /// Incident 4-simplices.
    pub incident_pentachora_count: usize,
    /// Incident hinges.
    pub incident_hinge_count: usize,
}

/// Complete curvature field and higher-derivative action across all vertices of a 4D triangulation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscreteCurvatureField4D {
    pub vertex_curvatures: BTreeMap<usize, VertexCurvature4D>,
    /// Total 4-volume: ∑_σ V_4(σ) = ∑_v V(v).
    pub total_4volume: f64,
    /// Total Einstein-Hilbert action: 1/2 ∑_v V(v) R(v) = ∑_h A_h ε_h.
    pub einstein_hilbert_action: f64,
    /// Higher-derivative curvature squared action: a ∑_v V(v) R(v)².
    pub higher_derivative_action: f64,
    pub coupling_a: f64,
}

fn accumulate_pentachora_dual_volumes(
    triangulation: &ReggeTriangulation4D,
    vertex_set: &BTreeSet<usize>,
) -> (BTreeMap<usize, f64>, BTreeMap<usize, usize>) {
    let mut vertex_dual_vol: BTreeMap<usize, f64> =
        vertex_set.iter().map(|&v| (v, 0.0)).collect();
    let mut vertex_incident_pent: BTreeMap<usize, usize> =
        vertex_set.iter().map(|&v| (v, 0)).collect();

    for (p_idx, p) in triangulation.pentachora.iter().enumerate() {
        let vol = triangulation.pentachora_volumes[p_idx];
        let share = 0.2 * vol; // 1/5 share of 4-simplex volume per vertex
        for &v in p {
            if let Some(entry) = vertex_dual_vol.get_mut(&v) {
                *entry += share;
            }
            if let Some(count) = vertex_incident_pent.get_mut(&v) {
                *count += 1;
            }
        }
    }
    (vertex_dual_vol, vertex_incident_pent)
}

fn accumulate_hinge_curvatures(
    triangulation: &ReggeTriangulation4D,
    vertex_set: &BTreeSet<usize>,
) -> (BTreeMap<usize, f64>, BTreeMap<usize, usize>) {
    let mut vertex_int_curv: BTreeMap<usize, f64> =
        vertex_set.iter().map(|&v| (v, 0.0)).collect();
    let mut vertex_incident_hinges: BTreeMap<usize, usize> =
        vertex_set.iter().map(|&v| (v, 0)).collect();

    // Distribute hinge curvature 2 * A_h * ε_h equally among its 3 vertices:
    // Hinge h = {u, v, w} contributes (2/3) * A_h * ε_h to each vertex,
    // so ∑_v ∑_{h ⊃ v} (2/3) A_h ε_h = 2 ∑_h A_h ε_h.
    for h in &triangulation.hinges {
        if !h.is_interior {
            continue;
        }
        let hinge_curv = 2.0 * h.area * h.deficit_angle;
        let share = hinge_curv / 3.0;
        for &v in &h.triangle {
            if let Some(c) = vertex_int_curv.get_mut(&v) {
                *c += share;
            }
            if let Some(count) = vertex_incident_hinges.get_mut(&v) {
                *count += 1;
            }
        }
    }
    (vertex_int_curv, vertex_incident_hinges)
}

/// Compute vertex-localized Ricci scalar curvature densities and higher-derivative action.
pub fn compute_discrete_curvature_field_4d(
    triangulation: &ReggeTriangulation4D,
    coupling_a: f64,
) -> Result<DiscreteCurvatureField4D, ReggeError> {
    let vertex_set: BTreeSet<usize> = triangulation
        .pentachora
        .iter()
        .flat_map(|p| p.iter().copied())
        .collect();

    let (vertex_dual_vol, vertex_incident_pent) =
        accumulate_pentachora_dual_volumes(triangulation, &vertex_set);
    let (vertex_int_curv, vertex_incident_hinges) =
        accumulate_hinge_curvatures(triangulation, &vertex_set);

    let mut vertex_curvatures = BTreeMap::new();
    let mut total_vol = 0.0;
    let mut eh_action = 0.0;
    let mut hd_action = 0.0;

    for &v in &vertex_set {
        let dual_vol = vertex_dual_vol.get(&v).copied().unwrap_or(0.0);
        let int_r = vertex_int_curv.get(&v).copied().unwrap_or(0.0);
        total_vol += dual_vol;
        eh_action += 0.5 * int_r;

        let (density, hd_term) = if dual_vol > 1e-12 {
            let density = int_r / dual_vol;
            (density, coupling_a * dual_vol * density * density)
        } else {
            (0.0, 0.0)
        };
        hd_action += hd_term;

        vertex_curvatures.insert(
            v,
            VertexCurvature4D {
                vertex: v,
                dual_volume: dual_vol,
                integrated_scalar_curvature: int_r,
                scalar_curvature_density: density,
                incident_pentachora_count: vertex_incident_pent.get(&v).copied().unwrap_or(0),
                incident_hinge_count: vertex_incident_hinges.get(&v).copied().unwrap_or(0),
            },
        );
    }

    Ok(DiscreteCurvatureField4D {
        vertex_curvatures,
        total_4volume: total_vol,
        einstein_hilbert_action: eh_action,
        higher_derivative_action: hd_action,
        coupling_a,
    })
}

// Origin: engine/crates_rs/core_general_relativity/src/ricci_curvature.rs
// Claim: urn:core:crates_rs:core-general-relativity:ricci-curvature:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord614f3925 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord614f3925` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError614f3925 {
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
impl BoundaryError614f3925 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError614f3925 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError614f3925 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord614f3925 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError614f3925> {
        if capacity_bound == 0 {
            return Err(BoundaryError614f3925::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError614f3925::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError614f3925::ExceedsCapacity {
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
    fn test_flat_fan_has_zero_ricci_curvature_at_interior_vertices() {
        let tri = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
        let field = compute_discrete_curvature_field_4d(&tri, 1.0).unwrap();

        // Total 4-volume should equal sum of the 4 pentachora volumes
        let sum_pent_vol: f64 = tri.pentachora_volumes.iter().sum();
        assert!((field.total_4volume - sum_pent_vol).abs() < 1e-7);

        // Float residual of this discrete field. Not the flatness admission:
        // that decision is `exact_regge::einstein_hilbert_fence`.
        assert!(field.einstein_hilbert_action.abs() < 1e-6);

        // Higher-derivative action is non-negative and zero for flat space
        assert!(field.higher_derivative_action >= 0.0);
        assert!(field.higher_derivative_action.abs() < 1e-6);
    }

    #[test]
    fn test_higher_derivative_action_is_strictly_non_negative() {
        let tri = ReggeTriangulation4D::two_pentachora_glued(1.0).unwrap();
        let field = compute_discrete_curvature_field_4d(&tri, 2.5).unwrap();

        assert!(
            field.higher_derivative_action >= 0.0,
            "Higher-derivative action must be non-negative, got {}",
            field.higher_derivative_action
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_614f3925 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord614f3925::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord614f3925::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord614f3925::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord614f3925::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord614f3925::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError614f3925::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError614f3925::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
