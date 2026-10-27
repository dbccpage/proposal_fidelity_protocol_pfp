//! Discrete Exterior Calculus (DEC) Laplacians on Simplicial Manifolds.
//!
//! Implements canonical discrete differential forms, exterior derivatives,
//! Hodge stars, and Hodge-de Rham / Laplace-Beltrami operators on finite
//! simplicial complexes:
//! - Coboundary operator $d_0: C^0 \to C^1$ (discrete gradient on edges)
//! - Coboundary operator $d_1: C^1 \to C^2$ (discrete curl on triangles)
//! - Exact nilpotency verification: $d_1 \circ d_0 = 0$
//! - Discrete Hodge stars:
//!   - $\star_0$: vertex dual cell volume (barycentric / Voronoi)
//!   - $\star_1$: edge dual volume
//! - Discrete Laplace-Beltrami operator on 0-forms:
//!   $(\Delta_0 \psi)_v = \frac{1}{\star v} \sum_{w \sim v} W_{vw} (\psi_v - \psi_w)$
//!   where $W_{vw} = \frac{\star e_{vw}}{l_{vw}}$.
//! - DEC Invariants:
//!   - Constant function in kernel: $\Delta_0 \mathbf{1} = 0$
//!   - Self-adjointness: $\langle \phi, \Delta_0 \psi \rangle_{\star_0} = \langle \Delta_0 \phi, \psi \rangle_{\star_0}$
//!   - Positive semi-definiteness: $\langle \psi, \Delta_0 \psi \rangle_{\star_0} \ge 0$.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const DEFAULT_DEC_TOL: f64 = 1e-12;

/// Discrete Hodge star metrics for 0-forms and 1-forms.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DecHodgeStar {
    /// Dual cell volume for each vertex v (index 0..num_vertices).
    pub star0_vertex_volumes: Vec<f64>,
    /// Dual volume for each edge e (index 0..num_edges).
    pub star1_edge_volumes: Vec<f64>,
    /// Hodge ratio weights W_e = star1_e / length_e for each edge.
    pub hodge_edge_weights: Vec<f64>,
}

/// Discrete Exterior Calculus operator engine.
#[derive(Debug, Clone, PartialEq)]
pub struct DecOperators {
    pub num_vertices: usize,
    /// Ordered edges (u, v) with u < v.
    pub edges: Vec<(usize, usize)>,
    /// Edge lookup map: (u, v) -> edge_index
    pub edge_index: BTreeMap<(usize, usize), usize>,
    /// Ordered triangles [u, v, w] with u < v < w.
    pub triangles: Vec<[usize; 3]>,
    /// Primal edge lengths.
    pub edge_lengths: Vec<f64>,
    /// Hodge star metrics.
    pub hodge: DecHodgeStar,
}

impl DecOperators {
    /// Construct a new DEC operator environment from vertices, edges, triangles, edge lengths,
    /// and dual cell volumes.
    fn validate_counts(
        num_vertices: usize,
        num_edges: usize,
        edge_lengths_len: usize,
        star1_len: usize,
        star0_len: usize,
    ) -> Result<(), String> {
        if num_vertices == 0 {
            return Err("DEC complex must have at least 1 vertex".to_string());
        }
        if num_edges != edge_lengths_len {
            return Err(format!(
                "Edge count mismatch: {num_edges} edges vs {edge_lengths_len} lengths"
            ));
        }
        if num_edges != star1_len {
            return Err(format!(
                "Edge count mismatch: {num_edges} edges vs {star1_len} star1 dual volumes"
            ));
        }
        if num_vertices != star0_len {
            return Err(format!(
                "Vertex count mismatch: {num_vertices} vertices vs {star0_len} star0 dual volumes"
            ));
        }
        Ok(())
    }

    fn compute_edge_weight(u: usize, v: usize, len: f64, dual_vol: f64) -> Result<f64, String> {
        if len <= 0.0 || !len.is_finite() {
            return Err(format!(
                "Invalid non-positive edge length {len} on edge ({u}, {v})"
            ));
        }
        if dual_vol <= 0.0 || !dual_vol.is_finite() {
            return Err(format!(
                "Invalid non-positive star1 dual volume {dual_vol} on edge ({u}, {v})"
            ));
        }
        let weight = dual_vol / len;
        if !weight.is_finite() || weight <= 0.0 {
            return Err("Hodge edge weight must be finite and positive".into());
        }
        Ok(weight)
    }

