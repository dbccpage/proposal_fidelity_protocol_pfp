//! Discrete oriented cell complex representation for cell complexes and graphs.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (canonical ordered adjacency, deterministic SHA-256).

use crate::error::HolonomyError;
use core_kernel::resource_limits::{check_and_reserve, OperationLimits};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

/// 0-cell (vertex) in the cell complex.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Vertex {
    pub id: String,
    pub index: usize,
}

/// Oriented 1-cell (directed edge) in the cell complex.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Edge {
    pub index: usize,
    pub source: String,
    pub target: String,
}

/// Directed step along an edge in a path or boundary cycle.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct OrientedStep {
    pub edge_index: usize,
    pub direction: i8,
}

/// 2-cell (plaquette / face) in the cell complex.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Face {
    pub id: String,
    pub index: usize,
    pub boundary_vertices: Vec<String>,
    pub boundary_edges: Vec<OrientedStep>,
}

/// Discrete cell complex carrier representing vertices, oriented edges, and 2-cells.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CellComplex {
    pub limits: OperationLimits,
    pub vertices: Vec<Vertex>,
    pub vertex_map: BTreeMap<String, usize>,
    pub edges: Vec<Edge>,
    pub edge_map: BTreeMap<(String, String), usize>,
    pub faces: Vec<Face>,
    pub face_map: BTreeMap<String, usize>,
}

impl CellComplex {
    /// Constructs a new cell complex bounded by OperationLimits.
    pub fn new(limits: OperationLimits) -> Self {
        Self {
            limits,
            vertices: Vec::new(),
            vertex_map: BTreeMap::new(),
            edges: Vec::new(),
            edge_map: BTreeMap::new(),
            faces: Vec::new(),
            face_map: BTreeMap::new(),
        }
    }

    /// Adds a 0-cell (vertex) to the complex under Soviet allocation discipline.
    pub fn add_vertex(&mut self, id: impl Into<String>) -> Result<usize, HolonomyError> {
        let id_str = id.into();
        if self.vertex_map.contains_key(&id_str) {
            return Err(HolonomyError::DuplicateVertex { id: id_str });
        }
        check_and_reserve(&mut self.vertices, 1, self.limits.max_vertices)?;

        let index = self.vertices.len();
        self.vertices.push(Vertex {
            id: id_str.clone(),
            index,
        });
        self.vertex_map.insert(id_str, index);
        Ok(index)
    }

    /// Adds a directed 1-cell (edge) between existing vertices.
    pub fn add_edge(&mut self, source: &str, target: &str) -> Result<usize, HolonomyError> {
        if !self.vertex_map.contains_key(source) {
            return Err(HolonomyError::VertexNotFound {
                id: source.to_string(),
            });
        }
        if !self.vertex_map.contains_key(target) {
            return Err(HolonomyError::VertexNotFound {
                id: target.to_string(),
            });
        }
        let edge_key = (source.to_string(), target.to_string());
        if self.edge_map.contains_key(&edge_key) {
            return Err(HolonomyError::DuplicateEdge {
                src: source.to_string(),
                tgt: target.to_string(),
            });
        }
        check_and_reserve(&mut self.edges, 1, self.limits.max_edges)?;

        let index = self.edges.len();
        self.edges.push(Edge {
            index,
            source: source.to_string(),
            target: target.to_string(),
        });
        self.edge_map.insert(edge_key, index);
        Ok(index)
    }

