//! The Symbol Game round loop and its exact domain adapters.
//!
//! The Symbol Game is not a cochain engine. It is a typed search protocol that
//! repeatedly asks an untrusted generator for one candidate move, parses and
//! replays that candidate outside the model, and advances an immutable
//! frontier. The mathematics lives in adapters it may call.
//!
//! Modules:
//!
//! - [`canonical`] -- the tagged `core-canonical-v1` wire format (not RFC 8785), and length-delimited domain digests over it.
//! - [`diff_parser`] -- Strict unified diff parsing, hunk checking, and path traversal security.
//! - [`code_change`] -- Code change proposal run roots, patch candidates, and gate receipt evaluation.
//! - [`research_evidence`] -- Research source artifacts, content-addressed intake bundles, and receipts.
//! - [`prompt_artifact`] -- Python-compatible prompt compilation, rendering, and strict content-addressed admission.
//! - [`prompt_turn`] -- Legacy driver prompt artifacts and elimination receipts.
//! - [`scoring_frontier`] -- Discrete coboundary scoring, L1 norms, and candidate frontier ranking.
//! - [`packets`] -- the candidate/host split, frontier state, terminal proposals.
//! - [`f2`] -- exact finite 𝔽₂ linear algebra and the gauge trichotomy.
//! - [`rational`] -- exact LP duality and L¹ quotient-distance certificates over ℚ.
//! - [`rewriting`] -- structural checks that turn an unsupported Squier-style claim into obligations.
//! - [`packet_wire`] -- Python `core-canonical-v1` packet checks, and the sorted-key plain JSON used for host request ids.
//!
//! # Two encodings, and which is which
//!
//! This crate touches two canonical encodings. They are not alternatives, and
//! confusing them produces digests that disagree across languages, so the
//! division is stated here rather than left to be inferred:
//!
//! - **`core-sorted-json-no-float-v1`** — the *digest envelope*, in
//!   `core_operad_theory::kernel::canonical`. A sorted-key `{domain, payload}`
//!   JSON object that refuses floats and non-ASCII. [`packets::RoundRecord::seal`] uses this, and
//!   `symgam --describe` advertises it. Its Rust↔Python byte-parity is pinned
//!   by a shared fixture.
//!
//! - **`core-canonical-v1`** — the *typed wire format*, in [`canonical`]. A
//!   tagged tree that distinguishes exact integers, rationals, and JSON lists.
//!   Python prompt-artifact identities and driver context identities hash this
//!   encoding with the length-delimited [`canonical::domain_digest`] frame.
//!   The host also exposes it through explicit `invoke` actions. Its parity is pinned by
//!   `tests/canonical_parity.rs` against `golden_canonical_vectors.json`.
//!
//! Select the encoding and domain from the artifact's published contract.
//! Tagged, framed identities and sorted-key digest envelopes are not interchangeable.
//!
//! `pfp::foundation` encodes through [`canonical`] and frames its
//! digests with [`canonical::framed_sha256`]; it has no encoder of its own.
//! `pfp::protocol::canonical_json` delegates to
//! [`packet_wire::sorted_json_bytes`]. That is sorted-key plain JSON, which
//! addresses host requests and outcomes. It is not `core-canonical-v1`, and
//! changing it would change every request id.
//!
//! # Exactness
//!
//! No floating point. [`rational`], [`scoring_frontier`] and [`f2`] are exact
//! over ℚ, 𝔽₂ or the integers, and exact values cross the wire as strings
//! (`"3/4"`), never as JSON numbers. A JSON number is a float in most readers,
//! and the digest profile refuses floats outright.
//!
//! AuthorityEffect: None.

pub mod canonical;
pub mod cochain;
pub mod code_change;
pub mod curriculum;
pub mod decode_control;
pub mod diff_parser;
pub mod driver;
pub mod f2;
pub mod homology_holonomy;
pub mod interface;
pub mod immune_fence;
pub mod jcs;
pub mod lean_verify;
pub mod modular;
pub mod operand;
pub mod operad;
pub mod packet_wire;
pub mod packets;
pub mod pfp_task_turn;
pub mod prompt_artifact;
pub mod prompt_turn;
pub mod rational;
pub mod refusal;
pub mod research_evidence;
pub mod rewriting;
pub mod scoring_frontier;
pub mod scratch_board;
pub mod symbol_game_host;
pub mod stabilizer;
pub mod strict_json;
pub mod synthesis_dag;

