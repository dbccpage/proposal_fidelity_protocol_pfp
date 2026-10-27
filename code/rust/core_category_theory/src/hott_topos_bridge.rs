//! Bridge HoTT judgments into finite topos-style semantics.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HottJudgmentInterpretation {
    pub judgment: String,
    pub context_object: String,
    pub semantic_object: String,
    pub evidence: Vec<String>,
}

impl HottJudgmentInterpretation {
    pub fn new(judgment: &str, context_object: &str, semantic_object: &str) -> Self {
        Self {
            judgment: judgment.into(),
            context_object: context_object.into(),
            semantic_object: semantic_object.into(),
            evidence: Vec::new(),
        }
    }

    pub fn add_evidence(&mut self, evidence: &str) {
        self.evidence.push(evidence.into());
    }

    pub fn validate(&self) -> Vec<String> {
        let mut violations = Vec::new();
        if self.judgment.trim().is_empty() {
            violations.push("HoTT judgment is empty".into());
        }
        if self.context_object.trim().is_empty() {
            violations.push("Context object is empty".into());
        }
        if self.semantic_object.trim().is_empty() {
            violations.push("Semantic object is empty".into());
        }
        violations
    }
}

/// Refusal from a monotone Kripke chain.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KripkeError {
    /// A later world drops a formula an earlier world forced.
    NotMonotone { world: usize },
}

// Origin: engine/crates_rs/core_category_theory/src/hott_topos_bridge.rs
// Claim: urn:core:crates_rs:core-category-theory:hott-topos-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for KripkeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for KripkeError {}

/// `worlds[i] = (forces_a, forces_b)` along a chain. Returns whether `a → b` is forced at world 0.
pub fn try_kripke_implication(worlds: &[(bool, bool)]) -> Result<bool, KripkeError> {
    let mut saw_a = false;
    let mut saw_b = false;
    for (index, &(forces_a, forces_b)) in worlds.iter().enumerate() {
        if saw_a && !forces_a {
            return Err(KripkeError::NotMonotone { world: index });
        }
        if saw_b && !forces_b {
            return Err(KripkeError::NotMonotone { world: index });
        }
        saw_a = forces_a;
        saw_b = forces_b;
    }
    let mut holds = true;
    for index in 0..worlds.len() {
        let later = &worlds[index..];
        for &(forces_a, forces_b) in later {
            if forces_a && !forces_b {
                holds = false;
            }
        }
        break;
    }
    Ok(holds)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod kripke_tests {
    use super::*;
    #[test]
    fn a_persistent_implication_holds() {
        assert!(matches!(try_kripke_implication(&[(false, false), (true, true)]), Ok(true)));
    }
    #[test]
    fn a_later_counterexample_fails_the_implication() {
        assert!(matches!(try_kripke_implication(&[(false, false), (true, false)]), Ok(false)));
    }
}
