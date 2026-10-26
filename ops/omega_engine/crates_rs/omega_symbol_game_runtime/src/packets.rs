//! Candidate packets, host round records, and frontier state.
//!
//! Merge spec sections 6.3–6.5. The separation those sections describe is
//! enforced here **by type, not by validation**:
//!
//! - [`CandidateMovePacket`] is what an untrusted generator emits. It has no
//!   field for a digest, a canonical id, a verification status, a receipt, a
//!   registry mutation, or a terminal decision. A model cannot claim any of
//!   them because there is nowhere to put them.
//! - [`RoundRecord`] carries exactly those things, and its only constructor is
//!   [`RoundRecord::seal`], which computes them from the packet. There is no
//!   way to hand-build one with a chosen digest.
//!
//! A validation-based split would have to be re-checked at every boundary and
//! could be forgotten at one. This cannot.
//!
//! AuthorityEffect: None throughout. `PASS` here means one named local
//! procedure passed on named artifacts; it is not a global `VERIFIED`.

use omega_operad_theory::kernel::canonical::{canonical_id, CanonicalError};
use serde::{Deserialize, Serialize};

/// Why a [`RoundRecord`] could not be sealed.
///
/// Sealing computes the receipt digest, so a failure here must surface rather
/// than resolve to some default. The previous `unwrap_or_default()` gave every
/// unrepresentable packet the digest of the empty string -- a plausible-looking
/// hash that several distinct packets would share.
#[derive(Debug, thiserror::Error)]
pub enum SealError {
    #[error("candidate packet is not representable as JSON: {source}")]
    NotRepresentable { source: serde_json::Error },

    /// The packet held something the canonical profile refuses: a float, or a
    /// non-ASCII string. Both are refused rather than coerced, because neither
    /// has an agreed byte-level form across languages.
    #[error("candidate packet is not canonical: {source}")]
    NotCanonical { source: CanonicalError },
}

/// The move families a candidate may declare.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MoveKind {
    Propose,
    Critique,
    RequestEvidence,
    SupplyWitness,
    Repair,
    Fork,
    MergeProposal,
    Refuse,
    TerminalProposal,
}

impl MoveKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Propose => "PROPOSE",
            Self::Critique => "CRITIQUE",
            Self::RequestEvidence => "REQUEST_EVIDENCE",
            Self::SupplyWitness => "SUPPLY_WITNESS",
            Self::Repair => "REPAIR",
            Self::Fork => "FORK",
            Self::MergeProposal => "MERGE_PROPOSAL",
            Self::Refuse => "REFUSE",
            Self::TerminalProposal => "TERMINAL_PROPOSAL",
        }
    }
}

/// An objection or detector finding. Detection is separate from repair: a
/// finding never carries the change that would fix it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Finding {
    pub code: String,
    pub detail: String,
}

/// An unresolved obligation the frontier still owes.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Obligation {
    pub id: String,
    pub description: String,
    pub discharged: bool,
}

/// What an untrusted generator emits.
///
/// Deliberately absent: `canonical_digest`, `verified`, `admitted`,
/// `receipt`, `authority_effect`, `terminal_status`. Those are host facts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateMovePacket {
    pub schema_version: String,
    pub parent_state_ref: String,
    pub round_index: u64,
    pub selected_operation_ref: String,
    pub move_kind: MoveKind,
    pub consumed_operand_refs: Vec<String>,
    pub public_rationale: String,
    pub proposed_claim_deltas: Vec<String>,
    pub witness_proposals: Vec<String>,
    pub evidence_requests: Vec<String>,
    pub objections: Vec<Finding>,
    pub child_obligations: Vec<Obligation>,
    pub requested_reframe: Option<String>,
}

impl CandidateMovePacket {
    pub const SCHEMA: &'static str = "candidate-move/v1";

    pub fn new(
        parent_state_ref: &str,
        round_index: u64,
        selected_operation_ref: &str,
        move_kind: MoveKind,
        public_rationale: &str,
    ) -> Self {
        Self {
            schema_version: Self::SCHEMA.to_owned(),
            parent_state_ref: parent_state_ref.to_owned(),
            round_index,
            selected_operation_ref: selected_operation_ref.to_owned(),
            move_kind,
            consumed_operand_refs: Vec::new(),
            public_rationale: public_rationale.to_owned(),
            proposed_claim_deltas: Vec::new(),
            witness_proposals: Vec::new(),
            evidence_requests: Vec::new(),
            objections: Vec::new(),
            child_obligations: Vec::new(),
            requested_reframe: None,
        }
    }

