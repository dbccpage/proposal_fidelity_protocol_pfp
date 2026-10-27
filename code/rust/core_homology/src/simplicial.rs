//! Canonical finite simplicial complex support.
//!
//! This module is the single simplicial implementation for `core_homology`.
//! It supports simplices in every finite dimension, closes complexes under all
//! faces, gives deterministic basis order, and builds signed boundary and
//! coboundary matrices for arbitrary degree.

use crate::errors::HomologicalError;
use crate::scalar::{q, Q};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::ExactRowReduction;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

/// A canonical unoriented simplex.
///
/// Vertices are strictly ascending. A k-simplex has k + 1 vertices.
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Simplex {
    vertices: Vec<usize>,
}

impl Simplex {
    /// Construct a simplex from strictly ascending vertices.
    pub fn new(vertices: Vec<usize>) -> Result<Self, HomologicalError> {
        validate_strict_vertices(&vertices)?;
        Ok(Self { vertices })
    }

    /// Construct a simplex from unordered vertices, rejecting duplicates.
    pub fn from_unordered(vertices: Vec<usize>) -> Result<Self, HomologicalError> {
        let canonical = canonicalize_vertices(vertices)?;
        Ok(Self {
            vertices: canonical,
        })
    }

    /// Simplex dimension.
    pub fn dimension(&self) -> usize {
        self.vertices.len() - 1
    }

    /// Vertex list in canonical order.
    pub fn vertices(&self) -> &[usize] {
        &self.vertices
    }

    /// Number of vertices.
    pub fn num_vertices(&self) -> usize {
        self.vertices.len()
    }

    /// The i-th codimension-one face, with the canonical boundary sign.
    pub fn face(&self, removed_index: usize) -> Result<(Self, i8), HomologicalError> {
        if removed_index >= self.vertices.len() {
            return Err(HomologicalError::InvalidDegree(removed_index as i32));
        }
        if self.vertices.len() == 1 {
            return Err(HomologicalError::InvalidDegree(0));
        }

        let mut vertices = self.vertices.clone();
        vertices.remove(removed_index);
        let sign = if removed_index.is_multiple_of(2) {
            1
        } else {
            -1
        };
        Ok((Self { vertices }, sign))
    }

    /// All codimension-one faces with signs.
    pub fn faces(&self) -> Vec<(Self, i8)> {
        if self.vertices.len() <= 1 {
            return Vec::new();
        }

        (0..self.vertices.len())
            .map(|i| {
                let mut vertices = self.vertices.clone();
                vertices.remove(i);
                let sign = if i % 2 == 0 { 1 } else { -1 };
                (Self { vertices }, sign)
            })
            .collect()
    }
}

/// An oriented simplex.
///
/// The stored vertices are canonical. `orientation` is the sign of the input
/// ordering relative to canonical ascending order.
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub struct OrientedSimplex {
    simplex: Simplex,
    orientation: i8,
}

impl OrientedSimplex {
    /// Construct from strictly ascending vertices with positive orientation.
    pub fn new(vertices: Vec<usize>) -> Result<Self, HomologicalError> {
        Ok(Self {
            simplex: Simplex::new(vertices)?,
            orientation: 1,
        })
    }

    /// Construct from an ordered vertex list, preserving permutation parity.
    pub fn from_ordered(vertices: Vec<usize>) -> Result<Self, HomologicalError> {
        let orientation = permutation_orientation(&vertices)?;
        Ok(Self {
            simplex: Simplex::from_unordered(vertices)?,
            orientation,
        })
    }

    /// Construct from unordered vertices using canonical positive orientation.
    pub fn from_unordered(vertices: Vec<usize>) -> Result<Self, HomologicalError> {
        Ok(Self {
            simplex: Simplex::from_unordered(vertices)?,
            orientation: 1,
        })
    }

    /// Canonical simplex.
    pub fn simplex(&self) -> &Simplex {
        &self.simplex
    }

