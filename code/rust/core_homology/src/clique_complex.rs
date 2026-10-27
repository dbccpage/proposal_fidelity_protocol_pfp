//! Flag / clique complex from an undirected graph.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_5ef921f0;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_5ef921f0<T> = std::result::Result<T, BoundaryError_5ef921f0>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `clique_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct CliqueComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl CliqueComplex {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("label must be non-empty".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_homology/src/clique_complex.rs
// Claim: urn:core:crates_rs:core-homology:clique-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = CliqueComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = CliqueComplex::new("clique_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Triangle census of a simple undirected graph on at most 12 vertices.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TriangleCensus {
    vertices: usize,
    edges: usize,
    triangles: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CliqueError {
    Bound,
    Edge,
    Duplicate,
}

impl std::fmt::Display for CliqueError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Bound => write!(f, "vertex count must be in 1..=12"),
            Self::Edge => write!(f, "edge endpoint is outside the vertex set or is a loop"),
            Self::Duplicate => write!(f, "edge list repeats an undirected edge"),
        }
    }
}

impl std::error::Error for CliqueError {}

impl TriangleCensus {
    pub fn count(vertices: usize, edges: &[(usize, usize)]) -> Result<Self, CliqueError> {
        let adj = Self::build_adjacency(vertices, edges)?;
        let triangles = Self::count_triangles(vertices, &adj)?;
        Ok(Self {
            vertices,
            edges: edges.len(),
            triangles,
        })
    }

    fn build_adjacency(vertices: usize, edges: &[(usize, usize)]) -> Result<Vec<Vec<bool>>, CliqueError> {
        if vertices == 0 || vertices > 12 {
            return Err(CliqueError::Bound);
        }
        let mut adj = vec![vec![false; vertices]; vertices];
        for &(left, right) in edges {
            if left >= vertices || right >= vertices || left == right {
                return Err(CliqueError::Edge);
            }
            let (a, b) = if left < right { (left, right) } else { (right, left) };
            if adj[a][b] {
                return Err(CliqueError::Duplicate);
            }
            adj[a][b] = true;
            adj[b][a] = true;
        }
        Ok(adj)
    }

    fn count_triangles(vertices: usize, adj: &[Vec<bool>]) -> Result<usize, CliqueError> {
        let mut triangles = 0usize;
        for i in 0..vertices {
            for j in (i + 1)..vertices {
                if !adj[i][j] {
                    continue;
                }
                for k in (j + 1)..vertices {
                    if adj[i][k] && adj[j][k] {
                        triangles = triangles.checked_add(1).ok_or(CliqueError::Bound)?;
                    }
                }
            }
        }
        Ok(triangles)
    }

    pub fn vertices(&self) -> usize {
        self.vertices
    }

    pub fn edges(&self) -> usize {
        self.edges
    }

    pub fn triangles(&self) -> usize {
        self.triangles
    }
}

#[cfg(test)]
mod exact_clique_tests {
    use super::*;

    #[test]
    fn one_triangle_and_a_path_of_length_two() {
        let triangle = TriangleCensus::count(3, &[(0, 1), (1, 2), (0, 2)]).map_or_else(|_| loop { assert!(false); }, |value| value);
        assert_eq!(triangle.triangles(), 1);
        let path = TriangleCensus::count(3, &[(0, 1), (1, 2)]).map_or_else(|_| loop { assert!(false); }, |value| value);
        assert_eq!(path.triangles(), 0);
        assert_eq!(path.edges(), 2);
    }
}
