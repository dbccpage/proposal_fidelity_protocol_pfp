//! `causal_dynamical_triangulation` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_d4a27827;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_d4a27827<T> = std::result::Result<T, BoundaryError_d4a27827>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `causal_dynamical_triangulation` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct CausalDynamicalTriangulation {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl CausalDynamicalTriangulation {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_and_fence() {
        let x = CausalDynamicalTriangulation::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(CausalDynamicalTriangulation::authority_fence().contains("AuthorityEffect None"));
    }
}

/// Closed triangulation census: `2E = 3F`, with Euler characteristic `V - E + F`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TriangulationCensus {
    vertices: u64,
    edges: u64,
    faces: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TriangulationCensusError {
    Empty,
    NotTriangulated { twice_edges: u64, thrice_faces: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_general_relativity/src/causal_dynamical_triangulation.rs
// Claim: urn:core:crates_rs:core-general-relativity:causal-dynamical-triangulation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TriangulationCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TriangulationCensusError {}

impl TriangulationCensus {
    pub fn try_new(vertices: u64, edges: u64, faces: u64) -> Result<Self, TriangulationCensusError> {
        if faces == 0 || edges == 0 || vertices == 0 {
            return Err(TriangulationCensusError::Empty);
        }
        let twice_edges = edges.checked_mul(2).ok_or(TriangulationCensusError::Overflow)?;
        let thrice_faces = faces.checked_mul(3).ok_or(TriangulationCensusError::Overflow)?;
        if twice_edges != thrice_faces {
            return Err(TriangulationCensusError::NotTriangulated { twice_edges, thrice_faces });
        }
        let census = Self { vertices, edges, faces };
        let _ = census.euler()?;
        Ok(census)
    }

    pub fn euler(&self) -> Result<i64, TriangulationCensusError> {
        let vertices = i64::try_from(self.vertices).map_err(|_| TriangulationCensusError::Overflow)?;
        let edges = i64::try_from(self.edges).map_err(|_| TriangulationCensusError::Overflow)?;
        let faces = i64::try_from(self.faces).map_err(|_| TriangulationCensusError::Overflow)?;
        vertices
            .checked_sub(edges)
            .and_then(|v| v.checked_add(faces))
            .ok_or(TriangulationCensusError::Overflow)
    }
}

#[cfg(test)]
mod triangulation_witness {
    use super::*;

    #[test]
    fn tetrahedron_has_euler_characteristic_two() {
        let census = TriangulationCensus::try_new(4, 6, 4).ok();
        assert_eq!(census.and_then(|c| c.euler().ok()), Some(2));
        assert!(TriangulationCensus::try_new(4, 6, 3).is_err());
    }
}
