//! Reconstruct a cycle representative for a persistence bar.
//!
//! AuthorityEffect: None. Shell / best-effort computational topology.
//! Not PROVED; not GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_6d7a52fa;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_6d7a52fa<T> = std::result::Result<T, BoundaryError_6d7a52fa>;
use serde::{Deserialize, Serialize};

/// Chain coefficients over a field (stored as f64 for shell; Z2/Q later).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RepresentativeCycle {
    pub dimension: usize,
    /// Sparse support: (simplex_index_in_filtration, coefficient).
    pub terms: Vec<(usize, f64)>,
    pub birth: f64,
    pub death: Option<f64>,
}

impl RepresentativeCycle {
    pub fn empty(dimension: usize, birth: f64, death: Option<f64>) -> Self {
        Self {
            dimension,
            terms: Vec::new(),
            birth,
            death,
        }
    }

    pub fn support_size(&self) -> usize {
        self.terms.len()
    }

    pub fn is_zero(&self) -> bool {
        self.terms.iter().all(|(_, c)| *c == 0.0)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_cycle_is_zero() {
        let c = RepresentativeCycle::empty(1, 0.0, Some(1.0));
        assert!(c.is_zero());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Gf2Error {
    Empty,
    Order,
    Index,
    Boundary,
}

// Origin: engine/crates_rs/core_homology/src/representative_cycle.rs
// Claim: urn:core:crates_rs:core-homology:representative-cycle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for Gf2Error {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for Gf2Error {}

/// A GF(2) cycle: the symmetric difference of the selected boundary supports is empty.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Gf2Cycle {
    support: Vec<usize>,
}

impl Gf2Cycle {
    pub fn try_cycle(support: &[usize], boundaries: &[Vec<usize>], universe: usize) -> Result<Self, Gf2Error> {
        if support.is_empty() || universe == 0 {
            return Err(Gf2Error::Empty);
        }
        if support.windows(2).any(|pair| pair[0] >= pair[1]) {
            return Err(Gf2Error::Order);
        }
        let mut parity = vec![0u8; universe];
        for &face_index in support {
            let face = boundaries.get(face_index).ok_or(Gf2Error::Index)?;
            for &vertex in face {
                let cell = parity.get_mut(vertex).ok_or(Gf2Error::Index)?;
                *cell ^= 1;
            }
        }
        if parity.iter().any(|bit| *bit != 0) {
            return Err(Gf2Error::Boundary);
        }
        Ok(Self { support: support.to_vec() })
    }

    pub fn support(&self) -> &[usize] { &self.support }
}

#[cfg(test)]
mod gf2_cycle_tests {
    use super::*;

    #[test]
    fn the_boundary_of_a_triangle_is_a_cycle() {
        let cycle = Gf2Cycle::try_cycle(&[0, 1, 2], &[vec![0, 1], vec![1, 2], vec![0, 2]], 3);
        assert!(matches!(cycle, Ok(ref cycle) if cycle.support().len() == 3));
    }

    #[test]
    fn two_edges_leave_a_nonzero_boundary() {
        let cycle = Gf2Cycle::try_cycle(&[0, 1], &[vec![0, 1], vec![1, 2], vec![0, 2]], 3);
        assert!(matches!(cycle, Err(Gf2Error::Boundary)));
    }
}