    /// The authority a candidate carries. Always `None`, and not a field, so a
    /// generator cannot set it.
    pub fn authority_effect(&self) -> &'static str {
        "None"
    }
}

/// Whether the host could parse the candidate at all.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ParseResult {
    Pass,
    Fail,
}

/// What the host decided to do with a parsed candidate.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Disposition {
    Rejected,
    NeedsEvidence,
    Bounded,
    AcceptedDelta,
    TerminalProposal,
}

impl Disposition {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Rejected => "REJECTED",
            Self::NeedsEvidence => "NEEDS_EVIDENCE",
            Self::Bounded => "BOUNDED",
            Self::AcceptedDelta => "ACCEPTED_DELTA",
            Self::TerminalProposal => "TERMINAL_PROPOSAL",
        }
    }
}

/// Outcome of a named local replay. Never a global verification status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LocalReplayStatus {
    NotRun,
    Pass,
    Fail,
    Inconclusive,
}

/// The host's record of one round.
///
/// Only [`RoundRecord::seal`] can build one, so `canonical_digest` is always a
/// value this host computed over the candidate's canonical bytes.
///
/// # Serialize only, and that is the enforcement
///
/// This type deliberately does **not** derive `Deserialize`, and must not.
///
/// It used to. A private field does not stop serde: the derive generates a
/// field-by-field constructor *inside this module*, where `canonical_digest`
/// is perfectly visible. Measured before the derive was removed, this was
/// accepted:
///
/// ```text
/// serde_json::from_value::<RoundRecord>(json!({ ..., "canonical_digest": "000...0" }))
///   -> Ok(RoundRecord { canonical_digest: "000...0", .. })
/// ```
///
/// A caller-supplied receipt hash, and `seal` never ran. The doc comment above
/// promised the opposite -- that a model-authored receipt hash is "impossible
/// rather than merely rejected" -- so the type was making a claim its own
/// derive list falsified.
///
/// [`F2Matrix`](crate::f2::F2Matrix) in this crate already carries the same
/// lesson and solves it with `#[serde(try_from = ...)]`, reconstructing through
/// the checked constructor. That answer does not transfer here: verifying the
/// digest needs the [`CandidateMovePacket`] it was computed over, and a
/// `RoundRecord` does not carry one. There is nothing to check against, so the
/// honest move is to refuse the direction entirely.
///
/// Removing the derive is a *compile-time* fence, not a runtime one: any future
/// `from_str::<RoundRecord>` fails to build at its own call site. Nothing
/// deserialized one when this was removed -- every construction in the
/// workspace goes through `seal`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct RoundRecord {
    pub schema_version: String,
    pub round_index: u64,
    pub parent_state_ref: String,
    pub compiled_operation_ref: String,
    pub parse_result: ParseResult,
    pub fidelity_findings: Vec<Finding>,
    pub detector_findings: Vec<Finding>,
    pub local_replay_status: LocalReplayStatus,
    pub disposition: Disposition,
    pub successor_state_refs: Vec<String>,
    canonical_digest: String,
}

impl RoundRecord {
    pub const SCHEMA: &'static str = "round-record/v1";

    /// Domain tag for [`RoundRecord::canonical_digest`].
    ///
    /// The digest is an envelope over `{domain, payload}`, so the tag is part
    /// of the hashed bytes: a candidate packet and some other structure with
    /// identical fields cannot collide.
    pub const DIGEST_DOMAIN: &'static str = "omega.symbol_game.candidate_move.v1";