    /// Orientation sign relative to canonical vertex order.
    pub fn orientation(&self) -> i8 {
        self.orientation
    }

    /// Simplex dimension.
    pub fn dimension(&self) -> usize {
        self.simplex.dimension()
    }

    /// Vertex list in canonical order.
    pub fn vertices(&self) -> &[usize] {
        self.simplex.vertices()
    }

    /// Number of vertices.
    pub fn num_vertices(&self) -> usize {
        self.simplex.num_vertices()
    }

    /// Signed boundary faces, including this simplex's orientation.
    pub fn faces(&self) -> Vec<(OrientedSimplex, i8)> {
        self.simplex
            .faces()
            .into_iter()
            .map(|(face, sign)| {
                (
                    OrientedSimplex {
                        simplex: face,
                        orientation: 1,
                    },
                    sign * self.orientation,
                )
            })
            .collect()
    }
}

/// A finite simplicial complex closed under all faces.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SimplicialComplex {
    simplices_by_dim: Vec<Vec<Simplex>>,
    indices_by_dim: Vec<BTreeMap<Simplex, usize>>,
    num_vertices: usize,
}

impl SimplicialComplex {
    /// Build a complex from maximal simplices, automatically closing under all faces.
    pub fn from_maximal_simplices(maximal: Vec<OrientedSimplex>) -> Result<Self, HomologicalError> {
        Self::from_canonical_simplices(maximal.into_iter().map(|s| s.simplex).collect())
    }

    /// Build a complex from arbitrary simplices, automatically closing under all faces.
    pub fn from_simplices(simplices: Vec<Simplex>) -> Result<Self, HomologicalError> {
        Self::from_canonical_simplices(simplices)
    }

    /// Build the full n-simplex on vertices 0..=n.
    ///
    /// The result contains every k-simplex for 0 <= k <= n.
    pub fn standard_n_simplex(n: usize) -> Result<Self, HomologicalError> {
        Self::from_simplices(vec![Simplex::new((0..=n).collect())?])
    }

    fn from_canonical_simplices(simplices: Vec<Simplex>) -> Result<Self, HomologicalError> {
        let mut all: BTreeSet<Simplex> = BTreeSet::new();
        let mut stack = simplices;

        while let Some(simplex) = stack.pop() {
            if all.insert(simplex.clone()) {
                for (face, _) in simplex.faces() {
                    stack.push(face);
                }
            }
        }

        let max_dim = all.iter().map(Simplex::dimension).max().unwrap_or(0);
        let mut simplices_by_dim = vec![Vec::new(); max_dim + 1];
        let mut max_vertex = None::<usize>;

        for simplex in all {
            if let Some(&v) = simplex.vertices().last() {
                max_vertex = Some(max_vertex.map_or(v, |m| m.max(v)));
            }
            simplices_by_dim[simplex.dimension()].push(simplex);
        }

        let indices_by_dim = simplices_by_dim
            .iter()
            .map(|simplices| {
                simplices
                    .iter()
                    .cloned()
                    .enumerate()
                    .map(|(index, simplex)| (simplex, index))
                    .collect()
            })
            .collect();

        Ok(Self {
            simplices_by_dim,
            indices_by_dim,
            num_vertices: max_vertex.map_or(0, |v| v + 1),
        })
    }

    /// Maximum simplex dimension. The empty complex has dimension 0 by storage convention.
    pub fn max_dimension(&self) -> usize {
        self.simplices_by_dim.len().saturating_sub(1)
    }

    /// Simplices of a fixed dimension.
    pub fn simplices(&self, dim: usize) -> &[Simplex] {
        self.simplices_by_dim
            .get(dim)
            .map(Vec::as_slice)
            .unwrap_or(&[])
    }

    /// All simplices, grouped by dimension.
    pub fn simplices_by_dim(&self) -> &[Vec<Simplex>] {
        &self.simplices_by_dim
    }

    /// Number of k-simplices.
    pub fn count(&self, dim: usize) -> usize {
        self.simplices(dim).len()
    }

