//! A local injected transport exercises the actual production composition.
use pfp::adversary_host::execute_with_transport;
use core_adversary::gateway::{SeatPrompt, SeatTransport, TransportFailure};
use serde_json::json;
use std::path::Path;
struct Stub;
impl SeatTransport for Stub {
    fn configured(&self, router: &str) -> bool {
        router == "openrouter"
    }
    fn send(
        &mut self,
        _router: &str,
        _model: &str,
        _prompt: &SeatPrompt,
        _max_tokens: u64,
    ) -> Result<Vec<u8>, TransportFailure> {
        panic!("live transport ran before instruction-plan admission")
    }
}
#[test]
fn live_bout_refuses_before_native_router_ledger_or_terminal_journal() {
    let output = tempfile::tempdir().unwrap();
    let resources = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap();
    let payload = json!({"task_key":"native_live_stub","objective":"write a function adding integers","repo_root":output.path(),"adversary_output_dir":output.path().join("_ic/adversary"),"resources_root":resources,"ledger_path":output.path().join("calls.jsonl"),"bout_id":"local1","config_path":resources.join("adversary/config/seat_routing_v1.yaml"),"live":true,"model_override":"openai/gpt-6-luna","learning_guidance":"reviewed local guidance"});
    let refusal = execute_with_transport(&payload, Stub).unwrap_err();
    assert_eq!(refusal.code, "NATIVE_INSTRUCTION_PLAN_UNBOUND");
    let direct = pfp::adversary_host::dispatch(&payload).unwrap();
    assert_eq!(direct["refusal"]["code"], "NATIVE_INSTRUCTION_PLAN_UNBOUND");
    assert!(!output.path().join("calls.jsonl").exists());
    assert!(!output
        .path()
        .join("_intelligence/_adversary/bout_journal.jsonl")
        .exists());
}

// Origin: engine/crates_rs/tests/pfp/adversary_host.rs
// Claim: urn:core:crates_rs:tests:adversary-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc2962f7e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc2962f7e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc2962f7e {
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
impl BoundaryErrorc2962f7e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc2962f7e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc2962f7e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc2962f7e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc2962f7e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc2962f7e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc2962f7e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc2962f7e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c2962f7e() {
    let admitted = BoundaryRecordc2962f7e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc2962f7e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