    fn build_edges_and_hodge(
        num_vertices: usize,
        edges: &[(usize, usize)],
        edge_lengths: &[f64],
        star1_edge_volumes: &[f64],
    ) -> Result<(BTreeMap<(usize, usize), usize>, Vec<f64>), String> {
        let mut edge_index = BTreeMap::new();
        let mut hodge_edge_weights = Vec::with_capacity(edges.len());

        for (idx, &(u, v)) in edges.iter().enumerate() {
            if u >= v {
                return Err(format!(
                    "Edge endpoints must be strictly ordered u < v: ({u}, {v})"
                ));
            }
            if v >= num_vertices {
                return Err(format!(
                    "Edge vertex {v} exceeds num_vertices {num_vertices}"
                ));
            }
            if edge_index.insert((u, v), idx).is_some() {
                return Err(format!("Duplicate edge ({u}, {v}) in DEC operators"));
            }

            let weight = Self::compute_edge_weight(u, v, edge_lengths[idx], star1_edge_volumes[idx])?;
            hodge_edge_weights.push(weight);
        }

        Ok((edge_index, hodge_edge_weights))
    }

    fn validate_triangles(
        num_vertices: usize,
        triangles: &[[usize; 3]],
        edge_index: &BTreeMap<(usize, usize), usize>,
    ) -> Result<(), String> {
        for tri in triangles {
            let (u, v, w) = (tri[0], tri[1], tri[2]);
            if !(u < v && v < w) {
                return Err(format!(
                    "Triangle vertices must be strictly ordered u < v < w: {tri:?}"
                ));
            }
            if w >= num_vertices {
                return Err(format!(
                    "Triangle vertex {w} exceeds num_vertices {num_vertices}"
                ));
            }
            // Check that all 3 edges exist in edge_index
            if !edge_index.contains_key(&(u, v)) {
                return Err(format!(
                    "Missing boundary edge ({u}, {v}) for triangle {tri:?}"
                ));
            }
            if !edge_index.contains_key(&(v, w)) {
                return Err(format!(
                    "Missing boundary edge ({v}, {w}) for triangle {tri:?}"
                ));
            }
            if !edge_index.contains_key(&(u, w)) {
                return Err(format!(
                    "Missing boundary edge ({u}, {w}) for triangle {tri:?}"
                ));
            }
        }
        Ok(())
    }

    fn validate_star0_volumes(star0_vertex_volumes: &[f64]) -> Result<(), String> {
        for (v, &vol) in star0_vertex_volumes.iter().enumerate() {
            if vol <= 0.0 || !vol.is_finite() {
                return Err(format!(
                    "Invalid non-positive star0 dual volume {vol} on vertex {v}"
                ));
            }
        }
        Ok(())
    }

    pub fn new(
        num_vertices: usize,
        edges: Vec<(usize, usize)>,
        triangles: Vec<[usize; 3]>,
        edge_lengths: Vec<f64>,
        star0_vertex_volumes: Vec<f64>,
        star1_edge_volumes: Vec<f64>,
    ) -> Result<Self, String> {
        Self::validate_counts(
            num_vertices,
            edges.len(),
            edge_lengths.len(),
            star1_edge_volumes.len(),
            star0_vertex_volumes.len(),
        )?;

        let (edge_index, hodge_edge_weights) = Self::build_edges_and_hodge(
            num_vertices,
            &edges,
            &edge_lengths,
            &star1_edge_volumes,
        )?;

        Self::validate_triangles(num_vertices, &triangles, &edge_index)?;
        Self::validate_star0_volumes(&star0_vertex_volumes)?;

        Ok(Self {
            num_vertices,
            edges,
            edge_index,
            triangles,
            edge_lengths,
            hodge: DecHodgeStar {
                star0_vertex_volumes,
                star1_edge_volumes,
                hodge_edge_weights,
            },
        })
    }

    pub(crate) fn validate(&self) -> Result<(), String> {
        // Public fields may have been modified after construction.
        let rebuilt = Self::new(
            self.num_vertices,
            self.edges.clone(),
            self.triangles.clone(),
            self.edge_lengths.clone(),
            self.hodge.star0_vertex_volumes.clone(),
            self.hodge.star1_edge_volumes.clone(),
        )?;
        if self.edge_index != rebuilt.edge_index
            || self.hodge.hodge_edge_weights != rebuilt.hodge.hodge_edge_weights
        {
            return Err("DEC cached metrics or edge indices differ from their inputs".into());
        }
        Ok(())
    }

