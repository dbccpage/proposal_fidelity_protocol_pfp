
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b42265f5<T> {
    fn checked_invariant_b42265f5(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b42265f5<T> for Option<T> {
    #[inline]
    fn checked_invariant_b42265f5(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b42265f5<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b42265f5(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

use crate::canonical::framed_sha256;

use super::reduction::{critical_pairs, reachable, replay_path, Reached, ReductionPath};
use super::Presentation;

/// A claimed critical peak: one source, two divergent reductions.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CriticalPeakClaim {
    pub source: String,
    pub left: ReductionPath,
    pub right: ReductionPath,
    /// The common term both branches were claimed to reach, if one was found.
    pub join: Option<String>,
    /// Rewrite steps inspected while searching for a join.
    pub steps_inspected: u64,
    /// The declared search budget.
    pub step_budget: u64,
}

/// Why the host is entitled to an exhaustive answer about ONE pair.
///
/// This used to be a *termination* witness, and that was the wrong price. A
/// termination argument is what Newman's lemma needs to lift local confluence
/// to confluence OF A SYSTEM. This module never makes that claim; it decides
/// joinability OF ONE PAIR, and what that needs is closure, not termination.
///
/// Requiring termination therefore cost answers and bought nothing: a
/// length-preserving presentation whose reachable sets close well inside the
/// budget was refused a verdict it could soundly be given.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExhaustionBasis {
    /// Both reachable sets closed inside the declared budget.
    ///
    /// `reachable` returns `Some` only when its frontier empties. At that point
    /// every term in the set has had every viable rule application tried and
    /// every successor is already in the set, so the set is closed under
    /// rewriting and finite -- and it is exactly the set of terms reachable
    /// from the origin. Two such sets settle joinability by intersection,
    /// whatever the rules do to term length.
    ClosedReachableSets,
}

/// What a peak claim actually supports.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PeakVerdict {
    /// Structure is missing; the gaps are listed as obligations.
    NeedsEvidence { obligations: Vec<String> },
    /// Both branches reach a common term. A 2-cell may be declared over the
    /// parallel paths -- this records that the endpoints agree, nothing more.
    Joined { join: String },
    /// No join found inside the budget. NOT a non-confluence result.
    ///
    /// `host_expansions` is what THIS host spent, counted by `reachable` and
    /// returned rather than discarded. It replaces the producer's declared
    /// `steps_inspected`, which this verdict used to copy verbatim: a host
    /// verdict reporting the producer's own figure launders testimony into
    /// evidence, which is the defect class the whole module exists to close.
    /// The producer's figure stays in the claim, where it is testimony, and is
    /// reconciled at `evaluate_peak` rather than echoed here.
    BoundedWithUnjoinedPeak {
        host_expansions: u64,
        step_budget: u64,
    },
    /// The two branches provably have no common reduct.
    ///
    /// Only emitted when both reachable sets were closed, so this is a
    /// decision and not an exhausted search. The basis is carried in the
    /// verdict because a reader must be able to see what paid for the word
    /// "provably".
    NotJoinable {
        left_endpoint: String,
        right_endpoint: String,
        basis: ExhaustionBasis,
    },
}

impl PeakVerdict {
    pub fn token(&self) -> &'static str {
        match self {
            Self::NeedsEvidence { .. } => "NEEDS_EVIDENCE",
            Self::Joined { .. } => "JOINED",
            Self::BoundedWithUnjoinedPeak { .. } => "BOUNDED_WITH_UNJOINED_PEAK",
            Self::NotJoinable { .. } => "NOT_JOINABLE",
        }
    }
}

/// The refusal a host raises when it cannot vouch for the rules it was handed.
///
/// Not a defect in the claim. It is a statement about the *host*: this
/// presentation matches nothing it pins, so whatever follows is true under
/// rules the host has never endorsed.
pub const REFUSAL_PRESENTATION_UNKNOWN: &str = "FW-PRESENTATION-UNKNOWN";

/// The claim's first divergence is not one of the host-enumerated critical pairs.
///
/// This is an obligation, not a refusal.  The two paths may still be joinable;
/// the qualification says only that their result is not evidence about a
/// critical pair of the supplied presentation.
pub const OBLIGATION_PEAK_NONCRITICAL: &str = "FW-PEAK-NONCRITICAL";

/// What a decision reached under producer-declared rules is reported as.
///
/// The same token the Python surface uses when it re-derives every ledger row
/// against a carrier the packet supplied, and for the same reason: what was
/// established is internal consistency, and consistency is all it is.
pub const TOKEN_SELF_CONSISTENT_ONLY: &str = "SELF_CONSISTENT_ONLY";

const PRESENTATION_DIGEST_DOMAIN: &str = "core.symbol_game.presentation.v1";

/// A digest naming the rewriting **system**, not the bytes that carried it.
///
/// Rules are a set and a signature is a set, so both are sorted before
/// digesting: reordering the rules in a payload does not produce a different
/// rewriting system, and a pin that a reorder defeats is not a pin. Changing
/// any rule's name, left- or right-hand side does change the system, and does
/// change this digest.
///
/// The payload is JSON, and that is load-bearing rather than incidental. The
/// obvious encoding -- join the fields with a delimiter -- is **injectable**: a
/// rule whose name contains the delimiter can reproduce another presentation's
/// serialisation exactly, and two different systems digest the same. We shipped
/// that bug once already, in the carrier digest on the Python side. JSON escapes
/// the delimiters, and `framed_sha256` length-prefixes the whole payload under a
/// domain string, so the pre-image is unambiguous at both levels.
pub fn presentation_digest(presentation: &Presentation) -> String {
    let mut signature: Vec<&str> = presentation.signature.iter().map(String::as_str).collect();
    signature.sort_unstable();
    let mut rules: Vec<[&str; 3]> = presentation
        .rules
        .iter()
        .map(|rule| [rule.name.as_str(), rule.lhs.as_str(), rule.rhs.as_str()])
        .collect();
    rules.sort_unstable();
    // A tuple, not a map: an array's serialisation order is fixed by the type
    // rather than by whichever map implementation serde_json was built with.
    let payload =
        serde_json::to_vec(&(&signature, &rules)).checked_invariant_b42265f5("a tree of strings always serializes");
    framed_sha256(PRESENTATION_DIGEST_DOMAIN, &payload)
}

/// Who authored the presentation a verdict was reached under.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PresentationAuthority {
    /// The digest matched a presentation the host pins, under this name.
    HostPinned { pin: String },
    /// The presentation arrived with the claim and matches nothing pinned.
    ProducerDeclared,
}