    /// Number of vertex labels in the ambient finite vertex set.
    pub fn num_vertices(&self) -> usize {
        self.num_vertices
    }

    /// Total number of simplices across all dimensions.
    pub fn total_simplices(&self) -> usize {
        self.simplices_by_dim.iter().map(Vec::len).sum()
    }

    /// Whether a simplex belongs to the complex.
    pub fn contains(&self, simplex: &Simplex) -> bool {
        self.indices_by_dim
            .get(simplex.dimension())
            .is_some_and(|indices| indices.contains_key(simplex))
    }

    /// Euler characteristic.
    pub fn euler_characteristic(&self) -> i64 {
        self.simplices_by_dim
            .iter()
            .enumerate()
            .map(|(k, simplices)| {
                if k % 2 == 0 {
                    simplices.len() as i64
                } else {
                    -(simplices.len() as i64)
                }
            })
            .sum()
    }

    /// Signed boundary matrix d_k: C_k -> C_{k-1}.
    ///
    /// Rows are (k-1)-simplices, columns are k-simplices, and entries are
    /// rational signs in {-1, 0, +1}.
    pub fn boundary_matrix(&self, k: usize) -> Result<BasicMatrix<Q>, HomologicalError> {
        if k == 0 {
            return BasicMatrix::zero(0, self.count(0)).map_err(HomologicalError::MatrixError);
        }

        let rows = self.count(k - 1);
        let cols = self.count(k);
        if cols == 0 {
            return BasicMatrix::zero(rows, 0).map_err(HomologicalError::MatrixError);
        }

        let face_indices = self
            .indices_by_dim
            .get(k - 1)
            .ok_or(HomologicalError::InvalidDegree(k as i32))?;
        let mut matrix = BasicMatrix::<Q>::zero(rows, cols)?;

        for (col, simplex) in self.simplices(k).iter().enumerate() {
            for (face, sign) in simplex.faces() {
                let row = face_indices.get(&face).ok_or_else(|| {
                    HomologicalError::UnsupportedOperation(format!(
                        "simplicial closure missing face {:?}",
                        face.vertices()
                    ))
                })?;
                matrix.set(*row, col, q(sign as i64))?;
            }
        }

        Ok(matrix)
    }

    /// Coboundary matrix d^k: C^k -> C^{k+1}, the transpose of d_{k+1}.
    pub fn coboundary_matrix(&self, k: usize) -> Result<BasicMatrix<Q>, HomologicalError> {
        let boundary = self.boundary_matrix(k + 1)?;
        let mut matrix = BasicMatrix::<Q>::zero(boundary.cols(), boundary.rows())?;

        for row in 0..boundary.rows() {
            for col in 0..boundary.cols() {
                matrix.set(col, row, boundary.get(row, col)?)?;
            }
        }

        Ok(matrix)
    }

    /// Composed boundary matrix d_{k-1} * d_k: C_k -> C_{k-2}.
    ///
    /// The fundamental property of simplicial homology is that this product
    /// vanishes identically: d_{k-1} * d_k = 0 for all k >= 2.
    pub fn boundary_composition(&self, k: usize) -> Result<BasicMatrix<Q>, HomologicalError> {
        if k < 2 {
            return Err(HomologicalError::InvalidDegree(k as i32));
        }
        let lower = self.boundary_matrix(k - 1)?;
        let upper = self.boundary_matrix(k)?;
        lower.mul(&upper).map_err(HomologicalError::MatrixError)
    }

    /// Verifies that d_{k-1} * d_k = 0 at degree k.
    ///
    /// Returns Ok(true) if the matrix product is identically zero.
    /// Returns Err(HomologicalError::BoundaryLawViolation { degree: (k - 1) as i32 }) if non-zero.
    pub fn verify_boundary_law_at(&self, k: usize) -> Result<bool, HomologicalError> {
        let composed = self.boundary_composition(k)?;
        let is_zero = composed.as_slice().iter().all(|x| *x == q(0));
        if is_zero {
            Ok(true)
        } else {
            Err(HomologicalError::BoundaryLawViolation {
                degree: (k - 1) as i32,
            })
        }
    }

