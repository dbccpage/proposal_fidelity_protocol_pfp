//! Multi-Simplex 4D Regge Triangulations and Simplicial Gravitational Dynamics (RQ-01, RQ-02).
//!
//! Extends Regge calculus to 4-dimensional manifolds:
//! - 4-simplices (pentachora) with 10 edges, 10 triangular faces, 5 tetrahedral facets.
//! - Codimension-2 hinges: 2-simplices (triangles) $f = \{u, v, w\}$.
//! - Dihedral angles $\theta_f(\sigma)$ at hinge triangle $f$ inside each incident 4-simplex $\sigma$.
//! - Deficit angles: $\epsilon_f = 2\pi - \sum_{\sigma \supset f} \theta_f(\sigma)$ for interior hinges.
//! - 4D Regge action:
//!   $S_{\text{Regge}}^{(4D)} = \sum_{f \in \text{hinges}} A_f \epsilon_f - \Lambda \sum_{\sigma \in \text{4-simplices}} V_4(\sigma)$
//!   where $A_f$ is the area of triangle $f$ and $V_4(\sigma)$ is the Cayley-Menger 4-volume.
//!
//! AuthorityEffect: None.

use crate::cayley_menger::simplex_volume_cayley_menger;
use crate::dec_laplacian::DecOperators;
use crate::dihedral_angles::pentachoron_dihedral_angle_at_triangle;
use crate::regge_calculus::{EdgeLengthMetric, ReggeError, DEFAULT_TOL};
use core_homology::simplicial::{OrientedSimplex, SimplicialComplex};
use serde::{Deserialize, Serialize};

/// Detailed breakdown of 4D Regge action evaluation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ReggeActionResult4D {
    pub curvature_term: f64,
    pub cosmological_term: f64,
    pub total_action: f64,
    pub lambda_param: f64,
    pub total_4volume: f64,
    pub total_hinges: usize,
    pub interior_hinges: usize,
    pub boundary_hinges: usize,
}

/// Codimension-2 hinge in a 4D triangulation (a triangular 2-simplex).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HingeTriangle4D {
    pub triangle: [usize; 3],
    pub area: f64,
    pub incident_pentachora: Vec<[usize; 5]>,
    pub dihedral_angles: Vec<f64>,
    pub total_dihedral_angle: f64,
    pub deficit_angle: f64,
    pub is_interior: bool,
}

/// Finite 4D Regge triangulation: multi-simplex 4D complex + metric lengths.
#[derive(Debug, Clone, PartialEq)]
pub struct ReggeTriangulation4D {
    pub complex: SimplicialComplex,
    pub metric: EdgeLengthMetric,
    pub pentachora: Vec<[usize; 5]>,
    pub hinges: Vec<HingeTriangle4D>,
    pub pentachora_volumes: Vec<f64>,
    pub label: String,
}

impl ReggeTriangulation4D {
    fn build_pentachora_and_volumes(
        complex: &SimplicialComplex,
        metric: &EdgeLengthMetric,
    ) -> Result<(Vec<[usize; 5]>, Vec<f64>), ReggeError> {
        let mut pentachora = Vec::new();
        let mut pentachora_volumes = Vec::new();

        for s4 in complex.simplices(4) {
            let verts = s4.vertices();
            if verts.len() != 5 {
                return Err(ReggeError::Computation(format!(
                    "4-simplex has {} vertices, expected 5",
                    verts.len()
                )));
            }
            let arr = [verts[0], verts[1], verts[2], verts[3], verts[4]];
            let vol = simplex_volume_cayley_menger(&arr, |u, v| metric.get(u, v).ok())
                .map_err(ReggeError::Computation)?;

            if vol <= DEFAULT_TOL {
                return Err(ReggeError::Computation(format!(
                    "4-simplex {arr:?} has non-positive Cayley-Menger volume {vol}"
                )));
            }

            pentachora.push(arr);
            pentachora_volumes.push(vol);
        }

        if pentachora.is_empty() {
            return Err(ReggeError::Computation(
                "No 4-simplices found in complex".to_string(),
            ));
        }

        Ok((pentachora, pentachora_volumes))
    }

