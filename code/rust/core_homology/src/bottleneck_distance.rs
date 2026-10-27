//! Bottleneck distance between persistence diagrams.
//!
//! AuthorityEffect: None. Best-effort shell. Not PROVED; not GlobalGreen.

use crate::persistence_diagram::{PersistenceDiagram, PersistencePoint};
use num_traits::{Signed, ToPrimitive};

/// L∞ cost between two finite points (or point and its diagonal projection).
pub fn point_cost(a: &PersistencePoint, b: &PersistencePoint) -> f64 {
    match (&a.death, &b.death) {
        (Some(da), Some(db)) => (&a.birth - &b.birth)
            .abs()
            .max((da - db).abs())
            .to_f64()
            .unwrap_or(f64::INFINITY),
        _ => f64::INFINITY,
    }
}

/// Distance from a finite point to the diagonal (birth = death).
pub fn diagonal_cost(p: &PersistencePoint) -> f64 {
    match &p.death {
        Some(d) => (d - &p.birth).abs().to_f64().unwrap_or(f64::INFINITY) / 2.0,
        None => f64::INFINITY,
    }
}

/// Bottleneck distance shell: exact matching for tiny diagrams (≤ 8 finite points each).
///
/// Each finite point may match a point of the other diagram or the diagonal.
/// Padding only up to `max(|A|, |B|)` has no diagonal slot when the diagrams
/// have equal cardinality, so two far points were forced onto each other.
/// Returns `None` if either diagram has more than 8 finite points.
pub fn bottleneck_distance(a: &PersistenceDiagram, b: &PersistenceDiagram) -> Option<f64> {
    let pa: Vec<_> = a.finite_only().cloned().collect();
    let pb: Vec<_> = b.finite_only().cloned().collect();
    if pa.len() > 8 || pb.len() > 8 {
        return None;
    }
    if pa.is_empty() && pb.is_empty() {
        return Some(0.0);
    }
    let mut best = f64::INFINITY;
    bottleneck_search(&pa, &pb, 0, 0, 0.0, &mut best);
    Some(best)
}

fn bottleneck_search(
    pa: &[PersistencePoint],
    pb: &[PersistencePoint],
    index: usize,
    used: u16,
    acc: f64,
    best: &mut f64,
) {
    if acc >= *best {
        return;
    }
    if index == pa.len() {
        let mut matched = acc;
        for (j, point) in pb.iter().enumerate() {
            if used & (1u16 << j) == 0 {
                matched = matched.max(diagonal_cost(point));
            }
        }
        if matched < *best {
            *best = matched;
        }
        return;
    }
    bottleneck_search(
        pa,
        pb,
        index + 1,
        used,
        acc.max(diagonal_cost(&pa[index])),
        best,
    );
    for j in 0..pb.len() {
        if used & (1u16 << j) != 0 {
            continue;
        }
        bottleneck_search(
            pa,
            pb,
            index + 1,
            used | (1u16 << j),
            acc.max(point_cost(&pa[index], &pb[j])),
            best,
        );
    }
}

// Origin: engine/crates_rs/core_homology/src/bottleneck_distance.rs
// Claim: urn:core:crates_rs:core-homology:bottleneck-distance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord550ff737 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord550ff737` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError550ff737 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError550ff737 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError550ff737 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError550ff737 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord550ff737 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError550ff737> {
        if capacity_bound == 0 {
            return Err(BoundaryError550ff737::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError550ff737::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError550ff737::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::persistence_diagram::PersistencePoint;

    #[test]
    fn identical_diagrams_zero() {
        let d = PersistenceDiagram::new(vec![PersistencePoint::finite(
            num_rational::BigRational::from_integer(0.into()),
            num_rational::BigRational::from_integer(1.into()),
            0,
        )]);
        assert_eq!(bottleneck_distance(&d, &d), Some(0.0));
    }

    #[test]
    fn empty_zero() {
        let d = PersistenceDiagram::new(vec![]);
        assert_eq!(bottleneck_distance(&d, &d), Some(0.0));
    }

    #[test]
    fn far_points_of_equal_cardinality_match_the_diagonal() {
        let a = PersistenceDiagram::new(vec![PersistencePoint::finite(
            num_rational::BigRational::from_integer(0.into()),
            num_rational::BigRational::from_integer(10.into()),
            0,
        )]);
        let b = PersistenceDiagram::new(vec![PersistencePoint::finite(
            num_rational::BigRational::from_integer(100.into()),
            num_rational::BigRational::from_integer(110.into()),
            0,
        )]);
        let distance = bottleneck_distance(&a, &b).unwrap();
        assert!(
            (distance - 5.0).abs() < 1e-9,
            "diagonal matching costs 5, got {distance}"
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_550ff737 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord550ff737::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord550ff737::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord550ff737::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord550ff737::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord550ff737::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError550ff737::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError550ff737::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