    /// The only way to obtain a `RoundRecord`.
    ///
    /// The digest is computed here over the candidate's canonical bytes; it is
    /// never accepted from a caller, which is what makes a model-authored
    /// receipt hash impossible rather than merely rejected.
    pub fn seal(
        candidate: &CandidateMovePacket,
        parse_result: ParseResult,
        fidelity_findings: Vec<Finding>,
        detector_findings: Vec<Finding>,
        local_replay_status: LocalReplayStatus,
        disposition: Disposition,
        successor_state_refs: Vec<String>,
    ) -> Result<Self, SealError> {
        // Through the kernel's canonical encoder, not `serde_json::to_vec`.
        //
        // `to_vec` emits fields in *declaration* order, while this host
        // advertises `omega-sorted-json-no-float-v1` and a verifier in another
        // language computes the sorted-key digest of the same packet. The two
        // disagree, so the digest was canonical in name only -- the exact
        // cross-language hazard `compile.rs` avoids by taking `executor_digest`
        // as a parameter rather than inventing one.
        //
        // Fallible rather than `unwrap_or_default()`: that collapsed every
        // serialization failure to the digest of the empty string, so an
        // unrepresentable packet produced a plausible-looking receipt hash
        // shared by every other unrepresentable packet.
        let payload = serde_json::to_value(candidate)
            .map_err(|source| SealError::NotRepresentable { source })?;
        let canonical_digest = canonical_id(Self::DIGEST_DOMAIN, &payload)
            .map_err(|source| SealError::NotCanonical { source })?;

        Ok(Self {
            schema_version: Self::SCHEMA.to_owned(),
            round_index: candidate.round_index,
            parent_state_ref: candidate.parent_state_ref.clone(),
            compiled_operation_ref: candidate.selected_operation_ref.clone(),
            parse_result,
            fidelity_findings,
            detector_findings,
            local_replay_status,
            disposition,
            successor_state_refs,
            canonical_digest,
        })
    }

    /// Host-computed; there is no setter.
    pub fn canonical_digest(&self) -> &str {
        &self.canonical_digest
    }

    pub fn authority_effect(&self) -> &'static str {
        "None"
    }
}

/// Why a search stopped.
///
/// The distinction merge spec acceptance criterion 14 turns on: a budget that
/// ran out is `BoundedWithOpenFrontier`, never `Exhausted`. Only a search that
/// actually inspected every branch may claim exhaustion.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StopReason {
    /// Every branch was inspected. A real claim about the whole space.
    Exhausted,
    /// Budget ran out, or branches remain unexplored.
    BoundedWithOpenFrontier,
    /// A terminal proposal was emitted.
    TerminalProposed,
}

impl StopReason {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Exhausted => "EXHAUSTED",
            Self::BoundedWithOpenFrontier => "BOUNDED_WITH_OPEN_FRONTIER",
            Self::TerminalProposed => "TERMINAL_PROPOSED",
        }
    }
}

/// Remaining search budget.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Budget {
    pub rounds_remaining: u64,
    pub branches_remaining: u64,
}

impl Budget {
    pub fn new(rounds: u64, branches: u64) -> Self {
        Self {
            rounds_remaining: rounds,
            branches_remaining: branches,
        }
    }

    pub fn is_exhausted(&self) -> bool {
        self.rounds_remaining == 0 || self.branches_remaining == 0
    }

    pub fn spend_round(&mut self) {
        self.rounds_remaining = self.rounds_remaining.saturating_sub(1);
    }
}

/// One immutable frontier state.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FrontierState {
    pub state_ref: String,
    pub parent_lineage: Vec<String>,
    pub claims: Vec<String>,
    pub obligations: Vec<Obligation>,
    pub findings: Vec<Finding>,
    pub surviving_branches: Vec<String>,
    pub pruned_branches: Vec<(String, String)>,
    pub budget: Budget,
    pub stop_reason: Option<StopReason>,
}

impl FrontierState {
    pub fn root(state_ref: &str, budget: Budget) -> Self {
        Self {
            state_ref: state_ref.to_owned(),
            parent_lineage: Vec::new(),
            claims: Vec::new(),
            obligations: Vec::new(),
            findings: Vec::new(),
            surviving_branches: Vec::new(),
            pruned_branches: Vec::new(),
            budget,
            stop_reason: None,
        }
    }

    /// Derive an immutable successor. The parent is never mutated, and lineage
    /// grows rather than being replaced, so a resumed run can still see how it
    /// got here.
    pub fn successor(&self, state_ref: &str) -> Self {
        let mut lineage = self.parent_lineage.clone();
        lineage.push(self.state_ref.clone());

        let mut next = self.clone();
        next.state_ref = state_ref.to_owned();
        next.parent_lineage = lineage;
        next.budget.spend_round();
        next.stop_reason = None;
        next
    }