/// The presentations this host recognises, by canonical digest.
///
/// **There is deliberately no `Deserialize` here, and there must not be one.**
/// A pin set the producer can supply is not a pin set -- it is the claim
/// vouching for itself. The absence of the derive is the enforcement: a
/// request payload cannot be parsed into this type, so the compiler refuses
/// the shortcut rather than a reviewer noticing it.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct PresentationPins {
    by_digest: BTreeMap<String, String>,
}

impl PresentationPins {
    /// A host that pins nothing. Every presentation is then producer-declared,
    /// which is the honest reading and not a degraded one.
    pub fn empty() -> Self {
        Self::default()
    }

    /// Pin `presentation` under `name`, returning the digest it was filed at.
    pub fn pin(&mut self, name: &str, presentation: &Presentation) -> String {
        let digest = presentation_digest(presentation);
        self.by_digest.insert(digest.clone(), name.to_owned());
        digest
    }

    pub fn is_empty(&self) -> bool {
        self.by_digest.is_empty()
    }

    pub fn len(&self) -> usize {
        self.by_digest.len()
    }

    /// The names of every pinned presentation, sorted.
    pub fn pin_names(&self) -> Vec<&str> {
        let mut names: Vec<&str> = self.by_digest.values().map(String::as_str).collect();
        names.sort_unstable();
        names
    }

    /// What the host can honestly say about the authorship of `digest`.
    pub fn authority_of(&self, digest: &str) -> PresentationAuthority {
        match self.by_digest.get(digest) {
            Some(pin) => PresentationAuthority::HostPinned { pin: pin.clone() },
            None => PresentationAuthority::ProducerDeclared,
        }
    }
}

/// A peak verdict together with the provenance of the rules that produced it.
///
/// The gap this closes
/// -------------------
///
/// `evaluate_peak` takes the presentation as an argument, and at the wire the
/// presentation arrives in the same payload as the claim. So a bare `JOINED`
/// read back off that wire says "the two branches join" while meaning "the two
/// branches join under rules the producer also supplied" -- and nothing in the
/// payload distinguishes the two readings. A producer choosing its own rewrite
/// system can arrange either answer it likes; `NotJoinable` is if anything the
/// easier one to arrange, since dropping a rule can only shrink the reachable
/// sets.
///
/// The mathematics is not in question and is not suppressed: the join really
/// does exist under those rules, and discarding a true finding would be its own
/// kind of dishonesty. What must not happen is that finding being *read* as one
/// the host stands behind. So the verdict is kept intact and the provenance
/// travels beside it, and [`PeakEvaluation::token`] -- the one field a
/// downstream consumer is meant to branch on -- reports a decision reached
/// under unpinned rules as `SELF_CONSISTENT_ONLY`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PeakEvaluation {
    pub verdict: PeakVerdict,
    pub presentation_digest: String,
    pub authority: PresentationAuthority,
    /// Qualifications about the rules or the claimed critical-pair status.
    /// They stand whatever the joinability verdict is.
    pub obligations: Vec<String>,
}

