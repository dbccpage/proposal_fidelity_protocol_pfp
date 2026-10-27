// AuthorityEffect: None.

//! Binary pattern carriers: `same`/`diff` edge patterns on a declared finite graph.
//!
//! A carrier is a finite graph without self-loops. A pattern gives each edge a
//! value in `F_2` (`0 = same`, `1 = diff`); an assignment gives each vertex a
//! value in `F_2`, and its coboundary is the pattern `(d0 f)(u, v) = f(u) + f(v)`.
//! An assignment family is the declared, finite set of exhibited repairs.
//! Patterns and assignments are bit masks: bit `e` is edge `e`, bit `v` is
//! vertex `v`. Computed exactly:
//!
//! - the image `{d0 f : f in F}` of a family, and whether a pattern is in it;
//! - the family-indexed binary residual `min_(f in F) |h + d0 f|` with unit
//!   edge weights. This is the source's binary `Phi1`, a Hamming distance over
//!   `F_2`; it is not `core_functional`'s rational quotient mass;
//! - even subgraphs `z` (every vertex has even degree in `z`). For those,
//!   `<d0 f, z> = 0` for every assignment, so a pattern with `<h, z> = 1` is
//!   removed by no family at all: this is the parity certificate;
//! - whether the full family leaves some pattern unremoved, and, separately, a
//!   union-find cycle test;
//! - every simple graph on a given number of labelled vertices.
//!
//! Parallel edges are allowed by [`PatternCarrier::new`] and reported by
//! [`PatternCarrier::is_simple`]; whether a carrier may have them is a
//! declaration. Refused: self-loops, endpoints out of range, more than 16
//! vertices or edges, patterns or assignments with bits beyond the carrier,
//! and residuals over an empty family.

use std::collections::BTreeSet;

/// Bit-mask width limit for vertices and for edges.
pub const MAX_BITS: usize = 16;

/// Refusals for pattern carriers.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PatternError {
    #[error("edge {edge} is a self-loop")]
    SelfLoop { edge: usize },
    #[error("edge {edge} names vertex {vertex}, but the carrier has {vertex_count} vertices")]
    VertexOutOfRange {
        edge: usize,
        vertex: usize,
        vertex_count: usize,
    },
    #[error("at most {MAX_BITS} vertices and {MAX_BITS} edges are supported")]
    TooLarge,
    #[error("pattern {pattern:#b} has bits beyond the {edges} edges")]
    PatternOutOfRange { pattern: u32, edges: usize },
    #[error("assignment {assignment:#b} has bits beyond the {vertices} vertices")]
    AssignmentOutOfRange { assignment: u32, vertices: usize },
    #[error("the residual over an empty family is undefined")]
    EmptyFamily,
}

/// A declared finite graph carrying `F_2` patterns on its edges.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PatternCarrier {
    vertex_count: usize,
    edges: Vec<(usize, usize)>,
}

impl PatternCarrier {
    pub fn new(vertex_count: usize, edges: Vec<(usize, usize)>) -> Result<Self, PatternError> {
        if vertex_count > MAX_BITS || edges.len() > MAX_BITS {
            return Err(PatternError::TooLarge);
        }
        for (edge, &(u, v)) in edges.iter().enumerate() {
            for vertex in [u, v] {
                if vertex >= vertex_count {
                    return Err(PatternError::VertexOutOfRange {
                        edge,
                        vertex,
                        vertex_count,
                    });
                }
            }
            if u == v {
                return Err(PatternError::SelfLoop { edge });
            }
        }
        Ok(Self {
            vertex_count,
            edges,
        })
    }

    pub fn vertex_count(&self) -> usize {
        self.vertex_count
    }

    pub fn edges(&self) -> &[(usize, usize)] {
        &self.edges
    }

    /// No two edges join the same pair of vertices.
    pub fn is_simple(&self) -> bool {
        let pairs: BTreeSet<(usize, usize)> = self
            .edges
            .iter()
            .map(|&(u, v)| (u.min(v), u.max(v)))
            .collect();
        pairs.len() == self.edges.len()
    }

    /// `2^|E|`, the size of the pattern alphabet on the carrier.
    pub fn pattern_count(&self) -> usize {
        1 << self.edges.len()
    }

    fn check_assignment(&self, f: u32) -> Result<(), PatternError> {
        if f >> self.vertex_count != 0 {
            return Err(PatternError::AssignmentOutOfRange {
                assignment: f,
                vertices: self.vertex_count,
            });
        }
        Ok(())
    }

    fn check_pattern(&self, h: u32) -> Result<(), PatternError> {
        if h >> self.edges.len() != 0 {
            return Err(PatternError::PatternOutOfRange {
                pattern: h,
                edges: self.edges.len(),
            });
        }
        Ok(())
    }

