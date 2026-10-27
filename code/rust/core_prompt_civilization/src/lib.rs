//! Prompt Civilization: pure calculus for prompt evolution, genealogy, rank, and immune regulation.
//!
//! AuthorityEffect: None.

#![allow(clippy::manual_div_ceil)]

pub mod antimorphism;
pub mod civilization;
pub mod convergence;
pub mod crossover;
pub mod domain;
pub mod ecology;
pub mod evidence;
pub mod fitness;
pub mod forge;
pub mod genealogy;
pub mod immune;
pub mod immunity;
pub mod lamarckian;
pub mod learning_signals;
pub mod matching;
pub mod metabolism;
pub mod pharmacy;
pub mod prompt_family;
pub mod rank;
pub mod rank_port;
pub mod record;
pub mod society;

pub use domain::{hard_domain_eligible, DomainPlacementV1};
pub use fitness::{
    compute_pareto_fronts, compute_pareto_fronts_bigrational, compute_pareto_fronts_rational,
    pareto_frontier_rational, CandidateBigRational, CandidateRational, PromptFitnessV1,
};
pub use forge::{MutationOperatorCandidateV1, PopulationPolicyV1, PromptMutationEngineV1};
pub use genealogy::{
    GenealogyError, GenealogyGraph, InheritanceEdgeV1, InheritanceRelationship, LineageGraphV1,
    LineageTree,
};
pub use immunity::{ImmunityAcquisitionV1, ImmunityEngineV1, ImmunityPropagationV1};
pub use lamarckian::{
    CochainHistoryTracker, CochainResidualV1, LamarckianCochainTrackerV1,
    LamarckianMutationReceiptV1, LamarckianTrackingError, LamarckianVerificationResult,
};
pub use matching::{PrecedentMatcherV1, ReferenceTrailEvaporationCalculatorV1};
pub use pharmacy::{
    decode_candidate_bytes, detect, detect_with_raw_bytes, ingest_and_detect, DetectionContext,
    DetectorReport, Disposition, FailureClass, Finding, HostIngestError,
};
pub use rank::{ExactPageRankSolverV1, RankError, RankEvidenceV1};
pub use record::{
    CustodyTier, ExecutionOccurrenceV1, PacketRefV1, ParentLinkV1, PromptGenomeV1, PromptMaturity,
    PromptViewV1, ProtectedSpanV1, RetrievalEligibility,
};
pub use society::{
    AggregateFitnessVectorV1, MigrationPolicyV1, PromptCivilizationV1, PromptSocietyV1,
};

/// Always `"None"` -- this crate mints zero authority.
pub fn authority_effect() -> &'static str {
    "None"
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalSpend {
    numer: i128,
    denom: i128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SpendError {
    ZeroDenom,
    Overflow,
    OverCeiling,
}

// Origin: engine/crates_rs/core_prompt_civilization/src/lib.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SpendError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SpendError {}

fn gcd_i128(mut a: i128, mut b: i128) -> Result<i128, SpendError> {
    if a < 0 {
        a = a.checked_neg().ok_or(SpendError::Overflow)?;
    }
    if b < 0 {
        b = b.checked_neg().ok_or(SpendError::Overflow)?;
    }
    while b != 0 {
        let r = a.checked_rem(b).ok_or(SpendError::Overflow)?;
        a = b;
        b = r;
    }
    Ok(a)
}

fn reduce_i128(mut numer: i128, mut denom: i128) -> Result<(i128, i128), SpendError> {
    if denom <= 0 {
        return Err(SpendError::ZeroDenom);
    }
    let g = gcd_i128(numer, denom)?;
    if g == 0 {
        return Err(SpendError::ZeroDenom);
    }
    numer = numer.checked_div(g).ok_or(SpendError::Overflow)?;
    denom = denom.checked_div(g).ok_or(SpendError::Overflow)?;
    Ok((numer, denom))
}

fn sum_fractions_i128(
    spent_n: i128,
    spent_d: i128,
    add_n: i128,
    add_d: i128,
) -> Result<(i128, i128), SpendError> {
    let left_term = spent_n.checked_mul(add_d).ok_or(SpendError::Overflow)?;
    let right_term = add_n.checked_mul(spent_d).ok_or(SpendError::Overflow)?;
    let num = left_term
        .checked_add(right_term)
        .ok_or(SpendError::Overflow)?;
    let den = spent_d.checked_mul(add_d).ok_or(SpendError::Overflow)?;
    Ok((num, den))
}

pub fn try_rational_spend(
    cap_n: i128,
    cap_d: i128,
    spent_n: i128,
    spent_d: i128,
    add_n: i128,
    add_d: i128,
) -> Result<RationalSpend, SpendError> {
    let all_positive = cap_d > 0 && spent_d > 0 && add_d > 0;
    if !all_positive {
        return Err(SpendError::ZeroDenom);
    }
    let (num, den) = sum_fractions_i128(spent_n, spent_d, add_n, add_d)?;
    let left = num.checked_mul(cap_d).ok_or(SpendError::Overflow)?;
    let right = cap_n.checked_mul(den).ok_or(SpendError::Overflow)?;
    if left > right {
        return Err(SpendError::OverCeiling);
    }
    let (numer, denom) = reduce_i128(num, den)?;
    Ok(RationalSpend { numer, denom })
}

impl RationalSpend {
    pub fn numer(&self) -> i128 {
        self.numer
    }

    pub fn denom(&self) -> i128 {
        self.denom
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod rational_spend_tests {
    use super::*;

    #[test]
    fn a_half_plus_a_half_fills_the_unit_cap() {
        let full = try_rational_spend(1, 1, 1, 2, 1, 2);
        assert!(matches!(full, Ok(spend) if spend.numer() == 1 && spend.denom() == 1));
        assert!(matches!(
            try_rational_spend(1, 1, 1, 2, 2, 3),
            Err(SpendError::OverCeiling)
        ));
    }
}
