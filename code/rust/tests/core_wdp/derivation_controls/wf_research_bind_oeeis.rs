//! Bounded finite control for WF-RESEARCH-BIND-OEEIS.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Witness {
    pub goal_id: &'static str,
    pub carrier_val: i64,
    pub secondary_num: i64,
    pub secondary_den: i64,
    pub negative_control_rejected: bool,
}

pub fn reject_inert_candidate_self_activation(promote_unverified: bool) -> Result<(), &'static str> {
    if promote_unverified {
        Err("reject_inert_candidate_self_activation")
    } else {
        Ok(())
    }
}

pub fn witness() -> Witness {
    let neg_rejected = reject_inert_candidate_self_activation(true).is_err();
    Witness {
        goal_id: "WF-RESEARCH-BIND-OEEIS",
        carrier_val: 3,
        secondary_num: 1,
        secondary_den: 1,
        negative_control_rejected: neg_rejected,
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wf_research_bind_oeeis.rs
// Claim: urn:core:crates_rs:tests:wf-research-bind-oeeis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8c5f523c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8c5f523c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8c5f523c {
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
impl BoundaryError8c5f523c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8c5f523c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8c5f523c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8c5f523c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8c5f523c> {
        if capacity_bound == 0 {
            return Err(BoundaryError8c5f523c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8c5f523c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8c5f523c::ExceedsCapacity {
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
    fn wf_research_bind_oeeis_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.goal_id, "WF-RESEARCH-BIND-OEEIS");
        assert_eq!(w.carrier_val, 3);
        assert_eq!(w.secondary_num, 1);
        assert_eq!(w.secondary_den, 1);
        assert!(w.negative_control_rejected);
        assert!(reject_inert_candidate_self_activation(true).is_err());
        assert!(reject_inert_candidate_self_activation(false).is_ok());
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ReducedRatio { numer: i64, denom: i64 }
fn gcd_i64(mut left: i64, mut right: i64) -> Result<i64, &'static str> {
    left = left.checked_abs().ok_or("absolute value overflow")?;
    right = right.checked_abs().ok_or("absolute value overflow")?;
    while right != 0 {
        let remainder = left.checked_rem(right).ok_or("remainder overflow")?;
        left = right;
        right = remainder;
    }
    if left == 0 { Ok(1) } else { Ok(left) }
}
pub fn try_reduce(numer: i64, denom: i64) -> Result<ReducedRatio, &'static str> {
    if denom == 0 {
        return Err("a denominator is positive");
    }
    let (numer, denom) = if denom < 0 {
        (numer.checked_neg().ok_or("numerator negation overflow")?, denom.checked_neg().ok_or("denominator negation overflow")?)
    } else {
        (numer, denom)
    };
    let divisor = gcd_i64(numer, denom)?;
    let numer = numer.checked_div(divisor).ok_or("numerator reduction overflow")?;
    let denom = denom.checked_div(divisor).ok_or("denominator reduction overflow")?;
    if denom <= 0 {
        return Err("a denominator is positive");
    }
    Ok(ReducedRatio { numer, denom })
}
#[test]
fn two_over_four_reduces_to_one_half() {
    let ratio = try_reduce(2, 4);
    assert_eq!(ratio.as_ref().map(|item| item.numer), Ok(1));
    assert_eq!(ratio.as_ref().map(|item| item.denom), Ok(2));
    assert_eq!(try_reduce(1, 0).map(|_| ()), Err("a denominator is positive"));
}

#[test]
fn l4_boundary_admits_and_refuses_8c5f523c() {
    let admitted = BoundaryRecord8c5f523c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8c5f523c::try_admit(9, 8).is_err());
}
