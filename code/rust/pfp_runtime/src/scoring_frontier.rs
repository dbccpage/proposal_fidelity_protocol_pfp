//! Discrete coboundary scoring, frontier ranking, and residual evaluation.
//!
//! **Exact throughout.** Masses, drops, costs and efficiencies are `BigRational`,
//! never `f64`. This is not stylistic: the module previously decided
//! `is_exact_candidate` — whether the residual has actually vanished, which is
//! what separates an accepted repair from a refusal — with the test
//! `post_norm < 1e-9`. A residual of `5e-10` counted as exact. The sibling
//! module states the rule this violates: `BigRational` is used "precisely so
//! that 'the objectives are equal' is a decision rather than a tolerance".
//!
//! Two further consequences of going exact, both improvements in their own
//! right:
//!
//! - An illegal proposal has **no** efficiency (`None`), where it used to have
//!   `f64::NEG_INFINITY`. There is no negative infinity in ℚ, and the sentinel
//!   was standing in for "this does not rank" — which `Option` says directly.
//! - Ranking is a total order. `BigRational: Ord`, so the comparisons are plain
//!   `cmp` instead of `partial_cmp(..).unwrap_or(Equal)` — a fallback that
//!   silently treated an incomparable pair as a tie.
//!
//! Exact values cross the wire as strings (`"3/4"`), never JSON numbers. A JSON
//! number is a float in most readers, and the canonicalization profile
//! (`core-sorted-json-no-float-v1`) refuses floats.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b60d41ac<T> {
    fn checked_invariant_b60d41ac(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b60d41ac<T> for Option<T> {
    #[inline]
    fn checked_invariant_b60d41ac(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b60d41ac<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b60d41ac(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::{BTreeMap, BTreeSet};

use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Serialize};
use thiserror::Error;

use core_kernel::{exact_wire, exact_wire_option, exact_wire_pairs, Exact};

pub const REFUSAL_AUTHORITY_NON_NONE: &str = "AUTHORITY_EFFECT_NON_NONE";
pub const REFUSAL_EXACT_WITHOUT_DUAL: &str = "EXACT_WITHOUT_DUAL";
pub const REFUSAL_ILLEGAL_PROPOSAL: &str = "ILLEGAL_PROPOSAL";
pub const REFUSAL_NEGATIVE_MAGNITUDE: &str = "NEGATIVE_MAGNITUDE";
pub const REFUSAL_PROSE_PROMPT_REFUSED: &str = "PROSE_PROMPT_REFUSED";

/// Why a scoring call refused.
///
/// Typed rather than `Result<_, String>`, matching the rest of the crate: a
/// caller can match on the reason instead of parsing prose, and adding a case
/// is a compile error at every match site.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ScoringError {
    #[error("{REFUSAL_NEGATIVE_MAGNITUDE}: {field} is negative")]
    NegativeMagnitude { field: &'static str },

    #[error("{REFUSAL_NEGATIVE_MAGNITUDE}: magnitude for {key:?} is negative")]
    NegativeMagnitudeAt { key: String },
}

/// A candidate repair, as proposed. Carries no verdict and no authority.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateProposal {
    pub proposal_id: String,
    pub repaired_obstruction_ids: Vec<String>,
    #[serde(with = "exact_wire_pairs")]
    pub cochain_delta: Vec<(String, Exact)>,
    #[serde(with = "exact_wire")]
    pub structural_cost: Exact,
    pub kill_triggers: Vec<String>,
    pub admitted_constructors_used: Vec<String>,
    pub dual_witness_ref: Option<String>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CoboundaryScoreResult {
    pub proposal_id: String,
    #[serde(with = "exact_wire")]
    pub prior_residual_norm: Exact,
    #[serde(with = "exact_wire")]
    pub post_residual_norm: Exact,
    #[serde(with = "exact_wire")]
    pub residual_drop: Exact,
    #[serde(with = "exact_wire")]
    pub structural_cost: Exact,
    /// `None` when the proposal is illegal: it does not rank at all, rather
    /// than ranking infinitely badly.
    #[serde(with = "exact_wire_option")]
    pub normalized_efficiency: Option<Exact>,
    pub is_legal: bool,
    /// The residual is **exactly** zero and a dual witness is named. Decided by
    /// `is_zero()`, never by a tolerance.
    pub is_exact_candidate: bool,
    pub dual_witness_ref: Option<String>,
    pub refusal_reason: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResidualDropV1 {
    #[serde(with = "exact_wire")]
    pub core_mass: Exact,
    #[serde(with = "exact_wire")]
    pub residual_mass: Exact,
    #[serde(with = "exact_wire_option")]
    pub delta: Option<Exact>,
    #[serde(with = "exact_wire_option")]
    pub relative_drop: Option<Exact>,
    pub eliminated_ids: Vec<String>,
    pub opened_ids: Vec<String>,
    pub retained_ids: Vec<String>,
    #[serde(with = "exact_wire")]
    pub cost: Exact,
    #[serde(with = "exact_wire_option")]
    pub efficiency: Option<Exact>,
    pub residual_colour: String,
    pub dual_witness_present: bool,
    pub legal: bool,
    pub refusal_code: Option<String>,
}

/// Mass of a set of obstruction ids, counted once each.
pub fn mass_from_ids(ids: &[String], unit: &Exact) -> Exact {
    let distinct: BTreeSet<&String> = ids.iter().collect();
    Exact::from_integer(distinct.len().into()) * unit
}

pub fn mass_from_magnitudes(magnitudes: &BTreeMap<String, Exact>) -> Result<Exact, ScoringError> {
    let mut total = Exact::zero();
    for (key, value) in magnitudes {
        if value.is_negative() {
            return Err(ScoringError::NegativeMagnitudeAt { key: key.clone() });
        }
        total += value;
    }
    Ok(total)
}

/// `(delta, relative_drop, efficiency)` for a legal proposal.
///
/// `relative_drop` is `None` when `core_mass` is zero: there is nothing to be
/// a fraction of, and reporting `0` would claim a measured result where none
/// exists.
pub fn residual_drop_mass(
    core_mass: &Exact,
    residual_mass: &Exact,
    cost: &Exact,
) -> Result<(Exact, Option<Exact>, Exact), ScoringError> {
    if core_mass.is_negative() {
        return Err(ScoringError::NegativeMagnitude {
            field: "core_mass",
        });
    }
    if residual_mass.is_negative() {
        return Err(ScoringError::NegativeMagnitude {
            field: "residual_mass",
        });
    }
    if cost.is_negative() {
        return Err(ScoringError::NegativeMagnitude { field: "cost" });
    }

    let delta = core_mass - residual_mass;
    let relative = if core_mass.is_zero() {
        None
    } else {
        Some(&delta / core_mass)
    };
    // `1 + cost` is never zero because cost is non-negative, so this division
    // is total.
    let efficiency = &delta / (Exact::one() + cost);
    Ok((delta, relative, efficiency))
}

pub fn residual_colour_from_mass(
    residual_mass: &Exact,
    dual_witness_present: bool,
    open_ids: &[String],
) -> Result<String, ScoringError> {
    if residual_mass.is_negative() {
        return Err(ScoringError::NegativeMagnitude {
            field: "residual_mass",
        });
    }
    if residual_mass.is_zero() && open_ids.is_empty() {
        Ok(if dual_witness_present {
            "Exact".to_owned()
        } else {
            "Closed".to_owned()
        })
    } else {
        Ok("Open".to_owned())
    }
}

pub fn set_delta(before: &[String], after: &[String]) -> (Vec<String>, Vec<String>, Vec<String>) {
    let before_set: BTreeSet<&String> = before.iter().collect();
    let after_set: BTreeSet<&String> = after.iter().collect();

    let eliminated = before_set
        .difference(&after_set)
        .map(|s| (*s).clone())
        .collect();
    let opened = after_set
        .difference(&before_set)
        .map(|s| (*s).clone())
        .collect();
    let retained = before_set
        .intersection(&after_set)
        .map(|s| (*s).clone())
        .collect();

    (eliminated, opened, retained)
}

#[allow(clippy::too_many_arguments)]
pub fn residual_drop_from_ids(
    before_ids: &[String],
    after_ids: &[String],
    cost: &Exact,
    dual_witness_present: bool,
    legal: bool,
    refusal_code: Option<String>,
    unit: &Exact,
) -> Result<ResidualDropV1, ScoringError> {
    let core_mass = mass_from_ids(before_ids, unit);

    if !legal {
        return Ok(ResidualDropV1 {
            residual_mass: core_mass.clone(),
            core_mass,
            // An illegal proposal has no measured drop and no efficiency. It
            // does not rank; it is excluded.
            delta: None,
            relative_drop: None,
            eliminated_ids: Vec::new(),
            opened_ids: Vec::new(),
            retained_ids: before_ids.to_vec(),
            cost: cost.clone(),
            efficiency: None,
            residual_colour: "Open".to_owned(),
            dual_witness_present,
            legal: false,
            refusal_code: Some(refusal_code.unwrap_or_else(|| REFUSAL_ILLEGAL_PROPOSAL.to_owned())),
        });
    }

    let residual_mass = mass_from_ids(after_ids, unit);
    let (delta, relative, efficiency) = residual_drop_mass(&core_mass, &residual_mass, cost)?;
    let (eliminated, opened, retained) = set_delta(before_ids, after_ids);
    let colour = residual_colour_from_mass(&residual_mass, dual_witness_present, after_ids)?;

    Ok(ResidualDropV1 {
        core_mass,
        residual_mass,
        delta: Some(delta),
        relative_drop: relative,
        eliminated_ids: eliminated,
        opened_ids: opened,
        retained_ids: retained,
        cost: cost.clone(),
        efficiency: Some(efficiency),
        residual_colour: colour,
        dual_witness_present,
        legal: true,
        refusal_code: None,
    })
}

/// Legal results, best efficiency first, cheaper first on a tie.
///
/// A total order: `Exact: Ord`, so no `partial_cmp` fallback is needed and two
/// distinct efficiencies can never compare as equal.
pub fn rank_by_efficiency(scored: &[ResidualDropV1]) -> Vec<ResidualDropV1> {
    let mut valid: Vec<ResidualDropV1> = scored.iter().filter(|r| r.legal).cloned().collect();
    valid.sort_by(|a, b| {
        b.efficiency
            .cmp(&a.efficiency)
            .then_with(|| a.cost.cmp(&b.cost))
            .then_with(|| a.core_mass.cmp(&b.core_mass))
    });
    valid
}

/// A refusal carries the prior norm unchanged: nothing was measured.
fn refused(
    proposal: &CandidateProposal,
    prior_norm: Exact,
    reason: String,
) -> CoboundaryScoreResult {
    CoboundaryScoreResult {
        proposal_id: proposal.proposal_id.clone(),
        post_residual_norm: prior_norm.clone(),
        prior_residual_norm: prior_norm,
        residual_drop: Exact::zero(),
        structural_cost: proposal.structural_cost.clone(),
        normalized_efficiency: None,
        is_legal: false,
        is_exact_candidate: false,
        dual_witness_ref: proposal.dual_witness_ref.clone(),
        refusal_reason: Some(reason),
    }
}

/// The legality checks every scoring path shares, in one place.
fn illegality(
    proposal: &CandidateProposal,
    admitted_constructors: Option<&[String]>,
    kill_conditions: Option<&BTreeMap<String, String>>,
) -> Option<String> {
    if proposal.structural_cost.is_negative() {
        return Some(format!(
            "{REFUSAL_NEGATIVE_MAGNITUDE}: structural_cost is negative"
        ));
    }
    if proposal.authority_effect != "None" {
        return Some(REFUSAL_AUTHORITY_NON_NONE.to_owned());
    }
    for trigger in &proposal.kill_triggers {
        match kill_conditions {
            Some(policy) => {
                if let Some(reason) = policy.get(trigger) {
                    return Some(reason.clone());
                }
            }
            None => return Some(format!("KILL_TRIGGER: {trigger:?}")),
        }
    }
    if let Some(admitted) = admitted_constructors {
        let admitted_set: BTreeSet<&String> = admitted.iter().collect();
        if proposal
            .admitted_constructors_used
            .iter()
            .any(|c| !admitted_set.contains(c))
        {
            return Some(REFUSAL_PROSE_PROMPT_REFUSED.to_owned());
        }
    }
    None
}

pub fn score_discrete_proposal(
    current_obstruction_ids: &[String],
    proposal: &CandidateProposal,
    admitted_constructors: Option<&[String]>,
) -> CoboundaryScoreResult {
    score_discrete_proposal_with_policy(
        current_obstruction_ids,
        proposal,
        admitted_constructors,
        None,
    )
}

pub fn score_discrete_proposal_with_policy(
    current_obstruction_ids: &[String],
    proposal: &CandidateProposal,
    admitted_constructors: Option<&[String]>,
    kill_conditions: Option<&BTreeMap<String, String>>,
) -> CoboundaryScoreResult {
    let distinct: BTreeSet<&String> = current_obstruction_ids.iter().collect();
    let prior_norm = Exact::from_integer(distinct.len().into());

    if let Some(reason) = illegality(proposal, admitted_constructors, kill_conditions) {
        return refused(proposal, prior_norm, reason);
    }

    let repaired: BTreeSet<&String> = proposal.repaired_obstruction_ids.iter().collect();
    let post_count = Exact::from_integer(distinct.difference(&repaired).count().into());
    let drop = &prior_norm - &post_count;

    let cost = proposal.structural_cost.clone();
    let efficiency = &drop / (Exact::one() + &cost);
    // Exact zero, not a tolerance.
    let is_exact = post_count.is_zero() && proposal.dual_witness_ref.is_some();

    CoboundaryScoreResult {
        proposal_id: proposal.proposal_id.clone(),
        prior_residual_norm: prior_norm,
        post_residual_norm: post_count,
        residual_drop: drop,
        structural_cost: cost,
        normalized_efficiency: Some(efficiency),
        is_legal: true,
        is_exact_candidate: is_exact,
        dual_witness_ref: proposal.dual_witness_ref.clone(),
        refusal_reason: None,
    }
}

pub fn score_cochain_proposal(
    core_cochain: &BTreeMap<String, Exact>,
    proposal: &CandidateProposal,
    admitted_constructors: Option<&[String]>,
) -> CoboundaryScoreResult {
    score_cochain_proposal_with_policy(core_cochain, proposal, admitted_constructors, None)
}

pub fn score_cochain_proposal_with_policy(
    core_cochain: &BTreeMap<String, Exact>,
    proposal: &CandidateProposal,
    admitted_constructors: Option<&[String]>,
    kill_conditions: Option<&BTreeMap<String, String>>,
) -> CoboundaryScoreResult {
    let prior_norm = core_functional::Phi1Functional::unweighted_l1_rational(
        &core_cochain.values().cloned().collect::<Vec<_>>(),
    )
    .checked_invariant_b60d41ac("exact cochain entries");

    if let Some(reason) = illegality(proposal, admitted_constructors, kill_conditions) {
        return refused(proposal, prior_norm, reason);
    }

    let mut residual = core_cochain.clone();
    for (key, delta) in &proposal.cochain_delta {
        *residual.entry(key.clone()).or_insert_with(Exact::zero) -= delta;
    }

    // Every non-zero term counts. The previous `filter(|v| v.abs() > 1e-9)`
    // discarded small residuals before summing, so a cochain of many tiny
    // non-zero components measured as exactly repaired.
    let post_norm = core_functional::Phi1Functional::unweighted_l1_rational(
        &residual.values().cloned().collect::<Vec<_>>(),
    )
    .checked_invariant_b60d41ac("exact cochain entries");
    let drop = &prior_norm - &post_norm;

    let cost = proposal.structural_cost.clone();
    let efficiency = &drop / (Exact::one() + &cost);
    let is_exact = post_norm.is_zero() && proposal.dual_witness_ref.is_some();

    CoboundaryScoreResult {
        proposal_id: proposal.proposal_id.clone(),
        prior_residual_norm: prior_norm,
        post_residual_norm: post_norm,
        residual_drop: drop,
        structural_cost: cost,
        normalized_efficiency: Some(efficiency),
        is_legal: true,
        is_exact_candidate: is_exact,
        dual_witness_ref: proposal.dual_witness_ref.clone(),
        refusal_reason: None,
    }
}

/// Score every proposal, legal ones first, then by efficiency, then by cost.
pub fn rank_candidate_proposals(
    current_obstruction_ids: &[String],
    proposals: &[CandidateProposal],
    admitted_constructors: Option<&[String]>,
) -> Vec<CoboundaryScoreResult> {
    rank_candidate_proposals_with_guard(
        current_obstruction_ids,
        proposals,
        admitted_constructors,
        |_| None,
    )
}

/// Apply a caller-owned exact guard before scoring, retaining a refused score
/// for every pruned proposal. The runtime does not depend on the guard compiler.
pub fn rank_candidate_proposals_with_guard(
    current_obstruction_ids: &[String],
    proposals: &[CandidateProposal],
    admitted_constructors: Option<&[String]>,
    mut guard_refusal: impl FnMut(&CandidateProposal) -> Option<String>,
) -> Vec<CoboundaryScoreResult> {
    let prior_norm = mass_from_ids(current_obstruction_ids, &Exact::one());
    let scored: Vec<CoboundaryScoreResult> = proposals
        .iter()
        .map(|proposal| match guard_refusal(proposal) {
            Some(reason) => refused(proposal, prior_norm.clone(), reason),
            None => {
                score_discrete_proposal(current_obstruction_ids, proposal, admitted_constructors)
            }
        })
        .collect();

    rank_scored_candidates(scored)
}

/// The cost check `illegality` already applies. A scored row has no authority,
/// kill list, or constructor list, so those arms are not re-decided here.
fn ranked_row_cost_refusal(score: &CoboundaryScoreResult) -> Option<String> {
    let proposal = CandidateProposal {
        proposal_id: String::new(),
        repaired_obstruction_ids: Vec::new(),
        cochain_delta: Vec::new(),
        structural_cost: score.structural_cost.clone(),
        kill_triggers: Vec::new(),
        admitted_constructors_used: Vec::new(),
        dual_witness_ref: None,
        authority_effect: "None".to_owned(),
    };
    illegality(&proposal, None, None)
}

pub fn rank_scored_candidates(
    mut scored: Vec<CoboundaryScoreResult>,
) -> Vec<CoboundaryScoreResult> {
    for row in &mut scored {
        if let Some(reason) = ranked_row_cost_refusal(row) {
            if row.is_legal || row.normalized_efficiency.is_some() || row.is_exact_candidate {
                row.is_legal = false;
                row.normalized_efficiency = None;
                row.is_exact_candidate = false;
                row.refusal_reason = Some(reason);
            }
        }
    }
    scored.sort_by(|a, b| {
        // Legality is `illegality`'s cost check, already applied above.
        // A negative cost has no efficiency, so it cannot outrank a measured row.
        // The client `is_legal` bit is not a sort key.
        b.normalized_efficiency
            .cmp(&a.normalized_efficiency)
            // `None` sorts below every `Some`, which is what an illegal
            // proposal deserves and what NEG_INFINITY was imitating.
            .then_with(|| a.structural_cost.cmp(&b.structural_cost))
            .then_with(|| a.proposal_id.cmp(&b.proposal_id))
    });

    scored
}

// Origin: engine/crates_rs/pfp_runtime/src/scoring_frontier.rs
// Claim: urn:core:crates_rs:pfp-runtime:scoring-frontier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_kernel::{exact, integer};

    fn proposal(id: &str, repairs: &[&str], cost: Exact, dual: Option<&str>) -> CandidateProposal {
        CandidateProposal {
            proposal_id: id.to_owned(),
            repaired_obstruction_ids: repairs.iter().map(|s| (*s).to_owned()).collect(),
            cochain_delta: vec![],
            structural_cost: cost,
            kill_triggers: vec![],
            admitted_constructors_used: vec![],
            dual_witness_ref: dual.map(str::to_owned),
            authority_effect: "None".to_owned(),
        }
    }

    fn ids(values: &[&str]) -> Vec<String> {
        values.iter().map(|s| (*s).to_owned()).collect()
    }

    #[test]
    fn score_and_rank_proposals() {
        let obs = ids(&["obs_01", "obs_02", "obs_03"]);
        let p1 = proposal("p1", &["obs_01", "obs_02"], integer(1), None);
        let p2 = proposal(
            "p2",
            &["obs_01", "obs_02", "obs_03"],
            exact(1, 2),
            Some("dual_cert_01"),
        );

        let ranked = rank_candidate_proposals(&obs, &[p1, p2], None);
        assert_eq!(ranked.len(), 2);
        assert_eq!(ranked[0].proposal_id, "p2");
        assert!(ranked[0].is_exact_candidate);
        assert!(ranked[0].post_residual_norm.is_zero());
    }

    #[test]
    fn a_residual_below_the_old_tolerance_is_not_exact() {
        // The defect this rewrite exists to remove. 1/10^12 is far under the
        // old `1e-9` threshold, so the previous implementation reported the
        // repair as exact and the residual as fully cleared.
        let omega = BTreeMap::from([("e1".to_owned(), exact(1, 1_000_000_000_000))]);
        let mut p = proposal("p", &[], Exact::zero(), Some("dual"));
        p.cochain_delta = vec![];

        let scored = score_cochain_proposal(&omega, &p, None);
        assert!(
            !scored.is_exact_candidate,
            "a non-zero residual is not exact, however small"
        );
        assert!(!scored.post_residual_norm.is_zero());
        assert_eq!(scored.post_residual_norm, exact(1, 1_000_000_000_000));
    }

    #[test]
    fn many_small_components_do_not_vanish_when_summed() {
        // The old filter dropped each term below 1e-9 *before* summing, so a
        // thousand of them summed to zero instead of to a thousandth.
        let omega: BTreeMap<String, Exact> = (0..1000)
            .map(|i| (format!("e{i}"), exact(1, 1_000_000_000_000)))
            .collect();
        let p = proposal("p", &[], Exact::zero(), Some("dual"));

        let scored = score_cochain_proposal(&omega, &p, None);
        assert_eq!(scored.post_residual_norm, exact(1000, 1_000_000_000_000));
        assert!(!scored.is_exact_candidate);
    }

    #[test]
    fn an_exactly_cancelled_cochain_is_exact() {
        let omega = BTreeMap::from([("e1".to_owned(), exact(3, 7))]);
        let mut p = proposal("p", &[], Exact::zero(), Some("dual"));
        p.cochain_delta = vec![("e1".to_owned(), exact(3, 7))];

        let scored = score_cochain_proposal(&omega, &p, None);
        assert!(scored.post_residual_norm.is_zero());
        assert!(scored.is_exact_candidate, "3/7 - 3/7 is exactly zero");
    }

    #[test]
    fn thirds_survive_a_round_trip_that_binary_floats_cannot() {
        // 1/3 has no exact binary representation. Three of them sum to exactly
        // one here; in f64 they do not.
        let omega: BTreeMap<String, Exact> =
            (0..3).map(|i| (format!("e{i}"), exact(1, 3))).collect();
        let p = proposal("p", &[], Exact::zero(), None);
        assert_eq!(
            score_cochain_proposal(&omega, &p, None).prior_residual_norm,
            integer(1)
        );
    }

    #[test]
    fn an_exact_candidate_still_requires_a_dual_witness() {
        let omega = BTreeMap::from([("e1".to_owned(), Exact::zero())]);
        let p = proposal("p", &[], Exact::zero(), None);
        let scored = score_cochain_proposal(&omega, &p, None);
        assert!(scored.post_residual_norm.is_zero());
        assert!(
            !scored.is_exact_candidate,
            "zero residual alone is not exactness"
        );
    }

    #[test]
    fn an_illegal_proposal_has_no_efficiency_and_ranks_last() {
        let obs = ids(&["obs_01"]);
        let mut bad = proposal("bad", &["obs_01"], Exact::zero(), None);
        bad.authority_effect = "StateTransition".to_owned();
        let good = proposal("good", &[], integer(5), None);

        let ranked = rank_candidate_proposals(&obs, &[bad, good], None);
        assert_eq!(ranked[0].proposal_id, "good");
        assert_eq!(ranked[1].proposal_id, "bad");
        assert_eq!(ranked[1].normalized_efficiency, None);
        assert_eq!(
            ranked[1].refusal_reason.as_deref(),
            Some(REFUSAL_AUTHORITY_NON_NONE)
        );
    }

    #[test]
    fn ranking_is_a_total_order_with_no_tie_fallback() {
        // Efficiencies 1/2 and 1/3 differ by less than any f64 epsilon dance;
        // exactly, they are ordered.
        let obs = ids(&["a"]);
        let p1 = proposal("p1", &["a"], integer(1), None); // drop 1, cost 1 -> 1/2
        let p2 = proposal("p2", &["a"], integer(2), None); // drop 1, cost 2 -> 1/3
        let ranked = rank_candidate_proposals(&obs, &[p2, p1], None);
        assert_eq!(ranked[0].proposal_id, "p1");
        assert_eq!(ranked[0].normalized_efficiency, Some(exact(1, 2)));
        assert_eq!(ranked[1].normalized_efficiency, Some(exact(1, 3)));
    }

    #[test]
    fn relative_drop_is_absent_rather_than_zero_when_there_was_nothing_to_drop() {
        let (delta, relative, _) =
            residual_drop_mass(&Exact::zero(), &Exact::zero(), &Exact::zero()).expect("legal");
        assert!(delta.is_zero());
        assert_eq!(relative, None, "0/0 is not 0");
    }

    #[test]
    fn negative_magnitudes_are_refused_with_a_typed_error() {
        assert_eq!(
            residual_drop_mass(&integer(-1), &Exact::zero(), &Exact::zero()),
            Err(ScoringError::NegativeMagnitude {
                field: "core_mass"
            })
        );
        let magnitudes = BTreeMap::from([("k".to_owned(), integer(-2))]);
        assert_eq!(
            mass_from_magnitudes(&magnitudes),
            Err(ScoringError::NegativeMagnitudeAt {
                key: "k".to_owned()
            })
        );
    }

    #[test]
    fn exact_values_cross_the_wire_as_strings_not_numbers() {
        let p = proposal("p", &[], exact(1, 3), None);
        let json = serde_json::to_string(&p).expect("serializes");
        assert!(json.contains(r#""structural_cost":"1/3""#), "{json}");
        assert!(
            !json.contains("0.333"),
            "an exact value must never degrade to a decimal: {json}"
        );
        let back: CandidateProposal = serde_json::from_str(&json).expect("round trips");
        assert_eq!(back.structural_cost, exact(1, 3));
    }

    #[test]
    fn a_negative_structural_cost_is_refused_and_zero_stays_legal() {
        let negative = proposal("bad", &["obs"], integer(-1), None);
        let omega = BTreeMap::from([("e".to_owned(), integer(1))]);
        for scored in [
            score_discrete_proposal(&ids(&["obs"]), &negative, None),
            score_cochain_proposal(&omega, &negative, None),
        ] {
            assert!(!scored.is_legal);
            assert_eq!(scored.structural_cost, integer(-1));
            assert_eq!(scored.normalized_efficiency, None);
            assert!(!scored.is_exact_candidate);
            assert_eq!(
                scored.refusal_reason.as_deref(),
                Some("NEGATIVE_MAGNITUDE: structural_cost is negative")
            );
        }
        let zero = proposal("ok", &[], Exact::zero(), None);
        for scored in [
            score_discrete_proposal(&ids(&["obs"]), &zero, None),
            score_cochain_proposal(&omega, &zero, None),
        ] {
            assert!(scored.is_legal);
            assert!(scored.refusal_reason.is_none());
            assert_eq!(scored.structural_cost, Exact::zero());
            assert!(scored.normalized_efficiency.is_some());
        }
    }

    #[test]
    fn a_float_on_the_wire_is_refused() {
        // The profile refuses floats; so must the parser, rather than rounding.
        let json = r#"{"proposal_id":"p","repaired_obstruction_ids":[],"cochain_delta":[],
            "structural_cost":0.333,"kill_triggers":[],"admitted_constructors_used":[],
            "dual_witness_ref":null,"authority_effect":"None"}"#;
        assert!(serde_json::from_str::<CandidateProposal>(json).is_err());
    }

    #[test]
    fn client_is_legal_bit_does_not_score_a_negative_structural_cost() {
        let forged = CoboundaryScoreResult {
            proposal_id: "forged".to_owned(),
            prior_residual_norm: Exact::zero(),
            post_residual_norm: Exact::zero(),
            residual_drop: Exact::zero(),
            structural_cost: integer(-1),
            normalized_efficiency: Some(integer(1000)),
            is_legal: true,
            is_exact_candidate: false,
            dual_witness_ref: None,
            refusal_reason: None,
        };
        let legal = CoboundaryScoreResult {
            proposal_id: "legal".to_owned(),
            prior_residual_norm: integer(1),
            post_residual_norm: integer(1),
            residual_drop: Exact::zero(),
            structural_cost: Exact::zero(),
            normalized_efficiency: Some(Exact::zero()),
            is_legal: true,
            is_exact_candidate: false,
            dual_witness_ref: None,
            refusal_reason: None,
        };

        let ranked = rank_scored_candidates(vec![forged, legal.clone()]);
        assert!(
            ranked.iter().all(|row| !(row.structural_cost.is_negative() && row.is_legal)),
            "a negative-cost row must not stay legal: {ranked:?}"
        );
        assert_eq!(ranked[0], legal, "cost 0 with is_legal true is unchanged");
        assert_eq!(ranked[1].structural_cost, integer(-1));
        assert!(!ranked[1].is_legal);
        assert_eq!(ranked[1].normalized_efficiency, None);
        assert_eq!(
            ranked[1].refusal_reason.as_deref(),
            Some("NEGATIVE_MAGNITUDE: structural_cost is negative")
        );

        let alone = rank_scored_candidates(vec![legal.clone()]);
        assert_eq!(alone, vec![legal]);

        let engine_negative = score_discrete_proposal(
            &ids(&["obs"]),
            &proposal("bad", &["obs"], integer(-1), None),
            None,
        );
        let engine_zero =
            score_discrete_proposal(&ids(&["obs"]), &proposal("ok", &[], Exact::zero(), None), None);
        assert!(!engine_negative.is_legal);
        assert!(engine_zero.is_legal);
        assert_eq!(
            rank_scored_candidates(vec![engine_negative.clone(), engine_zero.clone()]),
            vec![engine_zero, engine_negative]
        );
    }
}
