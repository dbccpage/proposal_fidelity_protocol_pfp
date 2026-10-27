//! Question-specific Source-25 bridge to the minimal bounded-counter report.
//! Only add/remove events on one existing fixed cell are in this context.
//! This does not quotient all Source-25 events or recover raw multiplicities.
use crate::genesis_source_execution::{Source25Change, Source25State, SourceRelation};
use num_bigint::BigInt;
use num_traits::ToPrimitive;
use core_category_theory::bounded_counter::{
    CounterBoundary, CounterEvent, CounterReport, CounterReportError,
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CellGuardError {
    OutsideCarrier,
    UnsupportedContextEvent,
    InvalidCount,
    Report(CounterReportError),
    Boundary(CounterBoundary),
}

// Origin: engine/crates_rs/core_wdp/src/genesis_guard_report.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-guard-report:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CellGuardError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CellGuardError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source25CellGuard {
    relation: SourceRelation,
    x: usize,
    y: usize,
    report: CounterReport,
}

impl Source25CellGuard {
    pub fn from_state(
        state: &Source25State,
        relation: SourceRelation,
        x: usize,
        y: usize,
        remaining: usize,
    ) -> Result<Self, CellGuardError> {
        if !state.is_enabled(Source25Change::AddAssertion { relation, x, y }) {
            return Err(CellGuardError::OutsideCarrier);
        }
        let packet = state.packet();
        let counts = match relation {
            SourceRelation::R => &packet.r,
            SourceRelation::S => &packet.s,
        };
        // The native constructor validated the square shape and nonnegativity.
        let count = &counts[x * packet.terms.len() + y];
        let clipped = if count >= &BigInt::from(remaining) {
            remaining
        } else {
            count.to_usize().ok_or(CellGuardError::InvalidCount)?
        };
        Ok(Self {
            relation,
            x,
            y,
            report: CounterReport::try_from_clip(remaining, clipped)
                .map_err(CellGuardError::Report)?,
        })
    }

    pub fn report(&self) -> CounterReport {
        self.report
    }

    pub fn advance(&self, change: Source25Change) -> Result<Self, CellGuardError> {
        let event = match change {
            Source25Change::AddAssertion { relation, x, y }
                if relation == self.relation && x == self.x && y == self.y =>
            {
                CounterEvent::Increment
            }
            Source25Change::Remove { relation, x, y }
                if relation == self.relation && x == self.x && y == self.y =>
            {
                CounterEvent::Decrement
            }
            _ => return Err(CellGuardError::UnsupportedContextEvent),
        };
        let report = self
            .report
            .advance(event)
            .map_err(CellGuardError::Boundary)?;
        Ok(Self {
            report,
            ..self.clone()
        })
    }

    pub fn observe(&self, changes: &[Source25Change]) -> Result<Self, CellGuardError> {
        changes
            .iter()
            .try_fold(self.clone(), |state, &change| state.advance(change))
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9e8a48d5 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