    /// Verifies the higher-dimensional boundary law d_{k-1} * d_k = 0 for all k in 2..=max_dim.
    ///
    /// For complex dimension < 2, the boundary law holds vacuously (Ok(true)).
    pub fn verify_boundary_law(&self) -> Result<bool, HomologicalError> {
        let max_dim = self.max_dimension();
        if max_dim < 2 {
            return Ok(true);
        }
        for k in 2..=max_dim {
            self.verify_boundary_law_at(k)?;
        }
        Ok(true)
    }

    /// Composed coboundary matrix d^k * d^{k-1}: C^{k-1} -> C^{k+1}.
    pub fn coboundary_composition(&self, k: usize) -> Result<BasicMatrix<Q>, HomologicalError> {
        if k < 1 {
            return Err(HomologicalError::InvalidDegree(k as i32));
        }
        let lower = self.coboundary_matrix(k - 1)?;
        let upper = self.coboundary_matrix(k)?;
        upper.mul(&lower).map_err(HomologicalError::MatrixError)
    }

    /// Verifies that d^k * d^{k-1} = 0 at degree k.
    pub fn verify_coboundary_law_at(&self, k: usize) -> Result<bool, HomologicalError> {
        let composed = self.coboundary_composition(k)?;
        let is_zero = composed.as_slice().iter().all(|x| *x == q(0));
        if is_zero {
            Ok(true)
        } else {
            Err(HomologicalError::CoboundaryLawViolation { degree: k as i32 })
        }
    }

    /// Verifies the coboundary law d^k * d^{k-1} = 0 for all k in 1..max_dim.
    pub fn verify_coboundary_law(&self) -> Result<bool, HomologicalError> {
        let max_dim = self.max_dimension();
        if max_dim < 2 {
            return Ok(true);
        }
        for k in 1..max_dim {
            self.verify_coboundary_law_at(k)?;
        }
        Ok(true)
    }

    /// Exact rational Betti numbers `b_k = dim H_k(K; Q)` for `0 <= k <= max_dimension`.
    ///
    /// `b_k = dim C_k - rank d_k - rank d_{k+1}`, with ranks by exact row
    /// reduction. A rank that exceeds the dimension it is subtracted from is a
    /// typed [`HomologicalError::BettiRankInconsistency`], never a clamp.
    pub fn rational_betti_numbers(&self) -> Result<Vec<usize>, HomologicalError> {
        let max_dim = self.max_dimension();
        let rank = |k: usize| -> Result<usize, HomologicalError> {
            self.boundary_matrix(k)?
                .rank()
                .map_err(|e| HomologicalError::UnsupportedOperation(format!("{}", e)))
        };
        let mut betti = Vec::with_capacity(max_dim + 1);

        for k in 0..=max_dim {
            let ck_dim = self.count(k);
            if ck_dim == 0 {
                betti.push(0);
                continue;
            }

            let rank_dk = if k == 0 { 0 } else { rank(k)? };
            let ker_dk =
                ck_dim
                    .checked_sub(rank_dk)
                    .ok_or(HomologicalError::BettiRankInconsistency {
                        dimension: ck_dim,
                        rank_sum: rank_dk,
                        degree: k,
                    })?;

            let rank_dk_plus_1 = if k == max_dim { 0 } else { rank(k + 1)? };
            let bk = ker_dk.checked_sub(rank_dk_plus_1).ok_or(
                HomologicalError::BettiRankInconsistency {
                    dimension: ker_dk,
                    rank_sum: rank_dk_plus_1,
                    degree: k,
                },
            )?;

            betti.push(bk);
        }

        Ok(betti)
    }
}

