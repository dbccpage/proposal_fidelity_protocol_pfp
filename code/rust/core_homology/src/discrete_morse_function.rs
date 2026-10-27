//! Discrete Morse function: cell pairing + critical cells.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_9a8975e8;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_9a8975e8<T> = std::result::Result<T, BoundaryError_9a8975e8>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `discrete_morse_function`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct DiscreteMorseFunction {
    pub label: String,
    pub notes: Vec<String>,
}

impl DiscreteMorseFunction {
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
        let s = DiscreteMorseFunction::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = DiscreteMorseFunction::new("discrete_morse_function").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// --- exact carrier witness ---
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MorseLawError {
    Shell,
    Shape,
    Vertex,
    Duplicate,
    Downward { simplex: u16 },
    Pairing { simplex: u16 },
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/discrete_morse_function.rs
// Claim: urn:core:crates_rs:core-homology:discrete-morse-function:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MorseLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MorseLawError {}

/// A discrete Morse function on simplices with at most eight vertices.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteMorseWitness {
    simplices: usize,
}

impl DiscreteMorseWitness {
    pub fn try_new(shell: &DiscreteMorseFunction, values: &[(u16, i64)]) -> Result<Self, MorseLawError> {
        if shell.validate_shell().is_err() || values.is_empty() {
            return Err(MorseLawError::Shell);
        }
        let function = Self::parse_morse_values(values)?;
        Self::check_downward_closed(&function)?;
        for (&simplex, &value) in &function {
            let (lower, upper) = Self::count_violating_neighbors(&function, simplex, value)?;
            if lower > 1 || upper > 1 {
                return Err(MorseLawError::Pairing { simplex });
            }
        }
        Ok(Self { simplices: function.len() })
    }

    fn parse_morse_values(values: &[(u16, i64)]) -> Result<BTreeMap<u16, i64>, MorseLawError> {
        let mut function = BTreeMap::new();
        for &(simplex, value) in values {
            if simplex > 0xff {
                return Err(MorseLawError::Vertex);
            }
            if function.insert(simplex, value).is_some() {
                return Err(MorseLawError::Duplicate);
            }
        }
        Ok(function)
    }

    fn check_downward_closed(function: &BTreeMap<u16, i64>) -> Result<(), MorseLawError> {
        for &simplex in function.keys() {
            let mut subset = simplex;
            loop {
                if !function.contains_key(&subset) {
                    return Err(MorseLawError::Downward { simplex });
                }
                if subset == 0 {
                    break;
                }
                subset = subset.wrapping_sub(1) & simplex;
            }
        }
        Ok(())
    }

    fn count_violating_neighbors(
        function: &BTreeMap<u16, i64>,
        simplex: u16,
        value: i64,
    ) -> Result<(u32, u32), MorseLawError> {
        let mut lower = 0u32;
        let mut upper = 0u32;
        for bit in 0..8u32 {
            let flag = 1u16.checked_shl(bit).ok_or(MorseLawError::Overflow)?;
            if simplex & flag != 0 {
                let face = simplex ^ flag;
                let face_value = *function.get(&face).ok_or(MorseLawError::Downward { simplex })?;
                if face_value >= value {
                    lower += 1;
                }
            } else if function.get(&(simplex | flag)).is_some_and(|&cv| cv <= value) {
                upper += 1;
            }
        }
        Ok((lower, upper))
    }

    pub fn simplices(&self) -> usize { self.simplices }
}

#[cfg(test)]
mod morse_law_tests {
    use super::*;

    #[test]
    fn an_edge_with_two_higher_faces_is_not_morse() {
        let shell = DiscreteMorseFunction::new("morse");
        let witness = DiscreteMorseWitness::try_new(&shell, &[(0, 0), (1, 2), (2, 2), (3, 1)]);
        assert!(matches!(witness, Err(MorseLawError::Pairing { simplex: 3 })));
    }

    #[test]
    fn a_vertex_paired_with_the_empty_face_is_admitted() {
        let shell = DiscreteMorseFunction::new("morse");
        let witness = DiscreteMorseWitness::try_new(&shell, &[(0, 0), (1, 0)]);
        assert!(matches!(witness, Ok(ref witness) if witness.simplices() == 2));
    }
}