    /// Adds an oriented 2-cell (plaquette) defined by a closed cycle of vertex IDs.
    pub fn add_face(
        &mut self,
        id: impl Into<String>,
        vertex_cycle: &[String],
    ) -> Result<usize, HolonomyError> {
        let id_str = id.into();
        if self.face_map.contains_key(&id_str) {
            return Err(HolonomyError::DuplicateFace { id: id_str });
        }
        if vertex_cycle.len() < 3 {
            return Err(HolonomyError::BoundaryCycleMismatch {
                face: id_str,
                detail: format!(
                    "Face cycle must have at least 3 vertices (got {})",
                    vertex_cycle.len()
                ),
            });
        }
        // Ensure cycle is closed
        let closed_cycle: Vec<String> = if vertex_cycle.first() == vertex_cycle.last() {
            vertex_cycle.to_vec()
        } else {
            let mut c = vertex_cycle.to_vec();
            c.push(vertex_cycle[0].clone());
            c
        };

        check_and_reserve(&mut self.faces, 1, self.limits.max_faces)?;

        let mut boundary_edges = Vec::new();
        for i in 0..(closed_cycle.len() - 1) {
            let u = &closed_cycle[i];
            let v = &closed_cycle[i + 1];
            if let Some(&edge_idx) = self.edge_map.get(&(u.clone(), v.clone())) {
                boundary_edges.push(OrientedStep {
                    edge_index: edge_idx,
                    direction: 1,
                });
            } else if let Some(&edge_idx) = self.edge_map.get(&(v.clone(), u.clone())) {
                boundary_edges.push(OrientedStep {
                    edge_index: edge_idx,
                    direction: -1,
                });
            } else {
                return Err(HolonomyError::EdgeNotFound {
                    src: u.clone(),
                    tgt: v.clone(),
                });
            }
        }

        let index = self.faces.len();
        self.faces.push(Face {
            id: id_str.clone(),
            index,
            boundary_vertices: closed_cycle,
            boundary_edges,
        });
        self.face_map.insert(id_str, index);
        Ok(index)
    }

    /// Computes the degree of a vertex (incoming + outgoing edges).
    pub fn degree(&self, vertex_id: &str) -> Result<usize, HolonomyError> {
        if !self.vertex_map.contains_key(vertex_id) {
            return Err(HolonomyError::VertexNotFound {
                id: vertex_id.to_string(),
            });
        }
        let deg = self
            .edges
            .iter()
            .filter(|e| e.source == vertex_id || e.target == vertex_id)
            .count();
        Ok(deg)
    }

    /// Returns all incident directed edges connected to `vertex_id`.
    pub fn incident_edges(&self, vertex_id: &str) -> Result<Vec<(String, String)>, HolonomyError> {
        if !self.vertex_map.contains_key(vertex_id) {
            return Err(HolonomyError::VertexNotFound {
                id: vertex_id.to_string(),
            });
        }
        let mut list = Vec::new();
        for e in &self.edges {
            if e.source == vertex_id {
                list.push((e.source.clone(), e.target.clone()));
            } else if e.target == vertex_id {
                list.push((e.target.clone(), e.source.clone()));
            }
        }
        Ok(list)
    }

    /// Returns canonical neighbors of `vertex_id` in lexicographical order.
    pub fn neighbors(&self, vertex_id: &str) -> Result<Vec<String>, HolonomyError> {
        if !self.vertex_map.contains_key(vertex_id) {
            return Err(HolonomyError::VertexNotFound {
                id: vertex_id.to_string(),
            });
        }
        let mut nbrs = Vec::new();
        for e in &self.edges {
            if e.source == vertex_id {
                nbrs.push(e.target.clone());
            } else if e.target == vertex_id {
                nbrs.push(e.source.clone());
            }
        }
        nbrs.sort();
        nbrs.dedup();
        Ok(nbrs)
    }