pub use canonical::{
    canonical_bytes, canonical_json, canonical_unwire, canonical_wire, domain_digest,
    domain_digest_json, framed_sha256, CanonicalValue, CanonicalizationError, CANONICAL_MARKER,
};
pub use code_change::{
    CandidateArtifactV1, CodeChangePatchArtifactV1, CodeChangeProposalPayloadV1,
    CodeChangeRunRootV1, CreateCodeChangeProposalUseCase, EvaluatePatchGatesUseCase, GateReceiptV1,
    SubmitPatchCandidateUseCase, CANDIDATE_ARTIFACT_SCHEMA, CODE_CHANGE_PATCH_SCHEMA,
    CODE_CHANGE_PROPOSAL_SCHEMA, CODE_CHANGE_RUN_ROOT_SCHEMA, GATE_RECEIPT_SCHEMA,
    REFUSAL_PROTECTED_FILE_PATCHED, REFUSAL_TOUCHED_OUTSIDE_OWNED,
};
pub use cochain::{
    rational as cochain_rational, CochainDisposition, CochainRefusal, PrimeTriadContext,
    PromptCellComplex, PromptCochainEvaluator,
};
pub use decode_control::{
    verify_decode_receipt, DecodeControlReceiptV1, DecodeVerificationVerdict, DECODE_RECEIPT_SCHEMA,
};
pub use diff_parser::{
    is_path_contained_in_root, parse_unified_diff, validate_path_security, DiffParseResult,
};
pub use driver::{
    next_prompt, step, CemeteryRowV1, DriverMovePacket, EngineTurnStateV1, PromptPolicyV1,
    StepOutcome,
};
pub use f2::{F2Error, F2Matrix, GaugeBoard, GaugeVerdict};
pub use homology_holonomy::{
    is_ordered_closure, ordered_loop_product, verify_boundary_closed,
    verify_simplicial_boundary_detailed, verify_simplicial_boundary_law, SimplicialBoundaryReport,
    SimplicialCompositionRecord,
};
pub use jcs::{
    canonicalize as jcs_canonicalize, canonicalize_str as jcs_canonicalize_str,
    canonicalize_value as jcs_canonicalize_value, digest_sha256 as jcs_digest_sha256,
    digest_str_sha256 as jcs_digest_str_sha256, format_es_number, format_es_string, JcsError,
    JcsValue, MAX_SAFE_INTEGER,
};
pub use lean_verify::{
    audit_lean_verification, parse_print_axioms, scan_lean_sources, LeanAuditRequest,
    LeanScanReport, LeanScanRequest, LeanVerificationReceipt, SourceFileEntry, SourceFinding,
    DEFAULT_AXIOM_POLICY, DEFAULT_FORBIDDEN_CONSTRUCTS, LEAN_SCAN_REPORT_SCHEMA,
    LEAN_VERIFICATION_RECEIPT_SCHEMA,
};
pub use modular::least_non_negative_residue;
pub use operand::{
    render_operand_prompt_block, select_operands_for_injection, OperandFilterRefusal,
    OperandStatus, OperandValidationError, SkillOperandV1, MAX_INJECTED_OPERANDS,
    MAX_OPERAND_BYTES, MAX_OPERAND_TOKENS, MAX_TOTAL_INJECTED_TOKENS,
};
pub use operad::{
    AnnihilatorDecoy, AnnihilatorDisposition, ColouredOperadPrompt, CongruenceIdeal, DecoyCandidate,
    LeafTextSpan, OperadMeta, OperadRefusal, OperadTree, PromptColour, PromptColourDef,
    PromptOperator, RefutationWitness,
};
pub use packets::{
    Budget, CandidateMovePacket, Disposition, Finding, FrontierState, LocalReplayStatus, MoveKind,
    Obligation, ParseResult, RoundRecord, StopReason, TerminalProposal,
};
pub use prompt_turn::{
    compile_prompt_artifact, create_elimination_receipt, validate_reply_residual, DemandItemV1,
    EliminationReceiptV1, ObjectiveTypedV1, ObstructionHintV1, PromptArtifactV1,
    DEFAULT_REQUIRED_FIELDS, ELIMINATION_RECEIPT_SCHEMA, PROMPT_ARTIFACT_SCHEMA,
};
pub use rational::{
    verify_l1_certificate, verify_lp_certificate, L1Certificate, L1Refusal, LpCertificate,
    LpRefusal, RationalMatrix, StandardLp,
};
pub use research_evidence::{
    IntakeResearchSourcesUseCase, SourceArtifactV1, SourceIntakeBundleV1, SourceIntakeReceiptV1,
    VerifyResearchClaimUseCase, SOURCE_ARTIFACT_SCHEMA, SOURCE_INTAKE_BUNDLE_SCHEMA,
    SOURCE_INTAKE_RECEIPT_SCHEMA,
};
pub use rewriting::{
    apply, critical_pairs, evaluate_peak_pinned, evaluate_peak_pinned as evaluate_peak,
    is_length_reducing, presentation_digest, CriticalPair, CriticalPeakClaim, ExhaustionBasis,
    PeakEvaluation, PeakVerdict, Presentation, PresentationAuthority, PresentationPins,
    ReductionPath, ReductionStep, Rule, OBLIGATION_PEAK_NONCRITICAL, REFUSAL_PRESENTATION_UNKNOWN,
    TOKEN_SELF_CONSISTENT_ONLY,
};
pub use scoring_frontier::{
    mass_from_ids, mass_from_magnitudes, rank_by_efficiency, rank_candidate_proposals,
    residual_colour_from_mass, residual_drop_from_ids, residual_drop_mass, score_cochain_proposal,
    score_discrete_proposal, set_delta, CandidateProposal, CoboundaryScoreResult, ResidualDropV1,
    REFUSAL_AUTHORITY_NON_NONE, REFUSAL_EXACT_WITHOUT_DUAL, REFUSAL_ILLEGAL_PROPOSAL,
    REFUSAL_NEGATIVE_MAGNITUDE, REFUSAL_PROSE_PROMPT_REFUSED,
};
pub use scratch_board::{
    detect_stationary_attractor, AttractorFinding, AttractorReport,
    DetectStationaryAttractorRequest, TurnRecord as ScratchTurnRecord, ATTRACTOR_REPORT_SCHEMA,
};
pub use stabilizer::{
    check as stabilizer_check, parse_case as stabilizer_parse_case, solve as stabilizer_solve,
    DecompositionRow, StabilizerCase, StabilizerCheckResult, StabilizerOutcome,
    Term as StabilizerTerm,
};
pub use synthesis_dag::{ModuleDagV1, ModuleNodeV1, ModuleStatus, RetractionContextV1};

