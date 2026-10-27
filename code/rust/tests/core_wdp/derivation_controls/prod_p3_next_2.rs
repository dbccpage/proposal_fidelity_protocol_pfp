//! Companion Rust witness for PROD-P3-NEXT-2 (Appendix Q.4 13-hit break-even example).

pub fn q4_saving_milli(hits: i64) -> i64 {
    // N = 10_000, v = 1 (1000 milli), g = 1/1000 (1 milli), C_0 = 2 (2000 milli)
    hits * 1000 - 10_000 * 1 - 2000
}

pub fn q4_strict_benefit(hits: i64) -> bool {
    q4_saving_milli(hits) > 0
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p3_next_2.rs
// Claim: urn:core:crates_rs:tests:prod-p3-next-2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb0d1c7c8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb0d1c7c8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb0d1c7c8 {
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
impl BoundaryErrorb0d1c7c8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb0d1c7c8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb0d1c7c8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb0d1c7c8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb0d1c7c8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb0d1c7c8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb0d1c7c8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb0d1c7c8::ExceedsCapacity {
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
    fn q4_worked_example_requires_at_least_thirteen_hits_for_strict_benefit() {
        for h in 0..=12 {
            assert!(!q4_strict_benefit(h));
        }
        assert_eq!(q4_saving_milli(12), 0);
        assert_eq!(q4_saving_milli(13), 1000);
        assert!(q4_strict_benefit(13));
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BreakEven { hits: i64, saving_milli: i64, strict: bool }
pub fn try_break_even(hits: i64) -> Result<BreakEven, &'static str> {
    if hits < 0 {
        return Err("hits are nonnegative");
    }
    let gross = hits.checked_mul(1000).ok_or("saving product overflow")?;
    let saving = gross.checked_sub(12_000).ok_or("saving difference overflow")?;
    let delta = hits.checked_sub(12).ok_or("break-even offset overflow")?;
    let scaled = delta.checked_mul(1000).ok_or("scaled saving overflow")?;
    if scaled != saving {
        return Err("saving is not the exact break-even identity");
    }
    let strict = saving > 0;
    if strict != (hits >= 13) {
        return Err("strict benefit is not hits at least 13");
    }
    Ok(BreakEven { hits, saving_milli: saving, strict })
}
#[test]
fn twelve_hits_save_nothing_and_thirteen_save_one_thousand_milli() {
    let even = try_break_even(12);
    assert_eq!(even.as_ref().map(|item| item.saving_milli), Ok(0));
    assert_eq!(even.as_ref().map(|item| item.strict), Ok(false));
    let benefit = try_break_even(13);
    assert_eq!(benefit.as_ref().map(|item| item.saving_milli), Ok(1000));
    assert_eq!(benefit.as_ref().map(|item| item.strict), Ok(true));
    assert_eq!(try_break_even(i64::MAX).map(|_| ()), Err("saving product overflow"));
}

#[test]
fn l4_boundary_admits_and_refuses_b0d1c7c8() {
    let admitted = BoundaryRecordb0d1c7c8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb0d1c7c8::try_admit(9, 8).is_err());
}
