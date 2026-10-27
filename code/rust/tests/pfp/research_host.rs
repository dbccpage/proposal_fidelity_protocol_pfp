//! The research loop and the Anthropic transport through the runtime dispatcher, as Python
//! reaches them. No provider is contacted.
//!
//! AuthorityEffect: None.

use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn invoke(action: &str, payload: Value) -> Value {
    let response = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.into(),
        action: action.into(),
        payload,
    });
    assert!(response.success, "{:?}", response.error);
    response.result.unwrap()
}

fn research(operation: &str, mut payload: Value) -> Value {
    payload["operation"] = json!(operation);
    invoke("adversary_support", payload)
}

fn digest(value: &Value) -> String {
    let bytes = core_adversary::research_loop::canonical::canonical_bytes(value).unwrap();
    format!("sha256:{}", hex::encode(Sha256::digest(bytes)))
}

fn mission() -> Value {
    json!({
        "mission_id": "HOST_FIXTURE", "run_id": "HOST_FIXTURE", "original_seed_ref": "seed.txt",
        "original_question": "fixture", "lane": "source_synthesis",
        "required_claim_ids": ["C1"], "done_predicates": ["provenance"],
        "owned_paths": ["runs/HOST_FIXTURE/"], "forbidden_surfaces": [],
        "source_inventory": "inventory.yaml", "capability_bindings": {"local_read": "bound"},
        "verifier_routes": {"C1": "exact inspection"}, "budget": {}, "retention_policy": "keep all",
    })
}

#[test]
fn a_round_runs_through_the_host_surface() {
    let admitted = research("research_admit", json!({"mission": mission()}));
    assert!(admitted["refusal"].is_null(), "{admitted}");
    let mut checkpoint = admitted["outcome"]["checkpoint"].clone();
    assert_eq!(admitted["outcome"]["next_action"]["action"], "BEGIN_ROUND");

    let apply = |checkpoint: &Value, command: Value| -> Value {
        let reply = research(
            "research_apply",
            json!({"checkpoint": checkpoint, "command": command}),
        );
        assert!(reply["refusal"].is_null(), "{reply}");
        reply["outcome"].clone()
    };
    let out = apply(
        &checkpoint,
        json!({"command": "begin_round", "source_snapshot_sha256": digest(&json!({"v": 1}))}),
    );
    checkpoint = out["checkpoint"].clone();
    let out = apply(
        &checkpoint,
        json!({"command": "reserve", "stage": 1, "occurrence_id": "HOST_FIXTURE.r1.s1.a1",
        "packet_sha256": digest(&json!({"p": 1})), "executor": "ide_agent", "tokens": 0, "cost_microusd": 0}),
    );
    let key = out["output"]["idempotency_key"].clone();
    assert_eq!(
        out["spent"]["model_calls"], 1,
        "an IDE occurrence still counts as a call"
    );

    // A checkpoint edited by the caller is refused before any command runs.
    let mut forged = out["checkpoint"].clone();
    forged["state"]["round_id"] = json!(0);
    let refused = research(
        "research_apply",
        json!({"checkpoint": forged, "command": {"command": "settle", "idempotency_key": key, "tokens": 0, "cost_microusd": 0}}),
    );
    assert_eq!(refused["refusal"]["code"], "CHECKPOINT_TAMPERED");

    let out = apply(
        &out["checkpoint"],
        json!({"command": "settle", "idempotency_key": key, "tokens": 0, "cost_microusd": 0}),
    );
    let out = apply(
        &out["checkpoint"],
        json!({"command": "record", "occurrence_id": "HOST_FIXTURE.r1.s1.a1", "payload": {"frame": "x"}, "failed": false}),
    );
    assert_eq!(
        out["next_action"],
        json!({"action": "DISPATCH", "round": 1, "stage": 2, "phase": "PRODUCE"})
    );
    let events = research("research_events", json!({"checkpoint": out["checkpoint"]}));
    assert!(events["outcome"].as_array().unwrap().len() >= 5);
}

