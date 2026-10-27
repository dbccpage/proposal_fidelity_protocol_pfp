//! Replay-side trace containers.
//!
//! The trace-artifact **vocabulary** (`TraceArtifact` and its marker family,
//! plus the `VoidTrace` sentinel) now lives in the foundation crate
//! `core_types::trace_artifact`, so that governance law (`core_contracts`)
//! can depend on it without depending on this verification crate
//! (SG-LAYER-001 / PO-LAYER). This module re-exports that vocabulary verbatim —
//! so existing `core_replay::trace::TraceArtifact` / `…::VoidTrace` paths keep
//! resolving — and keeps the concrete replay-side containers `StepTrace` and
//! `LayeredTrace`, which implement the foundation trait.

use serde::{Deserialize, Serialize};

// Vocabulary lives in the foundation; re-export so the replay public API is
// unchanged.
pub use core_types::trace_artifact::{
    ActionResultArtifact, AnalysisArtifact, DecisionArtifact, ImmutableTrace, TraceArtifact,
    ValidationArtifact, VoidTrace,
};

/// Sequential trace: an ordered list of step records.
#[derive(Clone, Serialize, Deserialize)]
pub struct StepTrace<T> {
    steps: Vec<T>,
}

impl<T> StepTrace<T> {
    pub fn new(steps: Vec<T>) -> Self {
        Self { steps }
    }

    pub fn steps(&self) -> &[T] {
        &self.steps
    }

    pub fn into_steps(self) -> Vec<T> {
        self.steps
    }
}

impl<T> TraceArtifact for StepTrace<T> where T: Clone + Serialize + for<'de> Deserialize<'de> {}
impl<T> ImmutableTrace for StepTrace<T> where T: Clone + Serialize + for<'de> Deserialize<'de> {}

/// Layered trace: a flat collection of layer records.
#[derive(Clone, Serialize, Deserialize)]
pub struct LayeredTrace<T> {
    layers: Vec<T>,
}

impl<T> LayeredTrace<T> {
    pub fn new(layers: Vec<T>) -> Self {
        Self { layers }
    }

    pub fn layers(&self) -> &[T] {
        &self.layers
    }

    pub fn into_layers(self) -> Vec<T> {
        self.layers
    }
}

impl<T> TraceArtifact for LayeredTrace<T> where T: Clone + Serialize + for<'de> Deserialize<'de> {}
impl<T> ImmutableTrace for LayeredTrace<T> where T: Clone + Serialize + for<'de> Deserialize<'de> {}

/// Checked length of a concatenation of two finite traces.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TraceLength {
    left: u64,
    right: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TraceLengthError {
    Overflow { left: u64, right: u64 },
}

// Origin: engine/crates_rs/core_replay/src/trace.rs
// Claim: urn:core:crates_rs:core-replay:trace:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TraceLengthError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TraceLengthError {}

impl TraceLength {
    pub fn try_concat(left: u64, right: u64) -> Result<Self, TraceLengthError> {
        let _total = left
            .checked_add(right)
            .ok_or(TraceLengthError::Overflow { left, right })?;
        Ok(Self { left, right })
    }

    pub fn total(&self) -> Option<u64> {
        self.left.checked_add(self.right)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod trace_length_witness {
    use super::*;

    #[test]
    fn concatenation_adds_the_lengths() {
        let length = TraceLength::try_concat(4, 7);
        assert!(length.is_ok());
        if let Ok(length) = length {
            assert_eq!(length.total(), Some(11));
        }
    }

    #[test]
    fn overflow_is_refused() {
        assert!(matches!(
            TraceLength::try_concat(u64::MAX, 1),
            Err(TraceLengthError::Overflow { .. })
        ));
    }
}
