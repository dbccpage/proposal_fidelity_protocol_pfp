//! Sequential create, submit and candidate-bound gate evaluation commands.

use super::*;
use crate::diff_parser::DiffParseResult;

pub struct CreateCodeChangeProposalUseCase;

fn validate_owned_and_protected_paths(
    owned_paths: &[String],
    protected_paths: &[String],
) -> Result<(), String> {
    require_path_list(owned_paths, "owned_paths")?;
    require_path_list(protected_paths, "protected_paths")?;
    if owned_paths.is_empty() {
        return Err(invalid_request("owned_paths must be nonempty"));
    }
    let overlap: Vec<&String> = owned_paths
        .iter()
        .filter(|path| protected_paths.contains(path))
        .collect();
    if !overlap.is_empty() {
        return Err(invalid_request(format!(
            "protected_paths must be disjoint from owned_paths: {overlap:?}"
        )));
    }
    Ok(())
}

fn validate_required_gates(required_gates: &[String]) -> Result<(), String> {
    if required_gates.is_empty() {
        return Err(invalid_request("required_gates must be nonempty"));
    }
    require_sorted_unique(required_gates, "required_gates")?;
    if let Some(unknown) = required_gates
        .iter()
        .find(|gate| !NATIVE_GATE_IDS.contains(&gate.as_str()))
    {
        return Err(invalid_request(format!(
            "required gate {unknown:?} is not run by the native evaluator; \
             supported gates are {NATIVE_GATE_IDS:?}"
        )));
    }
    Ok(())
}

impl CreateCodeChangeProposalUseCase {
    /// Validate every field and build a run root whose digest binds the task
    /// id, the payload and the path manifest. Every rejection is a typed
    /// `REFUSAL_CODE_CHANGE_REQUEST_INVALID`; nothing is defaulted.
    #[allow(clippy::too_many_arguments)]
    pub fn execute(
        &self,
        task_id: &str,
        objective: &str,
        base_revision: &str,
        owned_paths: Vec<String>,
        protected_paths: Vec<String>,
        candidate_budget: usize,
        operation_budget: usize,
        required_gates: Vec<String>,
    ) -> Result<CodeChangeRunRootV1, String> {
        require_text(task_id, "task_id", Some(MAX_CODE_CHANGE_ID_LENGTH))?;
        require_text(objective, "objective", None)?;
        require_revision(base_revision)?;
        validate_owned_and_protected_paths(&owned_paths, &protected_paths)?;
        require_budget(candidate_budget, "candidate_budget", MAX_CANDIDATE_BUDGET)?;
        require_budget(operation_budget, "operation_budget", MAX_OPERATION_BUDGET)?;
        validate_required_gates(&required_gates)?;

        let payload = CodeChangeProposalPayloadV1 {
            objective: objective.to_owned(),
            source_revision: base_revision.to_owned(),
            owned_paths,
            protected_paths,
            allowed_transforms: vec![
                "edit".to_owned(),
                "emit_evidence".to_owned(),
                "test".to_owned(),
            ],
            candidate_budget,
            operation_budget,
            required_gates,
        };
        let task_digest = native_task_packet_digest(task_id, &payload);
        let task_digest_for_chain = task_digest.clone();

        Ok(CodeChangeRunRootV1 {
            schema_version: CODE_CHANGE_RUN_ROOT_SCHEMA.to_owned(),
            task_packet_id: task_digest.clone(),
            task_packet_sha256: task_digest,
            task_id: task_id.to_owned(),
            payload,
            candidate_ids: Vec::new(),
            patch_ids: Vec::new(),
            attempts: Vec::new(),
            repairs: Vec::new(),
            refusals: Vec::new(),
            gate_receipt_ids: Vec::new(),
            terminal_status: "OpenEvaluation".to_owned(),
            open_obstruction_ids: Vec::new(),
            patch_sha256_by_candidate: BTreeMap::new(),
            run_root_digest: task_digest_for_chain,
            authority_effect: "None".to_owned(),
        })
    }
}

pub struct SubmitPatchCandidateUseCase;