    pub fn open_obligations(&self) -> Vec<&Obligation> {
        self.obligations.iter().filter(|o| !o.discharged).collect()
    }

    /// Classify a stop, given whether the search actually inspected everything.
    ///
    /// `all_branches_inspected` must come from the scheduler's own record, not
    /// from a model's assertion.
    pub fn classify_stop(&self, all_branches_inspected: bool) -> StopReason {
        if all_branches_inspected && !self.budget.is_exhausted() {
            StopReason::Exhausted
        } else {
            StopReason::BoundedWithOpenFrontier
        }
    }
}

/// The narrowest supported outcome, plus everything still open.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TerminalProposal {
    pub schema_version: String,
    pub state_ref: String,
    pub narrowest_claim: String,
    pub open_obligations: Vec<Obligation>,
    pub stop_reason: StopReason,
}

impl TerminalProposal {
    pub const SCHEMA: &'static str = "terminal-proposal/v1";

    /// Build a proposal, deriving the stop reason from the frontier.
    ///
    /// Takes `all_branches_inspected` rather than a [`StopReason`], because a
    /// caller-supplied reason was the one place the claim actually leaves the
    /// crate and nothing re-checked it. Acceptance criterion 14 turns on this:
    /// a budget-limited run must report `BoundedWithOpenFrontier` and never
    /// `Exhausted`, and [`FrontierState::classify_stop`] is the guard that
    /// enforces it. Passing the reason in meant the guard could be bypassed by
    /// not calling it.
    ///
    /// `Exhausted` is now underivable unless the frontier agrees: every branch
    /// inspected *and* the budget not spent.
    pub fn new(state: &FrontierState, narrowest_claim: &str, all_branches_inspected: bool) -> Self {
        let stop_reason = state.classify_stop(all_branches_inspected);
        Self {
            schema_version: Self::SCHEMA.to_owned(),
            state_ref: state.state_ref.clone(),
            narrowest_claim: narrowest_claim.to_owned(),
            open_obligations: state
                .obligations
                .iter()
                .filter(|o| !o.discharged)
                .cloned()
                .collect(),
            stop_reason,
        }
    }

    /// A proposal, never a decision. The outer host decides what to do with it.
    pub fn authority_effect(&self) -> &'static str {
        "None"
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn candidate() -> CandidateMovePacket {
        CandidateMovePacket::new("state-0", 17, "op@v1", MoveKind::Propose, "because")
    }

    #[test]
    fn a_candidate_carries_no_authority() {
        assert_eq!(candidate().authority_effect(), "None");
    }

    #[test]
    fn a_candidate_has_no_place_to_put_a_digest_or_verdict() {
        // The structural claim, checked against the serialized form: if a model
        // sets any of these, they are simply not part of the packet.
        let json = serde_json::to_value(candidate()).unwrap();
        let object = json.as_object().unwrap();
        for forbidden in [
            "canonical_digest",
            "verified",
            "admitted",
            "receipt",
            "authority_effect",
            "terminal_status",
            "outcome_root_sha256",
        ] {
            assert!(
                !object.contains_key(forbidden),
                "candidate exposes {forbidden}"
            );
        }
    }

    #[test]
    fn a_model_supplied_digest_field_is_refused_on_parse() {
        // This test used to be `..._is_dropped_on_parse`, and asserted that
        // deserialization silently ignores the smuggled keys. The property it
        // cares about -- a model cannot supply the host's digest -- survived
        // that, but only barely: the packet still parsed, and a reader who
        // wrote `canonical_digest` into it got a packet that looked accepted.
        //
        // With deny_unknown_fields the attempt is refused outright, which is
        // the stronger answer and the one the rest of this module already
        // gives. A field a producer believes is load-bearing must not turn out
        // to be inert.
        let smuggled = r#"{
            "schema_version": "candidate-move/v1",
            "parent_state_ref": "state-0",
            "round_index": 1,
            "selected_operation_ref": "op@v1",
            "move_kind": "Propose",
            "consumed_operand_refs": [],
            "public_rationale": "r",
            "proposed_claim_deltas": [],
            "witness_proposals": [],
            "evidence_requests": [],
            "objections": [],
            "child_obligations": [],
            "requested_reframe": null,
            "canonical_digest": "sha256:deadbeef",
            "verified": true
        }"#;
        let error = serde_json::from_str::<CandidateMovePacket>(smuggled)
            .expect_err("a packet claiming its own digest must be refused")
            .to_string();
        assert!(
            error.contains("unknown field"),
            "expected an unknown-field refusal, got {error}"
        );

