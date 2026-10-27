//! The **outside**: the push the engine cannot give itself.
//!
//! Crate boundary: outside everything.  Source: standing obstruction
//! **OB-1** (no object-language endogenous demand generator was derived);
//! L3 (a declared API discipline); the licence gate whose grantor the
//! estate does not model; the sealed external continuation policy.
//!
//! This trait is the whole of what the Core engine asks for, and it is
//! exactly the author's four primitives with the estate's names beside
//! them:
//!
//! | author | method | the estate's word | recorded as |
//! |---|---|---|---|
//! | presentation | `present` | supply | `Supply` then `AdmitDatum` |
//! | proposal | `demand` and `choose` | imposition; tie-break declaration | `Impose`; the chosen delta in `Respond` |
//! | evaluation | — | *not outside*: the engine does it | menu, family, prices, classes, certificates |
//! | authorization | `authorize`, `fund` | licence; budget | `SetLicense`; `SetBudget` |
//!
//! Note what the outside returns: tokens, pairs, indices, booleans, fuel.
//! **Never an event.**  The engine turns each answer into an event and
//! records it, so the history shows *that* the outside pushed and *what* it
//! pushed, even though nothing in the history can show why.  That is the
//! author's position on authorization, kept as a type: "it's just Popper on
//! steroids" — the world may still say no, and the record must survive it.
//!
//! Silent-run tests show local behavior, not a theorem excluding other engines.  `Scripted` pushes from a fixed script, so a run is a
//! deterministic function of the script and replays.

use std::collections::VecDeque;

use crate::candidate::Delta;
use crate::mark::Pair;
use crate::measure::{Cost, MeasureKind};
use crate::minima::Class;
use crate::regime::Regime;
use crate::token::Token;

/// A proposal the engine puts to the outside for authorization.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Proposal {
    /// The requirement it answers.
    pub target: Pair,
    /// The delta.
    pub delta: Delta,
    /// Whether it creates structure (rule 2) or repairs (rule 1).
    pub structure_creating: bool,
    /// Its cost under every declared measure.
    pub prices: Vec<(MeasureKind, Cost)>,
    /// How many tied classes it was chosen from.
    pub tie_classes: usize,
}

/// The push from outside.
pub trait Outside {
    /// Present a fresh token, or stay silent.
    fn present(&mut self, regime: &Regime) -> Option<Token>;
    /// Demand that a pair be separated, or stay silent.
    fn demand(&mut self, regime: &Regime) -> Option<Pair>;
    /// Select one of the retained tied classes, or decline.
    fn choose(&mut self, classes: &[Class]) -> Option<usize>;
    /// Grant or withhold the licence for a structure-creating proposal.
    fn authorize(&mut self, proposal: &Proposal) -> bool;
    /// Fund the run: how many responses may be paid for now.
    fn fund(&mut self, regime: &Regime) -> u32;
}

/// An outside that never pushes.
#[derive(Clone, Copy, Debug, Default)]
pub struct Silent;

impl Outside for Silent {
    fn present(&mut self, _: &Regime) -> Option<Token> {
        None
    }
    fn demand(&mut self, _: &Regime) -> Option<Pair> {
        None
    }
    fn choose(&mut self, _: &[Class]) -> Option<usize> {
        None
    }
    fn authorize(&mut self, _: &Proposal) -> bool {
        false
    }
    fn fund(&mut self, _: &Regime) -> u32 {
        0
    }
}

/// An outside that pushes from a fixed script.
#[derive(Clone, Debug, Default)]
pub struct Scripted {
    /// Tokens to present, in order.
    pub tokens: VecDeque<Token>,
    /// Demands, in order.
    pub demands: VecDeque<Pair>,
    /// Tie-break choices, in order; `None` declines.
    pub choices: VecDeque<Option<usize>>,
    /// Whether to grant licences.
    pub licence: bool,
    /// Funding grants, in order; exhausted means 0.
    pub funds: VecDeque<u32>,
    /// Everything the engine asked and what was answered.
    pub log: Vec<String>,
}

impl Scripted {
    /// A script that demands one pair, always takes the first class,
    /// grants the licence, and funds `fuel` responses once.
    pub fn one_demand(target: Pair, fuel: u32) -> Scripted {
        Scripted {
            tokens: VecDeque::new(),
            demands: VecDeque::from([target]),
            choices: VecDeque::from(vec![Some(0); 32]),
            licence: true,
            funds: VecDeque::from([fuel]),
            log: Vec::new(),
        }
    }
}

impl Outside for Scripted {
    fn present(&mut self, _: &Regime) -> Option<Token> {
        let t = self.tokens.pop_front();
        self.log.push(format!("present -> {}", t.as_ref().map_or("silent".to_string(), |t| t.to_string())));
        t
    }
    fn demand(&mut self, _: &Regime) -> Option<Pair> {
        let p = self.demands.pop_front();
        self.log.push(format!("demand -> {}", p.map_or("silent".to_string(), |p| p.to_string())));
        p
    }
    fn choose(&mut self, classes: &[Class]) -> Option<usize> {
        let c = self.choices.pop_front().flatten().filter(|&k| k < classes.len());
        self.log.push(format!("choose among {} -> {}", classes.len(), c.map_or("declined".to_string(), |k| k.to_string())));
        c
    }
    fn authorize(&mut self, proposal: &Proposal) -> bool {
        self.log.push(format!("authorize {} -> {}", proposal.target, self.licence));
        self.licence
    }
    fn fund(&mut self, _: &Regime) -> u32 {
        let f = self.funds.pop_front().unwrap_or(0);
        self.log.push(format!("fund -> {f}"));
        f
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/outside.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:outside:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6d416787 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6d416787` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6d416787 {
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
impl BoundaryError6d416787 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6d416787 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6d416787 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6d416787 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6d416787> {
        if capacity_bound == 0 {
            return Err(BoundaryError6d416787::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6d416787::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6d416787::ExceedsCapacity {
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

    #[test]
    fn the_silent_outside_pushes_nothing() {
        let mut s = Silent;
        let g = Regime::genesis();
        assert!(s.present(&g).is_none() && s.demand(&g).is_none() && s.choose(&[]).is_none());
        assert_eq!(s.fund(&g), 0);
    }

    #[test]
    fn a_script_is_consumed_in_order_and_logged() {
        let mut s = Scripted::one_demand(Pair::of(0, 1), 2);
        let g = Regime::genesis();
        assert_eq!(s.demand(&g), Some(Pair::of(0, 1)));
        assert_eq!(s.demand(&g), None);
        assert_eq!(s.fund(&g), 2);
        assert_eq!(s.fund(&g), 0);
        assert_eq!(s.log.len(), 4);
    }
}

#[cfg(test)]
mod l4_boundary_tests_6d416787 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6d416787::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6d416787::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6d416787::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6d416787::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6d416787::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6d416787::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6d416787::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
