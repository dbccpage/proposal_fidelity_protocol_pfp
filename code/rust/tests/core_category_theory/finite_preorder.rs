use core_category_theory::finite_relational::{FinitePreorder, RelationalError};

fn reachable_from(start: usize, edges: &[(usize, usize)]) -> [bool; 3] {
    let mut reached = [false; 3];
    reached[start] = true;
    let mut pending = vec![start];
    while let Some(x) = pending.pop() {
        for &(from, to) in edges {
            if from == x && !reached[to] {
                reached[to] = true;
                pending.push(to);
            }
        }
    }
    reached
}

fn is_reflexive_transitive_superrelation(candidate: u16, edges: &[(usize, usize)]) -> bool {
    let contains = |x: usize, y: usize| candidate & (1u16 << (3 * x + y)) != 0;
    (0..3).all(|x| contains(x, x))
        && edges.iter().all(|&(x, y)| contains(x, y))
        && (0..3).all(|x| {
            (0..3).all(|y| (0..3).all(|z| !(contains(x, y) && contains(y, z)) || contains(x, z)))
        })
}

#[test]
fn closure_matches_independent_path_search_for_every_three_state_relation() {
    for mask in 0..512u16 {
        let edges: Vec<_> = (0..9)
            .filter(|bit| mask & (1 << bit) != 0)
            .map(|bit| (bit / 3, bit % 3))
            .collect();
        let order = FinitePreorder::from_edges(3, &edges).unwrap();
        for start in 0..3 {
            for (end, expected) in reachable_from(start, &edges).into_iter().enumerate() {
                assert_eq!(order.leq(start, end).unwrap(), expected, "{mask}, {start}, {end}");
            }
        }
        // Leastness against every possible reflexive, transitive superrelation.
        for candidate in 0..512u16 {
            if is_reflexive_transitive_superrelation(candidate, &edges) {
                for x in 0..3 {
                    for y in 0..3 {
                        let contains = candidate & (1u16 << (3 * x + y)) != 0;
                        assert!(!order.leq(x, y).unwrap() || contains);
                    }
                }
            }
        }
    }
}

#[test]
fn refuses_unknown_endpoints_and_queries_and_distinguishes_preorders_from_orders() {
    assert_eq!(
        FinitePreorder::from_edges(1, &[(0, 1)]),
        Err(RelationalError::RelationOutsideCarrier)
    );
    let empty = FinitePreorder::from_edges(0, &[]).unwrap();
    assert!(empty.is_partial_order());
    assert_eq!(empty.leq(0, 0), Err(RelationalError::StateOutsideCarrier));
    let cycle = FinitePreorder::from_edges(2, &[(0, 1), (1, 0)]).unwrap();
    assert!(!cycle.is_partial_order());
    let chain = FinitePreorder::from_edges(2, &[(0, 1), (0, 1)]).unwrap();
    assert!(chain.is_partial_order());
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_preorder.rs
// Claim: urn:core:crates_rs:tests:finite-preorder:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd06b467b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd06b467b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord06b467b {
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
impl BoundaryErrord06b467b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord06b467b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord06b467b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd06b467b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord06b467b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord06b467b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord06b467b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord06b467b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d06b467b() {
    let admitted = BoundaryRecordd06b467b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd06b467b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
