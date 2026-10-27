//! Primitive — **transition roles**, derived from the accepted responses.
//!
//! Crate boundary: coda-price.  Source: `engine.py::_role`, `delta_label`;
//! sealed required question 9.
//!
//! The five roles the derivation itself produced — **supply,
//! discrimination, innovation, auxiliary witness, double discrimination** —
//! are not a taxonomy anyone declared.  They are the shapes of the deltas
//! the engine actually accepted, named after the fact.  The crosstab (§3)
//! makes the point that matters: these are the *object language's* roles;
//! the represented-process vocabulary (proposal, evaluation, authorization)
//! is a different layer built later to answer an outside question.  Running
//! the two together would be smuggling.
//!
//! In the represented process, `Discrimination` and `DoubleDiscrimination`
//! are rule-1 repairs; `Innovation` and `AuxiliaryWitness` are rule-2
//! augmentations (`candidate::is_structure_creating`).

use std::fmt;

use crate::candidate::{Delta, Item};
use crate::regime::Regime;

/// A recurring transition role.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Role {
    /// The external continuation policy admitted a fresh token.
    Supply,
    /// One instance on an existing form.
    Discrimination,
    /// A new form with one instance on it.
    Innovation,
    /// A fresh datum with an instance mentioning it.
    AuxiliaryWitness,
    /// Two instances on existing forms.
    DoubleDiscrimination,
    /// Any other accepted shape, named by its item kinds.
    Other(String),
}

/// The role of an accepted response.  `is_supply` marks the external
/// continuation move, which has an empty delta.
pub fn role(is_supply: bool, delta: &Delta) -> Role {
    if is_supply {
        return Role::Supply;
    }
    let mut kinds: Vec<&str> = delta
        .iter()
        .map(|it| match it {
            Item::NewDatum => "datum",
            Item::NewForm(_) => "form",
            Item::NewRuleAll(_) => "rule",
            Item::NewInst(_, _) => "inst",
        })
        .collect();
    kinds.sort();
    match kinds.as_slice() {
        ["inst"] => Role::Discrimination,
        ["form", "inst"] => Role::Innovation,
        ["datum", "inst"] => Role::AuxiliaryWitness,
        ["inst", "inst"] => Role::DoubleDiscrimination,
        other => Role::Other(other.join("+")),
    }
}

/// Deterministic neutral label for a response delta, as the sealed receipts
/// print it: `form1+inst1`, `form2+inst2diag`, `datum+inst2+fresh`, …
pub fn delta_label(base: &Regime, delta: &Delta) -> String {
    let n0 = base.n_data();
    let parts: Vec<String> = delta
        .iter()
        .map(|it| match it {
            Item::NewDatum => "datum".to_string(),
            Item::NewForm(a) => format!("form{a}"),
            Item::NewRuleAll(f) => format!("rule@{f}"),
            Item::NewInst(_, args) => {
                let distinct: std::collections::BTreeSet<usize> = args.iter().map(|m| m.0).collect();
                let shape = if distinct.len() == 1 && args.len() > 1 { "diag" } else { "" };
                let fresh = if args.iter().any(|m| m.0 >= n0) { "+fresh" } else { "" };
                format!("inst{}{shape}{fresh}", args.len())
            }
        })
        .collect();
    if parts.is_empty() {
        "empty".to_string()
    } else {
        parts.join("+")
    }
}

impl fmt::Display for Role {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Role::Supply => write!(f, "supply"),
            Role::Discrimination => write!(f, "discrimination"),
            Role::Innovation => write!(f, "innovation"),
            Role::AuxiliaryWitness => write!(f, "auxiliary_witness"),
            Role::DoubleDiscrimination => write!(f, "double_discrimination"),
            Role::Other(s) => write!(f, "{s}"),
        }
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/role.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:role:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1612c470 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1612c470` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1612c470 {
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
impl BoundaryError1612c470 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1612c470 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1612c470 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1612c470 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1612c470> {
        if capacity_bound == 0 {
            return Err(BoundaryError1612c470::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1612c470::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1612c470::ExceedsCapacity {
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
mod tests {
    use super::*;
    use crate::mark::Mark;
    use crate::reading::READING_L;
    use crate::replay::replay;

    #[test]
    fn the_five_roles() {
        let m = |a: &[usize]| Item::NewInst(0, a.iter().map(|&x| Mark(x)).collect());
        assert_eq!(role(true, &vec![]), Role::Supply);
        assert_eq!(role(false, &vec![m(&[0])]), Role::Discrimination);
        assert_eq!(role(false, &vec![Item::NewForm(1), m(&[0])]), Role::Innovation);
        assert_eq!(role(false, &vec![Item::NewDatum, m(&[2])]), Role::AuxiliaryWitness);
        assert_eq!(role(false, &vec![m(&[0]), m(&[1])]), Role::DoubleDiscrimination);
    }

    #[test]
    fn labels_match_the_sealed_receipt_vocabulary() {
        let base = replay(&READING_L.genesis).unwrap();
        let m = |a: &[usize]| Item::NewInst(0, a.iter().map(|&x| Mark(x)).collect());
        assert_eq!(delta_label(&base, &vec![Item::NewForm(1), m(&[0])]), "form1+inst1");
        assert_eq!(delta_label(&base, &vec![Item::NewForm(2), m(&[0, 0])]), "form2+inst2diag");
        assert_eq!(delta_label(&base, &vec![Item::NewForm(2), m(&[0, 1])]), "form2+inst2");
        assert_eq!(delta_label(&base, &vec![Item::NewDatum, m(&[2])]), "datum+inst1+fresh");
        assert_eq!(delta_label(&base, &vec![]), "empty");
    }
}

#[cfg(test)]
mod l4_boundary_tests_1612c470 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1612c470::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1612c470::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1612c470::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1612c470::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1612c470::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1612c470::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1612c470::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
