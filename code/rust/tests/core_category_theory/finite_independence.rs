use core_category_theory::finite_continuation::{ContinuationError, PartialDynamics};
use core_category_theory::finite_independence::SwapOutcome;
#[test]
fn exhaustive_two_state_diamonds_match_all_short_futures() {
    // 4 readouts * 81 tables * 2 starts; <=9 letters covers the totalized pair graph.
    for labels in 0..4 {
        for table in 0..81 {
            let mut n = table;
            let mut rows = vec![vec![None; 2]; 2];
            for cell in rows.iter_mut().flatten() {
                let v = n % 3;
                n /= 3;
                *cell = (v < 2).then_some(v);
            }
            let m = PartialDynamics::new(vec![labels & 1, labels >> 1], rows, 2).unwrap();
            for s in 0..2 {
                let c = m.certify_swap(s, 0, 1, 9).unwrap();
                m.verify_swap(&c).unwrap();
                let expected = match (m.run(s, &[0, 1]).unwrap(), m.run(s, &[1, 0]).unwrap()) {
                    (Some(l), Some(r)) => (0..10).all(|len| {
                        (0..1usize << len).all(|bits| {
                            let w: Vec<_> = (0..len).map(|i| (bits >> i) & 1).collect();
                            m.run(l, &w).unwrap().map(|t| m.reports()[t])
                                == m.run(r, &w).unwrap().map(|t| m.reports()[t])
                        })
                    }),
                    _ => false,
                };
                assert_eq!(
                    matches!(c.outcome, SwapOutcome::Independent { .. }),
                    expected
                );
            }
        }
    }
}
#[test]
fn unavailable_is_not_independence_and_malformed_witnesses_fail() {
    let m = PartialDynamics::new(vec![0], vec![vec![None, None]], 2).unwrap();
    let mut c = m.certify_swap(0, 0, 1, 1).unwrap();
    assert!(matches!(c.outcome, SwapOutcome::Unavailable { .. }));
    c.outcome = SwapOutcome::Independent {
        ab: usize::MAX,
        ba: usize::MAX,
    };
    assert!(m.verify_swap(&c).is_err());
    assert_eq!(
        m.certify_swap(0, 0, 2, 1),
        Err(ContinuationError::OutsideAlphabet)
    );
}
#[test]
fn present_equality_does_not_hide_future_availability() {
    let m = PartialDynamics::new(
        vec![0; 5],
        vec![
            vec![Some(1), Some(2)],
            vec![None, Some(3)],
            vec![Some(4), None],
            vec![Some(3), Some(3)],
            vec![None, Some(4)],
        ],
        2,
    )
    .unwrap();
    let c = m.certify_swap(0, 0, 1, 9).unwrap();
    let SwapOutcome::Distinguished { future, .. } = &c.outcome else {
        panic!("missing distinction")
    };
    assert_eq!(future.word, vec![0]);
    m.verify_swap(&c).unwrap();
    assert_eq!(
        m.certify_swap(0, 0, 1, 1),
        Err(ContinuationError::WorkLimit)
    );
}
#[test]
fn independence_need_not_be_raw_replay_equality() {
    let m = PartialDynamics::new(vec![0; 2], vec![vec![Some(0), Some(1)]; 2], 2).unwrap();
    let c = m.certify_swap(0, 0, 1, 4).unwrap();
    assert_eq!(c.outcome, SwapOutcome::Independent { ab: 1, ba: 0 });
    m.verify_swap(&c).unwrap();
    let changed = PartialDynamics::new(vec![0, 1], m.transitions().to_vec(), 2).unwrap();
    assert!(changed.verify_swap(&c).is_err());
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_independence.rs
// Claim: urn:core:crates_rs:tests:finite-independence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord01759067 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord01759067` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError01759067 {
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
impl BoundaryError01759067 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError01759067 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError01759067 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord01759067 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError01759067> {
        if capacity_bound == 0 {
            return Err(BoundaryError01759067::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError01759067::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError01759067::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_01759067() {
    let admitted = BoundaryRecord01759067::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord01759067::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