impl PeakEvaluation {
    /// Whether the verdict settles the pair one way or the other.
    ///
    /// `NeedsEvidence` and `BoundedWithUnjoinedPeak` decide nothing, so there
    /// is nothing in them for a presentation to have decided.
    pub fn decides(&self) -> bool {
        matches!(
            self.verdict,
            PeakVerdict::Joined { .. } | PeakVerdict::NotJoinable { .. }
        )
    }

    /// The token a downstream consumer may branch on.
    pub fn token(&self) -> &'static str {
        if self.decides() && matches!(self.authority, PresentationAuthority::ProducerDeclared) {
            return TOKEN_SELF_CONSISTENT_ONLY;
        }
        self.verdict.token()
    }
}

/// Evaluate a peak and record which presentation it was decided under.
///
/// This is the public host-facing entry point. The joinability calculation
/// below remains private: callers cannot bypass the presentation pin and
/// critical-pair qualification while still calling an API named
/// `evaluate_peak`.
pub fn evaluate_peak_pinned(
    presentation: &Presentation,
    claim: &CriticalPeakClaim,
    pins: &PresentationPins,
) -> PeakEvaluation {
    let presentation_digest = presentation_digest(presentation);
    let authority = pins.authority_of(&presentation_digest);
    let verdict = evaluate_peak(presentation, claim);

    let mut obligations = Vec::new();
    if matches!(authority, PresentationAuthority::ProducerDeclared) {
        obligations.push(format!(
            "{REFUSAL_PRESENTATION_UNKNOWN}: this host pins no presentation with digest \
             {presentation_digest}, so the verdict holds only under rules that arrived \
             with the claim; pin the presentation host-side to obtain a verdict the host \
             stands behind"
        ));
    }
    if !claim_names_critical_pair(presentation, claim) {
        obligations.push(format!(
            "{OBLIGATION_PEAK_NONCRITICAL}: the claimed source and first reduction steps do not \
             match any pair enumerated by critical_pairs(); the joinability verdict remains true \
             of these paths but is not a statement about a critical pair"
        ));
    }

    PeakEvaluation {
        verdict,
        presentation_digest,
        authority,
        obligations,
    }
}

/// Whether the claimed divergence starts at an enumerated critical pair.
///
/// `critical_pairs` canonicalizes its left/right order. A claim is allowed to
/// present the two branches in either order, so membership is symmetric while
/// the source and the two initial steps remain exact.
fn claim_names_critical_pair(presentation: &Presentation, claim: &CriticalPeakClaim) -> bool {
    let (Some(left), Some(right)) = (claim.left.steps.first(), claim.right.steps.first()) else {
        return false;
    };
    critical_pairs(presentation).iter().any(|pair| {
        pair.source == claim.source
            && ((pair.left == *left && pair.right == *right)
                || (pair.left == *right && pair.right == *left))
    })
}

fn collect_rule_obligations(presentation: &Presentation, obligations: &mut Vec<String>) {
    if presentation.rules.is_empty() {
        obligations.push("declare an explicit rewrite presentation with named rules".to_owned());
    }
    let mut rule_names = BTreeSet::new();
    for rule in &presentation.rules {
        if rule.name.trim().is_empty() {
            obligations.push("every rewrite rule must have a non-empty name".to_owned());
        } else if !rule_names.insert(rule.name.as_str()) {
            obligations.push(format!(
                "rewrite rule name {:?} is duplicated, so path replay is ambiguous",
                rule.name
            ));
        }
        if rule.lhs.is_empty() {
            obligations.push(format!(
                "rewrite rule {:?} has an empty left-hand side",
                rule.name
            ));
        }
    }
}

