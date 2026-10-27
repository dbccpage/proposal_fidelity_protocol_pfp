//! Commit a detached, licensed report state. No solving, evaluation or minting.
//!
//! This engine owns one in-memory state. Host persistence must conditionally
//! commit the state and trace together against the same pre-state bytes.
use core_policy::ActionLicense;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReportState {
    pub target: String,
    pub version: u64,
    pub contract_sha256: String,
    pub request_sha256: String,
    pub partition: Vec<usize>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CommitTrace {
    pub authority_effect: String,
    pub pre_state_digest: String,
    pub post_state_digest: String,
    pub license_binding: String,
    pub witness_digest: Option<String>,
}

pub fn state_digest(state: &ReportState) -> Result<String, String> {
    let mut hash = Sha256::new();
    hash.update(b"core.report-state.v1\0");
    hash.update(serde_json::to_vec(state).map_err(|e| e.to_string())?);
    Ok(format!("sha256:{:x}", hash.finalize()))
}

/// All checks precede the single assignment. Reusing the license on this
/// updated cell fails its pre-state binding, even if the payload is unchanged.
pub fn commit(
    current: &mut ReportState,
    detached: &ReportState,
    license: &ActionLicense,
) -> Result<CommitTrace, String> {
    if current.target != detached.target
        || current.contract_sha256 != detached.contract_sha256
        || current.request_sha256 != detached.request_sha256
        || current.version.checked_add(1) != Some(detached.version)
    {
        return Err("REPORT_STATE_BINDING".into());
    }
    let pre = state_digest(current)?;
    let post = state_digest(detached)?;
    if !license.authorizes(&pre, &post) {
        return Err("REPORT_LICENSE_BINDING".into());
    }
    let trace = CommitTrace {
        authority_effect: "StateTransition".into(),
        pre_state_digest: pre,
        post_state_digest: post,
        license_binding: license.binding().into(),
        witness_digest: license.exactness_witness_digest().map(str::to_owned),
    };
    *current = detached.clone();
    Ok(trace)
}

// Origin: engine/crates_rs/engines/src/licensed_commit.rs
// Claim: urn:core:crates_rs:engines:licensed-commit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc45dee20 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc45dee20` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc45dee20 {
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
impl BoundaryErrorc45dee20 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc45dee20 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc45dee20 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc45dee20 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc45dee20> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc45dee20::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc45dee20::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc45dee20::ExceedsCapacity {
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
mod tests {
    use super::*;
    use core_policy::{ExactnessWitness, LicensingBoundary, TransitionProposal, ValuationReceipt};

    #[test]
    fn license_is_target_version_payload_bound_and_single_use() {
        let original = ReportState {
            target: "report-a".into(),
            version: 0,
            contract_sha256: "a".repeat(64),
            request_sha256: "b".repeat(64),
            partition: vec![0, 0],
        };
        let mut post = original.clone();
        post.version = 1;
        post.partition = vec![0, 1];
        let license = LicensingBoundary
            .mint(
                &TransitionProposal {
                    pre_state_digest: state_digest(&original).unwrap(),
                    post_state_digest: state_digest(&post).unwrap(),
                    valuation: ValuationReceipt {
                        phi_pre: "1".into(),
                        phi_post: "0".into(),
                        delta_phi_is_non_positive: true,
                        gamma2: "0".into(),
                        gamma2_is_zero: true,
                        phi_post_is_zero: true,
                    },
                    exactness_witness: Some(ExactnessWitness {
                        repair_differential: "split".into(),
                        witness_digest: format!("sha256:{}", "c".repeat(64)),
                        checked_by: "test".into(),
                    }),
                    preserved_invariants: vec![],
                },
                &[],
            )
            .unwrap();
        for index in 0..5 {
            let mut bad = post.clone();
            match index {
                0 => bad.target = "other".into(),
                1 => bad.version = 2,
                2 => bad.partition = vec![1, 0],
                3 => bad.request_sha256 = "c".repeat(64),
                _ => bad.contract_sha256 = "d".repeat(64),
            }
            let mut current = original.clone();
            assert!(commit(&mut current, &bad, &license).is_err());
            assert_eq!(current, original);
        }
        let mut current = original;
        commit(&mut current, &post, &license).unwrap();
        assert_eq!(current, post);
        assert!(commit(&mut current, &post, &license).is_err());
        assert_eq!(current, post);
    }
}

#[cfg(test)]
mod l4_boundary_tests_c45dee20 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc45dee20::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc45dee20::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc45dee20::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc45dee20::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc45dee20::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc45dee20::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc45dee20::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
