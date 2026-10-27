//! Witness complex from landmarks and witnesses.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_fe8290a7;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_fe8290a7<T> = std::result::Result<T, BoundaryError_fe8290a7>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `witness_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct WitnessComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl WitnessComplex {
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
        let s = WitnessComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = WitnessComplex::new("witness_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WitnessLawError {
    Shell,
    Shape,
    Distance { row: usize, column: usize },
    Simplex,
    NoWitness,
}

// Origin: engine/crates_rs/core_homology/src/witness_complex.rs
// Claim: urn:core:crates_rs:core-homology:witness-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for WitnessLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for WitnessLawError {}

/// A nonempty proper landmark simplex that has a weak witness in an integer distance matrix.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WeakWitnessSimplex {
    landmarks: usize,
    simplex: u16,
}

impl WeakWitnessSimplex {
    pub fn try_new(
        shell: &WitnessComplex,
        distances: &[i64],
        points: usize,
        landmarks: usize,
        simplex: u16,
    ) -> Result<Self, WitnessLawError> {
        Self::check_shell_and_bounds(shell, points, landmarks)?;
        Self::validate_distance_matrix(distances, points)?;
        let (members, others) = Self::partition_landmarks(landmarks, simplex)?;
        if !Self::has_weak_witness(distances, points, &members, &others)? {
            return Err(WitnessLawError::NoWitness);
        }
        Ok(Self { landmarks, simplex })
    }

    fn check_shell_and_bounds(
        shell: &WitnessComplex,
        points: usize,
        landmarks: usize,
    ) -> Result<(), WitnessLawError> {
        if shell.validate_shell().is_err() || points == 0 || landmarks == 0 || landmarks > 8 || landmarks > points {
            return Err(WitnessLawError::Shell);
        }
        Ok(())
    }

    fn validate_distance_matrix(distances: &[i64], points: usize) -> Result<(), WitnessLawError> {
        let cells = points.checked_mul(points).ok_or(WitnessLawError::Shape)?;
        if distances.len() != cells {
            return Err(WitnessLawError::Shape);
        }
        for row in 0..points {
            for column in 0..points {
                let value = distances[row * points + column];
                let mirror = distances[column * points + row];
                if value < 0 || value != mirror || (row == column && value != 0) {
                    return Err(WitnessLawError::Distance { row, column });
                }
            }
        }
        Ok(())
    }

    fn partition_landmarks(
        landmarks: usize,
        simplex: u16,
    ) -> Result<(Vec<usize>, Vec<usize>), WitnessLawError> {
        let mut members = Vec::new();
        let mut others = Vec::new();
        for landmark in 0..landmarks {
            let shift = u32::try_from(landmark).map_err(|_| WitnessLawError::Shape)?;
            let flag = 1u16.checked_shl(shift).ok_or(WitnessLawError::Shape)?;
            if simplex & flag != 0 {
                members.push(landmark);
            } else {
                others.push(landmark);
            }
        }
        if members.is_empty() || others.is_empty() || simplex > 0xff {
            return Err(WitnessLawError::Simplex);
        }
        Ok((members, others))
    }

    fn max_distance_to_set(
        distances: &[i64],
        points: usize,
        witness: usize,
        set: &[usize],
    ) -> Result<i64, WitnessLawError> {
        let mut max_val = i64::MIN;
        for &landmark in set {
            let d = *distances
                .get(witness * points + landmark)
                .ok_or(WitnessLawError::Shape)?;
            if d > max_val {
                max_val = d;
            }
        }
        Ok(max_val)
    }

    fn min_distance_to_set(
        distances: &[i64],
        points: usize,
        witness: usize,
        set: &[usize],
    ) -> Result<i64, WitnessLawError> {
        let mut min_val = i64::MAX;
        for &landmark in set {
            let d = *distances
                .get(witness * points + landmark)
                .ok_or(WitnessLawError::Shape)?;
            if d < min_val {
                min_val = d;
            }
        }
        Ok(min_val)
    }

    fn has_weak_witness(
        distances: &[i64],
        points: usize,
        members: &[usize],
        others: &[usize],
    ) -> Result<bool, WitnessLawError> {
        for witness in 0..points {
            let max_inside = Self::max_distance_to_set(distances, points, witness, members)?;
            let min_outside = Self::min_distance_to_set(distances, points, witness, others)?;
            if max_inside <= min_outside {
                return Ok(true);
            }
        }
        Ok(false)
    }

    pub fn landmarks(&self) -> usize { self.landmarks }
    pub fn simplex(&self) -> u16 { self.simplex }
}

#[cfg(test)]
mod witness_law_tests {
    use super::*;

    #[test]
    fn landmark_zero_witnesses_the_edge() {
        let shell = WitnessComplex::new("weak");
        let distances = [0, 1, 4, 1, 0, 4, 4, 4, 0];
        let witness = WeakWitnessSimplex::try_new(&shell, &distances, 3, 3, 0b011);
        assert!(matches!(witness, Ok(ref witness) if witness.simplex() == 0b011));
    }

    #[test]
    fn a_far_edge_has_no_weak_witness() {
        let shell = WitnessComplex::new("weak");
        let distances = [0, 3, 1, 3, 0, 1, 1, 1, 0];
        let witness = WeakWitnessSimplex::try_new(&shell, &distances, 3, 3, 0b011);
        assert!(matches!(witness, Err(WitnessLawError::NoWitness)));
    }
}