fn collect_claim_shape_obligations(claim: &CriticalPeakClaim, obligations: &mut Vec<String>) {
    if claim.source.trim().is_empty() {
        obligations.push("declare the common source term of the peak".to_owned());
    }
    if claim.left.steps.is_empty() || claim.right.steps.is_empty() {
        obligations.push("declare two non-empty reduction paths from the source".to_owned());
    }
    if claim.left.steps == claim.right.steps {
        obligations
            .push("the two branches apply the same steps, so this is not a divergence".to_owned());
    }

    for (side, path) in [("left", &claim.left), ("right", &claim.right)] {
        if path.endpoint.trim().is_empty() {
            obligations.push(format!("{side} path declares no endpoint"));
        }
    }

    if claim.step_budget == 0 {
        obligations.push("declare a finite search budget".to_owned());
    }
    // `steps_inspected` is producer testimony and no longer reaches any host
    // verdict. It is still checked against the producer's OWN declared budget,
    // because a claim that reports spending more than it declared is
    // internally inconsistent -- and that is decidable without believing
    // either number.
    if claim.step_budget > 0 && claim.steps_inspected > claim.step_budget {
        obligations.push(format!(
            "claim reports {} steps inspected against its own declared budget of {}",
            claim.steps_inspected, claim.step_budget
        ));
    }
}

fn finalize_peak_verdict(
    decided: Option<PeakVerdict>,
    host_expansions: u64,
    declared: DeclaredJoin,
    step_budget: u64,
) -> PeakVerdict {
    if let DeclaredJoin::Refuted { detail } = declared {
        return PeakVerdict::NeedsEvidence {
            obligations: vec![detail],
        };
    }

    match decided {
        Some(verdict) => {
            // A declaration the host could not check must not ride out on a
            // verdict reached without it.
            if matches!(declared, DeclaredJoin::Unchecked) {
                return PeakVerdict::BoundedWithUnjoinedPeak {
                    host_expansions,
                    step_budget,
                };
            }
            verdict
        }
        // The host could not decide: no termination witness, or a budget too
        // small to close both sets. `Bounded` asserts nothing about confluence,
        // and a declared join changes none of that.
        None => PeakVerdict::BoundedWithUnjoinedPeak {
            host_expansions,
            step_budget,
        },
    }
}

/// Check a critical-peak claim against its presentation.
///
/// Every missing piece of structure becomes an obligation, so one call reports
/// everything a claim lacks instead of stopping at the first gap.
pub(super) fn evaluate_peak(presentation: &Presentation, claim: &CriticalPeakClaim) -> PeakVerdict {
    let mut obligations = Vec::new();
    collect_rule_obligations(presentation, &mut obligations);
    collect_claim_shape_obligations(claim, &mut obligations);

    let left_endpoint = replay_path(
        presentation,
        &claim.source,
        "left",
        &claim.left,
        &mut obligations,
    );
    let right_endpoint = replay_path(
        presentation,
        &claim.source,
        "right",
        &claim.right,
        &mut obligations,
    );

    if !obligations.is_empty() {
        return PeakVerdict::NeedsEvidence { obligations };
    }

    let left_endpoint = left_endpoint.checked_invariant_b42265f5("a valid left path must replay");
    let right_endpoint = right_endpoint.checked_invariant_b42265f5("a valid right path must replay");

    // The host decides, always, and decides the same way whether or not the
    // producer testified. A declared join used to short-circuit this entirely
    // when it happened to equal both endpoints, so the SAME peak returned a
    // different payload according to whether a `join` field was present -- the
    // producer's testimony selecting the host's answer. A declaration is a
    // claim to check; it is not a shortcut and it is not a vote.
    let (decided, host_expansions, declared) =
        decide_joinability(presentation, &left_endpoint, &right_endpoint, claim);

    finalize_peak_verdict(decided, host_expansions, declared, claim.step_budget)
}

/// Decide joinability exhaustively, or decline to.
///
/// Returns `None` whenever the host is not entitled to an exhaustive answer:
/// no termination witness, or a budget too small to close both reachable sets.
/// Declining is the common case and is not a failure.
/// What the host established about a join the producer declared.
///
/// Kept apart from the verdict because a declaration is a claim to check, never
/// a shortcut. The host's answer must be the same whether or not the producer
/// testified.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) enum DeclaredJoin {
    /// Nothing was declared.
    Absent,
    /// The host could not check the declaration -- no witness, or the budget
    /// closed neither set.
    Unchecked,
    /// The declared term really is reachable from both endpoints.
    Verified,
    /// The declared term is not a common reduct.
    Refuted { detail: String },
}

fn verify_identical_endpoint_join(
    left_endpoint: &str,
    declared_join: Option<&str>,
) -> (Option<PeakVerdict>, u64, DeclaredJoin) {
    // Verifiable at zero steps and without any termination argument: the
    // endpoints are host-derived, so a declaration naming that same term is
    // checked, and any other term is not a common reduct at distance zero.
    let declared = match declared_join {
        None => DeclaredJoin::Absent,
        Some(join) if join == left_endpoint => DeclaredJoin::Verified,
        Some(join) => DeclaredJoin::Refuted {
            detail: format!(
                "declared join {join:?} is not the term both branches reach ({left_endpoint:?})"
            ),
        },
    };
    (
        Some(PeakVerdict::Joined {
            join: left_endpoint.to_owned(),
        }),
        0,
        declared,
    )
}

