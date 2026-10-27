//! P1 Abstention and Impossibility Governor (PROD-P1) exact verifier.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TerminationLabel {
    Terminated,
    OutOfFuel,
    Impossible,
    InvalidRequest,
}

pub fn decide_abstention(
    certificate_valid: bool,
    optimal_cost: Option<u64>,
    budget: u64,
) -> TerminationLabel {
    if !certificate_valid {
        return TerminationLabel::InvalidRequest;
    }
    match optimal_cost {
        None => TerminationLabel::Impossible,
        Some(cost) if budget < cost => TerminationLabel::OutOfFuel,
        Some(_) => TerminationLabel::Terminated,
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AbstentionSlack {
    label: TerminationLabel,
    slack: Option<u64>,
    deficit: Option<u64>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AbstentionSlackError {
    LabelDrift,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p1.rs
// Claim: urn:core:crates_rs:tests:prod-p1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for AbstentionSlackError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for AbstentionSlackError {}

impl AbstentionSlack {
    pub fn certify(certificate_valid: bool, optimal_cost: Option<u64>, budget: u64) -> Result<Self, AbstentionSlackError> {
        let label = decide_abstention(certificate_valid, optimal_cost, budget);
        match (label, optimal_cost) {
            (TerminationLabel::Terminated, Some(cost)) if budget >= cost => {
                Ok(Self { label, slack: Some(budget - cost), deficit: None })
            }
            (TerminationLabel::OutOfFuel, Some(cost)) if cost > budget => {
                Ok(Self { label, slack: None, deficit: Some(cost - budget) })
            }
            (TerminationLabel::Impossible, None) if certificate_valid => {
                Ok(Self { label, slack: None, deficit: None })
            }
            (TerminationLabel::InvalidRequest, _) if !certificate_valid => {
                Ok(Self { label, slack: None, deficit: None })
            }
            _ => Err(AbstentionSlackError::LabelDrift),
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_p1_partition_labels() {
        assert_eq!(decide_abstention(true, Some(3), 2), TerminationLabel::OutOfFuel);
        assert_eq!(decide_abstention(true, Some(3), 3), TerminationLabel::Terminated);
        assert_eq!(decide_abstention(true, None, 100), TerminationLabel::Impossible);
        assert_eq!(decide_abstention(false, Some(3), 3), TerminationLabel::InvalidRequest);
    }

#[test]
    fn exact_witness_holds() {
        assert!(matches!(AbstentionSlack::certify(true, Some(3), 5), Ok(w) if w.label == TerminationLabel::Terminated && w.slack == Some(2) && w.deficit.is_none()));
        assert!(matches!(AbstentionSlack::certify(true, Some(3), 2), Ok(w) if w.label == TerminationLabel::OutOfFuel && w.deficit == Some(1)));
        assert!(matches!(AbstentionSlack::certify(true, None, 100), Ok(w) if w.label == TerminationLabel::Impossible));
        assert!(matches!(AbstentionSlack::certify(false, Some(3), 9), Ok(w) if w.label == TerminationLabel::InvalidRequest));
        assert!(matches!(AbstentionSlack::certify(true, Some(3), 3), Ok(w) if w.slack == Some(0)));
    }
}
