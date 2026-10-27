//! Primitive — **scope**: a result carries the scope it was certified under.
//!
//! Crate boundary: coda-terminal.  Source: `FW-SCOPE`; the sealed paper's
//! clause (d), where "three tied classes" is a bounded theorem within
//! `max_arity = 2` and the Lean arity family shows the unbounded tie is
//! infinite; the side-free control's terminal sentence, which is *narrower
//! than its table* on purpose.
//!
//! A `Terminal` is never returned without a `Scope` (`terminal.rs`), and a
//! `Scope` is a value, not a comment: it names the reading, the bounds, the
//! measures, and the population the claim ranged over.  A result quoted
//! outside its scope is a different claim, and usually a false one.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_28436e8a;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_28436e8a<T> = std::result::Result<T, BoundaryError_28436e8a>;
use std::fmt;

use crate::bounds::Bounds;
use crate::measure::{Measure, MeasureKind};

/// What a result was certified under.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Scope {
    /// The admission reading.
    pub reading: String,
    /// The declared candidate bounds.
    pub bounds: Bounds,
    /// The declared measures, tie-break measure first.
    pub measures: Vec<MeasureKind>,
    /// The population the claim ranged over.
    pub population: String,
    /// Anything else the claim depends on, one sentence each.
    pub notes: Vec<String>,
}

impl Scope {
    /// A scope for one reading with the sealed bounds and both measures.
    pub fn sealed(reading: &str, population: &str) -> Scope {
        Scope {
            reading: reading.to_string(),
            bounds: Bounds::default(),
            measures: MeasureKind::ALL.to_vec(),
            population: population.to_string(),
            notes: Vec::new(),
        }
    }

    /// Add a dependency note.
    pub fn with_note(mut self, note: impl Into<String>) -> Scope {
        self.notes.push(note.into());
        self
    }
}

impl fmt::Display for Scope {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let ms: Vec<&str> = self.measures.iter().map(|m| m.name()).collect();
        write!(f, "reading {}; {}; measures [{}]; population: {}", self.reading, self.bounds.describe(), ms.join(", "), self.population)?;
        for n in &self.notes {
            write!(f, "; {n}")?;
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/scope.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:scope:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_scope_names_reading_bounds_measures_and_population() {
        let s = Scope::sealed("L", "Challenge 3 situation").with_note("rule-free base");
        let text = s.to_string();
        assert!(text.contains("reading L"));
        assert!(text.contains("max_items=2"));
        assert!(text.contains("mu1, mu2"));
        assert!(text.contains("rule-free base"));
    }
}

/// Sealed scope: nonempty reading and population, and exactly two distinct measures.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SealedScopeWitness {
    measure_count: usize,
}

/// Errors encountered when validating a sealed scope witness.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SealedScopeError {
    /// Reading set is empty.
    EmptyReading,
    /// Population set is empty.
    EmptyPopulation,
    /// Incorrect number of measures.
    MeasureCount {
        /// Number of measures found.
        count: usize,
    },
    /// Measures are not distinct.
    MeasuresNotDistinct,
}

impl SealedScopeWitness {
    /// Attempts to validate and construct a sealed scope witness.
    pub fn try_sealed(scope: &Scope) -> Result<Self, SealedScopeError> {
        if scope.reading.is_empty() {
            return Err(SealedScopeError::EmptyReading);
        }
        if scope.population.is_empty() {
            return Err(SealedScopeError::EmptyPopulation);
        }
        if scope.measures.len() != 2 {
            return Err(SealedScopeError::MeasureCount {
                count: scope.measures.len(),
            });
        }
        let first = scope
            .measures
            .get(0)
            .ok_or(SealedScopeError::MeasureCount { count: 0 })?;
        let second = scope
            .measures
            .get(1)
            .ok_or(SealedScopeError::MeasureCount { count: 1 })?;
        if first == second {
            return Err(SealedScopeError::MeasuresNotDistinct);
        }
        Ok(Self { measure_count: 2 })
    }

    /// Returns the number of distinct measures in the sealed scope.
    pub fn measure_count(&self) -> usize {
        self.measure_count
    }
}