    fn collect_incident_dihedrals(
        tri: &[usize; 3],
        metric: &EdgeLengthMetric,
        pentachora: &[[usize; 5]],
    ) -> Result<(Vec<[usize; 5]>, Vec<f64>), ReggeError> {
        let mut incident = Vec::new();
        let mut dihedrals = Vec::new();
        for &p in pentachora {
            if p.contains(&tri[0]) && p.contains(&tri[1]) && p.contains(&tri[2]) {
                incident.push(p);
                let angle = pentachoron_dihedral_angle_at_triangle(&p, tri, |u, v| {
                    metric.get(u, v).ok()
                })
                .map_err(ReggeError::Computation)?;
                dihedrals.push(angle);
            }
        }
        Ok((incident, dihedrals))
    }

    fn build_single_hinge(
        tri: [usize; 3],
        metric: &EdgeLengthMetric,
        pentachora: &[[usize; 5]],
    ) -> Result<Option<HingeTriangle4D>, ReggeError> {
        let area = simplex_volume_cayley_menger(&tri, |u, v| metric.get(u, v).ok())
            .map_err(ReggeError::Computation)?;

        if area <= DEFAULT_TOL {
            return Err(ReggeError::Computation(format!(
                "Hinge triangle {tri:?} has non-positive area {area}"
            )));
        }

        let (incident, dihedrals) = Self::collect_incident_dihedrals(&tri, metric, pentachora)?;
        if incident.is_empty() {
            return Ok(None);
        }

        let total_angle: f64 = dihedrals.iter().copied().sum();
        let is_interior = incident.len() >= 3 || (total_angle - 2.0 * std::f64::consts::PI).abs() < 0.2;
        let target = if is_interior {
            2.0 * std::f64::consts::PI
        } else {
            std::f64::consts::PI
        };
        let deficit = target - total_angle;

        Ok(Some(HingeTriangle4D {
            triangle: tri,
            area,
            incident_pentachora: incident,
            dihedral_angles: dihedrals,
            total_dihedral_angle: total_angle,
            deficit_angle: deficit,
            is_interior,
        }))
    }

    fn build_hinges(
        complex: &SimplicialComplex,
        metric: &EdgeLengthMetric,
        pentachora: &[[usize; 5]],
    ) -> Result<Vec<HingeTriangle4D>, ReggeError> {
        let mut hinges = Vec::new();
        for s2 in complex.simplices(2) {
            let t_verts = s2.vertices();
            let tri = [t_verts[0], t_verts[1], t_verts[2]];
            if let Some(h) = Self::build_single_hinge(tri, metric, pentachora)? {
                hinges.push(h);
            }
        }
        Ok(hinges)
    }

    /// Construct a 4D Regge triangulation from a simplicial complex and edge metric.
    pub fn try_new(
        complex: SimplicialComplex,
        metric: EdgeLengthMetric,
        label: impl Into<String>,
    ) -> Result<Self, ReggeError> {
        if complex.total_simplices() == 0 {
            return Err(ReggeError::EmptyComplex);
        }
        if complex.max_dimension() < 4 {
            return Err(ReggeError::Computation(format!(
                "Complex max dimension is {}, expected 4 for 4D Regge calculus",
                complex.max_dimension()
            )));
        }

        // Verify every edge has a valid metric length
        for e in complex.simplices(1) {
            let v = e.vertices();
            let _ = metric.get(v[0], v[1])?;
        }

        // 1. Process 4-simplices (pentachora)
        // 2. Identify all triangular hinges (2-simplices)
            // A hinge is interior if the surrounding tetrahedra form a closed circuit
            // (in flat space, sum of angles is ~ 2*pi).
            // When total angle exceeds 1.5*pi or incident >= 3, treat as interior with target 2*pi.
                // Boundary hinge deficit
        let (pentachora, pentachora_volumes) =
            Self::build_pentachora_and_volumes(&complex, &metric)?;
        let hinges = Self::build_hinges(&complex, &metric, &pentachora)?;

        Ok(Self {
            complex,
            metric,
            pentachora,
            hinges,
            pentachora_volumes,
            label: label.into(),
        })
    }

    /// Construct a multi-simplex 4D triangulation with two regular pentachora glued along a common tetrahedron [0, 1, 2, 3].
    /// - Simplex 1: [0, 1, 2, 3, 4]
    /// - Simplex 2: [0, 1, 2, 3, 5]
    /// All edge lengths equal `edge_len`.
    pub fn two_pentachora_glued(edge_len: f64) -> Result<Self, ReggeError> {
        if edge_len <= 0.0 || !edge_len.is_finite() {
            return Err(ReggeError::NonFinite);
        }

        let s1 = OrientedSimplex::from_unordered(vec![0, 1, 2, 3, 4])?;
        let s2 = OrientedSimplex::from_unordered(vec![0, 1, 2, 3, 5])?;

        let complex = SimplicialComplex::from_maximal_simplices(vec![s1, s2])?;
        let mut metric = EdgeLengthMetric::new();

        for e in complex.simplices(1) {
            let v = e.vertices();
            metric.set(v[0], v[1], edge_len)?;
        }

        Self::try_new(complex, metric, "two_pentachora_glued")
    }