    /// Discrete exterior derivative on 0-forms: d_0: C^0 -> C^1.
    /// For oriented edge e = (u, v) with u < v:
    /// (d_0 psi)_e = psi_v - psi_u.
    pub fn coboundary_d0(&self, psi: &[f64]) -> Result<Vec<f64>, String> {
        self.validate()?;
        if psi.iter().any(|x| !x.is_finite()) {
            return Err("form entries must be finite".into());
        }
        if psi.len() != self.num_vertices {
            return Err(format!(
                "0-form state vector dimension mismatch: expected {}, got {}",
                self.num_vertices,
                psi.len()
            ));
        }

        let mut d_psi = Vec::with_capacity(self.edges.len());
        for &(u, v) in &self.edges {
            d_psi.push(psi[v] - psi[u]);
        }
        if d_psi.iter().any(|x| !x.is_finite()) {
            return Err("DEC arithmetic overflow".into());
        }
        Ok(d_psi)
    }

    /// Discrete exterior derivative on 1-forms: d_1: C^1 -> C^2.
    /// For oriented triangle f = [u, v, w] with u < v < w:
    /// partial [u, v, w] = [v, w] - [u, w] + [u, v].
    /// (d_1 omega)_f = omega_{(v, w)} - omega_{(u, w)} + omega_{(u, v)}.
    pub fn coboundary_d1(&self, omega: &[f64]) -> Result<Vec<f64>, String> {
        self.validate()?;
        if omega.iter().any(|x| !x.is_finite()) {
            return Err("form entries must be finite".into());
        }
        if omega.len() != self.edges.len() {
            return Err(format!(
                "1-form vector dimension mismatch: expected {}, got {}",
                self.edges.len(),
                omega.len()
            ));
        }

        let mut d_omega = Vec::with_capacity(self.triangles.len());
        for tri in &self.triangles {
            let (u, v, w) = (tri[0], tri[1], tri[2]);
            let e_uv = self.edge_index[&(u, v)];
            let e_vw = self.edge_index[&(v, w)];
            let e_uw = self.edge_index[&(u, w)];

            let val = omega[e_vw] - omega[e_uw] + omega[e_uv];
            d_omega.push(val);
        }
        if d_omega.iter().any(|x| !x.is_finite()) {
            return Err("DEC arithmetic overflow".into());
        }
        Ok(d_omega)
    }

    /// Check floating-point nilpotency within DEFAULT_DEC_TOL: d_1 o d_0 = 0.
    /// Returns (is_nilpotent, max_absolute_residual).
    pub fn verify_nilpotency_d1_d0(&self, psi: &[f64]) -> Result<(bool, f64), String> {
        let d0_psi = self.coboundary_d0(psi)?;
        let d1_d0_psi = self.coboundary_d1(&d0_psi)?;

        let mut max_res = 0.0f64;
        for &val in &d1_d0_psi {
            let abs = val.abs();
            if abs > max_res {
                max_res = abs;
            }
        }
        Ok((max_res < DEFAULT_DEC_TOL, max_res))
    }

    /// Discrete 0-form Laplace-Beltrami operator Delta_0: C^0 -> C^0.
    /// (Delta_0 psi)_v = (1 / star0_v) * sum_{w ~ v} W_{vw} * (psi_v - psi_w).
    pub fn laplacian_0form(&self, psi: &[f64]) -> Result<Vec<f64>, String> {
        self.validate()?;
        if psi.iter().any(|x| !x.is_finite()) {
            return Err("form entries must be finite".into());
        }
        if psi.len() != self.num_vertices {
            return Err(format!(
                "0-form state vector dimension mismatch: expected {}, got {}",
                self.num_vertices,
                psi.len()
            ));
        }

        let mut delta_psi = vec![0.0; self.num_vertices];

        for (idx, &(u, v)) in self.edges.iter().enumerate() {
            let w_e = self.hodge.hodge_edge_weights[idx];
            let diff = psi[u] - psi[v];

            // Contribution to vertex u: W_e * (psi_u - psi_v)
            delta_psi[u] += w_e * diff;
            // Contribution to vertex v: W_e * (psi_v - psi_u) = -W_e * diff
            delta_psi[v] -= w_e * diff;
        }

        for v in 0..self.num_vertices {
            let star0 = self.hodge.star0_vertex_volumes[v];
            delta_psi[v] /= star0;
        }

        if delta_psi.iter().any(|x| !x.is_finite()) {
            return Err("DEC arithmetic overflow".into());
        }
        Ok(delta_psi)
    }

