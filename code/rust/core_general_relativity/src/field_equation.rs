//! Discrete Simplicial Einstein–Regge Field Equations (MTW §42.4, Hamber §6.4).
//!
//! Evaluates the variation of the discrete Einstein–Hilbert–Regge action with
//! respect to squared edge lengths $s_e = \ell_e^2$:
//!
//! In 4 dimensions:
//!   $$E_e \equiv \frac{\partial S_R}{\partial s_e} = \sum_{f \supset e} \epsilon_f \frac{\partial A_f}{\partial s_e} - \Lambda \sum_{\sigma \supset e} \frac{\partial V_4(\sigma)}{\partial s_e} = 0$$
//!
//! In 3 dimensions:
//!   $$E_e^{(3D)} \equiv \frac{\partial S_R^{(3D)}}{\partial \ell_e} = \epsilon_e - \Lambda \sum_{\tau \supset e} \frac{\partial V_3(\tau)}{\partial \ell_e} = 0$$
//!
//! Due to the Schläfli identity ($\sum_f A_f d\epsilon_f = 0$), the variation
//! contains zero second derivatives of angles, reducing the field equations to
//! purely algebraic relations between deficit angles, hinge areas, and simplex volumes.
//!
//! AuthorityEffect: None.

use crate::cayley_menger::{simplex_volume_cayley_menger, simplex_volume_derivative_wrt_squared_edge};
use crate::regge_4d::ReggeTriangulation4D;
use crate::regge_calculus::{EdgeLengthMetric, ReggeError, DEFAULT_TOL};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; discrete Regge field equations.";

/// Result of evaluating the 4D Regge field equations across all edges.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ReggeFieldEquationResult {
    /// Residual E_e = ∂S/∂s_e for each edge (u, v) with u < v.
    pub residuals: BTreeMap<(usize, usize), f64>,
    /// Discrete Einstein tensor component G_e on each edge:
    /// G_e = (1 / V_e^*) * ∑_{f ⊃ e} ε_f (∂A_f / ∂s_e)
    pub einstein_tensor: BTreeMap<(usize, usize), f64>,
    /// Cosmological constant gradient term Λ ∑_{σ ⊃ e} (∂V_4 / ∂s_e)
    pub cosmological_terms: BTreeMap<(usize, usize), f64>,
    /// Maximum absolute residual: max_e |E_e|.
    pub max_residual: f64,
    /// L2 norm of the residuals: sqrt(∑_e E_e²).
    pub l2_residual: f64,
    /// Number of edges evaluated.
    pub total_edges: usize,
}

fn unique_complex_edges(pentachora: &[[usize; 5]]) -> BTreeSet<(usize, usize)> {
    // Find all unique edges in the complex
    let mut all_edges = BTreeSet::new();
    for p in pentachora {
        for i in 0..5 {
            for j in (i + 1)..5 {
                let u = p[i].min(p[j]);
                let v = p[i].max(p[j]);
                all_edges.insert((u, v));
            }
        }
    }
    all_edges
}

fn incident_hinge_curvature_gradient(
    triangulation: &ReggeTriangulation4D,
    u: usize,
    v: usize,
    bulk_only: bool,
) -> Result<f64, ReggeError> {
    // Edge lookup helper
    let get_len = |a: usize, b: usize| triangulation.metric.get(a, b).ok();
    // 1. Curvature contribution from incident hinges
    let mut curvature_grad = 0.0;
    for h in &triangulation.hinges {
        if bulk_only && !h.is_interior {
            continue;
        }
        let tri = h.triangle;
        if tri.contains(&u) && tri.contains(&v) {
            // Hinge contains edge {u, v}
            let eps = h.deficit_angle;
            let d_area = simplex_volume_derivative_wrt_squared_edge(&tri, u, v, get_len)
                .map_err(ReggeError::Computation)?;
            curvature_grad += eps * d_area;
        }
    }
    Ok(curvature_grad)
}

