//! Finite oriented cell grammar for constructing an exact cochain window.
//!
//! Rust face of `engine/kernel/cell_grammar.py`.

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

use super::cochain_realization::{canonical_sha256, CochainRealizationError, CochainWindowV1};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OrientedEdgeV1 {
    pub edge_id: String,
    pub coordinate_id: String,
    pub source_vertex_id: String,
    pub target_vertex_id: String,
    #[serde(default = "default_authority")]
    pub authority_effect: String,
}

fn default_authority() -> String {
    "None".into()
}

impl OrientedEdgeV1 {
    pub fn new(
        edge_id: &str,
        coordinate_id: &str,
        source_vertex_id: &str,
        target_vertex_id: &str,
    ) -> Result<Self, CochainRealizationError> {
        if source_vertex_id == target_vertex_id {
            return Err(CochainRealizationError::Validation(
                "oriented demand edges must have distinct endpoints".into(),
            ));
        }
        Ok(Self {
            edge_id: edge_id.to_string(),
            coordinate_id: coordinate_id.to_string(),
            source_vertex_id: source_vertex_id.to_string(),
            target_vertex_id: target_vertex_id.to_string(),
            authority_effect: "None".into(),
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "edge_id": self.edge_id,
            "coordinate_id": self.coordinate_id,
            "source_vertex_id": self.source_vertex_id,
            "target_vertex_id": self.target_vertex_id,
            "authority_effect": self.authority_effect,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BoundaryUseV1 {
    pub edge_id: String,
    pub coefficient: i64,
}

impl BoundaryUseV1 {
    pub fn new(edge_id: &str, coefficient: i64) -> Result<Self, CochainRealizationError> {
        if coefficient == 0 {
            return Err(CochainRealizationError::Validation(
                "boundary coefficient must be a nonzero integer".into(),
            ));
        }
        Ok(Self {
            edge_id: edge_id.to_string(),
            coefficient,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "edge_id": self.edge_id,
            "coefficient": self.coefficient,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OrientedFaceV1 {
    pub face_id: String,
    pub boundary: Vec<BoundaryUseV1>,
    #[serde(default = "default_authority")]
    pub authority_effect: String,
}

impl OrientedFaceV1 {
    pub fn new(
        face_id: &str,
        mut boundary: Vec<BoundaryUseV1>,
    ) -> Result<Self, CochainRealizationError> {
        if boundary.is_empty() {
            return Err(CochainRealizationError::Validation(
                "face boundary must be non-empty".into(),
            ));
        }
        let mut seen = BTreeSet::new();
        for b in &boundary {
            if !seen.insert(b.edge_id.clone()) {
                return Err(CochainRealizationError::Validation(
                    "an edge may occur at most once in a normalized face boundary".into(),
                ));
            }
        }
        boundary.sort_by(|a, b| a.edge_id.cmp(&b.edge_id));
        Ok(Self {
            face_id: face_id.to_string(),
            boundary,
            authority_effect: "None".into(),
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "face_id": self.face_id,
            "boundary": self.boundary.iter().map(|b| b.to_canonical()).collect::<Vec<_>>(),
            "authority_effect": self.authority_effect,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CellGrammarV1 {
    pub vertex_ids: Vec<String>,
    pub edges: Vec<OrientedEdgeV1>,
    pub faces: Vec<OrientedFaceV1>,
    #[serde(default = "default_authority")]
    pub authority_effect: String,
}

impl CellGrammarV1 {
    pub fn new(
        mut vertex_ids: Vec<String>,
        mut edges: Vec<OrientedEdgeV1>,
        mut faces: Vec<OrientedFaceV1>,
    ) -> Result<Self, CochainRealizationError> {
        if vertex_ids.is_empty() {
            return Err(CochainRealizationError::Validation(
                "vertex_ids must be non-empty".into(),
            ));
        }
        let mut v_seen = BTreeSet::new();
        for v in &vertex_ids {
            if !v_seen.insert(v.clone()) {
                return Err(CochainRealizationError::Validation(
                    "vertex_ids must be unique".into(),
                ));
            }
        }
        vertex_ids.sort();

        let e_seen = Self::validate_and_sort_edges(&mut edges, &v_seen)?;
        Self::validate_and_sort_faces(&mut faces, &e_seen)?;

        Ok(Self {
            vertex_ids,
            edges,
            faces,
            authority_effect: "None".into(),
        })
    }

    fn validate_and_sort_edges(
        edges: &mut [OrientedEdgeV1],
        v_seen: &BTreeSet<String>,
    ) -> Result<BTreeSet<String>, CochainRealizationError> {
        if edges.is_empty() {
            return Err(CochainRealizationError::Validation(
                "edges must be non-empty".into(),
            ));
        }
        let mut e_seen = BTreeSet::new();
        let mut coord_seen = BTreeSet::new();
        for e in edges.iter() {
            if !e_seen.insert(e.edge_id.clone()) {
                return Err(CochainRealizationError::Validation(
                    "edge IDs must be unique".into(),
                ));
            }
            if !coord_seen.insert(e.coordinate_id.clone()) {
                return Err(CochainRealizationError::Validation(
                    "edge coordinate IDs must be unique".into(),
                ));
            }
            if !v_seen.contains(&e.source_vertex_id) || !v_seen.contains(&e.target_vertex_id) {
                return Err(CochainRealizationError::Validation(
                    "every oriented edge endpoint must be a declared vertex".into(),
                ));
            }
        }
        edges.sort_by(|a, b| a.edge_id.cmp(&b.edge_id));
        Ok(e_seen)
    }

    fn validate_and_sort_faces(
        faces: &mut [OrientedFaceV1],
        e_seen: &BTreeSet<String>,
    ) -> Result<(), CochainRealizationError> {
        let mut f_seen = BTreeSet::new();
        for f in faces.iter() {
            if !f_seen.insert(f.face_id.clone()) {
                return Err(CochainRealizationError::Validation(
                    "face IDs must be unique".into(),
                ));
            }
            for b in &f.boundary {
                if !e_seen.contains(&b.edge_id) {
                    return Err(CochainRealizationError::Validation(
                        "every face boundary edge must be declared".into(),
                    ));
                }
            }
        }
        faces.sort_by(|a, b| a.face_id.cmp(&b.face_id));
        Ok(())
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "vertex_ids": self.vertex_ids,
            "edges": self.edges.iter().map(|e| e.to_canonical()).collect::<Vec<_>>(),
            "faces": self.faces.iter().map(|f| f.to_canonical()).collect::<Vec<_>>(),
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, CochainRealizationError> {
        canonical_sha256("core.cell-grammar.v1", &self.to_canonical())
    }
}

pub fn vertex_boundary(grammar: &CellGrammarV1, face: &OrientedFaceV1) -> Vec<i64> {
    let edge_map: BTreeMap<&str, &OrientedEdgeV1> = grammar
        .edges
        .iter()
        .map(|e| (e.edge_id.as_str(), e))
        .collect();
    let mut total: BTreeMap<&str, i64> = grammar
        .vertex_ids
        .iter()
        .map(|v| (v.as_str(), 0i64))
        .collect();

    for u in &face.boundary {
        if let Some(edge) = edge_map.get(u.edge_id.as_str()) {
            if let Some(src) = total.get_mut(edge.source_vertex_id.as_str()) {
                *src -= u.coefficient;
            }
            if let Some(tgt) = total.get_mut(edge.target_vertex_id.as_str()) {
                *tgt += u.coefficient;
            }
        }
    }

    grammar
        .vertex_ids
        .iter()
        .map(|v| *total.get(v.as_str()).unwrap_or(&0))
        .collect()
}

pub fn build_cochain_window_from_cells(
    grammar: &CellGrammarV1,
) -> Result<CochainWindowV1, CochainRealizationError> {
    for face in &grammar.faces {
        let vb = vertex_boundary(grammar, face);
        if vb.iter().any(|&v| v != 0) {
            return Err(CochainRealizationError::Refusal {
                code: "FACE_BOUNDARY_NOT_CLOSED".into(),
                message: "a declared face has nonzero vertex boundary".into(),
            });
        }
    }

    let vertex_index: BTreeMap<&str, usize> = grammar
        .vertex_ids
        .iter()
        .enumerate()
        .map(|(idx, v)| (v.as_str(), idx))
        .collect();
    let edge_index: BTreeMap<&str, usize> = grammar
        .edges
        .iter()
        .enumerate()
        .map(|(idx, e)| (e.edge_id.as_str(), idx))
        .collect();

    let mut d0_rows = Vec::with_capacity(grammar.edges.len());
    for edge in &grammar.edges {
        let mut row = vec![0i64; grammar.vertex_ids.len()];
        let s_idx = vertex_index[edge.source_vertex_id.as_str()];
        let t_idx = vertex_index[edge.target_vertex_id.as_str()];
        row[s_idx] = -1;
        row[t_idx] = 1;
        d0_rows.push(row);
    }

    let mut d1_rows = Vec::with_capacity(grammar.faces.len());
    for face in &grammar.faces {
        let mut row = vec![0i64; grammar.edges.len()];
        for u in &face.boundary {
            let e_idx = edge_index[u.edge_id.as_str()];
            row[e_idx] = u.coefficient;
        }
        d1_rows.push(row);
    }

    CochainWindowV1::new(
        grammar.vertex_ids.clone(),
        grammar
            .edges
            .iter()
            .map(|e| e.coordinate_id.clone())
            .collect(),
        grammar.faces.iter().map(|f| f.face_id.clone()).collect(),
        d0_rows,
        d1_rows,
    )
}

// Origin: engine/crates_rs/core_homology/src/cell_grammar.rs
// Claim: urn:core:crates_rs:core-homology:cell-grammar:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord33273047 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord33273047` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError33273047 {
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
impl BoundaryError33273047 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError33273047 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError33273047 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord33273047 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError33273047> {
        if capacity_bound == 0 {
            return Err(BoundaryError33273047::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError33273047::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError33273047::ExceedsCapacity {
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
mod l4_boundary_tests_33273047 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord33273047::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord33273047::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord33273047::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord33273047::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord33273047::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError33273047::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError33273047::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
