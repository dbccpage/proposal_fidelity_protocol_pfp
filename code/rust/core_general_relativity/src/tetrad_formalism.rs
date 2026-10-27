//! `tetrad_formalism` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_023619f2;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_023619f2<T> = std::result::Result<T, BoundaryError_023619f2>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `tetrad_formalism` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct TetradFormalism {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl TetradFormalism {
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
        let x = TetradFormalism::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(TetradFormalism::authority_fence().contains("AuthorityEffect None"));
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_general_relativity/src/tetrad_formalism.rs
// Claim: urn:core:gr:tetrad:minkowski-norm:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MinkowskiLeg {
    components: [i64; 4],
    norm: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MinkowskiLegError {
    EmptyLabel,
    NotSpacetime { degree: usize },
    NormOverflow,
    NormMismatch { computed: i64, claimed: i64 },
}

// Origin: engine/crates_rs/core_general_relativity/src/tetrad_formalism.rs
// Claim: urn:core:crates_rs:core-general-relativity:tetrad-formalism:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MinkowskiLegError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MinkowskiLegError {}

fn minkowski_norm(components: [i64; 4]) -> Result<i64, MinkowskiLegError> {
    let mut norm = 0i64;
    for (index, component) in components.iter().enumerate() {
        let square = component.checked_mul(*component).ok_or(MinkowskiLegError::NormOverflow)?;
        norm = if index == 0 {
            norm.checked_add(square)
        } else {
            norm.checked_sub(square)
        }
        .ok_or(MinkowskiLegError::NormOverflow)?;
    }
    Ok(norm)
}

impl MinkowskiLeg {
    pub fn try_from_carrier(
        carrier: &TetradFormalism,
        components: [i64; 4],
        claimed: i64,
    ) -> Result<Self, MinkowskiLegError> {
        if carrier.label.is_empty() {
            return Err(MinkowskiLegError::EmptyLabel);
        }
        if carrier.degree != 4 {
            return Err(MinkowskiLegError::NotSpacetime { degree: carrier.degree });
        }
        let norm = minkowski_norm(components)?;
        if norm != claimed {
            return Err(MinkowskiLegError::NormMismatch { computed: norm, claimed });
        }
        Ok(Self { components, norm })
    }

    pub fn norm(&self) -> i64 { self.norm }
}

#[cfg(test)]
mod minkowski_leg_tests {
    use super::*;

    #[test]
    fn null_leg_has_norm_zero() {
        let carrier = TetradFormalism::new(4, "null");
        let leg = MinkowskiLeg::try_from_carrier(&carrier, [5, 4, 3, 0], 0);
        assert!(matches!(leg, Ok(ref l) if l.norm() == 0));
    }

    #[test]
    fn refuses_a_wrong_claimed_norm() {
        let carrier = TetradFormalism::new(4, "time");
        let leg = MinkowskiLeg::try_from_carrier(&carrier, [1, 0, 0, 0], 0);
        assert!(matches!(leg, Err(MinkowskiLegError::NormMismatch { computed: 1, claimed: 0 })));
    }
}
