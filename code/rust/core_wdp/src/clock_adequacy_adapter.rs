//! Problem-bound WDP receipts for conditional finite clock adequacy.
//!
//! Chain arithmetic, edge coupling and budget/coarsening proofs are owned by
//! `core_measurement::finite_chain_clock`. Occurrence names, packet identity,
//! actual budgets and selected partition boundaries are preserved for replay.
//! Clock construction, physical coupling/units and traceability remain declared
//! prerequisites; adequate finite data does not derive those prerequisites.

use core_measurement::finite_chain_clock::{ChainClock, ChainClockError, ClockIntervalBound};
use thiserror::Error;

use crate::types::AuthorityEffect;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ClockPacketError {
    #[error("clock packet identity must be nonempty")]
    EmptyPacketIdentity,
    #[error("one nonempty occurrence label per chain vertex is required")]
    OccurrenceLabelsMismatch,
    #[error("the declared fine chain does not refine this coarse clock at these boundaries")]
    NotARefinement,
    #[error("finite clock refusal: {0}")]
    Clock(#[from] ChainClockError),
}

/// Labels annotate the declared vertices; equal strings may recur, since their
/// vertex positions are retained and no quotient of occurrences is inferred.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NamedChainClockPacket {
    pub packet_id: String,
    pub occurrences: Vec<String>,
    pub clock: ChainClock,
}