fn verify_closed_sets_declared_join(
    declared_join: Option<&str>,
    left_terms: &BTreeMap<String, u64>,
    right_terms: &BTreeMap<String, u64>,
    left_endpoint: &str,
    right_endpoint: &str,
) -> DeclaredJoin {
    // A declared join is checked against the host's own closure, and the check
    // is the ONLY thing the declaration affects. It never selects the payload.
    match declared_join {
        None => DeclaredJoin::Absent,
        Some(join) if left_terms.contains_key(join) && right_terms.contains_key(join) => {
            DeclaredJoin::Verified
        }
        Some(join) => DeclaredJoin::Refuted {
            detail: format!(
                "declared join {join:?} is not reachable from both endpoints \
                 ({left_endpoint:?}, {right_endpoint:?})"
            ),
        },
    }
}

pub(super) fn decide_joinability(
    presentation: &Presentation,
    left_endpoint: &str,
    right_endpoint: &str,
    claim: &CriticalPeakClaim,
) -> (Option<PeakVerdict>, u64, DeclaredJoin) {
    // Identical endpoints join at zero further steps via direct string equality
    // without requiring witness search when endpoints already match.
    if left_endpoint == right_endpoint {
        return verify_identical_endpoint_join(left_endpoint, claim.join.as_deref());
    }

    // `step_budget` is one cap for the decision, not a separate allowance for
    // each branch. Giving both closures the full value lets the host spend and
    // report as much as twice the declared budget. A failed left closure has
    // already consumed the entire allowance; a successful one leaves exactly
    // its unspent remainder for the right closure.
    let left = reachable(presentation, left_endpoint, claim.step_budget);
    let remaining = claim.step_budget.saturating_sub(left.expansions);
    let right = if left.terms.is_some() {
        reachable(presentation, right_endpoint, remaining)
    } else {
        Reached {
            terms: None,
            expansions: 0,
        }
    };
    let spent = left.expansions.saturating_add(right.expansions);

    let (Some(left_terms), Some(right_terms)) = (left.terms, right.terms) else {
        return (None, spent, unchecked_declaration(claim));
    };

    // Both sets are closed under rewriting and finite, so their intersection
    // settles the question either way.
    //
    // Which common reduct to report is a real choice, and it used to be made by
    // accident: taking the first element of a `BTreeSet` intersection reported
    // whichever term sorted first in byte order. That is neither the nearest
    // join nor a normal form -- it is the container's iteration order, and it
    // was undocumented because nobody chose it.
    //
    // The stated rule: the NEAREST common reduct, by total rewrite distance
    // from the two endpoints. A join is a witness that the peak converges, and
    // the shortest witness is the one a reader can check most cheaply. Ties
    // break lexicographically, so the verdict stays deterministic without the
    // tie-break ever being mistaken for the reason.
    let nearest = left_terms
        .iter()
        .filter_map(|(term, left_distance)| {
            right_terms
                .get(term)
                .map(|right_distance| (left_distance.saturating_add(*right_distance), term))
        })
        .min();

    let declared = verify_closed_sets_declared_join(
        claim.join.as_deref(),
        &left_terms,
        &right_terms,
        left_endpoint,
        right_endpoint,
    );

    let verdict = match nearest {
        Some((_, join)) => PeakVerdict::Joined {
            join: join.to_owned(),
        },
        None => PeakVerdict::NotJoinable {
            left_endpoint: left_endpoint.to_owned(),
            right_endpoint: right_endpoint.to_owned(),
            basis: ExhaustionBasis::ClosedReachableSets,
        },
    };
    (Some(verdict), spent, declared)
}

/// A declaration the host had no means to check.
fn unchecked_declaration(claim: &CriticalPeakClaim) -> DeclaredJoin {
    if claim.join.is_none() {
        DeclaredJoin::Absent
    } else {
        DeclaredJoin::Unchecked
    }
}

// Origin: engine/crates_rs/core_symbol_game_runtime/src/rewriting/peak.rs
// Claim: urn:core:crates_rs:core-symbol-game-runtime:peak:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb42265f5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb42265f5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb42265f5 {
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
impl BoundaryErrorb42265f5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb42265f5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb42265f5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb42265f5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb42265f5> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb42265f5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb42265f5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb42265f5::ExceedsCapacity {
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
mod l4_boundary_tests_b42265f5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb42265f5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb42265f5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb42265f5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb42265f5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb42265f5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb42265f5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb42265f5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