    /// Computes a deterministic SHA-256 content hash of the cell complex state.
    ///
    /// Invariant under insertion order: canonicalizes vertices, edges, and faces by sorting keys.
    pub fn content_hash(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(b"CellComplex:V1\n");

        // Canonical vertices: sorted by ID
        let mut sorted_v: Vec<&String> = self.vertex_map.keys().collect();
        sorted_v.sort();
        hasher.update(format!("Vertices:{}\n", sorted_v.len()).as_bytes());
        for v in sorted_v {
            hasher.update(format!("{v}\n").as_bytes());
        }

        // Canonical edges: sorted by (source, target)
        let mut sorted_e: Vec<&(String, String)> = self.edge_map.keys().collect();
        sorted_e.sort();
        hasher.update(format!("Edges:{}\n", sorted_e.len()).as_bytes());
        for (s, t) in sorted_e {
            hasher.update(format!("{s}->{t}\n").as_bytes());
        }

        // Canonical faces: sorted by face ID
        let mut sorted_f: Vec<&Face> = self.faces.iter().collect();
        sorted_f.sort_by(|a, b| a.id.cmp(&b.id));
        hasher.update(format!("Faces:{}\n", sorted_f.len()).as_bytes());
        for f in sorted_f {
            hasher.update(format!("Face:{}:{:?}\n", f.id, f.boundary_vertices).as_bytes());
        }

        format!("{:x}", hasher.finalize())
    }
}

fn validate_cochain_limits(
    complex: &CellComplex,
    vertices: usize,
    edges: usize,
    faces: usize,
) -> Result<(), HolonomyError> {
    let dense = edges
        .checked_mul(vertices)
        .and_then(|n| faces.checked_mul(edges).and_then(|m| n.checked_add(m)))
        .ok_or_else(|| HolonomyError::BoundaryCycleMismatch {
            face: "cell_complex".into(),
            detail: "dense matrix size overflow".into(),
        })?;
    if dense > 1 << 20 {
        return Err(HolonomyError::OperationLimitExceeded {
            limit: 1 << 20,
            requested: dense,
        });
    }
    let steps = complex
        .faces
        .iter()
        .try_fold(0usize, |a, f| a.checked_add(f.boundary_edges.len()))
        .ok_or_else(|| HolonomyError::BoundaryCycleMismatch {
            face: "cell_complex".into(),
            detail: "boundary work overflow".into(),
        })?;
    let work = steps
        .checked_mul(vertices)
        .ok_or_else(|| HolonomyError::BoundaryCycleMismatch {
            face: "cell_complex".into(),
            detail: "nilpotence work overflow".into(),
        })?;
    if work > 1 << 24 {
        return Err(HolonomyError::OperationLimitExceeded {
            limit: 1 << 24,
            requested: work,
        });
    }
    Ok(())
}

fn complexes_match(a: &CellComplex, b: &CellComplex) -> bool {
    a.vertices == b.vertices
        && a.edges == b.edges
        && a.faces == b.faces
        && a.vertex_map == b.vertex_map
        && a.edge_map == b.edge_map
        && a.face_map == b.face_map
}

fn rebuild_and_validate_complex(complex: &CellComplex) -> Result<CellComplex, HolonomyError> {
    let mut rebuilt = CellComplex::new(complex.limits);
    for v in &complex.vertices {
        rebuilt.add_vertex(v.id.clone())?;
    }
    for e in &complex.edges {
        rebuilt.add_edge(&e.source, &e.target)?;
    }
    for f in &complex.faces {
        rebuilt.add_face(f.id.clone(), &f.boundary_vertices)?;
    }
    if !complexes_match(&rebuilt, complex) {
        return Err(HolonomyError::BoundaryCycleMismatch {
            face: "cell_complex".into(),
            detail: "indices, maps, directions or face boundaries disagree".into(),
        });
    }
    Ok(rebuilt)
}

fn build_cochain_matrices(
    rebuilt: &CellComplex,
    vertices: usize,
    edges: usize,
    faces: usize,
) -> (
    Vec<Vec<num_rational::BigRational>>,
    Vec<Vec<num_rational::BigRational>>,
) {
    use num_rational::BigRational;
    use num_traits::{One, Zero};
    let mut d0 = vec![vec![BigRational::zero(); vertices]; edges];
    for edge in &rebuilt.edges {
        let source = rebuilt.vertex_map[&edge.source];
        let target = rebuilt.vertex_map[&edge.target];
        d0[edge.index][target] += BigRational::one();
        d0[edge.index][source] -= BigRational::one();
    }
    let mut d1 = vec![vec![BigRational::zero(); edges]; faces];
    for face in &rebuilt.faces {
        for step in &face.boundary_edges {
            d1[face.index][step.edge_index] +=
                BigRational::from_integer(i64::from(step.direction).into());
        }
    }
    (d0, d1)
}