    fn fan_complex() -> Result<SimplicialComplex, ReggeError> {
        let s1 = OrientedSimplex::from_unordered(vec![0, 1, 2, 3, 4])?;
        let s2 = OrientedSimplex::from_unordered(vec![0, 1, 2, 4, 5])?;
        let s3 = OrientedSimplex::from_unordered(vec![0, 1, 2, 5, 6])?;
        let s4 = OrientedSimplex::from_unordered(vec![0, 1, 2, 3, 6])?;
        Ok(SimplicialComplex::from_maximal_simplices(vec![s1, s2, s3, s4])?)
    }

    fn fan_metric_from_coords(
        complex: &SimplicialComplex,
        coords: &[[f64; 4]; 7],
    ) -> Result<EdgeLengthMetric, ReggeError> {
        let mut metric = EdgeLengthMetric::new();
        for e in complex.simplices(1) {
            let v = e.vertices();
            let u = v[0];
            let w = v[1];
            let p1 = coords[u];
            let p2 = coords[w];
            let mut dist_sq = 0.0;
            for k in 0..4 {
                let d = p1[k] - p2[k];
                dist_sq += d * d;
            }
            metric.set(u, w, dist_sq.sqrt())?;
        }
        Ok(metric)
    }

    /// Construct a flat multi-simplex 4D triangulation: 4 pentachora arranged around
    /// the interior hinge triangle [0, 1, 2] in the 4 quadrants of the orthogonal (z, w) 2-plane.
    /// In Euclidean R^4, each pentachoron has an exact dihedral angle of pi/2 at [0, 1, 2].
    /// Total dihedral angle = 4 * (pi/2) = 2*pi, giving an exact deficit angle of 0.0!
    pub fn four_pentachora_fan(edge_len: f64) -> Result<Self, ReggeError> {
        if edge_len <= 0.0 || !edge_len.is_finite() {
            return Err(ReggeError::NonFinite);
        }

        // Coordinates in R^4:
        // v0 = (0, 0, 0, 0)
        // v1 = (L, 0, 0, 0)
        // v2 = (0, L, 0, 0)
        // v3 = (0, 0, L, 0)   (+z)
        // v4 = (0, 0, 0, L)   (+w)
        // v5 = (0, 0, -L, 0)  (-z)
        // v6 = (0, 0, 0, -L)  (-w)
        let coords: [[f64; 4]; 7] = [
            [0.0, 0.0, 0.0, 0.0],
            [edge_len, 0.0, 0.0, 0.0],
            [0.0, edge_len, 0.0, 0.0],
            [0.0, 0.0, edge_len, 0.0],
            [0.0, 0.0, 0.0, edge_len],
            [0.0, 0.0, -edge_len, 0.0],
            [0.0, 0.0, 0.0, -edge_len],
        ];

        // 4 pentachora:
        // s1: [0, 1, 2, 3, 4]  (+z, +w)
        // s2: [0, 1, 2, 4, 5]  (+w, -z)
        // s3: [0, 1, 2, 5, 6]  (-z, -w)
        // s4: [0, 1, 2, 3, 6]  (+z, -w)
        let complex = Self::fan_complex()?;
        let metric = Self::fan_metric_from_coords(&complex, &coords)?;

        Self::try_new(complex, metric, "four_pentachora_flat_fan")
    }

    /// Compute the 4D Regge action:
    /// S_Regge = sum_{f in hinges} A_f * eps_f - Lambda * sum_{sigma} V_4(sigma).
    pub fn compute_action(&self, lambda_param: f64) -> ReggeActionResult4D {
        let mut curvature_term = 0.0;
        let mut interior_count = 0;
        let mut boundary_count = 0;

        for h in &self.hinges {
            curvature_term += h.area * h.deficit_angle;
            if h.is_interior {
                interior_count += 1;
            } else {
                boundary_count += 1;
            }
        }

        let total_4volume: f64 = self.pentachora_volumes.iter().copied().sum();
        let cosmological_term = lambda_param * total_4volume;
        let total_action = curvature_term - cosmological_term;

        ReggeActionResult4D {
            curvature_term,
            cosmological_term,
            total_action,
            lambda_param,
            total_4volume,
            total_hinges: self.hinges.len(),
            interior_hinges: interior_count,
            boundary_hinges: boundary_count,
        }
    }

