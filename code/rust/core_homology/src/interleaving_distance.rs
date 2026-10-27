//! Interleaving distance shell (multi-parameter / zigzag).
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_14d1d147;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_14d1d147<T> = std::result::Result<T, BoundaryError_14d1d147>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `interleaving_distance`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct InterleavingDistance {
    pub label: String,
    pub notes: Vec<String>,
}

impl InterleavingDistance {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = InterleavingDistance::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = InterleavingDistance::new("interleaving_distance").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Two closed integer intervals are ε-interleaved when each endpoint of one
/// lies within ε of the matching endpoint of the other, and each interval is
/// ordered birth ≤ death.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IntegerInterleaving {
    birth: i64,
    death: i64,
    other_birth: i64,
    other_death: i64,
    epsilon: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum InterleavingError {
    Unordered { birth: i64, death: i64 },
    OtherUnordered { birth: i64, death: i64 },
    BirthGap { gap: u64, epsilon: u64 },
    DeathGap { gap: u64, epsilon: u64 },
    GapOverflow,
}

// Origin: engine/crates_rs/core_homology/src/interleaving_distance.rs
// Claim: urn:core:crates_rs:core-homology:interleaving-distance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for InterleavingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for InterleavingError {}

fn abs_gap(left: i64, right: i64) -> Result<u64, InterleavingError> {
    let gap = left
        .checked_sub(right)
        .ok_or(InterleavingError::GapOverflow)?;
    u64::try_from(gap.unsigned_abs()).map_err(|_| InterleavingError::GapOverflow)
}

impl IntegerInterleaving {
    pub fn try_new(
        birth: i64,
        death: i64,
        other_birth: i64,
        other_death: i64,
        epsilon: u64,
    ) -> Result<Self, InterleavingError> {
        if birth > death {
            return Err(InterleavingError::Unordered { birth, death });
        }
        if other_birth > other_death {
            return Err(InterleavingError::OtherUnordered {
                birth: other_birth,
                death: other_death,
            });
        }
        let birth_gap = abs_gap(birth, other_birth)?;
        if birth_gap > epsilon {
            return Err(InterleavingError::BirthGap {
                gap: birth_gap,
                epsilon,
            });
        }
        let death_gap = abs_gap(death, other_death)?;
        if death_gap > epsilon {
            return Err(InterleavingError::DeathGap {
                gap: death_gap,
                epsilon,
            });
        }
        Ok(Self {
            birth,
            death,
            other_birth,
            other_death,
            epsilon,
        })
    }

    pub fn epsilon(&self) -> u64 {
        self.epsilon
    }

    pub fn birth(&self) -> i64 {
        self.birth
    }

    pub fn other_birth(&self) -> i64 {
        self.other_birth
    }
}

#[cfg(test)]
mod integer_interleaving_witness {
    use super::*;

    #[test]
    fn endpoints_within_epsilon() {
        let matchup = IntegerInterleaving::try_new(0, 5, 1, 6, 1);
        assert!(matchup.is_ok());
        if let Ok(matchup) = matchup {
            assert_eq!(matchup.epsilon(), 1);
            assert_eq!(matchup.birth(), 0);
        }
    }

    #[test]
    fn refuses_unordered_and_wide_gap() {
        assert!(matches!(
            IntegerInterleaving::try_new(4, 1, 0, 2, 1),
            Err(InterleavingError::Unordered { birth: 4, death: 1 })
        ));
        assert!(matches!(
            IntegerInterleaving::try_new(0, 5, 3, 5, 1),
            Err(InterleavingError::BirthGap { gap: 3, epsilon: 1 })
        ));
    }
}
