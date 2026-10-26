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
