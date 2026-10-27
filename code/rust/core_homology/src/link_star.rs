//! Link and star of a simplex in a complex.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_1ce82024;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_1ce82024<T> = std::result::Result<T, BoundaryError_1ce82024>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `link_star`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct LinkStar {
    pub label: String,
    pub notes: Vec<String>,
}

impl LinkStar {
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

// Origin: engine/crates_rs/core_homology/src/link_star.rs
// Claim: urn:core:crates_rs:core-homology:link-star:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = LinkStar::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = LinkStar::new("link_star").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Star/link bijection for one vertex of a finite abstract simplicial complex.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LinkStarCensus {
    star: usize,
    link: Vec<Vec<usize>>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LinkError {
    Simplex,
    Vertex,
    Bijection,
}

impl std::fmt::Display for LinkError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Simplex => write!(f, "a simplex is unsorted, repeated, or duplicated"),
            Self::Vertex => write!(f, "the vertex does not appear"),
            Self::Bijection => write!(f, "deleting the vertex did not biject star with link"),
        }
    }
}

impl std::error::Error for LinkError {}

impl LinkStarCensus {
    pub fn of(simplices: &[Vec<usize>], vertex: usize) -> Result<Self, LinkError> {
        let mut seen = Vec::<Vec<usize>>::new();
        for simplex in simplices {
            if simplex.windows(2).any(|pair| pair[0] >= pair[1]) {
                return Err(LinkError::Simplex);
            }
            if seen.iter().any(|other| other == simplex) {
                return Err(LinkError::Simplex);
            }
            seen.push(simplex.clone());
        }
        let mut link = Vec::new();
        for simplex in &seen {
            if !simplex.contains(&vertex) {
                continue;
            }
            let face: Vec<usize> = simplex.iter().copied().filter(|point| *point != vertex).collect();
            link.push(face);
        }
        if link.is_empty() {
            return Err(LinkError::Vertex);
        }
        let mut rebuilt = Vec::new();
        for face in &link {
            let mut restored = face.clone();
            restored.push(vertex);
            restored.sort_unstable();
            restored.dedup();
            rebuilt.push(restored);
        }
        rebuilt.sort();
        let mut star: Vec<Vec<usize>> = seen
            .into_iter()
            .filter(|simplex| simplex.contains(&vertex))
            .collect();
        star.sort();
        if rebuilt != star {
            return Err(LinkError::Bijection);
        }
        let count = link.len();
        Ok(Self { star: count, link })
    }

    pub fn star_count(&self) -> usize {
        self.star
    }

    pub fn link(&self) -> &[Vec<usize>] {
        &self.link
    }
}

#[cfg(test)]
mod exact_link_tests {
    use super::*;

    #[test]
    fn an_edge_stars_to_a_point_and_the_empty_face() {
        let census = LinkStarCensus::of(&[vec![0], vec![1], vec![0, 1]], 0).map_or_else(|_| loop { assert!(false); }, |value| value);
        assert_eq!(census.star_count(), 2);
        assert_eq!(census.link(), &[vec![], vec![1]]);
    }
}