/// Always `"None"` -- this crate mints zero authority.
pub fn authority_effect() -> &'static str {
    "None"
}

/// The evidence ceiling every result in this crate carries.
pub fn evidence_ceiling() -> &'static str {
    "LocalReplay"
}

/// One admitted local-replay round: both budget axes were positive, and exactly one round is spent.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LocalReplayBudgetWitness {
    rounds_opened: u64,
    rounds_after: u64,
    branches: u64,
    authority: &'static str,
    ceiling: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LocalReplayBudgetError {
    Exhausted,
    AuthorityDrift,
    CeilingDrift,
    RoundAccounting,
}

// Origin: engine/crates_rs/pfp_runtime/src/lib.rs
// Claim: urn:core:crates_rs:pfp-runtime:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for LocalReplayBudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for LocalReplayBudgetError {}

impl LocalReplayBudgetWitness {
    pub fn try_spend_round(opened: Budget) -> Result<Self, LocalReplayBudgetError> {
        if authority_effect() != "None" {
            return Err(LocalReplayBudgetError::AuthorityDrift);
        }
        if evidence_ceiling() != "LocalReplay" {
            return Err(LocalReplayBudgetError::CeilingDrift);
        }
        if opened.is_exhausted() {
            return Err(LocalReplayBudgetError::Exhausted);
        }
        let rounds_after = opened
            .rounds_remaining
            .checked_sub(1)
            .ok_or(LocalReplayBudgetError::RoundAccounting)?;
        let restored = rounds_after
            .checked_add(1)
            .ok_or(LocalReplayBudgetError::RoundAccounting)?;
        if restored != opened.rounds_remaining || opened.branches_remaining == 0 {
            return Err(LocalReplayBudgetError::RoundAccounting);
        }
        Ok(Self {
            rounds_opened: opened.rounds_remaining,
            rounds_after,
            branches: opened.branches_remaining,
            authority: authority_effect(),
            ceiling: evidence_ceiling(),
        })
    }

    pub fn rounds_opened(&self) -> u64 {
        self.rounds_opened
    }

    pub fn rounds_after(&self) -> u64 {
        self.rounds_after
    }

    pub fn branches(&self) -> u64 {
        self.branches
    }

    pub fn authority(&self) -> &'static str {
        self.authority
    }

    pub fn ceiling(&self) -> &'static str {
        self.ceiling
    }
}

/// Compile-time enforcement of this crate's packet contracts.
///
/// Generated by `build.rs` from
/// `governance/contracts/contracts_pfp/`, limited to
/// contracts whose `rust_crate` is `pfp_runtime`. Epic packet
/// types are enforced in `pfp::epics`. A field added, removed, or
/// renamed without amending its contract fails this build.
mod contract_shapes {
    include!(concat!(env!("OUT_DIR"), "/contract_shape_checks.rs"));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod contract_serde_tests {
    include!(concat!(env!("OUT_DIR"), "/contract_serde_tests.rs"));
}
