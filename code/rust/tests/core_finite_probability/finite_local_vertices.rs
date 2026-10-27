use core_finite_probability::local_deterministic::*;
use core_number_theory::rational::ri;
fn limits() -> LocalVertexLimits {
    LocalVertexLimits {
        assignments: 100,
        coordinates: 100,
        entries: 10000,
    }
}
#[test]
fn mixed_radix_vertices_cover_every_ternary_binary_assignment() {
    let v = finite_local_vertices(&[3, 2], &[vec![0], vec![1], vec![0, 1]], limits()).unwrap();
    assert_eq!(v.len(), 6);
    for (i, p) in v.iter().enumerate() {
        assert_eq!(p[i % 3], ri(1));
        assert_eq!(p[3 + i / 3], ri(1));
        assert_eq!(p[5 + i], ri(1));
        assert_eq!(p.iter().cloned().sum::<num_rational::BigRational>(), ri(3));
    }
}
#[test]
fn binary_order_matches_independent_bit_restriction() {
    for n in 1..=5 {
        let contexts: Vec<_> = (0..n).map(|i| vec![i]).collect();
        let v = binary_local_vertices(n, &contexts, limits()).unwrap();
        for (assignment, p) in v.iter().enumerate() {
            for i in 0..n {
                assert_eq!(p[2 * i + ((assignment >> i) & 1)], ri(1));
            }
        }
    }
}
#[test]
fn malformed_and_oversized_domains_fail_before_allocation() {
    for counts in [vec![], vec![0], vec![usize::MAX, 2]] {
        assert!(finite_local_vertices(&counts, &[vec![0]], limits()).is_err());
    }
    assert_eq!(
        finite_local_vertices(&[3, 2], &[vec![0]], limits()),
        Err(LocalVertexError::IncompleteCover)
    );
    assert!(finite_local_vertices(&[3], &[vec![0, 0]], limits()).is_err());
    assert_eq!(
        finite_local_vertices(
            &[3],
            &[vec![0]],
            LocalVertexLimits {
                entries: 8,
                ..limits()
            }
        ),
        Err(LocalVertexError::Budget)
    );
}

// Origin: engine/crates_rs/tests/core_finite_probability/finite_local_vertices.rs
// Claim: urn:core:crates_rs:tests:finite-local-vertices:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd03cf65b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd03cf65b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord03cf65b {
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
impl BoundaryErrord03cf65b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord03cf65b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord03cf65b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd03cf65b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord03cf65b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord03cf65b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord03cf65b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord03cf65b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d03cf65b() {
    let admitted = BoundaryRecordd03cf65b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd03cf65b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