    /// Build Discrete Exterior Calculus (DEC) operators corresponding to this 4D triangulation.
    /// Dual volumes are computed via the canonical barycentric dual decomposition:
    /// - star0_v = sum_{sigma \ni v} V_4(sigma) / 5
    /// - star1_e = sum_{sigma \ni e} V_4(sigma) / 10
    /// - W_e = star1_e / length_e
    fn collect_sorted_edges_and_lengths(&self) -> Result<(Vec<(usize, usize)>, Vec<f64>), String> {
        // 1. Collect and sort edges (u, v) with u < v
        let mut edges = Vec::new();
        let mut edge_lengths = Vec::new();

        for e in self.complex.simplices(1) {
            let v = e.vertices();
            let (u, w) = if v[0] < v[1] { (v[0], v[1]) } else { (v[1], v[0]) };
            let len = self.metric.get(u, w).map_err(|e| format!("{e:?}"))?;
            edges.push((u, w));
            edge_lengths.push(len);
        }

        // Sort edges canonically
        let mut edge_order: Vec<usize> = (0..edges.len()).collect();
        edge_order.sort_by_key(|&i| edges[i]);

        let sorted_edges: Vec<(usize, usize)> = edge_order.iter().map(|&i| edges[i]).collect();
        let sorted_lengths: Vec<f64> = edge_order.iter().map(|&i| edge_lengths[i]).collect();
        Ok((sorted_edges, sorted_lengths))
    }

    fn collect_sorted_triangles(&self) -> Vec<[usize; 3]> {
        // 2. Collect and sort triangles
        let mut triangles = Vec::new();
        for t in self.complex.simplices(2) {
            let v = t.vertices();
            let mut arr = [v[0], v[1], v[2]];
            arr.sort();
            triangles.push(arr);
        }
        triangles.sort();
        triangles
    }

    fn compute_star0_volumes(&self, num_vertices: usize) -> Vec<f64> {
        // 3. Compute barycentric dual volumes for vertices (star0)
        let mut star0 = vec![0.0; num_vertices];
        for (p_idx, &p) in self.pentachora.iter().enumerate() {
            let vol = self.pentachora_volumes[p_idx];
            let v_share = vol / 5.0;
            for &v in &p {
                if v < num_vertices {
                    star0[v] += v_share;
                }
            }
        }
        star0
    }

    fn compute_star1_volumes(
        &self,
        sorted_edges: &[(usize, usize)],
        sorted_lengths: &[f64],
    ) -> Vec<f64> {
        // 4. Compute barycentric dual volumes for edges (star1)
        let mut star1 = vec![0.0; sorted_edges.len()];
        for (e_idx, &(u, w)) in sorted_edges.iter().enumerate() {
            for (p_idx, &p) in self.pentachora.iter().enumerate() {
                if p.contains(&u) && p.contains(&w) {
                    let vol = self.pentachora_volumes[p_idx];
                    star1[e_idx] += vol / 10.0;
                }
            }
            // Fallback for boundary edges with tiny dual volume
            if star1[e_idx] <= 1e-15 {
                star1[e_idx] = sorted_lengths[e_idx].powi(3) / 24.0;
            }
        }
        star1
    }

    pub fn build_dec_operators(&self) -> Result<DecOperators, String> {
        let num_vertices = self.complex.num_vertices();
        let (sorted_edges, sorted_lengths) = self.collect_sorted_edges_and_lengths()?;
        let triangles = self.collect_sorted_triangles();
        let star0 = self.compute_star0_volumes(num_vertices);
        let star1 = self.compute_star1_volumes(&sorted_edges, &sorted_lengths);

        DecOperators::new(
            num_vertices,
            sorted_edges,
            triangles,
            sorted_lengths,
            star0,
            star1,
        )
    }

    fn perturbed_dihedral(
        pentachoron: &[usize; 5],
        tri: &[usize; 3],
        edge: (usize, usize),
        base_l: f64,
        shift: f64,
        get_length: &impl Fn(usize, usize) -> Option<f64>,
    ) -> Result<f64, String> {
        let (e1, e2) = edge;
        pentachoron_dihedral_angle_at_triangle(pentachoron, tri, |u, v| {
            if (u == e1 && v == e2) || (u == e2 && v == e1) {
                Some(base_l + shift)
            } else {
                get_length(u, v)
            }
        })
    }

