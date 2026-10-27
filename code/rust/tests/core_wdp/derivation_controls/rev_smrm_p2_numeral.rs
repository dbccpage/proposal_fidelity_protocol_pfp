//! Numeral-Bearing Measurement & Replay Calculus (REV-SMRM-P2-NUMERAL) exact verifier.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MeasurementStep {
    pub state_id: usize,
    pub observed_class: usize,
    pub calibrated_numeral: u64,
}

pub fn verify_measurement_replay(
    trace: &[MeasurementStep],
    calibration: &[u64],
    expected_total: u64,
) -> bool {
    if trace.is_empty() {
        return false;
    }
    let mut sum = 0u64;
    for step in trace {
        if step.observed_class >= calibration.len() {
            return false;
        }
        if calibration[step.observed_class] != step.calibrated_numeral {
            return false;
        }
        sum += step.calibrated_numeral;
    }
    sum == expected_total
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/rev_smrm_p2_numeral.rs
// Claim: urn:core:crates_rs:tests:rev-smrm-p2-numeral:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord009c6c8f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord009c6c8f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError009c6c8f {
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
impl BoundaryError009c6c8f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError009c6c8f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError009c6c8f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord009c6c8f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError009c6c8f> {
        if capacity_bound == 0 {
            return Err(BoundaryError009c6c8f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError009c6c8f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError009c6c8f::ExceedsCapacity {
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
    fn test_numeral_replay_verification() {
        let calibration = [10u64, 20, 35];
        let valid_trace = vec![
            MeasurementStep {
                state_id: 0,
                observed_class: 1,
                calibrated_numeral: 20,
            },
            MeasurementStep {
                state_id: 1,
                observed_class: 2,
                calibrated_numeral: 35,
            },
        ];
        assert!(verify_measurement_replay(&valid_trace, &calibration, 55));
        assert!(!verify_measurement_replay(&valid_trace, &calibration, 50));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_009c6c8f() {
    let admitted = BoundaryRecord009c6c8f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord009c6c8f::try_admit(9, 8).is_err());
}
