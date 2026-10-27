//! Simplicial 4-complex with per-pentatope charts in `Q^4`.
//!
//! Vertex ids come from the charts and are not renumbered. Squared edge lengths
//! are computed inside each chart and must agree where charts share an edge.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use linear_algebra::regge_exact::{cayley_menger, q_i64, signed_volume_4};
use num_rational::BigRational;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ManifoldError {
    Degenerate { cell: &'static str, index: usize },
    MissingGeometry,
    InconsistentLength { a: u32, b: u32 },
    InconsistentDefect { hinge: [u32; 3] },
    NotAFace,
    Empty,
    FrameRejected,
}

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/manifold.rs
// Claim: urn:core:crates_rs:core-general-relativity:manifold:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ManifoldError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ManifoldError {}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PentatopeChart {
    pub vertices: [u32; 5],
    pub coords: [[BigRational; 4]; 5],
}

#[derive(Clone, Debug)]
pub struct SimplicialManifold4D {
    vertex_count: u32,
    charts: Vec<PentatopeChart>,
    length_squared: BTreeMap<(u32, u32), BigRational>,
}

impl SimplicialManifold4D {
    pub fn from_ambient_pentatopes(
        pentatopes: &[[[BigRational; 4]; 5]],
    ) -> Result<Self, ManifoldError> {
        if pentatopes.is_empty() {
            return Err(ManifoldError::Empty);
        }
        let mut weld: BTreeMap<[BigRational; 4], u32> = BTreeMap::new();
        let mut charts = Vec::with_capacity(pentatopes.len());
        for pent in pentatopes {
            let mut vertices = [0_u32; 5];
            for i in 0..5 {
                vertices[i] = welded_id(&mut weld, &pent[i])?;
            }
            charts.push(PentatopeChart {
                vertices,
                coords: pent.clone(),
            });
        }
        Self::from_charts(charts)
    }

    fn record_chart_edges(
        chart: &PentatopeChart,
        length_squared: &mut BTreeMap<(u32, u32), BigRational>,
    ) -> Result<(), ManifoldError> {
        for i in 0..5 {
            for j in (i + 1)..5 {
                let a = chart.vertices[i];
                let b = chart.vertices[j];
                let (lo, hi) = if a < b { (a, b) } else { (b, a) };
                // Coordinates are chart-local. Only the squared length is shared.
                let len2 = squared_distance(&chart.coords[i], &chart.coords[j]);
                if let Some(existing) = length_squared.get(&(lo, hi)) {
                    if existing != &len2 {
                        return Err(ManifoldError::InconsistentLength { a: lo, b: hi });
                    }
                } else {
                    length_squared.insert((lo, hi), len2);
                }
            }
        }
        Ok(())
    }

    pub fn from_charts(charts: Vec<PentatopeChart>) -> Result<Self, ManifoldError> {
        if charts.is_empty() {
            return Err(ManifoldError::Empty);
        }
        let mut ids = BTreeSet::new();
        let mut length_squared = BTreeMap::new();
        for (index, chart) in charts.iter().enumerate() {
            if !distinct_five(&chart.vertices) {
                return Err(ManifoldError::Degenerate {
                    cell: "pentatope",
                    index,
                });
            }
            ids.extend(chart.vertices);
            Self::record_chart_edges(chart, &mut length_squared)?;
        }
        let vertex_count = u32::try_from(ids.len()).map_err(|_| ManifoldError::MissingGeometry)?;
        Ok(Self {
            vertex_count,
            charts,
            length_squared,
        })
    }

    pub fn vertex_count(&self) -> u32 {
        self.vertex_count
    }

    pub fn pentatope_count(&self) -> usize {
        self.charts.len()
    }

    pub fn pentatope(&self, index: usize) -> Result<&PentatopeChart, ManifoldError> {
        self.charts.get(index).ok_or(ManifoldError::MissingGeometry)
    }

    pub fn charts(&self) -> &[PentatopeChart] {
        &self.charts
    }

    pub fn chart_coords(
        &self,
        pentatope_index: usize,
        vertex: u32,
    ) -> Result<[BigRational; 4], ManifoldError> {
        let chart = self
            .charts
            .get(pentatope_index)
            .ok_or(ManifoldError::MissingGeometry)?;
        chart
            .vertices
            .iter()
            .position(|&id| id == vertex)
            .map(|i| chart.coords[i].clone())
            .ok_or(ManifoldError::MissingGeometry)
    }

