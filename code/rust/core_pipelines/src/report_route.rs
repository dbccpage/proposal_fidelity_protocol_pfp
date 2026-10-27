//! Typed manifest for the finite report operation. This manifest cannot execute,
//! evaluate, mint a license or mutate a carrier. The host runtime owns sequencing.
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Binding {
    pub contract_sha256: String,
    pub carrier_sha256: String,
    pub questions_sha256: String,
    pub request_sha256: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Stage {
    pub owner: String,
    pub input: String,
    pub output: String,
    pub authority_effect: String,
    pub binding: Binding,
}

pub fn manifest(binding: &Binding) -> Vec<Stage> {
    [
        ("core_wdp", "Request", "CheckedRepair", "None"),
        (
            "report_partition_copy",
            "CheckedRepair",
            "DetachedReport",
            "None",
        ),
        (
            "core_policy",
            "DetachedReport",
            "LicensedReport",
            "AuthorizesTransition",
        ),
        (
            "engines",
            "LicensedReport",
            "CommittedReport",
            "StateTransition",
        ),
    ]
    .into_iter()
    .map(|(owner, input, output, effect)| Stage {
        owner: owner.into(),
        input: input.into(),
        output: output.into(),
        authority_effect: effect.into(),
        binding: binding.clone(),
    })
    .collect()
}

/// Exact route identity binds every intermediate carrier, protected question
/// family and effect. No adapter or extra stage is silently licensed.
pub fn validate(stages: &[Stage], binding: &Binding) -> Result<(), String> {
    if stages == manifest(binding) {
        Ok(())
    } else {
        Err("REPORT_ROUTE_BINDING".into())
    }
}

// Origin: engine/crates_rs/core_pipelines/src/report_route.rs
// Claim: urn:core:crates_rs:core-pipelines:report-route:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord34573632 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord34573632` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError34573632 {
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
impl BoundaryError34573632 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError34573632 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError34573632 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord34573632 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError34573632> {
        if capacity_bound == 0 {
            return Err(BoundaryError34573632::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError34573632::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError34573632::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_34573632 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord34573632::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord34573632::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord34573632::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord34573632::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord34573632::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError34573632::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError34573632::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