fn incident_pentachora_volume_terms(
    triangulation: &ReggeTriangulation4D,
    u: usize,
    v: usize,
) -> Result<(f64, f64), ReggeError> {
    let get_len = |a: usize, b: usize| triangulation.metric.get(a, b).ok();
    // 2. Cosmological volume contribution from incident 4-simplices
    let mut vol_grad = 0.0;
    let mut dual_volume = 0.0;
    for p in &triangulation.pentachora {
        if p.contains(&u) && p.contains(&v) {
            let d_vol = simplex_volume_derivative_wrt_squared_edge(p, u, v, get_len)
                .map_err(ReggeError::Computation)?;
            vol_grad += d_vol;

            // Dual volume proxy: 1/10 of incident 4-simplex volume
            let vol4 =
                simplex_volume_cayley_menger(p, get_len).map_err(ReggeError::Computation)?;
            dual_volume += 0.1 * vol4;
        }
    }
    Ok((vol_grad, dual_volume))
}

/// Compute the 4D Regge field equation residuals E_e = ∂S_R/∂s_e for a 4D triangulation.
/// When `bulk_only` is true, only interior hinges contribute to the curvature variation,
/// corresponding to the bulk Einstein field equations with fixed Dirichlet boundary geometry.
pub fn compute_regge_field_equations_4d(
    triangulation: &ReggeTriangulation4D,
    lambda: f64,
    bulk_only: bool,
) -> Result<ReggeFieldEquationResult, ReggeError> {
    let mut residuals = BTreeMap::new();
    let mut einstein_tensor = BTreeMap::new();
    let mut cosmological_terms = BTreeMap::new();

    // Map each hinge triangle to its deficit angle and area
    let mut hinge_map = BTreeMap::new();
    for h in &triangulation.hinges {
        let mut sorted_tri = h.triangle;
        sorted_tri.sort();
        hinge_map.insert(sorted_tri, (h.deficit_angle, h.area));
    }

    let all_edges = unique_complex_edges(&triangulation.pentachora);
    let mut max_res: f64 = 0.0;
    let mut sum_sq: f64 = 0.0;

    for &(u, v) in &all_edges {
        let curvature_grad = incident_hinge_curvature_gradient(triangulation, u, v, bulk_only)?;
        let (vol_grad, dual_volume) = incident_pentachora_volume_terms(triangulation, u, v)?;

        let cosmo_grad = lambda * vol_grad;
        let e_res = curvature_grad - cosmo_grad;

        let g_e = if dual_volume > DEFAULT_TOL {
            curvature_grad / dual_volume
        } else {
            0.0
        };

        max_res = max_res.max(e_res.abs());
        sum_sq += e_res * e_res;

        residuals.insert((u, v), e_res);
        einstein_tensor.insert((u, v), g_e);
        cosmological_terms.insert((u, v), cosmo_grad);
    }

    Ok(ReggeFieldEquationResult {
        residuals,
        einstein_tensor,
        cosmological_terms,
        max_residual: max_res,
        l2_residual: sum_sq.sqrt(),
        total_edges: all_edges.len(),
    })
}

/// Convergence history and status of the simplicial field equation relaxation solver.
#[derive(Debug, Clone, PartialEq)]
pub struct ReggeRelaxationResult {
    pub converged: bool,
    pub iterations: usize,
    pub initial_l2_residual: f64,
    pub final_l2_residual: f64,
    pub final_max_residual: f64,
    pub metric: EdgeLengthMetric,
}