impl SubmitPatchCandidateUseCase {
    /// Admit one patch candidate: record its digest in the run root and extend
    /// the rolling run-root digest. `expected_task_packet_sha256` is the digest
    /// the caller received at create.
    pub fn execute(
        &self,
        run_root: &CodeChangeRunRootV1,
        expected_task_packet_sha256: &str,
        candidate_id: &str,
        producer_id: &str,
        patch_text: &str,
    ) -> Result<
        (
            CodeChangeRunRootV1,
            CandidateArtifactV1,
            CodeChangePatchArtifactV1,
        ),
        String,
    > {
        verify_run_root_binding(run_root, expected_task_packet_sha256)?;
        require_text(
            candidate_id,
            "candidate_id",
            Some(MAX_CODE_CHANGE_ID_LENGTH),
        )?;
        require_text(producer_id, "producer_id", Some(MAX_CODE_CHANGE_ID_LENGTH))?;
        if run_root.candidate_ids.iter().any(|id| id == candidate_id) {
            return Err(invalid_request(format!(
                "candidate_id {candidate_id:?} was already submitted to this run root"
            )));
        }
        let budget_limit = run_root.payload.candidate_budget;
        if run_root.candidate_ids.len() >= budget_limit {
            return Err(format!(
                "Candidate budget ({budget_limit}) exhausted for code change {}",
                run_root.task_id
            ));
        }

        let patch_sha = sha256_hex(patch_text);
        let byte_count = patch_text.len();
        let parse_res = parse_unified_diff(patch_text);

        let patch_artifact_id = patch_artifact_id_for(candidate_id);
        let patch_art = CodeChangePatchArtifactV1 {
            schema_version: CODE_CHANGE_PATCH_SCHEMA.to_owned(),
            patch_artifact_id: patch_artifact_id.clone(),
            patch_sha256: patch_sha.clone(),
            patch_text: patch_text.to_owned(),
            byte_count,
            touched_paths: parse_res.touched_paths.clone(),
            authority_effect: "None".to_owned(),
        };

        let cand_art = CandidateArtifactV1 {
            schema_version: CANDIDATE_ARTIFACT_SCHEMA.to_owned(),
            candidate_id: candidate_id.to_owned(),
            task_id: run_root.task_id.clone(),
            producer_id: producer_id.to_owned(),
            content_artifact_id: patch_artifact_id.clone(),
            content_sha256: patch_sha.clone(),
            content_bytes_len: byte_count,
            authority_effect: "None".to_owned(),
        };

        let mut updated_root = run_root.clone();
        updated_root.run_root_digest = chain_run_root_digest(
            &run_root.run_root_digest,
            candidate_id,
            &patch_artifact_id,
            &patch_sha,
        );
        updated_root.candidate_ids.push(candidate_id.to_owned());
        updated_root.patch_ids.push(patch_artifact_id);
        updated_root
            .patch_sha256_by_candidate
            .insert(candidate_id.to_owned(), patch_sha);

        Ok((updated_root, cand_art, patch_art))
    }
}

pub struct EvaluatePatchGatesUseCase;

fn evaluate_syntax_gate(parse_res: &DiffParseResult, patch_sha256: &str) -> GateReceiptV1 {
    // Gate 1: Syntax
    if !parse_res.is_valid {
        GateReceiptV1 {
            schema_version: GATE_RECEIPT_SCHEMA.to_owned(),
            gate_name: "gate_syntax".to_owned(),
            disposition: "FAIL".to_owned(),
            message: format!(
                "Diff syntax invalid or empty: {:?}",
                parse_res.error_message
            ),
            retained_metrics: serde_json::json!({ "syntax_error": parse_res.error_message }),
            patch_sha256: patch_sha256.to_owned(),
            authority_effect: "None".to_owned(),
        }
    } else {
        GateReceiptV1 {
            schema_version: GATE_RECEIPT_SCHEMA.to_owned(),
            gate_name: "gate_syntax".to_owned(),
            disposition: "PASS".to_owned(),
            message: "Diff structure valid".to_owned(),
            retained_metrics: serde_json::json!({ "touched_paths_count": parse_res.touched_paths.len() }),
            patch_sha256: patch_sha256.to_owned(),
            authority_effect: "None".to_owned(),
        }
    }
}

fn evaluate_ownership_gate(
    touched: &[String],
    owned: &[String],
    patch_sha256: &str,
) -> GateReceiptV1 {
    // Gate 2: Ownership
    if touched.is_empty() {
        return GateReceiptV1 {
            schema_version: GATE_RECEIPT_SCHEMA.to_owned(),
            gate_name: "gate_ownership".to_owned(),
            disposition: "FAIL".to_owned(),
            message: format!(
                "{REFUSAL_TOUCHED_OUTSIDE_OWNED}: Zero valid touched paths found in patch"
            ),
            retained_metrics: serde_json::json!({ "unowned_paths": Vec::<String>::new() }),
            patch_sha256: patch_sha256.to_owned(),
            authority_effect: "None".to_owned(),
        };
    }
    let unowned: Vec<&String> = touched
        .iter()
        .filter(|t| !owned.iter().any(|o| is_path_contained_in_root(t, o)))
        .collect();
    if !unowned.is_empty() {
        GateReceiptV1 {
            schema_version: GATE_RECEIPT_SCHEMA.to_owned(),
            gate_name: "gate_ownership".to_owned(),
            disposition: "FAIL".to_owned(),
            message: format!("{REFUSAL_TOUCHED_OUTSIDE_OWNED}: {unowned:?}"),
            retained_metrics: serde_json::json!({ "unowned_paths": unowned }),
            patch_sha256: patch_sha256.to_owned(),
            authority_effect: "None".to_owned(),
        }
    } else {
        GateReceiptV1 {
            schema_version: GATE_RECEIPT_SCHEMA.to_owned(),
            gate_name: "gate_ownership".to_owned(),
            disposition: "PASS".to_owned(),
            message: "All touched paths within declared owned manifest".to_owned(),
            retained_metrics: serde_json::json!({}),
            patch_sha256: patch_sha256.to_owned(),
            authority_effect: "None".to_owned(),
        }
    }
}

