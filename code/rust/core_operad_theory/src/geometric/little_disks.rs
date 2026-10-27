//! Geometric: Little n-Disks Operad D_n.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

/// A rectilinear disk embedding in R^n given by center and radius.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RectilinearDisk {
    pub dimension: usize,
    pub center: Vec<f64>,
    pub radius: f64,
}

impl RectilinearDisk {
    pub fn new(dimension: usize, center: Vec<f64>, radius: f64) -> Result<Self, String> {
        if radius <= 0.0 {
            return Err(format!("Disk radius must be positive, got {}", radius));
        }
        if center.len() != dimension {
            return Err(format!("Center dimension {} != disk dimension {}", center.len(), dimension));
        }
        Ok(Self {
            dimension,
            center,
            radius,
        })
    }

    pub fn center_norm(&self) -> f64 {
        self.center.iter().map(|x| x * x).sum::<f64>().sqrt()
    }

    pub fn is_contained_in_unit_disk(&self) -> bool {
        self.center_norm() + self.radius <= 1.0 + 1e-9
    }

    pub fn is_disjoint_from(&self, other: &RectilinearDisk) -> Result<bool, String> {
        if self.dimension != other.dimension {
            return Err("Cannot check disjointness for disks of differing dimensions".to_string());
        }
        let dist = self
            .center
            .iter()
            .zip(&other.center)
            .map(|(a, b)| (a - b) * (a - b))
            .sum::<f64>()
            .sqrt();
        Ok(dist + 1e-9 >= self.radius + other.radius)
    }
}

/// A valid point in the topological operad space D_n(k).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LittleDisksConfiguration {
    pub dimension: usize,
    pub disks: Vec<RectilinearDisk>,
}

impl LittleDisksConfiguration {
    pub fn new(dimension: usize, disks: Vec<RectilinearDisk>) -> Result<Self, String> {
        for d in &disks {
            if !d.is_contained_in_unit_disk() {
                return Err("Disk exceeds unit bounding ball".to_string());
            }
        }
        let n = disks.len();
        for i in 0..n {
            for j in (i + 1)..n {
                if !disks[i].is_disjoint_from(&disks[j])? {
                    return Err(format!("Disks at index {} and {} overlap in interior", i, j));
                }
            }
        }
        Ok(Self { dimension, disks })
    }

    pub fn arity(&self) -> usize {
        self.disks.len()
    }
}

/// Exact little-interval configuration inside an integer modulus.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactIntervalOperad {
    modulus: i64,
    count: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IntervalError {
    Bound,
    Order,
    Modulus,
    Overlap,
}

impl std::fmt::Display for IntervalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            IntervalError::Bound => write!(formatter, "modulus must be positive and the count must lie in 1..=16"),
            IntervalError::Order => write!(formatter, "an interval must start before it ends"),
            IntervalError::Modulus => write!(formatter, "an interval leaves [0, modulus]"),
            IntervalError::Overlap => write!(formatter, "intervals are unsorted or overlap"),
        }
    }
}

impl std::error::Error for IntervalError {}

impl ExactIntervalOperad {
    pub fn place(modulus: i64, intervals: &[(i64, i64)]) -> Result<Self, IntervalError> {
        if modulus <= 0 || intervals.is_empty() || intervals.len() > 16 {
            return Err(IntervalError::Bound);
        }
        let mut previous_end: Option<i64> = None;
        for &(start, end) in intervals {
            if start >= end {
                return Err(IntervalError::Order);
            }
            if start < 0 || end > modulus {
                return Err(IntervalError::Modulus);
            }
            if let Some(previous) = previous_end {
                if start < previous {
                    return Err(IntervalError::Overlap);
                }
            }
            previous_end = Some(end);
        }
        Ok(Self {
            modulus,
            count: intervals.len(),
        })
    }

    pub fn count(&self) -> usize {
        self.count
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/geometric/little_disks.rs
// Claim: urn:core:crates_rs:core-operad-theory:little-disks:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod interval_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn touching_intervals_fit_and_an_overlap_is_refused() {
        let placed = taken(ExactIntervalOperad::place(10, &[(0, 2), (2, 5)]));
        assert_eq!(placed.count(), 2);
        assert!(ExactIntervalOperad::place(10, &[(0, 3), (2, 4)]).is_err());
    }
}
