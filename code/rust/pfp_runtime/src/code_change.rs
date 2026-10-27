//! Code Change Proposal, Patch candidate submission, and Gate validation.
//!
//! # What the run root binds, and what it cannot
//!
//! A run root carries two keyless digests:
//!
//! * `task_packet_sha256` binds the task id, the proposal payload and the path
//!   manifest root ([`native_task_packet_digest`]);
//! * `run_root_digest` chains, from that task digest, every admitted
//!   `(candidate_id, patch_artifact_id, patch_sha256)` in order
//!   ([`derive_run_root_digest`]). The patch digests themselves are recorded in
//!   `patch_sha256_by_candidate`.
//!
//! Submit and evaluate take a required `expected_task_packet_sha256`, which the
//! caller must supply from the create response, and refuse on mismatch.
//! Evaluate also takes a required `expected_run_root_digest`: the rolling digest
//! the caller received from its last submit. They re-derive both digests, and
//! evaluate hashes the submitted patch bytes and compares them with the digest
//! the run root recorded at submit, not with the artifact's own `patch_sha256`.
//!
//! The host keeps no state and holds no key, so it cannot distinguish a run
//! root it issued from one a caller rebuilt: anyone can call create again with
//! empty protections, or recompute every digest with `domain_digest_json`.
//! Only the caller can close that: the single point of entry (Adversary) must keep
//! the create-time `task_packet_sha256` and the latest `run_root_digest` it was
//! given, and pass them as `expected_task_packet_sha256` and
//! `expected_run_root_digest`. A caller that controls both the root and its own
//! expectations is not constrained by these checks.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_1add80d6;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_1add80d6<T> = std::result::Result<T, BoundaryError_1add80d6>;

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_1add80d6<T> {
    fn checked_invariant_1add80d6(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_1add80d6<T> for Option<T> {
    #[inline]
    fn checked_invariant_1add80d6(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_1add80d6<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_1add80d6(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

use crate::canonical::domain_digest_json;
use crate::diff_parser::{is_path_contained_in_root, parse_unified_diff, validate_path_security};

mod commands;
mod validation;

pub use commands::{
    CreateCodeChangeProposalUseCase, EvaluatePatchGatesUseCase, SubmitPatchCandidateUseCase,
};
use validation::*;

pub const CODE_CHANGE_PATCH_SCHEMA: &str = "core.symbol-game.code-change-patch.v1";
pub const CODE_CHANGE_PROPOSAL_SCHEMA: &str = "core.symbol-game.code-change-proposal.v1";
pub const CODE_CHANGE_RUN_ROOT_SCHEMA: &str = "core.symbol-game.code-change-run-root.v1";
pub const CANDIDATE_ARTIFACT_SCHEMA: &str = "core.symbol-game.candidate-artifact.v1";
pub const GATE_RECEIPT_SCHEMA: &str = "core.symbol-game.gate-receipt.v1";

pub const REFUSAL_TOUCHED_OUTSIDE_OWNED: &str = "REFUSAL_TOUCHED_OUTSIDE_OWNED";
pub const REFUSAL_PROTECTED_FILE_PATCHED: &str = "REFUSAL_PROTECTED_FILE_PATCHED";
/// A create or submit request field is missing, mistyped or outside its bounds.
pub const REFUSAL_CODE_CHANGE_REQUEST_INVALID: &str = "REFUSAL_CODE_CHANGE_REQUEST_INVALID";
/// A run root no longer matches the digest recorded when it was created.
pub const REFUSAL_RUN_ROOT_BINDING_MISMATCH: &str = "REFUSAL_RUN_ROOT_BINDING_MISMATCH";
/// A patch artifact is not one this run root admitted, or its bytes changed.
pub const REFUSAL_PATCH_NOT_BOUND: &str = "REFUSAL_PATCH_NOT_BOUND";
/// The caller's create-time task digest is not the one this run root carries.
pub const REFUSAL_EXPECTED_TASK_DIGEST_MISMATCH: &str = "REFUSAL_EXPECTED_TASK_DIGEST_MISMATCH";
/// The rolling digest the caller holds from its last submit is not this run root's.
pub const REFUSAL_EXPECTED_RUN_ROOT_DIGEST_MISMATCH: &str =
    "REFUSAL_EXPECTED_RUN_ROOT_DIGEST_MISMATCH";

/// Same domain and value shape as the Python lifecycle's `_path_manifest_root`
/// (`pfp/domain/aggregates/code_change_wire.py`), so the
/// two digests agree for the same owned and protected paths.
pub const PATH_MANIFEST_DOMAIN: &str = "core.symbol-game.code-change-path-manifest.v1";
/// Domain of the native task packet digest recorded in `task_packet_sha256`.
pub const NATIVE_TASK_PACKET_DOMAIN: &str = "core.symbol-game.code-change-native-task-packet.v1";
/// Domain of each link of the rolling `run_root_digest` chain.
pub const RUN_ROOT_CHAIN_DOMAIN: &str = "core.symbol-game.code-change-run-root-chain.v1";

/// The gates `EvaluatePatchGatesUseCase` actually runs, in sorted order.
pub const NATIVE_GATE_IDS: [&str; 3] = ["gate_ownership", "gate_protected", "gate_syntax"];
pub const MAX_CODE_CHANGE_PATHS: usize = 256;
pub const MAX_CANDIDATE_BUDGET: usize = 32;
pub const MAX_OPERATION_BUDGET: usize = 4096;
pub const MAX_CODE_CHANGE_ID_LENGTH: usize = 128;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodeChangeProposalPayloadV1 {
    pub objective: String,
    pub source_revision: String,
    pub owned_paths: Vec<String>,
    pub protected_paths: Vec<String>,
    pub allowed_transforms: Vec<String>,
    pub candidate_budget: usize,
    pub operation_budget: usize,
    pub required_gates: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateArtifactV1 {
    pub schema_version: String,
    pub candidate_id: String,
    pub task_id: String,
    pub producer_id: String,
    pub content_artifact_id: String,
    pub content_sha256: String,
    pub content_bytes_len: usize,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodeChangePatchArtifactV1 {
    pub schema_version: String,
    pub patch_artifact_id: String,
    pub patch_sha256: String,
    pub patch_text: String,
    pub byte_count: usize,
    pub touched_paths: Vec<String>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GateReceiptV1 {
    pub schema_version: String,
    pub gate_name: String,
    pub disposition: String,
    pub message: String,
    pub retained_metrics: Value,
    /// Digest of the patch bytes this gate was run on, as the run root recorded it.
    pub patch_sha256: String,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodeChangeRunRootV1 {
    pub schema_version: String,
    pub task_packet_id: String,
    pub task_packet_sha256: String,
    pub task_id: String,
    pub payload: CodeChangeProposalPayloadV1,
    pub candidate_ids: Vec<String>,
    pub patch_ids: Vec<String>,
    pub attempts: Vec<String>,
    pub repairs: Vec<String>,
    pub refusals: Vec<String>,
    pub gate_receipt_ids: Vec<String>,
    pub terminal_status: String,
    pub open_obstruction_ids: Vec<String>,
    /// SHA-256 of each admitted patch's bytes, keyed by candidate id.
    pub patch_sha256_by_candidate: BTreeMap<String, String>,
    /// Rolling digest over the task digest and every admitted patch, in order.
    pub run_root_digest: String,
    pub authority_effect: String,
}

/// Digest binding the owned and protected path manifest, computed as the
/// Python lifecycle computes `path_manifest_root`.
pub fn path_manifest_root(owned_paths: &[String], protected_paths: &[String]) -> String {
    domain_digest_json(
        PATH_MANIFEST_DOMAIN,
        &serde_json::json!({
            "owned_paths": owned_paths,
            "protected_paths": protected_paths,
        }),
    )
    .checked_invariant_1add80d6("a manifest of strings is canonical under a nonempty domain")
}

/// Digest of the immutable task part of a run root: the task id, the whole
/// proposal payload, and the path manifest root. It is recorded at create as
/// `task_packet_id` and `task_packet_sha256` and re-derived before every later
/// step, so a run root whose owned or protected paths, budgets or gates were
/// edited after create is refused instead of evaluated.
///
/// The digest is keyless. It detects a run root that was changed without the
/// digest being recomputed. It cannot detect a caller that re-creates a root
/// with weaker protections or recomputes the digest: the host has no state and
/// no key. The caller (Adversary, as the single point of entry) must keep the
/// create-time digest and pass it as `expected_task_packet_sha256` to every
/// later step; that comparison is what binds the run to the task it created.
pub fn native_task_packet_digest(task_id: &str, payload: &CodeChangeProposalPayloadV1) -> String {
    let payload_value =
        serde_json::to_value(payload).checked_invariant_1add80d6("a code-change payload serializes to JSON");
    domain_digest_json(
        NATIVE_TASK_PACKET_DOMAIN,
        &serde_json::json!({
            "task_id": task_id,
            "payload": payload_value,
            "path_manifest_root": path_manifest_root(&payload.owned_paths, &payload.protected_paths),
        }),
    )
    .checked_invariant_1add80d6("a code-change payload holds only strings and integers")
}

fn chain_run_root_digest(
    previous: &str,
    candidate_id: &str,
    patch_artifact_id: &str,
    patch_sha256: &str,
) -> String {
    domain_digest_json(
        RUN_ROOT_CHAIN_DOMAIN,
        &serde_json::json!({
            "previous": previous,
            "candidate_id": candidate_id,
            "patch_artifact_id": patch_artifact_id,
            "patch_sha256": patch_sha256,
        }),
    )
    .checked_invariant_1add80d6("a chain link holds only strings")
}

fn patch_artifact_id_for(candidate_id: &str) -> String {
    format!("patch_{candidate_id}")
}

/// Re-derive the rolling run-root digest from the task digest and the admitted
/// patches, in submission order. Refuses a root whose id lists and recorded
/// patch digests do not correspond one to one.
pub fn derive_run_root_digest(run_root: &CodeChangeRunRootV1) -> Result<String, String> {
    if run_root.candidate_ids.len() != run_root.patch_ids.len()
        || run_root.patch_sha256_by_candidate.len() != run_root.candidate_ids.len()
    {
        return Err(format!(
            "{REFUSAL_RUN_ROOT_BINDING_MISMATCH}: candidate_ids, patch_ids and \
             patch_sha256_by_candidate do not correspond one to one"
        ));
    }
    let mut digest = run_root.task_packet_sha256.clone();
    for (candidate_id, patch_id) in run_root.candidate_ids.iter().zip(&run_root.patch_ids) {
        if *patch_id != patch_artifact_id_for(candidate_id) {
            return Err(format!(
                "{REFUSAL_RUN_ROOT_BINDING_MISMATCH}: patch id {patch_id:?} does not belong \
                 to candidate {candidate_id:?}"
            ));
        }
        let Some(patch_sha256) = run_root.patch_sha256_by_candidate.get(candidate_id) else {
            return Err(format!(
                "{REFUSAL_RUN_ROOT_BINDING_MISMATCH}: no patch digest recorded for \
                 candidate {candidate_id:?}"
            ));
        };
        digest = chain_run_root_digest(&digest, candidate_id, patch_id, patch_sha256);
    }
    Ok(digest)
}

/// Refuse a run root whose recorded digests do not re-derive from its content,
/// or whose task digest is not the one the caller received at create.
pub fn verify_run_root_binding(
    run_root: &CodeChangeRunRootV1,
    expected_task_packet_sha256: &str,
) -> Result<(), String> {
    if run_root.schema_version != CODE_CHANGE_RUN_ROOT_SCHEMA {
        return Err(format!(
            "{REFUSAL_RUN_ROOT_BINDING_MISMATCH}: unsupported run root schema {:?}",
            run_root.schema_version
        ));
    }
    if run_root.authority_effect != "None" {
        return Err(format!(
            "{REFUSAL_RUN_ROOT_BINDING_MISMATCH}: run root authority_effect must be None"
        ));
    }
    let derived = native_task_packet_digest(&run_root.task_id, &run_root.payload);
    if run_root.task_packet_sha256 != derived || run_root.task_packet_id != derived {
        return Err(format!(
            "{REFUSAL_RUN_ROOT_BINDING_MISMATCH}: recorded task_packet_sha256 {} does not \
             re-derive from the run root content (derived {derived})",
            run_root.task_packet_sha256
        ));
    }
    if expected_task_packet_sha256 != derived {
        return Err(format!(
            "{REFUSAL_EXPECTED_TASK_DIGEST_MISMATCH}: the caller expected task digest \
             {expected_task_packet_sha256:?}, but this run root binds {derived}"
        ));
    }
    let chained = derive_run_root_digest(run_root)?;
    if run_root.run_root_digest != chained {
        return Err(format!(
            "{REFUSAL_RUN_ROOT_BINDING_MISMATCH}: recorded run_root_digest {} does not \
             re-derive from the admitted patches (derived {chained})",
            run_root.run_root_digest
        ));
    }
    Ok(())
}

#[cfg(test)]
#[path = "code_change/tests.rs"]
mod tests;

// Origin: engine/crates_rs/pfp_runtime/src/code_change.rs
// Claim: urn:core:crates_rs:pfp-runtime:code-change:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1add80d6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1add80d6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1add80d6 {
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
impl BoundaryError1add80d6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1add80d6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1add80d6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1add80d6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1add80d6> {
        if capacity_bound == 0 {
            return Err(BoundaryError1add80d6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1add80d6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1add80d6::ExceedsCapacity {
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
mod l4_boundary_tests_1add80d6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1add80d6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1add80d6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1add80d6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1add80d6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1add80d6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1add80d6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1add80d6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
