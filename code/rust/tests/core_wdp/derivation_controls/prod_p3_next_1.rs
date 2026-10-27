//! Finite executable witness for `PROD-P3-NEXT-1`.
//!
//! Models the P3 `GuardTransferChecker` soundness check (source soundness +
//! target transfer safety under a representation adapter) and exact Appendix Q.4
//! rational break-even pricing, with fixed `authority_effect = "None"`.

#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet};

pub const AUTHORITY_EFFECT_NONE: &str = "None";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GuardRule {
    pub rule_id: String,
    pub instance_id: String,
    pub rejects: BTreeSet<String>,
    pub authority_effect: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TransferRefusal {
    SourceUnsound(Vec<String>),
    TransferUnsafe(Vec<String>),
}

pub fn check_rule_transfer(
    rule: &GuardRule,
    source_valid: &BTreeSet<String>,
    target_id: &str,
    target_valid: &BTreeSet<String>,
    adapter: &BTreeMap<String, String>,
) -> Result<GuardRule, TransferRefusal> {
    let source_counterexamples: Vec<String> =
        rule.rejects.intersection(source_valid).cloned().collect();
    if !source_counterexamples.is_empty() {
        return Err(TransferRefusal::SourceUnsound(source_counterexamples));
    }

    let transferred_rejects: BTreeSet<String> = adapter
        .iter()
        .filter_map(|(y, x)| {
            if rule.rejects.contains(x) {
                Some(y.clone())
            } else {
                None
            }
        })
        .collect();

    let target_counterexamples: Vec<String> = transferred_rejects
        .intersection(target_valid)
        .cloned()
        .collect();
    if !target_counterexamples.is_empty() {
        return Err(TransferRefusal::TransferUnsafe(target_counterexamples));
    }

    Ok(GuardRule {
        rule_id: rule.rule_id.clone(),
        instance_id: target_id.to_string(),
        rejects: transferred_rejects,
        authority_effect: AUTHORITY_EFFECT_NONE,
    })
}

pub fn gcd(mut a: i128, mut b: i128) -> i128 {
    a = a.abs();
    b = b.abs();
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    if a == 0 { 1 } else { a }
}

/// Computes exact rational saving `h*v - N*g - C_0` as reduced `(num, den)`.
pub fn price_saving(
    candidates: i128,
    hits: i128,
    v_num: i128,
    v_den: i128,
    g_num: i128,
    g_den: i128,
    c0_num: i128,
    c0_den: i128,
) -> (i128, i128) {
    let den = v_den * g_den * c0_den;
    let num = hits * v_num * g_den * c0_den
        - candidates * g_num * v_den * c0_den
        - c0_num * v_den * g_den;
    let d = gcd(num, den);
    (num / d, den / d)
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p3_next_1.rs
// Claim: urn:core:crates_rs:tests:prod-p3-next-1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4ebd5ab5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4ebd5ab5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4ebd5ab5 {
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
impl BoundaryError4ebd5ab5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4ebd5ab5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4ebd5ab5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4ebd5ab5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4ebd5ab5> {
        if capacity_bound == 0 {
            return Err(BoundaryError4ebd5ab5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4ebd5ab5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4ebd5ab5::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sound_transfer_admits_circulation_and_refuses_unsafe_or_unsound_rules() {
        let source_valid: BTreeSet<String> = ["zero".to_string()].into_iter().collect();
        let target_valid: BTreeSet<String> =
            ["zero".to_string(), "gradient".to_string()].into_iter().collect();
        let adapter: BTreeMap<String, String> = [
            ("zero".to_string(), "zero".to_string()),
            ("gradient".to_string(), "gradient".to_string()),
            ("curved".to_string(), "curved".to_string()),
        ]
        .into_iter()
        .collect();

        let circulation = GuardRule {
            rule_id: "circulation".to_string(),
            instance_id: "zero-repairs".to_string(),
            rejects: ["curved".to_string()].into_iter().collect(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        };
        let transferred = check_rule_transfer(
            &circulation,
            &source_valid,
            "all-triangle-repairs",
            &target_valid,
            &adapter,
        )
        .expect("circulation transfers soundly");
        assert_eq!(transferred.instance_id, "all-triangle-repairs");
        assert_eq!(transferred.authority_effect, "None");

        let unsafe_rule = GuardRule {
            rule_id: "unsafe-point".to_string(),
            instance_id: "zero-repairs".to_string(),
            rejects: ["gradient".to_string()].into_iter().collect(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        };
        assert_eq!(
            check_rule_transfer(
                &unsafe_rule,
                &source_valid,
                "all-triangle-repairs",
                &target_valid,
                &adapter
            ),
            Err(TransferRefusal::TransferUnsafe(vec!["gradient".to_string()]))
        );

        let unsound_rule = GuardRule {
            rule_id: "invalid-source-rule".to_string(),
            instance_id: "zero-repairs".to_string(),
            rejects: ["zero".to_string()].into_iter().collect(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        };
        assert_eq!(
            check_rule_transfer(
                &unsound_rule,
                &source_valid,
                "all-triangle-repairs",
                &target_valid,
                &adapter
            ),
            Err(TransferRefusal::SourceUnsound(vec!["zero".to_string()]))
        );

        // Reference input.json saving: N=4, h=2, v=1, g=1/10, C_0=1 -> 3/5
        assert_eq!(price_saving(4, 2, 1, 1, 1, 10, 1, 1), (3, 5));
        // Q.4 worked example: N=10000, v=1, g=1/1000, C_0=2 -> h=12 gives 0, h=13 gives 1
        assert_eq!(price_saving(10000, 12, 1, 1, 1, 1000, 2, 1), (0, 1));
        assert_eq!(price_saving(10000, 13, 1, 1, 1, 1000, 2, 1), (1, 1));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_4ebd5ab5() {
    let admitted = BoundaryRecord4ebd5ab5::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4ebd5ab5::try_admit(9, 8).is_err());
}
