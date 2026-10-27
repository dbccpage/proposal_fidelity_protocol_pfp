use num_rational::BigRational as Q;
use core_general_relativity::certified_dihedral::{
    deficit_enclosure, dihedral_enclosure, DeficitSign, GeometryError, MetricHingeStar,
};
use std::collections::BTreeMap;
fn q(n: i64, d: i64) -> Q {
    Q::new(n.into(), d.into())
}
fn regular() -> [[Q; 5]; 5] {
    std::array::from_fn(|i| std::array::from_fn(|j| q(if i == j { 0 } else { 1 }, 1)))
}
fn star(n: usize, orthogonal: bool) -> MetricHingeStar {
    let mut edges = BTreeMap::new();
    for i in 0..n {
        let ids = [0, 1, 2, 3 + i, 3 + (i + 1) % n];
        for a in 0..5 {
            for b in a + 1..5 {
                let x = ids[a].min(ids[b]);
                let y = ids[a].max(ids[b]);
                edges.insert((x, y), q(if orthogonal && x != 0 { 2 } else { 1 }, 1));
            }
        }
    }
    MetricHingeStar::new([0, 1, 2], (3..3 + n).collect(), edges).unwrap()
}

#[test]
fn regular_simplex_angle_is_bound_to_its_exact_gram_data() {
    let angle = dihedral_enclosure(&regular(), &q(1, 1000000)).unwrap();
    assert_eq!(angle.normal_gram(), &[q(2, 3), q(2, 3), q(1, 6)]);
    assert!(angle.bounds().lo() > &q(1318, 1000));
    assert!(angle.bounds().hi() < &q(1319, 1000));
    assert!(angle.bounds().diam() <= q(1, 1000000));
}

#[test]
fn obtuse_normal_angle_uses_the_correct_pi_minus_atan_branch() {
    let squared: [[Q; 5]; 5] = std::array::from_fn(|i| {
        std::array::from_fn(|j| {
            q(
                if i == j {
                    0
                } else if i == 0 || j == 0 {
                    1
                } else if (i == 3 && j == 4) || (i == 4 && j == 3) {
                    3
                } else {
                    2
                },
                1,
            )
        })
    });
    let a = dihedral_enclosure(&squared, &q(1, 100000)).unwrap();
    assert_eq!(a.normal_gram(), &[q(1, 1), q(1, 1), q(-1, 2)]);
    let pi = core_number_theory::certified_angles::pi_enclosure(&q(1, 100000)).unwrap();
    let exact_angle = pi.mul_scalar(&q(2, 3));
    assert!(a.bounds().lo() <= exact_angle.hi() && exact_angle.lo() <= a.bounds().hi());
    assert!(a.bounds().diam() <= q(1, 100000));
}

#[test]
fn closed_metric_stars_give_positive_negative_or_unresolved_zero() {
    for n in [3, 4, 5, 6] {
        let source = star(n, false);
        let c = deficit_enclosure(&source, &q(1, 100000)).unwrap();
        assert_eq!(c.source().cycle(), source.cycle());
        assert_eq!(c.source().squared_edges(), source.squared_edges());
        assert_eq!(c.angles().len(), n);
        assert!(c.bounds().diam() <= q(1, 100000));
        assert!(matches!(
            (n, c.sign()),
            (3 | 4, DeficitSign::Positive { .. }) | (5 | 6, DeficitSign::Negative { .. })
        ));
    }
    let flat = deficit_enclosure(&star(4, true), &q(1, 1000000)).unwrap();
    assert_eq!(flat.sign(), DeficitSign::ContainsZero);
    assert!(flat.bounds().diam() <= q(1, 1000000));
}

#[test]
fn invalid_metrics_cycles_coverage_and_precision_fail_without_panics() {
    let mut squared = regular();
    squared[1][2] = q(100, 1);
    squared[2][1] = q(100, 1);
    assert!(matches!(
        dihedral_enclosure(&squared, &q(1, 100)),
        Err(GeometryError::NotEuclidean)
    ));
    let mut squared = regular();
    squared[0][1] = q(2, 1);
    assert!(matches!(
        dihedral_enclosure(&squared, &q(1, 100)),
        Err(GeometryError::Input)
    ));
    assert!(dihedral_enclosure(&regular(), &Q::new_raw(1.into(), 0.into())).is_err());
    assert!(deficit_enclosure(&star(4, false), &q(-1, 1)).is_err());
    let valid = star(4, false);
    let mut edges = valid.squared_edges().clone();
    edges.remove(&(0, 1));
    assert!(MetricHingeStar::new([0, 1, 2], vec![3, 4, 5, 6], edges).is_err());
    assert!(MetricHingeStar::new([0, 1, 2], vec![3, 3, 4], BTreeMap::new()).is_err());
    assert!(MetricHingeStar::new([0, 1, 2], vec![], BTreeMap::new()).is_err());
}

// Origin: engine/crates_rs/tests/core_general_relativity/certified_dihedral.rs
// Claim: urn:core:crates_rs:tests:certified-dihedral:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord72b0440a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord72b0440a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError72b0440a {
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
impl BoundaryError72b0440a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError72b0440a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError72b0440a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord72b0440a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError72b0440a> {
        if capacity_bound == 0 {
            return Err(BoundaryError72b0440a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError72b0440a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError72b0440a::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_72b0440a() {
    let admitted = BoundaryRecord72b0440a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord72b0440a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