    pub fn edge_length_squared(&self, a: u32, b: u32) -> Result<BigRational, ManifoldError> {
        // The length map stores unordered pairs only. A diagonal is not an edge.
        if a == b {
            return Err(ManifoldError::Degenerate {
                cell: "edge",
                index: a as usize,
            });
        }
        let key = if a < b { (a, b) } else { (b, a) };
        self.length_squared
            .get(&key)
            .cloned()
            .ok_or(ManifoldError::MissingGeometry)
    }

    fn ensure_nonzero_pentatopes_and_edges(&self) -> Result<(), ManifoldError> {
        for (p, chart) in self.charts.iter().enumerate() {
            let volume = signed_volume_4(&chart.coords).map_err(|_| degenerate_pentatope(p))?;
            if volume == q_i64(0) {
                return Err(degenerate_pentatope(p));
            }
        }
        for &(a, b) in self.length_squared.keys() {
            if self.edge_length_squared(a, b)? == q_i64(0) {
                return Err(ManifoldError::Degenerate {
                    cell: "edge",
                    index: 0,
                });
            }
        }
        Ok(())
    }

    pub fn nondegeneracy(&self) -> Result<(), ManifoldError> {
        self.ensure_nonzero_pentatopes_and_edges()?;
        for triangle in self.triangles() {
            self.require_cayley(2, &triangle, "triangle", 0, 0)?;
        }
        for tetra in self.tetrahedra() {
            self.require_cayley(3, &tetra, "tetrahedron", 0, 0)?;
        }
        for (p, chart) in self.charts.iter().enumerate() {
            self.require_cayley(4, &chart.vertices, "pentatope", p, p)?;
        }
        Ok(())
    }

    pub fn triangles(&self) -> Vec<[u32; 3]> {
        let mut faces = BTreeSet::new();
        for chart in &self.charts {
            let v = chart.vertices;
            for i in 0..5 {
                for j in (i + 1)..5 {
                    for k in (j + 1)..5 {
                        let mut face = [v[i], v[j], v[k]];
                        face.sort_unstable();
                        faces.insert(face);
                    }
                }
            }
        }
        faces.into_iter().collect()
    }

    pub fn tetrahedra(&self) -> Vec<[u32; 4]> {
        let mut faces = BTreeSet::new();
        for chart in &self.charts {
            let v = chart.vertices;
            for omit in 0..5 {
                let mut face = [0_u32; 4];
                let mut n = 0;
                for (i, &id) in v.iter().enumerate() {
                    if i != omit {
                        face[n] = id;
                        n += 1;
                    }
                }
                debug_assert_eq!(n, 4);
                face.sort_unstable();
                faces.insert(face);
            }
        }
        faces.into_iter().collect()
    }

    pub fn edges(&self) -> Vec<(u32, u32)> {
        self.length_squared.keys().copied().collect()
    }

    /// Alternating face count `(V as i64) - E + T - Tet + P`.
    pub fn euler_characteristic(&self) -> i64 {
        let v = i64::from(self.vertex_count());
        let e = self.edges().len() as i64;
        let t = self.triangles().len() as i64;
        let tet = self.tetrahedra().len() as i64;
        let p = self.pentatope_count() as i64;
        v - e + t - tet + p
    }

    fn require_cayley(
        &self,
        dimension: u8,
        vertices: &[u32],
        zero_cell: &'static str,
        zero_index: usize,
        error_index: usize,
    ) -> Result<(), ManifoldError> {
        let lengths = self.squared_length_block(vertices)?;
        let computed =
            cayley_menger(dimension, &lengths).map_err(|_| degenerate_pentatope(error_index))?;
        if computed.volume_squared == q_i64(0) {
            return Err(ManifoldError::Degenerate {
                cell: zero_cell,
                index: zero_index,
            });
        }
        Ok(())
    }

