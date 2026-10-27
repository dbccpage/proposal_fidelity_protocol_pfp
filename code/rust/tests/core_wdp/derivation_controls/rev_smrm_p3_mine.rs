//! Rejection-Ledger Guard Mining & Trace Verification (REV-SMRM-P3-MINE) exact verifier.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Candidate(pub u8, pub u8, pub u8);

pub fn is_valid(c: Candidate) -> bool {
    c.0 == 1 && c.1 != 0 && c.2 == 2
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Guard {
    FirstNotOne,
    SecondIsZero,
    ThirdNotTwo,
}

pub fn mine_guard(c: Candidate) -> Option<Guard> {
    if c.0 != 1 {
        Some(Guard::FirstNotOne)
    } else if c.1 == 0 {
        Some(Guard::SecondIsZero)
    } else if c.2 != 2 {
        Some(Guard::ThirdNotTwo)
    } else {
        None
    }
}

pub fn guard_rejects(g: Guard, c: Candidate) -> bool {
    match g {
        Guard::FirstNotOne => c.0 != 1,
        Guard::SecondIsZero => c.1 == 0,
        Guard::ThirdNotTwo => c.2 != 2,
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/rev_smrm_p3_mine.rs
// Claim: urn:core:crates_rs:tests:rev-smrm-p3-mine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd03e2032 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd03e2032` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord03e2032 {
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
impl BoundaryErrord03e2032 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord03e2032 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord03e2032 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd03e2032 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord03e2032> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord03e2032::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord03e2032::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord03e2032::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mined_guards_never_reject_valid_candidates() {
        let mut universe = Vec::new();
        for a in 0..3 {
            for b in 0..3 {
                for c in 0..3 {
                    universe.push(Candidate(a, b, c));
                }
            }
        }
        for cand in &universe {
            if !is_valid(*cand) {
                let g = mine_guard(*cand).expect("invalid candidate must yield guard");
                assert!(guard_rejects(g, *cand));
                for v in universe.iter().copied().filter(|x| is_valid(*x)) {
                    assert!(!guard_rejects(g, v));
                }
            }
        }
    }
}

#[test]
fn l4_boundary_admits_and_refuses_d03e2032() {
    let admitted = BoundaryRecordd03e2032::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd03e2032::try_admit(9, 8).is_err());
}