impl NamedChainClockPacket {
    pub fn new(
        packet_id: String,
        occurrences: Vec<String>,
        clock: ChainClock,
    ) -> Result<Self, ClockPacketError> {
        let packet = Self {
            packet_id,
            occurrences,
            clock,
        };
        packet.validate()?;
        Ok(packet)
    }
    fn validate(&self) -> Result<(), ClockPacketError> {
        if self.packet_id.is_empty() {
            return Err(ClockPacketError::EmptyPacketIdentity);
        }
        if self.occurrences.len() != self.clock.edge_count() + 1
            || self.occurrences.iter().any(String::is_empty)
        {
            return Err(ClockPacketError::OccurrenceLabelsMismatch);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClockAdequacyReceipt {
    pub packet: NamedChainClockPacket,
    pub interval_bounds: Vec<ClockIntervalBound>,
    pub authority_effect: AuthorityEffect,
}

pub fn evaluate_clock_adequacy(
    packet: &NamedChainClockPacket,
) -> Result<ClockAdequacyReceipt, ClockPacketError> {
    packet.validate()?;
    Ok(ClockAdequacyReceipt {
        packet: packet.clone(),
        interval_bounds: packet.clock.all_interval_bounds(),
        authority_effect: AuthorityEffect::None,
    })
}

pub fn verify_clock_adequacy(
    actual_packet: &NamedChainClockPacket,
    candidate: &ClockAdequacyReceipt,
) -> Result<bool, ClockPacketError> {
    Ok(candidate == &evaluate_clock_adequacy(actual_packet)?)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClockIntervalComparison {
    pub fine_interval: ClockIntervalBound,
    pub coarse_interval: ClockIntervalBound,
}

fn comparisons(
    fine: &ChainClock,
    coarse: &ChainClock,
    boundaries: &[usize],
) -> Result<Vec<ClockIntervalComparison>, ClockPacketError> {
    coarse
        .all_interval_bounds()
        .into_iter()
        .map(|coarse_interval| {
            let fine_interval = fine.interval_bound(
                boundaries[coarse_interval.start],
                boundaries[coarse_interval.stop],
            )?;
            Ok(ClockIntervalComparison {
                fine_interval,
                coarse_interval,
            })
        })
        .collect()
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClockCoarseningReceipt {
    pub actual_fine: NamedChainClockPacket,
    pub selected_boundaries: Vec<usize>,
    pub coarse_clock: ChainClock,
    pub coarse_occurrences: Vec<String>,
    pub interval_comparisons: Vec<ClockIntervalComparison>,
    pub authority_effect: AuthorityEffect,
}

pub fn evaluate_clock_coarsening(
    fine: &NamedChainClockPacket,
    boundaries: &[usize],
) -> Result<ClockCoarseningReceipt, ClockPacketError> {
    fine.validate()?;
    let coarse_clock = fine.clock.coarsen(boundaries)?;
    Ok(ClockCoarseningReceipt {
        actual_fine: fine.clone(),
        selected_boundaries: boundaries.to_vec(),
        coarse_occurrences: boundaries
            .iter()
            .map(|&v| fine.occurrences[v].clone())
            .collect(),
        interval_comparisons: comparisons(&fine.clock, &coarse_clock, boundaries)?,
        coarse_clock,
        authority_effect: AuthorityEffect::None,
    })
}

/// Actual boundaries are a separate verifier argument. Changing a candidate's
/// declared cuts, dropping edges, weakening budgets or replaying a different
/// chain therefore cannot fabricate evidence for the requested coarsening.
pub fn verify_clock_coarsening(
    actual_fine: &NamedChainClockPacket,
    actual_boundaries: &[usize],
    candidate: &ClockCoarseningReceipt,
) -> Result<bool, ClockPacketError> {
    Ok(candidate == &evaluate_clock_coarsening(actual_fine, actual_boundaries)?)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClockRefinementReceipt {
    pub actual_fine: NamedChainClockPacket,
    pub actual_coarse: NamedChainClockPacket,
    pub selected_boundaries: Vec<usize>,
    pub interval_comparisons: Vec<ClockIntervalComparison>,
    pub authority_effect: AuthorityEffect,
}

/// Certify a separately declared coarse clock, permitting coarse budgets larger
/// than fine block sums but requiring the same endpoint readings, reference
/// durations, calibration and occurrence labels at the selected boundaries.
pub fn evaluate_clock_refinement(
    fine: &NamedChainClockPacket,
    coarse: &NamedChainClockPacket,
    boundaries: &[usize],
) -> Result<ClockRefinementReceipt, ClockPacketError> {
    fine.validate()?;
    coarse.validate()?;
    if !fine.clock.refines(&coarse.clock, boundaries)?
        || boundaries
            .iter()
            .map(|&v| fine.occurrences[v].clone())
            .collect::<Vec<_>>()
            != coarse.occurrences
    {
        return Err(ClockPacketError::NotARefinement);
    }
    Ok(ClockRefinementReceipt {
        actual_fine: fine.clone(),
        actual_coarse: coarse.clone(),
        selected_boundaries: boundaries.to_vec(),
        interval_comparisons: comparisons(&fine.clock, &coarse.clock, boundaries)?,
        authority_effect: AuthorityEffect::None,
    })
}

pub fn verify_clock_refinement(
    actual_fine: &NamedChainClockPacket,
    actual_coarse: &NamedChainClockPacket,
    actual_boundaries: &[usize],
    candidate: &ClockRefinementReceipt,
) -> Result<bool, ClockPacketError> {
    Ok(candidate == &evaluate_clock_refinement(actual_fine, actual_coarse, actual_boundaries)?)
}

// Origin: engine/crates_rs/core_wdp/src/clock_adequacy_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:clock-adequacy-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    use num_rational::BigRational;
    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }
    fn packet() -> NamedChainClockPacket {
        NamedChainClockPacket::new(
            "clock-0".into(),
            (0..5).map(|v| format!("event-{v}")).collect(),
            ChainClock::new(
                vec![q(3, 2), q(10, 3), q(15, 4), q(26, 5)],
                vec![q(-2, 1), q(-1, 1), q(1, 2), q(5, 2), q(5, 1)],
                q(2, 1),
                vec![q(1, 2), q(1, 3), q(1, 4), q(1, 5)],
            )
            .unwrap(),
        )
        .unwrap()
    }

    #[test]
    fn adequacy_receipt_binds_actual_budget_and_all_intervals() {
        let actual = packet();
        let receipt = evaluate_clock_adequacy(&actual).unwrap();
        assert_eq!(receipt.interval_bounds.len(), 15);
        assert!(verify_clock_adequacy(&actual, &receipt).unwrap());
        let mut forged = receipt.clone();
        forged.interval_bounds[1].error_budget = q(100, 1);
        assert!(!verify_clock_adequacy(&actual, &forged).unwrap());
        let mut forged = receipt.clone();
        forged.interval_bounds.pop();
        assert!(!verify_clock_adequacy(&actual, &forged).unwrap());
        let mut changed = actual.clone();
        changed.clock = ChainClock::new(
            actual.clock.durations().to_vec(),
            actual.clock.readings().to_vec(),
            actual.clock.calibration().clone(),
            vec![q(1, 1); 4],
        )
        .unwrap();
        assert!(!verify_clock_adequacy(&changed, &receipt).unwrap());
    }

    #[test]
    fn coarsening_replay_checks_boundaries_and_endpoint_block_sums() {
        let actual = packet();
        let receipt = evaluate_clock_coarsening(&actual, &[0, 2, 4]).unwrap();
        assert_eq!(receipt.coarse_clock.durations(), &[q(29, 6), q(179, 20)]);
        assert_eq!(receipt.coarse_clock.error_budgets(), &[q(5, 6), q(9, 20)]);
        assert_eq!(
            receipt.coarse_occurrences,
            vec!["event-0", "event-2", "event-4"]
        );
        assert!(verify_clock_coarsening(&actual, &[0, 2, 4], &receipt).unwrap());
        assert!(!verify_clock_coarsening(&actual, &[0, 1, 4], &receipt).unwrap());
        let mut forged = receipt.clone();
        forged.selected_boundaries = vec![0, 1, 4];
        assert!(!verify_clock_coarsening(&actual, &[0, 2, 4], &forged).unwrap());
        let mut forged = receipt;
        forged.interval_comparisons[1].fine_interval.discrepancy = q(0, 1);
        assert!(!verify_clock_coarsening(&actual, &[0, 2, 4], &forged).unwrap());
        assert!(evaluate_clock_coarsening(&actual, &[0, 2, 3]).is_err());
    }

    #[test]
    fn refinement_replay_accepts_relaxed_budget_and_rejects_endpoint_changes() {
        let fine = packet();
        let coarsening = evaluate_clock_coarsening(&fine, &[0, 2, 4]).unwrap();
        let coarse = NamedChainClockPacket::new(
            "coarse-0".into(),
            coarsening.coarse_occurrences.clone(),
            ChainClock::new(
                coarsening.coarse_clock.durations().to_vec(),
                coarsening.coarse_clock.readings().to_vec(),
                q(2, 1),
                vec![q(1, 1), q(1, 1)],
            )
            .unwrap(),
        )
        .unwrap();
        let receipt = evaluate_clock_refinement(&fine, &coarse, &[0, 2, 4]).unwrap();
        assert!(verify_clock_refinement(&fine, &coarse, &[0, 2, 4], &receipt).unwrap());
        for pair in &receipt.interval_comparisons {
            assert_eq!(
                pair.fine_interval.discrepancy,
                pair.coarse_interval.discrepancy
            );
            assert!(pair.fine_interval.error_budget <= pair.coarse_interval.error_budget);
        }
        let mut wrong = coarse.clone();
        wrong.occurrences[1] = "other-event".into();
        assert_eq!(
            evaluate_clock_refinement(&fine, &wrong, &[0, 2, 4]),
            Err(ClockPacketError::NotARefinement)
        );
        let mut forged = receipt;
        forged.actual_coarse.packet_id = "different-clock".into();
        assert!(!verify_clock_refinement(&fine, &coarse, &[0, 2, 4], &forged).unwrap());
    }

    #[test]
    fn empty_chain_and_invalid_named_packet_are_checked() {
        let empty = NamedChainClockPacket::new(
            "empty".into(),
            vec!["event".into()],
            ChainClock::new(vec![], vec![q(8, 1)], q(1, 1), vec![]).unwrap(),
        )
        .unwrap();
        let receipt = evaluate_clock_coarsening(&empty, &[0]).unwrap();
        assert!(verify_clock_coarsening(&empty, &[0], &receipt).unwrap());
        assert_eq!(receipt.interval_comparisons.len(), 1);
        let mut invalid = packet();
        invalid.occurrences.pop();
        assert_eq!(
            evaluate_clock_adequacy(&invalid),
            Err(ClockPacketError::OccurrenceLabelsMismatch)
        );
        invalid = packet();
        invalid.packet_id.clear();
        assert_eq!(
            evaluate_clock_adequacy(&invalid),
            Err(ClockPacketError::EmptyPacketIdentity)
        );
    }
}