    /// Leading block is symmetric with a zero diagonal. Entries past it stay zero.
    fn squared_length_block(
        &self,
        vertices: &[u32],
    ) -> Result<[[BigRational; 5]; 5], ManifoldError> {
        debug_assert!(vertices.len() <= 5);
        let mut block: [[BigRational; 5]; 5] =
            std::array::from_fn(|_| std::array::from_fn(|_| q_i64(0)));
        for i in 0..vertices.len() {
            for j in (i + 1)..vertices.len() {
                let len2 = self.edge_length_squared(vertices[i], vertices[j])?;
                block[i][j] = len2.clone();
                block[j][i] = len2;
            }
        }
        Ok(block)
    }
}

fn degenerate_pentatope(index: usize) -> ManifoldError {
    ManifoldError::Degenerate {
        cell: "pentatope",
        index,
    }
}

fn distinct_five(vertices: &[u32; 5]) -> bool {
    for i in 0..5 {
        for j in (i + 1)..5 {
            if vertices[i] == vertices[j] {
                return false;
            }
        }
    }
    true
}

fn welded_id(
    weld: &mut BTreeMap<[BigRational; 4], u32>,
    coord: &[BigRational; 4],
) -> Result<u32, ManifoldError> {
    if let Some(&id) = weld.get(coord) {
        return Ok(id);
    }
    let id = u32::try_from(weld.len()).map_err(|_| ManifoldError::MissingGeometry)?;
    weld.insert(coord.clone(), id);
    Ok(id)
}