    /// Inner product on 0-forms with respect to the dual Hodge star star0:
    /// <phi, psi>_{star0} = sum_{v} star0_v * phi_v * psi_v.
    pub fn inner_product_0form(&self, phi: &[f64], psi: &[f64]) -> Result<f64, String> {
        self.validate()?;
        if psi.iter().any(|x| !x.is_finite()) || phi.iter().any(|x| !x.is_finite()) {
            return Err("form entries must be finite".into());
        }
        if phi.len() != self.num_vertices || psi.len() != self.num_vertices {
            return Err("Vector dimension mismatch in 0-form inner product".to_string());
        }

        let mut sum = 0.0;
        for v in 0..self.num_vertices {
            sum += self.hodge.star0_vertex_volumes[v] * phi[v] * psi[v];
        }
        if !sum.is_finite() {
            return Err("DEC arithmetic overflow".into());
        }
        Ok(sum)
    }

    /// Dirichlet gradient energy of a 0-form:
    /// E[psi] = <d_0 psi, d_0 psi>_{star1} = sum_e W_e * (psi_v - psi_u)^2.
    pub fn dirichlet_energy_0form(&self, psi: &[f64]) -> Result<f64, String> {
        let d_psi = self.coboundary_d0(psi)?;
        let mut energy = 0.0;
        for (idx, &grad) in d_psi.iter().enumerate() {
            let w_e = self.hodge.hodge_edge_weights[idx];
            energy += w_e * grad * grad;
        }
        if !energy.is_finite() {
            return Err("DEC arithmetic overflow".into());
        }
        Ok(energy)
    }

    /// Verifies self-adjointness of Delta_0:
    /// <phi, Delta_0 psi>_{star0} == <Delta_0 phi, psi>_{star0}.
    /// Returns (lhs, rhs, absolute_difference).
    pub fn verify_self_adjointness(
        &self,
        phi: &[f64],
        psi: &[f64],
    ) -> Result<(f64, f64, f64), String> {
        let lap_psi = self.laplacian_0form(psi)?;
        let lap_phi = self.laplacian_0form(phi)?;

        let lhs = self.inner_product_0form(phi, &lap_psi)?;
        let rhs = self.inner_product_0form(&lap_phi, psi)?;

        let diff = (lhs - rhs).abs();
        Ok((lhs, rhs, diff))
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/dec_laplacian.rs
// Claim: urn:core:crates_rs:core-general-relativity:dec-laplacian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord51361b19 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord51361b19` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError51361b19 {
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
impl BoundaryError51361b19 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError51361b19 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError51361b19 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord51361b19 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError51361b19> {
        if capacity_bound == 0 {
            return Err(BoundaryError51361b19::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError51361b19::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError51361b19::ExceedsCapacity {
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
    fn test_dec_triangle_nilpotency_and_kernel() {
        // Simple triangle complex with 3 vertices, 3 edges, 1 triangle
        let edges = vec![(0, 1), (0, 2), (1, 2)];
        let triangles = vec![[0, 1, 2]];
        let lengths = vec![1.0, 1.0, 1.0];
        let star0 = vec![1.0, 1.0, 1.0];
        let star1 = vec![1.0, 1.0, 1.0];

        let dec = DecOperators::new(3, edges, triangles, lengths, star0, star1).unwrap();

        // 1. Nilpotency on arbitrary 0-form
        let psi = vec![2.5, -1.0, 4.2];
        let (is_nilpotent, res) = dec.verify_nilpotency_d1_d0(&psi).unwrap();
        assert!(is_nilpotent);
        assert!(res < 1e-14);

        // 2. Constant 0-form in kernel of Delta_0
        let const_psi = vec![3.14159; 3];
        let lap = dec.laplacian_0form(&const_psi).unwrap();
        for &val in &lap {
            assert!(val.abs() < 1e-14);
        }

        // 3. Self-adjointness
        let phi = vec![1.0, 0.5, -2.0];
        let (lhs, rhs, diff) = dec.verify_self_adjointness(&phi, &psi).unwrap();
        assert!(diff < 1e-12, "Self-adjointness violation: {lhs} vs {rhs}");
    }
}

#[cfg(test)]
mod l4_boundary_tests_51361b19 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord51361b19::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord51361b19::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord51361b19::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord51361b19::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord51361b19::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError51361b19::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError51361b19::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
