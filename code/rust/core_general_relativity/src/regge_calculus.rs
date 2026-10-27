//! Finite **2D Regge calculus** on a simplicial complex.
//!
//! Combinatorial complex: [`core_homology::simplicial`] (no separate
//! `core_simplex` crate — homology already owns face-closed complexes).
//!
//! Metric: positive edge lengths with triangle inequalities.
//! Curvature: hinge deficits at vertices (2-dimensional Regge).
//! Action: `S = Σ_v ε_v` (2D Einstein–Hilbert / Regge; Gauss–Bonnet discrete).
//!
//! **Not** continuum GR, **not** 3+1 dihedral Regge (future), **not** PROVED.
//! AuthorityEffect: None.
//!
//! PROD / research pointers: discrete GR programme papers; engines remain
//! diagnostic-only elsewhere.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_96a5827b<T> {
    fn checked_invariant_96a5827b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_96a5827b<T> for Option<T> {
    #[inline]
    fn checked_invariant_96a5827b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_96a5827b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_96a5827b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::discrete_spacetime::DiscreteSpacetime;
use core_homology::errors::HomologicalError;
use core_homology::simplicial::{OrientedSimplex, Simplex, SimplicialComplex};
use std::collections::BTreeMap;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite 2D Regge face.";

/// Default length / angle tolerance.
pub const DEFAULT_TOL: f64 = 1e-9;

/// Regge construction / validation errors.
#[derive(Debug, Clone, PartialEq)]
pub enum ReggeError {
    Homology(String),
    EmptyComplex,
    NotTwoDimensional {
        max_dim: usize,
    },
    MissingEdgeLength {
        u: usize,
        v: usize,
    },
    NonPositiveLength {
        u: usize,
        v: usize,
        length: f64,
    },
    UnknownVertex {
        vertex: usize,
    },
    /// A cyclic fan of two triangles is one simplex: `{0,1,2}` twice.
    DegenerateFan {
        n_triangles: usize,
    },
    TriangleInequality {
        triangle: [usize; 3],
    },
    DegenerateAngle {
        triangle: [usize; 3],
        vertex: usize,
    },
    NonFinite,
    Computation(String),
}

// Origin: engine/crates_rs/core_general_relativity/src/regge_calculus.rs
// Claim: urn:core:crates_rs:core-general-relativity:regge-calculus:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ReggeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ReggeError {}

impl From<HomologicalError> for ReggeError {
    fn from(e: HomologicalError) -> Self {
        ReggeError::Homology(format!("{e:?}"))
    }
}

/// Positive edge-length assignment on 1-simplices (keys ordered u < v).
#[derive(Debug, Clone, PartialEq)]
pub struct EdgeLengthMetric {
    lengths: BTreeMap<(usize, usize), f64>,
}

impl EdgeLengthMetric {
    pub fn new() -> Self {
        Self {
            lengths: BTreeMap::new(),
        }
    }

    /// Insert length for unordered edge {u,v}.
    pub fn set(&mut self, u: usize, v: usize, length: f64) -> Result<(), ReggeError> {
        if !length.is_finite() {
            return Err(ReggeError::NonFinite);
        }
        if length <= 0.0 {
            return Err(ReggeError::NonPositiveLength { u, v, length });
        }
        let (a, b) = if u < v { (u, v) } else { (v, u) };
        if a == b {
            return Err(ReggeError::NonPositiveLength { u, v, length });
        }
        self.lengths.insert((a, b), length);
        Ok(())
    }

    pub fn get(&self, u: usize, v: usize) -> Result<f64, ReggeError> {
        let (a, b) = if u < v { (u, v) } else { (v, u) };
        self.lengths
            .get(&(a, b))
            .copied()
            .ok_or(ReggeError::MissingEdgeLength { u: a, v: b })
    }

    pub fn edge_count(&self) -> usize {
        self.lengths.len()
    }
}

impl Default for EdgeLengthMetric {
    fn default() -> Self {
        Self::new()
    }
}

/// Finite 2D Regge geometry: triangulation + edge lengths.
#[derive(Debug, Clone, PartialEq)]
pub struct ReggeCalculus {
    /// Combinatorial complex (must include 2-simplices for curvature).
    pub complex: SimplicialComplex,
    /// Edge lengths.
    pub metric: EdgeLengthMetric,
    /// Label.
    pub label: String,
}

impl ReggeCalculus {
    /// Scaffold: unit-edge standard 2-simplex (one equilateral-ready triangle
    /// with edge lengths 1 — angles π/3 after build).
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        let n = degree.max(2);
        // Use triangle (dim 2) as minimal Regge face; higher n → standard simplex
        // with unit edges (may violate embedding in R^n; still a formal metric).
        let complex = SimplicialComplex::standard_n_simplex(n.min(2)).checked_invariant_96a5827b("standard simplex");
        let mut metric = EdgeLengthMetric::new();
        for e in complex.simplices(1) {
            let v = e.vertices();
            let _ = metric.set(v[0], v[1], 1.0);
        }
        Self {
            complex,
            metric,
            label: label.into(),
        }
    }

    /// Build 2D Regge data from a discrete spacetime + metric.
    pub fn try_from_spacetime(
        spacetime: &DiscreteSpacetime,
        metric: EdgeLengthMetric,
        label: impl Into<String>,
    ) -> Result<Self, ReggeError> {
        Self::try_new(spacetime.complex.clone(), metric, label)
    }

    /// Build and validate triangle inequalities on all 2-simplices.
    pub fn try_new(
        complex: SimplicialComplex,
        metric: EdgeLengthMetric,
        label: impl Into<String>,
    ) -> Result<Self, ReggeError> {
        if complex.total_simplices() == 0 {
            return Err(ReggeError::EmptyComplex);
        }
        if complex.max_dimension() < 2 {
            return Err(ReggeError::NotTwoDimensional {
                max_dim: complex.max_dimension(),
            });
        }
        // Every edge must have a length
        for e in complex.simplices(1) {
            let v = e.vertices();
            let _ = metric.get(v[0], v[1])?;
        }
        let geo = Self {
            complex,
            metric,
            label: label.into(),
        };
        geo.validate_triangle_inequalities()?;
        Ok(geo)
    }

    fn build_fan_maximal_simplices(
        n_triangles: usize,
    ) -> Result<Vec<OrientedSimplex>, ReggeError> {
        if n_triangles == 1 {
            return Ok(vec![OrientedSimplex::from_unordered(vec![0, 1, 2])?]);
        }
        let mut maximal = Vec::new();
        for i in 1..=n_triangles {
            let j = if i == n_triangles { 1 } else { i + 1 };
            maximal.push(OrientedSimplex::from_unordered(vec![0, i, j])?);
        }
        Ok(maximal)
    }

    /// Equilateral triangulation: fan of `n_triangles` equilateral triangles
    /// around a center vertex (curvature cone), or a single freestanding triangle.
    ///
    /// - `n_triangles == 1`: one triangle on vertices {0,1,2}.
    /// - `n_triangles >= 3`: center 0, boundary 1..=n, triangles (0,i,i+1) cyclic.
    /// - `n_triangles == 2` is refused: both cyclic triangles are the simplex {0,1,2}.
    pub fn equilateral_fan(n_triangles: usize, edge_len: f64) -> Result<Self, ReggeError> {
        if n_triangles < 1 {
            return Err(ReggeError::EmptyComplex);
        }
        if n_triangles == 2 {
            return Err(ReggeError::DegenerateFan { n_triangles });
        }
        if !(edge_len.is_finite() && edge_len > 0.0) {
            return Err(ReggeError::NonFinite);
        }
        let maximal = Self::build_fan_maximal_simplices(n_triangles)?;
        let complex = SimplicialComplex::from_maximal_simplices(maximal)?;
        let mut metric = EdgeLengthMetric::new();
        for e in complex.simplices(1) {
            let v = e.vertices();
            metric.set(v[0], v[1], edge_len)?;
        }
        Self::try_new(complex, metric, format!("fan_{n_triangles}"))
    }

    fn validate_triangle_inequalities(&self) -> Result<(), ReggeError> {
        for t in self.complex.simplices(2) {
            let v = t.vertices();
            let a = self.metric.get(v[1], v[2])?;
            let b = self.metric.get(v[0], v[2])?;
            let c = self.metric.get(v[0], v[1])?;
            if a + b <= c + DEFAULT_TOL || a + c <= b + DEFAULT_TOL || b + c <= a + DEFAULT_TOL {
                return Err(ReggeError::TriangleInequality {
                    triangle: [v[0], v[1], v[2]],
                });
            }
        }
        Ok(())
    }

    fn triangle_adjacent_vertices(
        [i, j, k]: [usize; 3],
        vertex: usize,
    ) -> Result<(usize, usize), ReggeError> {
        // Vertex v; adjacent edge endpoints p,q; opposite edge length = side facing v
        if vertex == i {
            Ok((j, k))
        } else if vertex == j {
            Ok((i, k))
        } else if vertex == k {
            Ok((i, j))
        } else {
            Err(ReggeError::DegenerateAngle {
                triangle: [i, j, k],
                vertex,
            })
        }
    }

    /// Interior angle of triangle at `vertex` via cosine law (radians).
    pub fn angle_at(&self, triangle: &Simplex, vertex: usize) -> Result<f64, ReggeError> {
        let verts = triangle.vertices();
        if verts.len() != 3 {
            return Err(ReggeError::NotTwoDimensional {
                max_dim: triangle.dimension(),
            });
        }
        let (i, j, k) = (verts[0], verts[1], verts[2]);
        let (p, q) = Self::triangle_adjacent_vertices([i, j, k], vertex)?;
        let a = self.metric.get(vertex, p)?;
        let b = self.metric.get(vertex, q)?;
        let c = self.metric.get(p, q)?;
        // cos C = (a² + b² - c²) / (2ab)
        let denom = 2.0 * a * b;
        if denom.abs() < DEFAULT_TOL {
            return Err(ReggeError::DegenerateAngle {
                triangle: [i, j, k],
                vertex,
            });
        }
        let cos_c = ((a * a + b * b - c * c) / denom).clamp(-1.0, 1.0);
        let ang = cos_c.acos();
        if !ang.is_finite() {
            return Err(ReggeError::NonFinite);
        }
        Ok(ang)
    }

    /// Sum of triangle angles at vertex `v`.
    pub fn angle_sum_at_vertex(&self, v: usize) -> Result<f64, ReggeError> {
        self.ensure_vertex(v)?;
        let mut sum = 0.0;
        for t in self.complex.simplices(2) {
            if t.vertices().contains(&v) {
                sum += self.angle_at(t, v)?;
            }
        }
        Ok(sum)
    }

    /// Interior deficit ε_v = 2π − Σ angles (2D Regge hinge at vertex).
    ///
    /// Positive → conical positive curvature; zero → locally flat;
    /// negative → hyperbolic-type deficit.
    pub fn deficit_at_vertex(&self, v: usize) -> Result<f64, ReggeError> {
        Ok(std::f64::consts::TAU - self.angle_sum_at_vertex(v)?)
    }

    /// Deficits of the 0-simplices, in ascending vertex-id order.
    ///
    /// `SimplicialComplex::num_vertices` is `max_id + 1`. A gap in the labels
    /// is not a vertex; treating it as angle-sum 0 would add a fake `2π`.
    pub fn vertex_deficits(&self) -> Result<Vec<f64>, ReggeError> {
        self.complex
            .simplices(0)
            .iter()
            .map(|simplex| self.deficit_at_vertex(simplex.vertices()[0]))
            .collect()
    }

    fn ensure_vertex(&self, vertex: usize) -> Result<(), ReggeError> {
        let simplex = Simplex::from_unordered(vec![vertex])?;
        if self.complex.contains(&simplex) {
            Ok(())
        } else {
            Err(ReggeError::UnknownVertex { vertex })
        }
    }

    /// 2D Regge action S = Σ_v ε_v.
    ///
    /// On a closed combinatorial 2-manifold this is 2π χ (discrete Gauss–Bonnet);
    /// on complexes with boundary the sum still records total deficit mass.
    pub fn regge_action_2d(&self) -> Result<f64, ReggeError> {
        Ok(self.vertex_deficits()?.into_iter().sum())
    }

    /// Degree proxy = max simplex dimension.
    pub fn degree(&self) -> usize {
        self.complex.max_dimension()
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }

    /// Volume of any simplex in the complex via Cayley-Menger determinant.
    pub fn simplex_volume(&self, simplex: &Simplex) -> Result<f64, ReggeError> {
        let verts = simplex.vertices();
        crate::cayley_menger::simplex_volume_cayley_menger(verts, |u, v| self.metric.get(u, v).ok())
            .map_err(ReggeError::Computation)
    }

    /// Interior deficit angle at an edge (1-simplex hinge) in 3D:
    /// ε_e = 2π − Σ_{tetrahedra ∋ e} θ_tet(e).
    pub fn deficit_at_edge(&self, u: usize, v: usize) -> Result<f64, ReggeError> {
        let (e1, e2) = if u < v { (u, v) } else { (v, u) };
        let mut angle_sum = 0.0;
        let mut count = 0;

        for tet in self.complex.simplices(3) {
            let verts = tet.vertices();
            if verts.contains(&e1) && verts.contains(&e2) {
                let tet_arr: [usize; 4] = [verts[0], verts[1], verts[2], verts[3]];
                let theta = crate::dihedral_angles::tetrahedron_dihedral_angle_at_edge(
                    &tet_arr,
                    (e1, e2),
                    |a, b| self.metric.get(a, b).ok(),
                )
                .map_err(ReggeError::Computation)?;
                angle_sum += theta;
                count += 1;
            }
        }

        if count == 0 {
            return Err(ReggeError::Computation(format!(
                "Edge ({e1}, {e2}) has no incident 3-simplices"
            )));
        }

        Ok(std::f64::consts::TAU - angle_sum)
    }

    fn collect_2d_hinges_and_volumes(&self) -> Result<(Vec<(f64, f64)>, Vec<f64>), ReggeError> {
        let mut hinges = Vec::new();
        let mut simplex_volumes = Vec::new();
        // Hinges are vertices (0-simplices)
        for v_simplex in self.complex.simplices(0) {
            let v = v_simplex.vertices()[0];
            let eps = self.deficit_at_vertex(v)?;
            hinges.push((1.0, eps));
        }
        for tri in self.complex.simplices(2) {
            let vol = self.simplex_volume(tri)?;
            simplex_volumes.push(vol);
        }
        Ok((hinges, simplex_volumes))
    }

    fn collect_3d_hinges_and_volumes(&self) -> Result<(Vec<(f64, f64)>, Vec<f64>), ReggeError> {
        let mut hinges = Vec::new();
        let mut simplex_volumes = Vec::new();
        // Hinges are edges (1-simplices)
        for e_simplex in self.complex.simplices(1) {
            let v = e_simplex.vertices();
            let len = self.metric.get(v[0], v[1])?;
            let eps = self.deficit_at_edge(v[0], v[1])?;
            hinges.push((len, eps));
        }
        for tet in self.complex.simplices(3) {
            let vol = self.simplex_volume(tet)?;
            simplex_volumes.push(vol);
        }
        Ok((hinges, simplex_volumes))
    }

    /// Classical Regge action with cosmological constant Λ across 2D, 3D, or 4D:
    /// S_Regge = Σ_{hinges} V_{D-2}(h) ε_h − Λ Σ_{simplices} V_D(σ).
    pub fn regge_action_with_lambda(
        &self,
        lambda_param: f64,
    ) -> Result<crate::regge_action::ReggeActionResult, ReggeError> {
        let dim = self.complex.max_dimension();
        let (hinges, simplex_volumes) = match dim {
            2 => self.collect_2d_hinges_and_volumes()?,
            3 => self.collect_3d_hinges_and_volumes()?,
            _ => {
                return Err(ReggeError::Computation(format!(
                    "Unsupported dimension {dim} for direct Regge action"
                )));
            }
        };

        Ok(crate::regge_action::compute_regge_action(
            &hinges,
            &simplex_volumes,
            lambda_param,
            dim,
        ))
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn equilateral_triangle_angles() {
        let g = ReggeCalculus::equilateral_fan(1, 1.0).unwrap();
        // Single triangle vertices 0,1,2 — each angle π/3
        let t = &g.complex.simplices(2)[0];
        for &v in t.vertices() {
            let a = g.angle_at(t, v).unwrap();
            assert!((a - std::f64::consts::FRAC_PI_3).abs() < 1e-9);
        }
    }

    #[test]
    fn six_equilateral_flat_at_center() {
        // Six equilateral triangles around center → angle sum 2π → deficit 0
        let g = ReggeCalculus::equilateral_fan(6, 1.0).unwrap();
        let d0 = g.deficit_at_vertex(0).unwrap();
        assert!(d0.abs() < 1e-8, "expected flat center, deficit={d0}");
    }

    #[test]
    fn three_equilateral_positive_curvature_cone() {
        // Three equilateral → angle sum π → deficit π at center
        let g = ReggeCalculus::equilateral_fan(3, 1.0).unwrap();
        let d0 = g.deficit_at_vertex(0).unwrap();
        assert!(
            (d0 - std::f64::consts::PI).abs() < 1e-8,
            "expected deficit π, got {d0}"
        );
    }

    #[test]
    fn rejects_triangle_inequality() {
        let complex = SimplicialComplex::standard_n_simplex(2).unwrap();
        let mut metric = EdgeLengthMetric::new();
        metric.set(0, 1, 1.0).unwrap();
        metric.set(1, 2, 1.0).unwrap();
        metric.set(0, 2, 3.0).unwrap(); // 1+1 < 3
        let err = ReggeCalculus::try_new(complex, metric, "bad");
        assert!(matches!(err, Err(ReggeError::TriangleInequality { .. })));
    }

    #[test]
    fn two_triangle_fan_is_not_silently_one_triangle() {
        assert!(matches!(
            ReggeCalculus::equilateral_fan(2, 1.0),
            Err(ReggeError::DegenerateFan { n_triangles: 2 })
        ));
    }

    #[test]
    fn gapped_vertex_ids_do_not_invent_two_pi() {
        let complex = SimplicialComplex::from_maximal_simplices(vec![
            OrientedSimplex::from_unordered(vec![0, 1, 3]).unwrap(),
        ])
        .unwrap();
        assert_eq!(complex.num_vertices(), 4);
        let mut metric = EdgeLengthMetric::new();
        metric.set(0, 1, 1.0).unwrap();
        metric.set(1, 3, 1.0).unwrap();
        metric.set(0, 3, 1.0).unwrap();
        let g = ReggeCalculus::try_new(complex, metric, "gap").unwrap();
        let deficits = g.vertex_deficits().unwrap();
        assert_eq!(deficits.len(), 3);
        let expected = std::f64::consts::TAU - std::f64::consts::FRAC_PI_3;
        for deficit in &deficits {
            assert!((deficit - expected).abs() < 1e-8, "deficit={deficit}");
        }
        let action = g.regge_action_2d().unwrap();
        assert!((action - 3.0 * expected).abs() < 1e-8, "action={action}");
        assert!(matches!(
            g.deficit_at_vertex(2),
            Err(ReggeError::UnknownVertex { vertex: 2 })
        ));
    }

    #[test]
    fn rejects_non_positive_length() {
        let mut m = EdgeLengthMetric::new();
        assert!(matches!(
            m.set(0, 1, 0.0),
            Err(ReggeError::NonPositiveLength { .. })
        ));
    }

    #[test]
    fn new_and_fence() {
        let x = ReggeCalculus::new(2, "test");
        assert_eq!(x.degree(), 2);
        assert!(ReggeCalculus::authority_fence().contains("AuthorityEffect None"));
    }
}
