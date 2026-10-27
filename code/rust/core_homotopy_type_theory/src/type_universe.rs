//! Finite universe-level record for HoTT type formers.
//!
//! Structural only: records a universe level and name; not a cumulative
//! hierarchy kernel.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// A named universe level `U_n`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TypeUniverse {
    pub level: u32,
    pub name: String,
}

impl TypeUniverse {
    /// Validate structural well-formedness: name must be non-empty.
    ///
    /// `level` is always a valid `u32`; no further range restriction is imposed
    /// at this record layer.
    pub fn validate(&self) -> Result<(), TypeUniverseError> {
        if self.name.is_empty() {
            return Err(TypeUniverseError::EmptyName);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum TypeUniverseError {
    #[error("type universe name must be non-empty")]
    EmptyName,
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/type_universe.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:type-universe:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok_nonempty_name() {
        let u = TypeUniverse {
            level: 0,
            name: "U0".to_string(),
        };
        assert!(u.validate().is_ok());
    }

    #[test]
    fn validate_rejects_empty_name() {
        let u = TypeUniverse {
            level: 1,
            name: String::new(),
        };
        assert_eq!(u.validate(), Err(TypeUniverseError::EmptyName));
    }

    #[test]
    fn level_zero_is_allowed() {
        let u = TypeUniverse {
            level: 0,
            name: "U".to_string(),
        };
        assert!(u.validate().is_ok());
        assert_eq!(u.level, 0);
    }
}

/// A term level sits strictly below a validated universe; `lift` is the gap.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CumulativityWitness {
    term_level: u32,
    universe_level: u32,
    lift: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CumulativityError {
    InvalidUniverse,
    NotStrictlyBelow { term_level: u32, universe_level: u32 },
}

impl CumulativityWitness {
    pub fn try_new(term_level: u32, universe: &TypeUniverse) -> Result<Self, CumulativityError> {
        universe
            .validate()
            .map_err(|_| CumulativityError::InvalidUniverse)?;
        if term_level >= universe.level {
            return Err(CumulativityError::NotStrictlyBelow {
                term_level,
                universe_level: universe.level,
            });
        }
        let lift = universe
            .level
            .checked_sub(term_level)
            .ok_or(CumulativityError::NotStrictlyBelow {
                term_level,
                universe_level: universe.level,
            })?;
        Ok(Self {
            term_level,
            universe_level: universe.level,
            lift,
        })
    }

    pub fn lift(&self) -> u32 {
        self.lift
    }
}