    /// `(d0 f)(u, v) = f(u) + f(v)` on every edge.
    pub fn coboundary(&self, f: u32) -> Result<u32, PatternError> {
        self.check_assignment(f)?;
        Ok(self.edges.iter().enumerate().fold(0, |acc, (e, &(u, v))| {
            acc | ((((f >> u) ^ (f >> v)) & 1) << e)
        }))
    }

    /// All `2^|V|` assignments.
    pub fn full_family(&self) -> Vec<u32> {
        (0..(1u32 << self.vertex_count)).collect()
    }

    /// `{d0 f : f in family}`.
    pub fn image(&self, family: &[u32]) -> Result<BTreeSet<u32>, PatternError> {
        family.iter().map(|&f| self.coboundary(f)).collect()
    }

    /// `h = d0 f` for some `f` in the family.
    pub fn is_removable(&self, h: u32, family: &[u32]) -> Result<bool, PatternError> {
        self.check_pattern(h)?;
        Ok(self.image(family)?.contains(&h))
    }

    /// `min_(f in family) |h + d0 f|`, the number of edges left unexplained.
    pub fn binary_residual(&self, h: u32, family: &[u32]) -> Result<u32, PatternError> {
        self.check_pattern(h)?;
        self.image(family)?
            .iter()
            .map(|r| (h ^ r).count_ones())
            .min()
            .ok_or(PatternError::EmptyFamily)
    }

    /// Some pattern is not removed even by the full family.
    pub fn has_unremovable_pattern(&self) -> bool {
        self.has_cycle()
    }

    /// `z` is nonzero and every vertex has even degree in the edges of `z`.
    pub fn is_even_subgraph(&self, z: u32) -> Result<bool, PatternError> {
        self.check_pattern(z)?;
        if z == 0 {
            return Ok(false);
        }
        let mut degree_parity = 0u32;
        for (e, &(u, v)) in self.edges.iter().enumerate() {
            if (z >> e) & 1 == 1 {
                degree_parity ^= (1 << u) ^ (1 << v);
            }
        }
        Ok(degree_parity == 0)
    }

    /// Some edge closes a cycle, found by union-find without any pattern.
    pub fn has_cycle(&self) -> bool {
        fn root(parent: &mut [usize], mut x: usize) -> usize {
            while parent[x] != x {
                parent[x] = parent[parent[x]];
                x = parent[x];
            }
            x
        }
        let mut parent: Vec<usize> = (0..self.vertex_count).collect();
        for &(u, v) in &self.edges {
            let (ru, rv) = (root(&mut parent, u), root(&mut parent, v));
            if ru == rv {
                return true;
            }
            parent[ru] = rv;
        }
        false
    }
}

/// `<h, z> = |h and z| mod 2`.
pub fn pattern_pairing(h: u32, z: u32) -> u32 {
    (h & z).count_ones() % 2
}

/// Every simple graph on `vertex_count` labelled vertices, one per edge subset
/// of the complete graph (edges `(i, j)`, `i < j`, in lexicographic order).
pub fn simple_graphs(vertex_count: usize) -> Result<Vec<PatternCarrier>, PatternError> {
    if vertex_count > MAX_BITS {
        return Err(PatternError::TooLarge);
    }
    let pairs: Vec<(usize, usize)> = (0..vertex_count)
        .flat_map(|i| ((i + 1)..vertex_count).map(move |j| (i, j)))
        .collect();
    if pairs.len() > MAX_BITS {
        return Err(PatternError::TooLarge);
    }
    (0..(1u32 << pairs.len()))
        .map(|mask| {
            let edges = pairs
                .iter()
                .enumerate()
                .filter(|(e, _)| (mask >> e) & 1 == 1)
                .map(|(_, &pair)| pair)
                .collect();
            PatternCarrier::new(vertex_count, edges)
        })
        .collect()
}

