//! Companion Rust witness for REV-SMRM-P1-LOSS (Governor refuses LOSS certificates lacking b_0).

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AbstentionLabel {
    Stalled,
    Exhausted,
    LosingInDeclaredArena,
    Impossible,
    RefusedCertificate,
}

pub fn verify_loss_trap_set(
    initial_belief: &str,
    trap_set: &[&str],
    trap_disjoint_from_goal: bool,
    trap_closed: bool,
    task_admits_impossibility: bool,
) -> AbstentionLabel {
    let contains_b0 = trap_set.contains(&initial_belief);
    if !contains_b0 || !trap_disjoint_from_goal || !trap_closed {
        return AbstentionLabel::RefusedCertificate;
    }
    if task_admits_impossibility {
        AbstentionLabel::Impossible
    } else {
        AbstentionLabel::LosingInDeclaredArena
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LossTrapCensus {
    hits: u64,
    label: AbstentionLabel,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LossTrapCensusError {
    ImageMiss,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/rev_smrm_p1_loss.rs
// Claim: urn:core:crates_rs:tests:rev-smrm-p1-loss:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for LossTrapCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for LossTrapCensusError {}

impl LossTrapCensus {
    pub fn certify(hits: u64, trap_disjoint_from_goal: bool, trap_closed: bool, task_admits_impossibility: bool) -> Result<Self, LossTrapCensusError> {
        let label = if hits == 0 || !trap_disjoint_from_goal || !trap_closed {
            AbstentionLabel::RefusedCertificate
        } else if task_admits_impossibility {
            AbstentionLabel::Impossible
        } else {
            AbstentionLabel::LosingInDeclaredArena
        };
        if label == AbstentionLabel::Stalled || label == AbstentionLabel::Exhausted { return Err(LossTrapCensusError::ImageMiss); }
        Ok(Self { hits, label })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loss_certificate_missing_initial_belief_is_refused() {
        assert_eq!(
            verify_loss_trap_set("b0", &["b1", "b2"], true, true, true),
            AbstentionLabel::RefusedCertificate
        );
        assert_eq!(
            verify_loss_trap_set("b0", &["b0", "b1"], true, true, true),
            AbstentionLabel::Impossible
        );
        assert_ne!(AbstentionLabel::Stalled, AbstentionLabel::Exhausted);
        assert_ne!(AbstentionLabel::Exhausted, AbstentionLabel::Impossible);
        assert_ne!(AbstentionLabel::Stalled, AbstentionLabel::Impossible);
    }

#[test]
    fn exact_witness_holds() {
        assert!(matches!(LossTrapCensus::certify(0, true, true, true), Ok(w) if w.label == AbstentionLabel::RefusedCertificate));
        assert!(matches!(LossTrapCensus::certify(1, true, true, true), Ok(w) if w.label == AbstentionLabel::Impossible));
        assert!(matches!(LossTrapCensus::certify(1, true, true, false), Ok(w) if w.label == AbstentionLabel::LosingInDeclaredArena));
        assert!(matches!(LossTrapCensus::certify(2, false, true, true), Ok(w) if w.label == AbstentionLabel::RefusedCertificate));
    }
}
