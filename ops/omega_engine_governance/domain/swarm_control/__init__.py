"""Swarm Control Domain Package.

AuthorityEffect: None.
Single-class-per-file domain layer adhering strictly to Clean Architecture and DDD.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from . import bootstrap_v1

if TYPE_CHECKING:
    from .active_lease_state import ActiveLeaseState
    from .agent_action import AgentAction
    from .agent_context import AgentContext
    from .agent_outcome import AgentOutcome
    from .agent_spec import AgentSpec
    from .aggregate_error import AggregateError
    from .application_receipt_v1 import APPLICATION_RECEIPT_SCHEMA_V1, ApplicationReceiptV1, RECEIPT_SCHEMA_V1, compute_receipt_sha256
    from .authority_effect_v1 import AuthorityEffectV1
    from .authority_fence import audit_public_type
    from .authority_fence_error import AuthorityFenceError
    from .authority_parser import parse_active_stop
    from .await_boundary import AwaitBoundary
    from .binding_error import BindingError
    from .blob_read_request import BlobReadRequest
    from .candidate_binding import CandidateBinding, bindings_equal, build_candidate_binding, compute_content_binding_id, revalidate_binding
    from .census_result import CensusResult
    from .census_source import CensusSource
    from .cherry_receipt import CherryReceipt
    from .configuration_error import ConfigurationError
    from .context_mismatch import ContextMismatch
    from .council_bridge import assess_advisory_council_votes, canonical_council_json_bytes, tally_council_votes, verify_council_resolution
    from .council_resolution_status import CouncilResolutionStatus
    from .council_resolution_v1 import CouncilResolutionV1
    from .council_vote_choice import CouncilVoteChoice
    from .council_vote_record import CouncilVoteRecord
    from .decision_outcome import DecisionOutcome
    from .decision_status_v1 import DecisionStatusV1
    from .decision_validation_error import DecisionValidationError
    from .delegate import Delegate
    from .dev_vs_strict import evaluate_measurement, parse_mode
    from .direct_pr_census import census_open_pulls
    from .disposal_decision import DisposalDecision
    from .duplicate_task import DuplicateTask
    from .event_journal import EventJournal
    from .event_tape import EventTape
    from .event_tape_entry_v1 import EventTapeEntryV1, TAPE_SCHEMA_V1, compute_entry_hash, compute_payload_sha256
    from .event_tape_error import EventTapeError
    from .evidence_status import EvidenceStatus, aggregate_required
    from .finish import Finish
    from .git_hygiene_policy import PolicyResult, check_command
    from .git_object_address import parse_blob_spec, safe_blob_read
    from .human_decision_v1 import ALLOWED_EFFECT_TEMPORARY_GIT_APPLY_ONCE, ERR_DECISION_EXPIRED, ERR_DECISION_SCHEMA_VERSION_MISMATCH, ERR_HOLD_DECISION_CANNOT_APPLY, ERR_INVALID_BASE_COMMIT_OID, ERR_INVALID_DECISION_ID, ERR_INVALID_EXPECTED_TREE_OID, ERR_INVALID_FIELD, ERR_INVALID_NONCE_ENTROPY, ERR_INVALID_ONE_USE_TOKEN, ERR_INVALID_POLICY_DIGEST, ERR_ISSUED_AFTER_EXPIRY, ERR_MISSING_IDENTITY_LINKS, ERR_REJECT_DECISION_CANNOT_APPLY, ERR_SELF_ISSUED_PRINCIPAL_ASSERTION_REFUSED, ERR_UNAUTHORIZED_EFFECT, ERR_UNRECOGNIZED_DECISION_OUTCOME, HUMAN_DECISION_SCHEMA_V1, HumanDecisionV1, validate_human_decision
    from .identity_contract_error import IdentityContractError
    from .identity_domain_v1 import IdentityDomainV1
    from .identity_links_v1 import APPLICATION_NOT_YET_CREATED, DECISION_NOT_YET_CREATED, EVIDENCE_NOT_YET_CREATED, EXECUTION_NOT_YET_CREATED, IDENTITY_LINKS_SCHEMA_V1, IdentityLinksV1, MAX_IDENTITY_LINKS_BYTES, MAX_IDENTITY_SCHEMA_CHARS, canonical_identity_links_bytes, identity_links_sha256, identity_ref_from_bytes, parse_identity_links_v1, verify_identity_links_v1
    from .identity_ref_v1 import IdentityRefV1
    from .identity_slot_v1 import IdentitySlotV1
    from .illegal_transition import IllegalTransition
    from .journal_event import JournalEvent
    from .journal_reducer import reduce_events
    from .lease_denied import LeaseDenied
    from .lease_error import LeaseError
    from .lease_grant import LeaseGrant
    from .lifecycle_status_v1 import LifecycleStatusV1
    from .main_readonly import WriteGuardResult, guard_write
    from .memory_record import MemoryRecord
    from .merge_capability import ALLOWED_METHODS, MergeCapability, discover_merge_methods
    from .message import Message
    from .mode import Mode
    from .mode_verdict import ModeVerdict
    from .n1_lease import N1Lease, N1_LEASE_SCHEMA_V1
    from .n1_lease_registry import N1LeaseRegistry
    from .no_agent_available import NoAgentAvailable
    from .nonforce_disposal import can_dispose, validate_cherry_receipt
    from .not_yet_created import NotYetCreated
    from .outcome_status import OutcomeStatus
    from .packet_state import PacketState
    from .parse_disposition import ParseDisposition
    from .parse_result import ParseResult
    from .path_canon import canonical_repo_path, canonicalize_path, path_is_under, paths_conflict, paths_equal
    from .path_lease_registry import PathLeaseRegistry
    from .pin_check import PinCheck
    from .policy_denied import PolicyDenied
    from .post_await_revalidate import record_await, resume_and_revalidate
    from .principal_evidence_v1 import PrincipalEvidenceV1
    from .quorum_threshold import QuorumThreshold
    from .receipt_validation_error import ReceiptValidationError
    from .revalidate_result import RevalidateResult
    from .review_pin import ReviewPin
    from .review_worktree_pin import check_pin, pin_review_head
    from .runtime_event import RuntimeEvent
    from .semantic_contract import SemanticContract
    from .step_limit_exceeded import StepLimitExceeded
    from .swarm_runtime_error import SwarmRuntimeError
    from .swarm_task_limit_exceeded import SwarmTaskLimitExceeded
    from .task import Task
    from .terminal_status_v1 import TerminalStatusV1
    from .tool_call import ToolCall
    from .tool_not_found import ToolNotFound
    from .tool_result import ToolResult
    from .unsafe_git_address import UnsafeGitAddress
    from .window_declaration import WindowDeclaration, fence_authority_effect
    from .work_packet_v1 import REQUIRED_FIELDS, WorkPacketV1, validate_work_packet
    from .work_packet_validation_error import WorkPacketValidationError
    from .value_objects.digest import Digest
    from .value_objects.digest_kind import DigestKind
    from .value_objects.domain_invariant_error import DomainInvariantError
    from .value_objects.epoch import Epoch
    from .value_objects.fence_token import FenceToken
    from .value_objects.id_kind import IdKind
    from .value_objects.identifier import Identifier
    from .value_objects.mutation_action import MutationAction
    from .value_objects.mutation_item_v1 import MutationItemV1
    from .value_objects.mutation_manifest_v1 import MutationManifestV1, compute_manifest_sha256
    from .value_objects.path import RepoPath
    from .value_objects.temporal import UtcTimestamp
    from .value_objects import CandidateId, DecisionId, EventId, EvidenceId, GitBlobOid, GitCommitOid, GitOid, GitTreeOid, LeaseId, ManifestDigest, Nonce, OneUseToken, OwnerId, PacketId, PolicyDigest, PrincipalId, ProblemId, ProposalId, PublicKeyRef, ReceiptId, RepoWorktreeId, Sha256Digest, SignatureDigest
    from .reconciliation_classifier import PathReconciliationDecision, ReconciliationDecisionClass, ReconciliationLedger, classify_path_conflict
    from .exact_blob_reconciliation import ReconciledTree, ReconciliationError, reconcile_exact_blobs
    from .evidence_freshness_rebind import EvidenceFreshnessAssessment, EvidenceFreshnessState, assess_evidence_freshness
    from .universal_transport_receipt import MutationShape, TransportReceiptError, TransportReceiptStatus, UniversalTransportReceipt, create_transport_receipt
    from .portable_reference_scanner import LocusHit, NonPortableReferenceError, ScanReport, scan_text_for_portable_references
    from .merge_mutex import MergeMutexHeldError, MergeMutexInvalidTokenError, MergeMutexState, MergeMutexStatus, MergeMutexToken
    from .cas_land_license import CasHeadDriftError, CasLandLicense, CasLicenseExpiredError, issue_cas_land_license, validate_cas_land_license
    from .postmerge_content_witness import PostmergeContentWitness, PostmergeMismatchError, create_postmerge_content_witness
    from .postmerge_closure_census import PostmergeClosureCensus, PrNotClosedError, verify_postmerge_pr_closure
    from .rebind_after_merge import CandidateRebindResult, rebind_candidate_to_main_epoch
    from .conflict_graph_admission import ConflictAdmissionDecision, ConflictAdmissionStatus, ConflictEdge, evaluate_conflict_graph_admission
    from .swarm_status_reconciliation import SwarmDriftKind, SwarmDriftResidual, SwarmStatusSnapshot, reconcile_swarm_status
    from .swarm_recovery_playbook import RecoveryAction, RecoveryActionType, RecoveryPlan, plan_recovery_from_snapshot
    from .qualification_n1_engine import N1QualificationResult, run_n1_qualification_pipeline
    from .qualification_n2_engine import N2QualificationResult, run_n2_qualification_pipeline
    from .qualification_n4_engine import N4QualificationResult, run_n4_qualification_pipeline
    from .epic_integration_id_map import EpicIntegrationMapRegistry, EpicIntegrationObligation
    from .swarm_n10_skeleton import N10CampaignResult, run_n10_skeleton_harness
    from .chaos_falsifiers import SelfJudgeTamperingError, StrictModeMeasurementError, evaluate_chaos_head_change, evaluate_chaos_measurement_strict, evaluate_chaos_self_judge, evaluate_chaos_transport_na
    from .bootstrap_v1 import BootstrapDeviationSpecV1, OperatorPolicyAdoptionReceiptV1

__all__ = ['ALLOWED_EFFECT_TEMPORARY_GIT_APPLY_ONCE', 'ALLOWED_METHODS', 'APPLICATION_NOT_YET_CREATED', 'APPLICATION_RECEIPT_SCHEMA_V1', 'ActiveLeaseState', 'AgentAction', 'AgentContext', 'AgentOutcome', 'AgentSpec', 'AggregateError', 'ApplicationReceiptV1', 'AuthorityEffectV1', 'AuthorityFenceError', 'AwaitBoundary', 'BindingError', 'BlobReadRequest', 'BootstrapDeviationSpecV1', 'bootstrap_v1', 'CandidateBinding', 'CandidateId', 'CensusResult', 'CensusSource', 'CherryReceipt', 'ConfigurationError', 'ContextMismatch', 'CouncilResolutionStatus', 'CouncilResolutionV1', 'CouncilVoteChoice', 'CouncilVoteRecord', 'DECISION_NOT_YET_CREATED', 'DecisionId', 'DecisionOutcome', 'DecisionStatusV1', 'DecisionValidationError', 'Delegate', 'Digest', 'DigestKind', 'DisposalDecision', 'DomainInvariantError', 'DuplicateTask', 'ERR_DECISION_EXPIRED', 'ERR_DECISION_SCHEMA_VERSION_MISMATCH', 'ERR_HOLD_DECISION_CANNOT_APPLY', 'ERR_INVALID_BASE_COMMIT_OID', 'ERR_INVALID_DECISION_ID', 'ERR_INVALID_EXPECTED_TREE_OID', 'ERR_INVALID_FIELD', 'ERR_INVALID_NONCE_ENTROPY', 'ERR_INVALID_ONE_USE_TOKEN', 'ERR_INVALID_POLICY_DIGEST', 'ERR_ISSUED_AFTER_EXPIRY', 'ERR_MISSING_IDENTITY_LINKS', 'ERR_REJECT_DECISION_CANNOT_APPLY', 'ERR_SELF_ISSUED_PRINCIPAL_ASSERTION_REFUSED', 'ERR_UNAUTHORIZED_EFFECT', 'ERR_UNRECOGNIZED_DECISION_OUTCOME', 'EVIDENCE_NOT_YET_CREATED', 'EXECUTION_NOT_YET_CREATED', 'Epoch', 'EventId', 'EventJournal', 'EventTape', 'EventTapeEntryV1', 'EventTapeError', 'EvidenceId', 'EvidenceStatus', 'FenceToken', 'Finish', 'GitBlobOid', 'GitCommitOid', 'GitOid', 'GitTreeOid', 'HUMAN_DECISION_SCHEMA_V1', 'HumanDecisionV1', 'IDENTITY_LINKS_SCHEMA_V1', 'IdKind', 'Identifier', 'IdentityContractError', 'IdentityDomainV1', 'IdentityLinksV1', 'IdentityRefV1', 'IdentitySlotV1', 'IllegalTransition', 'JournalEvent', 'LeaseDenied', 'LeaseError', 'LeaseGrant', 'LeaseId', 'LifecycleStatusV1', 'MAX_IDENTITY_LINKS_BYTES', 'MAX_IDENTITY_SCHEMA_CHARS', 'ManifestDigest', 'MemoryRecord', 'MergeCapability', 'Message', 'Mode', 'ModeVerdict', 'MutationAction', 'MutationItemV1', 'MutationManifestV1', 'N1Lease', 'N1LeaseRegistry', 'N1_LEASE_SCHEMA_V1', 'NoAgentAvailable', 'Nonce', 'NotYetCreated', 'OneUseToken', 'OperatorPolicyAdoptionReceiptV1', 'OutcomeStatus', 'OwnerId', 'PacketId', 'PacketState', 'ParseDisposition', 'ParseResult', 'PathLeaseRegistry', 'PinCheck', 'PolicyDenied', 'PolicyDigest', 'PolicyResult', 'PrincipalEvidenceV1', 'PrincipalId', 'ProblemId', 'ProposalId', 'PublicKeyRef', 'QuorumThreshold', 'RECEIPT_SCHEMA_V1', 'REQUIRED_FIELDS', 'ReceiptId', 'ReceiptValidationError', 'RepoPath', 'RepoWorktreeId', 'RevalidateResult', 'ReviewPin', 'RuntimeEvent', 'SemanticContract', 'Sha256Digest', 'SignatureDigest', 'StepLimitExceeded', 'SwarmRuntimeError', 'SwarmTaskLimitExceeded', 'TAPE_SCHEMA_V1', 'Task', 'TerminalStatusV1', 'ToolCall', 'ToolNotFound', 'ToolResult', 'UnsafeGitAddress', 'UtcTimestamp', 'WindowDeclaration', 'WorkPacketV1', 'WorkPacketValidationError', 'WriteGuardResult', 'aggregate_required', 'audit_public_type', 'bindings_equal', 'build_candidate_binding', 'can_dispose', 'canonical_council_json_bytes', 'canonical_identity_links_bytes', 'canonical_repo_path', 'canonicalize_path', 'census_open_pulls', 'check_command', 'check_pin', 'compute_content_binding_id', 'compute_entry_hash', 'compute_manifest_sha256', 'compute_payload_sha256', 'compute_receipt_sha256', 'discover_merge_methods', 'evaluate_measurement', 'fence_authority_effect', 'guard_write', 'identity_links_sha256', 'identity_ref_from_bytes', 'parse_active_stop', 'parse_blob_spec', 'parse_identity_links_v1', 'parse_mode', 'path_is_under', 'paths_conflict', 'paths_equal', 'pin_review_head', 'record_await', 'reduce_events', 'resume_and_revalidate', 'revalidate_binding', 'safe_blob_read', 'assess_advisory_council_votes', 'tally_council_votes', 'validate_cherry_receipt', 'validate_human_decision', 'validate_work_packet', 'verify_council_resolution', 'verify_identity_links_v1', 'ReconciliationDecisionClass', 'PathReconciliationDecision', 'ReconciliationLedger', 'classify_path_conflict', 'ReconciledTree', 'ReconciliationError', 'reconcile_exact_blobs', 'EvidenceFreshnessState', 'EvidenceFreshnessAssessment', 'assess_evidence_freshness', 'MutationShape', 'TransportReceiptStatus', 'TransportReceiptError', 'UniversalTransportReceipt', 'create_transport_receipt', 'LocusHit', 'ScanReport', 'NonPortableReferenceError', 'scan_text_for_portable_references', 'MergeMutexStatus', 'MergeMutexHeldError', 'MergeMutexInvalidTokenError', 'MergeMutexToken', 'MergeMutexState', 'CasHeadDriftError', 'CasLicenseExpiredError', 'CasLandLicense', 'issue_cas_land_license', 'validate_cas_land_license', 'PostmergeMismatchError', 'PostmergeContentWitness', 'create_postmerge_content_witness', 'PrNotClosedError', 'PostmergeClosureCensus', 'verify_postmerge_pr_closure', 'CandidateRebindResult', 'rebind_candidate_to_main_epoch', 'ConflictAdmissionStatus', 'ConflictEdge', 'ConflictAdmissionDecision', 'evaluate_conflict_graph_admission', 'SwarmDriftKind', 'SwarmDriftResidual', 'SwarmStatusSnapshot', 'reconcile_swarm_status', 'RecoveryActionType', 'RecoveryAction', 'RecoveryPlan', 'plan_recovery_from_snapshot', 'N1QualificationResult', 'run_n1_qualification_pipeline', 'N2QualificationResult', 'run_n2_qualification_pipeline', 'N4QualificationResult', 'run_n4_qualification_pipeline', 'EpicIntegrationObligation', 'EpicIntegrationMapRegistry', 'N10CampaignResult', 'run_n10_skeleton_harness', 'StrictModeMeasurementError', 'SelfJudgeTamperingError', 'evaluate_chaos_head_change', 'evaluate_chaos_transport_na', 'evaluate_chaos_measurement_strict', 'evaluate_chaos_self_judge']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ActiveLeaseState': ('.active_lease_state', 'ActiveLeaseState'),
    'AgentAction': ('.agent_action', 'AgentAction'),
    'AgentContext': ('.agent_context', 'AgentContext'),
    'AgentOutcome': ('.agent_outcome', 'AgentOutcome'),
    'AgentSpec': ('.agent_spec', 'AgentSpec'),
    'AggregateError': ('.aggregate_error', 'AggregateError'),
    'APPLICATION_RECEIPT_SCHEMA_V1': ('.application_receipt_v1', 'APPLICATION_RECEIPT_SCHEMA_V1'),
    'ApplicationReceiptV1': ('.application_receipt_v1', 'ApplicationReceiptV1'),
    'RECEIPT_SCHEMA_V1': ('.application_receipt_v1', 'RECEIPT_SCHEMA_V1'),
    'compute_receipt_sha256': ('.application_receipt_v1', 'compute_receipt_sha256'),
    'AuthorityEffectV1': ('.authority_effect_v1', 'AuthorityEffectV1'),
    'audit_public_type': ('.authority_fence', 'audit_public_type'),
    'AuthorityFenceError': ('.authority_fence_error', 'AuthorityFenceError'),
    'parse_active_stop': ('.authority_parser', 'parse_active_stop'),
    'AwaitBoundary': ('.await_boundary', 'AwaitBoundary'),
    'BindingError': ('.binding_error', 'BindingError'),
    'BlobReadRequest': ('.blob_read_request', 'BlobReadRequest'),
    'CandidateBinding': ('.candidate_binding', 'CandidateBinding'),
    'bindings_equal': ('.candidate_binding', 'bindings_equal'),
    'build_candidate_binding': ('.candidate_binding', 'build_candidate_binding'),
    'compute_content_binding_id': ('.candidate_binding', 'compute_content_binding_id'),
    'revalidate_binding': ('.candidate_binding', 'revalidate_binding'),
    'CensusResult': ('.census_result', 'CensusResult'),
    'CensusSource': ('.census_source', 'CensusSource'),
    'CherryReceipt': ('.cherry_receipt', 'CherryReceipt'),
    'ConfigurationError': ('.configuration_error', 'ConfigurationError'),
    'ContextMismatch': ('.context_mismatch', 'ContextMismatch'),
    'assess_advisory_council_votes': ('.council_bridge', 'assess_advisory_council_votes'),
    'canonical_council_json_bytes': ('.council_bridge', 'canonical_council_json_bytes'),
    'tally_council_votes': ('.council_bridge', 'tally_council_votes'),
    'verify_council_resolution': ('.council_bridge', 'verify_council_resolution'),
    'CouncilResolutionStatus': ('.council_resolution_status', 'CouncilResolutionStatus'),
    'CouncilResolutionV1': ('.council_resolution_v1', 'CouncilResolutionV1'),
    'CouncilVoteChoice': ('.council_vote_choice', 'CouncilVoteChoice'),
    'CouncilVoteRecord': ('.council_vote_record', 'CouncilVoteRecord'),
    'DecisionOutcome': ('.decision_outcome', 'DecisionOutcome'),
    'DecisionStatusV1': ('.decision_status_v1', 'DecisionStatusV1'),
    'DecisionValidationError': ('.decision_validation_error', 'DecisionValidationError'),
    'Delegate': ('.delegate', 'Delegate'),
    'evaluate_measurement': ('.dev_vs_strict', 'evaluate_measurement'),
    'parse_mode': ('.dev_vs_strict', 'parse_mode'),
    'census_open_pulls': ('.direct_pr_census', 'census_open_pulls'),
    'DisposalDecision': ('.disposal_decision', 'DisposalDecision'),
    'DuplicateTask': ('.duplicate_task', 'DuplicateTask'),
    'EventJournal': ('.event_journal', 'EventJournal'),
    'EventTape': ('.event_tape', 'EventTape'),
    'EventTapeEntryV1': ('.event_tape_entry_v1', 'EventTapeEntryV1'),
    'TAPE_SCHEMA_V1': ('.event_tape_entry_v1', 'TAPE_SCHEMA_V1'),
    'compute_entry_hash': ('.event_tape_entry_v1', 'compute_entry_hash'),
    'compute_payload_sha256': ('.event_tape_entry_v1', 'compute_payload_sha256'),
    'EventTapeError': ('.event_tape_error', 'EventTapeError'),
    'EvidenceStatus': ('.evidence_status', 'EvidenceStatus'),
    'aggregate_required': ('.evidence_status', 'aggregate_required'),
    'Finish': ('.finish', 'Finish'),
    'PolicyResult': ('.git_hygiene_policy', 'PolicyResult'),
    'check_command': ('.git_hygiene_policy', 'check_command'),
    'parse_blob_spec': ('.git_object_address', 'parse_blob_spec'),
    'safe_blob_read': ('.git_object_address', 'safe_blob_read'),
    'ALLOWED_EFFECT_TEMPORARY_GIT_APPLY_ONCE': ('.human_decision_v1', 'ALLOWED_EFFECT_TEMPORARY_GIT_APPLY_ONCE'),
    'ERR_DECISION_EXPIRED': ('.human_decision_v1', 'ERR_DECISION_EXPIRED'),
    'ERR_DECISION_SCHEMA_VERSION_MISMATCH': ('.human_decision_v1', 'ERR_DECISION_SCHEMA_VERSION_MISMATCH'),
    'ERR_HOLD_DECISION_CANNOT_APPLY': ('.human_decision_v1', 'ERR_HOLD_DECISION_CANNOT_APPLY'),
    'ERR_INVALID_BASE_COMMIT_OID': ('.human_decision_v1', 'ERR_INVALID_BASE_COMMIT_OID'),
    'ERR_INVALID_DECISION_ID': ('.human_decision_v1', 'ERR_INVALID_DECISION_ID'),
    'ERR_INVALID_EXPECTED_TREE_OID': ('.human_decision_v1', 'ERR_INVALID_EXPECTED_TREE_OID'),
    'ERR_INVALID_FIELD': ('.human_decision_v1', 'ERR_INVALID_FIELD'),
    'ERR_INVALID_NONCE_ENTROPY': ('.human_decision_v1', 'ERR_INVALID_NONCE_ENTROPY'),
    'ERR_INVALID_ONE_USE_TOKEN': ('.human_decision_v1', 'ERR_INVALID_ONE_USE_TOKEN'),
    'ERR_INVALID_POLICY_DIGEST': ('.human_decision_v1', 'ERR_INVALID_POLICY_DIGEST'),
    'ERR_ISSUED_AFTER_EXPIRY': ('.human_decision_v1', 'ERR_ISSUED_AFTER_EXPIRY'),
    'ERR_MISSING_IDENTITY_LINKS': ('.human_decision_v1', 'ERR_MISSING_IDENTITY_LINKS'),
    'ERR_REJECT_DECISION_CANNOT_APPLY': ('.human_decision_v1', 'ERR_REJECT_DECISION_CANNOT_APPLY'),
    'ERR_SELF_ISSUED_PRINCIPAL_ASSERTION_REFUSED': ('.human_decision_v1', 'ERR_SELF_ISSUED_PRINCIPAL_ASSERTION_REFUSED'),
    'ERR_UNAUTHORIZED_EFFECT': ('.human_decision_v1', 'ERR_UNAUTHORIZED_EFFECT'),
    'ERR_UNRECOGNIZED_DECISION_OUTCOME': ('.human_decision_v1', 'ERR_UNRECOGNIZED_DECISION_OUTCOME'),
    'HUMAN_DECISION_SCHEMA_V1': ('.human_decision_v1', 'HUMAN_DECISION_SCHEMA_V1'),
    'HumanDecisionV1': ('.human_decision_v1', 'HumanDecisionV1'),
    'validate_human_decision': ('.human_decision_v1', 'validate_human_decision'),
    'IdentityContractError': ('.identity_contract_error', 'IdentityContractError'),
    'IdentityDomainV1': ('.identity_domain_v1', 'IdentityDomainV1'),
    'APPLICATION_NOT_YET_CREATED': ('.identity_links_v1', 'APPLICATION_NOT_YET_CREATED'),
    'DECISION_NOT_YET_CREATED': ('.identity_links_v1', 'DECISION_NOT_YET_CREATED'),
    'EVIDENCE_NOT_YET_CREATED': ('.identity_links_v1', 'EVIDENCE_NOT_YET_CREATED'),
    'EXECUTION_NOT_YET_CREATED': ('.identity_links_v1', 'EXECUTION_NOT_YET_CREATED'),
    'IDENTITY_LINKS_SCHEMA_V1': ('.identity_links_v1', 'IDENTITY_LINKS_SCHEMA_V1'),
    'IdentityLinksV1': ('.identity_links_v1', 'IdentityLinksV1'),
    'MAX_IDENTITY_LINKS_BYTES': ('.identity_links_v1', 'MAX_IDENTITY_LINKS_BYTES'),
    'MAX_IDENTITY_SCHEMA_CHARS': ('.identity_links_v1', 'MAX_IDENTITY_SCHEMA_CHARS'),
    'canonical_identity_links_bytes': ('.identity_links_v1', 'canonical_identity_links_bytes'),
    'identity_links_sha256': ('.identity_links_v1', 'identity_links_sha256'),
    'identity_ref_from_bytes': ('.identity_links_v1', 'identity_ref_from_bytes'),
    'parse_identity_links_v1': ('.identity_links_v1', 'parse_identity_links_v1'),
    'verify_identity_links_v1': ('.identity_links_v1', 'verify_identity_links_v1'),
    'IdentityRefV1': ('.identity_ref_v1', 'IdentityRefV1'),
    'IdentitySlotV1': ('.identity_slot_v1', 'IdentitySlotV1'),
    'IllegalTransition': ('.illegal_transition', 'IllegalTransition'),
    'JournalEvent': ('.journal_event', 'JournalEvent'),
    'reduce_events': ('.journal_reducer', 'reduce_events'),
    'LeaseDenied': ('.lease_denied', 'LeaseDenied'),
    'LeaseError': ('.lease_error', 'LeaseError'),
    'LeaseGrant': ('.lease_grant', 'LeaseGrant'),
    'LifecycleStatusV1': ('.lifecycle_status_v1', 'LifecycleStatusV1'),
    'WriteGuardResult': ('.main_readonly', 'WriteGuardResult'),
    'guard_write': ('.main_readonly', 'guard_write'),
    'MemoryRecord': ('.memory_record', 'MemoryRecord'),
    'ALLOWED_METHODS': ('.merge_capability', 'ALLOWED_METHODS'),
    'MergeCapability': ('.merge_capability', 'MergeCapability'),
    'discover_merge_methods': ('.merge_capability', 'discover_merge_methods'),
    'Message': ('.message', 'Message'),
    'Mode': ('.mode', 'Mode'),
    'ModeVerdict': ('.mode_verdict', 'ModeVerdict'),
    'N1Lease': ('.n1_lease', 'N1Lease'),
    'N1_LEASE_SCHEMA_V1': ('.n1_lease', 'N1_LEASE_SCHEMA_V1'),
    'N1LeaseRegistry': ('.n1_lease_registry', 'N1LeaseRegistry'),
    'NoAgentAvailable': ('.no_agent_available', 'NoAgentAvailable'),
    'can_dispose': ('.nonforce_disposal', 'can_dispose'),
    'validate_cherry_receipt': ('.nonforce_disposal', 'validate_cherry_receipt'),
    'NotYetCreated': ('.not_yet_created', 'NotYetCreated'),
    'OutcomeStatus': ('.outcome_status', 'OutcomeStatus'),
    'PacketState': ('.packet_state', 'PacketState'),
    'ParseDisposition': ('.parse_disposition', 'ParseDisposition'),
    'ParseResult': ('.parse_result', 'ParseResult'),
    'canonical_repo_path': ('.path_canon', 'canonical_repo_path'),
    'canonicalize_path': ('.path_canon', 'canonicalize_path'),
    'path_is_under': ('.path_canon', 'path_is_under'),
    'paths_conflict': ('.path_canon', 'paths_conflict'),
    'paths_equal': ('.path_canon', 'paths_equal'),
    'PathLeaseRegistry': ('.path_lease_registry', 'PathLeaseRegistry'),
    'PinCheck': ('.pin_check', 'PinCheck'),
    'PolicyDenied': ('.policy_denied', 'PolicyDenied'),
    'record_await': ('.post_await_revalidate', 'record_await'),
    'resume_and_revalidate': ('.post_await_revalidate', 'resume_and_revalidate'),
    'PrincipalEvidenceV1': ('.principal_evidence_v1', 'PrincipalEvidenceV1'),
    'QuorumThreshold': ('.quorum_threshold', 'QuorumThreshold'),
    'ReceiptValidationError': ('.receipt_validation_error', 'ReceiptValidationError'),
    'RevalidateResult': ('.revalidate_result', 'RevalidateResult'),
    'ReviewPin': ('.review_pin', 'ReviewPin'),
    'check_pin': ('.review_worktree_pin', 'check_pin'),
    'pin_review_head': ('.review_worktree_pin', 'pin_review_head'),
    'RuntimeEvent': ('.runtime_event', 'RuntimeEvent'),
    'SemanticContract': ('.semantic_contract', 'SemanticContract'),
    'StepLimitExceeded': ('.step_limit_exceeded', 'StepLimitExceeded'),
    'SwarmRuntimeError': ('.swarm_runtime_error', 'SwarmRuntimeError'),
    'SwarmTaskLimitExceeded': ('.swarm_task_limit_exceeded', 'SwarmTaskLimitExceeded'),
    'Task': ('.task', 'Task'),
    'TerminalStatusV1': ('.terminal_status_v1', 'TerminalStatusV1'),
    'ToolCall': ('.tool_call', 'ToolCall'),
    'ToolNotFound': ('.tool_not_found', 'ToolNotFound'),
    'ToolResult': ('.tool_result', 'ToolResult'),
    'UnsafeGitAddress': ('.unsafe_git_address', 'UnsafeGitAddress'),
    'WindowDeclaration': ('.window_declaration', 'WindowDeclaration'),
    'fence_authority_effect': ('.window_declaration', 'fence_authority_effect'),
    'REQUIRED_FIELDS': ('.work_packet_v1', 'REQUIRED_FIELDS'),
    'WorkPacketV1': ('.work_packet_v1', 'WorkPacketV1'),
    'validate_work_packet': ('.work_packet_v1', 'validate_work_packet'),
    'WorkPacketValidationError': ('.work_packet_validation_error', 'WorkPacketValidationError'),
    'Digest': ('.value_objects.digest', 'Digest'),
    'DigestKind': ('.value_objects.digest_kind', 'DigestKind'),
    'DomainInvariantError': ('.value_objects.domain_invariant_error', 'DomainInvariantError'),
    'Epoch': ('.value_objects.epoch', 'Epoch'),
    'FenceToken': ('.value_objects.fence_token', 'FenceToken'),
    'IdKind': ('.value_objects.id_kind', 'IdKind'),
    'Identifier': ('.value_objects.identifier', 'Identifier'),
    'MutationAction': ('.value_objects.mutation_action', 'MutationAction'),
    'MutationItemV1': ('.value_objects.mutation_item_v1', 'MutationItemV1'),
    'MutationManifestV1': ('.value_objects.mutation_manifest_v1', 'MutationManifestV1'),
    'compute_manifest_sha256': ('.value_objects.mutation_manifest_v1', 'compute_manifest_sha256'),
    'RepoPath': ('.value_objects.path', 'RepoPath'),
    'UtcTimestamp': ('.value_objects.temporal', 'UtcTimestamp'),
    'CandidateId': ('.value_objects', 'CandidateId'),
    'DecisionId': ('.value_objects', 'DecisionId'),
    'EventId': ('.value_objects', 'EventId'),
    'EvidenceId': ('.value_objects', 'EvidenceId'),
    'GitBlobOid': ('.value_objects', 'GitBlobOid'),
    'GitCommitOid': ('.value_objects', 'GitCommitOid'),
    'GitOid': ('.value_objects', 'GitOid'),
    'GitTreeOid': ('.value_objects', 'GitTreeOid'),
    'LeaseId': ('.value_objects', 'LeaseId'),
    'ManifestDigest': ('.value_objects', 'ManifestDigest'),
    'Nonce': ('.value_objects', 'Nonce'),
    'OneUseToken': ('.value_objects', 'OneUseToken'),
    'OwnerId': ('.value_objects', 'OwnerId'),
    'PacketId': ('.value_objects', 'PacketId'),
    'PolicyDigest': ('.value_objects', 'PolicyDigest'),
    'PrincipalId': ('.value_objects', 'PrincipalId'),
    'ProblemId': ('.value_objects', 'ProblemId'),
    'ProposalId': ('.value_objects', 'ProposalId'),
    'PublicKeyRef': ('.value_objects', 'PublicKeyRef'),
    'ReceiptId': ('.value_objects', 'ReceiptId'),
    'RepoWorktreeId': ('.value_objects', 'RepoWorktreeId'),
    'Sha256Digest': ('.value_objects', 'Sha256Digest'),
    'SignatureDigest': ('.value_objects', 'SignatureDigest'),
    'PathReconciliationDecision': ('.reconciliation_classifier', 'PathReconciliationDecision'),
    'ReconciliationDecisionClass': ('.reconciliation_classifier', 'ReconciliationDecisionClass'),
    'ReconciliationLedger': ('.reconciliation_classifier', 'ReconciliationLedger'),
    'classify_path_conflict': ('.reconciliation_classifier', 'classify_path_conflict'),
    'ReconciledTree': ('.exact_blob_reconciliation', 'ReconciledTree'),
    'ReconciliationError': ('.exact_blob_reconciliation', 'ReconciliationError'),
    'reconcile_exact_blobs': ('.exact_blob_reconciliation', 'reconcile_exact_blobs'),
    'EvidenceFreshnessAssessment': ('.evidence_freshness_rebind', 'EvidenceFreshnessAssessment'),
    'EvidenceFreshnessState': ('.evidence_freshness_rebind', 'EvidenceFreshnessState'),
    'assess_evidence_freshness': ('.evidence_freshness_rebind', 'assess_evidence_freshness'),
    'MutationShape': ('.universal_transport_receipt', 'MutationShape'),
    'TransportReceiptError': ('.universal_transport_receipt', 'TransportReceiptError'),
    'TransportReceiptStatus': ('.universal_transport_receipt', 'TransportReceiptStatus'),
    'UniversalTransportReceipt': ('.universal_transport_receipt', 'UniversalTransportReceipt'),
    'create_transport_receipt': ('.universal_transport_receipt', 'create_transport_receipt'),
    'LocusHit': ('.portable_reference_scanner', 'LocusHit'),
    'NonPortableReferenceError': ('.portable_reference_scanner', 'NonPortableReferenceError'),
    'ScanReport': ('.portable_reference_scanner', 'ScanReport'),
    'scan_text_for_portable_references': ('.portable_reference_scanner', 'scan_text_for_portable_references'),
    'MergeMutexHeldError': ('.merge_mutex', 'MergeMutexHeldError'),
    'MergeMutexInvalidTokenError': ('.merge_mutex', 'MergeMutexInvalidTokenError'),
    'MergeMutexState': ('.merge_mutex', 'MergeMutexState'),
    'MergeMutexStatus': ('.merge_mutex', 'MergeMutexStatus'),
    'MergeMutexToken': ('.merge_mutex', 'MergeMutexToken'),
    'CasHeadDriftError': ('.cas_land_license', 'CasHeadDriftError'),
    'CasLandLicense': ('.cas_land_license', 'CasLandLicense'),
    'CasLicenseExpiredError': ('.cas_land_license', 'CasLicenseExpiredError'),
    'issue_cas_land_license': ('.cas_land_license', 'issue_cas_land_license'),
    'validate_cas_land_license': ('.cas_land_license', 'validate_cas_land_license'),
    'PostmergeContentWitness': ('.postmerge_content_witness', 'PostmergeContentWitness'),
    'PostmergeMismatchError': ('.postmerge_content_witness', 'PostmergeMismatchError'),
    'create_postmerge_content_witness': ('.postmerge_content_witness', 'create_postmerge_content_witness'),
    'PostmergeClosureCensus': ('.postmerge_closure_census', 'PostmergeClosureCensus'),
    'PrNotClosedError': ('.postmerge_closure_census', 'PrNotClosedError'),
    'verify_postmerge_pr_closure': ('.postmerge_closure_census', 'verify_postmerge_pr_closure'),
    'CandidateRebindResult': ('.rebind_after_merge', 'CandidateRebindResult'),
    'rebind_candidate_to_main_epoch': ('.rebind_after_merge', 'rebind_candidate_to_main_epoch'),
    'ConflictAdmissionDecision': ('.conflict_graph_admission', 'ConflictAdmissionDecision'),
    'ConflictAdmissionStatus': ('.conflict_graph_admission', 'ConflictAdmissionStatus'),
    'ConflictEdge': ('.conflict_graph_admission', 'ConflictEdge'),
    'evaluate_conflict_graph_admission': ('.conflict_graph_admission', 'evaluate_conflict_graph_admission'),
    'SwarmDriftKind': ('.swarm_status_reconciliation', 'SwarmDriftKind'),
    'SwarmDriftResidual': ('.swarm_status_reconciliation', 'SwarmDriftResidual'),
    'SwarmStatusSnapshot': ('.swarm_status_reconciliation', 'SwarmStatusSnapshot'),
    'reconcile_swarm_status': ('.swarm_status_reconciliation', 'reconcile_swarm_status'),
    'RecoveryAction': ('.swarm_recovery_playbook', 'RecoveryAction'),
    'RecoveryActionType': ('.swarm_recovery_playbook', 'RecoveryActionType'),
    'RecoveryPlan': ('.swarm_recovery_playbook', 'RecoveryPlan'),
    'plan_recovery_from_snapshot': ('.swarm_recovery_playbook', 'plan_recovery_from_snapshot'),
    'N1QualificationResult': ('.qualification_n1_engine', 'N1QualificationResult'),
    'run_n1_qualification_pipeline': ('.qualification_n1_engine', 'run_n1_qualification_pipeline'),
    'N2QualificationResult': ('.qualification_n2_engine', 'N2QualificationResult'),
    'run_n2_qualification_pipeline': ('.qualification_n2_engine', 'run_n2_qualification_pipeline'),
    'N4QualificationResult': ('.qualification_n4_engine', 'N4QualificationResult'),
    'run_n4_qualification_pipeline': ('.qualification_n4_engine', 'run_n4_qualification_pipeline'),
    'EpicIntegrationMapRegistry': ('.epic_integration_id_map', 'EpicIntegrationMapRegistry'),
    'EpicIntegrationObligation': ('.epic_integration_id_map', 'EpicIntegrationObligation'),
    'N10CampaignResult': ('.swarm_n10_skeleton', 'N10CampaignResult'),
    'run_n10_skeleton_harness': ('.swarm_n10_skeleton', 'run_n10_skeleton_harness'),
    'SelfJudgeTamperingError': ('.chaos_falsifiers', 'SelfJudgeTamperingError'),
    'StrictModeMeasurementError': ('.chaos_falsifiers', 'StrictModeMeasurementError'),
    'evaluate_chaos_head_change': ('.chaos_falsifiers', 'evaluate_chaos_head_change'),
    'evaluate_chaos_measurement_strict': ('.chaos_falsifiers', 'evaluate_chaos_measurement_strict'),
    'evaluate_chaos_self_judge': ('.chaos_falsifiers', 'evaluate_chaos_self_judge'),
    'evaluate_chaos_transport_na': ('.chaos_falsifiers', 'evaluate_chaos_transport_na'),
    'BootstrapDeviationSpecV1': ('.bootstrap_v1', 'BootstrapDeviationSpecV1'),
    'OperatorPolicyAdoptionReceiptV1': ('.bootstrap_v1', 'OperatorPolicyAdoptionReceiptV1'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