use core_number_theory::gf2::{F2Error, F2Matrix, F2Vector};
/// Graph cohomology without the legacy mask-width restriction. All elimination,
/// solution and dual-certificate computations use the shared GF(2) foundation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GraphCohomologyF2 {
    vertices: usize,
    edges: Vec<(usize, usize)>,
    d0: F2Matrix,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GraphF2Error {
    #[error("graph endpoint is outside the carrier or an edge is a self-loop")]
    Endpoint,
    #[error("graph storage or enumeration exceeds its finite budget")]
    Budget,
    #[error(transparent)]
    Matrix(#[from] F2Error),
}
impl GraphCohomologyF2 {
    pub fn new(vertices: usize, edges: Vec<(usize, usize)>) -> Result<Self, GraphF2Error> {
        Self::validate_graph_f2_inputs(vertices, &edges)?;
        let mut d0 = F2Matrix::zeros(edges.len(), vertices)?;
        for (edge, &(u, v)) in edges.iter().enumerate() {
            d0.set(edge, u, true)?;
            d0.set(edge, v, true)?;
        }
        Ok(Self {
            vertices,
            edges,
            d0,
        })
    }

    fn validate_graph_f2_inputs(vertices: usize, edges: &[(usize, usize)]) -> Result<(), GraphF2Error> {
        if vertices > 4096
            || edges.len() > 4096
            || vertices
                .checked_mul(edges.len())
                .is_none_or(|n| n > 1 << 22)
        {
            return Err(GraphF2Error::Budget);
        }
        if edges
            .iter()
            .any(|&(u, v)| u >= vertices || v >= vertices || u == v)
        {
            return Err(GraphF2Error::Endpoint);
        }
        Ok(())
    }
    pub fn vertex_count(&self) -> usize {
        self.vertices
    }
    pub fn edges(&self) -> &[(usize, usize)] {
        &self.edges
    }
    pub fn coboundary(&self, assignment: &F2Vector) -> Result<F2Vector, GraphF2Error> {
        Ok(self.d0.mul_vec(assignment)?)
    }
    pub fn cycle_space_basis(&self) -> Vec<F2Vector> {
        self.d0.left_nullspace()
    }
    pub fn cycle_rank(&self) -> usize {
        self.edges.len() - self.d0.rank()
    }
    pub fn solve_coboundary(&self, pattern: &F2Vector) -> Result<Option<F2Vector>, GraphF2Error> {
        Ok(self.d0.solve(pattern)?.map(|s| s.particular().clone()))
    }
    /// An even subgraph paired to one with pattern, precisely when the pattern
    /// is not a full-family coboundary. The caller can replay d0^T z=0 and h.z=1.
    pub fn parity_certificate(&self, pattern: &F2Vector) -> Result<Option<F2Vector>, GraphF2Error> {
        if pattern.len() != self.edges.len() {
            return Err(F2Error::LengthMismatch {
                expected: self.edges.len(),
                actual: pattern.len(),
            }
            .into());
        }
        for z in self.cycle_space_basis() {
            if z.dot(pattern)? {
                return Ok(Some(z));
            }
        }
        Ok(None)
    }
    pub fn minimum_hamming_residual(
        &self,
        pattern: &F2Vector,
        budget: usize,
    ) -> Result<usize, GraphF2Error> {
        if pattern.len() != self.edges.len() {
            return Err(F2Error::LengthMismatch {
                expected: self.edges.len(),
                actual: pattern.len(),
            }
            .into());
        }
        let basis = self.d0.column_space_basis();
        let exponent = u32::try_from(basis.len()).map_err(|_| GraphF2Error::Budget)?;
        let count = 1usize.checked_shl(exponent).ok_or(GraphF2Error::Budget)?;
        if budget > 1 << 20 || count > budget {
            return Err(GraphF2Error::Budget);
        }
        let mut best = pattern.weight();
        for mask in 0..count {
            let mut residual = pattern.clone();
            for (i, b) in basis.iter().enumerate() {
                if mask & (1usize << i) != 0 {
                    residual.add_assign(b)?;
                }
            }
            best = best.min(residual.weight());
        }
        Ok(best)
    }
}
// Origin: engine/crates_rs/core_homology/src/graph_f2.rs
// Claim: urn:core:crates_rs:core-homology:graph-f2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod graph_f2_tests {
    use super::*;
    #[test]
    fn graphs_beyond_mask_width_have_replayable_cycle_obstructions() {
        let edges = (0..40).map(|v| (v, (v + 1) % 40)).collect();
        let graph = GraphCohomologyF2::new(40, edges).unwrap();
        let pattern = F2Vector::unit(40, 0).unwrap();
        assert_eq!(graph.cycle_rank(), 1);
        assert!(graph.solve_coboundary(&pattern).unwrap().is_none());
        let z = graph.parity_certificate(&pattern).unwrap().unwrap();
        assert!(z.dot(&pattern).unwrap());
        assert!(graph.d0.transpose().mul_vec(&z).unwrap().is_zero());
        let assignment = F2Vector::unit(40, 0).unwrap();
        let trivial = graph.coboundary(&assignment).unwrap();
        assert!(graph.solve_coboundary(&trivial).unwrap().is_some());
        assert!(graph.parity_certificate(&trivial).unwrap().is_none());
        assert!(graph.minimum_hamming_residual(&pattern, 1 << 20).is_err());
    }
}
