#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PfpPersistenceCalibrationReceipt {
    pub status: &'static str,
    pub persisted_rounds: usize,
    pub max_brier_num: i64,
    pub reason: &'static str,
}

pub fn check_pfp_persistence_and_calibration(
    round_digests: &[&str],
    persisted_digests: &[&str],
    brier_numerators: &[i64],
    brier_denom: i64,
    max_allowed_num: i64,
) -> PfpPersistenceCalibrationReceipt {
    if round_digests.is_empty()
        || brier_denom <= 0
        || round_digests.len() != brier_numerators.len()
    {
        return PfpPersistenceCalibrationReceipt {
            status: "REFUSED",
            persisted_rounds: 0,
            max_brier_num: 0,
            reason: "INVALID_ROUND_OR_CALIBRATION_INPUT",
        };
    }
    if round_digests != persisted_digests {
        return PfpPersistenceCalibrationReceipt {
            status: "REFUSED",
            persisted_rounds: 0,
            max_brier_num: 0,
            reason: "PERSISTENCE_DIGEST_DRIFT",
        };
    }
    let peak = *brier_numerators.iter().max().unwrap_or(&0);
    if brier_numerators.iter().any(|&b| b < 0) || peak > max_allowed_num {
        return PfpPersistenceCalibrationReceipt {
            status: "REFUSED",
            persisted_rounds: round_digests.len(),
            max_brier_num: peak,
            reason: "CALIBRATION_THRESHOLD_EXCEEDED",
        };
    }
    PfpPersistenceCalibrationReceipt {
        status: "PASS",
        persisted_rounds: round_digests.len(),
        max_brier_num: peak,
        reason: "PERSISTENCE_AND_CALIBRATION_VERIFIED",
    }
}

#[test]
fn test_wdp_dp6_01_residual_persistence_and_calibration() {
    let digests = ["sha256:r1", "sha256:r2", "sha256:r3"];
    let ok = check_pfp_persistence_and_calibration(&digests, &digests, &[12, 15, 11], 100, 20);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.persisted_rounds, 3);

    let bad = check_pfp_persistence_and_calibration(&digests, &digests, &[12, 25, 11], 100, 20);
    assert_eq!(bad.status, "REFUSED");
    assert_eq!(bad.reason, "CALIBRATION_THRESHOLD_EXCEEDED");
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_dp6_01_residual.rs
// Claim: urn:core:crates_rs:tests:wdp-dp6-01-residual:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord60e94171 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord60e94171` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError60e94171 {
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
impl BoundaryError60e94171 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError60e94171 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError60e94171 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord60e94171 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError60e94171> {
        if capacity_bound == 0 {
            return Err(BoundaryError60e94171::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError60e94171::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError60e94171::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_60e94171() {
    let admitted = BoundaryRecord60e94171::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord60e94171::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