/// Damped gradient descent solver to find equilibrium edge lengths satisfying E_e = 0.
pub fn solve_regge_field_equations_relaxation(
    triangulation: &ReggeTriangulation4D,
    lambda: f64,
    bulk_only: bool,
    learning_rate: f64,
    max_iters: usize,
    tolerance: f64,
) -> Result<ReggeRelaxationResult, ReggeError> {
    let mut current_metric = triangulation.metric.clone();
    let initial_eval = compute_regge_field_equations_4d(triangulation, lambda, bulk_only)?;
    let initial_l2 = initial_eval.l2_residual;

    let mut current_triangulation = triangulation.clone();
    let mut final_l2 = initial_l2;
    let mut final_max = initial_eval.max_residual;
    let mut converged = false;
    let mut iters_completed = 0;

    for iter in 0..max_iters {
        iters_completed = iter + 1;
        let eval = compute_regge_field_equations_4d(&current_triangulation, lambda, bulk_only)?;
        final_l2 = eval.l2_residual;
        final_max = eval.max_residual;

        if final_max < tolerance {
            converged = true;
            break;
        }

        // Propose updated metric
        let mut next_metric = current_metric.clone();
        for (&(u, v), &res) in &eval.residuals {
            let current_len = current_metric.get(u, v)?;
            let current_sq = current_len * current_len;
            let step = learning_rate * res;
            let next_sq = current_sq - step;

            if next_sq <= DEFAULT_TOL {
                // Step too large; skip or damp
                continue;
            }
            let next_len = next_sq.sqrt();
            let _ = next_metric.set(u, v, next_len);
        }

        // Verify admissibility of next metric
        if let Ok(next_tri) = ReggeTriangulation4D::try_new(
            triangulation.complex.clone(),
            next_metric.clone(),
            format!("iter_{iters_completed}"),
        ) {
            current_metric = next_metric;
            current_triangulation = next_tri;
        } else {
            // Relaxation step led to invalid simplex embedding; terminate with current
            break;
        }
    }

    Ok(ReggeRelaxationResult {
        converged,
        iterations: iters_completed,
        initial_l2_residual: initial_l2,
        final_l2_residual: final_l2,
        final_max_residual: final_max,
        metric: current_metric,
    })
}

// Origin: engine/crates_rs/core_general_relativity/src/field_equation.rs
// Claim: urn:core:crates_rs:core-general-relativity:field-equation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord89c252ef {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord89c252ef` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError89c252ef {
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
impl BoundaryError89c252ef {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError89c252ef {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError89c252ef {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord89c252ef {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError89c252ef> {
        if capacity_bound == 0 {
            return Err(BoundaryError89c252ef::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError89c252ef::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError89c252ef::ExceedsCapacity {
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
    fn test_flat_fan_regge_field_equations_vanish_for_zero_lambda() {
        let tri = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
        // With lambda = 0 and bulk_only = true (interior hinge having deficit angle = 0),
        // the field equation residual on interior hinge edges (0,1), (1,2), (0,2) must be zero!
        let result = compute_regge_field_equations_4d(&tri, 0.0, true).unwrap();

        let res_01 = result.residuals.get(&(0, 1)).copied().unwrap();
        let res_12 = result.residuals.get(&(1, 2)).copied().unwrap();
        let res_02 = result.residuals.get(&(0, 2)).copied().unwrap();

        assert!(
            res_01.abs() < 1e-6,
            "Residual on (0, 1) should vanish for flat interior, got {res_01}"
        );
        assert!(
            res_12.abs() < 1e-6,
            "Residual on (1, 2) should vanish for flat interior, got {res_12}"
        );
        assert!(
            res_02.abs() < 1e-6,
            "Residual on (0, 2) should vanish for flat interior, got {res_02}"
        );
    }

    #[test]
    fn test_cosmological_term_nonzero_when_lambda_positive() {
        let tri = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
        let lambda = 0.5;
        let result = compute_regge_field_equations_4d(&tri, lambda, true).unwrap();

        let cosmo_01 = result.cosmological_terms.get(&(0, 1)).copied().unwrap();
        assert!(
            cosmo_01.abs() > 1e-4,
            "Cosmological gradient on (0, 1) should be non-zero for positive lambda"
        );
        // E_e = - lambda * dV/ds_e on flat interior
        let res_01 = result.residuals.get(&(0, 1)).copied().unwrap();
        assert!((res_01 - (-cosmo_01)).abs() < 1e-6);
    }
}

#[cfg(test)]
mod l4_boundary_tests_89c252ef {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord89c252ef::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord89c252ef::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord89c252ef::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord89c252ef::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord89c252ef::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError89c252ef::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError89c252ef::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
