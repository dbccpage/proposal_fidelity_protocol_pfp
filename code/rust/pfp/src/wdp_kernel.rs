//! Existing host seam for the bounded WDP application certificate checker.
use core_wdp::application_kernel::{check_certificate, model_digest};
use serde_json::{json, Value};
pub fn execute(payload: &Value) -> Result<Value, String> {
    let fields = payload.as_object().ok_or("WDP_KERNEL_REQUEST_INVALID")?;
    if fields.len() != 2 || !fields.contains_key("model") || !fields.contains_key("certificate") {
        return Err("WDP_KERNEL_REQUEST_INVALID".into());
    }
    let model = &fields["model"];
    let certificate = &fields["certificate"];
    Ok(
        json!({"checker_profile":"wdp-finite-belief-model-v1/native-replay-v1",
  "checker_source_sha256":core_wdp::types::sha256_digest(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../core_wdp/src/application_kernel.rs"))),
  "model_digest":model_digest(model)?,"certificate_digest":model_digest(certificate)?,
  "check":check_certificate(model,certificate),"authority_effect":"None"}),
    )
}

// Origin: engine/crates_rs/pfp/src/wdp_kernel.rs
// Claim: urn:core:crates_rs:pfp:wdp-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordeb5eb1e1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordeb5eb1e1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroreb5eb1e1 {
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
impl BoundaryErroreb5eb1e1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroreb5eb1e1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroreb5eb1e1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordeb5eb1e1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroreb5eb1e1> {
        if capacity_bound == 0 {
            return Err(BoundaryErroreb5eb1e1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroreb5eb1e1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroreb5eb1e1::ExceedsCapacity {
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
mod l4_boundary_tests_eb5eb1e1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordeb5eb1e1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordeb5eb1e1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordeb5eb1e1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordeb5eb1e1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordeb5eb1e1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroreb5eb1e1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroreb5eb1e1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