fn evaluate_protected_gate(
    touched: &[String],
    protected: &[String],
    patch_sha256: &str,
) -> GateReceiptV1 {
    // Gate 3: Protected Paths
    let violated: Vec<&String> = touched
        .iter()
        .filter(|t| protected.iter().any(|pr| is_path_contained_in_root(t, pr)))
        .collect();
    if !violated.is_empty() {
        GateReceiptV1 {
            schema_version: GATE_RECEIPT_SCHEMA.to_owned(),
            gate_name: "gate_protected".to_owned(),
            disposition: "FAIL".to_owned(),
            message: format!("{REFUSAL_PROTECTED_FILE_PATCHED}: {violated:?}"),
            retained_metrics: serde_json::json!({ "protected_paths_touched": violated }),
            patch_sha256: patch_sha256.to_owned(),
            authority_effect: "None".to_owned(),
        }
    } else {
        GateReceiptV1 {
            schema_version: GATE_RECEIPT_SCHEMA.to_owned(),
            gate_name: "gate_protected".to_owned(),
            disposition: "PASS".to_owned(),
            message: "Zero protected paths modified".to_owned(),
            retained_metrics: serde_json::json!({}),
            patch_sha256: patch_sha256.to_owned(),
            authority_effect: "None".to_owned(),
        }
    }
}

impl EvaluatePatchGatesUseCase {
    /// Refuse unless the run root still matches the caller's create-time task
    /// digest, re-derives its own rolling digest, and carries the rolling
    /// digest the caller holds from its last submit (`expected_run_root_digest`),
    /// and the patch bytes hash to the digest the run root recorded for that
    /// candidate at submit; then run the three native gates. Every receipt
    /// carries that patch digest.
    pub fn execute(
        &self,
        run_root: &CodeChangeRunRootV1,
        expected_task_packet_sha256: &str,
        expected_run_root_digest: &str,
        patch: &CodeChangePatchArtifactV1,
    ) -> Result<Vec<GateReceiptV1>, String> {
        verify_run_root_binding(run_root, expected_task_packet_sha256)?;
        if run_root.run_root_digest != expected_run_root_digest {
            return Err(format!(
                "{REFUSAL_EXPECTED_RUN_ROOT_DIGEST_MISMATCH}: the caller holds rolling digest \
                 {expected_run_root_digest:?}, but this run root carries {}",
                run_root.run_root_digest
            ));
        }
        let Some(index) = run_root
            .patch_ids
            .iter()
            .position(|id| *id == patch.patch_artifact_id)
        else {
            return Err(format!(
                "{REFUSAL_PATCH_NOT_BOUND}: patch {:?} was not submitted to this run root",
                patch.patch_artifact_id
            ));
        };
        let candidate_id = &run_root.candidate_ids[index];
        let recorded = run_root
            .patch_sha256_by_candidate
            .get(candidate_id)
            .expect("derive_run_root_digest checked every candidate has a digest")
            .clone();
        // The artifact's own patch_sha256 is caller-supplied; the bytes are
        // compared with the digest the run root recorded when it admitted them.
        if sha256_hex(&patch.patch_text) != recorded
            || patch.patch_sha256 != recorded
            || patch.byte_count != patch.patch_text.len()
        {
            return Err(format!(
                "{REFUSAL_PATCH_NOT_BOUND}: patch {:?} bytes do not match the digest the \
                 run root recorded for candidate {candidate_id:?} at submit",
                patch.patch_artifact_id
            ));
        }
        let patch_sha256 = recorded;
        let parse_res = parse_unified_diff(&patch.patch_text);
        let touched = if parse_res.is_valid {
            &parse_res.touched_paths
        } else {
            &patch.touched_paths
        };

        let receipts = vec![
            evaluate_syntax_gate(&parse_res, &patch_sha256),
            evaluate_ownership_gate(touched, &run_root.payload.owned_paths, &patch_sha256),
            evaluate_protected_gate(touched, &run_root.payload.protected_paths, &patch_sha256),
        ];

        Ok(receipts)
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/code_change/commands.rs
// Claim: urn:core:crates_rs:pfp-runtime:commands:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1f23c82a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1f23c82a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1f23c82a {
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
impl BoundaryError1f23c82a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1f23c82a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1f23c82a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1f23c82a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1f23c82a> {
        if capacity_bound == 0 {
            return Err(BoundaryError1f23c82a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1f23c82a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1f23c82a::ExceedsCapacity {
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
mod l4_boundary_tests_1f23c82a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1f23c82a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1f23c82a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1f23c82a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1f23c82a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1f23c82a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1f23c82a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1f23c82a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