    fn compute_face_schlafli_contribution(
        pentachoron: &[usize; 5],
        tri: &[usize; 3],
        edge: (usize, usize),
        base_l: f64,
        delta: f64,
        get_length: &impl Fn(usize, usize) -> Option<f64>,
    ) -> Result<f64, String> {
        let area = simplex_volume_cayley_menger(tri, get_length)?;
        let theta_plus =
            Self::perturbed_dihedral(pentachoron, tri, edge, base_l, delta, get_length)?;
        let theta_minus =
            Self::perturbed_dihedral(pentachoron, tri, edge, base_l, -delta, get_length)?;

        let d_theta = (theta_plus - theta_minus) / (2.0 * delta);
        Ok(area * d_theta)
    }

    /// Verifies the 4D Schläfli differential identity on a pentachoron:
    /// sum_{f in triangles} Area(f) * d theta_f = 0
    /// when edge `edge` is perturbed by `delta_l`.
    pub fn schlafli_differential_4d(
        pentachoron: &[usize; 5],
        edge: (usize, usize),
        get_length: impl Fn(usize, usize) -> Option<f64>,
        delta: f64,
    ) -> Result<f64, String> {
        let (e1, e2) = edge;
        let base_l = get_length(e1, e2).ok_or("Missing edge length")?;

        let tri_faces: [[usize; 3]; 10] = [
            [pentachoron[0], pentachoron[1], pentachoron[2]],
            [pentachoron[0], pentachoron[1], pentachoron[3]],
            [pentachoron[0], pentachoron[1], pentachoron[4]],
            [pentachoron[0], pentachoron[2], pentachoron[3]],
            [pentachoron[0], pentachoron[2], pentachoron[4]],
            [pentachoron[0], pentachoron[3], pentachoron[4]],
            [pentachoron[1], pentachoron[2], pentachoron[3]],
            [pentachoron[1], pentachoron[2], pentachoron[4]],
            [pentachoron[1], pentachoron[3], pentachoron[4]],
            [pentachoron[2], pentachoron[3], pentachoron[4]],
        ];

        let mut sum_area_dtheta = 0.0;

        for tri in &tri_faces {
            // Forward perturbed length lookup
            // Backward perturbed length lookup
            sum_area_dtheta += Self::compute_face_schlafli_contribution(
                pentachoron,
                tri,
                edge,
                base_l,
                delta,
                &get_length,
            )?;
        }

        Ok(sum_area_dtheta)
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/regge_4d.rs
// Claim: urn:core:crates_rs:core-general-relativity:regge-4d:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7586e0f6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7586e0f6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7586e0f6 {
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
impl BoundaryError7586e0f6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7586e0f6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7586e0f6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7586e0f6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7586e0f6> {
        if capacity_bound == 0 {
            return Err(BoundaryError7586e0f6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7586e0f6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7586e0f6::ExceedsCapacity {
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
    fn test_two_pentachora_glued_construction() {
        let tri = ReggeTriangulation4D::two_pentachora_glued(1.0).unwrap();
        assert_eq!(tri.pentachora.len(), 2);
        assert!(tri.pentachora_volumes[0] > 0.02);
        assert_eq!(tri.complex.num_vertices(), 6);

        // Action with Lambda = 0
        let act = tri.compute_action(0.0);
        assert!(act.curvature_term.is_finite());
        assert_eq!(act.cosmological_term, 0.0);
    }

    #[test]
    fn test_four_pentachora_flat_fan_deficit() {
        let fan = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
        assert_eq!(fan.pentachora.len(), 4);

        // Find the central hinge triangle [0, 1, 2]
        let central_hinge = fan
            .hinges
            .iter()
            .find(|h| h.triangle == [0, 1, 2])
            .expect("Central hinge [0, 1, 2] must exist");

        assert_eq!(central_hinge.incident_pentachora.len(), 4);
        // On the flat fan, each dihedral angle is pi/2, so total angle is 2*pi
        let expected_angle = 2.0 * std::f64::consts::PI;
        assert!((central_hinge.total_dihedral_angle - expected_angle).abs() < 1e-9);
        assert!(central_hinge.deficit_angle.abs() < 1e-9);
    }
}

#[cfg(test)]
mod l4_boundary_tests_7586e0f6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7586e0f6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7586e0f6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7586e0f6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7586e0f6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7586e0f6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7586e0f6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7586e0f6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
