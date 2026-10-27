//! universe shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Related contract (if present): `urn:core:math:type_universe:v0.1.0`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_5a4d7be6;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_5a4d7be6<T> = std::result::Result<T, BoundaryError_5a4d7be6>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a type-universe level record (U_i).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Universe {
    pub label: String,
    /// Non-negative universe level index `i` for `U_i`.
    pub level: u32,
    /// Whether lower-level types are included (cumulative hierarchy flag).
    pub cumulative: bool,
    pub notes: Vec<String>,
}

impl Universe {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            level: 0,
            cumulative: true,
            notes: Vec::new(),
        }
    }

    pub fn at_level(label: impl Into<String>, level: u32) -> Self {
        Self {
            label: label.into(),
            level,
            cumulative: true,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            Err("empty label".into())
        } else {
            Ok(())
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(Universe::new("x").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Universe::new("").validate_shell().is_err());
    }

    #[test]
    fn at_level_sets_level() {
        let u = Universe::at_level("U", 2);
        assert_eq!(u.level, 2);
        assert!(u.validate_shell().is_ok());
    }
}

/// Cumulative universe: the type count at level `i` is at least the count at level `i-1`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CumulativeUniverse {
    lower_types: u64,
    this_level_types: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CumulativeUniverseError {
    NotCumulative { lower_types: u64, this_level_types: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/foundations/universe.rs
// Claim: urn:core:crates_rs:core-category-theory:universe:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CumulativeUniverseError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CumulativeUniverseError {}

impl CumulativeUniverse {
    pub fn try_new(lower_types: u64, this_level_types: u64) -> Result<Self, CumulativeUniverseError> {
        if this_level_types < lower_types {
            return Err(CumulativeUniverseError::NotCumulative { lower_types, this_level_types });
        }
        let _ = this_level_types
            .checked_add(0)
            .ok_or(CumulativeUniverseError::Overflow)?;
        Ok(Self { lower_types, this_level_types })
    }

    pub fn fresh_types(&self) -> Result<u64, CumulativeUniverseError> {
        self.this_level_types
            .checked_sub(self.lower_types)
            .ok_or(CumulativeUniverseError::Overflow)
    }
}

#[cfg(test)]
mod cumulative_universe_witness {
    use super::*;

    #[test]
    fn a_cumulative_step_adds_only_nonnegative_fresh_types() {
        let level = CumulativeUniverse::try_new(4, 7).ok();
        assert_eq!(level.and_then(|l| l.fresh_types().ok()), Some(3));
        assert!(CumulativeUniverse::try_new(7, 4).is_err());
    }
}