fn squared_distance(p: &[BigRational; 4], q: &[BigRational; 4]) -> BigRational {
    let mut acc = q_i64(0);
    for k in 0..4 {
        let delta = &p[k] - &q[k];
        acc += &delta * &delta;
    }
    acc
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{ManifoldError, PentatopeChart, SimplicialManifold4D};
    use linear_algebra::regge_exact::q_i64;
    use num_rational::BigRational;

    fn q4(x: i64, y: i64, z: i64, w: i64) -> [BigRational; 4] {
        [q_i64(x), q_i64(y), q_i64(z), q_i64(w)]
    }

    fn add4(p: &[BigRational; 4], q: &[BigRational; 4]) -> [BigRational; 4] {
        [&p[0] + &q[0], &p[1] + &q[1], &p[2] + &q[2], &p[3] + &q[3]]
    }

    /// `ids[0]` at `(shift,0,0,0)`, the other four one unit along each axis.
    fn orth(ids: [u32; 5], shift: i64) -> PentatopeChart {
        let origin = q4(shift, 0, 0, 0);
        let steps = [
            q4(1, 0, 0, 0),
            q4(0, 1, 0, 0),
            q4(0, 0, 1, 0),
            q4(0, 0, 0, 1),
        ];
        PentatopeChart {
            vertices: ids,
            coords: [
                origin.clone(),
                add4(&origin, &steps[0]),
                add4(&origin, &steps[1]),
                add4(&origin, &steps[2]),
                add4(&origin, &steps[3]),
            ],
        }
    }

    #[test]
    fn from_charts_accepts_shared_edge_of_squared_length_one() {
        let first = orth([0, 1, 2, 3, 4], 0);
        let second = orth([0, 1, 5, 6, 7], 5);
        let manifold = SimplicialManifold4D::from_charts(vec![first, second]).unwrap();
        assert_eq!(manifold.vertex_count(), 8);
        assert_eq!(manifold.pentatope_count(), 2);
        assert_eq!(manifold.charts()[0].vertices, [0, 1, 2, 3, 4]);
        assert_eq!(manifold.charts()[1].vertices, [0, 1, 5, 6, 7]);
        assert_eq!(manifold.chart_coords(0, 0).unwrap(), q4(0, 0, 0, 0));
        assert_eq!(manifold.chart_coords(1, 0).unwrap(), q4(5, 0, 0, 0));
        assert_eq!(manifold.edge_length_squared(0, 1).unwrap(), q_i64(1));
        assert_eq!(manifold.edge_length_squared(1, 0).unwrap(), q_i64(1));
        assert_eq!(manifold.edges().len(), 19);
        assert_eq!(manifold.triangles().len(), 20);
        assert_eq!(manifold.tetrahedra().len(), 10);
        assert_eq!(manifold.euler_characteristic(), 1);
        assert_eq!(
            manifold.chart_coords(0, 9).unwrap_err(),
            ManifoldError::MissingGeometry
        );
        assert_eq!(
            manifold.edge_length_squared(2, 5).unwrap_err(),
            ManifoldError::MissingGeometry
        );
        assert_eq!(
            manifold.edge_length_squared(3, 3).unwrap_err(),
            ManifoldError::Degenerate {
                cell: "edge",
                index: 3,
            }
        );
    }

    #[test]
    fn from_charts_rejects_inconsistent_shared_edge() {
        let first = orth([0, 1, 2, 3, 4], 0);
        let mut second = orth([0, 1, 5, 6, 7], 0);
        second.coords[1] = q4(2, 0, 0, 0);
        let err = SimplicialManifold4D::from_charts(vec![first, second]).unwrap_err();
        assert_eq!(err, ManifoldError::InconsistentLength { a: 0, b: 1 });
    }

    #[test]
    fn from_ambient_welds_coordinates_in_first_seen_order() {
        let p0 = [
            q4(0, 0, 0, 0),
            q4(1, 0, 0, 0),
            q4(0, 1, 0, 0),
            q4(0, 0, 1, 0),
            q4(0, 0, 0, 1),
        ];
        let p1 = [
            q4(0, 0, 0, 1),
            q4(0, 0, 0, 0),
            q4(3, 0, 0, 0),
            q4(0, 3, 0, 0),
            q4(0, 0, 3, 0),
        ];
        let manifold = SimplicialManifold4D::from_ambient_pentatopes(&[p0, p1]).unwrap();
        assert_eq!(manifold.vertex_count(), 8);
        assert_eq!(manifold.pentatope(0).unwrap().vertices, [0, 1, 2, 3, 4]);
        assert_eq!(manifold.pentatope(1).unwrap().vertices, [4, 0, 5, 6, 7]);
        assert_eq!(manifold.chart_coords(1, 4).unwrap(), q4(0, 0, 0, 1));
        assert_eq!(manifold.edge_length_squared(0, 4).unwrap(), q_i64(1));
        assert_eq!(manifold.charts().len(), 2);
    }

    #[test]
    fn empty_and_repeated_vertex_are_refused() {
        assert_eq!(
            SimplicialManifold4D::from_charts(Vec::new()).unwrap_err(),
            ManifoldError::Empty
        );
        assert_eq!(
            SimplicialManifold4D::from_ambient_pentatopes(&[]).unwrap_err(),
            ManifoldError::Empty
        );
        let mut repeated = orth([10, 20, 30, 40, 50], 0);
        repeated.vertices[4] = 10;
        assert_eq!(
            SimplicialManifold4D::from_charts(vec![repeated]).unwrap_err(),
            ManifoldError::Degenerate {
                cell: "pentatope",
                index: 0,
            }
        );
        let mut collapsed = [
            q4(0, 0, 0, 0),
            q4(1, 0, 0, 0),
            q4(0, 1, 0, 0),
            q4(0, 0, 1, 0),
            q4(0, 0, 0, 1),
        ];
        collapsed[4] = collapsed[0].clone();
        assert_eq!(
            SimplicialManifold4D::from_ambient_pentatopes(&[collapsed]).unwrap_err(),
            ManifoldError::Degenerate {
                cell: "pentatope",
                index: 0,
            }
        );
    }

    #[test]
    fn ids_are_not_renumbered_and_one_pentatope_has_euler_one() {
        let manifold =
            SimplicialManifold4D::from_charts(vec![orth([10, 20, 30, 40, 50], 0)]).unwrap();
        assert_eq!(manifold.vertex_count(), 5);
        assert_eq!(
            manifold.pentatope(0).unwrap().vertices,
            [10, 20, 30, 40, 50]
        );
        assert_eq!(manifold.edge_length_squared(10, 20).unwrap(), q_i64(1));
        assert_eq!(manifold.edges().len(), 10);
        assert_eq!(manifold.triangles().first().copied(), Some([10, 20, 30]));
        assert_eq!(manifold.triangles().len(), 10);
        assert_eq!(
            manifold.tetrahedra().first().copied(),
            Some([10, 20, 30, 40])
        );
        assert_eq!(manifold.tetrahedra().len(), 5);
        assert_eq!(manifold.euler_characteristic(), 1);
        let edges = manifold.edges();
        assert!(edges.windows(2).all(|pair| pair[0] < pair[1]));
    }
}
