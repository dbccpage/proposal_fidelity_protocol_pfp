//! Seeded core.contract.v1 terminal/refusal vocabulary (spec §11.1).
//!
//! NO `core_state` dependency (layer rule: `core_contracts` must not depend on
//! `core_state`, the same prohibition that applies to `core_replay`). For the walking
//! skeleton this is a small local allow-list seeded with the trichotomy classes + generic
//! error vocabulary. A later sprint replaces/extends this with a generated global
//! `TermReg`/`RefusalReg`.

/// Terminal/class names recognized in v1 (Sprint 1 seed: trichotomy classes).
pub const V1_KNOWN_TERMINALS: &[&str] = &["ExactRepair", "StabilizedSurvivor", "OpenObstruction"];

/// Refusal/meta-outcome names recognized in v1 (Sprint 1 seed: trichotomy + generic errors).
pub const V1_KNOWN_REFUSALS: &[&str] = &[
    "Invalid",
    "Incomparable",
    "TriRefused(NumericUndecidable)",
    "NumericUndecidable",
    "DetectorInadequate",
    "NoRule",
    "RequiresLift",
    "Refused",
    "BudgetExhausted",
    "Cancelled",
    "UnknownTerminal",
    "UnknownRefusal",
];

pub fn is_known_terminal(name: &str) -> bool {
    V1_KNOWN_TERMINALS.contains(&name)
}

pub fn is_known_refusal(name: &str) -> bool {
    V1_KNOWN_REFUSALS.contains(&name)
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VocabularyPartition {
    terminals: u64,
    refusals: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum VocabularyPartitionError {
    EmptySide,
    Blank,
    DuplicateTerminal,
    DuplicateRefusal,
    Overlap,
    Overflow,
}

// Origin: engine/crates_rs/core_contracts/src/registry_v1_vocabulary.rs
// Claim: urn:core:crates_rs:core-contracts:registry-v1-vocabulary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for VocabularyPartitionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for VocabularyPartitionError {}

impl VocabularyPartition {
    fn check_no_overlap(name: &str, refusals: &[&str]) -> Result<(), VocabularyPartitionError> {
        let rcount = u64::try_from(refusals.len()).map_err(|_| VocabularyPartitionError::Overflow)?;
        let mut k = 0u64;
        while k < rcount {
            let k_us = usize::try_from(k).map_err(|_| VocabularyPartitionError::Overflow)?;
            let refusal = *refusals.get(k_us).ok_or(VocabularyPartitionError::Overflow)?;
            if name == refusal { return Err(VocabularyPartitionError::Overlap); }
            k = k.checked_add(1).ok_or(VocabularyPartitionError::Overflow)?;
        }
        Ok(())
    }

    fn check_no_later_duplicate(
        name: &str,
        items: &[&str],
        start: u64,
        count: u64,
        duplicate: &VocabularyPartitionError,
    ) -> Result<(), VocabularyPartitionError> {
        let mut j = start;
        while j < count {
            let j_us = usize::try_from(j).map_err(|_| VocabularyPartitionError::Overflow)?;
            let later = *items.get(j_us).ok_or(VocabularyPartitionError::Overflow)?;
            if name == later { return Err(duplicate.clone()); }
            j = j.checked_add(1).ok_or(VocabularyPartitionError::Overflow)?;
        }
        Ok(())
    }

    fn item_at<'a>(items: &'a [&'a str], index: u64) -> Result<&'a str, VocabularyPartitionError> {
        let idx = usize::try_from(index).map_err(|_| VocabularyPartitionError::Overflow)?;
        let name = *items.get(idx).ok_or(VocabularyPartitionError::Overflow)?;
        if name.trim().is_empty() { return Err(VocabularyPartitionError::Blank); }
        Ok(name)
    }

    fn walk(
        items: &[&str],
        duplicate: VocabularyPartitionError,
        other: Option<&[&str]>,
    ) -> Result<u64, VocabularyPartitionError> {
        let count = u64::try_from(items.len()).map_err(|_| VocabularyPartitionError::Overflow)?;
        if count == 0 { return Err(VocabularyPartitionError::EmptySide); }
        let mut i = 0u64;
        while i < count {
            let name = Self::item_at(items, i)?;
            let next = i.checked_add(1).ok_or(VocabularyPartitionError::Overflow)?;
            Self::check_no_later_duplicate(name, items, next, count, &duplicate)?;
            if let Some(refusals) = other {
                Self::check_no_overlap(name, refusals)?;
            }
            i = next;
        }
        Ok(count)
    }

    pub fn certify(terminals: &[&str], refusals: &[&str]) -> Result<Self, VocabularyPartitionError> {
        let terminals_n = Self::walk(terminals, VocabularyPartitionError::DuplicateTerminal, Some(refusals))?;
        let refusals_n = Self::walk(refusals, VocabularyPartitionError::DuplicateRefusal, None)?;
        let out = Self { terminals: terminals_n, refusals: refusals_n };
        Ok(out)
    }
}

impl VocabularyPartition {
    pub fn certify_seed() -> Result<Self, VocabularyPartitionError> {
        Self::certify(V1_KNOWN_TERMINALS, V1_KNOWN_REFUSALS)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn seeded_terminals_known() {
        assert!(is_known_terminal("ExactRepair"));
        assert!(is_known_terminal("StabilizedSurvivor"));
        assert!(is_known_terminal("OpenObstruction"));
        assert!(!is_known_terminal("MadeUpTerminal"));
    }

    #[test]
    fn seeded_refusals_known() {
        assert!(is_known_refusal("Invalid"));
        assert!(is_known_refusal("TriRefused(NumericUndecidable)"));
        assert!(is_known_refusal("DetectorInadequate"));
        assert!(is_known_refusal("NoRule"));
        assert!(is_known_refusal("RequiresLift"));
        assert!(is_known_refusal("Refused"));
        assert!(is_known_refusal("BudgetExhausted"));
        assert!(is_known_refusal("Cancelled"));
        assert!(!is_known_refusal("MadeUpRefusal"));
    }

#[test]
    fn exact_witness_holds() {
        assert!(matches!(VocabularyPartition::certify_seed(), Ok(w) if w.terminals == 3 && w.refusals == 12));
        assert!(matches!(VocabularyPartition::certify(&["ExactRepair", "ExactRepair"], &["Invalid"]), Err(VocabularyPartitionError::DuplicateTerminal)));
        assert!(matches!(VocabularyPartition::certify(&["ExactRepair"], &["ExactRepair"]), Err(VocabularyPartitionError::Overlap)));
        assert!(matches!(VocabularyPartition::certify(&["ExactRepair"], &[]), Err(VocabularyPartitionError::EmptySide)));
    }
}