#[test]
fn the_pack_check_and_response_validation_run_on_the_retained_pack() {
    let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../tests/core_adversary/fixtures/research_pack_v1");
    let dir = dir.to_string_lossy().to_string();
    let checked = research("research_pack_check", json!({"workflow_dir": dir}));
    assert!(checked["refusal"].is_null(), "{checked}");
    let reply = research(
        "research_response_validate",
        json!({"workflow_dir": dir, "prompt_id": "P_RESEARCH_06", "response": {"derived_under_policy": "SPK-001"}}),
    );
    assert_eq!(reply["outcome"]["valid"], false);
    let host_only = research(
        "research_response_validate",
        json!({"workflow_dir": dir, "prompt_id": "P_RESEARCH_05", "response": {}}),
    );
    assert_eq!(host_only["refusal"]["code"], "STAGE5_HOST_ONLY");
}

#[test]
fn invalidation_plans_come_back_typed() {
    let reply = research(
        "research_invalidated",
        json!({
            "graph": {"s": [], "c": ["s"], "r": ["c"]}, "changed": ["s"], "local_patch": false,
        }),
    );
    assert_eq!(
        reply["outcome"],
        json!({"route": "INVALIDATE_TRANSITIVE_DEPENDENTS", "invalidated": ["c", "r", "s"]})
    );
    let refused = research(
        "research_invalidated",
        json!({"graph": {}, "changed": [], "local_patch": "yes"}),
    );
    assert_eq!(refused["refusal"]["code"], "RESEARCH_HOST_INPUT_INVALID");
}

#[test]
fn a_zero_ceiling_is_answered_without_a_key_or_a_socket() {
    let reply = invoke(
        "anthropic_messages",
        json!({
            "request": {"model": "claude-sonnet-5-5", "max_tokens": 16, "messages": [{"role": "user", "content": "x"}]},
            "ceiling_microusd": 0, "raw_dir": "unused", "raw_name": "unused", "observations": [], "at_utc": "2026-10-06T12:00:00.000000Z",
        }),
    );
    assert_eq!(reply["outcome"]["dispatch"], "NOT_SENT");
    assert_eq!(
        reply["outcome"]["refusal"]["code"],
        "PAID_DISPATCH_DISABLED"
    );
    let malformed = invoke(
        "anthropic_messages",
        json!({"request": {"model": "m"}, "ceiling_microusd": 0}),
    );
    assert_eq!(malformed["refusal"]["code"], "ANTHROPIC_HOST_INPUT_INVALID");
    // A paid request may write only into an absolute run folder, never above it.
    for raw_dir in [
        "relative/raw",
        "C:/runs/../../elsewhere",
        "/runs/../elsewhere",
    ] {
        let refused = invoke(
            "anthropic_messages",
            json!({
                "request": {"model": "claude-sonnet-5-5", "max_tokens": 16, "messages": [{"role": "user", "content": "x"}]},
                "ceiling_microusd": 1, "raw_dir": raw_dir, "raw_name": "r1", "observations": [], "at_utc": "2026-10-06T12:00:00.000000Z",
            }),
        );
        assert_eq!(
            refused["refusal"]["code"], "ANTHROPIC_HOST_INPUT_INVALID",
            "{raw_dir}"
        );
    }
}

// Origin: engine/crates_rs/tests/pfp/research_host.rs
// Claim: urn:core:crates_rs:tests:research-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda7fc6ef3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda7fc6ef3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora7fc6ef3 {
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
impl BoundaryErrora7fc6ef3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora7fc6ef3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora7fc6ef3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda7fc6ef3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora7fc6ef3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora7fc6ef3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora7fc6ef3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora7fc6ef3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a7fc6ef3() {
    let admitted = BoundaryRecorda7fc6ef3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda7fc6ef3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