        // And the property that refusal protects, still asserted directly:
        // strip the smuggled keys and the host computes the digest itself.
        let mut honest: serde_json::Value =
            serde_json::from_str(smuggled).expect("the fixture is JSON");
        let object = honest.as_object_mut().expect("an object");
        object.remove("canonical_digest");
        object.remove("verified");
        let parsed: CandidateMovePacket = serde_json::from_value(honest)
            .expect("the fixture parses once the smuggled keys are gone");
        let round = RoundRecord::seal(
            &parsed,
            ParseResult::Pass,
            vec![],
            vec![],
            LocalReplayStatus::NotRun,
            Disposition::Bounded,
            vec![],
        )
        .expect("the fixture packet is canonical");
        assert_ne!(round.canonical_digest(), "sha256:deadbeef");
        assert!(round.canonical_digest().starts_with("sha256:"));
    }

    #[test]
    fn the_host_digest_is_computed_from_the_candidate() {
        let round = RoundRecord::seal(
            &candidate(),
            ParseResult::Pass,
            vec![],
            vec![],
            LocalReplayStatus::Pass,
            Disposition::AcceptedDelta,
            vec!["state-1".to_owned()],
        )
        .expect("the fixture packet is canonical");
        assert!(round.canonical_digest().starts_with("sha256:"));
        assert_eq!(round.canonical_digest().len(), "sha256:".len() + 64);
        assert_eq!(round.round_index, 17);
    }

    #[test]
    fn two_different_candidates_seal_to_different_digests() {
        let a = RoundRecord::seal(
            &candidate(),
            ParseResult::Pass,
            vec![],
            vec![],
            LocalReplayStatus::NotRun,
            Disposition::Bounded,
            vec![],
        )
        .expect("the fixture packet is canonical");
        let mut other = candidate();
        other.public_rationale = "different".to_owned();
        let b = RoundRecord::seal(
            &other,
            ParseResult::Pass,
            vec![],
            vec![],
            LocalReplayStatus::NotRun,
            Disposition::Bounded,
            vec![],
        )
        .expect("the fixture packet is canonical");
        assert_ne!(a.canonical_digest(), b.canonical_digest());
    }

    #[test]
    fn identical_candidates_seal_to_identical_digests() {
        let a = RoundRecord::seal(
            &candidate(),
            ParseResult::Pass,
            vec![],
            vec![],
            LocalReplayStatus::NotRun,
            Disposition::Bounded,
            vec![],
        )
        .expect("the fixture packet is canonical");
        let b = RoundRecord::seal(
            &candidate(),
            ParseResult::Pass,
            vec![],
            vec![],
            LocalReplayStatus::NotRun,
            Disposition::Bounded,
            vec![],
        )
        .expect("the fixture packet is canonical");
        assert_eq!(a.canonical_digest(), b.canonical_digest());
    }

    #[test]
    fn a_successor_preserves_lineage_and_leaves_the_parent_alone() {
        let root = FrontierState::root("state-0", Budget::new(10, 4));
        let child = root.successor("state-1");
        let grandchild = child.successor("state-2");

        assert_eq!(root.parent_lineage, Vec::<String>::new());
        assert_eq!(child.parent_lineage, vec!["state-0".to_owned()]);
        assert_eq!(
            grandchild.parent_lineage,
            vec!["state-0".to_owned(), "state-1".to_owned()]
        );
        assert_eq!(
            root.budget.rounds_remaining, 10,
            "parent budget is untouched"
        );
        assert_eq!(grandchild.budget.rounds_remaining, 8);
    }

    #[test]
    fn an_exhausted_budget_is_bounded_not_exhaustive() {
        // Acceptance criterion 14.
        let state = FrontierState::root("s", Budget::new(0, 4));
        assert_eq!(
            state.classify_stop(true),
            StopReason::BoundedWithOpenFrontier
        );
        assert_eq!(
            state.classify_stop(false),
            StopReason::BoundedWithOpenFrontier
        );
    }

    #[test]
    fn only_a_fully_inspected_search_may_claim_exhaustion() {
        let state = FrontierState::root("s", Budget::new(5, 4));
        assert_eq!(
            state.classify_stop(false),
            StopReason::BoundedWithOpenFrontier
        );
        assert_eq!(state.classify_stop(true), StopReason::Exhausted);
    }

    #[test]
    fn a_terminal_proposal_carries_the_open_obligations_forward() {
        let mut state = FrontierState::root("s", Budget::new(1, 1));
        state.obligations = vec![
            Obligation {
                id: "o1".into(),
                description: "prove it".into(),
                discharged: false,
            },
            Obligation {
                id: "o2".into(),
                description: "done".into(),
                discharged: true,
            },
        ];

        let proposal = TerminalProposal::new(
            &state,
            "holds on the declared fixture only",
            false, // branches remain uninspected
        );
        assert_eq!(proposal.open_obligations.len(), 1);
        assert_eq!(proposal.open_obligations[0].id, "o1");
        assert_eq!(proposal.stop_reason, StopReason::BoundedWithOpenFrontier);
        assert_eq!(proposal.authority_effect(), "None");
    }

    #[test]
    fn a_spent_budget_cannot_propose_exhausted() {
        // Acceptance criterion 14, at the point the claim leaves the crate.
        // Previously the caller passed the reason in, so `Exhausted` could be
        // published on a budget-limited run by simply asserting it.
        let mut state = FrontierState::root("s0", Budget::new(2, 2));
        while !state.budget.is_exhausted() {
            state.budget.spend_round();
        }

        let proposal = TerminalProposal::new(&state, "claim", true);
        assert_eq!(
            proposal.stop_reason,
            StopReason::BoundedWithOpenFrontier,
            "a spent budget is bounded, not exhaustive, even with every branch inspected"
        );
    }

    #[test]
    fn exhausted_requires_both_the_frontier_and_the_budget_to_agree() {
        let state = FrontierState::root("s0", Budget::new(8, 8));
        assert_eq!(
            TerminalProposal::new(&state, "claim", true).stop_reason,
            StopReason::Exhausted
        );
        assert_eq!(
            TerminalProposal::new(&state, "claim", false).stop_reason,
            StopReason::BoundedWithOpenFrontier
        );
    }

    #[test]
    fn round_trip_through_json_preserves_the_candidate() {
        let original = candidate();
        let encoded = serde_json::to_string(&original).unwrap();
        let decoded: CandidateMovePacket = serde_json::from_str(&encoded).unwrap();
        assert_eq!(original, decoded);
    }
    #[test]
    fn a_round_record_cannot_be_deserialized_at_all() {
        // A caller-supplied `canonical_digest` used to deserialize cleanly --
        // a private field is no obstacle to serde, whose derive constructs the
        // struct field by field inside this very module. `seal` never ran.
        //
        // The fence is the absent derive, so the check has to be on the derive
        // itself: with `Deserialize` back, `from_value::<RoundRecord>` compiles
        // again and the forgery is available again. Reading this file is ugly,
        // and it is the only assertion available -- a compile-failure is not
        // something a passing test can express.
        let source = include_str!("packets.rs");
        let marker = "pub struct RoundRecord {";
        let start = source.find(marker).expect("RoundRecord is defined here");
        let derive_line = source[..start]
            .lines()
            .rev()
            .find(|line| line.trim_start().starts_with("#[derive("))
            .expect("RoundRecord carries a derive attribute");
        assert!(
            derive_line.contains("Serialize"),
            "a round record must still serialize; the receipt goes out on the wire"
        );
        assert!(
            !derive_line.contains("Deserialize"),
            "RoundRecord derives Deserialize ({derive_line:?}), which rebuilds it \
             field by field and accepts a caller-supplied canonical_digest. The \
             type's own doc calls that impossible. Either the derive goes or the \
             doc does, and the derive is the one that is wrong."
        );
    }
}