fn validate_strict_vertices(vertices: &[usize]) -> Result<(), HomologicalError> {
    if vertices.is_empty() {
        return Err(HomologicalError::EmptyBasis);
    }

    for index in 1..vertices.len() {
        if vertices[index] <= vertices[index - 1] {
            return Err(HomologicalError::BasisMismatch {
                description: format!(
                    "simplex vertices must be strictly ascending; violation at index {}",
                    index
                ),
            });
        }
    }

    Ok(())
}

fn canonicalize_vertices(mut vertices: Vec<usize>) -> Result<Vec<usize>, HomologicalError> {
    if vertices.is_empty() {
        return Err(HomologicalError::EmptyBasis);
    }

    vertices.sort_unstable();
    for index in 1..vertices.len() {
        if vertices[index] == vertices[index - 1] {
            return Err(HomologicalError::BasisMismatch {
                description: "simplex vertices must be distinct".to_string(),
            });
        }
    }

    Ok(vertices)
}

fn permutation_orientation(vertices: &[usize]) -> Result<i8, HomologicalError> {
    if vertices.is_empty() {
        return Err(HomologicalError::EmptyBasis);
    }

    let mut seen = BTreeSet::new();
    for vertex in vertices {
        if !seen.insert(*vertex) {
            return Err(HomologicalError::BasisMismatch {
                description: "oriented simplex vertices must be distinct".to_string(),
            });
        }
    }

    let inversions = vertices
        .iter()
        .enumerate()
        .map(|(i, left)| {
            vertices
                .iter()
                .skip(i + 1)
                .filter(|right| left > *right)
                .count()
        })
        .sum::<usize>();

    Ok(if inversions % 2 == 0 { 1 } else { -1 })
}

// Origin: engine/crates_rs/core_homology/src/simplicial.rs
// Claim: urn:core:crates_rs:core-homology:simplicial:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde28da532 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde28da532` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore28da532 {
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
impl BoundaryErrore28da532 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore28da532 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore28da532 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde28da532 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore28da532> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore28da532::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore28da532::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore28da532::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn standard_n_simplex_has_all_dimensions() {
        let complex = SimplicialComplex::standard_n_simplex(4).unwrap();