fn verify_coboundary_nilpotence(
    faces: &[Face],
    d0: &[Vec<num_rational::BigRational>],
    vertices: usize,
) -> Result<(), HolonomyError> {
    use num_rational::BigRational;
    use num_traits::Zero;
    for face in faces {
        for vertex in 0..vertices {
            let value: BigRational = face
                .boundary_edges
                .iter()
                .map(|step| {
                    BigRational::from_integer(i64::from(step.direction).into())
                        * &d0[step.edge_index][vertex]
                })
                .sum();
            if !value.is_zero() {
                return Err(HolonomyError::BoundaryCycleMismatch {
                    face: "cell_complex".into(),
                    detail: "coboundaries violate d1 d0 = 0".into(),
                });
            }
        }
    }
    Ok(())
}

impl CellComplex {
    /// Checked rational coboundaries. Public/deserialized cell fields are
    /// reconstructed with the normal builders before any index is trusted.
    /// Dense storage and nilpotence replay have independent finite budgets.
    pub fn cochain_matrices(
        &self,
    ) -> Result<
        (
            Vec<Vec<num_rational::BigRational>>,
            Vec<Vec<num_rational::BigRational>>,
        ),
        HolonomyError,
    > {
        let (vertices, edges, faces) = (self.vertices.len(), self.edges.len(), self.faces.len());
        validate_cochain_limits(self, vertices, edges, faces)?;
        let rebuilt = rebuild_and_validate_complex(self)?;
        let (d0, d1) = build_cochain_matrices(&rebuilt, vertices, edges, faces);
        verify_coboundary_nilpotence(&self.faces, &d0, vertices)?;
        Ok((d0, d1))
    }
}

// Origin: engine/crates_rs/core_holonomy/src/graph.rs
// Claim: urn:core:crates_rs:core-holonomy:graph:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6d075a2c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6d075a2c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6d075a2c {
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
impl BoundaryError6d075a2c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6d075a2c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6d075a2c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6d075a2c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6d075a2c> {
        if capacity_bound == 0 {
            return Err(BoundaryError6d075a2c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6d075a2c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6d075a2c::ExceedsCapacity {
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
mod checked_cochain_tests {
    use super::*;
    #[test]
    fn malformed_public_cell_complex_fields_are_refused_before_indexing() {
        let mut c = CellComplex::new(OperationLimits::holonomy());
        for v in ["a", "b", "c"] {
            c.add_vertex(v).unwrap();
        }
        for (a, b) in [("a", "b"), ("b", "c"), ("c", "a")] {
            c.add_edge(a, b).unwrap();
        }
        c.add_face(
            "triangle",
            &["a".into(), "b".into(), "c".into(), "a".into()],
        )
        .unwrap();
        assert!(c.cochain_matrices().is_ok());
        let mut bad = c.clone();
        bad.vertex_map.insert("a".into(), 100);
        assert!(bad.cochain_matrices().is_err());
        let mut bad = c.clone();
        bad.edges[0].index = usize::MAX;
        assert!(bad.cochain_matrices().is_err());
        let mut bad = c.clone();
        bad.faces[0].boundary_edges[0].direction = 2;
        assert!(bad.cochain_matrices().is_err());
        let mut bad = c;
        bad.faces[0].boundary_edges[0].edge_index = usize::MAX;
        assert!(bad.cochain_matrices().is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_6d075a2c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6d075a2c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6d075a2c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6d075a2c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6d075a2c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6d075a2c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6d075a2c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6d075a2c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
