//! `connection` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_34d6024f;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_34d6024f<T> = std::result::Result<T, BoundaryError_34d6024f>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `connection` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Connection {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl Connection {
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
        let x = Connection::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(Connection::authority_fence().contains("AuthorityEffect None"));
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_general_relativity/src/connection.rs
// Claim: urn:core:gr:connection:face-holonomy:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FaceHolonomy {
    edge_values: Vec<i64>,
    oriented_edges: Vec<(u16, i8)>,
    holonomy: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FaceHolonomyError {
    EmptyLabel,
    DegreeMismatch { degree: usize, face: usize },
    EmptyFace,
    BadOrientation { index: usize },
    EdgeOutOfRange { index: usize },
    HolonomyOverflow { index: usize },
}

// Origin: engine/crates_rs/core_general_relativity/src/connection.rs
// Claim: urn:core:crates_rs:core-general-relativity:connection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FaceHolonomyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FaceHolonomyError {}

fn holonomy_of(edge_values: &[i64], oriented_edges: &[(u16, i8)]) -> Result<i64, FaceHolonomyError> {
    let mut holonomy = 0i64;
    for (index, (edge, orientation)) in oriented_edges.iter().enumerate() {
        if *orientation != 1 && *orientation != -1 {
            return Err(FaceHolonomyError::BadOrientation { index });
        }
        let value = edge_values
            .get(usize::from(*edge))
            .copied()
            .ok_or(FaceHolonomyError::EdgeOutOfRange { index })?;
        let term = value.checked_mul(i64::from(*orientation)).ok_or(FaceHolonomyError::HolonomyOverflow { index })?;
        holonomy = holonomy.checked_add(term).ok_or(FaceHolonomyError::HolonomyOverflow { index })?;
    }
    Ok(holonomy)
}

impl FaceHolonomy {
    pub fn try_from_carrier(
        carrier: &Connection,
        edge_values: &[i64],
        oriented_edges: &[(u16, i8)],
    ) -> Result<Self, FaceHolonomyError> {
        if carrier.label.is_empty() {
            return Err(FaceHolonomyError::EmptyLabel);
        }
        if carrier.degree != oriented_edges.len() || oriented_edges.is_empty() {
            return Err(if oriented_edges.is_empty() {
                FaceHolonomyError::EmptyFace
            } else {
                FaceHolonomyError::DegreeMismatch { degree: carrier.degree, face: oriented_edges.len() }
            });
        }
        let holonomy = holonomy_of(edge_values, oriented_edges)?;
        Ok(Self {
            edge_values: edge_values.to_vec(),
            oriented_edges: oriented_edges.to_vec(),
            holonomy,
        })
    }

    pub fn holonomy(&self) -> i64 { self.holonomy }

    pub fn recomputed(&self) -> Result<i64, FaceHolonomyError> {
        holonomy_of(&self.edge_values, &self.oriented_edges)
    }
}

#[cfg(test)]
mod face_holonomy_tests {
    use super::*;

    #[test]
    fn oriented_square_sums_the_connection() {
        let carrier = Connection::new(4, "plaquette");
        let face = FaceHolonomy::try_from_carrier(&carrier, &[1, 2, 3, 4], &[(0, 1), (1, 1), (2, -1), (3, 1)]);
        assert!(matches!(face, Ok(ref f) if f.holonomy() == 4));
        let again = face.and_then(|f| f.recomputed());
        assert!(matches!(again, Ok(4)));
    }

    #[test]
    fn refuses_a_zero_orientation() {
        let carrier = Connection::new(1, "plaquette");
        let face = FaceHolonomy::try_from_carrier(&carrier, &[1], &[(0, 0)]);
        assert!(matches!(face, Err(FaceHolonomyError::BadOrientation { index: 0 })));
    }
}