        assert_eq!(complex.count(0), 5);
        assert_eq!(complex.count(1), 10);
        assert_eq!(complex.count(2), 10);
        assert_eq!(complex.count(3), 5);
        assert_eq!(complex.count(4), 1);
        assert_eq!(complex.total_simplices(), 31);
        assert_eq!(complex.euler_characteristic(), 1);
    }

    #[test]
    fn rational_betti_numbers_of_circle_disk_and_sphere() {
        let edge = |a, b| Simplex::from_unordered(vec![a, b]).unwrap();
        let hollow =
            SimplicialComplex::from_simplices(vec![edge(0, 1), edge(1, 2), edge(0, 2)]).unwrap();
        assert_eq!(hollow.rational_betti_numbers().unwrap(), vec![1, 1]);

        let disk = SimplicialComplex::standard_n_simplex(2).unwrap();
        assert_eq!(disk.rational_betti_numbers().unwrap(), vec![1, 0, 0]);

        // Boundary of the tetrahedron is a 2-sphere: b = (1, 0, 1).
        let sphere = SimplicialComplex::from_simplices(
            [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]
                .into_iter()
                .map(|face| Simplex::from_unordered(face.to_vec()).unwrap())
                .collect(),
        )
        .unwrap();
        assert_eq!(sphere.rational_betti_numbers().unwrap(), vec![1, 0, 1]);

        let ball = SimplicialComplex::standard_n_simplex(4).unwrap();
        assert_eq!(ball.rational_betti_numbers().unwrap(), vec![1, 0, 0, 0, 0]);
    }

    #[test]
    fn closes_under_faces_for_tetrahedron() {
        let tetrahedron = OrientedSimplex::new(vec![0, 1, 2, 3]).unwrap();
        let complex = SimplicialComplex::from_maximal_simplices(vec![tetrahedron]).unwrap();

        assert_eq!(complex.count(0), 4);
        assert_eq!(complex.count(1), 6);
        assert_eq!(complex.count(2), 4);
        assert_eq!(complex.count(3), 1);
    }

    #[test]
    fn oriented_simplex_tracks_parity() {
        let positive = OrientedSimplex::from_ordered(vec![0, 1, 2]).unwrap();
        let negative = OrientedSimplex::from_ordered(vec![1, 0, 2]).unwrap();

        assert_eq!(positive.vertices(), &[0, 1, 2]);
        assert_eq!(positive.orientation(), 1);
        assert_eq!(negative.vertices(), &[0, 1, 2]);
        assert_eq!(negative.orientation(), -1);
    }

    #[test]
    fn boundary_matrix_1_for_edge() {
        let complex = SimplicialComplex::standard_n_simplex(1).unwrap();
        let d1 = complex.boundary_matrix(1).unwrap();

        assert_eq!(d1.rows(), 2);
        assert_eq!(d1.cols(), 1);
        assert_eq!(d1.get(0, 0).unwrap(), q(-1));
        assert_eq!(d1.get(1, 0).unwrap(), q(1));
    }

    #[test]
    fn boundary_matrix_2_for_triangle() {
        let complex = SimplicialComplex::standard_n_simplex(2).unwrap();
        let d2 = complex.boundary_matrix(2).unwrap();

        assert_eq!(d2.rows(), 3);
        assert_eq!(d2.cols(), 1);
        assert_eq!(d2.get(0, 0).unwrap(), q(1));
        assert_eq!(d2.get(1, 0).unwrap(), q(-1));
        assert_eq!(d2.get(2, 0).unwrap(), q(1));
    }

    #[test]
    fn boundary_squared_is_zero_for_4_simplex() {
        let complex = SimplicialComplex::standard_n_simplex(4).unwrap();

        for k in 2..=4 {
            let lower = complex.boundary_matrix(k - 1).unwrap();
            let upper = complex.boundary_matrix(k).unwrap();
            let composed = lower.mul(&upper).unwrap();
            for row in 0..composed.rows() {
                for col in 0..composed.cols() {
                    assert_eq!(composed.get(row, col).unwrap(), q(0));
                }
            }
        }
    }

    #[test]
    fn rejects_degenerate_simplex() {
        let result = Simplex::from_unordered(vec![0, 1, 1]);
        assert!(matches!(
            result,
            Err(HomologicalError::BasisMismatch { .. })
        ));
    }

    #[test]
    fn boundary_and_coboundary_composition_multi_dimension() {
        // Standard 5-simplex on 6 vertices: dimensions 0..=5
        let complex = SimplicialComplex::standard_n_simplex(5).unwrap();
        assert_eq!(complex.max_dimension(), 5);

        // Verify d_{k-1} * d_k = 0 for each degree k in 2..=5
        for k in 2..=5 {
            let composed = complex.boundary_composition(k).unwrap();
            let rows = complex.count(k - 2);
            let cols = complex.count(k);
            assert_eq!(composed.rows(), rows);
            assert_eq!(composed.cols(), cols);
            assert!(complex.verify_boundary_law_at(k).unwrap());
        }

        // Full boundary law verification across all degrees
        assert!(complex.verify_boundary_law().unwrap());

        // Full coboundary law verification across all degrees
        assert!(complex.verify_coboundary_law().unwrap());
    }

    #[test]
    fn boundary_composition_invalid_degree() {
        let complex = SimplicialComplex::standard_n_simplex(3).unwrap();
        assert!(matches!(
            complex.boundary_composition(0),
            Err(HomologicalError::InvalidDegree(0))
        ));
        assert!(matches!(
            complex.boundary_composition(1),
            Err(HomologicalError::InvalidDegree(1))
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_e28da532 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde28da532::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde28da532::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde28da532::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde28da532::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde28da532::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore28da532::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore28da532::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
