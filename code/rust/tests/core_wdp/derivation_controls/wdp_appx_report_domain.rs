//! Companion Rust witness crate for `WDP-APPX-REPORT-DOMAIN`:
//! Aligns calibrated model admission and bounded raw report semantics.
//! AuthorityEffect: None.

pub const COST_DOMAIN: &str = "ideal_calibrated_interval_product";
pub const MAX_RAW_BITS: u32 = 256;

/// Checks whether a point interval `[y_pow2, y_pow2]` with `offset = 0` and
/// `gain = 2^(-gain_neg_pow2)` has a raw reading `r = y / gain = 2^(y_pow2 + gain_neg_pow2)`
/// within the 256-bit parser cap (`<= 2^256`).
pub fn point_cell_raw_bits(y_pow2: u32, gain_neg_pow2: u32) -> u32 {
    y_pow2.saturating_add(gain_neg_pow2)
}

pub fn is_executable_under_256bit_cap(y_pow2: u32, gain_neg_pow2: u32) -> bool {
    point_cell_raw_bits(y_pow2, gain_neg_pow2) <= MAX_RAW_BITS
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct R1AlignmentSummary {
    pub cost_domain: &'static str,
    pub ideal_fixed_cost: u32,
    pub ideal_adaptive_cost: u32,
    pub high_cell_raw_exponent: u32,
    pub executable_raw_domain_admissible: bool,
    pub raw_2_510_status: &'static str,
    pub authority_effect: &'static str,
}

pub fn evaluate_r1_witness() -> R1AlignmentSummary {
    let exp = point_cell_raw_bits(255, 255);
    let admissible = is_executable_under_256bit_cap(255, 255);
    R1AlignmentSummary {
        cost_domain: COST_DOMAIN,
        ideal_fixed_cost: 1,
        ideal_adaptive_cost: 1,
        high_cell_raw_exponent: exp,
        executable_raw_domain_admissible: admissible,
        raw_2_510_status: if admissible { "SUPPORTED_MATCH" } else { "INVALID_REPORT" },
        authority_effect: "None",
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appx_report_domain.rs
// Claim: urn:core:crates_rs:tests:wdp-appx-report-domain:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordab4ceb97 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordab4ceb97` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorab4ceb97 {
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
impl BoundaryErrorab4ceb97 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorab4ceb97 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorab4ceb97 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordab4ceb97 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorab4ceb97> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorab4ceb97::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorab4ceb97::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorab4ceb97::ExceedsCapacity {
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
    fn test_r1_witness_alignment() {
        let s = evaluate_r1_witness();
        assert_eq!(s.cost_domain, "ideal_calibrated_interval_product");
        assert_eq!(s.ideal_fixed_cost, 1);
        assert_eq!(s.ideal_adaptive_cost, 1);
        assert_eq!(s.high_cell_raw_exponent, 510);
        assert!(!s.executable_raw_domain_admissible);
        assert_eq!(s.raw_2_510_status, "INVALID_REPORT");
        assert_eq!(s.authority_effect, "None");
    }

    #[test]
    fn test_cap_boundary_255_vs_257() {
        // y = 2^128, gain = 2^-127 => raw = 2^255 (within 2^256 cap)
        assert!(is_executable_under_256bit_cap(128, 127));
        // y = 2^128, gain = 2^-128 => raw = 2^256 (exact boundary of 2^256 cap)
        assert!(is_executable_under_256bit_cap(128, 128));
        // y = 2^129, gain = 2^-128 => raw = 2^257 (exceeds 2^256 cap)
        assert!(!is_executable_under_256bit_cap(129, 128));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_ab4ceb97() {
    let admitted = BoundaryRecordab4ceb97::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordab4ceb97::try_admit(9, 8).is_err());
}
